# -*- coding: utf-8 -*-
"""Trader App — Multi-currency / exchange rate helpers for the SPA."""

from __future__ import unicode_literals

import json

import frappe
from frappe import _
from frappe.utils import nowdate, getdate, flt, cint

from trader_app.api.company import resolve_active_company


def _company_base_currency(company):
    return frappe.get_cached_value("Company", company, "default_currency") or "PKR"


def _assert_currency_settings_permission():
    roles = set(frappe.get_roles())
    if frappe.session.user == "Administrator":
        return
    allowed = {"System Manager", "Trader Admin", "Accounts Manager"}
    if not roles.intersection(allowed):
        frappe.throw(_("You do not have permission to change currency settings."))


def _all_system_currencies():
    return frappe.get_all(
        "Currency",
        filters={"enabled": 1},
        fields=["name", "currency_name", "symbol"],
        order_by="name asc",
    )


def _parse_enabled_currencies(raw, base):
    enabled = []
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                enabled = [str(c).strip() for c in parsed if c]
        except Exception:
            enabled = []
    if base and base not in enabled:
        enabled.insert(0, base)
    return enabled


def get_company_currency_settings(company):
    """Per-company multi-currency configuration stored on Company."""
    company = resolve_active_company(company)
    base = _company_base_currency(company)
    multi = cint(frappe.db.get_value("Company", company, "trader_multi_currency_enabled"))
    raw = frappe.db.get_value("Company", company, "trader_enabled_currencies") or ""
    enabled = _parse_enabled_currencies(raw, base)

    if not multi:
        enabled = [base]

    return {
        "company": company,
        "base_currency": base,
        "multi_currency_enabled": bool(multi),
        "enabled_currencies": enabled,
    }


def _filter_currencies_for_company(company):
    settings = get_company_currency_settings(company)
    base = settings["base_currency"]
    all_rows = _all_system_currencies()
    if not settings["multi_currency_enabled"]:
        match = next((r for r in all_rows if r.name == base), None)
        rows = [match] if match else [{"name": base, "currency_name": base, "symbol": base}]
        return settings, rows

    allowed = set(settings["enabled_currencies"])
    raw = frappe.db.get_value("Company", company, "trader_enabled_currencies") or ""
    if not raw.strip():
        # Multi-currency on with no explicit list → all enabled ERP currencies
        rows = all_rows
    else:
        rows = [r for r in all_rows if r.name in allowed]
        if not any(r.name == base for r in rows):
            rows.insert(0, {"name": base, "currency_name": base, "symbol": base})
    return settings, rows


def _fetch_exchange_rate(from_currency, to_currency, transaction_date, for_selling=True):
    """Resolve ERPNext exchange rate with safe fallback to 1."""
    if not from_currency or not to_currency or from_currency == to_currency:
        return 1.0

    try:
        from erpnext.setup.utils import get_exchange_rate

        purpose = "for_selling" if for_selling else "for_buying"
        return flt(get_exchange_rate(from_currency, to_currency, transaction_date, purpose))
    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_exchange_rate failed")
        return 1.0


def apply_document_currency(doc, currency=None, exchange_rate=None, posting_date=None, for_selling=True):
    """Set currency and conversion_rate on a selling/purchase document."""
    company = doc.company
    settings = get_company_currency_settings(company)
    base = settings["base_currency"]
    currency = (currency or base).strip()

    if not settings["multi_currency_enabled"]:
        currency = base
    elif currency != base and currency not in settings["enabled_currencies"]:
        frappe.throw(
            _("Currency {0} is not enabled for this company. Update currency settings.").format(currency)
        )

    posting_date = posting_date or getattr(doc, "posting_date", None) or getattr(doc, "transaction_date", None) or nowdate()

    doc.currency = currency
    if currency == base:
        doc.conversion_rate = 1.0
    else:
        doc.conversion_rate = flt(exchange_rate) if exchange_rate else _fetch_exchange_rate(
            currency, base, posting_date, for_selling=for_selling
        )


def _list_exchange_rates(company, limit=40):
    base = _company_base_currency(company)
    return frappe.get_all(
        "Currency Exchange",
        filters=[
            ["date", ">=", frappe.utils.add_days(nowdate(), -365)],
            ["to_currency", "=", base],
        ],
        fields=[
            "name",
            "date",
            "from_currency",
            "to_currency",
            "exchange_rate",
            "for_selling",
            "for_buying",
        ],
        order_by="date desc, from_currency asc",
        limit=cint(limit) or 40,
    )


@frappe.whitelist()
def get_currency_options(company=None):
    """Enabled currencies and the company's base currency for transaction forms."""
    company = resolve_active_company(company)
    settings, rows = _filter_currencies_for_company(company)
    return {
        "company": company,
        "base_currency": settings["base_currency"],
        "multi_currency_enabled": settings["multi_currency_enabled"],
        "enabled_currencies": settings["enabled_currencies"],
        "currencies": rows,
    }


@frappe.whitelist()
def get_exchange_rate_for_date(currency, posting_date=None, company=None, transaction_type="selling"):
    """Exchange rate from document currency to company base currency."""
    company = resolve_active_company(company)
    settings = get_company_currency_settings(company)
    base = settings["base_currency"]
    currency = (currency or base).strip()
    posting_date = posting_date or nowdate()
    for_selling = (transaction_type or "selling").lower() != "buying"

    if not settings["multi_currency_enabled"] or currency == base:
        return {
            "currency": currency,
            "base_currency": base,
            "posting_date": posting_date,
            "exchange_rate": 1.0,
            "for_selling": for_selling,
            "multi_currency_enabled": settings["multi_currency_enabled"],
        }

    rate = _fetch_exchange_rate(currency, base, posting_date, for_selling=for_selling)
    return {
        "currency": currency,
        "base_currency": base,
        "posting_date": posting_date,
        "exchange_rate": rate,
        "for_selling": for_selling,
        "multi_currency_enabled": True,
    }


def _ensure_currency_custom_fields():
    if frappe.db.exists("Custom Field", "Company-trader_multi_currency_enabled"):
        return
    from trader_app.setup.custom_fields import ensure_custom_fields

    ensure_custom_fields()


@frappe.whitelist()
def get_currency_settings(company=None):
    """Full currency configuration for the Settings screen."""
    _ensure_currency_custom_fields()
    company = resolve_active_company(company)
    settings = get_company_currency_settings(company)
    return {
        **settings,
        "available_currencies": _all_system_currencies(),
        "exchange_rates": _list_exchange_rates(company),
    }


@frappe.whitelist()
def save_currency_settings(
    base_currency=None,
    multi_currency_enabled=None,
    enabled_currencies=None,
    company=None,
):
    """Update company base currency and Trader multi-currency options."""
    _assert_currency_settings_permission()
    company = resolve_active_company(company)
    doc = frappe.get_doc("Company", company)

    if base_currency:
        base_currency = base_currency.strip()
        if not frappe.db.exists("Currency", base_currency):
            frappe.throw(_("Currency {0} does not exist.").format(base_currency))
        if not frappe.db.get_value("Currency", base_currency, "enabled"):
            frappe.throw(_("Enable currency {0} in ERPNext before setting it as base.").format(base_currency))
        doc.default_currency = base_currency

    if multi_currency_enabled is not None:
        doc.trader_multi_currency_enabled = cint(multi_currency_enabled)

    if enabled_currencies is not None:
        if isinstance(enabled_currencies, str):
            try:
                enabled_currencies = json.loads(enabled_currencies)
            except Exception:
                frappe.throw(_("enabled_currencies must be a JSON array."))
        if not isinstance(enabled_currencies, list):
            frappe.throw(_("enabled_currencies must be a list of currency codes."))
        base = doc.default_currency or _company_base_currency(company)
        cleaned = []
        for code in enabled_currencies:
            code = str(code).strip()
            if code and code not in cleaned:
                cleaned.append(code)
        if base and base not in cleaned:
            cleaned.insert(0, base)
        doc.trader_enabled_currencies = json.dumps(cleaned)

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "ok": True,
        "message": _("Currency settings saved."),
        "settings": get_currency_settings(company),
    }


@frappe.whitelist()
def save_exchange_rate(
    from_currency,
    exchange_rate,
    to_currency=None,
    date=None,
    for_selling=1,
    for_buying=0,
    company=None,
):
    """Create or update a manual Currency Exchange row (foreign → base)."""
    _assert_currency_settings_permission()
    company = resolve_active_company(company)
    base = _company_base_currency(company)
    from_currency = (from_currency or "").strip()
    to_currency = (to_currency or base).strip()
    date = getdate(date or nowdate())
    rate = flt(exchange_rate)

    if not from_currency:
        frappe.throw(_("From currency is required."))
    if from_currency == to_currency:
        frappe.throw(_("From and to currency must differ."))
    if rate <= 0:
        frappe.throw(_("Exchange rate must be greater than zero."))

    filters = {
        "date": date,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "for_selling": cint(for_selling),
        "for_buying": cint(for_buying),
    }
    name = frappe.db.get_value("Currency Exchange", filters, "name")

    if name:
        doc = frappe.get_doc("Currency Exchange", name)
        doc.exchange_rate = rate
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Currency Exchange",
                "date": date,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "exchange_rate": rate,
                "for_selling": cint(for_selling),
                "for_buying": cint(for_buying),
            }
        )
        doc.insert(ignore_permissions=True)

    frappe.db.commit()
    return {
        "ok": True,
        "name": doc.name,
        "exchange_rate": doc.exchange_rate,
        "message": _("Exchange rate saved."),
    }


@frappe.whitelist()
def delete_exchange_rate(name):
    """Remove a manual exchange rate row."""
    _assert_currency_settings_permission()
    if not frappe.db.exists("Currency Exchange", name):
        frappe.throw(_("Exchange rate {0} not found.").format(name))
    frappe.delete_doc("Currency Exchange", name, ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True, "message": _("Exchange rate deleted.")}

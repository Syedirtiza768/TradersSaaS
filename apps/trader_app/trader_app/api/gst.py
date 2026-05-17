# -*- coding: utf-8 -*-
"""Trader App — GST Settings API.

Manages GST (General Sales Tax) configuration and compliance
for Pakistan, defaulting to Punjab province tax rates.

Punjab Pakistan GST structure:
  - Standard GST rate: 18% (Federal + Provincial combined)
  - Further Tax: 3% (for unregistered persons)
  - Reduced rate: 10% (specific categories)
  - Exempt: 0%

These rates are stored in ERPNext's Sales Taxes and Charges Template
DocType and managed through this API.
"""

from __future__ import unicode_literals

import json

import frappe
from frappe import _
from trader_app.api.company import resolve_active_company
from frappe.utils import flt, cint


# ────────────────────────────────────────────────────────────────
# GST DEFAULTS — Punjab, Pakistan
# ────────────────────────────────────────────────────────────────

PUNJAB_GST_TEMPLATES = [
    {
        "title": "GST 18% - Punjab Standard",
        "tax_rate": 18.0,
        "description": "General Sales Tax @ 18% (Federal + Provincial) — Punjab, Pakistan",
        "is_default": 1,
    },
    {
        "title": "GST 10% - Reduced Rate",
        "tax_rate": 10.0,
        "description": "Reduced GST rate @ 10% — select categories per FBR schedule",
        "is_default": 0,
    },
    {
        "title": "Further Tax 3% - Unregistered",
        "tax_rate": 3.0,
        "description": "Further Tax @ 3% for supplies to unregistered persons",
        "is_default": 0,
    },
    {
        "title": "GST Exempt",
        "tax_rate": 0.0,
        "description": "Zero-rated / Exempt supplies — no GST applicable",
        "is_default": 0,
    },
]


# ────────────────────────────────────────────────────────────────
# 1.  READ GST SETTINGS
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_gst_settings(company=None):
    """Return the GST tax templates and configuration for the company."""
    company = resolve_active_company(company)
    if not company:
        return {"templates": [], "company": None}

    abbr = frappe.get_cached_value("Company", company, "abbr")

    # Fetch Sales Taxes and Charges Templates
    sales_templates = frappe.db.sql("""
        SELECT t.name, t.title, t.is_default, t.disabled,
               tc.rate, tc.charge_type, tc.description, tc.account_head
        FROM `tabSales Taxes and Charges Template` t
        LEFT JOIN `tabSales Taxes and Charges` tc ON tc.parent = t.name
        WHERE t.company = %(company)s
        ORDER BY t.is_default DESC, t.title ASC
    """, {"company": company}, as_dict=True)

    # Fetch Purchase Taxes and Charges Templates
    purchase_templates = frappe.db.sql("""
        SELECT t.name, t.title, t.is_default, t.disabled,
               tc.rate, tc.charge_type, tc.description, tc.account_head
        FROM `tabPurchase Taxes and Charges Template` t
        LEFT JOIN `tabPurchase Taxes and Charges` tc ON tc.parent = t.name
        WHERE t.company = %(company)s
        ORDER BY t.is_default DESC, t.title ASC
    """, {"company": company}, as_dict=True)

    # Group by template name
    sales_grouped = _group_templates(sales_templates)
    purchase_grouped = _group_templates(purchase_templates)

    # Read the GST config from cache or defaults
    gst_config = _read_gst_config(company)

    return {
        "company": company,
        "abbr": abbr,
        "sales_templates": sales_grouped,
        "purchase_templates": purchase_grouped,
        "config": gst_config,
    }


def _group_templates(rows):
    """Group tax charge rows by their parent template."""
    grouped = {}
    for row in rows:
        name = row["name"]
        if name not in grouped:
            grouped[name] = {
                "name": name,
                "title": row["title"],
                "is_default": row["is_default"],
                "disabled": row["disabled"],
                "taxes": [],
            }
        if row.get("rate") is not None:
            grouped[name]["taxes"].append({
                "rate": row["rate"],
                "charge_type": row["charge_type"],
                "description": row["description"],
                "account_head": row["account_head"],
            })
    return list(grouped.values())


def _gst_config_key(company):
    return f"trader_gst_config::{company}"


def _read_gst_config(company):
    cached = frappe.cache().get_value(_gst_config_key(company))
    if cached:
        if isinstance(cached, bytes):
            cached = cached.decode("utf-8")
        return json.loads(cached)

    return {
        "default_sales_tax_template": "",
        "default_purchase_tax_template": "",
        "auto_apply_tax": 1,
        "region": "Punjab",
        "country": "Pakistan",
        "gst_registered": 1,
        "ntn_number": "",
        "strn_number": "",
    }


# ────────────────────────────────────────────────────────────────
# 2.  SAVE GST SETTINGS
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def save_gst_settings(company=None, config=None):
    """Save GST configuration for the company."""
    if frappe.session.user == 'Guest' or not any(
        r in frappe.get_roles()
        for r in ('System Manager', 'Trader Admin', 'Trader Accountant', 'Trader Finance Manager')
    ):
        frappe.throw(_('Not permitted'), frappe.PermissionError)
    company = resolve_active_company(company)
    if isinstance(config, str):
        config = json.loads(config)
    config = config or {}

    cleaned = {
        "default_sales_tax_template": config.get("default_sales_tax_template", ""),
        "default_purchase_tax_template": config.get("default_purchase_tax_template", ""),
        "auto_apply_tax": cint(config.get("auto_apply_tax", 1)),
        "region": config.get("region", "Punjab"),
        "country": config.get("country", "Pakistan"),
        "gst_registered": cint(config.get("gst_registered", 1)),
        "ntn_number": config.get("ntn_number", ""),
        "strn_number": config.get("strn_number", ""),
    }

    frappe.cache().set_value(_gst_config_key(company), json.dumps(cleaned))
    return {"ok": True, "message": "GST settings saved.", "config": cleaned}


# ────────────────────────────────────────────────────────────────
# 3.  SEED PUNJAB GST TEMPLATES
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def seed_punjab_gst_templates(company=None):
    """Create the default Punjab GST tax templates if they don't exist.
    Restricted to admin and finance roles.
    """
    if frappe.session.user == 'Guest' or not any(
        r in frappe.get_roles()
        for r in ('System Manager', 'Trader Admin', 'Trader Accountant', 'Trader Finance Manager')
    ):
        frappe.throw(_('Not permitted'), frappe.PermissionError)
    company = resolve_active_company(company)
    if not company:
        frappe.throw(_("No company found — create a company first"))

    abbr = frappe.get_cached_value("Company", company, "abbr")
    created = []

    # Ensure tax account exists
    tax_account = _ensure_tax_account(company, abbr)

    for tmpl in PUNJAB_GST_TEMPLATES:
        # Sales template
        sales_name = f"{tmpl['title']} - {abbr}"
        if not frappe.db.exists("Sales Taxes and Charges Template", sales_name):
            doc = frappe.new_doc("Sales Taxes and Charges Template")
            doc.title = tmpl["title"]
            doc.name = sales_name
            doc.company = company
            doc.is_default = tmpl["is_default"]
            doc.append("taxes", {
                "charge_type": "On Net Total",
                "account_head": tax_account,
                "rate": tmpl["tax_rate"],
                "description": tmpl["description"],
            })
            doc.insert(ignore_permissions=True)
            created.append(sales_name)

        # Purchase template
        purchase_name = f"{tmpl['title']} (Purchase) - {abbr}"
        if not frappe.db.exists("Purchase Taxes and Charges Template", purchase_name):
            doc = frappe.new_doc("Purchase Taxes and Charges Template")
            doc.title = f"{tmpl['title']} (Purchase)"
            doc.name = purchase_name
            doc.company = company
            doc.is_default = tmpl["is_default"]
            doc.append("taxes", {
                "charge_type": "On Net Total",
                "account_head": tax_account,
                "rate": tmpl["tax_rate"],
                "description": tmpl["description"],
            })
            doc.insert(ignore_permissions=True)
            created.append(purchase_name)

    frappe.db.commit()

    # Set the default template in config
    default_sales = f"GST 18% - Punjab Standard - {abbr}"
    default_purchase = f"GST 18% - Punjab Standard (Purchase) - {abbr}"
    config = _read_gst_config(company)
    if not config.get("default_sales_tax_template"):
        config["default_sales_tax_template"] = default_sales
    if not config.get("default_purchase_tax_template"):
        config["default_purchase_tax_template"] = default_purchase
    frappe.cache().set_value(_gst_config_key(company), json.dumps(config))

    return {
        "ok": True,
        "created": created,
        "message": f"Created {len(created)} GST templates for {company}",
    }


def _ensure_tax_account(company, abbr):
    """Make sure a GST tax liability account exists under the company's CoA."""
    account_name = f"GST Payable - {abbr}"
    if frappe.db.exists("Account", account_name):
        return account_name

    # Find parent Duties and Taxes group
    parent = frappe.db.get_value(
        "Account",
        {"company": company, "account_type": "Tax", "is_group": 1},
        "name",
    )
    if not parent:
        parent = frappe.db.get_value(
            "Account",
            {"company": company, "account_name": ["like", "%Duties%Tax%"], "is_group": 1},
            "name",
        )
    if not parent:
        parent = frappe.db.get_value(
            "Account",
            {"company": company, "root_type": "Liability", "is_group": 1},
            "name",
        )

    if parent:
        acc = frappe.new_doc("Account")
        acc.account_name = "GST Payable"
        acc.parent_account = parent
        acc.company = company
        acc.account_type = "Tax"
        acc.is_group = 0
        acc.insert(ignore_permissions=True)
        frappe.db.commit()
        return acc.name

    frappe.throw(_("Could not find a suitable parent account for GST. "
                   "Please create a 'GST Payable' account manually under "
                   "Duties and Taxes."))


# ────────────────────────────────────────────────────────────────
# 4.  GET TAX TEMPLATES FOR DOCUMENT CREATION
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_tax_templates(doctype="Sales", company=None):
    """Return available tax templates for Sales or Purchase documents.

    Each template includes its total_tax_rate (sum of charge rows)
    so the frontend can preview tax amounts before saving.
    """
    company = resolve_active_company(company)

    if doctype == "Purchase":
        template_dt = "Purchase Taxes and Charges Template"
        charge_dt = "Purchase Taxes and Charges"
    else:
        template_dt = "Sales Taxes and Charges Template"
        charge_dt = "Sales Taxes and Charges"

    templates = frappe.get_all(
        template_dt,
        filters={"company": company, "disabled": 0},
        fields=["name", "title", "is_default"],
        order_by="is_default desc, title asc",
    )

    # Enrich each template with total_tax_rate from its charge rows
    for tpl in templates:
        charges = frappe.get_all(
            charge_dt,
            filters={"parent": tpl["name"]},
            fields=["rate", "included_in_print_rate"],
        )
        tpl["total_tax_rate"] = sum(flt(c.rate) for c in charges)
        tpl["included_in_print_rate"] = (
            charges[0].included_in_print_rate if charges else 0
        )

    return {"templates": templates}

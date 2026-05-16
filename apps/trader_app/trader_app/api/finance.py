# -*- coding: utf-8 -*-
"""Trader App — Finance API.

Whitelisted endpoints for the Finance module:
- Payment Entry management
- Journal Entry
- Outstanding balance queries
"""

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import nowdate, flt, cint


# ────────────────────────────────────────────────────────────────
# 1.  PAYMENT ENTRIES
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_payment_entries(company=None, party_type=None, party=None,
                        payment_type=None, from_date=None, to_date=None,
                        page=1, page_size=20, search=None):
    """Paginated Payment Entries."""
    company = company or _default_company()
    page = cint(page) or 1
    page_size = min(cint(page_size) or 20, 100)
    offset = (page - 1) * page_size

    conditions = ["pe.company = %(company)s", "pe.docstatus IN (0, 1)"]
    params = {"company": company}

    if party_type:
        conditions.append("pe.party_type = %(party_type)s")
        params["party_type"] = party_type
    if party:
        conditions.append("pe.party = %(party)s")
        params["party"] = party
    if payment_type:
        conditions.append("pe.payment_type = %(payment_type)s")
        params["payment_type"] = payment_type
    if from_date:
        conditions.append("pe.posting_date >= %(from_date)s")
        params["from_date"] = from_date
    if to_date:
        conditions.append("pe.posting_date <= %(to_date)s")
        params["to_date"] = to_date
    if search:
        conditions.append("(pe.name LIKE %(search)s OR pe.party LIKE %(search)s)")
        params["search"] = f"%{search}%"

    where = " AND ".join(conditions)

    total = frappe.db.sql(
        f"SELECT COUNT(*) FROM `tabPayment Entry` pe WHERE {where}", params
    )[0][0]

    rows = frappe.db.sql(f"""
        SELECT pe.name, pe.posting_date, pe.payment_type,
               pe.party_type, pe.party, pe.party_name,
               pe.paid_amount, pe.received_amount,
               pe.mode_of_payment, pe.reference_no,
               pe.docstatus
        FROM `tabPayment Entry` pe
        WHERE {where}
        ORDER BY pe.posting_date DESC, pe.creation DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


@frappe.whitelist()
def get_payment_entry_detail(name):
    """Full Payment Entry with references."""
    doc = frappe.get_doc("Payment Entry", name)
    doc.check_permission("read")
    return doc.as_dict()


@frappe.whitelist()
def get_payment_entry_setup(company=None):
    """Lookup payment modes, settlement accounts, and defaults for the form."""
    company = company or _default_company()

    _ensure_payment_modes(company)

    modes = frappe.get_all(
        "Mode of Payment",
        filters={"enabled": 1},
        fields=["name", "type"],
        order_by="name asc",
    )

    settlement_accounts = _get_settlement_accounts(company)
    cash_account = _get_default_account(company, "Cash")
    bank_account = _get_default_account(company, "Bank") or cash_account

    mode_accounts = {}
    for mode in modes:
        mapped = _get_mode_of_payment_account(company, mode.name)
        if mapped:
            mode_accounts[mode.name] = mapped

    return {
        "modes": modes,
        "settlement_accounts": settlement_accounts,
        "mode_accounts": mode_accounts,
        "defaults": {
            "receive_account": cash_account or bank_account,
            "pay_account": cash_account or bank_account,
            "bank_account": bank_account,
            "cash_account": cash_account,
        },
    }


# ────────────────────────────────────────────────────────────────
# 2.  CREATE PAYMENT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def create_payment_entry(payment_type, party_type, party, amount,
                         company=None, posting_date=None,
                         reference_doctype=None, reference_name=None,
                         mode_of_payment=None, paid_to=None, paid_from=None,
                         reference_no=None, reference_date=None):
    """Create a Payment Entry from the UI."""
    company = company or _default_company()
    mode_of_payment = _resolve_payment_mode(mode_of_payment)
    party = _resolve_party(party_type, party)

    pe = frappe.new_doc("Payment Entry")
    pe.company = company
    pe.payment_type = payment_type
    pe.party_type = party_type
    pe.party = party
    pe.posting_date = posting_date or nowdate()
    pe.paid_amount = flt(amount)
    pe.received_amount = flt(amount)
    if mode_of_payment:
        pe.mode_of_payment = mode_of_payment

    settlement_account, party_account = _apply_payment_accounts(
        pe, company, payment_type, party_type, party,
        mode_of_payment, paid_to, paid_from,
    )

    if reference_doctype and reference_name:
        pe.append("references", {
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "allocated_amount": flt(amount),
        })

    _apply_bank_reference_fields(
        pe,
        reference_no=reference_no,
        reference_date=reference_date,
        fallback_reference=reference_name,
    )

    pe.insert(ignore_permissions=False)
    return {
        "name": pe.name,
        "status": "Draft",
        "settlement_account": settlement_account,
    }


@frappe.whitelist()
def record_invoice_payment(reference_doctype, reference_name, amount,
                           mode_of_payment=None, settlement_account=None,
                           posting_date=None, reference_no=None,
                           reference_date=None, submit=1):
    """Record and optionally submit a payment against an invoice into a bank/cash account."""
    if reference_doctype not in ("Sales Invoice", "Purchase Invoice"):
        frappe.throw(_("Only Sales Invoice and Purchase Invoice are supported."))

    invoice = frappe.get_doc(reference_doctype, reference_name)
    invoice.check_permission("read")

    if invoice.docstatus != 1:
        frappe.throw(_("Invoice must be submitted before recording a payment."))

    outstanding = flt(invoice.outstanding_amount)
    pay_amount = flt(amount)
    if pay_amount <= 0:
        frappe.throw(_("Enter a valid payment amount."))
    if pay_amount > outstanding + 0.005:
        frappe.throw(
            _("Payment amount {0} exceeds outstanding {1}.").format(pay_amount, outstanding)
        )

    company = invoice.company
    if reference_doctype == "Sales Invoice":
        payment_type = "Receive"
        party_type = "Customer"
        party = invoice.customer
    else:
        payment_type = "Pay"
        party_type = "Supplier"
        party = invoice.supplier

    mode_of_payment = _resolve_payment_mode(mode_of_payment)
    pe = frappe.new_doc("Payment Entry")
    pe.company = company
    pe.payment_type = payment_type
    pe.party_type = party_type
    pe.party = party
    pe.posting_date = posting_date or nowdate()
    pe.paid_amount = pay_amount
    pe.received_amount = pay_amount
    if mode_of_payment:
        pe.mode_of_payment = mode_of_payment

    applied_account, _party_account = _apply_payment_accounts(
        pe, company, payment_type, party_type, party, mode_of_payment,
        paid_to=settlement_account if payment_type == "Receive" else None,
        paid_from=settlement_account if payment_type == "Pay" else None,
    )

    pe.append("references", {
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "allocated_amount": pay_amount,
    })

    _apply_bank_reference_fields(
        pe,
        reference_no=reference_no,
        reference_date=reference_date,
        fallback_reference=reference_name,
    )

    pe.insert(ignore_permissions=False)

    if cint(submit):
        pe.submit()
        frappe.db.commit()

    invoice.reload()
    return {
        "name": pe.name,
        "status": "Submitted" if cint(submit) else "Draft",
        "settlement_account": applied_account,
        "outstanding_amount": flt(invoice.outstanding_amount),
        "paid_amount": flt(invoice.paid_amount),
    }


@frappe.whitelist()
def submit_payment_entry(name):
    """Submit a draft Payment Entry."""
    doc = frappe.get_doc("Payment Entry", name)
    doc.check_permission("submit")
    doc.submit()
    frappe.db.commit()
    return {"name": doc.name, "status": "Submitted"}


# ────────────────────────────────────────────────────────────────
# 3.  JOURNAL ENTRIES
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_journal_entries(company=None, from_date=None, to_date=None,
                        page=1, page_size=20):
    """Paginated Journal Entries."""
    company = company or _default_company()
    page = cint(page) or 1
    page_size = min(cint(page_size) or 20, 100)
    offset = (page - 1) * page_size

    conditions = ["je.company = %(company)s", "je.docstatus IN (0, 1)"]
    params = {"company": company}

    if from_date:
        conditions.append("je.posting_date >= %(from_date)s")
        params["from_date"] = from_date
    if to_date:
        conditions.append("je.posting_date <= %(to_date)s")
        params["to_date"] = to_date

    where = " AND ".join(conditions)

    total = frappe.db.sql(
        f"SELECT COUNT(*) FROM `tabJournal Entry` je WHERE {where}", params
    )[0][0]

    rows = frappe.db.sql(f"""
        SELECT je.name, je.posting_date, je.voucher_type,
               je.total_debit, je.total_credit,
               je.user_remark, je.docstatus
        FROM `tabJournal Entry` je
        WHERE {where}
        ORDER BY je.posting_date DESC, je.creation DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


@frappe.whitelist()
def get_journal_entry_detail(name):
    """Full Journal Entry with account lines."""
    doc = frappe.get_doc("Journal Entry", name)
    doc.check_permission("read")
    return doc.as_dict()


@frappe.whitelist()
def get_accounts(company=None, search=None, limit=100):
    """Lookup selectable ledger accounts for finance forms."""
    company = company or _default_company()
    limit = min(cint(limit) or 100, 200)

    conditions = ["company = %(company)s", "is_group = 0", "disabled = 0"]
    params = {"company": company, "limit": limit}

    if search:
        conditions.append("(name LIKE %(search)s OR account_name LIKE %(search)s)")
        params["search"] = f"%{search}%"

    where = " AND ".join(conditions)

    rows = frappe.db.sql(f"""
        SELECT name, account_name, account_number, account_type, root_type
        FROM `tabAccount`
        WHERE {where}
        ORDER BY root_type ASC, account_name ASC, name ASC
        LIMIT %(limit)s
    """, params, as_dict=True)

    return rows


@frappe.whitelist()
def create_journal_entry(voucher_type=None, posting_date=None,
                         user_remark=None, accounts=None, company=None):
    """Create a balanced draft Journal Entry from the UI."""
    import json
    if isinstance(accounts, str):
        accounts = json.loads(accounts)

    company = company or _default_company()
    accounts = accounts or []

    if len(accounts) < 2:
        frappe.throw(_("At least two account lines are required."))

    total_debit = 0
    total_credit = 0
    cleaned_accounts = []

    for row in accounts:
        account = row.get("account")
        debit = flt(row.get("debit") or row.get("debit_in_account_currency"))
        credit = flt(row.get("credit") or row.get("credit_in_account_currency"))
        if not account:
            continue
        if debit <= 0 and credit <= 0:
            continue

        total_debit += debit
        total_credit += credit
        cleaned_accounts.append({
            "account": account,
            "debit_in_account_currency": debit,
            "credit_in_account_currency": credit,
            "user_remark": row.get("user_remark") or user_remark,
        })

    if len(cleaned_accounts) < 2:
        frappe.throw(_("Add at least two non-empty account lines."))

    if abs(total_debit - total_credit) > 0.005:
        frappe.throw(_("Total debit and total credit must be equal."))

    je = frappe.new_doc("Journal Entry")
    je.company = company
    je.voucher_type = voucher_type or "Journal Entry"
    je.posting_date = posting_date or nowdate()
    je.user_remark = user_remark

    for row in cleaned_accounts:
        je.append("accounts", row)

    je.insert(ignore_permissions=False)
    return {"name": je.name, "status": "Draft"}


@frappe.whitelist()
def submit_journal_entry(name):
    """Submit a draft Journal Entry."""
    doc = frappe.get_doc("Journal Entry", name)
    doc.check_permission("submit")
    doc.submit()
    frappe.db.commit()
    return {"name": doc.name, "status": "Submitted"}


@frappe.whitelist()
def cancel_payment_entry(name):
    """Cancel a submitted Payment Entry."""
    doc = frappe.get_doc("Payment Entry", name)
    doc.check_permission("cancel")
    doc.cancel()
    frappe.db.commit()
    return {"name": doc.name, "status": "Cancelled"}


@frappe.whitelist()
def cancel_journal_entry(name):
    """Cancel a submitted Journal Entry."""
    doc = frappe.get_doc("Journal Entry", name)
    doc.check_permission("cancel")
    doc.cancel()
    frappe.db.commit()
    return {"name": doc.name, "status": "Cancelled"}


# ────────────────────────────────────────────────────────────────
# 4.  DOCTYPE EVENT HOOKS
# ────────────────────────────────────────────────────────────────

def on_payment_entry_submit(doc, method):
    """Runs on Payment Entry submit — publish realtime event."""
    frappe.publish_realtime(
        "payment_entry_submitted",
        {"payment": doc.name, "party": doc.party, "amount": doc.paid_amount},
        user=frappe.session.user,
    )


# ────────────────────────────────────────────────────────────────
# 5.  OUTSTANDING SUMMARY
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_outstanding_summary(company=None):
    """Receivable + Payable totals."""
    company = company or _default_company()

    receivable = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0) FROM `tabSales Invoice`
        WHERE company = %s AND docstatus = 1 AND outstanding_amount > 0
    """, (company,))[0][0])

    payable = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0) FROM `tabPurchase Invoice`
        WHERE company = %s AND docstatus = 1 AND outstanding_amount > 0
    """, (company,))[0][0])

    return {
        "receivable": receivable,
        "payable": payable,
        "net": receivable - payable,
    }


# ────────────────────────────────────────────────────────────────
#    HELPERS
# ────────────────────────────────────────────────────────────────

def _default_company():
    companies = frappe.get_all("Company", limit=1, pluck="name")
    return (
        frappe.defaults.get_user_default("Company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
        or (companies[0] if companies else None)
    )


def _get_default_account(company, account_type):
    """Get default cash or bank account for the company."""
    account = frappe.db.get_value(
        "Account",
        filters={"company": company, "account_type": account_type, "is_group": 0},
        fieldname="name",
    )
    if not account:
        account = frappe.db.get_value(
            "Account",
            filters={"company": company, "account_type": "Bank", "is_group": 0},
            fieldname="name",
        )
    return account


def _get_settlement_accounts(company):
    """Selectable cash and bank GL accounts for payment settlement."""
    return frappe.get_all(
        "Account",
        filters={
            "company": company,
            "account_type": ["in", ["Cash", "Bank"]],
            "is_group": 0,
            "disabled": 0,
        },
        fields=["name", "account_name", "account_type", "account_number"],
        order_by="account_type asc, account_name asc, name asc",
    )


def _get_mode_of_payment_account(company, mode_of_payment):
    return frappe.db.get_value(
        "Mode of Payment Account",
        {"parent": mode_of_payment, "company": company},
        "default_account",
    )


def _resolve_settlement_account(company, payment_type, mode_of_payment=None,
                                paid_to=None, paid_from=None):
    """Resolve the cash/bank account for Receive (paid_to) or Pay (paid_from)."""
    explicit = paid_to if payment_type == "Receive" else paid_from
    if explicit:
        if frappe.db.exists("Account", explicit):
            meta = frappe.db.get_value(
                "Account", explicit, ["company", "account_type", "is_group", "disabled"], as_dict=True
            )
            if (
                meta
                and meta.company == company
                and meta.account_type in ("Cash", "Bank")
                and not meta.is_group
                and not meta.disabled
            ):
                return explicit

    if mode_of_payment:
        mapped = _get_mode_of_payment_account(company, mode_of_payment)
        if mapped:
            return mapped
        mode_type = frappe.db.get_value("Mode of Payment", mode_of_payment, "type")
        account_type = "Bank" if mode_type == "Bank" else "Cash"
        account = _get_default_account(company, account_type)
        if account:
            return account

    return _get_default_account(company, "Cash") or _get_default_account(company, "Bank")


def _resolve_party(party_type, party):
    """Accept party doc name or display name from deep links."""
    if not party:
        frappe.throw(_("Party is required."))

    if frappe.db.exists(party_type, party):
        return party

    name_field = "customer_name" if party_type == "Customer" else "supplier_name"
    resolved = frappe.db.get_value(party_type, {name_field: party}, "name")
    if resolved:
        return resolved

    resolved = frappe.db.get_value(
        party_type,
        {name_field: ["like", f"%{party}%"]},
        "name",
    )
    if resolved:
        return resolved

    frappe.throw(_("{0} {1} was not found.").format(party_type, party))


def _get_party_ledger_account(company, party_type, party):
    from erpnext.accounts.party import get_party_account

    return get_party_account(party_type, party, company)


def _apply_bank_reference_fields(pe, reference_no=None, reference_date=None,
                                 fallback_reference=None):
    """ERPNext requires reference_no and reference_date when settlement account is Bank."""
    bank_account = pe.paid_to if pe.payment_type == "Receive" else pe.paid_from
    if not bank_account:
        return

    if frappe.get_cached_value("Account", bank_account, "account_type") != "Bank":
        return

    pe.reference_date = reference_date or pe.reference_date or pe.posting_date or nowdate()

    if reference_no:
        pe.reference_no = reference_no
    elif pe.reference_no:
        pass
    elif fallback_reference:
        pe.reference_no = fallback_reference
    elif pe.get("references"):
        pe.reference_no = pe.references[0].reference_name
    else:
        pe.reference_no = f"{pe.payment_type}-{pe.party}-{pe.posting_date}"


def _apply_payment_accounts(pe, company, payment_type, party_type, party,
                            mode_of_payment=None, paid_to=None, paid_from=None):
    """Set bank/cash and receivable/payable accounts before insert."""
    settlement_account = _resolve_settlement_account(
        company, payment_type, mode_of_payment, paid_to, paid_from
    )
    if not settlement_account:
        frappe.throw(_("No cash or bank account found for company {0}.").format(company))

    party_account = _get_party_ledger_account(company, party_type, party)

    if payment_type == "Receive":
        pe.paid_to = settlement_account
        pe.paid_from = party_account
    else:
        pe.paid_from = settlement_account
        pe.paid_to = party_account

    return settlement_account, party_account


def _apply_settlement_account(pe, company, payment_type, mode_of_payment=None,
                              paid_to=None, paid_from=None):
    settlement_account, _party_account = _apply_payment_accounts(
        pe, company, payment_type, pe.party_type, pe.party,
        mode_of_payment, paid_to, paid_from,
    )
    return settlement_account


def _ensure_payment_modes(company=None):
    """Create standard modes and map them to company settlement accounts when possible."""
    standard_modes = [
        ("Cash", "Cash"),
        ("Bank Transfer", "Bank"),
        ("Cheque", "Bank"),
        ("Wire Transfer", "Bank"),
    ]

    created = False
    for mode_name, mode_type in standard_modes:
        if not frappe.db.exists("Mode of Payment", mode_name):
            doc = frappe.new_doc("Mode of Payment")
            doc.mode_of_payment = mode_name
            doc.type = mode_type
            doc.enabled = 1
            doc.insert(ignore_permissions=True)
            created = True

    if created:
        frappe.db.commit()

    if not company:
        return

    cash_account = _get_default_account(company, "Cash")
    bank_account = _get_default_account(company, "Bank")
    bank_accounts = [
        row.name for row in _get_settlement_accounts(company) if row.account_type == "Bank"
    ]

    mode_account_map = {
        "Cash": cash_account,
        "Bank Transfer": bank_accounts[0] if bank_accounts else bank_account,
        "Cheque": bank_accounts[1] if len(bank_accounts) > 1 else (bank_account or cash_account),
        "Wire Transfer": bank_accounts[-1] if bank_accounts else (bank_account or cash_account),
    }

    for mode_name, default_account in mode_account_map.items():
        if not default_account or not frappe.db.exists("Mode of Payment", mode_name):
            continue
        existing = frappe.db.get_value(
            "Mode of Payment Account",
            {"parent": mode_name, "company": company},
            "name",
        )
        if existing:
            frappe.db.set_value(
                "Mode of Payment Account", existing, "default_account", default_account
            )
        else:
            mop = frappe.get_doc("Mode of Payment", mode_name)
            mop.append("accounts", {
                "company": company,
                "default_account": default_account,
            })
            mop.save(ignore_permissions=True)

    frappe.db.commit()


def _resolve_payment_mode(mode_of_payment):
    """Return a valid Mode of Payment name, falling back to the first available."""
    if mode_of_payment and frappe.db.exists("Mode of Payment", mode_of_payment):
        return mode_of_payment

    # Prefer "Cash", otherwise take the first enabled mode
    if frappe.db.exists("Mode of Payment", "Cash"):
        return "Cash"

    first = frappe.db.get_value("Mode of Payment", {"enabled": 1}, "name", order_by="name asc")
    return first  # may be None if table is still empty — ERPNext will use its own default

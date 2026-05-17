# -*- coding: utf-8 -*-
"""Trader App — Document Printing / PDF Generation API.

Generates printable document views for:
  - Quotations
  - Sales Orders
  - Sales Invoices (Tax Invoice, Commercial Invoice, Proforma Invoice)

Supports two viewing modes:
  - External (client-facing): grouped/bundle items show only the
    overarching description
  - Internal (staff-facing): shows both bundle description AND
    individual sub-items
"""

from __future__ import unicode_literals

import json

import frappe
from frappe import _
from frappe.utils import flt, cint, nowdate, getdate, fmt_money

from trader_app.api.company import assert_document_company_access, resolve_active_company
from trader_app.api.invoice_types import print_format_for_doc, print_title_for_format


# ────────────────────────────────────────────────────────────────
# 1.  DOCUMENT DATA FOR PRINT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_print_data(doctype, name, view_mode="external", doc_format="tax_invoice"):
    """Return structured data for printing a document.

    Parameters
    ----------
    doctype : str     — "Quotation", "Sales Order", or "Sales Invoice"
    name : str        — Document name
    view_mode : str   — "external" or "internal"
    doc_format : str  — "tax_invoice", "commercial_invoice", or "proforma_invoice"
    """
    if doctype not in ("Quotation", "Sales Order", "Sales Invoice", "Delivery Note", "Purchase Invoice"):
        frappe.throw(_("Unsupported document type: {0}").format(doctype))

    doc = frappe.get_doc(doctype, name)
    doc.check_permission("read")
    assert_document_company_access(doc.company)

    if not doc_format or doc_format == "auto":
        doc_format = print_format_for_doc(doc)

    company = doc.company or resolve_active_company()
    company_doc = frappe.get_doc("Company", company)

    # Build structured items — applying view mode filtering
    items = _build_print_items(doc, view_mode)

    # Company info
    company_info = {
        "name": company_doc.name,
        "abbr": company_doc.abbr,
        "address": _get_company_address(company),
        "phone": company_doc.phone_no or "",
        "email": company_doc.email or "",
        "website": company_doc.website or "",
        "tax_id": company_doc.tax_id or "",
        "country": company_doc.country or "Pakistan",
    }

    # Customer/Party info
    party_info = _get_party_info(doc, doctype)

    # Taxes
    taxes = []
    if hasattr(doc, "taxes") and doc.taxes:
        for tax in doc.taxes:
            taxes.append({
                "description": tax.description or "",
                "rate": flt(tax.rate),
                "tax_amount": flt(tax.tax_amount),
                "total": flt(tax.total),
                "charge_type": tax.charge_type or "",
            })

    # Build the document title based on format
    doc_title = _get_document_title(doctype, doc_format, doc.name)

    bank_payment = _get_bank_payment_info(doc, doctype)

    return {
        "doc_title": doc_title,
        "doc_format": doc_format,
        "view_mode": view_mode,
        "doctype": doctype,
        "name": doc.name,
        "status": _get_doc_status(doc),
        "date": str(doc.posting_date if hasattr(doc, "posting_date") else doc.transaction_date),
        "due_date": str(getattr(doc, "due_date", "") or getattr(doc, "valid_till", "") or ""),
        "currency": doc.currency or "PKR",
        "company": company_info,
        "party": party_info,
        "items": items,
        "taxes": taxes,
        "net_total": flt(doc.net_total),
        "total_taxes": flt(getattr(doc, "total_taxes_and_charges", 0)),
        "grand_total": flt(doc.grand_total),
        "rounded_total": flt(getattr(doc, "rounded_total", 0)),
        "outstanding_amount": flt(getattr(doc, "outstanding_amount", 0)),
        "paid_amount": flt(getattr(doc, "paid_amount", 0)),
        "in_words": getattr(doc, "in_words", "") or "",
        "terms": getattr(doc, "terms", "") or "",
        "remarks": getattr(doc, "remarks", "") or "",
        "printed_on": nowdate(),
        "bank_payment": bank_payment,
    }


def _build_print_items(doc, view_mode):
    """Build the items list for printing.

    In external mode, bundled items show only the bundle description.
    In internal mode, both the bundle and sub-items are shown.
    """
    items = []
    if not hasattr(doc, "items"):
        return items

    for item in doc.items:
        item_data = {
            "item_code": item.item_code or "",
            "item_name": item.item_name or "",
            "description": item.description or item.item_name or "",
            "qty": flt(item.qty),
            "rate": flt(item.rate),
            "amount": flt(item.amount),
            "uom": getattr(item, "uom", "") or getattr(item, "stock_uom", "") or "Nos",
            "is_bundle": 0,
            "bundle_items": [],
        }

        # Check if this item has bundle metadata in custom fields
        bundle_name = getattr(item, "bundle_ref", None) or ""
        bundle_desc = getattr(item, "bundle_description", None) or ""

        if bundle_name or bundle_desc:
            item_data["is_bundle"] = 1
            item_data["bundle_description"] = bundle_desc or item_data["description"]

            if view_mode == "internal":
                # Load sub-items from the bundle reference
                if bundle_name and frappe.db.exists("Item Bundle", bundle_name):
                    bundle_doc = frappe.get_doc("Item Bundle", bundle_name)
                    item_data["bundle_items"] = [
                        {
                            "item_code": bi.item_code,
                            "qty": flt(bi.qty),
                            "rate": flt(bi.rate),
                            "amount": flt(bi.amount),
                        }
                        for bi in bundle_doc.items
                    ]
            elif view_mode == "external":
                # External mode: override description to show only bundle desc
                item_data["description"] = bundle_desc or item_data["description"]
                item_data["item_name"] = bundle_desc or item_data["item_name"]

        items.append(item_data)

    return items


def _get_party_info(doc, doctype):
    """Extract customer/party info from the document."""
    if doctype == "Quotation":
        party_name = doc.party_name or ""
        party_display = doc.customer_name or party_name
        link_doctype = "Customer"
    elif doctype == "Purchase Invoice":
        party_name = doc.supplier or ""
        party_display = doc.supplier_name or party_name
        link_doctype = "Supplier"
    else:
        party_name = doc.customer or ""
        party_display = doc.customer_name or party_name
        link_doctype = "Customer"

    address = ""
    if party_name:
        # Get primary address
        addr = frappe.db.get_value(
            "Dynamic Link",
            {"link_doctype": link_doctype, "link_name": party_name, "parenttype": "Address"},
            "parent",
        )
        if addr:
            addr_doc = frappe.get_doc("Address", addr)
            parts = [
                addr_doc.address_line1 or "",
                addr_doc.address_line2 or "",
                addr_doc.city or "",
                addr_doc.state or "",
                addr_doc.country or "",
            ]
            address = ", ".join(p for p in parts if p)

    return {
        "name": party_name,
        "display_name": party_display,
        "address": address,
        "tax_id": "",
    }


def _get_bank_payment_info(doc, doctype):
    """Preferred bank account for customer remittance (Sales Invoice)."""
    if doctype != "Sales Invoice":
        return None
    account = getattr(doc, "preferred_bank_account", None) or ""
    if not account or not frappe.db.exists("Account", account):
        return None

    account_name = frappe.get_cached_value("Account", account, "account_name") or account
    info = {
        "account": account,
        "account_name": account_name,
        "bank": "",
        "iban": "",
        "branch_code": "",
        "account_no": "",
    }

    if frappe.db.has_column("Account", "account_number"):
        info["account_no"] = frappe.get_cached_value("Account", account, "account_number") or ""

    if frappe.db.exists("DocType", "Bank Account"):
        bank_row = frappe.db.get_value(
            "Bank Account",
            {"account": account, "is_company_account": 1},
            ["bank", "bank_account_no", "iban", "branch_code"],
            as_dict=True,
        )
        if bank_row:
            info["bank"] = bank_row.get("bank") or ""
            info["account_no"] = info["account_no"] or bank_row.get("bank_account_no") or ""
            info["iban"] = bank_row.get("iban") or ""
            info["branch_code"] = bank_row.get("branch_code") or ""

    return info


def _get_company_address(company):
    """Get the company's primary address."""
    addr = frappe.db.get_value(
        "Dynamic Link",
        {"link_doctype": "Company", "link_name": company, "parenttype": "Address"},
        "parent",
    )
    if addr:
        addr_doc = frappe.get_doc("Address", addr)
        parts = [
            addr_doc.address_line1 or "",
            addr_doc.address_line2 or "",
            addr_doc.city or "",
            addr_doc.state or "",
            addr_doc.country or "",
        ]
        return ", ".join(p for p in parts if p)
    return ""


def _get_document_title(doctype, doc_format, doc_name):
    """Return the appropriate document title based on format."""
    title = print_title_for_format(doc_format, doctype)
    if title:
        return title
    if doctype == "Quotation":
        return "QUOTATION"
    if doctype == "Sales Order":
        return "SALES ORDER"
    if doctype == "Delivery Note":
        return "DELIVERY CHALLAN"
    return "INVOICE"


def _get_doc_status(doc):
    """Return a human-readable status."""
    if doc.docstatus == 0:
        return "Draft"
    if doc.docstatus == 2:
        return "Cancelled"
    if hasattr(doc, "status") and doc.status:
        return doc.status
    return "Submitted"

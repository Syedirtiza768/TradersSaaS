# -*- coding: utf-8 -*-
"""Trader App — Invoice / document classification for Pakistan trading workflows.

Maps UI-facing document types to ERPNext doctypes, tax templates, and print titles.
"""

from __future__ import unicode_literals

import frappe
from frappe.utils import cint


# Values stored on Custom Field `trader_invoice_type`
SALES_INVOICE_TYPES = (
    "Tax Invoice",
    "Commercial Invoice",
    "Non-GST Invoice",
    "Bill of Supply",
    "Credit Note",
)

PURCHASE_INVOICE_TYPES = (
    "Tax Invoice",
    "Commercial Invoice",
    "Non-GST Invoice",
    "Bill of Supply",
    "Debit Note",
)

QUOTATION_TYPES = (
    "Quotation",
    "Proforma Invoice",
)

DELIVERY_NOTE_TYPES = (
    "Delivery Challan",
)


def get_document_catalog(side="sales"):
    """Return document types available in the UI for sales or purchases."""
    if side == "purchases":
        return [
            _catalog_entry(
                "tax_invoice",
                "Tax Invoice",
                "Purchase Invoice",
                "Registered purchase with GST/sales tax",
                "/purchases/new?type=tax_invoice",
            ),
            _catalog_entry(
                "commercial_invoice",
                "Commercial Invoice",
                "Purchase Invoice",
                "Supplier bill without tax lines",
                "/purchases/new?type=commercial_invoice",
            ),
            _catalog_entry(
                "non_gst_invoice",
                "Non-GST Invoice",
                "Purchase Invoice",
                "Purchase with no GST charged",
                "/purchases/new?type=non_gst_invoice",
            ),
            _catalog_entry(
                "bill_of_supply",
                "Bill of Supply",
                "Purchase Invoice",
                "Exempt / zero-rated purchase documentation",
                "/purchases/new?type=bill_of_supply",
            ),
            _catalog_entry(
                "debit_note",
                "Debit Note",
                "Purchase Invoice",
                "Return or adjustment against a purchase invoice",
                "/purchases/returns/new",
            ),
        ]

    return [
        _catalog_entry(
            "tax_invoice",
            "Tax Invoice",
            "Sales Invoice",
            "GST/sales tax invoice for registered sellers",
            "/sales/new?type=tax_invoice",
        ),
        _catalog_entry(
            "commercial_invoice",
            "Commercial Invoice",
            "Sales Invoice",
            "Bill of sale without tax (e.g. unregistered)",
            "/sales/new?type=commercial_invoice",
        ),
        _catalog_entry(
            "non_gst_invoice",
            "Non-GST Invoice",
            "Sales Invoice",
            "Sale with no GST on the document",
            "/sales/new?type=non_gst_invoice",
        ),
        _catalog_entry(
            "bill_of_supply",
            "Bill of Supply",
            "Sales Invoice",
            "Exempt supplies at 0% with proper labeling",
            "/sales/new?type=bill_of_supply",
        ),
        _catalog_entry(
            "credit_note",
            "Credit Note",
            "Sales Invoice",
            "Sales return against an earlier invoice",
            "/sales/returns/new",
        ),
        _catalog_entry(
            "proforma_invoice",
            "Proforma Invoice",
            "Quotation",
            "Non-binding quote before billing",
            "/sales/proforma/new",
        ),
        _catalog_entry(
            "delivery_challan",
            "Delivery Challan",
            "Delivery Note",
            "Goods dispatched without billing (or before invoice)",
            "/sales/challans/new",
        ),
    ]


def _catalog_entry(key, label, doctype, description, route):
    return {
        "key": key,
        "label": label,
        "doctype": doctype,
        "description": description,
        "route": route,
    }


def normalize_type_key(invoice_type=None, is_return=0, doctype=None):
    """Map API key or flags to stored Select label."""
    if cint(is_return):
        if doctype == "Purchase Invoice":
            return "Debit Note"
        return "Credit Note"

    key = (invoice_type or "tax_invoice").strip().lower().replace(" ", "_").replace("-", "_")
    mapping = {
        "tax_invoice": "Tax Invoice",
        "tax": "Tax Invoice",
        "gst_invoice": "Tax Invoice",
        "gst": "Tax Invoice",
        "commercial_invoice": "Commercial Invoice",
        "commercial": "Commercial Invoice",
        "non_gst_invoice": "Non-GST Invoice",
        "non_gst": "Non-GST Invoice",
        "bill_of_supply": "Bill of Supply",
        "bill_of_supply_invoice": "Bill of Supply",
        "credit_note": "Credit Note",
        "debit_note": "Debit Note",
        "proforma_invoice": "Proforma Invoice",
        "proforma": "Proforma Invoice",
        "delivery_challan": "Delivery Challan",
        "delivery_note": "Delivery Challan",
        "challan": "Delivery Challan",
        "quotation": "Quotation",
    }
    return mapping.get(key, "Tax Invoice")


def resolve_sales_taxes(company, invoice_type_key, taxes_and_charges=None):
    """Pick tax template from invoice type when caller did not pass one."""
    if taxes_and_charges:
        return taxes_and_charges

    key = (invoice_type_key or "tax_invoice").strip().lower()
    if key in ("commercial_invoice", "commercial", "non_gst_invoice", "non_gst"):
        return None

    if key in ("bill_of_supply", "bill_of_supply_invoice"):
        return _find_template(company, "Sales", prefer_titles=("GST Exempt", "Exempt", "0%"))

    return _default_sales_tax_template(company)


def resolve_purchase_taxes(company, invoice_type_key, taxes_and_charges=None):
    if taxes_and_charges:
        return taxes_and_charges

    key = (invoice_type_key or "tax_invoice").strip().lower()
    if key in ("commercial_invoice", "commercial", "non_gst_invoice", "non_gst"):
        return None

    if key in ("bill_of_supply", "bill_of_supply_invoice"):
        return _find_template(company, "Purchase", prefer_titles=("GST Exempt", "Exempt", "0%"))

    return _default_purchase_tax_template(company)


def set_trader_invoice_type(doc, invoice_type=None, is_return=0):
    label = normalize_type_key(invoice_type, is_return=is_return, doctype=doc.doctype)
    if frappe.db.has_column(doc.doctype, "trader_invoice_type"):
        doc.trader_invoice_type = label
    return label


def print_format_for_doc(doc):
    """Suggest print format key from stored classification."""
    label = getattr(doc, "trader_invoice_type", None) or ""
    if doc.get("is_return"):
        if doc.doctype == "Purchase Invoice":
            return "debit_note"
        return "credit_note"

    mapping = {
        "Tax Invoice": "tax_invoice",
        "Commercial Invoice": "commercial_invoice",
        "Non-GST Invoice": "commercial_invoice",
        "Bill of Supply": "bill_of_supply",
        "Proforma Invoice": "proforma_invoice",
        "Delivery Challan": "delivery_challan",
        "Quotation": "proforma_invoice",
        "Credit Note": "credit_note",
        "Debit Note": "debit_note",
    }
    return mapping.get(label, "tax_invoice")


def print_title_for_format(doc_format, doctype=None):
    titles = {
        "tax_invoice": "TAX INVOICE",
        "commercial_invoice": "COMMERCIAL INVOICE",
        "non_gst_invoice": "NON-GST INVOICE",
        "bill_of_supply": "BILL OF SUPPLY",
        "proforma_invoice": "PROFORMA INVOICE",
        "delivery_challan": "DELIVERY CHALLAN",
        "credit_note": "CREDIT NOTE",
        "debit_note": "DEBIT NOTE",
    }
    return titles.get(doc_format, "TAX INVOICE")


def _default_sales_tax_template(company):
    from trader_app.api.gst import _read_gst_config

    config = _read_gst_config(company)
    tpl = config.get("default_sales_tax_template")
    if tpl and frappe.db.exists("Sales Taxes and Charges Template", tpl):
        return tpl
    abbr = frappe.get_cached_value("Company", company, "abbr")
    fallback = f"GST 18% - Punjab Standard - {abbr}"
    if frappe.db.exists("Sales Taxes and Charges Template", fallback):
        return fallback
    return _find_template(company, "Sales")


def _default_purchase_tax_template(company):
    from trader_app.api.gst import _read_gst_config

    config = _read_gst_config(company)
    tpl = config.get("default_purchase_tax_template")
    if tpl and frappe.db.exists("Purchase Taxes and Charges Template", tpl):
        return tpl
    abbr = frappe.get_cached_value("Company", company, "abbr")
    fallback = f"GST 18% - Punjab Standard (Purchase) - {abbr}"
    if frappe.db.exists("Purchase Taxes and Charges Template", fallback):
        return fallback
    return _find_template(company, "Purchase")


def _find_template(company, side, prefer_titles=()):
    doctype = "Sales Taxes and Charges Template" if side == "Sales" else "Purchase Taxes and Charges Template"
    abbr = frappe.get_cached_value("Company", company, "abbr")
    for title in prefer_titles:
        name = f"{title} - {abbr}" if side == "Sales" else f"{title} (Purchase) - {abbr}"
        if frappe.db.exists(doctype, name):
            return name
        rows = frappe.get_all(
            doctype,
            filters={"company": company, "disabled": 0},
            or_filters={"title": ["like", f"%{title}%"], "name": ["like", f"%{title}%"]},
            pluck="name",
            limit=1,
        )
        if rows:
            return rows[0]
    rows = frappe.get_all(
        doctype,
        filters={"company": company, "disabled": 0},
        order_by="is_default desc, modified desc",
        pluck="name",
        limit=1,
    )
    return rows[0] if rows else None

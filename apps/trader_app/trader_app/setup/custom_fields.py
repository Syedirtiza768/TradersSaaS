# -*- coding: utf-8 -*-
"""Create Trader custom fields on ERPNext doctypes."""

from __future__ import unicode_literals

import frappe


CUSTOM_FIELDS = [
    {
        "dt": "Sales Invoice",
        "fieldname": "trader_invoice_type",
        "label": "Trader Invoice Type",
        "fieldtype": "Select",
        "options": "\n".join([
            "Tax Invoice",
            "Commercial Invoice",
            "Non-GST Invoice",
            "Bill of Supply",
            "Credit Note",
        ]),
        "insert_after": "customer",
        "in_standard_filter": 1,
        "in_list_view": 1,
    },
    {
        "dt": "Purchase Invoice",
        "fieldname": "trader_invoice_type",
        "label": "Trader Invoice Type",
        "fieldtype": "Select",
        "options": "\n".join([
            "Tax Invoice",
            "Commercial Invoice",
            "Non-GST Invoice",
            "Bill of Supply",
            "Debit Note",
        ]),
        "insert_after": "supplier",
        "in_standard_filter": 1,
        "in_list_view": 1,
    },
    {
        "dt": "Quotation",
        "fieldname": "trader_invoice_type",
        "label": "Trader Document Type",
        "fieldtype": "Select",
        "options": "\nQuotation\nProforma Invoice",
        "insert_after": "party_name",
        "in_standard_filter": 1,
    },
    {
        "dt": "Delivery Note",
        "fieldname": "trader_invoice_type",
        "label": "Trader Document Type",
        "fieldtype": "Select",
        "options": "Delivery Challan",
        "default": "Delivery Challan",
        "insert_after": "customer",
        "in_standard_filter": 1,
        "in_list_view": 1,
    },
    {
        "dt": "Company",
        "fieldname": "trader_multi_currency_enabled",
        "label": "Trader Multi-Currency",
        "fieldtype": "Check",
        "default": "0",
        "insert_after": "default_currency",
        "description": "When enabled, Trader UI allows foreign currency on sales and purchases.",
    },
    {
        "dt": "Company",
        "fieldname": "trader_enabled_currencies",
        "label": "Trader Enabled Currencies",
        "fieldtype": "Small Text",
        "insert_after": "trader_multi_currency_enabled",
        "description": "JSON array of currency codes allowed in Trader UI (base currency is always included).",
    },
    {
        "dt": "Sales Invoice",
        "fieldname": "preferred_bank_account",
        "label": "Preferred Bank Account",
        "fieldtype": "Link",
        "options": "Account",
        "insert_after": "due_date",
        "description": "Bank account shown on the invoice for customer payments.",
    },
]


def ensure_custom_fields():
    """Idempotently create custom fields."""
    for spec in CUSTOM_FIELDS:
        name = f"{spec['dt']}-{spec['fieldname']}"
        if frappe.db.exists("Custom Field", name):
            continue
        doc = frappe.new_doc("Custom Field")
        doc.update(spec)
        doc.module = "Trader"
        doc.insert(ignore_permissions=True)
    frappe.db.commit()

# -*- coding: utf-8 -*-
"""Trader App — Point of sale (counter checkout) API."""

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import nowdate

from trader_app.api.company import resolve_active_company
from trader_app.api.currency import _company_base_currency


@frappe.whitelist()
def get_pos_setup(company=None):
    """Defaults for POS screen: warehouse, currency, optional walk-in customer."""
    company = resolve_active_company(company)
    abbr = frappe.get_cached_value("Company", company, "abbr")
    base_currency = _company_base_currency(company)

    walk_in = frappe.db.get_value("Customer", {"customer_name": "Walk-in Customer"}, "name")
    if not walk_in:
        walk_in = frappe.db.get_value("Customer", {"disabled": 0}, "name", order_by="creation asc")

    return {
        "company": company,
        "default_warehouse": f"Main Warehouse - {abbr}",
        "base_currency": base_currency,
        "default_customer": walk_in,
    }


@frappe.whitelist()
def create_pos_sale(customer, items, company=None, posting_date=None,
                    warehouse=None, currency=None, exchange_rate=None,
                    taxes_and_charges=None, tax_inclusive=0,
                    submit=1, record_payment=0, payment_amount=None,
                    mode_of_payment=None, settlement_account=None,
                    payment_reference_no=None, payment_reference_date=None):
    """Create a POS sales invoice with stock update; optionally submit and record payment."""
    from frappe.utils import cint, flt

    from trader_app.api.sales import create_sales_invoice, submit_sales_invoice

    company = resolve_active_company(company)
    abbr = frappe.get_cached_value("Company", company, "abbr")
    warehouse = warehouse or f"Main Warehouse - {abbr}"

    import json
    if isinstance(items, str):
        items = json.loads(items)

    normalized = []
    for item in items:
        row = dict(item)
        row["warehouse"] = row.get("warehouse") or warehouse
        normalized.append(row)

    result = create_sales_invoice(
        customer=customer,
        items=normalized,
        company=company,
        posting_date=posting_date or nowdate(),
        due_date=posting_date or nowdate(),
        taxes_and_charges=taxes_and_charges,
        tax_inclusive=tax_inclusive,
        update_stock=1,
        invoice_type="tax_invoice",
        currency=currency,
        exchange_rate=exchange_rate,
    )

    invoice_name = result["name"]

    if cint(submit):
        submit_sales_invoice(invoice_name)
        result["status"] = "Submitted"
        invoice = frappe.get_doc("Sales Invoice", invoice_name)
        result["grand_total"] = flt(invoice.grand_total)
        result["outstanding_amount"] = flt(invoice.outstanding_amount)

        if cint(record_payment):
            from trader_app.api.finance import record_invoice_payment

            pay_amount = flt(payment_amount) if payment_amount is not None else flt(invoice.grand_total)
            if pay_amount > flt(invoice.grand_total):
                frappe.throw(
                    _("Payment amount {0} cannot exceed invoice total {1}.").format(
                        pay_amount, invoice.grand_total
                    )
                )
            if pay_amount > 0:
                pe_result = record_invoice_payment(
                    "Sales Invoice",
                    invoice_name,
                    pay_amount,
                    mode_of_payment=mode_of_payment,
                    settlement_account=settlement_account,
                    posting_date=posting_date or nowdate(),
                    reference_no=payment_reference_no or invoice_name,
                    reference_date=payment_reference_date or posting_date or nowdate(),
                    submit=1,
                )
                result["payment_entry"] = pe_result.get("name")
                result["outstanding_amount"] = flt(pe_result.get("outstanding_amount"))

    return result

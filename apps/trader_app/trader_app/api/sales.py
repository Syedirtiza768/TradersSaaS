# -*- coding: utf-8 -*-
"""Trader App — Sales API.

Whitelisted endpoints for the Sales module:
- Sales Invoice CRUD
- Sales Order CRUD
- Delivery Note
- Customer credit-limit checks
- DocType event hooks
"""

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import nowdate, getdate, flt, cint


# ────────────────────────────────────────────────────────────────
# 1.  LIST ENDPOINTS
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_sales_invoices(company=None, customer=None, status=None,
                       from_date=None, to_date=None,
                       page=1, page_size=20, search=None):
    """Paginated list of Sales Invoices with optional filters."""
    try:
        company = company or _default_company()
        page = cint(page) or 1
        page_size = min(cint(page_size) or 20, 100)
        offset = (page - 1) * page_size

        conditions = ["si.company = %(company)s", "si.docstatus IN (0, 1)"]
        params = {"company": company}

        if customer:
            conditions.append("si.customer = %(customer)s")
            params["customer"] = customer

        if status == "Paid":
            conditions.append("si.outstanding_amount <= 0 AND si.docstatus = 1")
        elif status == "Unpaid":
            conditions.append("si.outstanding_amount > 0 AND si.docstatus = 1")
        elif status == "Overdue":
            conditions.append("si.outstanding_amount > 0 AND si.docstatus = 1 AND si.due_date < %(today)s")
            params["today"] = nowdate()
        elif status == "Draft":
            conditions.append("si.docstatus = 0")

        if from_date:
            conditions.append("si.posting_date >= %(from_date)s")
            params["from_date"] = from_date
        if to_date:
            conditions.append("si.posting_date <= %(to_date)s")
            params["to_date"] = to_date
        if search:
            conditions.append("(si.name LIKE %(search)s OR si.customer LIKE %(search)s)")
            params["search"] = f"%{search}%"

        where = " AND ".join(conditions)

        total = frappe.db.sql(
            f"SELECT COUNT(*) FROM `tabSales Invoice` si WHERE {where}",
            params,
        )[0][0]

        rows = frappe.db.sql(f"""
            SELECT si.name, si.customer, si.customer_name, si.posting_date,
                   si.due_date, si.grand_total, si.outstanding_amount,
                   si.currency, si.docstatus,
                   si.is_return, si.return_against,
                   CASE
                       WHEN si.docstatus = 0 THEN 'Draft'
                       WHEN si.docstatus = 2 THEN 'Cancelled'
                       WHEN si.outstanding_amount <= 0 THEN 'Paid'
                       WHEN si.due_date < CURDATE() AND si.outstanding_amount > 0 THEN 'Overdue'
                       WHEN si.outstanding_amount < si.grand_total THEN 'Partly Paid'
                       ELSE 'Unpaid'
                   END AS status
            FROM `tabSales Invoice` si
            WHERE {where}
            ORDER BY si.posting_date DESC, si.creation DESC
            LIMIT %(page_size)s OFFSET %(offset)s
        """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

        return {
            "data": rows,
            "total": cint(total),
            "page": page,
            "page_size": page_size,
        }
    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_sales_invoices failed")
        return {"data": [], "total": 0, "page": cint(page) or 1, "page_size": cint(page_size) or 20}


@frappe.whitelist()
def get_sales_invoice_detail(name):
    """Full Sales Invoice with items."""
    doc = frappe.get_doc("Sales Invoice", name)
    doc.check_permission("read")
    return doc.as_dict()


@frappe.whitelist()
def get_sales_orders(company=None, customer=None, status=None,
                     from_date=None, to_date=None,
                     page=1, page_size=20, search=None):
    """Paginated list of Sales Orders."""
    try:
        company = company or _default_company()
        page = cint(page) or 1
        page_size = min(cint(page_size) or 20, 100)
        offset = (page - 1) * page_size

        conditions = ["so.company = %(company)s", "so.docstatus IN (0, 1)"]
        params = {"company": company}

        if customer:
            conditions.append("so.customer = %(customer)s")
            params["customer"] = customer
        if status:
            conditions.append("so.status = %(status)s")
            params["status"] = status
        if from_date:
            conditions.append("so.transaction_date >= %(from_date)s")
            params["from_date"] = from_date
        if to_date:
            conditions.append("so.transaction_date <= %(to_date)s")
            params["to_date"] = to_date
        if search:
            conditions.append("(so.name LIKE %(search)s OR so.customer LIKE %(search)s)")
            params["search"] = f"%{search}%"

        where = " AND ".join(conditions)

        total = frappe.db.sql(
            f"SELECT COUNT(*) FROM `tabSales Order` so WHERE {where}", params
        )[0][0]

        rows = frappe.db.sql(f"""
            SELECT so.name, so.customer, so.customer_name,
                   so.transaction_date, so.delivery_date,
                   so.grand_total, so.status, so.currency, so.docstatus
            FROM `tabSales Order` so
            WHERE {where}
            ORDER BY so.transaction_date DESC, so.creation DESC
            LIMIT %(page_size)s OFFSET %(offset)s
        """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

        order_names = [row.name for row in rows]
        invoice_counts = {}
        unpaid_counts = {}
        if order_names:
            # ERPNext v15: tabSales Invoice has no 'sales_order' header field.
            # Link is through tabSales Invoice Item.sales_order.
            linked_invoices = frappe.db.sql("""
                SELECT DISTINCT sii.sales_order, si.outstanding_amount
                FROM `tabSales Invoice Item` sii
                INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
                WHERE sii.sales_order IN %(order_names)s AND si.docstatus < 2
            """, {"order_names": order_names}, as_dict=True)
            for invoice in linked_invoices:
                sales_order = invoice.get("sales_order")
                invoice_counts[sales_order] = invoice_counts.get(sales_order, 0) + 1
                if flt(invoice.get("outstanding_amount")) > 0:
                    unpaid_counts[sales_order] = unpaid_counts.get(sales_order, 0) + 1

        for row in rows:
            row["linked_invoice_count"] = invoice_counts.get(row.name, 0)
            row["unpaid_invoice_count"] = unpaid_counts.get(row.name, 0)

        return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_sales_orders failed")
        return {"data": [], "total": 0, "page": cint(page) or 1, "page_size": cint(page_size) or 20}


@frappe.whitelist()
def get_sales_order_detail(name):
    """Full Sales Order with items."""
    doc = frappe.get_doc("Sales Order", name)
    doc.check_permission("read")
    data = doc.as_dict()
    # ERPNext v15: tabSales Invoice has no 'sales_order' header field.
    # Link is through tabSales Invoice Item.sales_order.
    data["linked_sales_invoices"] = frappe.db.sql("""
        SELECT DISTINCT si.name, si.posting_date, si.grand_total,
                        si.currency, si.status, si.outstanding_amount
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE sii.sales_order = %(so_name)s AND si.docstatus < 2
        ORDER BY si.posting_date DESC, si.creation DESC
    """, {"so_name": doc.name}, as_dict=True)
    return data


@frappe.whitelist()
def get_quotations(company=None, customer=None, status=None,
                   from_date=None, to_date=None,
                   page=1, page_size=20, search=None):
    """Paginated list of Quotations."""
    try:
        company = company or _default_company()
        page = cint(page) or 1
        page_size = min(cint(page_size) or 20, 100)
        offset = (page - 1) * page_size

        conditions = ["q.company = %(company)s", "q.docstatus IN (0, 1)"]
        params = {"company": company}

        if customer:
            conditions.append("q.party_name = %(customer)s")
            params["customer"] = customer
        if status:
            conditions.append("q.status = %(status)s")
            params["status"] = status
        if from_date:
            conditions.append("q.transaction_date >= %(from_date)s")
            params["from_date"] = from_date
        if to_date:
            conditions.append("q.transaction_date <= %(to_date)s")
            params["to_date"] = to_date
        if search:
            conditions.append("(q.name LIKE %(search)s OR q.party_name LIKE %(search)s)")
            params["search"] = f"%{search}%"

        where = " AND ".join(conditions)

        total = frappe.db.sql(
            f"SELECT COUNT(*) FROM `tabQuotation` q WHERE {where}", params
        )[0][0]

        rows = frappe.db.sql(f"""
            SELECT q.name, q.party_name AS customer, q.customer_name,
                   q.transaction_date, q.valid_till,
                   q.grand_total, q.currency, q.status, q.docstatus,
                   q.order_type
            FROM `tabQuotation` q
            WHERE {where}
            ORDER BY q.transaction_date DESC, q.creation DESC
            LIMIT %(page_size)s OFFSET %(offset)s
        """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

        quotation_names = [row.name for row in rows]
        order_counts = {}
        if quotation_names:
            # ERPNext v15: tabSales Order has no 'quotation' header field.
            # Link is through tabSales Order Item.prevdoc_docname.
            linked = frappe.db.sql("""
                SELECT DISTINCT soi.prevdoc_docname AS qname
                FROM `tabSales Order Item` soi
                INNER JOIN `tabSales Order` so ON so.name = soi.parent
                WHERE soi.prevdoc_docname IN %(names)s AND so.docstatus < 2
            """, {"names": quotation_names}, as_dict=True)
            for row_l in linked:
                qname = row_l.qname
                order_counts[qname] = order_counts.get(qname, 0) + 1

        for row in rows:
            row["linked_order_count"] = order_counts.get(row.name, 0)

        return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_quotations failed")
        return {"data": [], "total": 0, "page": cint(page) or 1, "page_size": cint(page_size) or 20}


@frappe.whitelist()
def get_quotation_detail(name):
    """Full Quotation with items."""
    doc = frappe.get_doc("Quotation", name)
    doc.check_permission("read")
    data = doc.as_dict()
    # ERPNext v15: tabSales Order has no 'quotation' header field.
    # Link is through tabSales Order Item.prevdoc_docname.
    data["linked_sales_orders"] = frappe.db.sql("""
        SELECT DISTINCT so.name, so.transaction_date, so.delivery_date,
                        so.grand_total, so.currency, so.status
        FROM `tabSales Order Item` soi
        INNER JOIN `tabSales Order` so ON so.name = soi.parent
        WHERE soi.prevdoc_docname = %(quotation)s AND so.docstatus < 2
        ORDER BY so.transaction_date DESC, so.creation DESC
    """, {"quotation": doc.name}, as_dict=True)
    return data


# ────────────────────────────────────────────────────────────────
# 2.  CREATE / SUBMIT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def create_sales_invoice(customer, items, company=None, posting_date=None,
                         due_date=None, taxes_and_charges=None,
                         tax_inclusive=0,
                         is_return=0, return_against=None,
                         update_stock=0):
    """Create a Sales Invoice from the UI.

    Parameters
    ----------
    customer : str
    items : list of dict — each with item_code, qty, rate
    update_stock : int — default 0 (stock is managed via Delivery Notes).
                   Pass 1 only when invoicing without a delivery note and
                   stock deduction is explicitly required.
    """
    import json
    if isinstance(items, str):
        items = json.loads(items)

    company = company or _default_company()
    abbr = frappe.get_cached_value("Company", company, "abbr")

    si = frappe.new_doc("Sales Invoice")
    si.company = company
    si.customer = customer
    si.posting_date = posting_date or nowdate()
    si.due_date = due_date or si.posting_date
    si.set_warehouse = f"Main Warehouse - {abbr}"
    si.update_stock = cint(update_stock)
    si.is_return = cint(is_return)
    if return_against:
        si.return_against = return_against

    for item in items:
        row = {
            "item_code": item.get("item_code"),
            "qty": -abs(flt(item.get("qty", 1))) if cint(is_return) else flt(item.get("qty", 1)),
            "rate": flt(item.get("rate", 0)),
            "warehouse": item.get("warehouse") or f"Main Warehouse - {abbr}",
        }
        if item.get("description"):
            row["description"] = item["description"]
        si.append("items", row)

    if taxes_and_charges:
        si.taxes_and_charges = taxes_and_charges
        si.run_method("set_taxes")
        if cint(tax_inclusive):
            for tax_row in si.taxes:
                tax_row.included_in_print_rate = 1

    si.insert(ignore_permissions=False)
    return {"name": si.name, "status": "Draft"}


@frappe.whitelist()
def create_sales_order(customer, items, company=None, transaction_date=None,
                       delivery_date=None, taxes_and_charges=None,
                       tax_inclusive=0):
    """Create a Sales Order from the UI."""
    import json
    if isinstance(items, str):
        items = json.loads(items)

    company = company or _default_company()
    abbr = frappe.get_cached_value("Company", company, "abbr")

    so = frappe.new_doc("Sales Order")
    so.company = company
    so.customer = customer
    so.transaction_date = transaction_date or nowdate()
    so.delivery_date = delivery_date or so.transaction_date

    for item in items:
        row = {
            "item_code": item.get("item_code"),
            "qty": flt(item.get("qty", 1)),
            "rate": flt(item.get("rate", 0)),
            "warehouse": item.get("warehouse") or f"Main Warehouse - {abbr}",
            "delivery_date": item.get("delivery_date") or delivery_date or so.delivery_date,
        }
        if item.get("description"):
            row["description"] = item["description"]
        so.append("items", row)

    if taxes_and_charges:
        so.taxes_and_charges = taxes_and_charges
        so.run_method("set_taxes")
        if cint(tax_inclusive):
            for tax_row in so.taxes:
                tax_row.included_in_print_rate = 1

    so.insert(ignore_permissions=False)
    return {"name": so.name, "status": "Draft"}


@frappe.whitelist()
def submit_sales_invoice(name):
    """Submit a draft Sales Invoice."""
    doc = frappe.get_doc("Sales Invoice", name)
    doc.check_permission("submit")
    doc.submit()
    frappe.db.commit()
    return {"name": doc.name, "status": "Submitted"}


@frappe.whitelist()
def submit_sales_order(name):
    """Submit a draft Sales Order."""
    doc = frappe.get_doc("Sales Order", name)
    doc.check_permission("submit")
    doc.submit()
    frappe.db.commit()
    return {"name": doc.name, "status": "Submitted"}


@frappe.whitelist()
def cancel_sales_invoice(name):
    """Cancel a submitted Sales Invoice."""
    doc = frappe.get_doc("Sales Invoice", name)
    doc.check_permission("cancel")
    doc.cancel()
    frappe.db.commit()
    return {"name": doc.name, "status": "Cancelled"}


@frappe.whitelist()
def cancel_sales_order(name):
    """Cancel a submitted Sales Order."""
    doc = frappe.get_doc("Sales Order", name)
    doc.check_permission("cancel")
    doc.cancel()
    frappe.db.commit()
    return {"name": doc.name, "status": "Cancelled"}


@frappe.whitelist()
def create_quotation(customer, items, company=None, transaction_date=None,
                     valid_till=None, taxes_and_charges=None,
                     tax_inclusive=0):
    """Create a Quotation from the UI."""
    import json
    if isinstance(items, str):
        items = json.loads(items)

    company = company or _default_company()
    abbr = frappe.get_cached_value("Company", company, "abbr")

    q = frappe.new_doc("Quotation")
    q.company = company
    q.quotation_to = "Customer"
    q.party_name = customer
    q.transaction_date = transaction_date or nowdate()
    q.valid_till = valid_till or q.transaction_date

    for item in items:
        row = {
            "item_code": item.get("item_code"),
            "qty": flt(item.get("qty", 1)),
            "rate": flt(item.get("rate", 0)),
            "warehouse": item.get("warehouse") or f"Main Warehouse - {abbr}",
        }
        if item.get("description"):
            row["description"] = item["description"]
        q.append("items", row)

    if taxes_and_charges:
        q.taxes_and_charges = taxes_and_charges
        q.run_method("set_taxes")
        if cint(tax_inclusive):
            for tax_row in q.taxes:
                tax_row.included_in_print_rate = 1

    q.insert(ignore_permissions=False)
    return {"name": q.name, "status": "Draft"}


@frappe.whitelist()
def submit_quotation(name):
    """Submit a draft Quotation."""
    doc = frappe.get_doc("Quotation", name)
    doc.check_permission("submit")
    doc.submit()
    frappe.db.commit()
    return {"name": doc.name, "status": "Submitted"}


# ────────────────────────────────────────────────────────────────
# 3.  SALES SUMMARY / ANALYTICS
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_sales_summary(company=None):
    """Aggregate sales stats for the Sales page header."""
    try:
        company = company or _default_company()
        today = nowdate()
        first_of_month = getdate(today).replace(day=1).isoformat()

        total_invoices = cint(frappe.db.sql("""
            SELECT COUNT(*) FROM `tabSales Invoice`
            WHERE company = %s AND docstatus = 1
        """, (company,))[0][0])

        monthly_sales = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(grand_total), 0) FROM `tabSales Invoice`
            WHERE company = %s AND docstatus = 1
                  AND posting_date >= %s AND posting_date <= %s
        """, (company, first_of_month, today))[0][0])

        total_outstanding = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(outstanding_amount), 0) FROM `tabSales Invoice`
            WHERE company = %s AND docstatus = 1 AND outstanding_amount > 0
        """, (company,))[0][0])

        avg_order_value = flt(frappe.db.sql("""
            SELECT COALESCE(AVG(grand_total), 0) FROM `tabSales Invoice`
            WHERE company = %s AND docstatus = 1
                  AND posting_date >= %s AND posting_date <= %s
        """, (company, first_of_month, today))[0][0])

        return {
            "total_invoices": total_invoices,
            "monthly_sales": monthly_sales,
            "total_outstanding": total_outstanding,
            "avg_order_value": avg_order_value,
        }
    except Exception:
        frappe.log_error(frappe.get_traceback(), "get_sales_summary failed")
        return {"total_invoices": 0, "monthly_sales": 0.0, "total_outstanding": 0.0, "avg_order_value": 0.0}


# ────────────────────────────────────────────────────────────────
# 4.  DOCTYPE EVENT HOOKS
# ────────────────────────────────────────────────────────────────

def validate_sales_invoice(doc, method):
    """Runs on Sales Invoice validate — enforce credit limit."""
    if doc.docstatus == 0:
        _check_customer_credit_limit(doc)


def on_sales_invoice_submit(doc, method):
    """Runs on Sales Invoice submit — log activity."""
    frappe.publish_realtime(
        "sales_invoice_submitted",
        {"invoice": doc.name, "customer": doc.customer, "total": doc.grand_total},
        user=frappe.session.user,
    )


def on_sales_invoice_cancel(doc, method):
    """Runs on Sales Invoice cancel."""
    frappe.publish_realtime(
        "sales_invoice_cancelled",
        {"invoice": doc.name},
        user=frappe.session.user,
    )


# ────────────────────────────────────────────────────────────────
#    HELPERS
# ────────────────────────────────────────────────────────────────

def _check_customer_credit_limit(doc):
    """Check if the invoice would exceed customer credit limit."""
    from erpnext.selling.doctype.customer.customer import get_credit_limit, get_customer_outstanding
    try:
        credit_limit = get_credit_limit(doc.customer, doc.company)
        if not credit_limit:
            return
        outstanding = get_customer_outstanding(doc.customer, doc.company)
        if flt(outstanding) + flt(doc.grand_total) > flt(credit_limit):
            frappe.msgprint(
                _("Warning: This invoice will exceed the credit limit of {0} for customer {1}. "
                  "Current outstanding: {2}").format(
                    frappe.format_value(credit_limit, {"fieldtype": "Currency"}),
                    doc.customer,
                    frappe.format_value(outstanding, {"fieldtype": "Currency"}),
                ),
                indicator="orange",
                alert=True,
            )
    except (AttributeError, ImportError):
        # Optional ERPNext helpers / version differences — do not swallow broader errors.
        pass


def _default_company():
    companies = frappe.get_all("Company", limit=1, pluck="name")
    return (
        frappe.defaults.get_user_default("Company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
        or (companies[0] if companies else None)
    )

# -*- coding: utf-8 -*-
"""Trader App — Customers API.

Whitelisted endpoints for customer management.
"""

from __future__ import unicode_literals

import frappe
from frappe import _
from trader_app.api.company import resolve_active_company
from frappe.utils import nowdate, flt, cint


@frappe.whitelist()
def get_customers(page=1, page_size=20, search=None, customer_group=None):
    """Paginated customer list with outstanding summary."""
    page = cint(page) or 1
    page_size = min(cint(page_size) or 20, 100)
    offset = (page - 1) * page_size
    company = resolve_active_company()

    conditions = ["c.disabled = 0"]
    params = {}

    if search:
        conditions.append("(c.name LIKE %(search)s OR c.customer_name LIKE %(search)s)")
        params["search"] = f"%{search}%"
    if customer_group:
        conditions.append("c.customer_group = %(customer_group)s")
        params["customer_group"] = customer_group

    where = " AND ".join(conditions)

    total = frappe.db.sql(
        f"SELECT COUNT(*) FROM `tabCustomer` c WHERE {where}", params
    )[0][0]

    rows = frappe.db.sql(f"""
        SELECT c.name, c.customer_name, c.customer_group, c.territory,
               c.mobile_no, c.email_id,
               COALESCE(outstanding.total, 0) AS outstanding_amount,
               COALESCE(revenue.total, 0) AS total_revenue
        FROM `tabCustomer` c
        LEFT JOIN (
            SELECT customer, SUM(outstanding_amount) AS total
            FROM `tabSales Invoice`
            WHERE docstatus = 1 AND company = %(company)s AND outstanding_amount > 0
            GROUP BY customer
        ) outstanding ON outstanding.customer = c.name
        LEFT JOIN (
            SELECT customer, SUM(grand_total) AS total
            FROM `tabSales Invoice`
            WHERE docstatus = 1 AND company = %(company)s
            GROUP BY customer
        ) revenue ON revenue.customer = c.name
        WHERE {where}
        ORDER BY c.customer_name
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "company": company, "page_size": page_size, "offset": offset}, as_dict=True)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


@frappe.whitelist()
def get_customer_detail(name):
    """Customer detail with transactions summary."""
    doc = frappe.get_doc("Customer", name)
    doc.check_permission("read")
    company = resolve_active_company()

    outstanding = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0) FROM `tabSales Invoice`
        WHERE customer = %s AND company = %s AND docstatus = 1 AND outstanding_amount > 0
    """, (name, company))[0][0])

    total_revenue = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0) FROM `tabSales Invoice`
        WHERE customer = %s AND company = %s AND docstatus = 1
    """, (name, company))[0][0])

    invoice_count = cint(frappe.db.sql("""
        SELECT COUNT(*) FROM `tabSales Invoice`
        WHERE customer = %s AND company = %s AND docstatus = 1
    """, (name, company))[0][0])

    result = doc.as_dict()
    result["outstanding_amount"] = outstanding
    result["total_revenue"] = total_revenue
    result["invoice_count"] = invoice_count

    return result


@frappe.whitelist()
def get_customer_groups():
    """List distinct customer groups."""
    return frappe.get_all("Customer Group", filters={"is_group": 0}, pluck="name", order_by="name")


@frappe.whitelist()
def get_customer_transactions(customer, company=None, page=1, page_size=20):
    """Recent transactions for a customer."""
    company = resolve_active_company(company)
    page = cint(page) or 1
    page_size = min(cint(page_size) or 20, 100)
    offset = (page - 1) * page_size

    total = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabSales Invoice`
        WHERE customer = %s AND company = %s AND docstatus = 1
    """, (customer, company))[0][0]

    rows = frappe.db.sql("""
        SELECT name, posting_date, grand_total, outstanding_amount,
               CASE
                   WHEN outstanding_amount <= 0 THEN 'Paid'
                   WHEN outstanding_amount < grand_total THEN 'Partly Paid'
                   ELSE 'Unpaid'
               END AS status
        FROM `tabSales Invoice`
        WHERE customer = %s AND company = %s AND docstatus = 1
        ORDER BY posting_date DESC
        LIMIT %s OFFSET %s
    """, (customer, company, page_size, offset), as_dict=True)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


@frappe.whitelist()
def create_customer(customer_name, customer_group=None, territory=None, mobile_no=None, email_id=None):
    """Create a minimal Customer record for the Trader UI."""
    doc = frappe.new_doc("Customer")
    doc.customer_name = customer_name
    doc.customer_group = customer_group or _default_customer_group()
    doc.territory = territory or _default_territory()
    doc.mobile_no = mobile_no
    doc.email_id = email_id
    doc.insert(ignore_permissions=False)
    frappe.db.commit()
    return {"name": doc.name, "customer_name": doc.customer_name, "status": "Created"}


@frappe.whitelist()
def update_customer(name, customer_name=None, customer_group=None, territory=None,
                    mobile_no=None, email_id=None):
    """Update an existing Customer record."""
    doc = frappe.get_doc("Customer", name)
    doc.check_permission("write")

    if customer_name is not None:
        doc.customer_name = customer_name
    if customer_group is not None:
        doc.customer_group = customer_group
    if territory is not None:
        doc.territory = territory
    if mobile_no is not None:
        doc.mobile_no = mobile_no
    if email_id is not None:
        doc.email_id = email_id

    doc.save(ignore_permissions=False)
    frappe.db.commit()
    return {"name": doc.name, "customer_name": doc.customer_name, "status": "Updated"}


@frappe.whitelist()
def disable_customer(name):
    """Disable (soft-delete) a Customer record."""
    doc = frappe.get_doc("Customer", name)
    doc.check_permission("write")
    doc.disabled = 1
    doc.save(ignore_permissions=False)
    frappe.db.commit()
    return {"name": doc.name, "status": "Disabled"}


@frappe.whitelist()
def enable_customer(name):
    """Re-enable a previously disabled Customer record."""
    doc = frappe.get_doc("Customer", name)
    doc.check_permission("write")
    doc.disabled = 0
    doc.save(ignore_permissions=False)
    frappe.db.commit()
    return {"name": doc.name, "status": "Enabled"}


def _default_customer_group():
    return frappe.db.get_single_value("Selling Settings", "customer_group") or frappe.get_all(
        "Customer Group", filters={"is_group": 0}, order_by="name", limit=1, pluck="name"
    )[0]


def _default_territory():
    return frappe.db.get_single_value("Selling Settings", "territory") or frappe.get_all(
        "Territory", filters={"is_group": 0}, order_by="name", limit=1, pluck="name"
    )[0]

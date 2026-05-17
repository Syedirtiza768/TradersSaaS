# -*- coding: utf-8 -*-
"""Trader App — Suppliers API.

Whitelisted endpoints for supplier management.
"""

from __future__ import unicode_literals

import frappe
from frappe import _
from trader_app.api.company import resolve_active_company
from frappe.utils import nowdate, flt, cint


@frappe.whitelist()
def get_suppliers(page=1, page_size=20, search=None, supplier_group=None):
    """Paginated supplier list with payable summary."""
    page = cint(page) or 1
    page_size = min(cint(page_size) or 20, 100)
    offset = (page - 1) * page_size
    company = resolve_active_company()

    conditions = ["s.disabled = 0"]
    params = {}

    if search:
        conditions.append("(s.name LIKE %(search)s OR s.supplier_name LIKE %(search)s)")
        params["search"] = f"%{search}%"
    if supplier_group:
        conditions.append("s.supplier_group = %(supplier_group)s")
        params["supplier_group"] = supplier_group

    where = " AND ".join(conditions)

    total = frappe.db.sql(
        f"SELECT COUNT(*) FROM `tabSupplier` s WHERE {where}", params
    )[0][0]

    rows = frappe.db.sql(f"""
        SELECT s.name, s.supplier_name, s.supplier_group, s.country,
               s.mobile_no, s.email_id,
               COALESCE(payable.total, 0) AS outstanding_amount,
               COALESCE(purchases.total, 0) AS total_purchases
        FROM `tabSupplier` s
        LEFT JOIN (
            SELECT supplier, SUM(outstanding_amount) AS total
            FROM `tabPurchase Invoice`
            WHERE docstatus = 1 AND company = %(company)s AND outstanding_amount > 0
            GROUP BY supplier
        ) payable ON payable.supplier = s.name
        LEFT JOIN (
            SELECT supplier, SUM(grand_total) AS total
            FROM `tabPurchase Invoice`
            WHERE docstatus = 1 AND company = %(company)s
            GROUP BY supplier
        ) purchases ON purchases.supplier = s.name
        WHERE {where}
        ORDER BY s.supplier_name
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "company": company, "page_size": page_size, "offset": offset}, as_dict=True)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


@frappe.whitelist()
def get_supplier_detail(name):
    """Supplier detail with payable summary."""
    doc = frappe.get_doc("Supplier", name)
    doc.check_permission("read")
    company = resolve_active_company()

    outstanding = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0) FROM `tabPurchase Invoice`
        WHERE supplier = %s AND company = %s AND docstatus = 1 AND outstanding_amount > 0
    """, (name, company))[0][0])

    total_purchases = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0) FROM `tabPurchase Invoice`
        WHERE supplier = %s AND company = %s AND docstatus = 1
    """, (name, company))[0][0])

    invoice_count = cint(frappe.db.sql("""
        SELECT COUNT(*) FROM `tabPurchase Invoice`
        WHERE supplier = %s AND company = %s AND docstatus = 1
    """, (name, company))[0][0])

    result = doc.as_dict()
    result["outstanding_amount"] = outstanding
    result["total_purchases"] = total_purchases
    result["invoice_count"] = invoice_count

    return result


@frappe.whitelist()
def get_supplier_groups():
    """List distinct supplier groups."""
    return frappe.get_all("Supplier Group", filters={"is_group": 0}, pluck="name", order_by="name")


@frappe.whitelist()
def get_supplier_transactions(supplier, company=None, page=1, page_size=20):
    """Recent transactions for a supplier."""
    company = resolve_active_company(company)
    page = cint(page) or 1
    page_size = min(cint(page_size) or 20, 100)
    offset = (page - 1) * page_size

    total = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabPurchase Invoice`
        WHERE supplier = %s AND company = %s AND docstatus = 1
    """, (supplier, company))[0][0]

    rows = frappe.db.sql("""
        SELECT name, posting_date, grand_total, outstanding_amount,
               CASE
                   WHEN outstanding_amount <= 0 THEN 'Paid'
                   WHEN outstanding_amount < grand_total THEN 'Partly Paid'
                   ELSE 'Unpaid'
               END AS status
        FROM `tabPurchase Invoice`
        WHERE supplier = %s AND company = %s AND docstatus = 1
        ORDER BY posting_date DESC
        LIMIT %s OFFSET %s
    """, (supplier, company, page_size, offset), as_dict=True)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


@frappe.whitelist()
def create_supplier(supplier_name, supplier_group=None, country=None, mobile_no=None, email_id=None):
    """Create a minimal Supplier record for the Trader UI."""
    doc = frappe.new_doc("Supplier")
    doc.supplier_name = supplier_name
    doc.supplier_group = supplier_group or _default_supplier_group()
    doc.country = country or frappe.db.get_default("country") or "Pakistan"
    doc.mobile_no = mobile_no
    doc.email_id = email_id
    doc.insert(ignore_permissions=False)
    frappe.db.commit()
    return {"name": doc.name, "supplier_name": doc.supplier_name, "status": "Created"}


@frappe.whitelist()
def update_supplier(name, supplier_name=None, supplier_group=None, country=None,
                    mobile_no=None, email_id=None):
    """Update an existing Supplier record."""
    doc = frappe.get_doc("Supplier", name)
    doc.check_permission("write")

    if supplier_name is not None:
        doc.supplier_name = supplier_name
    if supplier_group is not None:
        doc.supplier_group = supplier_group
    if country is not None:
        doc.country = country
    if mobile_no is not None:
        doc.mobile_no = mobile_no
    if email_id is not None:
        doc.email_id = email_id

    doc.save(ignore_permissions=False)
    frappe.db.commit()
    return {"name": doc.name, "supplier_name": doc.supplier_name, "status": "Updated"}


@frappe.whitelist()
def disable_supplier(name):
    """Disable (soft-delete) a Supplier record."""
    doc = frappe.get_doc("Supplier", name)
    doc.check_permission("write")
    doc.disabled = 1
    doc.save(ignore_permissions=False)
    frappe.db.commit()
    return {"name": doc.name, "status": "Disabled"}


@frappe.whitelist()
def enable_supplier(name):
    """Re-enable a previously disabled Supplier record."""
    doc = frappe.get_doc("Supplier", name)
    doc.check_permission("write")
    doc.disabled = 0
    doc.save(ignore_permissions=False)
    frappe.db.commit()
    return {"name": doc.name, "status": "Enabled"}


def _default_supplier_group():
    return frappe.get_all(
        "Supplier Group", filters={"is_group": 0}, order_by="name", limit=1, pluck="name"
    )[0]

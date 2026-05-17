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

from trader_app.api.company import assert_document_company_access, resolve_active_company

from trader_app.api.invoice_types import (
    get_document_catalog,
    normalize_type_key,
    resolve_sales_taxes,
    set_trader_invoice_type,
    print_format_for_doc,
)


# ────────────────────────────────────────────────────────────────
# 1.  LIST ENDPOINTS
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_sales_document_catalog():
    """Return sales-side document types the UI can create."""
    from trader_app.setup.custom_fields import ensure_custom_fields

    ensure_custom_fields()
    return {"documents": get_document_catalog("sales")}


@frappe.whitelist()
def get_sales_invoices(company=None, customer=None, status=None,
                       from_date=None, to_date=None,
                       invoice_type=None,
                       page=1, page_size=20, search=None):
    """Paginated list of Sales Invoices with optional filters."""
    try:
        company = resolve_active_company(company)
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

        if invoice_type and frappe.db.has_column("Sales Invoice", "trader_invoice_type"):
            if invoice_type == "credit_note":
                conditions.append("si.is_return = 1")
            else:
                label = normalize_type_key(invoice_type, is_return=0)
                conditions.append("si.trader_invoice_type = %(invoice_type_label)s")
                params["invoice_type_label"] = label

        where = " AND ".join(conditions)

        type_select = (
            ", si.trader_invoice_type"
            if frappe.db.has_column("Sales Invoice", "trader_invoice_type")
            else ", NULL AS trader_invoice_type"
        )

        total = frappe.db.sql(
            f"SELECT COUNT(*) FROM `tabSales Invoice` si WHERE {where}",
            params,
        )[0][0]

        rows = frappe.db.sql(f"""
            SELECT si.name, si.customer, si.customer_name, si.posting_date,
                   si.due_date, si.grand_total, si.outstanding_amount,
                   si.currency, si.docstatus,
                   si.is_return, si.return_against
                   {type_select},
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
    assert_document_company_access(doc.company)
    return doc.as_dict()


@frappe.whitelist()
def get_sales_orders(company=None, customer=None, status=None,
                     from_date=None, to_date=None,
                     page=1, page_size=20, search=None):
    """Paginated list of Sales Orders."""
    try:
        company = resolve_active_company(company)
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
    assert_document_company_access(doc.company)
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
        company = resolve_active_company(company)
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
    assert_document_company_access(doc.company)
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
def get_customer_item_sales_history(customer, item_code, company=None, limit=5):
    """Last N submitted sale lines for the same customer and item (invoice-time pricing history)."""
    if not customer or not item_code:
        return {"data": []}

    company = resolve_active_company(company)
    limit = min(cint(limit) or 5, 20)

    rows = frappe.db.sql("""
        SELECT si.name AS invoice,
               si.posting_date,
               sii.item_code,
               sii.item_name,
               sii.qty,
               sii.rate,
               sii.discount_percentage,
               sii.discount_amount,
               sii.amount AS line_amount
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.customer = %(customer)s
          AND sii.item_code = %(item_code)s
          AND si.company = %(company)s
          AND si.docstatus = 1
          AND IFNULL(si.is_return, 0) = 0
        ORDER BY si.posting_date DESC, si.creation DESC, sii.idx DESC
        LIMIT %(limit)s
    """, {
        "customer": customer,
        "item_code": item_code,
        "company": company,
        "limit": limit,
    }, as_dict=True)

    return {"data": rows}


@frappe.whitelist()
def create_sales_invoice(customer, items, company=None, posting_date=None,
                         due_date=None, taxes_and_charges=None,
                         tax_inclusive=0,
                         is_return=0, return_against=None,
                         update_stock=0, invoice_type=None,
                         preferred_bank_account=None,
                         currency=None, exchange_rate=None):
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

    company = resolve_active_company(company)
    abbr = frappe.get_cached_value("Company", company, "abbr")
    default_warehouse = f"Main Warehouse - {abbr}"

    from trader_app.setup.custom_fields import ensure_custom_fields
    ensure_custom_fields()

    si = frappe.new_doc("Sales Invoice")
    si.company = company
    si.customer = customer
    si.posting_date = posting_date or nowdate()
    si.due_date = due_date or si.posting_date
    si.set_warehouse = default_warehouse
    si.update_stock = cint(update_stock)

    from trader_app.api.currency import apply_document_currency
    apply_document_currency(
        si,
        currency=currency,
        exchange_rate=exchange_rate,
        posting_date=si.posting_date,
        for_selling=True,
    )
    si.is_return = cint(is_return)
    if return_against:
        si.return_against = return_against
    if preferred_bank_account and frappe.db.has_column("Sales Invoice", "preferred_bank_account"):
        si.preferred_bank_account = preferred_bank_account

    set_trader_invoice_type(si, invoice_type=invoice_type, is_return=is_return)
    taxes_and_charges = resolve_sales_taxes(company, invoice_type, taxes_and_charges)

    for item in items:
        item_code = item.get("item_code")
        warehouse = item.get("warehouse") or default_warehouse
        qty = -abs(flt(item.get("qty", 1))) if cint(is_return) else flt(item.get("qty", 1))

        if cint(update_stock) and not cint(is_return) and frappe.get_cached_value("Item", item_code, "is_stock_item"):
            _ensure_stock_available(item_code, warehouse, qty, company)

        serial_no = (item.get("serial_no") or "").strip()
        if serial_no:
            from trader_app.api.inventory import check_serial_for_item
            result = check_serial_for_item(item_code, serial_no, warehouse=warehouse, company=company)
            if not result.get("valid"):
                frappe.throw(result.get("message") or _("Invalid serial number."))

        row = {
            "item_code": item_code,
            "qty": qty,
            "rate": flt(item.get("rate", 0)),
            "warehouse": warehouse,
        }
        if item.get("description"):
            row["description"] = item["description"]
        if serial_no:
            row["serial_no"] = serial_no
        si.append("items", row)

    if taxes_and_charges:
        si.taxes_and_charges = taxes_and_charges
        si.run_method("set_taxes")
        if cint(tax_inclusive):
            for tax_row in si.taxes:
                tax_row.included_in_print_rate = 1

    si.insert(ignore_permissions=False)
    return {
        "name": si.name,
        "status": "Draft",
        "trader_invoice_type": getattr(si, "trader_invoice_type", None),
        "print_format": print_format_for_doc(si),
    }


@frappe.whitelist()
def create_sales_order(customer, items, company=None, transaction_date=None,
                       delivery_date=None, taxes_and_charges=None,
                       tax_inclusive=0):
    """Create a Sales Order from the UI."""
    import json
    if isinstance(items, str):
        items = json.loads(items)

    company = resolve_active_company(company)
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
                     tax_inclusive=0, invoice_type=None):
    """Create a Quotation from the UI."""
    import json
    if isinstance(items, str):
        items = json.loads(items)

    company = resolve_active_company(company)
    abbr = frappe.get_cached_value("Company", company, "abbr")

    q = frappe.new_doc("Quotation")
    q.company = company
    q.quotation_to = "Customer"
    q.party_name = customer
    q.transaction_date = transaction_date or nowdate()
    q.valid_till = valid_till or q.transaction_date

    type_key = invoice_type or "quotation"
    set_trader_invoice_type(q, invoice_type=type_key)
    taxes_and_charges = resolve_sales_taxes(company, type_key, taxes_and_charges)

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
    return {
        "name": q.name,
        "status": "Draft",
        "trader_invoice_type": getattr(q, "trader_invoice_type", None),
        "print_format": print_format_for_doc(q),
    }


# ────────────────────────────────────────────────────────────────
# 2b. DELIVERY NOTE / DELIVERY CHALLAN
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_delivery_notes(company=None, customer=None, status=None,
                       page=1, page_size=20, search=None):
    """Paginated delivery challans (Delivery Notes)."""
    company = resolve_active_company(company)
    page = cint(page) or 1
    page_size = min(cint(page_size) or 20, 100)
    offset = (page - 1) * page_size

    conditions = ["dn.company = %(company)s", "dn.docstatus IN (0, 1)"]
    params = {"company": company}

    if customer:
        conditions.append("dn.customer = %(customer)s")
        params["customer"] = customer
    if status == "Draft":
        conditions.append("dn.docstatus = 0")
    elif status == "Submitted":
        conditions.append("dn.docstatus = 1")
    if search:
        conditions.append("(dn.name LIKE %(search)s OR dn.customer LIKE %(search)s)")
        params["search"] = f"%{search}%"

    where = " AND ".join(conditions)
    type_select = (
        ", dn.trader_invoice_type"
        if frappe.db.has_column("Delivery Note", "trader_invoice_type")
        else ", 'Delivery Challan' AS trader_invoice_type"
    )

    total = frappe.db.sql(
        f"SELECT COUNT(*) FROM `tabDelivery Note` dn WHERE {where}", params
    )[0][0]

    rows = frappe.db.sql(f"""
        SELECT dn.name, dn.customer, dn.customer_name, dn.posting_date,
               dn.grand_total, dn.currency, dn.docstatus, dn.status
               {type_select}
        FROM `tabDelivery Note` dn
        WHERE {where}
        ORDER BY dn.posting_date DESC, dn.creation DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


@frappe.whitelist()
def get_delivery_note_detail(name):
    doc = frappe.get_doc("Delivery Note", name)
    doc.check_permission("read")
    assert_document_company_access(doc.company)
    data = doc.as_dict()
    data["print_format"] = print_format_for_doc(doc)
    return data


@frappe.whitelist()
def create_delivery_note(customer, items, company=None, posting_date=None,
                         sales_order=None, against_sales_invoice=None):
    """Create a delivery challan (Delivery Note)."""
    import json
    if isinstance(items, str):
        items = json.loads(items)

    company = resolve_active_company(company)
    abbr = frappe.get_cached_value("Company", company, "abbr")

    dn = frappe.new_doc("Delivery Note")
    dn.company = company
    dn.customer = customer
    dn.posting_date = posting_date or nowdate()
    dn.set_warehouse = f"Main Warehouse - {abbr}"
    set_trader_invoice_type(dn, invoice_type="delivery_challan")

    for item in items:
        row = {
            "item_code": item.get("item_code"),
            "qty": flt(item.get("qty", 1)),
            "warehouse": item.get("warehouse") or f"Main Warehouse - {abbr}",
        }
        if item.get("description"):
            row["description"] = item["description"]
        if item.get("rate") is not None:
            row["rate"] = flt(item.get("rate", 0))
        if sales_order:
            row["against_sales_order"] = sales_order
        dn.append("items", row)

    dn.insert(ignore_permissions=False)

    if against_sales_invoice:
        try:
            dn.reload()
            for row in dn.items:
                row.against_sales_invoice = against_sales_invoice
            dn.save(ignore_permissions=False)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "delivery note link to invoice failed")

    return {
        "name": dn.name,
        "status": "Draft",
        "trader_invoice_type": getattr(dn, "trader_invoice_type", "Delivery Challan"),
        "print_format": print_format_for_doc(dn),
    }


@frappe.whitelist()
def submit_delivery_note(name):
    doc = frappe.get_doc("Delivery Note", name)
    doc.check_permission("submit")
    doc.submit()
    frappe.db.commit()
    return {"name": doc.name, "status": "Submitted"}


@frappe.whitelist()
def cancel_delivery_note(name):
    doc = frappe.get_doc("Delivery Note", name)
    doc.check_permission("cancel")
    doc.cancel()
    frappe.db.commit()
    return {"name": doc.name, "status": "Cancelled"}


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
        company = resolve_active_company(company)
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

def _ensure_stock_available(item_code, warehouse, qty, company):
    """Block invoice creation when update_stock would oversell a warehouse."""
    if not frappe.db.exists("Warehouse", warehouse):
        frappe.throw(_("Warehouse {0} does not exist.").format(warehouse))

    wh_company = frappe.get_cached_value("Warehouse", warehouse, "company")
    if wh_company and wh_company != company:
        frappe.throw(_("Warehouse {0} does not belong to company {1}.").format(warehouse, company))

    available = flt(frappe.db.get_value(
        "Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty"
    ) or 0)
    if available < flt(qty):
        frappe.throw(
            _("Insufficient stock for {0} in {1}. Available: {2}, required: {3}.").format(
                item_code, warehouse, available, qty
            )
        )


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



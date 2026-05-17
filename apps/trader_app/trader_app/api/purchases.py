# -*- coding: utf-8 -*-
"""Trader App — Purchases API.

Whitelisted endpoints for the Purchases module:
- Purchase Invoice CRUD
- Purchase Order CRUD
- Supplier analytics
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
    resolve_purchase_taxes,
    set_trader_invoice_type,
    print_format_for_doc,
)


# ────────────────────────────────────────────────────────────────
# 1.  LIST ENDPOINTS
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_purchase_document_catalog():
    """Return purchase-side document types the UI can create."""
    from trader_app.setup.custom_fields import ensure_custom_fields

    ensure_custom_fields()
    return {"documents": get_document_catalog("purchases")}


@frappe.whitelist()
def get_purchase_invoices(company=None, supplier=None, status=None,
                          from_date=None, to_date=None,
                          invoice_type=None,
                          page=1, page_size=20, search=None):
    """Paginated Purchase Invoices."""
    company = resolve_active_company(company)
    page = cint(page) or 1
    page_size = min(cint(page_size) or 20, 100)
    offset = (page - 1) * page_size

    conditions = ["pi.company = %(company)s", "pi.docstatus IN (0, 1)"]
    params = {"company": company}

    if supplier:
        conditions.append("pi.supplier = %(supplier)s")
        params["supplier"] = supplier

    if status == "Paid":
        conditions.append("pi.outstanding_amount <= 0 AND pi.docstatus = 1")
    elif status == "Unpaid":
        conditions.append("pi.outstanding_amount > 0 AND pi.docstatus = 1")
    elif status == "Overdue":
        conditions.append("pi.outstanding_amount > 0 AND pi.docstatus = 1 AND pi.due_date < %(today)s")
        params["today"] = nowdate()
    elif status == "Draft":
        conditions.append("pi.docstatus = 0")

    if from_date:
        conditions.append("pi.posting_date >= %(from_date)s")
        params["from_date"] = from_date
    if to_date:
        conditions.append("pi.posting_date <= %(to_date)s")
        params["to_date"] = to_date
    if search:
        conditions.append("(pi.name LIKE %(search)s OR pi.supplier LIKE %(search)s)")
        params["search"] = f"%{search}%"

    if invoice_type and frappe.db.has_column("Purchase Invoice", "trader_invoice_type"):
        if invoice_type == "debit_note":
            conditions.append("pi.is_return = 1")
        else:
            label = normalize_type_key(invoice_type, is_return=0)
            conditions.append("pi.trader_invoice_type = %(invoice_type_label)s")
            params["invoice_type_label"] = label

    where = " AND ".join(conditions)

    type_select = (
        ", pi.trader_invoice_type, pi.is_return, pi.return_against"
        if frappe.db.has_column("Purchase Invoice", "trader_invoice_type")
        else ", NULL AS trader_invoice_type, pi.is_return, pi.return_against"
    )

    total = frappe.db.sql(
        f"SELECT COUNT(*) FROM `tabPurchase Invoice` pi WHERE {where}", params
    )[0][0]

    rows = frappe.db.sql(f"""
        SELECT pi.name, pi.supplier, pi.supplier_name, pi.posting_date,
               pi.due_date, pi.grand_total, pi.outstanding_amount,
               pi.currency, pi.docstatus
               {type_select},
               CASE
                   WHEN pi.docstatus = 0 THEN 'Draft'
                   WHEN pi.docstatus = 2 THEN 'Cancelled'
                   WHEN pi.outstanding_amount <= 0 THEN 'Paid'
                   WHEN pi.due_date < CURDATE() AND pi.outstanding_amount > 0 THEN 'Overdue'
                   WHEN pi.outstanding_amount < pi.grand_total THEN 'Partly Paid'
                   ELSE 'Unpaid'
               END AS status
        FROM `tabPurchase Invoice` pi
        WHERE {where}
        ORDER BY pi.posting_date DESC, pi.creation DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


@frappe.whitelist()
def get_purchase_invoice_detail(name):
    """Full Purchase Invoice with items."""
    doc = frappe.get_doc("Purchase Invoice", name)
    doc.check_permission("read")
    assert_document_company_access(doc.company)
    return doc.as_dict()


@frappe.whitelist()
def get_purchase_orders(company=None, supplier=None, status=None,
                        from_date=None, to_date=None,
                        page=1, page_size=20, search=None):
    """Paginated Purchase Orders."""
    company = resolve_active_company(company)
    page = cint(page) or 1
    page_size = min(cint(page_size) or 20, 100)
    offset = (page - 1) * page_size

    conditions = ["po.company = %(company)s", "po.docstatus IN (0, 1)"]
    params = {"company": company}

    if supplier:
        conditions.append("po.supplier = %(supplier)s")
        params["supplier"] = supplier
    if status:
        conditions.append("po.status = %(status)s")
        params["status"] = status
    if from_date:
        conditions.append("po.transaction_date >= %(from_date)s")
        params["from_date"] = from_date
    if to_date:
        conditions.append("po.transaction_date <= %(to_date)s")
        params["to_date"] = to_date
    if search:
        conditions.append("(po.name LIKE %(search)s OR po.supplier LIKE %(search)s)")
        params["search"] = f"%{search}%"

    where = " AND ".join(conditions)

    total = frappe.db.sql(
        f"SELECT COUNT(*) FROM `tabPurchase Order` po WHERE {where}", params
    )[0][0]

    rows = frappe.db.sql(f"""
        SELECT po.name, po.supplier, po.supplier_name,
               po.transaction_date, po.grand_total, po.status,
               po.currency, po.docstatus
        FROM `tabPurchase Order` po
        WHERE {where}
        ORDER BY po.transaction_date DESC, po.creation DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    order_names = [row.name for row in rows]
    invoice_counts = {}
    unpaid_counts = {}
    if order_names:
        linked_invoices = frappe.db.sql("""
            SELECT DISTINCT pii.purchase_order, pi.outstanding_amount
            FROM `tabPurchase Invoice Item` pii
            JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
            WHERE pii.purchase_order IN %(order_names)s AND pi.docstatus < 2
        """, {"order_names": order_names}, as_dict=True)
        for invoice in linked_invoices:
            purchase_order = invoice.get("purchase_order")
            invoice_counts[purchase_order] = invoice_counts.get(purchase_order, 0) + 1
            if flt(invoice.get("outstanding_amount")) > 0:
                unpaid_counts[purchase_order] = unpaid_counts.get(purchase_order, 0) + 1

    for row in rows:
        row["linked_invoice_count"] = invoice_counts.get(row.name, 0)
        row["unpaid_invoice_count"] = unpaid_counts.get(row.name, 0)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


@frappe.whitelist()
def get_material_requests(company=None, status=None, from_date=None, to_date=None,
                          page=1, page_size=20, search=None):
    """Paginated purchase requisitions backed by Material Request."""
    company = resolve_active_company(company)
    page = cint(page) or 1
    page_size = min(cint(page_size) or 20, 100)
    offset = (page - 1) * page_size

    conditions = [
        "mr.company = %(company)s",
        "mr.docstatus IN (0, 1)",
        "mr.material_request_type = 'Purchase'",
    ]
    params = {"company": company}

    if status:
        if status == 'Draft':
            conditions.append("mr.docstatus = 0")
        else:
            conditions.append("mr.status = %(status)s")
            params['status'] = status
    if from_date:
        conditions.append("mr.transaction_date >= %(from_date)s")
        params['from_date'] = from_date
    if to_date:
        conditions.append("mr.transaction_date <= %(to_date)s")
        params['to_date'] = to_date
    if search:
        conditions.append("(mr.name LIKE %(search)s OR mr.title LIKE %(search)s)")
        params['search'] = f"%{search}%"

    where = " AND ".join(conditions)

    total = frappe.db.sql(
        f"SELECT COUNT(*) FROM `tabMaterial Request` mr WHERE {where}", params
    )[0][0]

    rows = frappe.db.sql(f"""
        SELECT mr.name, mr.transaction_date, mr.schedule_date,
               mr.status, mr.docstatus, mr.per_ordered,
               mr.material_request_type, mr.company
        FROM `tabMaterial Request` mr
        WHERE {where}
        ORDER BY mr.transaction_date DESC, mr.creation DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, 'page_size': page_size, 'offset': offset}, as_dict=True)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


@frappe.whitelist()
def get_material_request_detail(name):
    """Full purchase requisition detail."""
    doc = frappe.get_doc("Material Request", name)
    doc.check_permission("read")
    if doc.company:
        assert_document_company_access(doc.company)
    return doc.as_dict()


@frappe.whitelist()
def get_supplier_quotations(company=None, supplier=None, status=None, from_date=None, to_date=None,
                            page=1, page_size=20, search=None):
    """Paginated RFQs backed by Supplier Quotation."""
    company = resolve_active_company(company)
    page = cint(page) or 1
    page_size = min(cint(page_size) or 20, 100)
    offset = (page - 1) * page_size

    conditions = ["sq.company = %(company)s", "sq.docstatus IN (0, 1)"]
    params = {"company": company}

    if supplier:
        conditions.append("sq.supplier = %(supplier)s")
        params['supplier'] = supplier
    if status:
        if status == 'Draft':
            conditions.append("sq.docstatus = 0")
        else:
            conditions.append("sq.status = %(status)s")
            params['status'] = status
    if from_date:
        conditions.append("sq.transaction_date >= %(from_date)s")
        params['from_date'] = from_date
    if to_date:
        conditions.append("sq.transaction_date <= %(to_date)s")
        params['to_date'] = to_date
    if search:
        conditions.append("(sq.name LIKE %(search)s OR sq.supplier_name LIKE %(search)s OR sq.supplier = %(supplier_search)s)")
        params['search'] = f"%{search}%"
        params['supplier_search'] = search

    where = " AND ".join(conditions)

    total = frappe.db.sql(
        f"SELECT COUNT(*) FROM `tabSupplier Quotation` sq WHERE {where}", params
    )[0][0]

    rows = frappe.db.sql(f"""
        SELECT sq.name, sq.supplier, sq.supplier_name, sq.transaction_date,
               sq.valid_till, sq.grand_total, sq.currency, sq.status, sq.docstatus
        FROM `tabSupplier Quotation` sq
        WHERE {where}
        ORDER BY sq.transaction_date DESC, sq.creation DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, 'page_size': page_size, 'offset': offset}, as_dict=True)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


@frappe.whitelist()
def get_supplier_quotation_detail(name):
    """Full supplier quotation detail."""
    doc = frappe.get_doc("Supplier Quotation", name)
    doc.check_permission("read")
    assert_document_company_access(doc.company)
    data = doc.as_dict()

    comparison_quotes = []
    quoted_item_codes = [item.get('item_code') for item in data.get('items', []) if item.get('item_code')]

    if data.get('material_request'):
        comparison_quotes = frappe.get_all(
            'Supplier Quotation',
            filters={
                'material_request': data.get('material_request'),
                'docstatus': ['<', 2],
            },
            fields=['name', 'supplier', 'supplier_name', 'transaction_date', 'valid_till', 'grand_total', 'currency', 'status', 'docstatus'],
            order_by='transaction_date desc, creation desc',
        )

    item_comparisons = {}
    if comparison_quotes and quoted_item_codes:
        quote_names = [row.get('name') for row in comparison_quotes]
        rows = frappe.get_all(
            'Supplier Quotation Item',
            filters={
                'parent': ['in', quote_names],
                'item_code': ['in', quoted_item_codes],
            },
            fields=['parent', 'item_code', 'qty', 'rate', 'amount'],
            order_by='item_code asc, rate asc',
        )
        for row in rows:
            item_comparisons.setdefault(row.get('item_code'), []).append(row)

    data['comparison_quotes'] = comparison_quotes
    data['item_comparisons'] = item_comparisons
    return data


@frappe.whitelist()
def get_purchase_order_detail(name):
    """Full Purchase Order with items."""
    doc = frappe.get_doc("Purchase Order", name)
    doc.check_permission("read")
    assert_document_company_access(doc.company)
    data = doc.as_dict()
    data["linked_purchase_invoices"] = frappe.db.sql("""
        SELECT DISTINCT pi.name, pi.posting_date, pi.grand_total,
               pi.currency, pi.status, pi.outstanding_amount
        FROM `tabPurchase Invoice Item` pii
        JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        WHERE pii.purchase_order = %(po_name)s AND pi.docstatus < 2
        ORDER BY pi.posting_date DESC, pi.creation DESC
    """, {"po_name": doc.name}, as_dict=True)
    return data


# ────────────────────────────────────────────────────────────────
# 2.  CREATE / SUBMIT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def create_purchase_invoice(supplier, items, company=None, posting_date=None,
                            due_date=None, taxes_and_charges=None,
                            tax_inclusive=0,
                            is_return=0, return_against=None,
                            update_stock=1, invoice_type=None,
                            currency=None, exchange_rate=None):
    """Create a Purchase Invoice.

    Parameters
    ----------
    supplier : str
    items : list of dict — each with item_code, qty, rate
    tax_inclusive : int — default 0; pass 1 for tax-inclusive pricing
    is_return : int — default 0; pass 1 to create a debit note (purchase return)
    return_against : str — source Purchase Invoice name when is_return=1
    update_stock : int — default 1; pass 0 for invoice-only entries
    """
    import json
    if isinstance(items, str):
        items = json.loads(items)

    company = resolve_active_company(company)
    abbr = frappe.get_cached_value("Company", company, "abbr")

    pi = frappe.new_doc("Purchase Invoice")
    pi.company = company
    pi.supplier = supplier
    pi.posting_date = posting_date or nowdate()
    pi.due_date = due_date or pi.posting_date
    pi.update_stock = cint(update_stock)
    pi.is_return = cint(is_return)
    if return_against:
        pi.return_against = return_against

    from trader_app.api.currency import apply_document_currency
    apply_document_currency(
        pi,
        currency=currency,
        exchange_rate=exchange_rate,
        posting_date=pi.posting_date,
        for_selling=False,
    )

    set_trader_invoice_type(pi, invoice_type=invoice_type, is_return=is_return)
    taxes_and_charges = resolve_purchase_taxes(company, invoice_type, taxes_and_charges)

    default_warehouse = f"Main Warehouse - {abbr}"
    seen_serials = set()
    for item in items:
        item_code = item.get("item_code")
        warehouse = item.get("warehouse") or default_warehouse
        serial_no = (item.get("serial_no") or "").strip()

        if serial_no and not cint(is_return):
            serial_key = serial_no.lower()
            if serial_key in seen_serials:
                frappe.throw(
                    _("Duplicate serial {0} on multiple purchase lines.").format(serial_no)
                )
            seen_serials.add(serial_key)
            from trader_app.api.inventory import check_serial_for_purchase
            result = check_serial_for_purchase(item_code, serial_no, company=company)
            if not result.get("valid"):
                frappe.throw(result.get("message") or _("Invalid serial number."))

        row = {
            "item_code": item_code,
            "qty": -abs(flt(item.get("qty", 1))) if cint(is_return) else flt(item.get("qty", 1)),
            "rate": flt(item.get("rate", 0)),
            "warehouse": warehouse,
        }
        if serial_no:
            row["serial_no"] = serial_no
        pi.append("items", row)

    if taxes_and_charges:
        pi.taxes_and_charges = taxes_and_charges
        pi.run_method("set_taxes")
        if cint(tax_inclusive):
            for tax_row in pi.taxes:
                tax_row.included_in_print_rate = 1

    pi.insert(ignore_permissions=False)
    return {
        "name": pi.name,
        "status": "Draft",
        "trader_invoice_type": getattr(pi, "trader_invoice_type", None),
        "print_format": print_format_for_doc(pi),
    }


@frappe.whitelist()
def create_purchase_order(supplier, items, company=None, transaction_date=None,
                          schedule_date=None, taxes_and_charges=None,
                          tax_inclusive=0):
    """Create a Purchase Order."""
    import json
    if isinstance(items, str):
        items = json.loads(items)

    company = resolve_active_company(company)
    abbr = frappe.get_cached_value("Company", company, "abbr")

    po = frappe.new_doc("Purchase Order")
    po.company = company
    po.supplier = supplier
    po.transaction_date = transaction_date or nowdate()
    po.schedule_date = schedule_date or po.transaction_date
    po.set_warehouse = f"Main Warehouse - {abbr}"

    for item in items:
        po.append("items", {
            "item_code": item.get("item_code"),
            "qty": flt(item.get("qty", 1)),
            "rate": flt(item.get("rate", 0)),
            "warehouse": item.get("warehouse") or f"Main Warehouse - {abbr}",
            "schedule_date": item.get("schedule_date") or schedule_date or po.schedule_date,
        })

    if taxes_and_charges:
        po.taxes_and_charges = taxes_and_charges
        po.run_method("set_taxes")
        if cint(tax_inclusive):
            for tax_row in po.taxes:
                tax_row.included_in_print_rate = 1

    po.insert(ignore_permissions=False)
    return {"name": po.name, "status": "Draft"}


@frappe.whitelist()
def create_purchase_order_from_supplier_quotation(name, company=None, transaction_date=None, schedule_date=None):
    """Create a draft purchase order from a selected supplier quotation."""
    sq = frappe.get_doc('Supplier Quotation', name)
    sq.check_permission('read')

    company = resolve_active_company(company or sq.company)
    abbr = frappe.get_cached_value('Company', company, 'abbr')

    po = frappe.new_doc('Purchase Order')
    po.company = company
    po.supplier = sq.supplier
    po.transaction_date = transaction_date or sq.transaction_date or nowdate()
    po.schedule_date = schedule_date or sq.valid_till or po.transaction_date
    po.set_warehouse = f"Main Warehouse - {abbr}"

    if getattr(sq, 'material_request', None):
        po.material_request = sq.material_request

    for item in sq.items:
        po.append('items', {
            'item_code': item.item_code,
            'qty': flt(item.qty or 1),
            'rate': flt(item.rate or 0),
            'warehouse': getattr(item, 'warehouse', None) or f"Main Warehouse - {abbr}",
            'schedule_date': schedule_date or sq.valid_till or sq.transaction_date or nowdate(),
            'supplier_quotation': sq.name,
            'material_request': getattr(item, 'material_request', None) or getattr(sq, 'material_request', None),
        })

    po.insert(ignore_permissions=False)
    return {'name': po.name, 'status': 'Draft'}


@frappe.whitelist()
def create_material_request(items, company=None, transaction_date=None, schedule_date=None, title=None):
    """Create a purchase requisition using Material Request."""
    import json
    if isinstance(items, str):
        items = json.loads(items)

    company = resolve_active_company(company)
    abbr = frappe.get_cached_value("Company", company, "abbr")

    mr = frappe.new_doc("Material Request")
    mr.company = company
    mr.material_request_type = 'Purchase'
    mr.transaction_date = transaction_date or nowdate()
    mr.schedule_date = schedule_date or mr.transaction_date
    if title:
        mr.title = title

    for item in items:
        mr.append('items', {
            'item_code': item.get('item_code'),
            'qty': flt(item.get('qty', 1)),
            'schedule_date': item.get('schedule_date') or schedule_date or mr.schedule_date,
            'warehouse': item.get('warehouse') or f"Main Warehouse - {abbr}",
            'rate': flt(item.get('rate', 0)),
        })

    mr.insert(ignore_permissions=False)
    return {'name': mr.name, 'status': 'Draft'}


@frappe.whitelist()
def create_supplier_quotation(supplier, items, company=None, transaction_date=None, valid_till=None,
                              material_request=None, taxes_and_charges=None, tax_inclusive=0):
    """Create an RFQ using Supplier Quotation."""
    import json
    if isinstance(items, str):
        items = json.loads(items)

    company = resolve_active_company(company)

    sq = frappe.new_doc('Supplier Quotation')
    sq.company = company
    sq.supplier = supplier
    sq.transaction_date = transaction_date or nowdate()
    sq.valid_till = valid_till or sq.transaction_date
    if material_request:
        sq.material_request = material_request

    for item in items:
        sq.append('items', {
            'item_code': item.get('item_code'),
            'qty': flt(item.get('qty', 1)),
            'rate': flt(item.get('rate', 0)),
            'material_request': item.get('material_request') or material_request,
        })

    if taxes_and_charges:
        sq.taxes_and_charges = taxes_and_charges
        sq.run_method('set_taxes')
        if cint(tax_inclusive):
            for tax_row in sq.taxes:
                tax_row.included_in_print_rate = 1

    sq.insert(ignore_permissions=False)
    return {'name': sq.name, 'status': 'Draft'}


@frappe.whitelist()
def submit_purchase_invoice(name):
    """Submit a draft Purchase Invoice."""
    doc = frappe.get_doc("Purchase Invoice", name)
    doc.check_permission("submit")
    doc.submit()
    frappe.db.commit()
    return {"name": doc.name, "status": "Submitted"}


@frappe.whitelist()
def submit_purchase_order(name):
    """Submit a draft Purchase Order."""
    doc = frappe.get_doc("Purchase Order", name)
    doc.check_permission("submit")
    doc.submit()
    frappe.db.commit()
    return {"name": doc.name, "status": "Submitted"}


@frappe.whitelist()
def submit_material_request(name):
    """Submit a draft purchase requisition."""
    doc = frappe.get_doc('Material Request', name)
    doc.check_permission('submit')
    doc.submit()
    frappe.db.commit()
    return {'name': doc.name, 'status': 'Submitted'}


@frappe.whitelist()
def submit_supplier_quotation(name):
    """Submit a draft supplier quotation / RFQ."""
    doc = frappe.get_doc('Supplier Quotation', name)
    doc.check_permission('submit')
    doc.submit()
    frappe.db.commit()
    return {'name': doc.name, 'status': 'Submitted'}


@frappe.whitelist()
def cancel_purchase_invoice(name):
    """Cancel a submitted Purchase Invoice."""
    doc = frappe.get_doc("Purchase Invoice", name)
    doc.check_permission("cancel")
    doc.cancel()
    frappe.db.commit()
    return {"name": doc.name, "status": "Cancelled"}


@frappe.whitelist()
def cancel_purchase_order(name):
    """Cancel a submitted Purchase Order."""
    doc = frappe.get_doc("Purchase Order", name)
    doc.check_permission("cancel")
    doc.cancel()
    frappe.db.commit()
    return {"name": doc.name, "status": "Cancelled"}


@frappe.whitelist()
def cancel_material_request(name):
    """Cancel a submitted Material Request."""
    doc = frappe.get_doc("Material Request", name)
    doc.check_permission("cancel")
    doc.cancel()
    frappe.db.commit()
    return {"name": doc.name, "status": "Cancelled"}


@frappe.whitelist()
def cancel_supplier_quotation(name):
    """Cancel a submitted Supplier Quotation."""
    doc = frappe.get_doc("Supplier Quotation", name)
    doc.check_permission("cancel")
    doc.cancel()
    frappe.db.commit()
    return {"name": doc.name, "status": "Cancelled"}


# ────────────────────────────────────────────────────────────────
# 3.  PURCHASE SUMMARY
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_purchase_summary(company=None):
    """Aggregate purchase stats."""
    company = resolve_active_company(company)
    today = nowdate()
    first_of_month = getdate(today).replace(day=1).isoformat()

    total_invoices = cint(frappe.db.sql("""
        SELECT COUNT(*) FROM `tabPurchase Invoice`
        WHERE company = %s AND docstatus = 1
    """, (company,))[0][0])

    monthly_purchases = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0) FROM `tabPurchase Invoice`
        WHERE company = %s AND docstatus = 1
              AND posting_date >= %s AND posting_date <= %s
    """, (company, first_of_month, today))[0][0])

    total_outstanding = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0) FROM `tabPurchase Invoice`
        WHERE company = %s AND docstatus = 1 AND outstanding_amount > 0
    """, (company,))[0][0])

    total_suppliers = cint(frappe.db.count("Supplier", {"disabled": 0}))

    return {
        "total_invoices": total_invoices,
        "monthly_purchases": monthly_purchases,
        "total_outstanding": total_outstanding,
        "total_suppliers": total_suppliers,
    }


# ────────────────────────────────────────────────────────────────
# 4.  DOCTYPE EVENT HOOKS
# ────────────────────────────────────────────────────────────────

def validate_purchase_invoice(doc, method):
    """Runs on Purchase Invoice validate."""
    pass  # placeholder for custom validation


def on_purchase_invoice_submit(doc, method):
    """Runs on Purchase Invoice submit."""
    frappe.publish_realtime(
        "purchase_invoice_submitted",
        {"invoice": doc.name, "supplier": doc.supplier, "total": doc.grand_total},
        user=frappe.session.user,
    )


def on_purchase_invoice_cancel(doc, method):
    """Runs on Purchase Invoice cancel."""
    frappe.publish_realtime(
        "purchase_invoice_cancelled",
        {"invoice": doc.name},
        user=frappe.session.user,
    )


# ────────────────────────────────────────────────────────────────
#    HELPERS
# ────────────────────────────────────────────────────────────────


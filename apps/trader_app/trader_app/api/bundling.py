# -*- coding: utf-8 -*-
"""Trader App — Item Bundling / Grouping API.

Enables grouping multiple inventory items into a single "bundle" line
on Quotations, Sales Orders, and Sales Invoices.  Each bundle has an
overarching description that masks the individual sub-items.

Two viewing modes:
  - External (client-facing): shows only the bundle description + total
  - Internal (staff-facing): shows both the bundle description AND the
    individual items within it
"""

from __future__ import unicode_literals

import json

import frappe
from frappe import _
from trader_app.api.company import resolve_active_company
from frappe.utils import flt, cint, nowdate


# ────────────────────────────────────────────────────────────────
# 1.  ITEM BUNDLE CRUD
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_item_bundles(search=None, page=1, page_size=50):
    """List all saved item bundles."""
    page = cint(page) or 1
    page_size = min(cint(page_size) or 50, 200)
    offset = (page - 1) * page_size

    conditions = ["1=1"]
    params = {}

    if search:
        conditions.append(
            "(bundle_name LIKE %(search)s OR description LIKE %(search)s)"
        )
        params["search"] = f"%{search}%"

    where = " AND ".join(conditions)

    total = frappe.db.sql(
        f"SELECT COUNT(*) FROM `tabItem Bundle` WHERE {where}", params
    )[0][0]

    rows = frappe.db.sql(f"""
        SELECT name, bundle_name, description, total_rate, creation
        FROM `tabItem Bundle`
        WHERE {where}
        ORDER BY creation DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    # Attach sub-item counts
    bundle_names = [r.name for r in rows]
    if bundle_names:
        sub_counts = frappe.db.sql("""
            SELECT parent, COUNT(*) AS cnt
            FROM `tabItem Bundle Detail`
            WHERE parent IN %(names)s
            GROUP BY parent
        """, {"names": bundle_names}, as_dict=True)
        count_map = {r.parent: r.cnt for r in sub_counts}
        for row in rows:
            row["item_count"] = count_map.get(row.name, 0)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


@frappe.whitelist()
def get_item_bundle_detail(name):
    """Return full bundle definition with sub-items."""
    if not frappe.db.exists("Item Bundle", name):
        frappe.throw(_("Bundle {0} not found").format(name))

    doc = frappe.get_doc("Item Bundle", name)
    data = doc.as_dict()
    return data


@frappe.whitelist()
def create_item_bundle(bundle_name, description, items):
    """Create a new item bundle.

    Parameters
    ----------
    bundle_name : str   — Display name for the bundle
    description : str   — Overarching description shown on external docs
    items : list[dict]  — Each with item_code, qty, rate (optional)
    """
    if isinstance(items, str):
        items = json.loads(items)

    if not bundle_name or not bundle_name.strip():
        frappe.throw(_("Bundle name is required"))
    if not items or len(items) == 0:
        frappe.throw(_("At least one item is required in a bundle"))

    doc = frappe.new_doc("Item Bundle")
    doc.bundle_name = bundle_name.strip()
    doc.description = (description or "").strip()
    doc.total_rate = 0

    for item in items:
        item_code = item.get("item_code")
        qty = flt(item.get("qty", 1))
        rate = flt(item.get("rate", 0))
        if not item_code:
            continue
        doc.append("items", {
            "item_code": item_code,
            "qty": qty,
            "rate": rate,
            "amount": flt(qty * rate),
        })
        doc.total_rate += flt(qty * rate)

    doc.insert(ignore_permissions=False)
    return {"name": doc.name, "bundle_name": doc.bundle_name}


@frappe.whitelist()
def update_item_bundle(name, bundle_name=None, description=None, items=None):
    """Update an existing item bundle."""
    doc = frappe.get_doc("Item Bundle", name)

    if bundle_name is not None:
        doc.bundle_name = bundle_name.strip()
    if description is not None:
        doc.description = description.strip()

    if items is not None:
        if isinstance(items, str):
            items = json.loads(items)
        doc.items = []
        doc.total_rate = 0
        for item in items:
            item_code = item.get("item_code")
            qty = flt(item.get("qty", 1))
            rate = flt(item.get("rate", 0))
            if not item_code:
                continue
            doc.append("items", {
                "item_code": item_code,
                "qty": qty,
                "rate": rate,
                "amount": flt(qty * rate),
            })
            doc.total_rate += flt(qty * rate)

    doc.save(ignore_permissions=False)
    return {"name": doc.name, "bundle_name": doc.bundle_name}


@frappe.whitelist()
def delete_item_bundle(name):
    """Delete an item bundle."""
    frappe.delete_doc("Item Bundle", name, ignore_permissions=False)
    return {"ok": True}


# ────────────────────────────────────────────────────────────────
# 2.  EXPAND BUNDLE FOR DOCUMENT CREATION
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def expand_bundle(name):
    """Return the sub-items for a bundle for insertion into a document.

    Returns a list of dicts with item_code, qty, rate, amount.
    """
    if not frappe.db.exists("Item Bundle", name):
        frappe.throw(_("Bundle {0} not found").format(name))

    doc = frappe.get_doc("Item Bundle", name)
    return {
        "bundle_name": doc.bundle_name,
        "description": doc.description,
        "total_rate": doc.total_rate,
        "items": [
            {
                "item_code": d.item_code,
                "qty": d.qty,
                "rate": d.rate,
                "amount": d.amount,
            }
            for d in doc.items
        ],
    }

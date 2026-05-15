# -*- coding: utf-8 -*-
"""Generator — preset Item Bundles + inter-warehouse transfers."""

from __future__ import unicode_literals

import random

import frappe
from frappe.utils import add_days, flt, getdate, nowdate

from trader_app.demo.seed_engine.base import BaseGenerator


BUNDLE_BLUEPRINTS = [
    (
        "Demo Pack FMCG Starter",
        "Sample FMCG bundle for quotes and invoices.",
        3,
        (0.92, 1.02),
    ),
    (
        "Demo Pack Hardware Kit",
        "Tools starter kit bundle.",
        3,
        (0.90, 1.05),
    ),
    (
        "Demo Pack Electrical Basics",
        "Cable + fitting combo.",
        3,
        (0.93, 1.04),
    ),
    (
        "Demo Pack Office Consumables",
        "Desk and cleaning consumables.",
        4,
        (0.88, 1.06),
    ),
]


class BundlesTransfersGenerator(BaseGenerator):
    name = "BundlesTransfers"
    depends_on = ["Company", "Items", "Inventory"]

    def generate(self):
        self._suppress_notifications()
        try:
            self._seed_bundles()
            self._seed_transfers()
            frappe.db.commit()
        finally:
            self._restore_notifications()

    def _seed_bundles(self):
        items = frappe.get_all(
            "Item",
            filters={"is_stock_item": 1, "disabled": 0},
            fields=["name"],
            limit_page_length=0,
        )
        if not items:
            print("  ⚠️  No items for bundles")
            return

        codes = [r.name for r in items]
        buying = {}
        for ip in frappe.get_all(
            "Item Price",
            filters={"price_list": "Standard Buying"},
            fields=["item_code", "price_list_rate"],
            limit_page_length=0,
        ):
            buying[ip.item_code] = flt(ip.price_list_rate)

        for title, desc, n_lines, rate_jitter in BUNDLE_BLUEPRINTS:
            if frappe.db.exists("Item Bundle", {"bundle_name": title}):
                continue
            picked = random.sample(codes, min(n_lines, len(codes)))
            doc = frappe.new_doc("Item Bundle")
            doc.bundle_name = title
            doc.description = desc
            doc.total_rate = 0
            for ic in picked:
                base = buying.get(ic, random.uniform(80, 1200))
                rate = round(
                    base * random.uniform(rate_jitter[0], rate_jitter[1]), 2
                )
                qty = random.choice([1, 1, 2])
                amt = flt(qty * rate)
                doc.append(
                    "items",
                    {
                        "item_code": ic,
                        "qty": qty,
                        "rate": rate,
                        "amount": amt,
                    },
                )
                doc.total_rate += amt
            try:
                doc.insert(ignore_permissions=True)
                self.created_records.append(("Item Bundle", doc.name))
            except Exception as e:
                self.errors.append("Bundle %s: %s" % (title, str(e)))

        print("  ✅ Item Bundles preset")

    def _ensure_transfer_stock_entry_type(self):
        if frappe.db.exists("Stock Entry Type", "Material Transfer"):
            return
        doc = frappe.get_doc({
            "doctype": "Stock Entry Type",
            "name": "Material Transfer",
            "stock_entry_type": "Material Transfer",
            "purpose": "Material Transfer",
        })
        doc.insert(ignore_permissions=True)

    def _seed_transfers(self):
        self._ensure_transfer_stock_entry_type()
        company = self.config["company_name"]
        abbr = self.config["company_abbr"]
        main = "Main Warehouse - %s" % abbr
        sec = "Secondary Warehouse - %s" % abbr
        retail = "Retail Warehouse - %s" % abbr

        pairs = [
            (main, sec),
            (sec, main),
            (main, retail),
            (retail, main),
            (sec, retail),
            (retail, sec),
        ]
        lo, hi = self.config["num_inter_warehouse_transfers"]
        n = random.randint(lo, hi)

        rows = frappe.db.sql(
            """
            SELECT b.item_code, i.item_name, i.stock_uom, b.warehouse, b.actual_qty
            FROM `tabBin` b
            INNER JOIN `tabItem` i ON i.name = b.item_code
            INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
            WHERE w.company = %s AND b.actual_qty > 15
            ORDER BY RAND()
            LIMIT 400
            """,
            (company,),
            as_dict=True,
        )
        if not rows:
            print("  ⚠️  No bins for transfers")
            return

        by_wh = {}
        for r in rows:
            by_wh.setdefault(r.warehouse, []).append(r)

        for k in range(n):
            s_wh, t_wh = random.choice(pairs)
            src_pool = by_wh.get(s_wh) or []
            if not src_pool:
                continue
            row = random.choice(src_pool)
            move_qty = max(
                1,
                min(
                    int(row.actual_qty * random.uniform(0.05, 0.22)),
                    int(row.actual_qty) - 1,
                ),
            )
            if move_qty < 1:
                continue

            start_demo = getdate(self.config["demo_start_date"])
            end_demo = getdate(self.config["demo_end_date"])
            nd = getdate(nowdate())
            if end_demo > nd:
                end_demo = nd
            span_days = max(1, (end_demo - start_demo).days)
            posting = add_days(start_demo, random.randint(0, span_days))
            if getdate(posting) > nd:
                posting = nd

            se = frappe.get_doc(
                {
                    "doctype": "Stock Entry",
                    "purpose": "Material Transfer",
                    "stock_entry_type": "Material Transfer",
                    "company": company,
                    "posting_date": posting,
                    "posting_time": "11:30:00",
                    "items": [
                        {
                            "item_code": row.item_code,
                            "item_name": row.item_name,
                            "qty": move_qty,
                            "uom": row.stock_uom,
                            "stock_uom": row.stock_uom,
                            "conversion_factor": 1,
                            "s_warehouse": s_wh,
                            "t_warehouse": t_wh,
                        }
                    ],
                }
            )
            try:
                se.insert(ignore_permissions=True)
                se.submit()
                self.created_records.append(("Stock Entry Transfer", se.name))
            except Exception as e:
                self.errors.append("Transfer: %s" % str(e))

            if (k + 1) % 5 == 0:
                frappe.db.commit()

        print("  ✅ Inter-warehouse transfers: %s" % n)

    def validate(self):
        n = frappe.db.sql(
            "SELECT COUNT(*) FROM `tabItem Bundle` WHERE bundle_name LIKE %s",
            ("Demo Pack%",),
        )[0][0]
        assert int(n or 0) >= 1, "Demo bundles missing"
        return True

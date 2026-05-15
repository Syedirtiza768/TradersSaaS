# -*- coding: utf-8 -*-
"""Generator — Material Request + Supplier Quotation samples."""

from __future__ import unicode_literals

import random

import frappe
from frappe.utils import add_days, flt, getdate, nowdate

from trader_app.demo.seed_engine.base import BaseGenerator


class RequisitionsGenerator(BaseGenerator):
    name = "Requisitions"

    depends_on = ["Company", "Suppliers", "Items"]

    def generate(self):
        self._suppress_notifications()
        try:
            company = self.config["company_name"]
            abbr = self.config["company_abbr"]
            main_wh = "Main Warehouse - %s" % abbr

            suppliers = frappe.get_all(
                "Supplier", filters={"disabled": 0}, pluck="name"
            )
            items = frappe.get_all(
                "Item",
                filters={"is_stock_item": 1, "disabled": 0, "is_purchase_item": 1},
                fields=["name", "item_name", "stock_uom"],
                limit_page_length=0,
            )
            if not suppliers or not items:
                print("  ⚠️  No suppliers/items; skipping MR/SQ seed")
                return

            buying = {}
            for ip in frappe.get_all(
                "Item Price",
                filters={"price_list": "Standard Buying"},
                fields=["item_code", "price_list_rate"],
                limit_page_length=0,
            ):
                buying[ip.item_code] = flt(ip.price_list_rate)

            start = getdate(self.config["demo_start_date"])

            mr_lo, mr_hi = self.config["num_material_requests"]
            n_mr = random.randint(mr_lo, mr_hi)
            mr_names = []

            print("  📝 Material Requests: %s" % n_mr)
            for i in range(n_mr):
                tr = add_days(start, random.randint(0, 240))
                if getdate(tr) > getdate(nowdate()):
                    tr = nowdate()
                picks = random.sample(
                    items, min(random.randint(2, 5), len(items))
                )

                mr = frappe.new_doc("Material Request")
                mr.company = company
                mr.material_request_type = "Purchase"
                mr.transaction_date = tr
                mr.schedule_date = add_days(tr, random.randint(3, 21))
                mr.title = random.choice(
                    [
                        "Store replenishment",
                        "Weekly stock pull",
                        "Promo buildup",
                        "Branch request",
                        "Core SKU restock",
                    ]
                )

                for row in picks:
                    qty = random.randint(5, 120)
                    mr.append(
                        "items",
                        {
                            "item_code": row["name"],
                            "item_name": row.get("item_name", row["name"]),
                            "qty": qty,
                            "schedule_date": mr.schedule_date,
                            "warehouse": main_wh,
                            "rate": buying.get(row["name"], random.uniform(50, 900)),
                            "uom": row.get("stock_uom", "Nos"),
                            "stock_uom": row.get("stock_uom", "Nos"),
                        },
                    )

                try:
                    mr.insert(ignore_permissions=True)
                    self.created_records.append(("Material Request", mr.name))
                    mr_names.append(mr.name)
                    if random.random() < 0.72:
                        mr.submit()
                        self.created_records.append(
                            ("Material Request Submit", mr.name)
                        )
                except Exception as e:
                    self.errors.append("MR: %s" % str(e))

                if (i + 1) % 15 == 0:
                    frappe.db.commit()

            sq_lo, sq_hi = self.config["num_supplier_quotations"]
            n_sq = random.randint(sq_lo, sq_hi)
            linked_mr = random.sample(
                mr_names, min(max(1, len(mr_names) // 3), len(mr_names))
            ) if mr_names else []

            print("  📨 Supplier Quotations: %s" % n_sq)
            for j in range(n_sq):
                sup = random.choice(suppliers)
                tr = add_days(start, random.randint(0, 260))
                if getdate(tr) > getdate(nowdate()):
                    tr = nowdate()

                mr_link = linked_mr[j % len(linked_mr)] if linked_mr else None
                mr_doc = frappe.get_doc("Material Request", mr_link) if mr_link else None

                sq = frappe.new_doc("Supplier Quotation")
                sq.company = company
                sq.supplier = sup
                sq.transaction_date = tr
                sq.valid_till = add_days(tr, random.randint(14, 60))
                if mr_link and frappe.db.exists("Material Request", mr_link):
                    sq.material_request = mr_link

                if mr_doc and mr_doc.items:
                    mr_items = mr_doc.items[
                        : max(1, random.randint(1, len(mr_doc.items)))
                    ]
                    for mi in mr_items:
                        base = buying.get(mi.item_code, flt(mi.rate) or 100)
                        sq.append(
                            "items",
                            {
                                "item_code": mi.item_code,
                                "qty": max(1, flt(mi.qty) * random.uniform(0.8, 1.0)),
                                "rate": round(base * random.uniform(0.95, 1.08), 2),
                                "material_request": mr_link,
                            },
                        )
                else:
                    picks = random.sample(
                        items, min(random.randint(2, 6), len(items))
                    )
                    for row in picks:
                        base = buying.get(row["name"], random.uniform(50, 2000))
                        sq.append(
                            "items",
                            {
                                "item_code": row["name"],
                                "qty": random.randint(5, 80),
                                "rate": round(base * random.uniform(0.92, 1.05), 2),
                            },
                        )

                if not sq.items:
                    continue

                try:
                    sq.insert(ignore_permissions=True)
                    self.created_records.append(("Supplier Quotation", sq.name))
                    if random.random() < 0.68:
                        sq.submit()
                        self.created_records.append(
                            ("Supplier Quotation Submit", sq.name)
                        )
                except Exception as e:
                    self.errors.append("SQ: %s" % str(e))

                if (j + 1) % 18 == 0:
                    frappe.db.commit()

            frappe.db.commit()
        finally:
            self._restore_notifications()

    def validate(self):
        c = frappe.db.count(
            "Material Request",
            filters={"company": self.config["company_name"]},
        )
        assert c >= 3, "Material Request seed thin"
        c2 = frappe.db.count(
            "Supplier Quotation",
            filters={"company": self.config["company_name"]},
        )
        assert c2 >= 3, "Supplier Quotation seed thin"
        return True

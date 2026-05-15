# -*- coding: utf-8 -*-
"""Generator — Quotations (draft / submitted).

Seeds Quotations so dashboard “awaiting conversion” and Sales → Quotations tabs
have data. SO/SI linkage is added later in SalesGenerator for a subset.
"""

from __future__ import unicode_literals

import random

import frappe
from frappe.utils import add_days, flt, getdate, nowdate

from trader_app.demo.seed_engine.base import BaseGenerator


class QuotationGenerator(BaseGenerator):
    name = "Quotations"
    depends_on = ["Company", "Customers", "Items"]

    def generate(self):
        self._suppress_notifications()
        try:
            company = self.config["company_name"]
            abbr = self.config["company_abbr"]
            warehouse = f"Main Warehouse - {abbr}"
            start_date = getdate(self.config["demo_start_date"])
            end_date = getdate(self.config["demo_end_date"])
            total_days = max(1, (end_date - start_date).days)

            customers = frappe.get_all(
                "Customer", filters={"disabled": 0}, pluck="name"
            )
            items = frappe.get_all(
                "Item",
                filters={"is_stock_item": 1, "disabled": 0},
                fields=["name", "item_name", "stock_uom"],
                limit_page_length=0,
            )
            if not customers or not items:
                print("  ⚠️  No customers or items; skipping quotations")
                return

            item_prices = {}
            for ip in frappe.get_all(
                "Item Price",
                filters={"price_list": "Standard Selling"},
                fields=["item_code", "price_list_rate"],
                limit_page_length=0,
            ):
                item_prices[ip.item_code] = float(ip.price_list_rate)

            low, high = self.config["num_quotations"]
            num_q = random.randint(low, high)
            submit_fraction = float(
                self.config.get("fraction_quotation_submit", 0.62)
            )

            print(f"  📋 Creating {num_q} Quotations (~{submit_fraction:.0%} submit)")

            for i in range(num_q):
                customer = random.choice(customers)
                day_off = random.randint(0, total_days)
                tr = add_days(start_date, day_off)
                if getdate(tr) > getdate(nowdate()):
                    tr = nowdate()
                selected = random.sample(
                    items, min(random.randint(1, 6), len(items))
                )

                q = frappe.new_doc("Quotation")
                q.company = company
                q.quotation_to = "Customer"
                q.party_name = customer
                q.transaction_date = tr
                q.valid_till = add_days(tr, random.randint(7, 45))
                q.order_type = "Sales"

                remaining = random.uniform(25000, 180000)
                for row in selected:
                    rate = item_prices.get(
                        row["name"], random.uniform(100, 4000)
                    )
                    qty = random.randint(
                        1, max(1, min(8, int(remaining / max(rate, 1))))
                    )
                    line = flt(rate) * qty
                    if line > remaining:
                        continue
                    remaining -= line
                    q.append(
                        "items",
                        {
                            "item_code": row["name"],
                            "item_name": row.get("item_name", row["name"]),
                            "qty": qty,
                            "rate": round(rate, 2),
                            "uom": row.get("stock_uom", "Nos"),
                            "stock_uom": row.get("stock_uom", "Nos"),
                            "conversion_factor": 1,
                            "warehouse": warehouse,
                        },
                    )
                    if remaining < 1500:
                        break

                if not q.items:
                    continue

                try:
                    q.insert(ignore_permissions=True)
                    self.created_records.append(("Quotation", q.name))

                    if random.random() < submit_fraction:
                        q.submit()
                        self.created_records.append(
                            ("Quotation Submitted", q.name)
                        )
                except Exception as e:
                    self.errors.append("Quotation: %s" % str(e))

                if (i + 1) % 25 == 0:
                    frappe.db.commit()

            frappe.db.commit()
            print(f"  ✅ Quotations done ({len(self.errors)} errors)")
        finally:
            self._restore_notifications()

    def validate(self):
        n = frappe.db.count(
            "Quotation",
            filters={"company": self.config["company_name"]},
        )
        lo = self.config["num_quotations"][0] // 4
        assert n >= lo, "Too few Quotations seeded"
        return True

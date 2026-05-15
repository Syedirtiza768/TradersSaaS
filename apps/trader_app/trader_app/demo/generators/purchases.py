# -*- coding: utf-8 -*-
"""Generator — Purchase Orders + Invoices.

Creates a mix of:
- **Standalone** Purchase Invoices (no PO) — matches legacy distributor behaviour
- **PO-backed** Purchase Invoices with `purchase_order` + `po_detail` on lines —
  feeds dashboard PO↔payables KPIs.

Also leaves headroom for enrichment “open pipeline” PO rows.
"""

from __future__ import unicode_literals

import random

import frappe
from frappe.utils import add_days, flt, getdate, nowdate

from trader_app.demo.seed_engine.base import BaseGenerator


class PurchaseGenerator(BaseGenerator):
    name = "Purchases"
    depends_on = ["Company", "Suppliers", "Items"]
    debug_single_doc = False

    def generate(self):
        self._suppress_notifications()
        try:
            company = self.config["company_name"]
            abbr = self.config["company_abbr"]
            start_date = getdate(self.config["demo_start_date"])
            end_date = getdate(self.config["demo_end_date"])
            warehouse = "Main Warehouse - %s" % abbr

            suppliers = frappe.get_all(
                "Supplier", filters={"disabled": 0}, pluck="name"
            )
            items = frappe.get_all(
                "Item",
                filters={"is_stock_item": 1, "disabled": 0},
                fields=["name", "item_name", "stock_uom", "item_group"],
                limit_page_length=0,
            )

            self._ensure_item_procurement_flags(
                [r["name"] for r in items]
            )

            if not suppliers or not items:
                print(
                    "  ⚠️  No suppliers or items found. Skipping purchase generation."
                )
                return

            item_prices = {}
            for ip in frappe.get_all(
                "Item Price",
                filters={"price_list": "Standard Buying"},
                fields=["item_code", "price_list_rate"],
                limit_page_length=0,
            ):
                item_prices[ip.item_code] = float(ip.price_list_rate)

            num_pi_total = random.randint(
                *self.config["num_purchase_invoices"]
            )
            pct_po = float(
                self.config.get(
                    "pct_purchase_invoices_from_po", 0.52
                )
            )
            n_from_po = min(
                num_pi_total,
                max(0, int(round(num_pi_total * pct_po))),
            )
            n_orphan = num_pi_total - n_from_po

            print(
                "  📊 Purchases: %s invoices (%s from PO, %s standalone)"
                % (num_pi_total, n_from_po, n_orphan)
            )

            total_days = max(1, (end_date - start_date).days)

            for i in range(n_orphan):
                posting_date = add_days(
                    start_date, random.randint(0, total_days)
                )
                if getdate(posting_date) > getdate(nowdate()):
                    posting_date = nowdate()

                supplier = random.choice(suppliers)
                num_pick = random.randint(1, 10)
                selected = random.sample(
                    items, min(num_pick, len(items))
                )

                self._create_standalone_pi(
                    company=company,
                    supplier=supplier,
                    items=selected,
                    item_prices=item_prices,
                    posting_date=posting_date,
                    warehouse=warehouse,
                )

                if i % 50 == 0:
                    frappe.db.commit()
                    print(
                        "    ... %s/%s standalone PIs"
                        % (i + 1, n_orphan)
                    )

                if self.debug_single_doc:
                    frappe.db.commit()
                    return

            for j in range(n_from_po):
                posting_date = add_days(
                    start_date, random.randint(0, total_days)
                )
                if getdate(posting_date) > getdate(nowdate()):
                    posting_date = nowdate()

                supplier = random.choice(suppliers)
                num_pick = random.randint(2, 8)
                selected = random.sample(
                    items, min(num_pick, len(items))
                )

                self._create_pi_from_po(
                    company=company,
                    supplier=supplier,
                    items=selected,
                    item_prices=item_prices,
                    posting_date=posting_date,
                    warehouse=warehouse,
                    partial_invoice=random.random() < 0.38,
                )

                if j % 50 == 0:
                    frappe.db.commit()
                    print(
                        "    ... %s/%s PO-linked PIs"
                        % (j + 1, n_from_po)
                    )

                if self.debug_single_doc:
                    frappe.db.commit()
                    return

            frappe.db.commit()
            print(
                "  ✅ Created %s purchase records"
                % len(self.created_records)
            )
            for err in self.errors[:5]:
                print("  ⚠️  %s" % err)
        finally:
            self._restore_notifications()

    def _create_standalone_pi(
        self, company, supplier, items, item_prices,
        posting_date, warehouse,
    ):
        pi = frappe.new_doc("Purchase Invoice")
        pi.company = company
        pi.supplier = supplier
        pi.posting_date = posting_date
        pi.due_date = posting_date
        pi.currency = self.config["currency"]
        pi.buying_price_list = "Standard Buying"
        pi.update_stock = 0
        pi.set_warehouse = warehouse
        pi.bill_date = posting_date

        for item in items:
            rate = item_prices.get(
                item["name"], random.uniform(50, 3000)
            )
            rate = rate * random.uniform(0.92, 1.08)
            qty = random.randint(5, 100)

            pi.append("items", {
                "item_code": item["name"],
                "item_name": item.get("item_name", item["name"]),
                "qty": qty,
                "rate": round(rate, 2),
                "uom": item.get("stock_uom", "Nos"),
                "stock_uom": item.get("stock_uom", "Nos"),
                "conversion_factor": 1,
                "warehouse": warehouse,
            })

        try:
            pi.insert(ignore_permissions=True)
            pi.submit()
            self.created_records.append(("Purchase Invoice", pi.name))
        except Exception as e:
            if len(self.errors) < 12:
                print(
                    "  ⚠️  PI failed for %s: %s" % (supplier, str(e))
                )
            self.errors.append("Purchase Invoice: %s" % str(e))

    def _create_pi_from_po(
        self,
        company,
        supplier,
        items,
        item_prices,
        posting_date,
        warehouse,
        partial_invoice,
    ):
        """Submit a PO then invoice it (full or partial qty)."""
        tr = add_days(posting_date, -random.randint(1, 21))
        if getdate(tr) > getdate(posting_date):
            tr = posting_date
        sch = add_days(tr, random.randint(5, 28))

        po = frappe.new_doc("Purchase Order")
        po.company = company
        po.supplier = supplier
        po.transaction_date = tr
        po.schedule_date = sch
        po.currency = self.config["currency"]
        po.buying_price_list = "Standard Buying"
        po.set_warehouse = warehouse

        for item in items:
            base = item_prices.get(
                item["name"], random.uniform(50, 3000)
            )
            rate = base * random.uniform(0.93, 1.07)
            qty = random.randint(20, 220)
            po.append(
                "items",
                {
                    "item_code": item["name"],
                    "item_name": item.get("item_name", item["name"]),
                    "qty": qty,
                    "rate": round(rate, 2),
                    "uom": item.get("stock_uom", "Nos"),
                    "stock_uom": item.get("stock_uom", "Nos"),
                    "conversion_factor": 1,
                    "warehouse": warehouse,
                    "schedule_date": sch,
                },
            )

        try:
            po.insert(ignore_permissions=True)
            po.submit()
            self.created_records.append(("Purchase Order", po.name))
        except Exception as e:
            self.errors.append("PO seed: %s" % str(e))
            return

        pi = frappe.new_doc("Purchase Invoice")
        pi.company = company
        pi.supplier = supplier
        pi.posting_date = posting_date
        pi.due_date = add_days(posting_date, random.randint(7, 45))
        pi.currency = self.config["currency"]
        pi.buying_price_list = "Standard Buying"
        pi.update_stock = 0
        pi.set_warehouse = warehouse
        po_key = po.name.replace("/", "-").replace(" ", "")[-12:]
        pi.bill_no = "BILL-%s-%04d" % (po_key, random.randint(100, 9999))
        pi.bill_date = posting_date

        for po_row in po.items:
            po_qty = flt(po_row.qty)
            if partial_invoice and po_qty > 4:
                bill_qty = random.randint(
                    max(1, int(po_qty * 0.35)),
                    max(1, int(po_qty * 0.78)),
                )
                bill_qty = min(bill_qty, int(po_qty))
            else:
                bill_qty = int(po_qty)

            pi.append(
                "items",
                {
                    "item_code": po_row.item_code,
                    "item_name": po_row.item_name or po_row.item_code,
                    "qty": bill_qty,
                    "rate": flt(po_row.rate),
                    "uom": po_row.uom or po_row.stock_uom,
                    "stock_uom": po_row.stock_uom or po_row.uom,
                    "conversion_factor": (
                        flt(po_row.conversion_factor) or 1
                    ),
                    "warehouse": po_row.warehouse or warehouse,
                    "purchase_order": po.name,
                    "po_detail": po_row.name,
                },
            )

        try:
            pi.insert(ignore_permissions=True)
            pi.submit()
            self.created_records.append(
                ("Purchase Invoice (from PO)", pi.name)
            )
        except Exception as e:
            self.errors.append("PI-from-PO %s: %s" % (po.name, str(e)))

    def _ensure_item_procurement_flags(self, item_codes):
        if not item_codes:
            return

        for item_code in item_codes:
            frappe.db.set_value(
                "Item",
                item_code,
                {
                    "is_purchase_item": 1,
                    "is_sales_item": 1,
                },
                update_modified=False,
            )
        frappe.db.commit()

    def validate(self):
        count = frappe.db.count(
            "Purchase Invoice", filters={"docstatus": 1}
        )
        lo = self.config["num_purchase_invoices"][0] // 2
        assert count >= lo, "Too few purchase invoices"

        linked = frappe.db.sql(
            """
            SELECT COUNT(DISTINCT pi.name)
            FROM `tabPurchase Invoice` pi
            INNER JOIN `tabPurchase Invoice Item` pii ON pii.parent = pi.name
            WHERE pi.company = %s AND pi.docstatus = 1
                  AND IFNULL(pii.purchase_order, '') != ''
            """,
            (self.config["company_name"],),
        )[0][0]

        pct_po = float(
            self.config.get("pct_purchase_invoices_from_po", 0)
        )
        if pct_po > 1e-6:
            assert int(linked or 0) >= 3, "Too few PO-linked PIs"
        return True

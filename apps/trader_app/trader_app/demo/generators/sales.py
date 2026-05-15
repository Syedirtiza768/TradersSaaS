# -*- coding: utf-8 -*-
"""Generator — Sales Orders + Invoices.

Creates:
- Mixed **direct** Sales Invoices (no SO) — common trading shortcut
- **Submitted Sales Orders** linked to **Sales Invoice** lines (`sales_order` / `so_detail`)
- Optional **Quotation → SO → SI** chain for a subset (uses pending submitted quotations)

Outstanding / credit logic matches the previous direct-invoice path.
"""

from __future__ import unicode_literals

import random

import frappe
from frappe.utils import add_days, flt, getdate, nowdate

from trader_app.demo.seed_engine.base import BaseGenerator


class SalesGenerator(BaseGenerator):
    name = "Sales"
    depends_on = ["Company", "Customers", "Items", "Inventory", "Quotations"]
    debug_single_doc = False

    def generate(self):
        self._suppress_notifications()
        try:
            company = self.config["company_name"]
            abbr = self.config["company_abbr"]
            self._last_invoice_total = 0.0
            start_date = getdate(self.config["demo_start_date"])
            end_date = getdate(self.config["demo_end_date"])
            warehouse = "Main Warehouse - %s" % abbr
            total_days = max(1, (end_date - start_date).days)

            customers = frappe.get_all(
                "Customer", filters={"disabled": 0}, pluck="name"
            )
            items = frappe.get_all(
                "Item",
                filters={"is_stock_item": 1, "disabled": 0},
                fields=["name", "item_name", "stock_uom", "item_group"],
                limit_page_length=0,
            )
            self._ensure_item_sales_flags([r["name"] for r in items])

            customer_credit_limits = self._get_customer_credit_limits(company)
            customer_outstanding = self._get_customer_outstanding(company)

            if not customers or not items:
                print(
                    "  ⚠️  No customers or items found. Skipping sales generation."
                )
                return

            item_prices = {}
            for ip in frappe.get_all(
                "Item Price",
                filters={"price_list": "Standard Selling"},
                fields=["item_code", "price_list_rate"],
                limit_page_length=0,
            ):
                item_prices[ip.item_code] = float(ip.price_list_rate)

            num_si_total = random.randint(*self.config["num_sales_invoices"])
            pct_so = float(
                self.config.get("pct_sales_invoices_via_sales_order", 0.34)
            )
            pct_from_q = float(
                self.config.get("pct_so_linked_from_quotation", 0.36)
            )

            n_via_chain = min(
                num_si_total, max(0, int(round(num_si_total * pct_so)))
            )
            n_direct = num_si_total - n_via_chain

            print(
                "  📊 Sales: %s invoices planned (%s direct, %s via SO→SI)"
                % (num_si_total, n_direct, n_via_chain)
            )

            for i in range(n_direct):
                posting_date = self._random_posting_date(
                    start_date, end_date, total_days
                )
                eligible_cust = [
                    c
                    for c in customers
                    if self._get_available_credit(
                        c, customer_credit_limits, customer_outstanding
                    )
                    > 5000
                ]
                customer = random.choice(eligible_cust or customers)
                num_pick = random.randint(1, 8)
                sel = random.sample(
                    items, min(num_pick, len(items))
                )
                month = getdate(posting_date).month
                seasonal = self._seasonal_factor(month)

                self._create_direct_sales_invoice(
                    company=company,
                    customer=customer,
                    items=sel,
                    item_prices=item_prices,
                    customer_credit_limit=customer_credit_limits.get(
                        customer, 0
                    ),
                    customer_outstanding=customer_outstanding.get(
                        customer, 0
                    ),
                    posting_date=posting_date,
                    warehouse=warehouse,
                    seasonal_factor=seasonal,
                )
                if self._last_invoice_total > 0:
                    customer_outstanding[customer] = (
                        customer_outstanding.get(customer, 0)
                        + self._last_invoice_total
                    )

                if i % 50 == 0:
                    frappe.db.commit()

                if self.debug_single_doc:
                    frappe.db.commit()
                    return

            pending_quotations = self._eligible_pending_quotations(company)
            random.shuffle(pending_quotations)
            q_ptr = 0

            for i in range(n_via_chain):
                posting_date = self._random_posting_date(
                    start_date, end_date, total_days
                )
                eligible_cust = [
                    c
                    for c in customers
                    if self._get_available_credit(
                        c, customer_credit_limits, customer_outstanding
                    )
                    > 5000
                ]
                customer = random.choice(eligible_cust or customers)
                month = getdate(posting_date).month
                seasonal = self._seasonal_factor(month)

                use_qtn = (
                    q_ptr < len(pending_quotations)
                    and random.random() < pct_from_q
                )
                if use_qtn:
                    qname = pending_quotations[q_ptr]
                    q_ptr += 1
                    self._chain_quotation_so_invoice(
                        company=company,
                        warehouse=warehouse,
                        quotation_name=qname,
                        item_prices=item_prices,
                        customer_credit_limits=customer_credit_limits,
                        customer_outstanding=customer_outstanding,
                        posting_date=posting_date,
                        seasonal_factor=seasonal,
                    )
                else:
                    num_pick = random.randint(1, 7)
                    sel = random.sample(
                        items, min(num_pick, len(items))
                    )
                    self._chain_standalone_so_invoice(
                        company=company,
                        customer=customer,
                        warehouse=warehouse,
                        items=sel,
                        item_prices=item_prices,
                        customer_credit_limits=customer_credit_limits,
                        customer_outstanding=customer_outstanding,
                        posting_date=posting_date,
                        seasonal_factor=seasonal,
                    )

                if self._last_invoice_total > 0:
                    # customer was set inside chain methods on last invoice row
                    cust_key = getattr(self, "_last_si_customer", customer)
                    customer_outstanding[cust_key] = (
                        customer_outstanding.get(cust_key, 0)
                        + self._last_invoice_total
                    )

                if i % 50 == 0:
                    frappe.db.commit()

                if self.debug_single_doc:
                    frappe.db.commit()
                    return

            frappe.db.commit()
            print("  ✅ Created %s sales records" % len(self.created_records))
            for err in self.errors[:5]:
                print("  ⚠️  %s" % err)
        finally:
            self._restore_notifications()

    def _random_posting_date(self, start_date, end_date, total_days):
        posting_date = add_days(
            start_date, random.randint(0, total_days)
        )
        if getdate(posting_date) > getdate(nowdate()):
            posting_date = nowdate()
        return posting_date

    # ─────────────────────────────────────────────────────────────
    # Quotation → Sales Order → Sales Invoice
    # ─────────────────────────────────────────────────────────────
    def _eligible_pending_quotations(self, company):
        return frappe.db.sql(
            """
            SELECT q.name
            FROM `tabQuotation` q
            WHERE q.company = %(c)s
                  AND q.docstatus = 1
                  AND NOT EXISTS (
                      SELECT 1 FROM `tabSales Order Item` soi
                      INNER JOIN `tabSales Order` so
                          ON so.name = soi.parent AND so.company = %(c)s
                      WHERE IFNULL(soi.prevdoc_docname, '') = q.name
                        AND so.docstatus < 2
                  )
            ORDER BY q.modified DESC
            LIMIT 260
            """,
            {"c": company},
            pluck="name",
        )

    def _chain_quotation_so_invoice(
        self,
        company,
        warehouse,
        quotation_name,
        item_prices,
        customer_credit_limits,
        customer_outstanding,
        posting_date,
        seasonal_factor,
    ):
        self._last_invoice_total = 0.0
        try:
            q = frappe.get_doc("Quotation", quotation_name)
        except Exception as e:
            self.errors.append(
                "QT load %s: %s" % (quotation_name, str(e))
            )
            return

        if q.docstatus != 1 or not q.items:
            return

        customer = q.party_name
        avail = self._get_available_credit(
            customer, customer_credit_limits, customer_outstanding
        )
        if avail <= 2500:
            return

        so = frappe.new_doc("Sales Order")
        so.company = company
        so.customer = customer
        so.transaction_date = posting_date
        so.delivery_date = add_days(posting_date, random.randint(3, 18))
        so.currency = self.config["currency"]
        so.selling_price_list = getattr(
            q, "selling_price_list", None
        ) or "Standard Selling"
        if getattr(q, "price_list_currency", None):
            so.price_list_currency = q.price_list_currency
            so.plc_conversion_rate = flt(
                getattr(q, "plc_conversion_rate", None) or 1
            )
        remaining = avail * 0.55

        for qi in q.items:
            rate_src = (
                qi.rate
                if flt(qi.rate) > 0
                else item_prices.get(qi.item_code, random.uniform(100, 5000))
            )
            rate = flt(rate_src) * seasonal_factor * random.uniform(
                0.95, 1.05
            )
            qty = max(1, int(flt(qi.qty)))
            line = rate * qty
            if line > remaining:
                continue
            remaining -= line
            row = {
                "item_code": qi.item_code,
                "item_name": qi.item_name or qi.item_code,
                "qty": qty,
                "rate": round(rate, 2),
                "warehouse": qi.warehouse or warehouse,
                "uom": qi.uom or qi.stock_uom or "Nos",
                "stock_uom": qi.stock_uom or qi.uom or "Nos",
                "conversion_factor": flt(qi.conversion_factor) or 1,
                "prevdoc_docname": q.name,
            }
            if frappe.get_meta("Sales Order Item").has_field(
                "quotation_item"
            ):
                row["quotation_item"] = qi.name
            so.append("items", row)
            if remaining < 1000:
                break

        if not so.items:
            return
        try:
            so.insert(ignore_permissions=True)
            so.submit()
            self.created_records.append(("Sales Order", so.name))
        except Exception as e:
            self.errors.append("SO-from-QT %s: %s" % (quotation_name, str(e)))
            return

        self._submit_linked_sales_invoice_from_so(
            company=company,
            customer=customer,
            so_name=so.name,
            posting_date=posting_date,
            warehouse_override=warehouse,
        )

    def _chain_standalone_so_invoice(
        self,
        company,
        customer,
        warehouse,
        items,
        item_prices,
        customer_credit_limits,
        customer_outstanding,
        posting_date,
        seasonal_factor,
    ):
        self._last_invoice_total = 0.0
        if not customer or not items:
            return

        avail = self._get_available_credit(
            customer, customer_credit_limits, customer_outstanding
        )
        if avail <= 2500:
            return

        so = frappe.new_doc("Sales Order")
        so.company = company
        so.customer = customer
        so.transaction_date = posting_date
        so.delivery_date = add_days(posting_date, random.randint(3, 20))
        so.currency = self.config["currency"]
        so.selling_price_list = "Standard Selling"
        remaining = avail * 0.58

        for item in items:
            rate = item_prices.get(
                item["name"], random.uniform(100, 5000)
            )
            rate = rate * seasonal_factor * random.uniform(0.96, 1.05)
            max_qty = max(1, int(remaining / max(rate, 1)))
            qty = random.randint(1, min(max_qty, 5))
            discount = random.choice([0, 0, 0, 3, 5, 10]) if random.random() < 0.25 else 0
            line = flt(rate) * qty * (1 - (discount / 100.0))
            if line > remaining:
                continue
            remaining -= line
            so.append(
                "items",
                {
                    "item_code": item["name"],
                    "item_name": item.get("item_name", item["name"]),
                    "qty": qty,
                    "rate": round(rate, 2),
                    "warehouse": warehouse,
                    "uom": item.get("stock_uom", "Nos"),
                    "stock_uom": item.get("stock_uom", "Nos"),
                    "conversion_factor": 1,
                    "discount_percentage": discount,
                },
            )
            if remaining < 900:
                break

        if not so.items:
            return
        try:
            so.insert(ignore_permissions=True)
            so.submit()
            self.created_records.append(("Sales Order", so.name))
        except Exception as e:
            self.errors.append("SO standalone %s: %s" % (customer, str(e)))
            return

        self._submit_linked_sales_invoice_from_so(
            company=company,
            customer=customer,
            so_name=so.name,
            posting_date=posting_date,
            warehouse_override=warehouse,
        )

    def _submit_linked_sales_invoice_from_so(
        self, company, customer, so_name, posting_date, warehouse_override
    ):
        self._last_invoice_total = 0.0
        so = frappe.get_doc("Sales Order", so_name)
        if so.docstatus != 1:
            return

        si = frappe.new_doc("Sales Invoice")
        si.company = company
        si.customer = customer or so.customer
        si.posting_date = posting_date
        si.due_date = posting_date
        si.currency = self.config["currency"]
        si.selling_price_list = getattr(
            so, "selling_price_list", None
        ) or "Standard Selling"
        si.conversion_rate = flt(so.conversion_rate) or 1
        if getattr(so, "price_list_currency", None):
            si.price_list_currency = so.price_list_currency
            si.plc_conversion_rate = flt(so.plc_conversion_rate or 1)
        si.update_stock = 0

        for so_row in so.items:
            qty = flt(so_row.qty)
            if qty <= 0:
                continue
            wh = warehouse_override or so_row.warehouse
            si.append(
                "items",
                {
                    "item_code": so_row.item_code,
                    "item_name": getattr(
                        so_row, "item_name", None
                    )
                    or so_row.item_code,
                    "qty": qty,
                    "rate": flt(so_row.rate),
                    "uom": so_row.uom or so_row.stock_uom,
                    "stock_uom": so_row.stock_uom or so_row.uom,
                    "conversion_factor": (
                        flt(so_row.conversion_factor) or 1
                    ),
                    "warehouse": wh,
                    "discount_percentage": flt(
                        getattr(so_row, "discount_percentage", 0)
                    ),
                    "sales_order": so.name,
                    "so_detail": so_row.name,
                },
            )

        if not si.items:
            return
        try:
            si.insert(ignore_permissions=True)
            si.submit()
            self._last_invoice_total = flt(si.grand_total)
            self._last_si_customer = si.customer
            self.created_records.append(("Sales Invoice", si.name))
        except Exception as e:
            self._last_invoice_total = 0.0
            if len(self.errors) < 14:
                self.errors.append(
                    "SI-from-SO %s: %s" % (so_name, str(e))
                )

    # ─────────────────────────────────────────────────────────────
    # Direct invoices (legacy path)
    # ─────────────────────────────────────────────────────────────
    def _create_direct_sales_invoice(
        self,
        company,
        customer,
        items,
        item_prices,
        customer_credit_limit,
        customer_outstanding,
        posting_date,
        warehouse,
        seasonal_factor,
    ):
        self._last_invoice_total = 0.0
        si = frappe.get_doc({
            "doctype": "Sales Invoice",
            "company": company,
            "customer": customer,
            "posting_date": posting_date,
            "due_date": posting_date,
            "currency": self.config["currency"],
            "selling_price_list": "Standard Selling",
            "update_stock": 0,
            "set_warehouse": warehouse,
        })

        available_credit = self._get_available_credit(
            customer,
            {customer: customer_credit_limit},
            {customer: customer_outstanding},
        )
        if available_credit <= 2500:
            return

        remaining_credit = available_credit * 0.6

        for item in items:
            rate = item_prices.get(
                item["name"], random.uniform(100, 5000)
            )
            rate = rate * seasonal_factor * random.uniform(0.95, 1.05)
            max_qty = max(
                1, int(remaining_credit // max(rate, 1))
            )
            qty = random.randint(1, min(max_qty, 5))

            discount = 0
            if random.random() < 0.3:
                discount = random.choice([2, 5, 7, 10, 15])
            line_total = (
                flt(rate) * qty * (1 - (discount / 100.0))
            )

            if line_total > remaining_credit:
                continue

            remaining_credit -= line_total

            si.append("items", {
                "item_code": item["name"],
                "item_name": item.get("item_name", item["name"]),
                "qty": qty,
                "rate": round(rate, 2),
                "uom": item.get("stock_uom", "Nos"),
                "stock_uom": item.get("stock_uom", "Nos"),
                "conversion_factor": 1,
                "warehouse": warehouse,
                "discount_percentage": discount,
            })

            if remaining_credit <= 0:
                break

        if not si.items:
            return

        try:
            si.insert(ignore_permissions=True)
            si.submit()
            self._last_invoice_total = flt(si.grand_total)
            self._last_si_customer = si.customer
            self.created_records.append(("Sales Invoice", si.name))
        except Exception as e:
            self._last_invoice_total = 0.0
            if len(self.errors) < 10:
                print(
                    "  ⚠️  Sales Invoice failed for %s: %s"
                    % (customer, str(e))
                )
            self.errors.append("Sales Invoice: %s" % str(e))

    def _get_customer_credit_limits(self, company):
        limits = {}
        for row in frappe.get_all(
            "Customer Credit Limit",
            filters={"company": company},
            fields=["parent", "credit_limit"],
            limit_page_length=0,
        ):
            limits[row.parent] = float(row.credit_limit or 0)
        return limits

    def _get_customer_outstanding(self, company):
        outstanding = {}
        for row in frappe.get_all(
            "Sales Invoice",
            filters={
                "company": company,
                "docstatus": 1,
                "outstanding_amount": [">", 0],
            },
            fields=["customer", "outstanding_amount"],
            limit_page_length=0,
        ):
            outstanding[row.customer] = outstanding.get(
                row.customer, 0.0
            ) + flt(row.outstanding_amount)
        return outstanding

    @staticmethod
    def _get_available_credit(
        customer, customer_credit_limits, customer_outstanding
    ):
        credit_limit = flt(customer_credit_limits.get(customer, 0))
        currently_outstanding = flt(
            customer_outstanding.get(customer, 0)
        )
        return max(credit_limit - currently_outstanding, 0.0)

    def _ensure_item_sales_flags(self, item_codes):
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

    @staticmethod
    def _seasonal_factor(month):
        factors = {
            1: 1.15,
            2: 1.05,
            3: 1.10,
            4: 0.90,
            5: 1.05,
            6: 0.95,
            7: 0.85,
            8: 0.90,
            9: 1.00,
            10: 1.05,
            11: 1.15,
            12: 1.20,
        }
        return factors.get(month, 1.0)

    def validate(self):
        count = frappe.db.count(
            "Sales Invoice", filters={"docstatus": 1}
        )
        min_si = self.config["num_sales_invoices"][0] // 2
        assert count >= min_si, "Too few Sales Invoices seeded"

        n_so = frappe.db.count(
            "Sales Order", filters={"docstatus": 1}
        )
        pct_so = float(
            self.config.get("pct_sales_invoices_via_sales_order", 0)
        )
        if pct_so > 1e-6:
            assert n_so >= 3, "Too few Sales Orders for SO mix configuration"
        return True

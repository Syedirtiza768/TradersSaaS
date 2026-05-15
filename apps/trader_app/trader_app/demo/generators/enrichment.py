# -*- coding: utf-8 -*-
"""Generator — Data Enrichment.

Patches gaps that make reports show incomplete / inconsistent data:

1. Sales Team entries on Sales Invoices        → salesperson-performance report
2. Tax entries on Sales & Purchase Invoices     → tax-summary report
3. incoming_rate back-fill on SI Items          → sales-performance, customer-profitability GP
4. Purchase Orders (some open, some received)   → open-purchase-orders report
5. Sales Returns (credit notes)                 → sales-return report
6. Purchase Returns (debit notes)               → purchase-return report
7. Item Reorder + Item Default + lead_time_days → reorder report full columns
8. Stock Ledger Entries via stock deductions     → stock-aging, inventory-movement freshness

Run AFTER all other generators via:
    bench --site <site> execute trader_app.demo.enrich_reports
"""

from __future__ import unicode_literals

import random
import frappe
from frappe.utils import flt, cint, getdate, add_days, nowdate, add_months
from trader_app.demo.seed_engine.base import BaseGenerator


# ── Sales-person names ──────────────────────────────────────────
SALES_PERSONS = [
    "Ali Raza", "Hassan Malik", "Usman Tariq", "Bilal Ahmed",
    "Kamran Shah", "Faisal Mehmood", "Zain Abbas", "Omar Farooq",
]

# ── Expense categories reused for tax description ───────────────
TAX_RATES = [17.0, 5.0]


class EnrichmentGenerator(BaseGenerator):
    """Post-seed enrichment to make every report produce complete data."""

    name = "Enrichment"
    depends_on = ["Sales", "Purchases", "Payments", "Financial"]

    def generate(self):
        self._suppress_notifications()
        try:
            self.company = self.config["company_name"]
            self.abbr = self.config["company_abbr"]
            self.currency = self.config["currency"]
            self.start_date = getdate(self.config["demo_start_date"])
            self.end_date = getdate(self.config["demo_end_date"])
            self.warehouse = f"Main Warehouse - {self.abbr}"

            self._enrich_sales_persons()
            self._enrich_sales_teams()
            self._enrich_tax_entries()
            self._backfill_incoming_rate()
            self._create_purchase_orders()
            self._create_sales_returns()
            self._create_purchase_returns()
            self._enrich_item_reorder()
            self._create_stock_deductions()

            frappe.db.commit()
        finally:
            self._restore_notifications()

    def validate(self):
        # Sales Team exists
        st_count = frappe.db.count("Sales Team")
        assert st_count > 0, "No Sales Team entries"

        # Tax entries exist
        stc = cint(frappe.db.sql(
            "SELECT COUNT(*) FROM `tabSales Taxes and Charges`")[0][0])
        assert stc > 0, "No Sales Tax entries"

        # incoming_rate populated
        ir = frappe.db.sql("""
            SELECT COUNT(*) FROM `tabSales Invoice Item`
            WHERE incoming_rate > 0
        """)[0][0]
        assert cint(ir) > 0, "No incoming_rate values"

        # Purchase Orders exist
        po = frappe.db.count("Purchase Order", filters={"docstatus": 1})
        assert po > 0, "No Purchase Orders"

        # Returns exist
        sr = frappe.db.count("Sales Invoice",
                             filters={"docstatus": 1, "is_return": 1})
        assert sr > 0, "No Sales Returns"

        # Item Reorder exists
        ird = frappe.db.count("Item Reorder")
        assert ird > 0, "No Item Reorder records"

        return True

    # ────────────────────────────────────────────────────────────
    # 1.  SALES PERSONS (master records)
    # ────────────────────────────────────────────────────────────
    def _enrich_sales_persons(self):
        """Create Sales Person master records if absent."""
        # ERPNext keeps Sales Person as a tree — need a root
        if not frappe.db.exists("Sales Person", {"is_group": 1}):
            root_name = "All Sales Persons"
            if not frappe.db.exists("Sales Person", root_name):
                doc = frappe.get_doc({
                    "doctype": "Sales Person",
                    "sales_person_name": root_name,
                    "is_group": 1,
                    "enabled": 1,
                })
                doc.insert(ignore_permissions=True)

        root = frappe.db.get_value("Sales Person",
                                   {"is_group": 1}, "name") or "All Sales Persons"

        created = 0
        for sp_name in SALES_PERSONS:
            if not frappe.db.exists("Sales Person", sp_name):
                doc = frappe.get_doc({
                    "doctype": "Sales Person",
                    "sales_person_name": sp_name,
                    "parent_sales_person": root,
                    "is_group": 0,
                    "enabled": 1,
                })
                doc.insert(ignore_permissions=True)
                created += 1
        frappe.db.commit()
        print(f"  ✅ Sales Persons: {created} created")

    # ────────────────────────────────────────────────────────────
    # 2.  SALES TEAM on submitted Sales Invoices
    # ────────────────────────────────────────────────────────────
    def _enrich_sales_teams(self):
        """Add Sales Team child rows to existing submitted Sales Invoices."""
        invoices = frappe.db.sql("""
            SELECT si.name
            FROM `tabSales Invoice` si
            WHERE si.company = %s AND si.docstatus = 1
                  AND NOT EXISTS (
                      SELECT 1 FROM `tabSales Team` st
                      WHERE st.parent = si.name AND st.parenttype = 'Sales Invoice'
                  )
        """, (self.company,), as_dict=True)

        persons = frappe.get_all("Sales Person",
                                 filters={"is_group": 0, "enabled": 1},
                                 pluck="name")
        if not persons:
            print("  ⚠️  No sales persons found, skipping sales teams")
            return

        count = 0
        for inv in invoices:
            # 1 or 2 persons per invoice
            num = random.choice([1, 1, 1, 2])
            chosen = random.sample(persons, min(num, len(persons)))
            pct = 100.0 / num

            for sp in chosen:
                frappe.get_doc({
                    "doctype": "Sales Team",
                    "parent": inv["name"],
                    "parenttype": "Sales Invoice",
                    "parentfield": "sales_team",
                    "sales_person": sp,
                    "allocated_percentage": pct,
                    "allocated_amount": 0,  # will be recalced
                }).db_insert()
                count += 1

            if count % 200 == 0:
                frappe.db.commit()

        frappe.db.commit()
        print(f"  ✅ Sales Team rows: {count} added to {len(invoices)} invoices")

    # ────────────────────────────────────────────────────────────
    # 3.  TAX ENTRIES on invoices
    # ────────────────────────────────────────────────────────────
    def _enrich_tax_entries(self):
        """Add Sales Taxes and Charges (and Purchase Taxes) to a subset of invoices."""
        tax_account = self._get_or_create_tax_account()
        if not tax_account:
            print("  ⚠️  Could not find/create tax account, skipping tax enrichment")
            return

        s_count = self._add_tax_rows("Sales Invoice", "Sales Taxes and Charges",
                                     "taxes", tax_account, rate=17.0, fraction=0.6)
        p_count = self._add_tax_rows("Purchase Invoice", "Purchase Taxes and Charges",
                                     "taxes", tax_account, rate=17.0, fraction=0.5)

        frappe.db.commit()
        print(f"  ✅ Tax entries: {s_count} sales + {p_count} purchase")

    def _get_or_create_tax_account(self):
        """Find or create a tax liability account."""
        acct = frappe.db.get_value(
            "Account",
            filters={
                "company": self.company,
                "account_type": "Tax",
                "is_group": 0,
            },
            fieldname="name",
        )
        if acct:
            return acct

        # Try to find any account containing 'tax' or 'output'
        acct = frappe.db.sql("""
            SELECT name FROM `tabAccount`
            WHERE company = %s AND is_group = 0
                  AND (name LIKE '%%Tax%%' OR name LIKE '%%Output%%' OR name LIKE '%%GST%%')
            ORDER BY name LIMIT 1
        """, (self.company,))
        if acct:
            return acct[0][0]

        # Create one under Duties and Taxes
        parent = frappe.db.get_value(
            "Account",
            filters={"company": self.company, "is_group": 1,
                      "root_type": "Liability",
                      "name": ("like", "%Duties and Taxes%")},
            fieldname="name",
        )
        if not parent:
            parent = frappe.db.get_value(
                "Account",
                filters={"company": self.company, "is_group": 1,
                          "root_type": "Liability"},
                fieldname="name",
            )
        if not parent:
            return None

        new_acct = frappe.get_doc({
            "doctype": "Account",
            "account_name": "Output Tax",
            "parent_account": parent,
            "company": self.company,
            "account_type": "Tax",
            "root_type": "Liability",
        })
        new_acct.insert(ignore_permissions=True)
        return new_acct.name

    def _add_tax_rows(self, invoice_dt, tax_dt, parentfield, tax_account,
                      rate, fraction):
        """Insert tax child-table rows for a fraction of invoices."""
        invoices = frappe.db.sql(f"""
            SELECT inv.name, inv.net_total
            FROM `tab{invoice_dt}` inv
            WHERE inv.company = %s AND inv.docstatus = 1
                  AND NOT EXISTS (
                      SELECT 1 FROM `tab{tax_dt}` t
                      WHERE t.parent = inv.name AND t.parenttype = %s
                  )
        """, (self.company, invoice_dt), as_dict=True)

        # Only enrich a fraction of invoices
        sample_size = max(1, int(len(invoices) * fraction))
        chosen = random.sample(invoices, min(sample_size, len(invoices)))

        count = 0
        for inv in chosen:
            net = flt(inv["net_total"])
            tax_amount = round(net * rate / 100, 2)
            frappe.get_doc({
                "doctype": tax_dt,
                "parent": inv["name"],
                "parenttype": invoice_dt,
                "parentfield": parentfield,
                "charge_type": "On Net Total",
                "account_head": tax_account,
                "description": f"Sales Tax {rate}%",
                "rate": rate,
                "tax_amount": tax_amount,
                "total": net + tax_amount,
                "base_tax_amount": tax_amount,
                "base_total": net + tax_amount,
            }).db_insert()
            count += 1

            if count % 200 == 0:
                frappe.db.commit()

        return count

    # ────────────────────────────────────────────────────────────
    # 4.  BACK-FILL incoming_rate on Sales Invoice Items
    # ────────────────────────────────────────────────────────────
    def _backfill_incoming_rate(self):
        """Set incoming_rate on Sales Invoice Items from buying price list or estimated cost."""
        # Build cost map: item_code → buying rate
        cost_map = {}
        for ip in frappe.get_all("Item Price",
                                 filters={"price_list": "Standard Buying"},
                                 fields=["item_code", "price_list_rate"],
                                 limit_page_length=0):
            cost_map[ip.item_code] = flt(ip.price_list_rate)

        # Update all SI Items where incoming_rate is 0 or NULL
        items = frappe.db.sql("""
            SELECT sii.name, sii.item_code, sii.rate
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE si.company = %s AND si.docstatus = 1
                  AND COALESCE(sii.incoming_rate, 0) = 0
        """, (self.company,), as_dict=True)

        count = 0
        for row in items:
            cost = cost_map.get(row["item_code"])
            if not cost:
                # Estimate cost as 60-80% of selling rate
                cost = flt(row["rate"]) * random.uniform(0.60, 0.80)
            cost = round(cost, 2)
            frappe.db.set_value("Sales Invoice Item", row["name"],
                                "incoming_rate", cost, update_modified=False)
            count += 1
            if count % 500 == 0:
                frappe.db.commit()

        frappe.db.commit()
        print(f"  ✅ incoming_rate back-filled on {count} SI Items")

    # ────────────────────────────────────────────────────────────
    # 5.  PURCHASE ORDERS (open + partially received)
    # ────────────────────────────────────────────────────────────
    def _create_purchase_orders(self):
        """Create Purchase Orders — some open, some partially received."""
        suppliers = frappe.get_all("Supplier", filters={"disabled": 0}, pluck="name")
        items = frappe.get_all("Item",
                               filters={"is_stock_item": 1, "disabled": 0,
                                        "is_purchase_item": 1},
                               fields=["name", "item_name", "stock_uom"],
                               limit_page_length=0)

        cost_map = {}
        for ip in frappe.get_all("Item Price",
                                 filters={"price_list": "Standard Buying"},
                                 fields=["item_code", "price_list_rate"],
                                 limit_page_length=0):
            cost_map[ip.item_code] = flt(ip.price_list_rate)

        if not suppliers or not items:
            print("  ⚠️  No suppliers/items for PO creation")
            return

        num_pos = random.randint(10, 22)
        count = 0
        for _ in range(num_pos):
            days_offset = random.randint(-60, 0)
            posting_date = add_days(nowdate(), days_offset)
            schedule_date = add_days(posting_date, random.randint(7, 30))
            supplier = random.choice(suppliers)
            selected = random.sample(items, min(random.randint(2, 6), len(items)))

            po = frappe.get_doc({
                "doctype": "Purchase Order",
                "title": supplier,
                "company": self.company,
                "supplier": supplier,
                "transaction_date": posting_date,
                "schedule_date": schedule_date,
                "currency": self.currency,
                "buying_price_list": "Standard Buying",
                "set_warehouse": self.warehouse,
                "status": "Draft",
            })

            for item in selected:
                rate = cost_map.get(item["name"], random.uniform(100, 5000))
                qty = random.randint(10, 200)
                po.append("items", {
                    "item_code": item["name"],
                    "item_name": item["item_name"],
                    "qty": qty,
                    "rate": round(rate, 2),
                    "uom": item["stock_uom"],
                    "stock_uom": item["stock_uom"],
                    "conversion_factor": 1,
                    "warehouse": self.warehouse,
                    "schedule_date": schedule_date,
                })

            try:
                po.insert(ignore_permissions=True)
                po.submit()
                self.created_records.append(("Purchase Order", po.name))

                # Mark some as partially received (30%)
                if random.random() < 0.30:
                    for item_row in po.items:
                        partial = random.randint(1, max(1, int(item_row.qty * 0.6)))
                        frappe.db.set_value("Purchase Order Item", item_row.name,
                                            "received_qty", partial,
                                            update_modified=False)
                    frappe.db.set_value("Purchase Order", po.name,
                                        "per_received", random.randint(20, 60),
                                        update_modified=False)
                count += 1
            except Exception as e:
                if len(self.errors) < 5:
                    print(f"  ⚠️  PO failed for {supplier}: {e}")
                self.errors.append(f"PO: {str(e)}")

            if count % 20 == 0:
                frappe.db.commit()

        frappe.db.commit()
        print(f"  ✅ Purchase Orders: {count} created")

    # ────────────────────────────────────────────────────────────
    # 6.  SALES RETURNS (credit notes)
    # ────────────────────────────────────────────────────────────
    def _create_sales_returns(self):
        """Create Sales Return invoices (is_return=1) for ~5% of invoices."""
        invoices = frappe.db.sql("""
            SELECT si.name, si.customer, si.posting_date
            FROM `tabSales Invoice` si
            WHERE si.company = %s AND si.docstatus = 1 AND si.is_return = 0
            ORDER BY RAND()
            LIMIT 20
        """, (self.company,), as_dict=True)

        count = 0
        for inv in invoices:
            try:
                # Load original doc to copy required account fields
                orig = frappe.get_doc("Sales Invoice", inv["name"])
                if not orig.items:
                    continue

                return_date = add_days(inv["posting_date"], random.randint(1, 14))
                if getdate(return_date) > getdate(nowdate()):
                    return_date = nowdate()

                ret = frappe.get_doc({
                    "doctype": "Sales Invoice",
                    "company": self.company,
                    "customer": orig.customer,
                    "posting_date": return_date,
                    "due_date": return_date,
                    "is_return": 1,
                    "return_against": orig.name,
                    "currency": orig.currency,
                    "debit_to": orig.debit_to,
                    "selling_price_list": orig.selling_price_list,
                    "price_list_currency": orig.price_list_currency,
                    "plc_conversion_rate": orig.plc_conversion_rate or 1,
                    "conversion_rate": orig.conversion_rate or 1,
                    "update_stock": 0,
                })

                # Return 1-2 items, partial quantity — copy all account fields from original
                return_items = random.sample(orig.items,
                                             min(random.randint(1, 2), len(orig.items)))
                for item in return_items:
                    ret_qty = max(1, random.randint(1, max(1, cint(item.qty) // 2)))
                    ret.append("items", {
                        "item_code": item.item_code,
                        "item_name": item.item_name,
                        "qty": ret_qty * -1,
                        "rate": item.rate,
                        "uom": item.uom,
                        "stock_uom": item.stock_uom,
                        "conversion_factor": item.conversion_factor or 1,
                        "warehouse": item.warehouse or self.warehouse,
                        "income_account": item.income_account,
                        "cost_center": item.cost_center,
                        "expense_account": item.expense_account,
                    })

                ret.insert(ignore_permissions=True)
                ret.submit()
                self.created_records.append(("Sales Invoice Return", ret.name))
                count += 1
            except Exception as e:
                if len(self.errors) < 5:
                    print(f"  ⚠️  Sales Return failed for {inv['name']}: {e}")
                self.errors.append(f"Sales Return: {str(e)}")

        frappe.db.commit()
        print(f"  ✅ Sales Returns: {count} created")

    # ────────────────────────────────────────────────────────────
    # 7.  PURCHASE RETURNS (debit notes)
    # ────────────────────────────────────────────────────────────
    def _create_purchase_returns(self):
        """Create Purchase Return invoices (is_return=1) for ~5% of invoices."""
        invoices = frappe.db.sql("""
            SELECT pi.name, pi.supplier, pi.posting_date
            FROM `tabPurchase Invoice` pi
            WHERE pi.company = %s AND pi.docstatus = 1
                  AND COALESCE(pi.is_return, 0) = 0
            ORDER BY RAND()
            LIMIT 15
        """, (self.company,), as_dict=True)

        count = 0
        for inv in invoices:
            items = frappe.get_all("Purchase Invoice Item",
                                   filters={"parent": inv["name"]},
                                   fields=["item_code", "item_name", "qty",
                                            "rate", "uom", "stock_uom",
                                            "warehouse"])
            if not items:
                continue

            return_date = add_days(inv["posting_date"], random.randint(1, 14))
            if getdate(return_date) > getdate(nowdate()):
                return_date = nowdate()

            ret = frappe.get_doc({
                "doctype": "Purchase Invoice",
                "company": self.company,
                "supplier": inv["supplier"],
                "posting_date": return_date,
                "due_date": return_date,
                "is_return": 1,
                "return_against": inv["name"],
                "currency": self.currency,
                "update_stock": 0,
                "bill_no": f"RET-{inv['name']}",
                "bill_date": return_date,
            })

            return_items = random.sample(items, min(random.randint(1, 2), len(items)))
            for item in return_items:
                ret_qty = max(1, random.randint(1, max(1, cint(item["qty"]) // 2)))
                ret.append("items", {
                    "item_code": item["item_code"],
                    "item_name": item["item_name"],
                    "qty": ret_qty * -1,
                    "rate": item["rate"],
                    "uom": item.get("uom", "Nos"),
                    "stock_uom": item.get("stock_uom", "Nos"),
                    "conversion_factor": 1,
                    "warehouse": item.get("warehouse", self.warehouse),
                })

            try:
                ret.insert(ignore_permissions=True)
                ret.submit()
                self.created_records.append(("Purchase Invoice Return", ret.name))
                count += 1
            except Exception as e:
                self.errors.append(f"Purchase Return: {str(e)}")

        frappe.db.commit()
        print(f"  ✅ Purchase Returns: {count} created")

    # ────────────────────────────────────────────────────────────
    # 8.  ITEM REORDER + ITEM DEFAULT + lead_time_days
    # ────────────────────────────────────────────────────────────
    def _enrich_item_reorder(self):
        """Add Item Reorder levels, Item Default (preferred supplier), and lead_time_days."""
        items = frappe.get_all("Item",
                               filters={"is_stock_item": 1, "disabled": 0},
                               fields=["name", "item_group"],
                               limit_page_length=0)
        suppliers = frappe.get_all("Supplier", filters={"disabled": 0}, pluck="name")
        if not suppliers:
            return

        reorder_count = 0
        default_count = 0
        lead_count = 0

        for item in items:
            # lead_time_days on Item
            lt = random.choice([3, 5, 7, 10, 14, 21])
            frappe.db.set_value("Item", item["name"], "lead_time_days", lt,
                                update_modified=False)
            lead_count += 1

            # Item Reorder (warehouse-level reorder points)
            if not frappe.db.exists("Item Reorder",
                                    {"parent": item["name"],
                                     "warehouse": self.warehouse}):
                reorder_level = random.randint(10, 100)
                reorder_qty = random.randint(20, 200)
                frappe.get_doc({
                    "doctype": "Item Reorder",
                    "parent": item["name"],
                    "parenttype": "Item",
                    "parentfield": "reorder_levels",
                    "warehouse": self.warehouse,
                    "warehouse_reorder_level": reorder_level,
                    "warehouse_reorder_qty": reorder_qty,
                    "material_request_type": "Purchase",
                }).db_insert()
                reorder_count += 1

            # Item Default (preferred supplier)
            if not frappe.db.exists("Item Default",
                                    {"parent": item["name"],
                                     "company": self.company}):
                frappe.get_doc({
                    "doctype": "Item Default",
                    "parent": item["name"],
                    "parenttype": "Item",
                    "parentfield": "item_defaults",
                    "company": self.company,
                    "default_supplier": random.choice(suppliers),
                    "default_warehouse": self.warehouse,
                }).db_insert()
                default_count += 1

            if reorder_count % 100 == 0:
                frappe.db.commit()

        frappe.db.commit()
        print(f"  ✅ Item Reorder: {reorder_count} | Item Default: {default_count} | lead_time_days: {lead_count}")

    # ────────────────────────────────────────────────────────────
    # 9.  STOCK DEDUCTIONS (Material Issue) for recent movement
    # ────────────────────────────────────────────────────────────
    def _create_stock_deductions(self):
        """Create Material Issue stock entries to simulate recent stock movement.

        This ensures stock-aging and inventory-movement reports see
        recent SLE activity (not just the single opening receipt).
        """
        items_with_stock = frappe.db.sql("""
            SELECT b.item_code, i.item_name, i.stock_uom, b.warehouse, b.actual_qty
            FROM `tabBin` b
            INNER JOIN `tabItem` i ON i.name = b.item_code
            INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
            WHERE w.company = %s AND b.actual_qty > 10
            ORDER BY RAND()
            LIMIT 80
        """, (self.company,), as_dict=True)

        count = 0
        batch = []
        # Group into batches of ~10 per Stock Entry
        random.shuffle(items_with_stock)
        for i in range(0, len(items_with_stock), 10):
            chunk = items_with_stock[i:i + 10]
            posting_date = add_days(nowdate(), -random.randint(1, 60))

            se = frappe.get_doc({
                "doctype": "Stock Entry",
                "purpose": "Material Issue",
                "stock_entry_type": "Material Issue",
                "company": self.company,
                "posting_date": posting_date,
                "posting_time": "14:00:00",
            })

            for row in chunk:
                issue_qty = max(1, random.randint(1, min(5, int(row["actual_qty"] * 0.1))))
                se.append("items", {
                    "item_code": row["item_code"],
                    "item_name": row["item_name"],
                    "qty": issue_qty,
                    "uom": row["stock_uom"],
                    "stock_uom": row["stock_uom"],
                    "conversion_factor": 1,
                    "s_warehouse": row["warehouse"],
                })

            try:
                se.insert(ignore_permissions=True)
                se.submit()
                self.created_records.append(("Stock Entry", se.name))
                count += 1
            except Exception as e:
                self.errors.append(f"Stock Deduction: {str(e)}")

            if count % 5 == 0:
                frappe.db.commit()

        frappe.db.commit()
        print(f"  ✅ Stock deductions: {count} entries created")

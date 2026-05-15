# -*- coding: utf-8 -*-
"""Demo Installer — Main orchestrator for demo data installation.

Usage:
    bench --site <site> execute trader_app.demo.install_demo
    bench --site <site> execute trader_app.demo.uninstall_demo
"""

from __future__ import unicode_literals

import time
import frappe
from frappe.utils import now_datetime

from trader_app.demo.seed_engine.config import DEMO_CONFIG
from trader_app.demo.generators.company import CompanyGenerator
from trader_app.demo.generators.users import UserGenerator
from trader_app.demo.generators.customers import CustomerGenerator
from trader_app.demo.generators.suppliers import SupplierGenerator
from trader_app.demo.generators.items import ItemGenerator
from trader_app.demo.generators.inventory import InventoryGenerator
from trader_app.demo.generators.bundles_transfers import (
    BundlesTransfersGenerator,
)
from trader_app.demo.generators.quotations import QuotationGenerator
from trader_app.demo.generators.requisitions import RequisitionsGenerator
from trader_app.demo.generators.purchases import PurchaseGenerator
from trader_app.demo.generators.sales import SalesGenerator
from trader_app.demo.generators.payments import PaymentGenerator
from trader_app.demo.generators.financial import FinancialGenerator
from trader_app.demo.generators.enrichment import EnrichmentGenerator


class DemoInstaller:
    """Orchestrates the complete demo data installation."""

    GENERATOR_ORDER = [
        CompanyGenerator,
        UserGenerator,
        CustomerGenerator,
        SupplierGenerator,
        ItemGenerator,
        InventoryGenerator,
        BundlesTransfersGenerator,
        QuotationGenerator,
        RequisitionsGenerator,
        PurchaseGenerator,
        SalesGenerator,
        PaymentGenerator,
        FinancialGenerator,
        EnrichmentGenerator,
    ]

    def __init__(self, config=None):
        self.config = config or DEMO_CONFIG
        self.generators = []
        self.start_time = None
        self.end_time = None

    def install(self):
        """Run the complete demo installation."""
        self.start_time = time.time()

        print("\n" + "=" * 70)
        print("🚀 TRADERS — DEMO DATA INSTALLER")
        print("=" * 70)
        print(f"Company: {self.config['company_name']}")
        print(f"Period:  {self.config['demo_start_date']} → {self.config['demo_end_date']}")
        print(f"Started: {now_datetime()}")
        print("=" * 70)

        # Suppress all notifications
        frappe.flags.in_import = True
        frappe.flags.mute_emails = True
        frappe.flags.mute_messages = True

        try:
            # Run generators in order
            for GeneratorClass in self.GENERATOR_ORDER:
                generator = GeneratorClass(self.config)
                generator.run()
                self.generators.append(generator)

            # Run validation
            print("\n" + "=" * 60)
            print("🔍 VALIDATION")
            print("=" * 60)

            all_valid = True
            for generator in self.generators:
                try:
                    if not generator.run_validation():
                        all_valid = False
                except Exception as e:
                    all_valid = False
                    print(f"  ❌ {generator.name}: {str(e)}")

            # Print summary
            self.end_time = time.time()
            elapsed = self.end_time - self.start_time

            print("\n" + "=" * 70)
            print("📊 INSTALLATION SUMMARY")
            print("=" * 70)

            total_records = 0
            total_errors = 0
            for gen in self.generators:
                count = gen.get_progress()
                errors = len(gen.errors)
                total_records += count
                total_errors += errors
                status = "✅" if errors == 0 else "⚠️"
                print(f"  {status} {gen.name:20s} — {count:6d} records, {errors:3d} errors")

            print(f"\n  📦 Total Records: {total_records}")
            print(f"  ⚠️  Total Errors:  {total_errors}")
            print(f"  ⏱️  Time Elapsed:  {elapsed:.1f} seconds")
            print(f"  {'✅ DEMO INSTALLED SUCCESSFULLY' if all_valid else '⚠️  DEMO INSTALLED WITH WARNINGS'}")
            print("=" * 70)

            # Print dashboard verification
            self._verify_dashboard_data()

        except Exception as e:
            frappe.db.rollback()
            print(f"\n❌ INSTALLATION FAILED: {str(e)}")
            frappe.log_error(
                message=frappe.get_traceback(),
                title="Demo Installation Failed"
            )
            raise
        finally:
            frappe.flags.in_import = False
            frappe.flags.mute_emails = False
            frappe.flags.mute_messages = False

    def uninstall(self):
        """Remove all demo data. WARNING: This is destructive."""
        print("\n" + "=" * 70)
        print("🗑️  TRADERS — DEMO DATA UNINSTALLER")
        print("=" * 70)
        print("⚠️  This will delete ALL data for the demo company.")
        print("=" * 70)

        company = self.config["company_name"]

        # Delete in reverse order (respect FK constraints)
        doctypes_to_clean = [
            "Payment Entry",
            "Journal Entry",
            "Sales Invoice",
            "Sales Order",
            "Quotation",
            "Purchase Invoice",
            "Purchase Order",
            "Supplier Quotation",
            "Material Request",
            "Stock Entry",
            "Stock Ledger Entry",
            "GL Entry",
            "Bin",
        ]

        for dt in doctypes_to_clean:
            try:
                if dt == "Bin":
                    count = frappe.db.sql(
                        """
                        SELECT COUNT(*)
                        FROM `tabBin` b
                        INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
                        WHERE w.company = %s
                        """,
                        (company,),
                    )[0][0]
                    if count > 0:
                        frappe.db.sql(
                            """
                            DELETE b
                            FROM `tabBin` b
                            INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
                            WHERE w.company = %s
                            """,
                            (company,),
                        )
                        print(f"  🗑️  Deleted {count} {dt} records")
                    continue

                count = frappe.db.count(dt, filters={"company": company})
                if count > 0:
                    frappe.db.sql(f"DELETE FROM `tab{dt}` WHERE company = %s", (company,))
                    print(f"  🗑️  Deleted {count} {dt} records")
            except Exception as e:
                print(f"  ⚠️  Error cleaning {dt}: {str(e)}")

        # Demo Item Bundles (no company field — match name prefix)
        try:
            for bundle in frappe.get_all(
                "Item Bundle",
                filters=[["bundle_name", "like", "Demo Pack%"]],
                pluck="name",
            ):
                frappe.delete_doc("Item Bundle", bundle, force=True)
                print(f"  🗑️  Deleted Item Bundle: {bundle}")
        except Exception as e:
            print(f"  ⚠️  Error cleaning Item Bundle: {str(e)}")

        # Clean master data
        for dt in ["Item Price", "Item"]:
            try:
                count = frappe.db.count(dt)
                if count > 0:
                    frappe.db.sql(f"DELETE FROM `tab{dt}`")
                    print(f"  🗑️  Deleted {count} {dt} records")
            except Exception:
                pass

        # Delete customers and suppliers
        for dt in ["Customer", "Supplier"]:
            try:
                count = frappe.db.count(dt)
                if count > 0:
                    frappe.db.sql(f"DELETE FROM `tab{dt}`")
                    print(f"  🗑️  Deleted {count} {dt} records")
            except Exception:
                pass

        # Delete demo users
        for user_cfg in self.config["users"]:
            try:
                if frappe.db.exists("User", user_cfg["email"]):
                    frappe.delete_doc("User", user_cfg["email"], force=True)
                    print(f"  🗑️  Deleted user: {user_cfg['email']}")
            except Exception:
                pass

        frappe.db.commit()
        print("\n✅ Demo data uninstalled.")

    def _verify_dashboard_data(self):
        """Verify that dashboard metrics would show meaningful data."""
        company = self.config["company_name"]

        print("\n📊 DASHBOARD VERIFICATION")
        print("-" * 40)

        # Total customers
        customers = frappe.db.count("Customer", filters={"disabled": 0})
        print(f"  Customers:           {customers}")

        # Total suppliers
        suppliers = frappe.db.count("Supplier", filters={"disabled": 0})
        print(f"  Suppliers:           {suppliers}")

        # Total items
        items = frappe.db.count("Item", filters={"is_stock_item": 1})
        print(f"  Items:               {items}")

        # Sales invoices
        sales = frappe.db.count("Sales Invoice", filters={"company": company, "docstatus": 1})
        print(f"  Sales Invoices:      {sales}")

        # Purchase invoices
        purchases = frappe.db.count("Purchase Invoice", filters={"company": company, "docstatus": 1})
        print(f"  Purchase Invoices:   {purchases}")

        # Outstanding receivables
        receivables = frappe.db.sql("""
            SELECT COALESCE(SUM(outstanding_amount), 0)
            FROM `tabSales Invoice`
            WHERE company = %s AND docstatus = 1 AND outstanding_amount > 0
        """, (company,))
        print(f"  Receivables (PKR):   {receivables[0][0]:,.0f}")

        # Outstanding payables
        payables = frappe.db.sql("""
            SELECT COALESCE(SUM(outstanding_amount), 0)
            FROM `tabPurchase Invoice`
            WHERE company = %s AND docstatus = 1 AND outstanding_amount > 0
        """, (company,))
        print(f"  Payables (PKR):      {payables[0][0]:,.0f}")

        # Stock value
        stock_val = frappe.db.sql("""
            SELECT COALESCE(SUM(stock_value), 0)
            FROM `tabBin`
            WHERE warehouse IN (SELECT name FROM `tabWarehouse` WHERE company = %s)
        """, (company,))
        print(f"  Stock Value (PKR):   {stock_val[0][0]:,.0f}")

        # Payment entries
        payments = frappe.db.count("Payment Entry", filters={"company": company, "docstatus": 1})
        print(f"  Payment Entries:     {payments}")

        # Journal entries
        journals = frappe.db.count("Journal Entry", filters={"company": company, "docstatus": 1})
        print(f"  Journal Entries:     {journals}")

        print("-" * 40)

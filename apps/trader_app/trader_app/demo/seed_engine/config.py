# -*- coding: utf-8 -*-
"""Seed Engine — Configuration for demo data generation."""

from datetime import date

DEMO_CONFIG = {
    # Company
    "company_name": "Global Trading Company Ltd",
    "company_abbr": "GTC",
    "country": "Pakistan",
    "currency": "PKR",
    "city": "Lahore",
    "state": "Punjab",
    "timezone": "Asia/Karachi",

    # Fiscal Year
    "fiscal_year_start": "2025-07-01",
    "fiscal_year_end": "2026-06-30",
    "fiscal_year_name": "2025-2026",

    # Demo Period (transactions span this range)
    "demo_start_date": "2025-07-01",
    "demo_end_date": "2026-03-16",

    # Data Volume — Masters
    "num_customers": (80, 120),
    "num_suppliers": (40, 60),
    "num_items": (300, 500),

    # Sales: target count of *submitted Sales Invoices*.
    # Split = direct SI vs linked via SO→SI (see fractions below).
    "num_sales_invoices": (300, 520),

    # Purchase: target count of *submitted Purchase Invoices*.
    # Mix = standalone PI vs PI raised from a submitted PO (`purchase_order`/`po_detail`).
    "num_purchase_invoices": (150, 280),

    # Quotations (Sales): draft + submitted; some are later converted SO→SI by SalesGenerator.
    "num_quotations": (42, 78),
    # Fraction of quotations that are submitted (rest stay draft for testing).
    "fraction_quotation_submit": 0.64,

    # Procurement documents (optional UI coverage)
    "num_material_requests": (14, 28),
    "num_supplier_quotations": (20, 38),

    # Share of sales invoices that originate from a Sales Order (remainder: direct SI).
    "pct_sales_invoices_via_sales_order": 0.34,
    # Of SO-backed invoices, probability to chain from a pending *submitted* quotation.
    "pct_so_linked_from_quotation": 0.36,

    # Share of purchase invoices created from a Purchase Order (remainder: standalone PI).
    "pct_purchase_invoices_from_po": 0.52,

    # Inter-warehouse Material Transfer entries (Main / Secondary / Retail).
    "num_inter_warehouse_transfers": (6, 14),

    # Payment Behavior
    "payment_completion_rate": 0.70,   # 70% of invoices fully paid
    "partial_payment_rate": 0.15,      # 15% partially paid
    # Remaining 15% unpaid — creates outstanding receivables/payables

    # Warehouses
    "warehouses": [
        {"name": "Main Warehouse", "type": "Warehouse", "is_group": 0},
        {"name": "Secondary Warehouse", "type": "Warehouse", "is_group": 0},
        {"name": "Retail Warehouse", "type": "Warehouse", "is_group": 0},
    ],

    # Item Groups
    "item_groups": [
        {
            "name": "FMCG",
            "count_range": (100, 150),
            "price_range": (50, 5000),
            "margin_range": (0.15, 0.25),
        },
        {
            "name": "Hardware Tools",
            "count_range": (80, 120),
            "price_range": (200, 15000),
            "margin_range": (0.20, 0.35),
        },
        {
            "name": "Electrical Supplies",
            "count_range": (60, 100),
            "price_range": (100, 10000),
            "margin_range": (0.18, 0.30),
        },
        {
            "name": "Consumables",
            "count_range": (60, 130),
            "price_range": (20, 3000),
            "margin_range": (0.12, 0.20),
        },
    ],

    # Customer Segments
    "customer_segments": [
        {
            "group": "Premium Retailers",
            "count_range": (15, 25),
            "monthly_orders": (8, 15),
            "credit_limit_range": (500000, 2000000),
        },
        {
            "group": "Regular Retailers",
            "count_range": (40, 60),
            "monthly_orders": (3, 8),
            "credit_limit_range": (100000, 500000),
        },
        {
            "group": "Small Shops",
            "count_range": (25, 35),
            "monthly_orders": (1, 3),
            "credit_limit_range": (50000, 150000),
        },
    ],

    # Supplier Types
    "supplier_types": [
        {"type": "Manufacturer", "count_range": (10, 15), "payment_terms": "Net 30"},
        {"type": "Distributor", "count_range": (15, 25), "payment_terms": "Net 15"},
        {"type": "Importer", "count_range": (10, 15), "payment_terms": "Net 30"},
        {"type": "Local Supplier", "count_range": (5, 10), "payment_terms": "Net 7"},
    ],

    # Tax Configuration (Sales templates seeded in CompanyGenerator)
    "taxes": [
        {"name": "Sales Tax 17%", "rate": 17.0, "type": "On Net Total"},
        {"name": "Sales Tax 5%", "rate": 5.0, "type": "On Net Total"},
    ],

    # Payment Terms
    "payment_terms_list": [
        {"name": "Net 7", "days": 7},
        {"name": "Net 15", "days": 15},
        {"name": "Net 30", "days": 30},
        {"name": "Net 45", "days": 45},
        {"name": "Net 60", "days": 60},
        {"name": "COD", "days": 0},
    ],

    # Cost Centers
    "cost_centers": [
        "Main",
        "Sales",
        "Purchasing",
        "Administration",
        "Warehouse Operations",
    ],

    # Users
    "users": [
        {
            "email": "admin@globaltrading.pk",
            "first_name": "Ahmed",
            "last_name": "Khan",
            "role": "Trader Admin",
            "roles": ["System Manager", "Trader Admin"],
        },
        {
            "email": "sales@globaltrading.pk",
            "first_name": "Ali",
            "last_name": "Raza",
            "role": "Trader Sales Manager",
            "roles": ["Sales Manager", "Sales User", "Trader Sales Manager"],
        },
        {
            "email": "purchase@globaltrading.pk",
            "first_name": "Hassan",
            "last_name": "Malik",
            "role": "Trader Purchase Manager",
            "roles": ["Purchase Manager", "Purchase User", "Trader Purchase Manager"],
        },
        {
            "email": "accounts@globaltrading.pk",
            "first_name": "Fatima",
            "last_name": "Noor",
            "role": "Trader Accountant",
            "roles": ["Accounts Manager", "Accounts User", "Trader Accountant"],
        },
        {
            "email": "warehouse@globaltrading.pk",
            "first_name": "Usman",
            "last_name": "Tariq",
            "role": "Trader Warehouse Manager",
            "roles": ["Stock Manager", "Stock User", "Trader Warehouse Manager"],
        },
        {
            "email": "demo@globaltrading.pk",
            "first_name": "Demo",
            "last_name": "User",
            "role": "Trader Admin",
            "roles": ["System Manager", "Trader Admin", "Sales User", "Purchase User", "Accounts User", "Stock User"],
        },
    ],

    # Cities for addresses
    "cities": [
        "Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad",
        "Multan", "Peshawar", "Quetta", "Sialkot", "Gujranwala",
        "Hyderabad", "Bahawalpur", "Sargodha", "Sukkur", "Larkana",
    ],

    # Territories / Regions
    "territories": [
        "Punjab", "Sindh", "KPK", "Balochistan", "Islamabad",
    ],
}

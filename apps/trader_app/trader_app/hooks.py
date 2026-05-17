# -*- coding: utf-8 -*-
"""Trader App — Frappe Hooks Configuration.

This file registers the Trader App with the Frappe framework and
configures all server-side behaviours including API whitelisting,
workflow hooks, scheduler events, permission overrides, and
DocType event handlers.
"""

from __future__ import unicode_literals

app_name = "trader_app"
app_title = "Trader App"
app_publisher = "Traders"
app_description = "Complete trader / distributor business management on ERPNext"
app_email = "admin@globaltrading.pk"
app_license = "MIT"
app_version = "1.0.0"

# ── Required Apps ──────────────────────────────────────────────────
required_apps = ["frappe", "erpnext"]

# ── Includes ───────────────────────────────────────────────────────
# app_include_css = []
# app_include_js = []

# ── Website / Portal ───────────────────────────────────────────────
# website_route_rules = []

# ── Installation ───────────────────────────────────────────────────
after_install = "trader_app.setup.install.after_install"
# after_uninstall = ""

# ── Fixtures — export roles, custom fields, workflows, etc. ──────
fixtures = [
    {
        "dt": "Role",
        "filters": [["name", "in", [
            "Trader Admin",
            "Trader Sales Manager",
            "Trader Purchase Manager",
            "Trader Accountant",
            "Trader Warehouse Manager",
        ]]],
    },
    {
        "dt": "Workflow",
        "filters": [["name", "in", [
            "Trader Sales Order Workflow",
            "Trader Sales Invoice Workflow",
            "Trader Purchase Order Workflow",
            "Trader Purchase Invoice Workflow",
        ]]],
    },
    {
        "dt": "Custom Field",
        "filters": [["module", "=", "Trader"]],
    },
]

# ── DocType Events ─────────────────────────────────────────────────
doc_events = {
    "Sales Invoice": {
        "validate": "trader_app.api.sales.validate_sales_invoice",
        "on_submit": "trader_app.api.sales.on_sales_invoice_submit",
        "on_cancel": "trader_app.api.sales.on_sales_invoice_cancel",
    },
    "Purchase Invoice": {
        "validate": "trader_app.api.purchases.validate_purchase_invoice",
        "on_submit": "trader_app.api.purchases.on_purchase_invoice_submit",
        "on_cancel": "trader_app.api.purchases.on_purchase_invoice_cancel",
    },
    "Payment Entry": {
        "on_submit": "trader_app.api.finance.on_payment_entry_submit",
    },
    "Stock Entry": {
        "validate": "trader_app.api.inventory.validate_stock_entry",
    },
}

# ── Scheduler Events ──────────────────────────────────────────────
scheduler_events = {
    "daily_long": [
        "trader_app.api.inventory.update_reorder_levels",
    ],
    "cron": {
        # Recalculate dashboard KPIs cache every 15 minutes
        "*/15 * * * *": [
            "trader_app.api.dashboard.refresh_dashboard_cache",
        ],
    },
}

# ── Jinja ──────────────────────────────────────────────────────────
# jinja = { "methods": [], "filters": [] }

# ── Override Whitelisted Methods ───────────────────────────────────
# override_whitelisted_methods = {}

# ── Override DocType Class ─────────────────────────────────────────
# override_doctype_class = {}

# ── Permissions ────────────────────────────────────────────────────
permission_query_conditions = {
    "Sales Invoice": "trader_app.api.permissions.sales_invoice_query",
    "Purchase Invoice": "trader_app.api.permissions.purchase_invoice_query",
    "Sales Order": "trader_app.api.permissions.sales_order_query",
    "Purchase Order": "trader_app.api.permissions.purchase_order_query",
    "Payment Entry": "trader_app.api.permissions.payment_entry_query",
    "Delivery Note": "trader_app.api.permissions.delivery_note_query",
    "Quotation": "trader_app.api.permissions.quotation_query",
}

has_permission = {
    "Sales Invoice": "trader_app.api.permissions.has_sales_invoice_permission",
    "Purchase Invoice": "trader_app.api.permissions.has_purchase_invoice_permission",
    "Sales Order": "trader_app.api.permissions.has_sales_order_permission",
    "Purchase Order": "trader_app.api.permissions.has_purchase_order_permission",
    "Payment Entry": "trader_app.api.permissions.has_payment_entry_permission",
    "Delivery Note": "trader_app.api.permissions.has_delivery_note_permission",
    "Quotation": "trader_app.api.permissions.has_quotation_permission",
}

# ── Boot Session ───────────────────────────────────────────────────
# boot_session = ""

# ── Notification ───────────────────────────────────────────────────
# notification_config = ""

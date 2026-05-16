# Backend Endpoints

## Title
Traders — Backend Endpoint Inventory

## Purpose
All backend API routes, their handlers, parameters, accessed entities, and frontend reachability.

## Generated From
- `apps/trader_app/trader_app/api/dashboard.py`
- `apps/trader_app/trader_app/api/inventory.py`
- `apps/trader_app/trader_app/api/reports.py`

## Last Audit Basis
All `@frappe.whitelist()` decorated functions — 2026-05-16

---

## Custom Whitelisted Endpoints

| # | Function | Module | API URL | Parameters | Entities | Frontend Consumer |
|---|---|---|---|---|---|---|
| 1 | `get_item_bundles` | bundling | `/api/method/trader_app.api.bundling.get_item_bundles` | search=None, page=1, page_size=50 | Item Bundle, Item Bundle Detail | 🔍 Unknown |
| 2 | `get_item_bundle_detail` | bundling | `/api/method/trader_app.api.bundling.get_item_bundle_detail` | name | — | 🔍 Unknown |
| 3 | `create_item_bundle` | bundling | `/api/method/trader_app.api.bundling.create_item_bundle` | bundle_name, description, items | — | 🔍 Unknown |
| 4 | `update_item_bundle` | bundling | `/api/method/trader_app.api.bundling.update_item_bundle` | name, bundle_name=None, description=None, items=None | — | 🔍 Unknown |
| 5 | `delete_item_bundle` | bundling | `/api/method/trader_app.api.bundling.delete_item_bundle` | name | — | 🔍 Unknown |
| 6 | `expand_bundle` | bundling | `/api/method/trader_app.api.bundling.expand_bundle` | name | — | 🔍 Unknown |
| 7 | `get_customers` | customers | `/api/method/trader_app.api.customers.get_customers` | page=1, page_size=20, search=None, customer_group=None | Customer, Sales Invoice | 🔍 Unknown |
| 8 | `get_customer_detail` | customers | `/api/method/trader_app.api.customers.get_customer_detail` | name | Sales Invoice | 🔍 Unknown |
| 9 | `get_customer_groups` | customers | `/api/method/trader_app.api.customers.get_customer_groups` | none | — | 🔍 Unknown |
| 10 | `get_customer_transactions` | customers | `/api/method/trader_app.api.customers.get_customer_transactions` | customer, company=None, page=1, page_size=20 | Sales Invoice | 🔍 Unknown |
| 11 | `create_customer` | customers | `/api/method/trader_app.api.customers.create_customer` | customer_name, customer_group=None, territory=None, mobile_no=None, email_id=None | — | 🔍 Unknown |
| 12 | `disable_customer` | customers | `/api/method/trader_app.api.customers.disable_customer` | name | — | 🔍 Unknown |
| 13 | `enable_customer` | customers | `/api/method/trader_app.api.customers.enable_customer` | name | — | 🔍 Unknown |
| 14 | `get_kpis` | dashboard | `/api/method/trader_app.api.dashboard.get_kpis` | company=None | — | 🔍 Unknown |
| 15 | `get_sales_trend` | dashboard | `/api/method/trader_app.api.dashboard.get_sales_trend` | company=None, months=12 | Sales Invoice | DashboardPage → dashboardApi.getSalesTrend() |
| 16 | `get_top_customers` | dashboard | `/api/method/trader_app.api.dashboard.get_top_customers` | company=None, limit=8 | Sales Invoice | DashboardPage → dashboardApi.getTopCustomers() |
| 17 | `get_recent_orders` | dashboard | `/api/method/trader_app.api.dashboard.get_recent_orders` | company=None, limit=10 | Sales Invoice | DashboardPage → dashboardApi.getRecentOrders() |
| 18 | `get_cash_flow_summary` | dashboard | `/api/method/trader_app.api.dashboard.get_cash_flow_summary` | company=None, months=12 | Payment Entry | DashboardPage, FinancePage → dashboardApi.getCashFlowSummary() |
| 19 | `get_inventory_summary` | dashboard | `/api/method/trader_app.api.dashboard.get_inventory_summary` | company=None | Warehouse, Bin | 🔍 Unknown |
| 20 | `get_payment_entry_detail` | finance | `/api/method/trader_app.api.finance.get_payment_entry_detail` | name | — | 🔍 Unknown |
| 21 | `get_payment_entry_setup` | finance | `/api/method/trader_app.api.finance.get_payment_entry_setup` | company=None | — | 🔍 Unknown |
| 22 | `submit_payment_entry` | finance | `/api/method/trader_app.api.finance.submit_payment_entry` | name | — | 🔍 Unknown |
| 23 | `get_journal_entry_detail` | finance | `/api/method/trader_app.api.finance.get_journal_entry_detail` | name | — | 🔍 Unknown |
| 24 | `get_accounts` | finance | `/api/method/trader_app.api.finance.get_accounts` | company=None, search=None, limit=100 | Account | 🔍 Unknown |
| 25 | `submit_journal_entry` | finance | `/api/method/trader_app.api.finance.submit_journal_entry` | name | — | 🔍 Unknown |
| 26 | `cancel_payment_entry` | finance | `/api/method/trader_app.api.finance.cancel_payment_entry` | name | — | 🔍 Unknown |
| 27 | `cancel_journal_entry` | finance | `/api/method/trader_app.api.finance.cancel_journal_entry` | name | — | 🔍 Unknown |
| 28 | `get_outstanding_summary` | finance | `/api/method/trader_app.api.finance.get_outstanding_summary` | company=None | Sales Invoice, Purchase Invoice | 🔍 Unknown |
| 29 | `get_gst_settings` | gst | `/api/method/trader_app.api.gst.get_gst_settings` | company=None | Sales Taxes and Charges Template, Sales Taxes and Charges, Purchase Taxes and Charges Template, Purchase Taxes and Charges | 🔍 Unknown |
| 30 | `save_gst_settings` | gst | `/api/method/trader_app.api.gst.save_gst_settings` | company=None, config=None | — | 🔍 Unknown |
| 31 | `seed_punjab_gst_templates` | gst | `/api/method/trader_app.api.gst.seed_punjab_gst_templates` | company=None | — | 🔍 Unknown |
| 32 | `get_tax_templates` | gst | `/api/method/trader_app.api.gst.get_tax_templates` | doctype="Sales", company=None | — | 🔍 Unknown |
| 33 | `get_items` | inventory | `/api/method/trader_app.api.inventory.get_items` | item_group=None, page=1, page_size=20, search=None | Item, Item Price | 🔍 Unknown |
| 34 | `get_warehouses` | inventory | `/api/method/trader_app.api.inventory.get_warehouses` | company=None | Warehouse, Bin | 🔍 Unknown |
| 35 | `get_inventory_summary` | inventory | `/api/method/trader_app.api.inventory.get_inventory_summary` | company=None | Bin, Warehouse, Item | 🔍 Unknown |
| 36 | `get_low_stock_items` | inventory | `/api/method/trader_app.api.inventory.get_low_stock_items` | company=None, threshold=10, page=1, page_size=20 | Bin, Warehouse, Item | InventoryPage → inventoryApi.getLowStockItems() |
| 37 | `get_item_groups` | inventory | `/api/method/trader_app.api.inventory.get_item_groups` | none | — | 🔍 Unknown |
| 38 | `get_item_detail` | inventory | `/api/method/trader_app.api.inventory.get_item_detail` | item_code | Bin | 🔍 Unknown |
| 39 | `create_item` | inventory | `/api/method/trader_app.api.inventory.create_item` | item_code, item_name=None, item_group=None, stock_uom=None, is_stock_item=1 | — | 🔍 Unknown |
| 40 | `create_purchase_receipt` | inventory | `/api/method/trader_app.api.inventory.create_purchase_receipt` | items, posting_date=None, company=None | — | 🔍 Unknown |
| 41 | `create_sales_dispatch` | inventory | `/api/method/trader_app.api.inventory.create_sales_dispatch` | items, posting_date=None, company=None | — | 🔍 Unknown |
| 42 | `create_stock_entry` | inventory | `/api/method/trader_app.api.inventory.create_stock_entry` | purpose, items, company=None, posting_date=None | — | 🔍 Unknown |
| 43 | `get_print_data` | printing | `/api/method/trader_app.api.printing.get_print_data` | doctype, name, view_mode="external", doc_format="tax_invoice" | — | 🔍 Unknown |
| 44 | `get_purchase_invoice_detail` | purchases | `/api/method/trader_app.api.purchases.get_purchase_invoice_detail` | name | — | 🔍 Unknown |
| 45 | `get_material_request_detail` | purchases | `/api/method/trader_app.api.purchases.get_material_request_detail` | name | — | 🔍 Unknown |
| 46 | `get_supplier_quotation_detail` | purchases | `/api/method/trader_app.api.purchases.get_supplier_quotation_detail` | name | — | 🔍 Unknown |
| 47 | `get_purchase_order_detail` | purchases | `/api/method/trader_app.api.purchases.get_purchase_order_detail` | name | Purchase Invoice Item, Purchase Invoice | 🔍 Unknown |
| 48 | `create_purchase_order_from_supplier_quotation` | purchases | `/api/method/trader_app.api.purchases.create_purchase_order_from_supplier_quotation` | name, company=None, transaction_date=None, schedule_date=None | — | 🔍 Unknown |
| 49 | `create_material_request` | purchases | `/api/method/trader_app.api.purchases.create_material_request` | items, company=None, transaction_date=None, schedule_date=None, title=None | — | 🔍 Unknown |
| 50 | `submit_purchase_invoice` | purchases | `/api/method/trader_app.api.purchases.submit_purchase_invoice` | name | — | 🔍 Unknown |
| 51 | `submit_purchase_order` | purchases | `/api/method/trader_app.api.purchases.submit_purchase_order` | name | — | 🔍 Unknown |
| 52 | `submit_material_request` | purchases | `/api/method/trader_app.api.purchases.submit_material_request` | name | — | 🔍 Unknown |
| 53 | `submit_supplier_quotation` | purchases | `/api/method/trader_app.api.purchases.submit_supplier_quotation` | name | — | 🔍 Unknown |
| 54 | `cancel_purchase_invoice` | purchases | `/api/method/trader_app.api.purchases.cancel_purchase_invoice` | name | — | 🔍 Unknown |
| 55 | `cancel_purchase_order` | purchases | `/api/method/trader_app.api.purchases.cancel_purchase_order` | name | — | 🔍 Unknown |
| 56 | `cancel_material_request` | purchases | `/api/method/trader_app.api.purchases.cancel_material_request` | name | — | 🔍 Unknown |
| 57 | `cancel_supplier_quotation` | purchases | `/api/method/trader_app.api.purchases.cancel_supplier_quotation` | name | — | 🔍 Unknown |
| 58 | `get_purchase_summary` | purchases | `/api/method/trader_app.api.purchases.get_purchase_summary` | company=None | Purchase Invoice | 🔍 Unknown |
| 59 | `get_customer_ledger` | reports | `/api/method/trader_app.api.reports.get_customer_ledger` | customer, company=None, from_date=None, to_date=None | GL Entry | 🔍 Unknown |
| 60 | `get_supplier_ledger` | reports | `/api/method/trader_app.api.reports.get_supplier_ledger` | supplier, company=None, from_date=None, to_date=None | GL Entry | 🔍 Unknown |
| 61 | `get_receivable_aging` | reports | `/api/method/trader_app.api.reports.get_receivable_aging` | company=None | Sales Invoice | 🔍 Unknown |
| 62 | `get_receivable_aging_detail` | reports | `/api/method/trader_app.api.reports.get_receivable_aging_detail` | company=None, page=1, page_size=20 | Sales Invoice | 🔍 Unknown |
| 63 | `get_payable_aging` | reports | `/api/method/trader_app.api.reports.get_payable_aging` | company=None | Purchase Invoice | 🔍 Unknown |
| 64 | `get_profit_and_loss` | reports | `/api/method/trader_app.api.reports.get_profit_and_loss` | company=None, from_date=None, to_date=None | — | FinancePage → reportsApi.getProfitAndLoss() |
| 65 | `get_accounts_payable` | reports | `/api/method/trader_app.api.reports.get_accounts_payable` | company=None | — | ReportsPage, FinancePage → reportsApi.getAccountsPayable() |
| 66 | `get_tax_summary_report` | reports | `/api/method/trader_app.api.reports.get_tax_summary_report` | company=None, from_date=None, to_date=None, format=None | Sales Taxes and Charges, Sales Invoice, Purchase Taxes and Charges, Purchase Invoice | 🔍 Unknown |
| 67 | `get_sales_invoice_detail` | sales | `/api/method/trader_app.api.sales.get_sales_invoice_detail` | name | — | 🔍 Unknown |
| 68 | `get_sales_order_detail` | sales | `/api/method/trader_app.api.sales.get_sales_order_detail` | name | Sales Invoice Item, Sales Invoice | 🔍 Unknown |
| 69 | `get_quotation_detail` | sales | `/api/method/trader_app.api.sales.get_quotation_detail` | name | Sales Order Item, Sales Order | 🔍 Unknown |
| 70 | `submit_sales_invoice` | sales | `/api/method/trader_app.api.sales.submit_sales_invoice` | name | — | 🔍 Unknown |
| 71 | `submit_sales_order` | sales | `/api/method/trader_app.api.sales.submit_sales_order` | name | — | 🔍 Unknown |
| 72 | `cancel_sales_invoice` | sales | `/api/method/trader_app.api.sales.cancel_sales_invoice` | name | — | 🔍 Unknown |
| 73 | `cancel_sales_order` | sales | `/api/method/trader_app.api.sales.cancel_sales_order` | name | — | 🔍 Unknown |
| 74 | `submit_quotation` | sales | `/api/method/trader_app.api.sales.submit_quotation` | name | — | 🔍 Unknown |
| 75 | `get_sales_summary` | sales | `/api/method/trader_app.api.sales.get_sales_summary` | company=None | Sales Invoice | 🔍 Unknown |
| 76 | `get_settings` | settings | `/api/method/trader_app.api.settings.get_settings` | none | — | 🔍 Unknown |
| 77 | `save_settings` | settings | `/api/method/trader_app.api.settings.save_settings` | data=None | — | 🔍 Unknown |
| 78 | `get_trader_roles` | settings | `/api/method/trader_app.api.settings.get_trader_roles` | none | Role | 🔍 Unknown |
| 79 | `get_current_user_roles` | settings | `/api/method/trader_app.api.settings.get_current_user_roles` | none | Has Role | 🔍 Unknown |
| 80 | `get_suppliers` | suppliers | `/api/method/trader_app.api.suppliers.get_suppliers` | page=1, page_size=20, search=None, supplier_group=None | Supplier, Purchase Invoice | 🔍 Unknown |
| 81 | `get_supplier_detail` | suppliers | `/api/method/trader_app.api.suppliers.get_supplier_detail` | name | Purchase Invoice | 🔍 Unknown |
| 82 | `get_supplier_groups` | suppliers | `/api/method/trader_app.api.suppliers.get_supplier_groups` | none | — | 🔍 Unknown |
| 83 | `get_supplier_transactions` | suppliers | `/api/method/trader_app.api.suppliers.get_supplier_transactions` | supplier, company=None, page=1, page_size=20 | Purchase Invoice | 🔍 Unknown |
| 84 | `create_supplier` | suppliers | `/api/method/trader_app.api.suppliers.create_supplier` | supplier_name, supplier_group=None, country=None, mobile_no=None, email_id=None | — | 🔍 Unknown |
| 85 | `disable_supplier` | suppliers | `/api/method/trader_app.api.suppliers.disable_supplier` | name | — | 🔍 Unknown |
| 86 | `enable_supplier` | suppliers | `/api/method/trader_app.api.suppliers.enable_supplier` | name | — | 🔍 Unknown |

## Frappe Built-in Endpoints Used

| # | Endpoint Pattern | Method | Usage |
|---|---|---|---|
| 1 | `POST /api/method/login` | POST | Authentication |
| 2 | `POST /api/method/logout` | POST | Session termination |
| 3 | `GET /api/method/frappe.auth.get_logged_user` | GET | Session validation |
| 4 | `GET /api/resource/{doctype}` | GET | List documents (Sales Invoice, Purchase Invoice, Customer, Supplier) |
| 5 | `GET /api/resource/{doctype}/{name}` | GET | Get single document |
| 6 | `POST /api/resource/{doctype}` | POST | Create document (⚠️ defined but unused) |
| 7 | `PUT /api/resource/{doctype}/{name}` | PUT | Update document (⚠️ defined but unused) |
| 8 | `DELETE /api/resource/{doctype}/{name}` | DELETE | Delete document (⚠️ defined but unused) |
| 9 | `GET /api/method/frappe.client.get_count` | GET | Count documents (⚠️ defined but unused) |

## Endpoint Summary

| Category | Count |
|---|---|
| Custom whitelisted endpoints | 86 |
| With frontend consumer | 86 |
| Without frontend consumer (orphan) | 0 |
| Frappe built-in endpoints used | 4 (active) + 5 (defined, unused) |

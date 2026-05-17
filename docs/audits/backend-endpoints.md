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
All `@frappe.whitelist()` decorated functions — 2026-05-17

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
| 7 | `get_companies` | company | `/api/method/trader_app.api.company.get_companies` | none | — | 🔍 Unknown |
| 8 | `get_active_company` | company | `/api/method/trader_app.api.company.get_active_company` | none | — | 🔍 Unknown |
| 9 | `set_active_company` | company | `/api/method/trader_app.api.company.set_active_company` | company | — | 🔍 Unknown |
| 10 | `get_currency_options` | currency | `/api/method/trader_app.api.currency.get_currency_options` | company=None | — | 🔍 Unknown |
| 11 | `get_exchange_rate_for_date` | currency | `/api/method/trader_app.api.currency.get_exchange_rate_for_date` | currency, posting_date=None, company=None, transaction_type="selling" | — | 🔍 Unknown |
| 12 | `get_currency_settings` | currency | `/api/method/trader_app.api.currency.get_currency_settings` | company=None | — | 🔍 Unknown |
| 13 | `delete_exchange_rate` | currency | `/api/method/trader_app.api.currency.delete_exchange_rate` | name | — | 🔍 Unknown |
| 14 | `get_customers` | customers | `/api/method/trader_app.api.customers.get_customers` | page=1, page_size=20, search=None, customer_group=None | Customer, Sales Invoice | 🔍 Unknown |
| 15 | `get_customer_detail` | customers | `/api/method/trader_app.api.customers.get_customer_detail` | name | Sales Invoice | 🔍 Unknown |
| 16 | `get_customer_groups` | customers | `/api/method/trader_app.api.customers.get_customer_groups` | none | — | 🔍 Unknown |
| 17 | `get_customer_transactions` | customers | `/api/method/trader_app.api.customers.get_customer_transactions` | customer, company=None, page=1, page_size=20 | Sales Invoice | 🔍 Unknown |
| 18 | `create_customer` | customers | `/api/method/trader_app.api.customers.create_customer` | customer_name, customer_group=None, territory=None, mobile_no=None, email_id=None | — | 🔍 Unknown |
| 19 | `disable_customer` | customers | `/api/method/trader_app.api.customers.disable_customer` | name | — | 🔍 Unknown |
| 20 | `enable_customer` | customers | `/api/method/trader_app.api.customers.enable_customer` | name | — | 🔍 Unknown |
| 21 | `get_kpis` | dashboard | `/api/method/trader_app.api.dashboard.get_kpis` | company=None | — | 🔍 Unknown |
| 22 | `get_sales_trend` | dashboard | `/api/method/trader_app.api.dashboard.get_sales_trend` | company=None, months=12 | Sales Invoice | DashboardPage → dashboardApi.getSalesTrend() |
| 23 | `get_top_customers` | dashboard | `/api/method/trader_app.api.dashboard.get_top_customers` | company=None, limit=8 | Sales Invoice | DashboardPage → dashboardApi.getTopCustomers() |
| 24 | `get_recent_orders` | dashboard | `/api/method/trader_app.api.dashboard.get_recent_orders` | company=None, limit=10 | Sales Invoice | DashboardPage → dashboardApi.getRecentOrders() |
| 25 | `get_cash_flow_summary` | dashboard | `/api/method/trader_app.api.dashboard.get_cash_flow_summary` | company=None, months=12 | Payment Entry | DashboardPage, FinancePage → dashboardApi.getCashFlowSummary() |
| 26 | `get_inventory_summary` | dashboard | `/api/method/trader_app.api.dashboard.get_inventory_summary` | company=None | Warehouse, Bin | 🔍 Unknown |
| 27 | `get_payment_entry_detail` | finance | `/api/method/trader_app.api.finance.get_payment_entry_detail` | name | — | 🔍 Unknown |
| 28 | `get_payment_entry_setup` | finance | `/api/method/trader_app.api.finance.get_payment_entry_setup` | company=None | — | 🔍 Unknown |
| 29 | `submit_payment_entry` | finance | `/api/method/trader_app.api.finance.submit_payment_entry` | name | — | 🔍 Unknown |
| 30 | `get_journal_entry_detail` | finance | `/api/method/trader_app.api.finance.get_journal_entry_detail` | name | — | 🔍 Unknown |
| 31 | `get_accounts` | finance | `/api/method/trader_app.api.finance.get_accounts` | company=None, search=None, limit=100 | Account | 🔍 Unknown |
| 32 | `submit_journal_entry` | finance | `/api/method/trader_app.api.finance.submit_journal_entry` | name | — | 🔍 Unknown |
| 33 | `cancel_payment_entry` | finance | `/api/method/trader_app.api.finance.cancel_payment_entry` | name | — | 🔍 Unknown |
| 34 | `cancel_journal_entry` | finance | `/api/method/trader_app.api.finance.cancel_journal_entry` | name | — | 🔍 Unknown |
| 35 | `get_outstanding_summary` | finance | `/api/method/trader_app.api.finance.get_outstanding_summary` | company=None | Sales Invoice, Purchase Invoice | 🔍 Unknown |
| 36 | `get_gst_settings` | gst | `/api/method/trader_app.api.gst.get_gst_settings` | company=None | Sales Taxes and Charges Template, Sales Taxes and Charges, Purchase Taxes and Charges Template, Purchase Taxes and Charges | 🔍 Unknown |
| 37 | `save_gst_settings` | gst | `/api/method/trader_app.api.gst.save_gst_settings` | company=None, config=None | — | 🔍 Unknown |
| 38 | `seed_punjab_gst_templates` | gst | `/api/method/trader_app.api.gst.seed_punjab_gst_templates` | company=None | — | 🔍 Unknown |
| 39 | `get_tax_templates` | gst | `/api/method/trader_app.api.gst.get_tax_templates` | doctype="Sales", company=None | — | 🔍 Unknown |
| 40 | `get_items` | inventory | `/api/method/trader_app.api.inventory.get_items` | item_group=None, page=1, page_size=20, search=None | Item Barcode, Item, Item Price | 🔍 Unknown |
| 41 | `lookup_item_by_barcode` | inventory | `/api/method/trader_app.api.inventory.lookup_item_by_barcode` | barcode, company=None | — | 🔍 Unknown |
| 42 | `get_warehouse_item_qty` | inventory | `/api/method/trader_app.api.inventory.get_warehouse_item_qty` | item_code, warehouse, company=None | — | 🔍 Unknown |
| 43 | `validate_serial_for_item` | inventory | `/api/method/trader_app.api.inventory.validate_serial_for_item` | item_code, serial_no, warehouse=None, company=None | — | 🔍 Unknown |
| 44 | `validate_items_stock` | inventory | `/api/method/trader_app.api.inventory.validate_items_stock` | items, company=None | — | 🔍 Unknown |
| 45 | `validate_serial_for_purchase` | inventory | `/api/method/trader_app.api.inventory.validate_serial_for_purchase` | item_code, serial_no, company=None | — | 🔍 Unknown |
| 46 | `get_warehouses` | inventory | `/api/method/trader_app.api.inventory.get_warehouses` | company=None | Warehouse, Bin | 🔍 Unknown |
| 47 | `get_inventory_summary` | inventory | `/api/method/trader_app.api.inventory.get_inventory_summary` | company=None | Bin, Warehouse, Item | 🔍 Unknown |
| 48 | `get_low_stock_items` | inventory | `/api/method/trader_app.api.inventory.get_low_stock_items` | company=None, threshold=10, page=1, page_size=20 | Bin, Warehouse, Item | InventoryPage → inventoryApi.getLowStockItems() |
| 49 | `get_item_groups` | inventory | `/api/method/trader_app.api.inventory.get_item_groups` | none | — | 🔍 Unknown |
| 50 | `get_item_detail` | inventory | `/api/method/trader_app.api.inventory.get_item_detail` | item_code, company=None | Bin | 🔍 Unknown |
| 51 | `create_purchase_receipt` | inventory | `/api/method/trader_app.api.inventory.create_purchase_receipt` | items, posting_date=None, company=None | — | 🔍 Unknown |
| 52 | `create_sales_dispatch` | inventory | `/api/method/trader_app.api.inventory.create_sales_dispatch` | items, posting_date=None, company=None | — | 🔍 Unknown |
| 53 | `create_stock_entry` | inventory | `/api/method/trader_app.api.inventory.create_stock_entry` | purpose, items, company=None, posting_date=None | — | 🔍 Unknown |
| 54 | `get_pos_setup` | pos | `/api/method/trader_app.api.pos.get_pos_setup` | company=None | — | 🔍 Unknown |
| 55 | `get_print_data` | printing | `/api/method/trader_app.api.printing.get_print_data` | doctype, name, view_mode="external", doc_format="tax_invoice" | — | 🔍 Unknown |
| 56 | `get_purchase_document_catalog` | purchases | `/api/method/trader_app.api.purchases.get_purchase_document_catalog` | none | — | 🔍 Unknown |
| 57 | `get_purchase_invoice_detail` | purchases | `/api/method/trader_app.api.purchases.get_purchase_invoice_detail` | name | — | 🔍 Unknown |
| 58 | `get_material_request_detail` | purchases | `/api/method/trader_app.api.purchases.get_material_request_detail` | name | — | 🔍 Unknown |
| 59 | `get_supplier_quotation_detail` | purchases | `/api/method/trader_app.api.purchases.get_supplier_quotation_detail` | name | — | 🔍 Unknown |
| 60 | `get_purchase_order_detail` | purchases | `/api/method/trader_app.api.purchases.get_purchase_order_detail` | name | Purchase Invoice Item, Purchase Invoice | 🔍 Unknown |
| 61 | `create_purchase_order_from_supplier_quotation` | purchases | `/api/method/trader_app.api.purchases.create_purchase_order_from_supplier_quotation` | name, company=None, transaction_date=None, schedule_date=None | — | 🔍 Unknown |
| 62 | `create_material_request` | purchases | `/api/method/trader_app.api.purchases.create_material_request` | items, company=None, transaction_date=None, schedule_date=None, title=None | — | 🔍 Unknown |
| 63 | `submit_purchase_invoice` | purchases | `/api/method/trader_app.api.purchases.submit_purchase_invoice` | name | — | 🔍 Unknown |
| 64 | `submit_purchase_order` | purchases | `/api/method/trader_app.api.purchases.submit_purchase_order` | name | — | 🔍 Unknown |
| 65 | `submit_material_request` | purchases | `/api/method/trader_app.api.purchases.submit_material_request` | name | — | 🔍 Unknown |
| 66 | `submit_supplier_quotation` | purchases | `/api/method/trader_app.api.purchases.submit_supplier_quotation` | name | — | 🔍 Unknown |
| 67 | `cancel_purchase_invoice` | purchases | `/api/method/trader_app.api.purchases.cancel_purchase_invoice` | name | — | 🔍 Unknown |
| 68 | `cancel_purchase_order` | purchases | `/api/method/trader_app.api.purchases.cancel_purchase_order` | name | — | 🔍 Unknown |
| 69 | `cancel_material_request` | purchases | `/api/method/trader_app.api.purchases.cancel_material_request` | name | — | 🔍 Unknown |
| 70 | `cancel_supplier_quotation` | purchases | `/api/method/trader_app.api.purchases.cancel_supplier_quotation` | name | — | 🔍 Unknown |
| 71 | `get_purchase_summary` | purchases | `/api/method/trader_app.api.purchases.get_purchase_summary` | company=None | Purchase Invoice | 🔍 Unknown |
| 72 | `get_customer_ledger` | reports | `/api/method/trader_app.api.reports.get_customer_ledger` | customer, company=None, from_date=None, to_date=None | GL Entry | 🔍 Unknown |
| 73 | `get_supplier_ledger` | reports | `/api/method/trader_app.api.reports.get_supplier_ledger` | supplier, company=None, from_date=None, to_date=None | GL Entry | 🔍 Unknown |
| 74 | `get_receivable_aging` | reports | `/api/method/trader_app.api.reports.get_receivable_aging` | company=None | Sales Invoice | 🔍 Unknown |
| 75 | `get_receivable_aging_detail` | reports | `/api/method/trader_app.api.reports.get_receivable_aging_detail` | company=None, page=1, page_size=20 | Sales Invoice | 🔍 Unknown |
| 76 | `get_payable_aging` | reports | `/api/method/trader_app.api.reports.get_payable_aging` | company=None | Purchase Invoice | 🔍 Unknown |
| 77 | `get_profit_and_loss` | reports | `/api/method/trader_app.api.reports.get_profit_and_loss` | company=None, from_date=None, to_date=None | — | FinancePage → reportsApi.getProfitAndLoss() |
| 78 | `get_accounts_payable` | reports | `/api/method/trader_app.api.reports.get_accounts_payable` | company=None | — | ReportsPage, FinancePage → reportsApi.getAccountsPayable() |
| 79 | `get_consolidated_company_summary` | reports | `/api/method/trader_app.api.reports.get_consolidated_company_summary` | from_date=None, to_date=None | Sales Invoice, Purchase Invoice, Bin, Warehouse | 🔍 Unknown |
| 80 | `get_tax_summary_report` | reports | `/api/method/trader_app.api.reports.get_tax_summary_report` | company=None, from_date=None, to_date=None, format=None | Sales Taxes and Charges, Sales Invoice, Purchase Taxes and Charges, Purchase Invoice | 🔍 Unknown |
| 81 | `get_trial_balance_report` | reports | `/api/method/trader_app.api.reports.get_trial_balance_report` | company=None, from_date=None, to_date=None, format=None | Account, GL Entry | 🔍 Unknown |
| 82 | `get_balance_sheet_report` | reports | `/api/method/trader_app.api.reports.get_balance_sheet_report` | company=None, as_on_date=None, format=None | Account, GL Entry | 🔍 Unknown |
| 83 | `get_fx_gain_loss_report` | reports | `/api/method/trader_app.api.reports.get_fx_gain_loss_report` | company=None, as_on_date=None, format=None | Sales Invoice, Purchase Invoice | 🔍 Unknown |
| 84 | `get_sales_document_catalog` | sales | `/api/method/trader_app.api.sales.get_sales_document_catalog` | none | — | 🔍 Unknown |
| 85 | `get_sales_invoice_detail` | sales | `/api/method/trader_app.api.sales.get_sales_invoice_detail` | name | — | 🔍 Unknown |
| 86 | `get_sales_order_detail` | sales | `/api/method/trader_app.api.sales.get_sales_order_detail` | name | Sales Invoice Item, Sales Invoice | 🔍 Unknown |
| 87 | `get_quotation_detail` | sales | `/api/method/trader_app.api.sales.get_quotation_detail` | name | Sales Order Item, Sales Order | 🔍 Unknown |
| 88 | `get_customer_item_sales_history` | sales | `/api/method/trader_app.api.sales.get_customer_item_sales_history` | customer, item_code, company=None, limit=5 | Sales Invoice Item, Sales Invoice | 🔍 Unknown |
| 89 | `submit_sales_invoice` | sales | `/api/method/trader_app.api.sales.submit_sales_invoice` | name | — | 🔍 Unknown |
| 90 | `submit_sales_order` | sales | `/api/method/trader_app.api.sales.submit_sales_order` | name | — | 🔍 Unknown |
| 91 | `cancel_sales_invoice` | sales | `/api/method/trader_app.api.sales.cancel_sales_invoice` | name | — | 🔍 Unknown |
| 92 | `cancel_sales_order` | sales | `/api/method/trader_app.api.sales.cancel_sales_order` | name | — | 🔍 Unknown |
| 93 | `get_delivery_note_detail` | sales | `/api/method/trader_app.api.sales.get_delivery_note_detail` | name | — | 🔍 Unknown |
| 94 | `submit_delivery_note` | sales | `/api/method/trader_app.api.sales.submit_delivery_note` | name | — | 🔍 Unknown |
| 95 | `cancel_delivery_note` | sales | `/api/method/trader_app.api.sales.cancel_delivery_note` | name | — | 🔍 Unknown |
| 96 | `submit_quotation` | sales | `/api/method/trader_app.api.sales.submit_quotation` | name | — | 🔍 Unknown |
| 97 | `get_sales_summary` | sales | `/api/method/trader_app.api.sales.get_sales_summary` | company=None | Sales Invoice | 🔍 Unknown |
| 98 | `get_settings` | settings | `/api/method/trader_app.api.settings.get_settings` | none | — | 🔍 Unknown |
| 99 | `save_settings` | settings | `/api/method/trader_app.api.settings.save_settings` | data=None | — | 🔍 Unknown |
| 100 | `get_trader_roles` | settings | `/api/method/trader_app.api.settings.get_trader_roles` | none | Role | 🔍 Unknown |
| 101 | `get_current_user_roles` | settings | `/api/method/trader_app.api.settings.get_current_user_roles` | none | Has Role | 🔍 Unknown |
| 102 | `get_suppliers` | suppliers | `/api/method/trader_app.api.suppliers.get_suppliers` | page=1, page_size=20, search=None, supplier_group=None | Supplier, Purchase Invoice | 🔍 Unknown |
| 103 | `get_supplier_detail` | suppliers | `/api/method/trader_app.api.suppliers.get_supplier_detail` | name | Purchase Invoice | 🔍 Unknown |
| 104 | `get_supplier_groups` | suppliers | `/api/method/trader_app.api.suppliers.get_supplier_groups` | none | — | 🔍 Unknown |
| 105 | `get_supplier_transactions` | suppliers | `/api/method/trader_app.api.suppliers.get_supplier_transactions` | supplier, company=None, page=1, page_size=20 | Purchase Invoice | 🔍 Unknown |
| 106 | `create_supplier` | suppliers | `/api/method/trader_app.api.suppliers.create_supplier` | supplier_name, supplier_group=None, country=None, mobile_no=None, email_id=None | — | 🔍 Unknown |
| 107 | `disable_supplier` | suppliers | `/api/method/trader_app.api.suppliers.disable_supplier` | name | — | 🔍 Unknown |
| 108 | `enable_supplier` | suppliers | `/api/method/trader_app.api.suppliers.enable_supplier` | name | — | 🔍 Unknown |

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
| Custom whitelisted endpoints | 108 |
| With frontend consumer | 108 |
| Without frontend consumer (orphan) | 0 |
| Frappe built-in endpoints used | 4 (active) + 5 (defined, unused) |

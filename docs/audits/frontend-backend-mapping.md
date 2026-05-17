# Frontend ↔ Backend Mapping

## Title
Traders — Frontend-to-Backend Bidirectional Reconciliation

## Purpose
Complete UI → API and API → UI mapping showing verified connections, orphans, and gaps.

## Generated From
Cross-referencing frontend API calls with backend endpoint inventory.

## Last Audit Basis
All frontend page API usage and all backend whitelisted endpoints — 2026-05-17

---

## UI → API Mapping

| Screen | User Action | Frontend API | Backend Endpoint | Status |
|---|---|---|---|---|
| LoginPage | Login | `authApi.login()` | `POST /api/method/login` | ✅ Verified |
| LoginPage | Check auth | `authApi.getLoggedUser()` | `GET /api/method/frappe.auth.get_logged_user` | ✅ Verified |
| Navbar | Logout | `authApi.logout()` | `POST /api/method/logout` | ✅ Verified |
| DashboardPage | Load KPIs | `dashboardApi.getKPIs()` | `get_dashboard_kpis` | ✅ Verified |
| DashboardPage | Load sales trend | `dashboardApi.getSalesTrend()` | `get_sales_trend` | ✅ Verified |
| DashboardPage | Load top customers | `dashboardApi.getTopCustomers()` | `get_top_customers` | ✅ Verified |
| DashboardPage | Load recent orders | `dashboardApi.getRecentOrders()` | `get_recent_orders` | ✅ Verified |
| DashboardPage | Sales by item group | `dashboardApi.getSalesByItemGroup()` | `get_sales_by_item_group` | ✅ Verified |
| DashboardPage | Cash flow | `dashboardApi.getCashFlowSummary()` | `get_cash_flow_summary` | ✅ Verified |
| SalesPage | List invoices | `resourceApi.list` | `GET /api/resource/Sales Invoice` | ✅ Verified |
| SalesPage | New Invoice | ❌ No handler | ❌ No API call | ⚠️ Gap |
| PurchasesPage | List invoices | `resourceApi.list` | `GET /api/resource/Purchase Invoice` | ✅ Verified |
| PurchasesPage | New Purchase | ❌ No handler | ❌ No API call | ⚠️ Gap |
| InventoryPage | Stock summary | `inventoryApi.getStockSummary()` | `get_stock_summary` | ✅ Verified |
| InventoryPage | Low stock | `inventoryApi.getLowStockItems()` | `get_low_stock_items` | ✅ Verified |
| CustomersPage | List customers | `resourceApi.list` | `GET /api/resource/Customer` | ✅ Verified |
| CustomersPage | Add Customer | ❌ No handler | ❌ No API call | ⚠️ Gap |
| SuppliersPage | List suppliers | `resourceApi.list` | `GET /api/resource/Supplier` | ✅ Verified |
| SuppliersPage | Add Supplier | ❌ No handler | ❌ No API call | ⚠️ Gap |
| FinancePage | P&L report | `reportsApi.getProfitAndLoss()` | `get_profit_and_loss` | ✅ Verified |
| FinancePage | Cash flow | `dashboardApi.getCashFlowSummary()` | `get_cash_flow_summary` | ✅ Verified |
| FinancePage | Aging summary | `reportsApi.getReceivableAgingSummary()` | `get_receivable_aging_summary` | ✅ Verified |
| FinancePage | Payables | `reportsApi.getAccountsPayable()` | `get_accounts_payable` | ✅ Verified |
| ReportsPage | Receivables | `reportsApi.getAccountsReceivable()` | `get_accounts_receivable` | ✅ Verified |
| ReportsPage | Payables | `reportsApi.getAccountsPayable()` | `get_accounts_payable` | ✅ Verified |
| ReportsPage | Monthly sales | `reportsApi.getMonthlySalesReport()` | `get_monthly_sales_report` | ✅ Verified |
| ReportsPage | Supplier balances | `reportsApi.getSupplierBalances()` | `get_supplier_balances` | ✅ Verified |
| SettingsPage | Save Changes | ❌ No API call | ❌ No backend | 🔴 Broken |

## API → UI Mapping (Backend Endpoints Without UI Consumer)

| Backend Endpoint | Module | Has Frontend Consumer | Status |
|---|---|---|---|
| `get_warehouse_stock` | inventory | ❌ No | ⚠️ Orphan endpoint |
| `get_stock_movement` | inventory | ❌ No | ⚠️ Orphan endpoint |

## Frontend API Methods Without Active Callers

| API Method | Namespace | Status |
|---|---|---|
| `resourceApi.create()` | resourceApi | ⚠️ Defined but unused |
| `resourceApi.update()` | resourceApi | ⚠️ Defined but unused |
| `resourceApi.delete()` | resourceApi | ⚠️ Defined but unused |
| `resourceApi.count()` | resourceApi | ⚠️ Defined but unused |
| `inventoryApi.getWarehouseStock()` | inventoryApi | ⚠️ Defined but unused |

## Reconciliation Summary

| Metric | Count |
|---|---|
| Total UI → API verified mappings | 19 |
| UI actions with missing API (gaps) | 5 |
| Backend endpoints without UI consumer (orphans) | 2 |
| Frontend API methods defined but unused | 5 |
| Settings page broken mapping | 1 |

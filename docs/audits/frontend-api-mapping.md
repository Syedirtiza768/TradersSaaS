# Frontend API Mapping

## Title
Traders — Frontend API Call Inventory

## Purpose
All frontend API calls, their originating screens, HTTP methods, and target endpoints.

## Generated From
- `frontend/trader-ui/src/lib/api.ts`
- `frontend/trader-ui/src/pages/*.tsx`
- `frontend/trader-ui/src/stores/authStore.ts`

## Last Audit Basis
Full scan of all API namespaces and page-level call sites — 2026-05-17

---

## API Namespaces

### `companyApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

### `authApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

### `dashboardApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

### `salesApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

### `purchasesApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

### `inventoryApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

### `customersApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

### `reportsApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

### `auditApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

### `currencyApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

### `posApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

### `settingsApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

### `gstApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

### `bundlingApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

### `printApi`

| Method | HTTP | Endpoint | Parameters |
|---|---|---|---|

## Page → API Usage Map

| Page | Imported APIs | API Calls Made |
|---|---|---|
| LoginPage | authApi (via authStore) | `authApi.login()`, `authApi.getLoggedUser()` |
| DashboardPage | dashboardApi | `getKPIs()`, `getSalesTrend()`, `getTopCustomers()`, `getRecentOrders()` |
| SalesPage | resourceApi | `resourceApi.list({ doctype: 'Sales Invoice' })` |
| PurchasesPage | resourceApi | `resourceApi.list({ doctype: 'Purchase Invoice' })` |
| InventoryPage | inventoryApi | `getStockSummary()`, `getLowStockItems()` |
| CustomersPage | resourceApi | `resourceApi.list({ doctype: 'Customer' })` |
| SuppliersPage | resourceApi | `resourceApi.list({ doctype: 'Supplier' })` |
| FinancePage | reportsApi, dashboardApi | `getProfitAndLoss()`, `getCashFlowSummary()`, `getReceivableAgingSummary()`, `getAccountsPayable()` |
| ReportsPage | reportsApi | `getAccountsReceivable()`, `getAccountsPayable()`, `getMonthlySalesReport()`, `getSupplierBalances()` |
| SettingsPage | ❌ None | ❌ No API calls |

## API Methods Without Page Consumers

| Namespace | Method | Endpoint | Status |
|---|---|---|---|
| dashboardApi | `getSalesByItemGroup()` | `get_sales_by_item_group` | ⚠️ Defined but DashboardPage may not call it |
| inventoryApi | `getWarehouseStock()` | `get_warehouse_stock` | ⚠️ Not called from any page |
| resourceApi | `create()` | `POST /api/resource/{doctype}` | ⚠️ Defined but no page calls it |
| resourceApi | `update()` | `PUT /api/resource/{doctype}/{name}` | ⚠️ Defined but no page calls it |
| resourceApi | `delete()` | `DELETE /api/resource/{doctype}/{name}` | ⚠️ Defined but no page calls it |
| resourceApi | `count()` | `GET frappe.client.get_count` | ⚠️ Defined but no page calls it |

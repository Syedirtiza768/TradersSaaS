# Frontend Screen Inventory

## Title
Traders — Complete Frontend Screen Inventory

## Purpose
Every screen, route, layout, user actions, and current status in the Traders frontend application.

## Generated From
- `frontend/trader-ui/src/App.tsx`
- `frontend/trader-ui/src/pages/*.tsx`
- `frontend/trader-ui/src/layouts/*.tsx`

## Last Audit Basis
All route definitions and page components — 2026-05-16

---

## Route Inventory

| # | Path | Component | Guard | Layout | Status |
|---|---|---|---|---|---|
| 1 | `/login` | LoginPage | None | None | ✅ Active |
| 2 | `/` | DashboardPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 3 | `sales` | SalesPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 4 | `sales/new` | CreateSalesInvoicePage | ProtectedRoute | DashboardLayout | ✅ Active |
| 5 | `sales/returns/new` | CreateSalesReturnPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 6 | `sales/dispatches/new` | CreateSalesDispatchPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 7 | `sales/orders` | SalesOrdersPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 8 | `sales/orders/new` | CreateSalesOrderPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 9 | `sales/orders/:orderId` | SalesOrderDetailPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 10 | `sales/quotations` | QuotationsPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 11 | `sales/quotations/new` | CreateQuotationPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 12 | `sales/quotations/:quotationId` | QuotationDetailPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 13 | `sales/:invoiceId` | SalesInvoiceDetailPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 14 | `purchases` | PurchasesPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 15 | `purchases/new` | CreatePurchaseInvoicePage | ProtectedRoute | DashboardLayout | ✅ Active |
| 16 | `purchases/returns/new` | CreatePurchaseReturnPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 17 | `purchases/receipts/new` | CreatePurchaseReceiptPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 18 | `purchases/orders` | PurchaseOrdersPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 19 | `purchases/orders/new` | CreatePurchaseOrderPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 20 | `purchases/orders/:orderId` | PurchaseOrderDetailPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 21 | `purchases/requisitions` | PurchaseRequisitionsPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 22 | `purchases/requisitions/new` | CreatePurchaseRequisitionPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 23 | `purchases/requisitions/:reqId` | PurchaseRequisitionDetailPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 24 | `purchases/rfqs` | SupplierQuotationsPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 25 | `purchases/rfqs/new` | CreateSupplierQuotationPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 26 | `purchases/rfqs/:quotationId` | SupplierQuotationDetailPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 27 | `purchases/:invoiceId` | PurchaseInvoiceDetailPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 28 | `inventory` | InventoryPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 29 | `inventory/items/new` | CreateItemPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 30 | `inventory/items/:itemId` | InventoryItemDetailPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 31 | `inventory/bundles` | ItemBundlesPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 32 | `inventory/warehouse` | WarehouseStockPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 33 | `inventory/movements` | StockMovementPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 34 | `inventory/dispatches/new` | CreateSalesDispatchPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 35 | `customers` | CustomersPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 36 | `customers/new` | CreateCustomerPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 37 | `customers/:customerId` | CustomerDetailPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 38 | `customers/:customerId/edit` | EditCustomerPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 39 | `suppliers` | SuppliersPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 40 | `suppliers/new` | CreateSupplierPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 41 | `suppliers/:supplierId` | SupplierDetailPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 42 | `suppliers/:supplierId/edit` | EditSupplierPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 43 | `finance` | FinancePage | ProtectedRoute | DashboardLayout | ✅ Active |
| 44 | `finance/journals` | JournalEntriesPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 45 | `finance/journals/new` | CreateJournalEntryPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 46 | `finance/journals/:journalId` | JournalEntryDetailPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 47 | `finance/payments` | PaymentEntriesPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 48 | `finance/payments/new` | CreatePaymentEntryPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 49 | `finance/payments/:paymentId` | PaymentEntryDetailPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 50 | `operations` | OperationsPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 51 | `reports` | ReportsPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 52 | `settings` | SettingsPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 53 | `settings/gst` | GstSettingsPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 54 | `print` | DocumentPrintPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 55 | `*` | NotFoundPage | ProtectedRoute | None | ✅ Active |
| 56 | `/sales` | SalesPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 57 | `/purchases` | PurchasesPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 58 | `/inventory` | InventoryPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 59 | `/customers` | CustomersPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 60 | `/suppliers` | SuppliersPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 61 | `/finance` | FinancePage | ProtectedRoute | DashboardLayout | ✅ Active |
| 62 | `/reports` | ReportsPage | ProtectedRoute | DashboardLayout | ✅ Active |
| 63 | `/settings` | SettingsPage | ProtectedRoute | DashboardLayout | ✅ Active |

## Screen Details

### LoginPage (`/login`)
- **Purpose:** User authentication
- **Layout:** Standalone (no DashboardLayout)
- **Guard:** None (public)
- **Actions:** Login form submit, show/hide password
- **API Calls:** `authApi.login()`, `authApi.getLoggedUser()`
- **Status:** ✅ Fully functional

### DashboardPage (`/`)
- **Purpose:** Business overview with KPIs, charts, and recent activity
- **Layout:** DashboardLayout (Navbar + Sidebar)
- **Guard:** ProtectedRoute
- **Actions:** View-only (no mutations)
- **API Calls:** `dashboardApi.getKPIs()`, `dashboardApi.getSalesTrend()`, `dashboardApi.getTopCustomers()`, `dashboardApi.getRecentOrders()`
- **Status:** ✅ Fully functional

### SalesPage (`/sales`)
- **Purpose:** Sales invoice list with pagination
- **Layout:** DashboardLayout
- **Guard:** ProtectedRoute
- **Actions:** View list, paginate. Buttons: New Invoice ⚠️, Filter ⚠️, Export ⚠️
- **API Calls:** `resourceApi.list({ doctype: 'Sales Invoice' })`
- **Status:** ⚠️ Read-only — action buttons non-functional

### PurchasesPage (`/purchases`)
- **Purpose:** Purchase invoice list with pagination
- **Layout:** DashboardLayout
- **Guard:** ProtectedRoute
- **Actions:** View list, paginate. Buttons: New Purchase ⚠️, Filter ⚠️, Export ⚠️
- **API Calls:** `resourceApi.list({ doctype: 'Purchase Invoice' })`
- **Status:** ⚠️ Read-only — action buttons non-functional

### InventoryPage (`/inventory`)
- **Purpose:** Stock summary and low-stock alerts
- **Layout:** DashboardLayout
- **Guard:** ProtectedRoute
- **Actions:** View stock, switch tabs (All/Low), search items
- **API Calls:** `inventoryApi.getStockSummary()`, `inventoryApi.getLowStockItems()`
- **Status:** ✅ Functional (read-only by design)

### CustomersPage (`/customers`)
- **Purpose:** Customer list as card grid
- **Layout:** DashboardLayout
- **Guard:** ProtectedRoute
- **Actions:** View list, search, paginate. Button: Add Customer ⚠️
- **API Calls:** `resourceApi.list({ doctype: 'Customer' })`
- **Status:** ⚠️ Read-only — Add Customer button non-functional

### SuppliersPage (`/suppliers`)
- **Purpose:** Supplier list as table
- **Layout:** DashboardLayout
- **Guard:** ProtectedRoute
- **Actions:** View list, search, paginate. Button: Add Supplier ⚠️
- **API Calls:** `resourceApi.list({ doctype: 'Supplier' })`
- **Status:** ⚠️ Read-only — Add Supplier button non-functional

### FinancePage (`/finance`)
- **Purpose:** Financial overview with P&L, cash flow, aging analysis
- **Layout:** DashboardLayout
- **Guard:** ProtectedRoute
- **Actions:** View-only
- **API Calls:** `reportsApi.getProfitAndLoss()`, `dashboardApi.getCashFlowSummary()`, `reportsApi.getReceivableAgingSummary()`, `reportsApi.getAccountsPayable()`
- **Status:** ✅ Fully functional (read-only)

### ReportsPage (`/reports`)
- **Purpose:** Multi-report viewer with report selector
- **Layout:** DashboardLayout
- **Guard:** ProtectedRoute
- **Actions:** Switch reports, view data. Button: Export ⚠️
- **API Calls:** `reportsApi.getAccountsReceivable()`, `reportsApi.getAccountsPayable()`, `reportsApi.getMonthlySalesReport()`, `reportsApi.getSupplierBalances()`
- **Status:** ✅ Functional (export not implemented)

### SettingsPage (`/settings`)
- **Purpose:** System configuration forms
- **Layout:** DashboardLayout
- **Guard:** ProtectedRoute
- **Actions:** Edit form fields, switch sections, Save Changes ⚠️
- **API Calls:** ❌ None — no backend persistence
- **Status:** ⚠️ UI-only — Save button non-functional

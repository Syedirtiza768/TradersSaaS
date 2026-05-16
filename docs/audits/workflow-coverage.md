# Workflow Coverage

## Title
Traders — Workflow Completeness Audit

## Purpose
Tracks the completeness of business workflows across UI, API, and database layers.

## Generated From
Workflow scanner analysis of all backend endpoints, frontend pages, and demo generators.

## Last Audit Basis
Full workflow pattern analysis — 2026-05-16

---

## Workflow Coverage Matrix

| # | Workflow | Module | UI Coverage | API Coverage | DB Coverage | Completeness |
|---|---|---|---|---|---|---|
| 1 | Sales Workflow | Sales | SalesPage, DashboardPage | 3 endpoints | ✅ | 40% — Partial — read-only workflow, no create/submit/cancel from UI |
| 2 | Purchase Workflow | Purchases | PurchasesPage, DashboardPage | 2 endpoints | ✅ | 50% — Partial — read-only workflow, no create/submit from UI |
| 3 | Inventory Workflow | Inventory | InventoryPage, DashboardPage | 4 endpoints | ✅ | 83% — Mostly complete — viewing works, stock movement UI missing |
| 4 | Payment Workflow | Finance | FinancePage, DashboardPage | 2 endpoints | ✅ | 75% — Partial — viewing works, no payment creation from UI |
| 5 | Reporting Workflow | Reports | ReportsPage, FinancePage | 6 endpoints | ✅ | 100% — Complete — all report endpoints have UI consumers |
| 6 | Customer Management | CRM | CustomersPage | 1 endpoints | ✅ | 33% — Partial — list only, no create/edit/detail views |
| 7 | Supplier Management | CRM | SuppliersPage | 1 endpoints | ✅ | 50% — Partial — list only, no create/edit views |
| 8 | Scheduled Tasks | System | — | 0 endpoints | ✅ | 0% — Unknown |
| 9 | Document Events | System | — | 0 endpoints | ✅ | 0% — Unknown |

## Detailed Workflow Steps

### Sales Workflow

| Step | Actor | Endpoint | Status |
|---|---|---|---|
| Sales Order Created | User (Frontend) | resourceApi.create (Sales Order) | ⚠️ Inferred — no create UI exists |
| Sales Invoice Created | User (Frontend) | resourceApi.list (Sales Invoice) — read only | ⚠️ No create action in UI |
| Sales Invoice Submitted | Backend (docstatus=1) | Frappe workflow | ✅ Verified — queried with docstatus=1 |
| Payment Received | User / Backend | Payment Entry | ✅ Verified — cash flow API |
| Delivery Note Created | Backend / Demo | Demo generator only | ⚠️ No frontend management |

### Purchase Workflow

| Step | Actor | Endpoint | Status |
|---|---|---|---|
| Purchase Invoice Created | User (Frontend) | resourceApi.list (Purchase Invoice) — read only | ⚠️ No create action in UI |
| Purchase Invoice Submitted | Backend (docstatus=1) | Frappe workflow | ✅ Verified — queried with docstatus=1 |
| Purchase Receipt Created | Backend / Demo | Demo generator only | ⚠️ No frontend management |
| Payment Made | User / Backend | Payment Entry | ✅ Verified — cash flow API (outflow) |

### Inventory Workflow

| Step | Actor | Endpoint | Status |
|---|---|---|---|
| Stock Entry (Initial) | Demo generator | InventoryGenerator | ✅ Verified — demo seeding |
| Stock Updated via Purchase | Backend | Purchase Receipt → Bin | ✅ Verified — ERPNext automatic |
| Stock Reduced via Sale | Backend | Delivery Note → Bin | ✅ Verified — ERPNext automatic |
| Stock Summary Viewed | User (Frontend) | inventoryApi.getStockSummary() | ✅ Verified |
| Low Stock Alerts Viewed | User (Frontend) | inventoryApi.getLowStockItems() | ✅ Verified |
| Stock Movement History | User (Frontend) | get_stock_movement() | ⚠️ Backend exists, no UI |

### Payment Workflow

| Step | Actor | Endpoint | Status |
|---|---|---|---|
| Payment Entry Created | Demo / Backend | PaymentGenerator | ⚠️ No create from UI |
| Cash Inflow Tracked | Backend | get_cash_flow_summary() — Receive type | ✅ Verified |
| Cash Outflow Tracked | Backend | get_cash_flow_summary() — Pay type | ✅ Verified |
| Invoice Reconciliation | Backend (ERPNext) | outstanding_amount updates | ✅ Verified — reflected in reports |

### Reporting Workflow

| Step | Actor | Endpoint | Status |
|---|---|---|---|
| Accounts Receivable Report | User (Frontend) | reportsApi.getAccountsReceivable() | ✅ Verified |
| Accounts Payable Report | User (Frontend) | reportsApi.getAccountsPayable() | ✅ Verified |
| Profit & Loss Report | User (Frontend) | reportsApi.getProfitAndLoss() | ✅ Verified |
| Monthly Sales Report | User (Frontend) | reportsApi.getMonthlySalesReport() | ✅ Verified |
| Supplier Balances Report | User (Frontend) | reportsApi.getSupplierBalances() | ✅ Verified |
| Receivable Aging Summary | User (Frontend) | reportsApi.getReceivableAgingSummary() | ✅ Verified |

### Customer Management

| Step | Actor | Endpoint | Status |
|---|---|---|---|
| Customer List Viewed | User (Frontend) | resourceApi.list({ doctype: "Customer" }) | ✅ Verified |
| Customer Created | User (Frontend) | "Add Customer" button | ⚠️ Button exists, no handler |
| Customer Details Viewed | User (Frontend) | resourceApi.get("Customer", name) | ⚠️ Inferred — card is clickable but no detail view |

### Supplier Management

| Step | Actor | Endpoint | Status |
|---|---|---|---|
| Supplier List Viewed | User (Frontend) | resourceApi.list({ doctype: "Supplier" }) | ✅ Verified |
| Supplier Created | User (Frontend) | "Add Supplier" button | ⚠️ Button exists, no handler |

### Scheduled Tasks

| Step | Actor | Endpoint | Status |
|---|---|---|---|
| Scheduled tasks defined in hooks | System | hooks.py | 🔍 Needs review |

### Document Events

| Step | Actor | Endpoint | Status |
|---|---|---|---|
| Doc events defined in hooks | System | hooks.py | 🔍 Needs review |


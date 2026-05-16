# Dead Path Audit

## Title
Traders — Dead Routes, Endpoints, Components, and Orphan Services

## Purpose
Identifies dead or unreachable code paths across the entire application stack.

## Generated From
Cross-referencing all route, navigation, API, and endpoint inventories.

## Last Audit Basis
Full bidirectional reconciliation — 2026-05-16

---

## Dead / Orphan Backend Endpoints

| # | Endpoint | Module | Reason | Severity |
|---|---|---|---|---|
| 1 | `get_warehouse_stock(warehouse)` | inventory.py | No frontend consumer — not called from any page or API namespace method | ⚠️ Medium |
| 2 | `get_stock_movement(...)` | inventory.py | No frontend consumer — defined in backend but `inventoryApi` does not expose it | ⚠️ Medium |

## Dead / Orphan Frontend API Methods

| # | Method | Namespace | Reason | Severity |
|---|---|---|---|---|
| 1 | `resourceApi.create()` | resourceApi | Defined in api.ts but no page calls it | ⚠️ Low (ready for future use) |
| 2 | `resourceApi.update()` | resourceApi | Defined in api.ts but no page calls it | ⚠️ Low |
| 3 | `resourceApi.delete()` | resourceApi | Defined in api.ts but no page calls it | ⚠️ Low |
| 4 | `resourceApi.count()` | resourceApi | Defined in api.ts but no page calls it | ⚠️ Low |
| 5 | `inventoryApi.getWarehouseStock()` | inventoryApi | Defined but no page imports or calls it | ⚠️ Medium |

## Non-Functional UI Elements (Dead Buttons)

| # | Screen | Element | Reason | Severity |
|---|---|---|---|---|
| 1 | SalesPage | "New Invoice" button | No onClick handler | ⚠️ High |
| 2 | SalesPage | "Filter" button | No onClick handler | ⚠️ Medium |
| 3 | SalesPage | "Export" button | No onClick handler | ⚠️ Medium |
| 4 | PurchasesPage | "New Purchase" button | No onClick handler | ⚠️ High |
| 5 | PurchasesPage | "Filter" button | No onClick handler | ⚠️ Medium |
| 6 | PurchasesPage | "Export" button | No onClick handler | ⚠️ Medium |
| 7 | CustomersPage | "Add Customer" button | No onClick handler | ⚠️ High |
| 8 | SuppliersPage | "Add Supplier" button | No onClick handler | ⚠️ High |
| 9 | ReportsPage | "Export" button | No onClick handler | ⚠️ Medium |
| 10 | SettingsPage | "Save Changes" button | No onClick handler, no API | 🔴 Critical |
| 11 | Navbar | Search input | No handler | ⚠️ Low |
| 12 | Navbar | Notifications bell | No handler, red dot is misleading | ⚠️ Low |

## Dead Routes

None detected. All routes point to existing components.

## Orphan Components

None detected. All components in `components/` are imported by layouts or pages.

## Summary

| Category | Count |
|---|---|
| Orphan backend endpoints | 2 |
| Orphan frontend API methods | 5 |
| Non-functional UI buttons | 12 |
| Dead routes | 0 |
| Orphan components | 0 |

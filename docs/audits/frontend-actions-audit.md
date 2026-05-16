# Frontend Actions Audit

## Title
Traders — Frontend User Actions Inventory

## Purpose
All forms, buttons, handlers, mutations, and interactive elements across the frontend.

## Generated From
All page components in `frontend/trader-ui/src/pages/*.tsx`

## Last Audit Basis
Full scan of all page component JSX and event handlers — 2026-05-16

---

## Action Inventory

### Functional Actions (✅ Implemented)

| # | Screen | Action | Type | Handler | API Call | Status |
|---|---|---|---|---|---|---|
| 1 | LoginPage | Login form submit | Form | `handleSubmit` | `authApi.login()` | ✅ |
| 2 | LoginPage | Show/hide password | Toggle | `setShowPassword` | — | ✅ |
| 3 | Navbar | Logout | Button | `handleLogout` | `authApi.logout()` | ✅ |
| 4 | SalesPage | Paginate | Button | `setPage` | `resourceApi.list` | ✅ |
| 5 | PurchasesPage | Paginate | Button | `setPage` | `resourceApi.list` | ✅ |
| 6 | InventoryPage | Switch tab (All/Low) | Tab | `setActiveTab` | — (client filter) | ✅ |
| 7 | InventoryPage | Search items | Input | `setSearch` | — (client filter) | ✅ |
| 8 | CustomersPage | Search customers | Input | `setSearch` | — (client filter) | ✅ |
| 9 | CustomersPage | Paginate | Button | `setPage` | `resourceApi.list` | ✅ |
| 10 | SuppliersPage | Search suppliers | Input | `setSearch` | — (client filter) | ✅ |
| 11 | SuppliersPage | Paginate | Button | `setPage` | `resourceApi.list` | ✅ |
| 12 | ReportsPage | Switch report type | Button | `setActiveReport` | various report APIs | ✅ |
| 13 | SettingsPage | Switch settings section | Button | `setActiveSection` | — | ✅ |

### Non-Functional Actions (⚠️ No Handler / Placeholder)

| # | Screen | Action | Type | Handler | Expected API | Status |
|---|---|---|---|---|---|---|
| 14 | SalesPage | New Invoice | Button | ❌ None | `resourceApi.create` | ⚠️ Placeholder |
| 15 | SalesPage | Filter | Button | ❌ None | Client-side filter | ⚠️ Placeholder |
| 16 | SalesPage | Export | Button | ❌ None | CSV/Excel generation | ⚠️ Placeholder |
| 17 | PurchasesPage | New Purchase | Button | ❌ None | `resourceApi.create` | ⚠️ Placeholder |
| 18 | PurchasesPage | Filter | Button | ❌ None | Client-side filter | ⚠️ Placeholder |
| 19 | PurchasesPage | Export | Button | ❌ None | CSV/Excel generation | ⚠️ Placeholder |
| 20 | CustomersPage | Add Customer | Button | ❌ None | `resourceApi.create` | ⚠️ Placeholder |
| 21 | SuppliersPage | Add Supplier | Button | ❌ None | `resourceApi.create` | ⚠️ Placeholder |
| 22 | ReportsPage | Export | Button | ❌ None | CSV/Excel generation | ⚠️ Placeholder |
| 23 | SettingsPage | Save Changes | Button | ❌ None | Settings API | ⚠️ Placeholder |
| 24 | Navbar | Search input | Input | ❌ None | Search API | ⚠️ Placeholder |
| 25 | Navbar | Notifications bell | Button | ❌ None | Notifications API | ⚠️ Placeholder |

## Summary

| Category | Count |
|---|---|
| Fully functional actions | 13 |
| Non-functional / placeholder actions | 12 |
| **Total actions** | **25** |
| **Implementation rate** | **52%** |

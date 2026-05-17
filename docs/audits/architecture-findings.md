# Architecture Findings

## Title
Traders — Architecture Audit Findings and Risk Register

## Purpose
Central register of all architectural issues, gaps, risks, and their resolution status.

## Generated From
Full architecture audit reconciliation of all layers.

## Last Audit Basis
Complete audit — 2026-05-17

---

## Current Critical Issues

| ID | Finding | Module | Description | Status |
|---|---|---|---|---|
| FIND-01 | Settings page has no backend | Settings | Save Changes button has no handler; no API calls; changes lost on refresh | 🔴 New |

## Current High Issues

| ID | Finding | Module | Description | Status |
|---|---|---|---|---|
| FIND-02 | Create actions non-functional | Sales | "New Invoice" button rendered but no onClick handler or create modal | 🔴 New |
| FIND-03 | Create actions non-functional | Purchases | "New Purchase" button rendered but no onClick handler or create modal | 🔴 New |
| FIND-04 | Create actions non-functional | Customers | "Add Customer" button rendered but no onClick handler or create modal | 🔴 New |
| FIND-05 | Create actions non-functional | Suppliers | "Add Supplier" button rendered but no onClick handler or create modal | 🔴 New |
| FIND-06 | No role-based UI visibility | Permissions | Trader roles defined in fixtures but sidebar shows all items to all users | 🔴 New |

## Current Medium Issues

| ID | Finding | Module | Description | Status |
|---|---|---|---|---|
| FIND-07 | Orphan backend endpoints | Inventory | `get_warehouse_stock` and `get_stock_movement` not called from frontend | ⚠️ New |
| FIND-08 | Filter/Export buttons | Sales, Purchases | Filter and Export buttons have no implementation | ⚠️ New |
| FIND-09 | Sales Orders read-only | Sales | Sales Orders queried for dashboard but not manageable from UI | ⚠️ New |
| FIND-10 | Delivery/Receipt not exposed | Inventory | Created by demo but no frontend screens | ⚠️ New |
| FIND-11 | Global search non-functional | Navbar | Search input has no handler | ⚠️ New |

## Current Low Issues

| ID | Finding | Module | Description | Status |
|---|---|---|---|---|
| FIND-12 | `_get_default_company` duplication | Backend | Same helper duplicated in 3 API modules | 🔵 New |
| FIND-13 | Notification bell misleading | Navbar | Red dot indicator but no notification system | 🔵 New |
| FIND-14 | Commented-out code in hooks.py | Backend | Multiple inactive config sections | 🔵 New |
| FIND-15 | Export buttons non-functional | Reports | Export button in Reports page has no handler | 🔵 New |
| FIND-16 | CRUD API methods unused | Frontend | resourceApi.create/update/delete/count defined but never called | 🔵 New |

## Recently Resolved Issues

None — this is the initial audit baseline.

## Needs Manual Verification

| ID | Item | Reason |
|---|---|---|
| MV-01 | DashboardPage `getSalesByItemGroup()` call | Code exists but may be conditional — verify at runtime |
| MV-02 | Frappe DocType permissions | Role-based access via Frappe resource API depends on server-side config — cannot verify from code scan alone |
| MV-03 | CSRF token handling | Cookie parsing implementation — verify in deployed environment |

## Release Blockers

Based on the audit policy, the following are release-blocking:

| Finding | Reason | Waivable? |
|---|---|---|
| FIND-01 (Settings no backend) | User-visible broken functionality | Yes, if Settings marked as "Coming Soon" |
| FIND-06 (No role-based visibility) | Permission mismatch between visible UI and backend guards | Yes, if all users are admins in current deployment |

## Summary Statistics

| Severity | Count |
|---|---|
| 🔴 Critical | 1 |
| 🔴 High | 5 |
| ⚠️ Medium | 5 |
| 🔵 Low | 5 |
| **Total** | **16** |
| Needs Manual Verification | 3 |
| Release Blockers | 2 |

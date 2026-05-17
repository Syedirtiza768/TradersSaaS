# Module Coverage Matrix

## Title
Traders — Module Implementation Completeness

## Purpose
Snapshot of each business module's implementation status across all architectural layers.

## Generated From
Combined analysis of all scanner outputs.

## Last Audit Basis
Full architecture audit — 2026-05-17

---

## Coverage Matrix

| Module | Nav | Route | Screen | Actions | Frontend API | Backend API | DB Access | Workflow | Overall |
|---|---|---|---|---|---|---|---|---|---|
| **Dashboard** | ✅ | ✅ | ✅ | ✅ View | ✅ 6 calls | ✅ 6 endpoints | ✅ 7 tables | ✅ Read | 🟢 95% |
| **Sales** | ✅ | ✅ | ✅ | ⚠️ Read-only | ✅ 1 call | ✅ (resource) | ✅ SI table | ⚠️ Partial | 🟡 60% |
| **Purchases** | ✅ | ✅ | ✅ | ⚠️ Read-only | ✅ 1 call | ✅ (resource) | ✅ PI table | ⚠️ Partial | 🟡 60% |
| **Inventory** | ✅ | ✅ | ✅ | ✅ View+Search | ✅ 2 calls | ✅ 4 endpoints | ✅ 4 tables | ✅ Read | 🟢 85% |
| **Customers** | ✅ | ✅ | ✅ | ⚠️ Read-only | ✅ 1 call | ✅ (resource) | ✅ Customer | ⚠️ Partial | 🟡 55% |
| **Suppliers** | ✅ | ✅ | ✅ | ⚠️ Read-only | ✅ 1 call | ✅ (resource) | ✅ Supplier | ⚠️ Partial | 🟡 55% |
| **Finance** | ✅ | ✅ | ✅ | ✅ View | ✅ 4 calls | ✅ 4 endpoints | ✅ 5 tables | ✅ Read | 🟢 90% |
| **Reports** | ✅ | ✅ | ✅ | ✅ View+Switch | ✅ 4 calls | ✅ 4 endpoints | ✅ 2 tables | ✅ Read | 🟢 90% |
| **Settings** | ✅ | ✅ | ✅ | 🔴 Broken | ❌ 0 calls | ❌ None | ❌ None | ❌ None | 🔴 25% |
| **Auth** | — | ✅ | ✅ | ✅ Login/Logout | ✅ 3 calls | ✅ (Frappe) | ✅ Session | ✅ Full | 🟢 100% |

## Legend

| Symbol | Meaning |
|---|---|
| 🟢 | 80%+ complete — functional for primary use cases |
| 🟡 | 50-79% — core viewing works, write operations missing |
| 🔴 | <50% — significant functionality gaps |

## Module Risk Assessment

| Module | Risk Level | Primary Gap |
|---|---|---|
| Settings | 🔴 High | No backend persistence — user-visible broken functionality |
| Sales | 🟡 Medium | No create/edit/submit workflow from UI |
| Purchases | 🟡 Medium | No create/edit/submit workflow from UI |
| Customers | 🟡 Medium | No create/edit from UI |
| Suppliers | 🟡 Medium | No create/edit from UI |
| Inventory | 🟢 Low | Stock movement history not exposed in UI |
| Dashboard | 🟢 None | Fully functional read-only dashboard |
| Finance | 🟢 None | Fully functional read-only finance view |
| Reports | 🟢 None | Export not implemented (minor) |

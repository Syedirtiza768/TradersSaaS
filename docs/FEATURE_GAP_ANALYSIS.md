# Feature Gap Analysis Report

**Application:** Traders (Frappe 15 + ERPNext 15 + React SPA `trader-ui`)  
**Repository:** `f:\apps\traders`  
**Audit date:** 2026-05-17  
**Method:** Evidence from source code, API modules, React routes, hooks, and existing architecture docs. No feature marked implemented without corroborating paths.

---

## 1. Executive Summary

### Overall maturity

The application is a **custom React front end** on top of **ERPNext’s full ERP data model**, with a focused `trader_app` API layer (~15 whitelisted modules) and **59 routed SPA pages**. Core **read and create/submit workflows** for sales, purchases, inventory, finance, and **22+ analytics reports** are in place—materially ahead of an earlier May 2026 audit that described the UI as read-only.

It is **not production-ready** for the full ERP checklist in this audit, especially:

- DBA / multi-company operations from one UI  
- Serial numbers with model/warehouse validation  
- Customer + item-specific invoice price history  
- POS / barcode counter sales  
- Manufacturing / production  
- Trial balance / balance sheet in the SPA  
- Multi-currency beyond company default  

### Strongest areas

| Area | Why |
|------|-----|
| **Sales & purchase document flows** | Create/list/detail/submit for quotations, orders, invoices, returns, challans, requisitions, RFQs (`App.tsx`, `sales.py`, `purchases.py`) |
| **Finance payments & journals** | Payment Entry and Journal Entry APIs + UI (`finance.py`, finance routes) |
| **Inventory & warehouses** | Stock balance, ledger, transfers, warehouse stock page (`inventory.py`, `WarehouseStockPage.tsx`, `StockMovementPage.tsx`) |
| **Reporting** | Rich `reportDefinitions.ts` backed by `reports.py` with CSV export |
| **Auth & roles** | Frappe session auth + Trader roles + client capability map (`authStore.ts`, `permissions.ts`, `settings.get_current_user_roles`) |
| **Tax invoice variants** | Custom `trader_invoice_type` fields (`custom_fields.py`, `invoiceTypes.ts`) |

### Weakest areas

| Area | Why |
|------|-----|
| **Serial / barcode / POS** | No implementation in `trader_app` or SPA |
| **DBA multi-company UX** | Single default company everywhere |
| **Invoice-time pricing history** | Not on create invoice screen |
| **Formal financial statements** | No TB/BS in report registry |
| **Production** | No Work Order/BOM exposure |

### Business-critical missing features

See [CRITICAL_GAPS_ACTION_PLAN.md](./CRITICAL_GAPS_ACTION_PLAN.md).

### Production readiness

**Conditional no** for the full checklist. **Conditional yes** for single-company distribution/trading with standard SI/PI, warehouses, GST-style tax, payments, and analytics—after UAT on stock submission path (default `update_stock=0` on invoice create) and permission review.

---

## 2. Technology & Architecture Overview

| Layer | Technology | Evidence |
|-------|------------|----------|
| **Frontend** | React 18, TypeScript, Vite 5, Tailwind, Zustand, React Router 6 | `frontend/trader-ui/package.json`, `App.tsx` |
| **Backend** | Frappe 15, Python 3.11, `trader_app` custom app | `apps/trader_app/`, `hooks.py` |
| **ERP core** | ERPNext 15 DocTypes (SI, PI, Item, Warehouse, GL Entry, etc.) | Used via `frappe.get_doc`, SQL on `tab*` tables |
| **Database** | MariaDB 10.11 | `compose/docker-compose.yml` |
| **Cache/queue** | Redis 7 | Compose services |
| **Auth** | Frappe session cookie + CSRF header | `api.ts`, `LoginPage.tsx` |
| **API style** | RPC: `/api/method/trader_app.api.*` | `docs/API_REFERENCE.md`, `api/*.py` |
| **Reporting** | Custom SQL in `reports.py` + client charts (Recharts) | `reportDefinitions.ts`, `ReportView.tsx` |
| **Export** | Client CSV (`toCsv`); print HTML via `printing.py` | `ReportView.tsx`, `DocumentPrintPage.tsx` |
| **Deploy** | Docker Compose + nginx proxy | `compose/`, `infra/nginx/proxy.conf` |
| **Backup** | Shell script | `scripts/backup.sh` |

### Custom vs standard data model

- **Custom DocTypes:** `Item Bundle`, `Item Bundle Detail`, `Migration Job` (`trader/doctype/`)  
- **Custom fields:** `trader_invoice_type` on SI, PI, Quotation, Delivery Note (`custom_fields.py`)  
- **Everything else:** Standard ERPNext tables (`tabSales Invoice`, `tabBin`, `tabGL Entry`, …)

---

## 3. Feature Coverage Matrix

The full line-by-line checklist is maintained in:

**[FEATURE_COVERAGE_MATRIX.md](./FEATURE_COVERAGE_MATRIX.md)**

### Summary counts (matrix rows)

| Status | Count | % |
|--------|------:|--:|
| **Implemented** | 108 | 40% |
| **Partially Implemented** | 82 | 30% |
| **Missing** | 80 | 29% |
| **Not Production-Ready** | 2 | 1% |
| **Unclear / Needs Verification** | 1 | <1% |
| **Total features reviewed** | **273** | 100% |

---

## 4. Module-by-Module Analysis

### 4.1 User & Company Management

**What exists**

- Login/logout and session bootstrap (`LoginPage.tsx`, `authStore.ts`)  
- Trader roles in fixtures (`hooks.py` L35–44)  
- Role list and UI preferences (`settings.py`, `SettingsPage.tsx`)  
- Read-only company block in settings (`settings.py` `_payload()`, `SettingsPage.tsx`)  
- Fiscal year created in demo (`demo/generators/company.py` L121–134)

**What is missing**

- Company CRUD and logo in SPA  
- Company switcher  
- Company-scoped permissions  
- License module  

**Evidence**

```761:767:apps/trader_app/trader_app/api/sales.py
def _default_company():
    companies = frappe.get_all("Company", limit=1, pluck="name")
    return (
        frappe.defaults.get_user_default("Company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
        or (companies[0] if companies else None)
    )
```

**Required changes**

| Layer | Change |
|-------|--------|
| DB | Use existing `tabCompany`; optional `trader_company_settings` for branding |
| API | `list_companies`, `set_user_default_company`, `update_company_profile` |
| Frontend | Company selector in navbar; settings edit form |
| Testing | User A default company A; user B company B; no cross-company list leakage |

---

### 4.2 DBA / Shared Resource Multi-Company

**What exists**

- ERPNext naturally shares **Customer**, **Supplier**, **Item** across companies  
- **Warehouse** and all subledgers are **company-specific** (`inventory.py` L32–33: `w.company = %(company)s`)  
- Transaction tables include `company` column; APIs filter when parameter supplied  

**What is missing**

- Configurable shared vs company-specific masters  
- Shared warehouse across companies  
- Consolidated reports  
- UI to operate multiple companies  
- Company-aware permission queries  

**Leakage risk**

- APIs always filter by `_default_company()`, not by user’s allowed companies—if a second company is added in desk, SPA still shows only default unless extended.  
- Permission hooks do **not** include `company` clause (`permissions.py`).

**Required implementation**

1. `User Permission` or custom `allowed_companies` on session boot.  
2. Mandatory `company` on every API call from UI.  
3. Consolidated SQL: `company IN %(companies)s` with group by company.  
4. Optional `trader_shared_resource` settings DocType for DBA policy.

---

### 4.3 Multi-Currency

**What exists**

- `currency` on invoice list responses (`sales.py` L103)  
- Company `default_currency` in settings payload  

**What is missing**

- Exchange rate maintenance UI/API in trader_app  
- Foreign currency on create documents  
- Gain/loss posting and currency-wise reports  

**Mark:** **Partial** — fields exist; business logic not exposed.

---

### 4.4 Accounting

**What exists**

- Journal Entry: `create_journal_entry`, pages under `/finance/journals`  
- Payment Entry: full create + invoice allocation (`finance.py`, `CreatePaymentEntryPage.tsx`)  
- Auto GL on ERPNext submit for SI/PI/PE  
- P&L summary, GL, cashflow, tax summary, AR/AP aging in reports  
- Bank/cash settlement accounts auto-provisioned (`_ensure_company_bank_accounts`)

**What is missing**

- Trial balance & balance sheet in SPA  
- Bank account **on sales invoice** (only on payment)  
- Currency gain/loss  
- Dedicated cashbook (cashflow is adjacent)

**Auto voucher evidence**

Hooks only log realtime events on submit (`sales.py` `on_sales_invoice_submit`); GL is ERPNext core on `doc.submit()`.

---

### 4.5 Inventory

**What exists**

- Item CRUD (`create_item`, `CreateItemPage.tsx`)  
- Stock balance, ledger, low stock, reorder report  
- Stock Entry: receipt, issue, transfer (`inventory.py`)  
- Item bundles (`bundling.py`, `ItemBundlesPage.tsx`)  
- Demo barcodes in seed only (`items.py` L198–214)

**What is missing**

- Serial/batch tracking in API/UI  
- Model number custom field  
- Item images in SPA  
- Strong negative-stock enforcement in custom create paths  

**Invoice stock note**

```327:355:apps/trader_app/trader_app/api/sales.py
def create_sales_invoice(..., update_stock=0, ...):
    ...
    si.update_stock = cint(update_stock)
```

Default **does not** update stock on invoice—stock expected via Delivery Note workflow; operators must understand this.

---

### 4.6 Multi-Warehouse

**What exists**

- `get_warehouses`, `get_stock_balance` with `warehouse` filter  
- `WarehouseStockPage.tsx`, `StockMovementPage.tsx`  
- Material Transfer in `create_stock_entry`  
- Demo: Main / Secondary / Retail warehouses  

**Gaps**

- Sales/purchase **create UIs** do not expose per-line warehouse (backend supports `warehouse` key on items)  
- No user-warehouse permission  
- No validation UI before save for insufficient bin qty  

---

### 4.7 Purchasing

**What exists**

- Material Request (requisition), Supplier Quotation (RFQ), PO, PI, returns, receipt  
- Submit/cancel APIs mirroring sales  
- Purchase reports (scorecard, variance, open PO, returns, item purchases)  

**Gaps**

- Inward gate pass (no DocType)  
- Landed cost  
- Serial on receipt  
- PO approval UI (workflow fixtures exist; not surfaced in SPA)

---

### 4.8 Sales & Invoicing

**What exists**

- Full document chain: Quotation → SO → SI; Delivery Challan; returns  
- Multiple invoice types (tax, commercial, non-GST, bill of supply, credit note)  
- Print pipeline (`printing.py`, `DocumentPrintPage.tsx`)  
- Tax inclusive/exclusive on create (`CreateSalesInvoicePage.tsx` L271–294)  

**Gaps**

- Discount fields on create form  
- Customer-specific pricing  
- Warehouse/currency/bank on invoice form  
- **Last 4–5 customer+item transactions** (critical)  
- Outward gate pass naming (challan only)

**Customer transactions (not sufficient for IH requirement)**

```101:126:apps/trader_app/trader_app/api/customers.py
def get_customer_transactions(customer, company=None, page=1, page_size=20):
    ...
    SELECT name, posting_date, grand_total, outstanding_amount, ...
    FROM `tabSales Invoice`
```

No `item_code` filter; used on `CustomerDetailPage.tsx` (8 rows), not on invoice screen.

---

### 4.9 Barcode, Serial Number & POS

**Status:** **Missing** in `trader_app` and React UI.

- Demo generates EAN-13 barcodes on items only.  
- `create_item` does not accept barcodes.  
- No POS route in `App.tsx`.  
- No `Serial No` validation anywhere in custom API.

ERPNext desk can handle serials if enabled; **Trader SPA does not integrate them.**

---

### 4.10 Production & Assembly

**Status:** **Missing** (manufacturing).

- `Item Bundle` + `bundling.py` = sellable kit definition, not production order.  
- No Work Order, BOM, job costing APIs or pages.

---

### 4.11 Reports

**What exists**

- 22 report definitions in UI (`reportDefinitions.ts`)  
- Additional endpoints in `reports.py` (e.g. `get_sales_report`) not all wired to SPA  
- Filters: dates, warehouse text, customer/supplier text  
- Export: CSV per report (`ReportView.tsx` L59–64)  
- Company filter in SQL when `company` passed (defaults if omitted)

**Gaps**

- Trial balance, balance sheet, daily affairs, serial report, warranty report  
- Consolidated multi-company  
- PDF export for reports (print exists for documents only)  
- Company picker on report filters  

---

### 4.12 Backup / Export / Data Safety

| Capability | Status | Evidence |
|------------|--------|----------|
| DB backup script | Partial | `scripts/backup.sh` |
| Restore | Unclear | Not in repo |
| Report CSV export | Implemented | `ReportView.tsx` |
| Invoice print | Implemented | `printing.py` |
| Audit log UI | Missing | ERPNext desk only |
| Soft delete | Partial | Customer/supplier disable APIs |

---

### 4.13 Security / Permissions

**What exists**

- Frappe authentication  
- Trader roles + `get_current_user_roles`  
- Client capabilities (`permissions.ts`) hide nav items  
- `permission_query_conditions` on SI/PI (`hooks.py` L104–112)  
- Owner-based restriction for non-managers (`permissions.py` L21–22)

**Gaps**

- No company in permission SQL  
- No warehouse restrictions  
- Many DocTypes rely on ERPNext default permissions only  
- No dedicated audit/activity view in SPA  

---

## 5. Critical Business Gaps

Detailed in [CRITICAL_GAPS_ACTION_PLAN.md](./CRITICAL_GAPS_ACTION_PLAN.md). Top items:

1. Customer + item/model last-4–5 transactions on invoice  
2. Serial validation (especially wrong model)  
3. DBA / multi-company UI and isolation  
4. Bank account on sales invoice  
5. Warehouse on sales with stock validation  
6. Multi-currency + FX gain/loss  
7. Trial balance & balance sheet  
8. POS / barcode  
9. Production (if in scope)  
10. Company-wise permissions  

---

## 6. Database Gap Analysis

| Required Entity/Table | Exists? | Current Table/Model | Missing Columns / Notes |
|----------------------|---------|---------------------|-------------------------|
| companies | Yes | `tabCompany` | — |
| users | Yes | `tabUser` | — |
| roles | Yes | `tabRole` | Trader roles in fixtures |
| permissions | Yes | `tabDocPerm`, Custom hooks | Not company-scoped in trader hooks |
| company_users | Partial | `tabUser Permission` (ERPNext) | Not used in trader_app |
| currencies | Yes | `tabCurrency` | — |
| exchange_rates | Yes | `tabCurrency Exchange` | Not exposed in API |
| chart_of_accounts | Yes | `tabAccount` | Per company |
| vouchers | Yes | SI, PI, JE, PE | — |
| voucher_lines | Yes | Child tables `* Item`, JE Account | — |
| customers | Yes | `tabCustomer` | Global (no company) |
| vendors | Yes | `tabSupplier` | Global |
| items | Yes | `tabItem` | Global; no trader model_no field |
| item_models | No | — | Use Item or custom field |
| warehouses | Yes | `tabWarehouse` | `company` required |
| stock_ledger | Yes | `tabStock Ledger Entry` | — |
| stock_balances | Yes | `tabBin` | Per item+warehouse |
| serial_numbers | Yes (ERPNext) | `tabSerial No` | Unused by trader_app |
| purchase_orders | Yes | `tabPurchase Order` | — |
| purchases | Yes | `tabPurchase Invoice` | — |
| sale_orders | Yes | `tabSales Order` | — |
| sale_invoices | Yes | `tabSales Invoice` | `trader_invoice_type` custom |
| sale_invoice_items | Yes | `tabSales Invoice Item` | No serial in custom API |
| delivery_challans | Yes | `tabDelivery Note` | Labeled via trader_invoice_type |
| gate_passes | No | — | Not implemented |
| bank_accounts | Yes | `tabAccount` (type Bank) | GL accounts, not Bank doc |
| payments | Yes | `tabPayment Entry` | — |
| receipts | Yes | PE type Receive | — |
| production_orders | Yes (ERPNext) | `tabWork Order` | Not exposed |
| reports/audit_logs | Yes | `tabVersion`, Activity Log | Not in SPA |
| item_bundles | Yes | `tabItem Bundle` | Custom DocType |

---

## 7. API Gap Analysis

| Required API | Exists? | Current Route | Missing Logic |
|-------------|---------|---------------|---------------|
| Company list/switch | Partial | ERPNext desk only | `list_companies`, `set_default_company` |
| Shared resource config | No | — | DBA settings |
| Currency setup | Partial | Company in settings | CRUD Currency Exchange |
| Exchange rates on txn | No | — | Apply on SI/PI/PE create |
| Warehouse management | Yes | `inventory.get_warehouses` | Create warehouse from SPA |
| Stock transfer | Yes | `inventory.create_stock_entry` | Submit from SPA |
| Serial validation | No | — | `validate_serial_for_item` |
| Sale invoice create | Yes | `sales.create_sales_invoice` | Serial, warehouse UI, bank, history |
| Purchase create | Yes | `purchases.create_purchase_invoice` | Serial, warehouse UI |
| Bank on invoice | No | — | Field + print |
| Last transaction lookup | No | — | `get_customer_item_sales_history` |
| Trial balance | No | — | Report method |
| Balance sheet | No | — | Report method |
| Consolidated reports | No | — | Multi-company SQL |
| POS checkout | No | — | Entire module |
| Production order | No | — | BOM/WO wrappers |

**Implemented API surface (reference):** `docs/audits/backend-endpoints.md` — 100+ whitelisted methods across `sales`, `purchases`, `inventory`, `finance`, `reports`, `customers`, `suppliers`, `gst`, `bundling`, `printing`, `dashboard`, `settings`.

---

## 8. Frontend Gap Analysis

| Required Screen / UI | Exists? | Current Path/Component | Missing UI |
|---------------------|---------|------------------------|------------|
| Company setup | Partial | `SettingsPage.tsx` | Edit company, logo |
| Company switcher | No | — | Navbar dropdown |
| User permissions admin | Partial | Settings roles list | User-role assignment |
| Currency setup | No | — | Exchange rate maintenance |
| Warehouse setup | Partial | Inventory pages | Create warehouse form |
| Item/model setup | Partial | `CreateItemPage.tsx` | Model, barcode, image |
| Serial management | No | — | Serial list/status |
| Sale invoice | Yes | `/sales/new` `CreateSalesInvoicePage.tsx` | History, warehouse, bank, serial |
| Purchase invoice | Yes | `/purchases/new` | Warehouse, serial |
| POS | No | — | Full screen |
| Stock transfer | Partial | Stock movement view | Create transfer form |
| Reports | Yes | `/reports` | TB, BS, company filter |
| Invoice price history | No | — | Panel on invoice form |
| Bank on invoice | No | — | Selector + print |

**Route inventory:** 59 pages under `frontend/trader-ui/src/pages/` (see `App.tsx`).

---

## 9. Serial Number Validation Audit

| Question | Answer |
|----------|--------|
| Are serial numbers tracked? | **No** in trader_app. ERPNext `Serial No` exists if enabled in desk. |
| Linked to item/model? | **Not in custom code.** |
| Linked to warehouse? | **Not in custom code.** |
| Linked to purchase? | **No** |
| Linked to sale invoice? | **No** |
| Duplicate serials prevented? | **Unclear** — would be ERPNext core if used; not invoked |
| Sold serial reused? | **Not enforced in SPA** |
| Serial from Model A scanned under Model B? | **Not blocked** — feature missing |
| Validation frontend only? | **N/A** |
| Validation backend/API? | **N/A** |
| Blocked before save? | **No** |

### Required validation logic (recommended)

```
ON serial_scan(item_code, serial_no, warehouse, context):
  serial = get Serial No where name = serial_no
  IF not serial: REJECT "Unknown serial"
  IF serial.item_code != item_code: REJECT "Serial belongs to {serial.item_code}, not {item_code}"
  IF warehouse AND serial.warehouse != warehouse: REJECT "Serial not in this warehouse"
  IF context = 'sale' AND serial.status != 'Active': REJECT "Serial not available"
  IF context = 'sale' AND serial linked to open invoice: REJECT "Serial already allocated"
  RETURN OK
```

Apply in: `create_sales_invoice`, `create_delivery_note`, `create_purchase_invoice` (receipt), and Stock Entry submit hooks.

---

## 10. Last 4/5 Transaction History Audit

| Question | Answer |
|----------|--------|
| Invoice screen shows previous history? | **No** |
| Customer-specific? | **Only on Customer Detail** (invoice-level, not item) |
| Item-specific? | **No** |
| Model-specific? | **No** (no model field) |
| Last 4 or 5? | **No** |
| Previous sale price? | **No** |
| Date and invoice number? | Partial on customer page |
| Updates when customer/item changes? | **N/A** |
| Backend API? | **No** dedicated endpoint |
| Performant/indexed? | **Not implemented** |

### Recommended API

```python
# trader_app.api.sales.get_customer_item_sales_history
# Params: customer, item_code, limit=5
# SQL: tabSales Invoice Item sii
#       JOIN tabSales Invoice si ON si.name = sii.parent
# WHERE si.customer = %(customer)s AND sii.item_code = %(item_code)s
#       AND si.docstatus = 1 AND si.is_return = 0
# ORDER BY si.posting_date DESC, si.creation DESC
# LIMIT 5
# Return: posting_date, invoice name, qty, rate, discount, amount
```

### Recommended UI

On `CreateSalesInvoicePage.tsx`, when `customer` and line `item_code` are set, fetch and render a compact table (last 5 rows) under the line or in a side panel.

---

## 11. DBA / Multi-Company Shared Resource Audit

| Question | Answer |
|----------|--------|
| Multiple companies supported? | **Data yes** (ERPNext); **SPA no** |
| Resources shared or company-specific? | **Implicit ERPNext rules** (global masters, company transactions) |
| Same customer across companies? | **Yes** (standard ERPNext) |
| Same item across companies? | **Yes** |
| Same warehouse across companies? | **No** — warehouse has `company` |
| Transactions separated company-wise? | **Yes** in DB |
| Reports separated? | **Backend yes** if `company` passed; UI uses default only |
| Consolidated reports? | **No** |
| Data leakage risk? | **Medium** — wrong default company, weak permissions |
| Permissions company-aware? | **No** |

### Recommended implementation

1. Session context: `active_company` from user default or switcher.  
2. All `trader_app` list/create methods require explicit `company` (no silent first-company fallback for multi-company sites).  
3. `permission_query_conditions` append `` AND `tabSales Invoice`.company IN ({allowed}) ``.  
4. Report parameter `companies: []` for consolidated mode.  
5. Optional admin UI for “shared customer/item” flags if business requires overriding ERPNext defaults.

---

## 12. Recommended Implementation Roadmap

### Phase 1: Critical data integrity (4–6 weeks)

| Task | Files / areas |
|------|----------------|
| Serial validation API + item flags | New `api/serial.py`, Item custom fields, SI/DN/PI line handling |
| Wrong-model scan block | `validate_serial_for_item` called from create/submit |
| Warehouse on sales/purchase lines | `CreateSalesInvoicePage.tsx`, `CreatePurchaseInvoicePage.tsx`, `sales.create_sales_invoice` |
| Stock availability check | `inventory.py` helper; call before submit when updating stock |
| Company on all API calls | `api.ts` context, every `*_api` call, remove blind `_default_company` for multi-company sites |

**Testing:** Integration tests for serial mismatch; bin qty < invoice qty; company A user cannot POST company B invoice.

### Phase 2: Core ERP completion (3–4 weeks)

| Task | Files / areas |
|------|----------------|
| Customer-item history API + UI | `sales.py`, `CreateSalesInvoicePage.tsx` |
| Bank account on invoice | Custom field, `create_sales_invoice`, print template |
| Discount on invoice lines | Create pages + API |
| Submit stock policy documented + UI toggle for update_stock / DN path | `sales.py`, user docs |

### Phase 3: Multi-company / DBA (4–6 weeks)

| Task | Files / areas |
|------|----------------|
| Company switcher | `Navbar.tsx`, `authStore` or settings store |
| Company-aware permissions | `permissions.py`, Frappe User Permissions |
| Consolidated reports | `reports.py`, `reportDefinitions.ts` |

### Phase 4: Multi-currency (3–4 weeks)

| Task | Files / areas |
|------|----------------|
| Currency Exchange UI | New settings section or desk link |
| FX on SI/PI/PE | Create forms + ERPNext conversion |
| Gain/loss report | `reports.py` |

### Phase 5: Reporting & exports (2–3 weeks)

| Task | Files / areas |
|------|----------------|
| Trial balance & balance sheet | `reports.py`, `reportDefinitions.ts` |
| PDF report export optional | Server-side or print CSS |
| Serial / warranty reports | After serial phase |

**Files likely to change most:** `sales.py`, `inventory.py`, `reports.py`, `CreateSalesInvoicePage.tsx`, `permissions.py`, `reportDefinitions.ts`, `api.ts`.

---

## 13. Final Recommendation

| Question | Recommendation |
|----------|----------------|
| Ready for production (full checklist)? | **No** |
| Must fix before client deployment? | Serial/model validation (if serials required); invoice price history; warehouse on sales; company isolation if multi-company; bank on invoice if mandated |
| Can add later? | POS, production, landed cost, license, Excel export |
| Architectural risks | Single default company; `update_stock=0` on invoice; permissions only on SI/PI; reliance on ERPNext desk for TB/BS/serials until exposed |
| Modules needing refactor | Permissions layer; company context propagation; sales invoice create (warehouse + history + serial) |

---

## Appendix: Backend vs frontend mismatches

| Capability | Backend | Frontend |
|------------|---------|----------|
| Per-line warehouse on SI | Yes (`item.warehouse`) | No selector |
| Company parameter on reports | Yes | Not passed |
| Stock ledger | Yes (`get_stock_ledger`) | `StockMovementPage.tsx` **wired** |
| Payment bank accounts | Yes (`get_payment_entry_setup`) | Payment pages only |
| Customer transactions | Yes | Customer detail only (not item-level) |
| Settings save | Yes (`save_settings`) | **Working** (`SettingsPage.tsx`) |
| Item bundle | Yes (`bundling.py`) | `ItemBundlesPage.tsx` |

---

*This document should be updated after each major release. Run a fresh grep-based audit when adding modules. Sync checklist counts via `FEATURE_COVERAGE_MATRIX.md`.*

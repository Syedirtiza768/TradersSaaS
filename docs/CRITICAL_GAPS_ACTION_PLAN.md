# Critical Gaps Action Plan

Pre-production gaps that must be addressed before client deployment. Each item includes evidence, business risk, and recommended direction.

---

## 1. Customer + item/model invoice history (last 4–5 transactions)

| Field | Detail |
|-------|--------|
| **Status** | Missing |
| **Evidence** | `CreateSalesInvoicePage.tsx` has no history panel. `customersApi.getTransactions` (`customers.py` L101–126) returns invoice-level rows only (no `item_code`, no limit-5 by item). |
| **Business risk** | Sales staff cannot see prior pricing for the same customer/item at invoice time — pricing errors, margin loss, disputes. |
| **Required work** | New API e.g. `get_customer_item_sales_history(customer, item_code, limit=5)` querying `tabSales Invoice Item` joined to submitted SIs; React panel on invoice form updating on customer + item change; index on `(customer, item_code, posting_date)`. |

---

## 2. Serial number tracking and wrong-model scan prevention

| Field | Detail |
|-------|--------|
| **Status** | Missing |
| **Evidence** | No `serial` references in `apps/trader_app/trader_app/api/*.py`. No serial fields in `CreateSalesInvoicePage.tsx`. Demo seeds barcodes only (`demo/generators/items.py`). |
| **Business risk** | Cannot trace units; wrong serial under wrong model breaks warranty and inventory integrity. |
| **Required work** | Enable ERPNext `has_serial_no` on items; capture `serial_no` on PI/DN/SI lines; API `validate_serial_for_item(item_code, serial_no, warehouse)`; block save/submit if model mismatch; serial status report. |

---

## 3. DBA / multi-company with shared resources and company isolation

| Field | Detail |
|-------|--------|
| **Status** | Partially Implemented (ERPNext only) — Missing Trader DBA layer |
| **Evidence** | `_default_company()` in all API modules (`sales.py` L761–767, etc.). No company switcher in React. Customers/items global; warehouses per company. Permissions not company-scoped (`permissions.py`). |
| **Business risk** | Operating multiple legal entities on one site without UI isolation risks wrong-company posting; no consolidated vs separate reporting. |
| **Required work** | Company switcher + pass `company` on every API call; company-aware permission queries; optional shared-master flags; consolidated report endpoints. |

---

## 4. Bank account on sales invoice (display and settlement intent)

| Field | Detail |
|-------|--------|
| **Status** | Missing on invoice; Partial on payments |
| **Evidence** | `create_sales_invoice` (`sales.py` L327–387) has no bank field. Bank selection exists on `CreatePaymentEntryPage.tsx` and `RecordInvoicePaymentPanel.tsx` via `financeApi.getPaymentSetup`. |
| **Business risk** | Invoice does not show where to pay; bank choice only appears at payment time. |
| **Required work** | Custom field `preferred_bank_account` on Sales Invoice (or mode of payment); show on print + create form; optional default from customer. |

---

## 5. Warehouse-wise sales with validation

| Field | Detail |
|-------|--------|
| **Status** | Partially Implemented |
| **Evidence** | Backend defaults `Main Warehouse - {abbr}` (`sales.py` L354, L368). `CreateSalesInvoicePage.tsx` does not pass `warehouse` per line. `get_stock_balance` / `WarehouseStockPage.tsx` prove warehouse stock exists. |
| **Business risk** | Stock deducted from wrong warehouse; overselling from empty location. |
| **Required work** | Warehouse selector per line on sale/purchase/challan forms; validate `Bin.actual_qty` before submit when `update_stock=1` or via DN workflow. |

---

## 6. Multi-currency and exchange gain/loss

| Field | Detail |
|-------|--------|
| **Status** | Missing in Trader layer |
| **Evidence** | List APIs return `currency`; create flows do not set foreign currency or exchange rate. Demo payments hard-code `target_exchange_rate: 1` (`payments.py` L198). |
| **Business risk** | Cannot trade in USD/other currencies with correct GL; FX exposure untracked. |
| **Required work** | Currency + exchange rate on SI/PI/PE forms; ERPNext Currency Exchange maintenance UI; FX gain/loss report/journals. |

---

## 7. Trial balance and balance sheet in SPA

| Field | Detail |
|-------|--------|
| **Status** | Missing |
| **Evidence** | `reportDefinitions.ts` includes P&L and GL but not trial balance or balance sheet. `reports.py` has no whitelisted TB/BS methods used by UI. |
| **Business risk** | Accountants cannot close books from Trader UI; must use ERPNext desk. |
| **Required work** | Whitelist wrappers or SQL reports for TB/BS; add to Finance category in `reportDefinitions.ts`. |

---

## 8. POS and barcode operational flows

| Field | Detail |
|-------|--------|
| **Status** | Missing |
| **Evidence** | No `/pos` routes in `App.tsx`. No barcode scan handlers in frontend. |
| **Business risk** | Counter sales and scan-driven fulfillment not supported in custom UI. |
| **Required work** | POS screen (fast cart + scan input) or integrate ERPNext POS; barcode lookup API by barcode → item. |

---

## 9. Production / manufacturing

| Field | Detail |
|-------|--------|
| **Status** | Missing |
| **Evidence** | No Work Order/BOM APIs. `Item Bundle` (`bundling.py`) is kit definition only, not production. |
| **Business risk** | Cannot run job costing or FG receipt from raw materials in Trader UI. |
| **Required work** | Expose ERPNext Work Order/BOM or defer scope; if deferred, document as out of scope for v1. |

---

## 10. Company-wise permissions and audit trail in UI

| Field | Detail |
|-------|--------|
| **Status** | Not Production-Ready |
| **Evidence** | `permissions.py` filters by role/owner on SI/PI only. No Activity Log / Version in SPA. |
| **Business risk** | Users may see wrong documents; compliance audits harder. |
| **Required work** | Expand permission hooks; optional audit log screen; company in permission queries. |

---

## Suggested implementation order

1. **Week 1–2:** Warehouse on sales + stock validation; bank on invoice; customer-item history API/UI.  
2. **Week 3–4:** Serial master + validation API + invoice line serial entry.  
3. **Week 5–6:** Company switcher + company param propagation + permission hardening.  
4. **Week 7+:** Multi-currency, TB/BS reports, DBA consolidated reporting, POS (if in scope).

---

## Out of scope for this action plan (unless client confirms)

- License / subscription module  
- Landed cost vouchers  
- Full gate pass DocType (vs delivery challan)  
- Excel export (CSV may suffice short-term)

See full evidence and module notes in [FEATURE_GAP_ANALYSIS.md](./FEATURE_GAP_ANALYSIS.md) and the complete checklist in [FEATURE_COVERAGE_MATRIX.md](./FEATURE_COVERAGE_MATRIX.md).

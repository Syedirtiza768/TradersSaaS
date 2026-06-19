# Feature Coverage Matrix

Evidence-based audit of the Traders application (Frappe 15 + ERPNext 15 + React `trader-ui`).  
Audit date: 2026-05-17. Status definitions match `FEATURE_GAP_ANALYSIS.md`.

| # | Feature | Category | Status | Evidence | Gap / Missing Work | Priority |
|---|---------|----------|--------|----------|-------------------|----------|
| **A — User & Company Management** |
| A1 | User login | Auth | Implemented | `LoginPage.tsx`; `authApi.login` → `POST /api/method/login` | — | — |
| A2 | User authentication (session) | Auth | Implemented | `authStore.ts`; `frappe.auth.get_logged_user`; CSRF in `api.ts` | — | — |
| A3 | User logout | Auth | Implemented | `authApi.logout` | — | — |
| A4 | User roles | Auth | Implemented | `hooks.py` fixtures: Trader Admin, Sales/Purchase/Accountant/Warehouse Manager | — | — |
| A5 | User rights / permissions | Auth | Partially Implemented | `permissions.py` (SI/PI only); `permissions.ts` capabilities | No module-wide Frappe permission matrix in UI | High |
| A6 | Role-based access control | Auth | Partially Implemented | `get_current_user_roles`; `ProtectedRoute`; sidebar capability gating | Not company-scoped; limited doctypes | High |
| A7 | Company profile setup | Company | Partially Implemented | ERPNext `Company` via demo `CompanyGenerator`; Settings read-only | No Trader UI to create/edit company | Medium |
| A8 | Company logo management | Company | Missing | No API/UI references | Add company branding API + Settings UI | Low |
| A9 | Company general information | Company | Partially Implemented | `settings.py` `_payload()` returns company fields | Read-only in `SettingsPage.tsx` | Medium |
| A10 | Multi-company support (data model) | Company | Partially Implemented | ERPNext `tabCompany`; APIs accept `company` param | UI uses `_default_company()` only | Critical |
| A11 | Manage / open different companies | Company | Missing | No company switcher in `DashboardLayout` / `Navbar` | Company selector + default persistence | Critical |
| A12 | Company-wise settings | Company | Partially Implemented | GST via `gst.py`; tax templates per company | No unified company settings CRUD in SPA | Medium |
| A13 | Company-wise financial years | Company | Partially Implemented | Demo creates `Fiscal Year`; Settings links `/app/fiscal-year` | No in-SPA fiscal year management | Medium |
| A14 | Unlimited financial years | Company | Implemented | ERPNext supports multiple `Fiscal Year` records | — | — |
| A15 | Company-wise invoice numbering | Company | Implemented | ERPNext naming series on `Sales Invoice` / `Purchase Invoice` | — | — |
| A16 | Company-wise voucher numbering | Company | Implemented | ERPNext naming on Journal/Payment Entry | — | — |
| A17 | Company-wise tax setup | Company | Partially Implemented | `gst.py`, `invoice_types.py`, `GstSettingsPage.tsx` | — | — |
| A18 | Company-wise bank accounts | Company | Partially Implemented | `finance.py` `_ensure_company_bank_accounts`, payment settlement | Not on sales invoice form | High |
| A19 | Company-wise reporting | Company | Partially Implemented | Report APIs filter `company = %(company)s` | No company picker on reports | High |
| A20 | Company-wise permissions | Company | Missing | Permissions are role/owner-based, not company | Company in permission queries | Critical |
| A21 | License handling | Company | Missing | No license module in codebase | N/A unless product requirement | Low |
| A22 | Unlimited period license | Company | Missing | No license logic | N/A | Low |
| **B — DBA / Shared Resource Multi-Company** |
| B1 | Multiple companies in one DB | DBA | Partially Implemented | ERPNext multi-Company | Trader SPA single-company UX | Critical |
| B2 | Shared master data model | DBA | Partially Implemented | ERPNext: Customer/Supplier/Item global | No `is_shared` / DBA config layer | Critical |
| B3 | Shared customers | DBA | Implemented | `tabCustomer` has no `company` (ERPNext standard) | — | — |
| B4 | Shared vendors | DBA | Implemented | `tabSupplier` global | — | — |
| B5 | Shared items | DBA | Implemented | `tabItem` global; `inventory.py` `get_items` | — | — |
| B6 | Shared warehouses | DBA | Missing | `tabWarehouse.company` required per warehouse | DBA shared warehouse flag | Critical |
| B7 | Shared users | DBA | Implemented | `tabUser` + `Has Role` | — | — |
| B8 | Shared chart of accounts (where applicable) | DBA | Missing | CoA is per-company in ERPNext | Consolidation chart not implemented | High |
| B9 | Configurable shared vs company-specific | DBA | Missing | No trader DBA settings DocType | Design + implement | Critical |
| B10 | Company-wise transaction separation | DBA | Partially Implemented | `si.company`, `pi.company` on all list APIs | UI never switches company | Critical |
| B11 | Company-wise invoices | DBA | Partially Implemented | `create_sales_invoice` sets `si.company` | Default company only | Critical |
| B12 | Company-wise accounting entries | DBA | Partially Implemented | ERPNext GL on submit | Same default-company limit | Critical |
| B13 | Company-wise stock movements | DBA | Partially Implemented | SLE/Bin via warehouse.company | — | High |
| B14 | Company-wise ledgers | DBA | Partially Implemented | Reports filter by company | — | High |
| B15 | Company-wise tax | DBA | Partially Implemented | Tax templates filtered by company in `invoice_types.py` | — | — |
| B16 | Company-wise bank accounts | DBA | Partially Implemented | `finance.py` company bank GL accounts | — | — |
| B17 | Company-wise financial years | DBA | Partially Implemented | Fiscal Year linked to companies in ERPNext | — | — |
| B18 | Company-wise permissions | DBA | Missing | See A20 | — | Critical |
| B19 | Consolidated reporting | DBA | Missing | All reports single `company` param | Multi-company rollup reports | Critical |
| B20 | Separate reporting per company | DBA | Partially Implemented | Backend supports `company` arg | UI lacks company filter | High |
| B21 | Prevent cross-company data mixing | DBA | Not Production-Ready | SQL uses company filter when param set | Default company + no UI = operational risk | Critical |
| B22 | `company_id` on transactional records | DBA | Implemented | ERPNext standard on SI, PI, SO, PO, JE, PE, SE | — | — |
| B23 | Query scopes / leakage prevention | DBA | Partially Implemented | List endpoints use `company = %(company)s` | Permissions not company-aware | Critical |
| **C — Multi-Currency** |
| C1 | Currency master | Currency | Implemented | ERPNext `Currency`; Company.default_currency | — | — |
| C2 | Base currency per company | Currency | Implemented | `Company.default_currency`; `settings.py` | — | — |
| C3 | Foreign currency transactions | Currency | Missing | No trader API/UI for multi-currency invoices | ERPNext supports; not exposed | High |
| C4 | Currency on sale invoice | Currency | Partially Implemented | `get_sales_invoices` selects `si.currency` | Create form does not set foreign currency | Medium |
| C5 | Currency on purchase invoice | Currency | Partially Implemented | List APIs return `currency` | Create form does not expose | Medium |
| C6 | Currency on receipts | Currency | Partially Implemented | Payment Entry has currency fields (ERPNext) | UI uses company default implicitly | Medium |
| C7 | Currency on payments | Currency | Partially Implemented | Same as C6 | — | Medium |
| C8 | Exchange rate setup | Currency | Missing | No trader `get_exchange_rates` API | Use ERPNext Currency Exchange | High |
| C9 | Exchange rate on transactions | Currency | Missing | Demo payments use `target_exchange_rate: 1` only | — | High |
| C10 | Currency conversion in ledgers | Currency | Missing | No custom conversion in `reports.py` | — | High |
| C11 | Currency in financial reports | Currency | Missing | Reports in company currency only | — | Medium |
| C12 | Currency gain/loss | Currency | Missing | No trader logic | ERPNext exchange gain/loss journals | High |
| C13 | Customer/vendor currency | Currency | Partially Implemented | ERPNext party account currency | Not in Trader UI | Medium |
| C14 | Multi-currency bank accounts | Currency | Missing | Bank accounts have `account_currency` in demo | Not managed in SPA | Medium |
| C15 | Tax/VAT by country | Currency | Partially Implemented | `GstSettingsPage`, Pakistan-oriented demo | Country-agnostic tax engine incomplete | Medium |
| C16 | Sales tax/VAT invoices | Currency | Implemented | `trader_invoice_type` Tax Invoice; `invoiceTypes.ts` | — | — |
| C17 | Non-sales-tax invoices | Currency | Implemented | Commercial / Non-GST / Bill of Supply types | — | — |
| C18 | Localization-ready tax structure | Currency | Partially Implemented | Template-based GST | Hard-coded Pakistan demo patterns | Medium |
| **D — Backup & Export** |
| D1 | Backup system | Data Safety | Partially Implemented | `scripts/backup.sh` (MariaDB + site files) | No restore UI; ops script only | Medium |
| D2 | Data restore | Data Safety | Unclear / Needs Verification | Not documented in trader_app | Verify bench restore procedure | Medium |
| D3 | Export to Excel | Export | Missing | Reports export CSV only (`ReportView.tsx`) | XLSX export | Low |
| D4 | Export to PDF | Export | Partially Implemented | `printing.py` print data; `DocumentPrintPage.tsx` | Not all list reports | Medium |
| D5 | Export to CSV | Export | Implemented | `ReportView` `toCsv` + `downloadTextFile` | — | — |
| D6 | Export to Text | Export | Missing | — | — | Low |
| D7 | Export to HTML | Export | Partially Implemented | Print view renders HTML client-side | — | Low |
| D8 | Report export | Export | Implemented | Per-report CSV in `ReportView.tsx` | No PDF batch | — |
| D9 | Invoice export | Export | Partially Implemented | `get_print_data` for print | — | — |
| D10 | Ledger export | Export | Partially Implemented | CSV via report export on GL report | — | Low |
| D11 | Data safety controls | Data Safety | Partially Implemented | Frappe transactions; `docstatus` workflow | No custom audit DocType | Medium |
| D12 | Audit logs | Data Safety | Partially Implemented | ERPNext Version / Activity Log (desk) | Not exposed in trader-ui | Medium |
| D13 | Soft deletes | Data Safety | Partially Implemented | `disable_customer` / `disable_supplier` | Not universal | Low |
| D14 | DB transaction handling | Data Safety | Implemented | Frappe ORM commits on API methods | — | — |
| D15 | Error handling failed operations | Data Safety | Partially Implemented | Try/except on list endpoints; UI error banners | Inconsistent across all APIs | Medium |
| **E — Accounting** |
| E1 | Chart of accounts | Accounting | Implemented | ERPNext CoA; demo `CompanyGenerator` | — | — |
| E2 | Multi-level CoA | Accounting | Implemented | ERPNext account tree | — | — |
| E3 | 2-level CoA | Accounting | Implemented | Configurable in ERPNext | — | — |
| E4 | 4-level CoA | Accounting | Implemented | Configurable in ERPNext | — | — |
| E5 | Account groups | Accounting | Implemented | `is_group` on Account | — | — |
| E6 | Account heads / ledgers | Accounting | Implemented | `finance.py` `get_accounts` | — | — |
| E7 | Journal vouchers | Accounting | Implemented | `create_journal_entry`; `CreateJournalEntryPage.tsx` | — | — |
| E8 | Auto-generated vouchers | Accounting | Implemented | ERPNext on submit SI/PI/PE | — | — |
| E9 | Sales voucher generation | Accounting | Implemented | ERPNext GL from Sales Invoice submit | — | — |
| E10 | Purchase voucher generation | Accounting | Implemented | ERPNext GL from Purchase Invoice submit | — | — |
| E11 | Receipt voucher generation | Accounting | Implemented | `create_payment_entry`; `RecordInvoicePaymentPanel` | — | — |
| E12 | Payment voucher generation | Accounting | Implemented | `finance.py` payment APIs | — | — |
| E13 | Cash receipts | Accounting | Implemented | Payment Entry Receive + Cash account | — | — |
| E14 | Bank receipts | Accounting | Implemented | Payment Entry + Bank settlement accounts | — | — |
| E15 | Cash payments | Accounting | Implemented | Payment Entry Pay | — | — |
| E16 | Bank payments | Accounting | Implemented | Payment Entry Pay + bank reference fields | — | — |
| E17 | Bank account on sale invoice | Accounting | Missing | Not in `CreateSalesInvoicePage.tsx` or `create_sales_invoice` | Display + optional link to payment | High |
| E18 | Cashbook | Accounting | Partially Implemented | `get_cashflow_report` approximates cash movement | No dedicated cashbook report in UI | Medium |
| E19 | Bank ledgers | Accounting | Partially Implemented | GL report with account filter | No dedicated bank ledger screen | Medium |
| E20 | Account ledgers | Accounting | Implemented | `get_general_ledger` report in UI | — | — |
| E21 | Trial balance | Accounting | Missing | Not in `reportDefinitions.ts` or `reports.py` whitelist used by UI | Add report | High |
| E22 | Income statement / P&L | Accounting | Implemented | `profit-and-loss` report; `get_profit_and_loss` | — | — |
| E23 | Balance sheet | Accounting | Missing | Not in trader reports UI/API exposure | Add report | High |
| E24 | Daily general journal | Accounting | Partially Implemented | `get_general_ledger` | No "daily affairs" journal report | Medium |
| E25 | Receivables aging | Accounting | Implemented | `receivable-aging-detail` report | — | — |
| E26 | Payables aging | Accounting | Implemented | `payable-aging-detail` report | — | — |
| E27 | Opening balances | Accounting | Partially Implemented | ERPNext opening entries (desk) | No SPA workflow | Medium |
| E28 | Posting rules | Accounting | Implemented | ERPNext account settings | — | — |
| E29 | Fiscal year handling | Accounting | Partially Implemented | `_current_fiscal_year` in `reports.py` | Desk-only setup | Medium |
| E30 | Account-wise reporting | Accounting | Implemented | GL report account filter | — | — |
| E31 | Customer ledger | Accounting | Implemented | `customer-ledger` report | — | — |
| E32 | Supplier ledger | Accounting | Implemented | `supplier-ledger` report | — | — |
| E33 | Voucher reversal/correction | Accounting | Partially Implemented | Cancel SI/PI; Journal entries | No dedicated reversal wizard | Medium |
| E34 | Tax posting logic | Accounting | Implemented | Tax templates on invoices; `get_tax_summary_report` | — | — |
| E35 | Currency gain/loss posting | Accounting | Missing | See C12 | — | High |
| **F — Inventory** |
| F1 | Item/product master | Inventory | Implemented | `get_items`, `create_item`, `CreateItemPage.tsx` | — | — |
| F2 | Item categories/groups | Inventory | Implemented | `get_item_groups`; Item Group in ERPNext | — | — |
| F3 | Multi-level inventory chart | Inventory | Implemented | ERPNext Item Group tree | — | — |
| F4 | 2-level inventory hierarchy | Inventory | Implemented | ERPNext configurable | — | — |
| F5 | 3-level inventory hierarchy | Inventory | Implemented | ERPNext configurable | — | — |
| F6 | Product pictures | Inventory | Missing | `get_item_detail` no image fields in API | Item image in ERPNext | Low |
| F7 | SKU/item code | Inventory | Implemented | `item_code` primary key | — | — |
| F8 | Model number field | Inventory | Missing | No custom field on Item in trader_app | Add custom field if required | Medium |
| F9 | Brand/manufacturer | Inventory | Partially Implemented | ERPNext `brand` on Item; reports group by brand | Not on create item form | Low |
| F10 | Unit of measure | Inventory | Implemented | `stock_uom` on create_item | — | — |
| F11 | Opening stock | Inventory | Partially Implemented | Demo `InventoryGenerator` Stock Entry | No guided opening stock UI | Medium |
| F12 | Stock in | Inventory | Implemented | `create_purchase_receipt` Material Receipt | — | — |
| F13 | Stock out | Inventory | Implemented | `create_sales_dispatch` Material Issue | — | — |
| F14 | Inventory adjustments | Inventory | Partially Implemented | Stock Entry purposes via ERPNext | No dedicated adjustment screen | Medium |
| F15 | Inventory transfers | Inventory | Implemented | `create_stock_entry` Material Transfer | — | — |
| F16 | Reorder levels | Inventory | Partially Implemented | `get_reorder_report`; scheduler `update_reorder_levels` | Item Reorder not in create item UI | Medium |
| F17 | Inventory ledgers | Inventory | Implemented | `get_stock_ledger`; `StockMovementPage.tsx` | — | — |
| F18 | Inventory balances | Inventory | Implemented | `get_stock_balance`; `WarehouseStockPage.tsx` | — | — |
| F19 | Inventory issue notes | Inventory | Partially Implemented | Material Issue stock entry | No named "issue note" DocType | Low |
| F20 | Item-wise costing | Inventory | Partially Implemented | Valuation via ERPNext; reports show COGS | Costing method not in UI | Medium |
| F21 | FIFO/average costing | Inventory | Partially Implemented | ERPNext stock settings | Not configurable in SPA | Medium |
| F22 | Item cost/price statistics | Inventory | Partially Implemented | `get_item_detail` prices; item sales report | — | — |
| F23 | Item-wise profit | Inventory | Implemented | `sales-performance` / `customer-profitability` reports | — | — |
| F24 | Stock valuation | Inventory | Implemented | Bin.stock_value; stock balance report | — | — |
| F25 | Negative stock prevention | Inventory | Partially Implemented | ERPNext stock settings | Not explicitly validated in trader APIs | Medium |
| F26 | Stock availability validation | Inventory | Partially Implemented | ERPNext on submit with settings | Invoice create uses `update_stock=0` default | High |
| F27 | Stock reservation | Inventory | Missing | No reservation API | — | Low |
| F28 | Warranty tracking | Inventory | Missing | No warranty DocType/API | — | Medium |
| F29 | Product serial tracking | Inventory | Missing | No serial in trader_app | ERPNext Serial No not integrated | Critical |
| F30 | Serial-based item tracking | Inventory | Missing | Same as F29 | — | Critical |
| **G — Multi-Warehouse** |
| G1 | Warehouse master | Warehouse | Implemented | `get_warehouses`; ERPNext Warehouse | — | — |
| G2 | Multiple warehouses | Warehouse | Implemented | Demo 3 warehouses; company filter | — | — |
| G3 | Branches/storage locations | Warehouse | Implemented | Warehouse records | — | — |
| G4 | Warehouse-wise stock qty | Warehouse | Implemented | `get_stock_balance` warehouse filter | — | — |
| G5 | Warehouse-wise inventory ledger | Warehouse | Implemented | `get_stock_ledger` warehouse filter | — | — |
| G6 | Warehouse-wise availability | Warehouse | Implemented | `WarehouseStockPage.tsx` | — | — |
| G7 | Warehouse-wise valuation | Warehouse | Implemented | stock balance report | — | — |
| G8 | Warehouse-wise reorder | Warehouse | Partially Implemented | Reorder report warehouse filter | — | — |
| G9 | Warehouse-wise reports | Warehouse | Implemented | Multiple inventory reports | — | — |
| G10 | Warehouse-to-warehouse transfer | Warehouse | Implemented | `create_stock_entry` Material Transfer | — | — |
| G11 | Location transfers | Warehouse | Implemented | Same as G10 | — | — |
| G12 | Stock adjustment by warehouse | Warehouse | Partially Implemented | Stock Entry | No dedicated UI | Medium |
| G13 | Purchase receiving to warehouse | Warehouse | Partially Implemented | `create_purchase_invoice` line warehouse; receipt stock entry | Purchase receipt page limited | Medium |
| G14 | Sale from specific warehouse | Warehouse | Partially Implemented | API supports per-line `warehouse` | `CreateSalesInvoicePage` does not expose warehouse | High |
| G15 | Production issue/receipt warehouse | Warehouse | Missing | No production module | — | Low |
| G16 | User permission by warehouse | Warehouse | Missing | No warehouse in permission hooks | — | Medium |
| G17 | Company-wise warehouse separation | Warehouse | Implemented | `w.company = %s` in SQL | — | — |
| G18 | Shared warehouse (DBA) | Warehouse | Missing | See B6 | — | Critical |
| G19 | Prevent sell from wrong warehouse | Warehouse | Not Production-Ready | Defaults to Main Warehouse; no UI validation | Per-line warehouse + stock check | High |
| G20 | Prevent transfer unavailable stock | Warehouse | Partially Implemented | ERPNext validates on Stock Entry submit | Draft entries not validated in custom API | Medium |
| **H — Purchasing** |
| H1 | Purchase requisitions | Purchasing | Implemented | Material Request APIs + pages | — | — |
| H2 | Purchase orders | Purchasing | Implemented | Full CRUD flow in SPA | — | — |
| H3 | PO approval flow | Purchasing | Partially Implemented | ERPNext workflows in fixtures | Not visible as approval UI in SPA | Medium |
| H4 | PO tracking | Purchasing | Implemented | `open-purchase-orders` report; Operations queues | — | — |
| H5 | Inward gate passes | Purchasing | Missing | No Gate Pass DocType | Delivery Note used for outbound only | Medium |
| H6 | Purchase receiving | Purchasing | Implemented | `CreatePurchaseReceiptPage.tsx`; stock receipt API | — | — |
| H7 | Purchases / purchase invoice | Purchasing | Implemented | `CreatePurchaseInvoicePage.tsx` | — | — |
| H8 | Purchase invoice (tax variants) | Purchasing | Implemented | `trader_invoice_type` on PI | — | — |
| H9 | Supplier management | Purchasing | Implemented | Supplier CRUD pages + API | — | — |
| H10 | Purchase returns | Purchasing | Implemented | `CreatePurchaseReturnPage.tsx` | — | — |
| H11 | Landed cost | Purchasing | Missing | No landed cost voucher in trader_app | ERPNext feature not exposed | Low |
| H12 | Purchase reports | Purchasing | Implemented | Multiple purchasing reports | — | — |
| H13 | Inventory purchase analysis | Purchasing | Implemented | `item-purchases` report | — | — |
| H14 | Purchase and sale analysis | Purchasing | Partially Implemented | Separate sales/purchase reports | Combined analysis report missing | Low |
| H15 | Auto accounting from purchase | Purchasing | Implemented | ERPNext on PI submit | — | — |
| H16 | Warehouse on purchase | Purchasing | Partially Implemented | API `warehouse` per line; default Main | UI may not expose per line | Medium |
| H17 | Serial on purchase | Purchasing | Missing | No serial capture | — | Critical |
| H18 | Currency on purchase | Purchasing | Partially Implemented | See C5 | — | Medium |
| H19 | Tax on purchase | Purchasing | Implemented | Tax templates on create PI | — | — |
| **I — Sales & Invoicing** |
| I1 | Quotations | Sales | Implemented | Full SPA flow | — | — |
| I2 | Sale orders | Sales | Implemented | Full SPA flow | — | — |
| I3 | Sale order tracking | Sales | Implemented | Operations page; order detail | — | — |
| I4 | Delivery challans | Sales | Implemented | Delivery Note + `trader_invoice_type` | — | — |
| I5 | Outward gate passes | Sales | Missing | No Gate Pass DocType | Challan only | Medium |
| I6 | Sale invoices | Sales | Implemented | Create/list/detail/submit | — | — |
| I7 | Sales tax/VAT invoices | Sales | Implemented | Tax Invoice type | — | — |
| I8 | Simple invoices | Sales | Implemented | Commercial Invoice type | — | — |
| I9 | Non-sales-tax invoices | Sales | Implemented | Non-GST / Bill of Supply | — | — |
| I10 | Multiple invoice formats | Sales | Partially Implemented | `invoiceTypes.ts`; `printing.py` formats | Limited templates | Medium |
| I11 | Discount columns | Sales | Partially Implemented | ERPNext supports discount; not in create UI | Add discount fields to lines | Medium |
| I12 | Percentage discounts | Sales | Missing | Not in `CreateSalesInvoicePage` | — | Medium |
| I13 | Amount discounts | Sales | Missing | Not in create UI | — | Medium |
| I14 | Customer management | Sales | Implemented | Customer CRUD | — | — |
| I15 | Customer-specific pricing | Sales | Missing | Uses item selling price only | Price list / party-specific | Medium |
| I16 | Sale returns | Sales | Implemented | `CreateSalesReturnPage.tsx` | — | — |
| I17 | Auto accounting from sale | Sales | Implemented | ERPNext on SI submit | — | — |
| I18 | Warehouse on sale | Sales | Partially Implemented | API supports; UI does not | Add warehouse selector | High |
| I19 | Currency on sale | Sales | Partially Implemented | See C4 | — | Medium |
| I20 | Tax on sale | Sales | Implemented | Tax template picker on create | — | — |
| I21 | Print invoice | Sales | Implemented | `DocumentPrintPage.tsx`; `printApi` | — | — |
| I22 | PDF invoice | Sales | Partially Implemented | Browser print from print view | Server PDF generation unclear | Medium |
| I23 | Invoice templates | Sales | Partially Implemented | `print_format_for_doc` | Limited set | Medium |
| I24 | Bank account on sale invoice | Sales | Missing | See E17 | — | High |
| **I-Hist — Invoice screen transaction history (customer + item/model)** |
| IH1 | Last 4/5 sale transactions on invoice screen | Sales | Missing | Not in `CreateSalesInvoicePage.tsx` | New API + UI panel | Critical |
| IH2 | Previous sale price history | Sales | Missing | — | — | Critical |
| IH3 | Customer-wise item price history | Sales | Missing | — | — | Critical |
| IH4 | Model-wise previous price | Sales | Missing | No model field | — | Critical |
| IH5 | Same item/model sold to same client | Sales | Missing | `get_customer_transactions` is invoice-level only | — | Critical |
| IH6 | Transaction date in history | Sales | Partially Implemented | Customer detail shows `posting_date` | Not on invoice form | Critical |
| IH7 | Previous invoice number | Sales | Partially Implemented | Customer transactions include `name` | Not item-level on invoice | Critical |
| IH8 | Previous quantity | Sales | Missing | — | — | Critical |
| IH9 | Previous rate | Sales | Missing | — | — | Critical |
| IH10 | Previous discount | Sales | Missing | — | — | Critical |
| **J — Barcode, Serial, POS** |
| J1 | Barcode scanning | POS/Serial | Missing | No scan handler in UI | — | High |
| J2 | Barcode printing | POS/Serial | Missing | — | — | Medium |
| J3 | Barcode generation | POS/Serial | Partially Implemented | Demo `items.py` `_generate_ean13` | Not in production UI | Low |
| J4 | Barcode field on item | POS/Serial | Partially Implemented | Demo sets Item Barcode child table | `create_item` does not accept barcodes | Medium |
| J5 | POS system | POS/Serial | Missing | No POS routes | — | High |
| J6 | POS invoice screen | POS/Serial | Missing | — | — | High |
| J7 | Fast item scanning | POS/Serial | Missing | — | — | High |
| J8 | Serial scanning | POS/Serial | Missing | — | — | Critical |
| J9 | Serial purchase-to-sale trace | POS/Serial | Missing | — | — | Critical |
| J10 | Serial warehouse-to-warehouse | POS/Serial | Missing | — | — | Critical |
| J11 | Serial warranty claims | POS/Serial | Missing | — | — | Medium |
| J12 | Serial availability status | POS/Serial | Missing | — | — | Critical |
| J13 | Sold/unsold serial status | POS/Serial | Missing | — | — | Critical |
| J14 | Returned serial status | POS/Serial | Missing | — | — | Critical |
| J15 | Damaged/replaced serial | POS/Serial | Missing | — | — | Medium |
| J16 | Block serial wrong model | POS/Serial | Missing | No validation code in trader_app | — | Critical |
| **K — Production** |
| K1 | Jobs management | Production | Missing | No routes/APIs | — | Medium |
| K2 | Job costing | Production | Missing | — | — | Medium |
| K3 | Production management | Production | Missing | — | — | Medium |
| K4 | Production and assembly | Production | Missing | Item Bundle is not manufacturing | — | Medium |
| K5 | Bill of materials | Production | Missing | ERPNext BOM not exposed | — | Medium |
| K6 | Raw material issue | Production | Missing | Material Issue is generic only | — | Medium |
| K7 | Finished goods receipt | Production | Missing | — | — | Medium |
| K8 | Inventory issue notes | Production | Partially Implemented | Material Issue stock entry | — | Low |
| K9 | Production warehouse | Production | Missing | — | — | Medium |
| K10 | Assembly/disassembly | Production | Partially Implemented | `Item Bundle` custom DocType + `bundling.py` | Not full assembly workflow | Medium |
| K11 | Production cost posting | Production | Missing | — | — | Medium |
| K12 | Production reports | Production | Missing | — | — | Low |
| K13 | Serial/batch in production | Production | Missing | — | — | Medium |
| **L — Reports (checklist names)** |
| L1 | Daily affairs report | Reports | Missing | — | — | Medium |
| L2 | Daily general journal | Reports | Partially Implemented | GL report | Dedicated daily journal | Medium |
| L3 | Purchase reports | Reports | Implemented | Multiple in `reportDefinitions.ts` | — | — |
| L4 | Sale reports | Reports | Implemented | Multiple | — | — |
| L5 | Sales tax/VAT registers | Reports | Implemented | `tax-summary` report | — | — |
| L6 | Inventory purchase analysis | Reports | Implemented | `item-purchases` | — | — |
| L7 | Inventory sale analysis | Reports | Implemented | `top-selling-items`, etc. | — | — |
| L8 | Combined purchase/sale analysis | Reports | Partially Implemented | Separate reports | Combined dashboard | Low |
| L9 | Item-wise profit | Reports | Implemented | `sales-performance`, `customer-profitability` | — | — |
| L10 | Item cost/price statistics | Reports | Partially Implemented | Item detail + reports | Dedicated report thin | Low |
| L11 | Receivables aging | Reports | Implemented | — | — | — |
| L12 | Payables aging | Reports | Implemented | — | — | — |
| L13 | Cashbook | Reports | Partially Implemented | Cashflow report | — | Medium |
| L14 | Bank ledgers | Reports | Partially Implemented | GL with account filter | — | Medium |
| L15 | Account ledgers | Reports | Implemented | GL | — | — |
| L16 | Trial balance | Reports | Missing | — | — | High |
| L17 | Income statement / P&L | Reports | Implemented | `profit-and-loss` | — | — |
| L18 | Balance sheet | Reports | Missing | — | — | High |
| L19 | Inventory ledgers | Reports | Implemented | Stock movement / ledger | — | — |
| L20 | Inventory balances | Reports | Implemented | `stock-balance` | — | — |
| L21 | Warehouse-wise stock | Reports | Implemented | Stock balance + warehouse filter | — | — |
| L22 | Company-wise reports | Reports | Partially Implemented | Backend company param | No UI company picker | High |
| L23 | Consolidated multi-company reports | Reports | Missing | — | — | Critical |
| L24 | Currency-wise reports | Reports | Missing | — | — | High |
| L25 | Serial tracking report | Reports | Missing | — | — | Critical |
| L26 | Warranty claim report | Reports | Missing | — | — | Medium |
| L27 | PO tracking report | Reports | Implemented | `open-purchase-orders` | — | — |
| L28 | SO tracking report | Reports | Partially Implemented | Operations queues | Dedicated SO tracking report thin | Low |

# Seed Data Architecture

## Overview

The demo seed generates a wholesale trading / distribution dataset (roughly multi‑month horizon) driven by **`DemoInstaller`** in `trader_app/demo/installer/main.py`. Implementations live under `trader_app/demo/generators/` and configuration in `trader_app/demo/seed_engine/config.py`.

## Execution Order (actual dependency chain)

```
1.  CompanyGenerator         → Company, fiscal year, CoA-linked setup, warehouses,
                               payment terms, cost centers, baseline sales tax templates,
                               warehouse types / address template
2.  UserGenerator            → Trader role users + role profiles
3.  CustomerGenerator       → Customers / credit / territories
4.  SupplierGenerator        → Suppliers
5.  ItemGenerator            → Item groups, items, price lists (buy/sell)
6.  InventoryGenerator      → Opening stock (Material Receipt) across warehouses
7.  BundlesTransfersGenerator → Demo `Item Bundle` presets + Material Transfer Stock Entries
                               (Main ⇄ Secondary ⇄ Retail)
8.  QuotationGenerator       → Customer quotations (mixed draft / submitted); some are later
                               converted in SalesGenerator (Quotation → SO → SI)
9.  RequisitionsGenerator    → Sample `Material Request` + `Supplier Quotation`
10. PurchaseGenerator       → Purchase Invoices — mix of **standalone PI** and **PI-from-PO**
                               (linked `purchase_order` / `po_detail` lines for KPI realism)
11. SalesGenerator          → Sales Invoices — **direct SI** vs **SO → SI**
                               (`sales_order` / `so_detail`; optional quotation→SO linkage)
12. PaymentGenerator       → Payments on AR/AP behaviour from config fractions
13. FinancialGenerator      → JE / operating expenses
14. EnrichmentGenerator     → Reporting polish (sales persons, PO pipeline samples, taxes on
                               a subset of invoices, returns, item reorder, stock issues, etc.)

```

## Configuration (`DEMO_CONFIG`)

Key volume / mix keys (ranges are `(low, high)` tuples unless noted):

| Key | Purpose |
|-----|---------|
| `num_sales_invoices` | Target count of **submitted Sales Invoices** (direct + SO-linked combined). |
| `pct_sales_invoices_via_sales_order` | Fraction of those invoices spawned from a **submitted Sales Order** (remainder: direct invoices). |
| `pct_so_linked_from_quotation` | Of SO-backed flows, likelihood to originate from an eligible **submitted quotation** pending conversion. |
| `num_purchase_invoices` | Target count of **submitted Purchase Invoices**. |
| `pct_purchase_invoices_from_po` | Fraction seeded **from a submitted PO** (lines carry `purchase_order` / `po_detail`). Remaining PIs are standalone. |
| `num_quotations` | Quotations seeded (draft/submit mix via `fraction_quotation_submit`). |
| `num_material_requests` | Internal requisitions (`Material Request`, mostly Purchase purpose). |
| `num_supplier_quotations` | RFQ-style docs (`Supplier Quotation`), some referencing MRs. |
| `num_inter_warehouse_transfers` | Extra **Material Transfer** movements between the three seeded warehouses. |

Removed / unused legacy keys: **`num_sales_orders`** and **`num_purchase_orders`** (PO volume is implicit: PO-linked PIs plus enrichment extras).

### Generator Interface

Each generator subclasses `BaseGenerator` (`trader_app/demo/seed_engine/base.py`): `generate()`, `validate()`, `run()`, `run_validation()`, `depends_on` (documentation only).

## Item Groups & Pricing

See inline `item_groups`, `customer_segments`, and `supplier_types` in `DEMO_CONFIG` — unchanged conceptually from prior docs (margins / credit bands / supplier personas).

## Data Realism Constraints

Handled across generators where applicable:

1. Transaction dates clipped to ≤ site “today”.
2. Credit checks on outbound sales chains (approximate rolling outstanding).
3. Purchase PO dates precede PI posting where seeded from PO.
4. Warehouse inventory for transfers prefers bins with surplus stock.
5. Post-seed enrichment still back-fills salesperson / tax subsets / reorder rows for reports — see docstring on `EnrichmentGenerator`.

## Manual / UI-only seeds

**Punjab GST templates** (`trader_app.api.gst.seed_punjab_gst_templates`) remain a **desk/UI action** — not part of `install_demo`. Demo company PKR flows still rely on baseline templates from **CompanyGenerator** unless operators run GST seed.

## Operational Notes

Run:

```bash
bench --site <site> execute trader_app.demo.install_demo
bench --site <site> execute trader_app.demo.uninstall_demo
```

`uninstall_demo` removes company‑scoped transactional doctypes listed in `DemoInstaller.uninstall()`, deletes **Demo Pack\*** bundles, then clears global Item/Customer/Supplier masters (destructive wipe pattern).

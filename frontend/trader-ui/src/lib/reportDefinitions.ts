/**
 * Report definitions registry.
 *
 * Each entry describes one report: its API method, filters, KPI strip,
 * chart config, and table columns. The generic ReportView component
 * renders any report from its definition.
 */
import type { FilterDef } from '../components/reports/ReportFiltersBar';
import type { ColDef } from '../components/reports/ReportTable';
import type { KpiItem } from '../components/reports/ReportKpiStrip';
import { reportsApi } from './api';

// ─── Types ───────────────────────────────────────────────────────

export type ReportCategory = 'sales' | 'purchasing' | 'inventory' | 'finance';

export type ChartConfig = {
  type: 'bar' | 'stacked-bar' | 'line' | 'pie' | 'horizontal-bar';
  xKey: string;
  bars?: { dataKey: string; name: string; color?: string }[];
  title?: string;
  /** path in response.message to chart data; defaults to 'chart' */
  dataPath?: string;
};

export type ReportDef = {
  id: string;
  category: ReportCategory;
  title: string;
  description: string;
  fetch: (params: Record<string, any>) => Promise<any>;
  filters: FilterDef[];
  /** Build KPI items from the API response.message */
  kpis: (msg: any) => KpiItem[];
  chart?: ChartConfig;
  columns: ColDef[];
  /** Path inside response.message that holds the table rows; defaults to 'data' */
  dataPath?: string;
  /** Path inside response.message that holds total count; defaults to 'total' */
  totalPath?: string;
};

// ─── Helper to build date filters shared across most reports ─────

const fromDateFilter: FilterDef = { key: 'from_date', label: 'From', type: 'date' };
const toDateFilter: FilterDef = { key: 'to_date', label: 'To', type: 'date' };

function groupByFilter(options: string[]): FilterDef {
  return {
    key: 'group_by',
    label: 'Group By',
    type: 'select',
    options: options.map((o) => ({ label: o.charAt(0).toUpperCase() + o.slice(1).replace(/_/g, ' '), value: o })),
    defaultValue: options[0],
  };
}

// ─── Report Definitions ──────────────────────────────────────────

export const REPORTS: ReportDef[] = [
  // ──── SALES ─────────────────────────────────────────────────────
  {
    id: 'sales-performance',
    category: 'sales',
    title: 'Sales Performance',
    description: 'Revenue, cost, gross profit breakdown by month, customer, item or salesperson',
    fetch: (p) => reportsApi.getSalesPerformanceReport(p),
    filters: [
      fromDateFilter, toDateFilter,
      groupByFilter(['month', 'customer', 'item', 'item_group', 'brand', 'sales_person']),
    ],
    kpis: (m) => [
      { label: 'Net Sales', value: m.summary?.net_sales, format: 'currency', color: 'text-green-700' },
      { label: 'Gross Profit', value: m.summary?.gross_profit, format: 'currency', color: 'text-blue-700' },
      { label: 'Margin %', value: m.summary?.gross_margin_pct, format: 'percent' },
      { label: 'Total Qty', value: m.summary?.qty, format: 'number' },
    ],
    chart: { type: 'bar', xKey: 'period', bars: [
      { dataKey: 'net_sales', name: 'Net Sales', color: '#2563eb' },
      { dataKey: 'gross_profit', name: 'Gross Profit', color: '#059669' },
    ], title: 'Revenue & Profit', dataPath: 'chart' },
    columns: [
      { key: 'dimension', label: 'Group', width: '200px' },
      { key: 'net_sales', label: 'Net Sales', format: 'currency', align: 'right' },
      { key: 'cogs', label: 'Cost', format: 'currency', align: 'right' },
      { key: 'gross_profit', label: 'Gross Profit', format: 'currency', align: 'right' },
      { key: 'gross_margin_pct', label: 'Margin %', format: 'percent', align: 'right' },
      { key: 'qty', label: 'Qty', format: 'number', align: 'right' },
      { key: 'avg_selling_price', label: 'Avg Price', format: 'currency', align: 'right' },
    ],
  },
  {
    id: 'customer-profitability',
    category: 'sales',
    title: 'Customer Profitability',
    description: 'Revenue, cost, GP margin and credit utilization per customer',
    fetch: (p) => reportsApi.getCustomerProfitabilityReport(p),
    filters: [fromDateFilter, toDateFilter],
    kpis: (m) => [
      { label: 'Customers', value: m.total, format: 'number' },
      { label: 'Total Revenue', value: m.data?.reduce((s: number, r: any) => s + (r.revenue || 0), 0), format: 'currency', color: 'text-green-700' },
    ],
    chart: { type: 'horizontal-bar', xKey: 'customer_name', bars: [
      { dataKey: 'revenue', name: 'Revenue', color: '#2563eb' },
      { dataKey: 'gross_profit', name: 'Gross Profit', color: '#059669' },
    ], title: 'Top Customers by Revenue', dataPath: 'data' },
    columns: [
      { key: 'customer_name', label: 'Customer', width: '200px' },
      { key: 'revenue', label: 'Revenue', format: 'currency', align: 'right' },
      { key: 'cogs', label: 'Cost', format: 'currency', align: 'right' },
      { key: 'gross_profit', label: 'Gross Profit', format: 'currency', align: 'right' },
      { key: 'gross_margin_pct', label: 'Margin %', format: 'percent', align: 'right' },
      { key: 'outstanding_amount', label: 'Outstanding', format: 'currency', align: 'right' },
      { key: 'credit_utilization_pct', label: 'Credit Util %', format: 'percent', align: 'right' },
    ],
  },
  {
    id: 'collection-efficiency',
    category: 'sales',
    title: 'Collection Efficiency',
    description: 'Billed vs collected amounts and efficiency percentage by month or customer',
    fetch: (p) => reportsApi.getCollectionEfficiencyReport(p),
    filters: [fromDateFilter, toDateFilter, groupByFilter(['month', 'customer'])],
    kpis: (m) => [
      { label: 'Total Billed', value: m.summary?.total_billed, format: 'currency' },
      { label: 'Total Collected', value: m.summary?.total_collected, format: 'currency', color: 'text-green-700' },
      { label: 'Efficiency', value: m.summary?.overall_efficiency_pct, format: 'percent', color: 'text-blue-700' },
    ],
    chart: { type: 'bar', xKey: 'dimension', bars: [
      { dataKey: 'billed_amount', name: 'Billed', color: '#2563eb' },
      { dataKey: 'collected_amount', name: 'Collected', color: '#059669' },
    ], title: 'Billed vs Collected', dataPath: 'data' },
    columns: [
      { key: 'dimension', label: 'Period / Customer', width: '200px' },
      { key: 'billed_amount', label: 'Billed', format: 'currency', align: 'right' },
      { key: 'collected_amount', label: 'Collected', format: 'currency', align: 'right' },
      { key: 'efficiency_pct', label: 'Efficiency %', format: 'percent', align: 'right' },
    ],
  },

  // ──── PURCHASING ────────────────────────────────────────────────
  {
    id: 'supplier-scorecard',
    category: 'purchasing',
    title: 'Supplier Scorecard',
    description: 'Purchase value, quantity, average rate, and outstanding per supplier',
    fetch: (p) => reportsApi.getSupplierScorecardReport(p),
    filters: [fromDateFilter, toDateFilter],
    kpis: (m) => [
      { label: 'Suppliers', value: m.total, format: 'number' },
      { label: 'Total Purchases', value: m.data?.reduce((s: number, r: any) => s + (r.purchase_value || 0), 0), format: 'currency', color: 'text-blue-700' },
    ],
    chart: { type: 'horizontal-bar', xKey: 'supplier_name', bars: [
      { dataKey: 'purchase_value', name: 'Purchase Value', color: '#059669' },
    ], title: 'Top Suppliers by Value', dataPath: 'data' },
    columns: [
      { key: 'supplier_name', label: 'Supplier', width: '200px' },
      { key: 'purchase_value', label: 'Value', format: 'currency', align: 'right' },
      { key: 'total_qty', label: 'Qty', format: 'number', align: 'right' },
      { key: 'avg_rate', label: 'Avg Rate', format: 'currency', align: 'right' },
      { key: 'payable_outstanding', label: 'Outstanding', format: 'currency', align: 'right' },
    ],
  },
  {
    id: 'purchase-price-variance',
    category: 'purchasing',
    title: 'Purchase Price Variance',
    description: 'Min, max, avg rate and price spread per item/supplier',
    fetch: (p) => reportsApi.getPurchasePriceVarianceReport(p),
    filters: [fromDateFilter, toDateFilter],
    kpis: (m) => [
      { label: 'Items Tracked', value: m.total, format: 'number' },
    ],
    columns: [
      { key: 'item_name', label: 'Item' },
      { key: 'supplier_name', label: 'Supplier' },
      { key: 'total_qty', label: 'Qty', format: 'number', align: 'right' },
      { key: 'min_rate', label: 'Min Rate', format: 'currency', align: 'right' },
      { key: 'max_rate', label: 'Max Rate', format: 'currency', align: 'right' },
      { key: 'avg_rate', label: 'Avg Rate', format: 'currency', align: 'right' },
      { key: 'price_spread', label: 'Spread', format: 'currency', align: 'right' },
      { key: 'variance_pct', label: 'Variance %', format: 'percent', align: 'right' },
    ],
  },
  {
    id: 'open-purchase-orders',
    category: 'purchasing',
    title: 'Open Purchase Orders',
    description: 'Pending receipt items and overdue deliveries',
    fetch: (p) => reportsApi.getOpenPurchaseOrdersReport(p),
    filters: [fromDateFilter, toDateFilter],
    kpis: (m) => [
      { label: 'Open Items', value: m.total, format: 'number' },
      { label: 'Pending Value', value: m.summary?.pending_value, format: 'currency', color: 'text-orange-600' },
      { label: 'Overdue Items', value: m.summary?.overdue_count, format: 'number', color: 'text-red-600' },
    ],
    columns: [
      { key: 'purchase_order', label: 'PO #' },
      { key: 'supplier_name', label: 'Supplier' },
      { key: 'item_name', label: 'Item' },
      { key: 'qty', label: 'Ordered', format: 'number', align: 'right' },
      { key: 'received_qty', label: 'Received', format: 'number', align: 'right' },
      { key: 'pending_qty', label: 'Pending', format: 'number', align: 'right' },
      { key: 'pending_value', label: 'Pending Value', format: 'currency', align: 'right' },
      { key: 'required_date', label: 'Due', format: 'date' },
      { key: 'delay_days', label: 'Delay', format: 'number', align: 'right' },
    ],
  },

  // ──── INVENTORY ─────────────────────────────────────────────────
  {
    id: 'stock-aging',
    category: 'inventory',
    title: 'Stock Aging',
    description: 'Inventory value by age bucket (0-30, 31-60, 61-90, 91-180, 180+ days)',
    fetch: (p) => reportsApi.getStockAgingReport(p),
    filters: [{ key: 'warehouse', label: 'Warehouse', type: 'text' }],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: '0–30 Days', value: s['0-30'], format: 'currency' },
        { label: '31–60 Days', value: s['31-60'], format: 'currency' },
        { label: '61–90 Days', value: s['61-90'], format: 'currency', color: 'text-yellow-600' },
        { label: '91–180 Days', value: s['91-180'], format: 'currency', color: 'text-orange-600' },
        { label: '180+ Days', value: s['180+'], format: 'currency', color: 'text-red-600' },
        { label: 'Total Value', value: s.total_value, format: 'currency', color: 'text-gray-900' },
      ];
    },
    chart: { type: 'pie', xKey: 'bucket', bars: [{ dataKey: 'value', name: 'Value' }], title: 'Value by Age Bucket', dataPath: 'chart' },
    columns: [
      { key: 'item_name', label: 'Item' },
      { key: 'warehouse', label: 'Warehouse' },
      { key: 'qty', label: 'Qty', format: 'number', align: 'right' },
      { key: 'valuation_rate', label: 'Rate', format: 'currency', align: 'right' },
      { key: 'stock_value', label: 'Value', format: 'currency', align: 'right' },
      { key: 'age_days', label: 'Age (Days)', format: 'number', align: 'right' },
      { key: 'age_bucket', label: 'Bucket' },
    ],
  },
  {
    id: 'inventory-movement',
    category: 'inventory',
    title: 'Inventory Movement',
    description: 'Fast, slow and non-moving item classification based on sales velocity',
    fetch: (p) => reportsApi.getInventoryMovementReport(p),
    filters: [{ key: 'warehouse', label: 'Warehouse', type: 'text' }, { key: 'classification', label: 'Class', type: 'select', options: [
      { label: 'Fast', value: 'fast' }, { label: 'Slow', value: 'slow' }, { label: 'Non-moving', value: 'non_moving' },
    ]}],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Fast Moving', value: s.fast, format: 'number', color: 'text-green-600' },
        { label: 'Slow Moving', value: s.slow, format: 'number', color: 'text-yellow-600' },
        { label: 'Non-Moving', value: s.non_moving, format: 'number', color: 'text-red-600' },
        { label: 'Total Stock Value', value: s.total_stock_value, format: 'currency' },
      ];
    },
    chart: { type: 'pie', xKey: 'classification', bars: [{ dataKey: 'count', name: 'Items' }], title: 'Movement Classification', dataPath: 'chart' },
    columns: [
      { key: 'item_name', label: 'Item' },
      { key: 'warehouse', label: 'Warehouse' },
      { key: 'actual_qty', label: 'Stock Qty', format: 'number', align: 'right' },
      { key: 'stock_value', label: 'Value', format: 'currency', align: 'right' },
      { key: 'sold_last_30', label: '30d Sales', format: 'number', align: 'right' },
      { key: 'sold_last_90', label: '90d Sales', format: 'number', align: 'right' },
      { key: 'classification', label: 'Class' },
    ],
  },
  {
    id: 'serial-trace',
    category: 'inventory',
    title: 'Serial Trace',
    description: 'Serial numbers with status, warehouse, and linked purchase/delivery documents',
    fetch: (p) => reportsApi.getSerialTraceReport(p),
    filters: [
      { key: 'serial_no', label: 'Serial', type: 'text' },
      { key: 'item_code', label: 'Item', type: 'text' },
      { key: 'status', label: 'Status', type: 'text' },
    ],
    kpis: (m) => {
      const s = m.summary || {};
      const byStatus = s.by_status || {};
      const entries = Object.entries(byStatus) as [string, number][];
      const kpis: KpiItem[] = [
        { label: 'Serials', value: s.total_serials, format: 'number' },
      ];
      for (const [status, count] of entries.slice(0, 4)) {
        kpis.push({ label: status, value: count, format: 'number' });
      }
      return kpis;
    },
    columns: [
      { key: 'serial_no', label: 'Serial', width: '160px' },
      { key: 'item_code', label: 'Item' },
      { key: 'item_name', label: 'Name', width: '180px' },
      { key: 'warehouse', label: 'Warehouse' },
      { key: 'status', label: 'Status' },
      { key: 'purchase_document_no', label: 'Purchase Doc' },
      { key: 'delivery_document_no', label: 'Delivery Doc' },
    ],
  },
  {
    id: 'reorder',
    category: 'inventory',
    title: 'Reorder Report',
    description: 'Items at or below reorder level with suggested reorder quantities',
    fetch: (p) => reportsApi.getReorderReport(p),
    filters: [{ key: 'warehouse', label: 'Warehouse', type: 'text' }, { key: 'status', label: 'Status', type: 'select', options: [
      { label: 'Stockout', value: 'stockout' }, { label: 'Critical', value: 'critical' }, { label: 'Low', value: 'low' },
    ]}],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Stockout', value: s.stockout, format: 'number', color: 'text-red-600' },
        { label: 'Critical', value: s.critical, format: 'number', color: 'text-orange-600' },
        { label: 'Low Stock', value: s.low, format: 'number', color: 'text-yellow-600' },
        { label: 'Healthy', value: s.healthy, format: 'number', color: 'text-green-600' },
      ];
    },
    columns: [
      { key: 'item_name', label: 'Item' },
      { key: 'warehouse', label: 'Warehouse' },
      { key: 'actual_qty', label: 'On Hand', format: 'number', align: 'right' },
      { key: 'reorder_level', label: 'Reorder Lvl', format: 'number', align: 'right' },
      { key: 'reorder_qty', label: 'Reorder Qty', format: 'number', align: 'right' },
      { key: 'days_of_cover', label: 'Days Cover', format: 'number', align: 'right' },
      { key: 'avg_daily_sales', label: 'Avg Daily', format: 'number', align: 'right' },
      { key: 'suggested_reorder', label: 'Suggested', format: 'number', align: 'right' },
      { key: 'stock_status', label: 'Status' },
    ],
  },

  // ──── FINANCE ───────────────────────────────────────────────────
  {
    id: 'receivable-aging-detail',
    category: 'finance',
    title: 'Receivable Aging (Invoices)',
    description: 'Invoice-level accounts receivable aging with due-date buckets',
    fetch: (p) => reportsApi.getReceivableAgingInvoiceDetail(p),
    filters: [{ key: 'customer', label: 'Customer', type: 'text' }],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: '0–30 Days', value: s['0-30'], format: 'currency' },
        { label: '31–60 Days', value: s['31-60'], format: 'currency', color: 'text-yellow-600' },
        { label: '61–90 Days', value: s['61-90'], format: 'currency', color: 'text-orange-600' },
        { label: '90+ Days', value: s['90+'], format: 'currency', color: 'text-red-600' },
        { label: 'Total Outstanding', value: s.total, format: 'currency', color: 'text-red-700' },
      ];
    },
    columns: [
      { key: 'invoice', label: 'Invoice' },
      { key: 'customer_name', label: 'Customer' },
      { key: 'posting_date', label: 'Date', format: 'date' },
      { key: 'due_date', label: 'Due', format: 'date' },
      { key: 'grand_total', label: 'Total', format: 'currency', align: 'right' },
      { key: 'outstanding_amount', label: 'Outstanding', format: 'currency', align: 'right' },
      { key: 'age_days', label: 'Age', format: 'number', align: 'right' },
      { key: 'age_bucket', label: 'Bucket' },
    ],
  },
  {
    id: 'payable-aging-detail',
    category: 'finance',
    title: 'Payable Aging (Invoices)',
    description: 'Invoice-level accounts payable aging with due-date buckets',
    fetch: (p) => reportsApi.getPayableAgingInvoiceDetail(p),
    filters: [{ key: 'supplier', label: 'Supplier', type: 'text' }],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: '0–30 Days', value: s['0-30'], format: 'currency' },
        { label: '31–60 Days', value: s['31-60'], format: 'currency', color: 'text-yellow-600' },
        { label: '61–90 Days', value: s['61-90'], format: 'currency', color: 'text-orange-600' },
        { label: '90+ Days', value: s['90+'], format: 'currency', color: 'text-red-600' },
        { label: 'Total Payable', value: s.total, format: 'currency', color: 'text-orange-700' },
      ];
    },
    columns: [
      { key: 'invoice', label: 'Invoice' },
      { key: 'supplier_name', label: 'Supplier' },
      { key: 'posting_date', label: 'Date', format: 'date' },
      { key: 'due_date', label: 'Due', format: 'date' },
      { key: 'grand_total', label: 'Total', format: 'currency', align: 'right' },
      { key: 'outstanding_amount', label: 'Outstanding', format: 'currency', align: 'right' },
      { key: 'age_days', label: 'Age', format: 'number', align: 'right' },
      { key: 'age_bucket', label: 'Bucket' },
    ],
  },
  {
    id: 'tax-summary',
    category: 'finance',
    title: 'Tax Summary',
    description: 'Output tax (sales) vs input tax (purchases) with net tax payable',
    fetch: (p) => reportsApi.getTaxSummaryReport(p),
    filters: [fromDateFilter, toDateFilter],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Output Tax', value: s.total_output_tax, format: 'currency', color: 'text-red-600' },
        { label: 'Input Tax', value: s.total_input_tax, format: 'currency', color: 'text-green-600' },
        { label: 'Net Tax Payable', value: s.net_tax_payable, format: 'currency', color: 'text-blue-700' },
      ];
    },
    chart: { type: 'bar', xKey: 'account_head', bars: [
      { dataKey: 'output_tax', name: 'Output Tax', color: '#dc2626' },
      { dataKey: 'input_tax', name: 'Input Tax', color: '#059669' },
    ], title: 'Tax by Account', dataPath: 'data' },
    columns: [
      { key: 'account_head', label: 'Tax Account' },
      { key: 'output_tax', label: 'Output Tax', format: 'currency', align: 'right' },
      { key: 'input_tax', label: 'Input Tax', format: 'currency', align: 'right' },
      { key: 'net_tax', label: 'Net Tax', format: 'currency', align: 'right' },
    ],
  },

  // ══════════════════════════════════════════════════════════════
  // PHASE 2 REPORTS
  // ══════════════════════════════════════════════════════════════

  // ──── SALES (phase 2) ───────────────────────────────────────────
  {
    id: 'daily-sales',
    category: 'sales',
    title: 'Daily Sales',
    description: 'Day-by-day revenue, invoice count and collection breakdown',
    fetch: (p) => reportsApi.getDailySalesReport(p),
    filters: [fromDateFilter, toDateFilter],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Total Revenue', value: s.total_revenue, format: 'currency', color: 'text-green-700' },
        { label: 'Total Invoices', value: s.total_invoices, format: 'number' },
        { label: 'Avg Daily Revenue', value: s.avg_daily_revenue, format: 'currency', color: 'text-blue-700' },
        { label: 'Avg Invoice Value', value: s.avg_invoice_value, format: 'currency' },
      ];
    },
    chart: { type: 'bar', xKey: 'label', bars: [
      { dataKey: 'revenue', name: 'Revenue', color: '#2563eb' },
    ], title: 'Daily Revenue Trend', dataPath: 'chart' },
    columns: [
      { key: 'date', label: 'Date', format: 'date' },
      { key: 'invoice_count', label: 'Invoices', format: 'number', align: 'right' },
      { key: 'grand_total', label: 'Revenue', format: 'currency', align: 'right' },
      { key: 'net_total', label: 'Net Total', format: 'currency', align: 'right' },
      { key: 'collected', label: 'Collected', format: 'currency', align: 'right' },
      { key: 'outstanding', label: 'Outstanding', format: 'currency', align: 'right' },
    ],
  },
  {
    id: 'sales-returns',
    category: 'sales',
    title: 'Sales Returns',
    description: 'Credit notes / returns analysis by customer',
    fetch: (p) => reportsApi.getSalesReturnReport(p),
    filters: [fromDateFilter, toDateFilter, { key: 'customer', label: 'Customer', type: 'text' }],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Total Returns', value: s.total_returns, format: 'number', color: 'text-red-600' },
        { label: 'Return Value', value: s.total_return_value, format: 'currency', color: 'text-red-700' },
        { label: 'Customers w/ Returns', value: s.customers_with_returns, format: 'number' },
      ];
    },
    columns: [
      { key: 'customer_name', label: 'Customer' },
      { key: 'return_count', label: 'Returns', format: 'number', align: 'right' },
      { key: 'return_value', label: 'Return Value', format: 'currency', align: 'right' },
      { key: 'net_return_value', label: 'Net Value', format: 'currency', align: 'right' },
    ],
  },
  {
    id: 'salesperson-performance',
    category: 'sales',
    title: 'Salesperson Performance',
    description: 'Revenue, gross profit, margins and contribution per salesperson',
    fetch: (p) => reportsApi.getSalespersonPerformanceReport(p),
    filters: [fromDateFilter, toDateFilter],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Salespersons', value: s.total_salespersons, format: 'number' },
        { label: 'Total Revenue', value: s.total_revenue, format: 'currency', color: 'text-green-700' },
        { label: 'Total GP', value: s.total_gp, format: 'currency', color: 'text-blue-700' },
        { label: 'Avg Margin', value: s.avg_margin, format: 'percent' },
      ];
    },
    chart: { type: 'horizontal-bar', xKey: 'sales_person', bars: [
      { dataKey: 'revenue', name: 'Revenue', color: '#2563eb' },
      { dataKey: 'gross_profit', name: 'Gross Profit', color: '#059669' },
    ], title: 'Salesperson Revenue', dataPath: 'data' },
    columns: [
      { key: 'sales_person', label: 'Salesperson' },
      { key: 'revenue', label: 'Revenue', format: 'currency', align: 'right' },
      { key: 'gross_profit', label: 'Gross Profit', format: 'currency', align: 'right' },
      { key: 'gp_margin', label: 'Margin %', format: 'percent', align: 'right' },
      { key: 'invoice_count', label: 'Invoices', format: 'number', align: 'right' },
      { key: 'customer_count', label: 'Customers', format: 'number', align: 'right' },
      { key: 'revenue_share', label: 'Share %', format: 'percent', align: 'right' },
    ],
  },
  {
    id: 'top-selling-items',
    category: 'sales',
    title: 'Top Selling Items',
    description: 'Best selling items ranked by revenue with quantity and invoice count',
    fetch: (p) => reportsApi.getItemSalesReport(p),
    filters: [fromDateFilter, toDateFilter, { key: 'item_group', label: 'Item Group', type: 'text' }],
    kpis: (m) => [
      { label: 'Items', value: m.total, format: 'number' },
    ],
    chart: { type: 'horizontal-bar', xKey: 'item_name', bars: [
      { dataKey: 'total_amount', name: 'Revenue', color: '#2563eb' },
    ], title: 'Top Items by Revenue', dataPath: 'data' },
    columns: [
      { key: 'item_name', label: 'Item' },
      { key: 'item_group', label: 'Group' },
      { key: 'total_qty', label: 'Qty Sold', format: 'number', align: 'right' },
      { key: 'total_amount', label: 'Revenue', format: 'currency', align: 'right' },
      { key: 'invoice_count', label: 'Invoices', format: 'number', align: 'right' },
    ],
  },

  // ──── PURCHASING (phase 2) ──────────────────────────────────────
  {
    id: 'purchase-returns',
    category: 'purchasing',
    title: 'Purchase Returns',
    description: 'Debit notes / returns analysis by supplier',
    fetch: (p) => reportsApi.getPurchaseReturnReport(p),
    filters: [fromDateFilter, toDateFilter, { key: 'supplier', label: 'Supplier', type: 'text' }],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Total Returns', value: s.total_returns, format: 'number', color: 'text-red-600' },
        { label: 'Return Value', value: s.total_return_value, format: 'currency', color: 'text-red-700' },
        { label: 'Suppliers w/ Returns', value: s.suppliers_with_returns, format: 'number' },
      ];
    },
    columns: [
      { key: 'supplier_name', label: 'Supplier' },
      { key: 'return_count', label: 'Returns', format: 'number', align: 'right' },
      { key: 'return_value', label: 'Return Value', format: 'currency', align: 'right' },
      { key: 'net_return_value', label: 'Net Value', format: 'currency', align: 'right' },
    ],
  },
  {
    id: 'item-purchases',
    category: 'purchasing',
    title: 'Item-wise Purchases',
    description: 'Purchase breakdown by item — qty, value, avg rate, supplier count',
    fetch: (p) => reportsApi.getItemPurchaseReport(p),
    filters: [fromDateFilter, toDateFilter, { key: 'item_group', label: 'Item Group', type: 'text' }, { key: 'supplier', label: 'Supplier', type: 'text' }],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Unique Items', value: s.unique_items, format: 'number' },
        { label: 'Total Value', value: s.total_value, format: 'currency', color: 'text-blue-700' },
        { label: 'Total Qty', value: s.total_qty, format: 'number' },
      ];
    },
    chart: { type: 'horizontal-bar', xKey: 'item_name', bars: [
      { dataKey: 'total_amount', name: 'Purchase Value', color: '#059669' },
    ], title: 'Top Purchased Items', dataPath: 'data' },
    columns: [
      { key: 'item_name', label: 'Item' },
      { key: 'item_group', label: 'Group' },
      { key: 'total_qty', label: 'Qty', format: 'number', align: 'right' },
      { key: 'total_amount', label: 'Value', format: 'currency', align: 'right' },
      { key: 'avg_rate', label: 'Avg Rate', format: 'currency', align: 'right' },
      { key: 'min_rate', label: 'Min Rate', format: 'currency', align: 'right' },
      { key: 'max_rate', label: 'Max Rate', format: 'currency', align: 'right' },
      { key: 'supplier_count', label: 'Suppliers', format: 'number', align: 'right' },
    ],
  },

  // ──── INVENTORY (phase 2) ───────────────────────────────────────
  {
    id: 'stock-balance',
    category: 'inventory',
    title: 'Stock Balance',
    description: 'Warehouse-wise stock quantities and valuation',
    fetch: (p) => reportsApi.getStockBalanceReport(p),
    filters: [{ key: 'warehouse', label: 'Warehouse', type: 'text' }, { key: 'item_group', label: 'Item Group', type: 'text' }],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Unique Items', value: s.unique_items, format: 'number' },
        { label: 'Warehouses', value: s.warehouses, format: 'number' },
        { label: 'Total Qty', value: s.total_qty, format: 'number' },
        { label: 'Total Value', value: s.total_value, format: 'currency', color: 'text-green-700' },
      ];
    },
    columns: [
      { key: 'item_name', label: 'Item' },
      { key: 'item_group', label: 'Group' },
      { key: 'warehouse', label: 'Warehouse' },
      { key: 'actual_qty', label: 'Actual Qty', format: 'number', align: 'right' },
      { key: 'reserved_qty', label: 'Reserved', format: 'number', align: 'right' },
      { key: 'ordered_qty', label: 'Ordered', format: 'number', align: 'right' },
      { key: 'stock_value', label: 'Value', format: 'currency', align: 'right' },
      { key: 'valuation_rate', label: 'Rate', format: 'currency', align: 'right' },
    ],
  },

  // ──── FINANCE (phase 2) ─────────────────────────────────────────
  {
    id: 'consolidated-company-summary',
    category: 'finance',
    title: 'Multi-Company Summary',
    description: 'Sales, purchases, receivables, payables and stock value across all companies you can access',
    fetch: (p) => reportsApi.getConsolidatedCompanySummary(p),
    filters: [fromDateFilter, toDateFilter],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Companies', value: s.company_count, format: 'number' },
        { label: 'Total Sales', value: s.sales, format: 'currency', color: 'text-green-700' },
        { label: 'Total Purchases', value: s.purchases, format: 'currency', color: 'text-orange-600' },
        { label: 'Receivables', value: s.receivables, format: 'currency', color: 'text-blue-700' },
        { label: 'Payables', value: s.payables, format: 'currency', color: 'text-red-600' },
        { label: 'Stock Value', value: s.stock_value, format: 'currency' },
      ];
    },
    chart: {
      type: 'bar',
      xKey: 'company',
      bars: [
        { dataKey: 'sales', name: 'Sales', color: '#2563eb' },
        { dataKey: 'purchases', name: 'Purchases', color: '#ea580c' },
      ],
      title: 'Sales vs Purchases by Company',
      dataPath: 'data',
    },
    columns: [
      { key: 'company', label: 'Company', width: '180px' },
      { key: 'currency', label: 'Currency', width: '80px' },
      { key: 'sales', label: 'Sales', format: 'currency', align: 'right' },
      { key: 'purchases', label: 'Purchases', format: 'currency', align: 'right' },
      { key: 'receivables', label: 'Receivables', format: 'currency', align: 'right' },
      { key: 'payables', label: 'Payables', format: 'currency', align: 'right' },
      { key: 'stock_value', label: 'Stock Value', format: 'currency', align: 'right' },
    ],
  },
  {
    id: 'profit-and-loss',
    category: 'finance',
    title: 'Profit & Loss',
    description: 'Income, COGS, gross profit, expenses and net profit summary',
    fetch: (p) => reportsApi.getProfitLossSummaryReport(p),
    filters: [fromDateFilter, toDateFilter],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Total Income', value: s.total_income, format: 'currency', color: 'text-green-700' },
        { label: 'COGS', value: s.cogs, format: 'currency', color: 'text-orange-600' },
        { label: 'Gross Profit', value: s.gross_profit, format: 'currency', color: 'text-blue-700' },
        { label: 'GP Margin', value: s.gp_margin, format: 'percent' },
        { label: 'Total Expenses', value: s.total_expense, format: 'currency', color: 'text-red-600' },
        { label: 'Net Profit', value: s.net_profit, format: 'currency', color: s.net_profit >= 0 ? 'text-green-700' : 'text-red-700' },
      ];
    },
    columns: [
      { key: 'account', label: 'Account' },
      { key: 'type', label: 'Type' },
      { key: 'parent_account', label: 'Parent Account' },
      { key: 'amount', label: 'Amount', format: 'currency', align: 'right' },
    ],
  },
  {
    id: 'cashflow',
    category: 'finance',
    title: 'Cash Flow',
    description: 'Payment entries — inflow vs outflow by month or payment type',
    fetch: (p) => reportsApi.getCashflowReport(p),
    filters: [fromDateFilter, toDateFilter, groupByFilter(['month', 'payment_type'])],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Total Inflow', value: s.total_inflow, format: 'currency', color: 'text-green-700' },
        { label: 'Total Outflow', value: s.total_outflow, format: 'currency', color: 'text-red-600' },
        { label: 'Net Cash Flow', value: s.net_flow, format: 'currency', color: s.net_flow >= 0 ? 'text-green-700' : 'text-red-700' },
        { label: 'Total Entries', value: s.total_entries, format: 'number' },
      ];
    },
    chart: { type: 'bar', xKey: 'label', bars: [
      { dataKey: 'inflow', name: 'Inflow', color: '#059669' },
      { dataKey: 'outflow', name: 'Outflow', color: '#dc2626' },
    ], title: 'Cash Inflow vs Outflow', dataPath: 'chart' },
    columns: [
      { key: 'label', label: 'Period / Type' },
      { key: 'inflow', label: 'Inflow', format: 'currency', align: 'right' },
      { key: 'outflow', label: 'Outflow', format: 'currency', align: 'right' },
      { key: 'net_flow', label: 'Net Flow', format: 'currency', align: 'right' },
      { key: 'transfers', label: 'Transfers', format: 'currency', align: 'right' },
      { key: 'entry_count', label: 'Entries', format: 'number', align: 'right' },
    ],
  },
  {
    id: 'trial-balance',
    category: 'finance',
    title: 'Trial Balance',
    description: 'Opening, period debit/credit, and closing balances per GL account',
    fetch: (p) => reportsApi.getTrialBalanceReport(p),
    filters: [fromDateFilter, toDateFilter],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Period Debit', value: s.debit, format: 'currency' },
        { label: 'Period Credit', value: s.credit, format: 'currency' },
        { label: 'Closing Debit', value: s.closing_debit, format: 'currency' },
        { label: 'Closing Credit', value: s.closing_credit, format: 'currency' },
        {
          label: 'Difference',
          value: s.difference,
          format: 'currency',
          color: s.is_balanced ? 'text-green-700' : 'text-red-600',
        },
      ];
    },
    columns: [
      { key: 'account', label: 'Account', width: '140px' },
      { key: 'account_name', label: 'Name', width: '180px' },
      { key: 'root_type', label: 'Type' },
      { key: 'opening_debit', label: 'Open Dr', format: 'currency', align: 'right' },
      { key: 'opening_credit', label: 'Open Cr', format: 'currency', align: 'right' },
      { key: 'debit', label: 'Debit', format: 'currency', align: 'right' },
      { key: 'credit', label: 'Credit', format: 'currency', align: 'right' },
      { key: 'closing_debit', label: 'Close Dr', format: 'currency', align: 'right' },
      { key: 'closing_credit', label: 'Close Cr', format: 'currency', align: 'right' },
    ],
  },
  {
    id: 'fx-gain-loss',
    category: 'finance',
    title: 'FX Gain / Loss (Unrealized)',
    description: 'Open foreign-currency receivables and payables revalued at current exchange rates',
    fetch: (p) => reportsApi.getFxGainLossReport({ ...p, as_on_date: p.as_on_date || p.to_date }),
    filters: [{ key: 'as_on_date', label: 'As on', type: 'date' }],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Total unrealized', value: s.total_unrealized_gain_loss, format: 'currency', color: s.total_unrealized_gain_loss >= 0 ? 'text-green-700' : 'text-red-600' },
        { label: 'Receivables', value: s.receivable_gain_loss, format: 'currency' },
        { label: 'Payables', value: s.payable_gain_loss, format: 'currency' },
        { label: 'Open docs', value: s.open_documents, format: 'number' },
      ];
    },
    columns: [
      { key: 'exposure_type', label: 'Type' },
      { key: 'doctype', label: 'Document' },
      { key: 'name', label: 'Name', width: '140px' },
      { key: 'party', label: 'Party' },
      { key: 'currency', label: 'CCY' },
      { key: 'outstanding_fcy', label: 'Outstanding (FCY)', format: 'currency', align: 'right' },
      { key: 'book_rate', label: 'Book rate', format: 'number', align: 'right' },
      { key: 'current_rate', label: 'Current rate', format: 'number', align: 'right' },
      { key: 'book_base', label: 'Book (base)', format: 'currency', align: 'right' },
      { key: 'current_base', label: 'Current (base)', format: 'currency', align: 'right' },
      { key: 'unrealized_gain_loss', label: 'Unrealized G/L', format: 'currency', align: 'right' },
    ],
  },
  {
    id: 'balance-sheet',
    category: 'finance',
    title: 'Balance Sheet',
    description: 'Assets, liabilities, and equity as of a selected date',
    fetch: (p) => reportsApi.getBalanceSheetReport({ ...p, as_on_date: p.as_on_date || p.to_date }),
    filters: [{ key: 'as_on_date', label: 'As on', type: 'date' }],
    kpis: (m) => {
      const s = m.summary || {};
      return [
        { label: 'Total Assets', value: s.total_assets, format: 'currency', color: 'text-green-700' },
        { label: 'Total Liabilities', value: s.total_liabilities, format: 'currency', color: 'text-orange-600' },
        { label: 'Total Equity', value: s.total_equity, format: 'currency', color: 'text-blue-700' },
        {
          label: 'A − L − E',
          value: s.accounting_equation_diff,
          format: 'currency',
          color: s.is_balanced ? 'text-green-700' : 'text-red-600',
        },
      ];
    },
    columns: [
      { key: 'root_type', label: 'Section' },
      { key: 'account', label: 'Account', width: '140px' },
      { key: 'account_name', label: 'Name', width: '200px' },
      { key: 'parent_account', label: 'Parent' },
      { key: 'balance', label: 'Balance', format: 'currency', align: 'right' },
    ],
  },
  {
    id: 'general-ledger',
    category: 'finance',
    title: 'General Ledger',
    description: 'Full general ledger with debit/credit entries',
    fetch: (p) => reportsApi.getGeneralLedger(p),
    filters: [fromDateFilter, toDateFilter, { key: 'account', label: 'Account', type: 'text' }, { key: 'party', label: 'Party', type: 'text' }],
    kpis: (m) => [
      { label: 'Entries', value: m.total, format: 'number' },
    ],
    columns: [
      { key: 'posting_date', label: 'Date', format: 'date' },
      { key: 'account', label: 'Account' },
      { key: 'party_type', label: 'Party Type' },
      { key: 'party', label: 'Party' },
      { key: 'debit', label: 'Debit', format: 'currency', align: 'right' },
      { key: 'credit', label: 'Credit', format: 'currency', align: 'right' },
      { key: 'voucher_type', label: 'Voucher Type' },
      { key: 'voucher_no', label: 'Voucher No' },
    ],
  },

  // ──── FINANCE (phase 3 — ledgers) ──────────────────────────────
  {
    id: 'customer-ledger',
    category: 'finance',
    title: 'Customer Ledger',
    description: 'GL entries and running balance for a specific customer',
    fetch: async (p) => {
      const res = await reportsApi.getCustomerLedger(p.customer || '', p);
      // Legacy endpoint returns flat array — normalize
      const rows = res.data.message || [];
      return { data: { message: { data: rows, total: rows.length } } };
    },
    filters: [
      { key: 'customer', label: 'Customer', type: 'text' },
      fromDateFilter, toDateFilter,
    ],
    kpis: (m) => {
      const rows = m.data || [];
      const totalDebit = rows.reduce((s: number, r: any) => s + (r.debit || 0), 0);
      const totalCredit = rows.reduce((s: number, r: any) => s + (r.credit || 0), 0);
      return [
        { label: 'Entries', value: rows.length, format: 'number' },
        { label: 'Total Debit', value: totalDebit, format: 'currency', color: 'text-red-600' },
        { label: 'Total Credit', value: totalCredit, format: 'currency', color: 'text-green-600' },
        { label: 'Balance', value: totalDebit - totalCredit, format: 'currency', color: 'text-blue-700' },
      ];
    },
    columns: [
      { key: 'posting_date', label: 'Date', format: 'date' },
      { key: 'voucher_type', label: 'Voucher Type' },
      { key: 'voucher_no', label: 'Voucher No' },
      { key: 'debit', label: 'Debit', format: 'currency', align: 'right' },
      { key: 'credit', label: 'Credit', format: 'currency', align: 'right' },
      { key: 'balance', label: 'Balance', format: 'currency', align: 'right' },
      { key: 'remarks', label: 'Remarks' },
    ],
  },
  {
    id: 'supplier-ledger',
    category: 'finance',
    title: 'Supplier Ledger',
    description: 'GL entries and running balance for a specific supplier',
    fetch: async (p) => {
      const res = await reportsApi.getSupplierLedger(p.supplier || '', p);
      const rows = res.data.message || [];
      return { data: { message: { data: rows, total: rows.length } } };
    },
    filters: [
      { key: 'supplier', label: 'Supplier', type: 'text' },
      fromDateFilter, toDateFilter,
    ],
    kpis: (m) => {
      const rows = m.data || [];
      const totalDebit = rows.reduce((s: number, r: any) => s + (r.debit || 0), 0);
      const totalCredit = rows.reduce((s: number, r: any) => s + (r.credit || 0), 0);
      return [
        { label: 'Entries', value: rows.length, format: 'number' },
        { label: 'Total Debit', value: totalDebit, format: 'currency', color: 'text-red-600' },
        { label: 'Total Credit', value: totalCredit, format: 'currency', color: 'text-green-600' },
        { label: 'Balance', value: totalCredit - totalDebit, format: 'currency', color: 'text-blue-700' },
      ];
    },
    columns: [
      { key: 'posting_date', label: 'Date', format: 'date' },
      { key: 'voucher_type', label: 'Voucher Type' },
      { key: 'voucher_no', label: 'Voucher No' },
      { key: 'debit', label: 'Debit', format: 'currency', align: 'right' },
      { key: 'credit', label: 'Credit', format: 'currency', align: 'right' },
      { key: 'balance', label: 'Balance', format: 'currency', align: 'right' },
      { key: 'remarks', label: 'Remarks' },
    ],
  },
];

// ─── Helpers ─────────────────────────────────────────────────────

export function getReportById(id: string): ReportDef | undefined {
  return REPORTS.find((r) => r.id === id);
}

export function getReportsByCategory(category: ReportCategory): ReportDef[] {
  return REPORTS.filter((r) => r.category === category);
}

export const CATEGORIES: { key: ReportCategory; label: string; icon: string }[] = [
  { key: 'sales', label: 'Sales', icon: 'TrendingUp' },
  { key: 'purchasing', label: 'Purchasing', icon: 'ShoppingCart' },
  { key: 'inventory', label: 'Inventory', icon: 'Package' },
  { key: 'finance', label: 'Finance', icon: 'DollarSign' },
];

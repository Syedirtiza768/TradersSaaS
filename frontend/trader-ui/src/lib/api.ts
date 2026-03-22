/**
 * Trader App — API Client
 *
 * Axios-based wrapper around the Frappe / ERPNext REST API.
 * All backend calls go through this module so every page can stay thin.
 */

import axios, { type AxiosInstance, type AxiosResponse } from 'axios';

// ─── Axios Instance ──────────────────────────────────────────────

const http: AxiosInstance = axios.create({
  baseURL: '/',
  withCredentials: true,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    'X-Frappe-CSRF-Token': getCsrfToken(),
  },
});

// On every response, grab the latest CSRF token if returned
http.interceptors.response.use(
  (res) => res,
  (err) => {
    // Session expired — redirect to login
    if (err.response?.status === 401) {
      window.location.href = '/login';
      return Promise.reject(err);
    }
    // CSRF token mismatch — refresh & retry once
    if (err.response?.status === 403 && !err.config._retried) {
      const token = getCsrfToken();
      if (token) {
        err.config._retried = true;
        err.config.headers['X-Frappe-CSRF-Token'] = token;
        return http.request(err.config);
      }
    }
    return Promise.reject(err);
  },
);

function getCsrfToken(): string {
  return (
    document.cookie
      .split('; ')
      .find((c) => c.startsWith('csrf_token='))
      ?.split('=')[1] || ''
  );
}

// ─── Generic Frappe call helper ──────────────────────────────────

/** Strip keys whose value is undefined — Frappe serialises them as the
 *  literal string "undefined" which causes 400 BAD REQUEST errors. */
function clean(obj?: Record<string, any>): Record<string, any> | undefined {
  if (!obj) return undefined;
  const out: Record<string, any> = {};
  for (const [k, v] of Object.entries(obj)) {
    if (v !== undefined) out[k] = v;
  }
  return Object.keys(out).length ? out : undefined;
}

function call<T = any>(method: string, params?: Record<string, any>): Promise<AxiosResponse<{ message: T }>> {
  return http.post('/api/method/' + method, clean(params));
}

function get<T = any>(method: string, params?: Record<string, any>): Promise<AxiosResponse<{ message: T }>> {
  return http.get('/api/method/' + method, { params: clean(params) });
}

// ─── Auth API ────────────────────────────────────────────────────

export const authApi = {
  login: (usr: string, pwd: string) =>
    http.post('/api/method/login', { usr, pwd }),

  logout: () =>
    http.get('/api/method/logout'),

  getLoggedUser: () =>
    http.get('/api/method/frappe.auth.get_logged_user'),

  getRoles: () =>
    get('trader_app.api.settings.get_current_user_roles'),
};

// ─── Dashboard API ───────────────────────────────────────────────

export const dashboardApi = {
  getKPIs: (company?: string) =>
    get('trader_app.api.dashboard.get_kpis', { company }),

  getSalesTrend: (company?: string, months?: number) =>
    get('trader_app.api.dashboard.get_sales_trend', { company, months }),

  getTopCustomers: (limit?: number, company?: string) =>
    get('trader_app.api.dashboard.get_top_customers', { company, limit }),

  getRecentOrders: (limit?: number, company?: string) =>
    get('trader_app.api.dashboard.get_recent_orders', { company, limit }),

  getCashFlowSummary: (company?: string, months?: number) =>
    get('trader_app.api.dashboard.get_cash_flow_summary', { company, months }),

  getInventorySummary: (company?: string) =>
    get('trader_app.api.dashboard.get_inventory_summary', { company }),
};

// ─── Sales API ───────────────────────────────────────────────────

export const salesApi = {
  getInvoices: (params?: Record<string, any>) =>
    get('trader_app.api.sales.get_sales_invoices', params),

  getInvoiceDetail: (name: string) =>
    get('trader_app.api.sales.get_sales_invoice_detail', { name }),

  getOrders: (params?: Record<string, any>) =>
    get('trader_app.api.sales.get_sales_orders', params),

  getOrderDetail: (name: string) =>
    get('trader_app.api.sales.get_sales_order_detail', { name }),

  getQuotations: (params?: Record<string, any>) =>
    get('trader_app.api.sales.get_quotations', params),

  getQuotationDetail: (name: string) =>
    get('trader_app.api.sales.get_quotation_detail', { name }),

  createInvoice: (data: Record<string, any>) =>
    call('trader_app.api.sales.create_sales_invoice', data),

  createOrder: (data: Record<string, any>) =>
    call('trader_app.api.sales.create_sales_order', data),

  createQuotation: (data: Record<string, any>) =>
    call('trader_app.api.sales.create_quotation', data),

  submitInvoice: (name: string) =>
    call('trader_app.api.sales.submit_sales_invoice', { name }),

  submitOrder: (name: string) =>
    call('trader_app.api.sales.submit_sales_order', { name }),

  submitQuotation: (name: string) =>
    call('trader_app.api.sales.submit_quotation', { name }),

  cancelInvoice: (name: string) =>
    call('trader_app.api.sales.cancel_sales_invoice', { name }),

  cancelOrder: (name: string) =>
    call('trader_app.api.sales.cancel_sales_order', { name }),

  createReturnInvoice: (data: Record<string, any>) =>
    call('trader_app.api.sales.create_sales_invoice', { ...data, is_return: 1 }),

  getSummary: (company?: string) =>
    get('trader_app.api.sales.get_sales_summary', { company }),
};

// ─── Purchases API ───────────────────────────────────────────────

export const purchasesApi = {
  getInvoices: (params?: Record<string, any>) =>
    get('trader_app.api.purchases.get_purchase_invoices', params),

  getInvoiceDetail: (name: string) =>
    get('trader_app.api.purchases.get_purchase_invoice_detail', { name }),

  getOrders: (params?: Record<string, any>) =>
    get('trader_app.api.purchases.get_purchase_orders', params),

  getOrderDetail: (name: string) =>
    get('trader_app.api.purchases.get_purchase_order_detail', { name }),

  getRequisitions: (params?: Record<string, any>) =>
    get('trader_app.api.purchases.get_material_requests', params),

  getRequisitionDetail: (name: string) =>
    get('trader_app.api.purchases.get_material_request_detail', { name }),

  submitRequisition: (name: string) =>
    call('trader_app.api.purchases.submit_material_request', { name }),

  getRfqs: (params?: Record<string, any>) =>
    get('trader_app.api.purchases.get_supplier_quotations', params),

  getRfqDetail: (name: string) =>
    get('trader_app.api.purchases.get_supplier_quotation_detail', { name }),

  createInvoice: (data: Record<string, any>) =>
    call('trader_app.api.purchases.create_purchase_invoice', data),

  createOrder: (data: Record<string, any>) =>
    call('trader_app.api.purchases.create_purchase_order', data),

  createRequisition: (data: Record<string, any>) =>
    call('trader_app.api.purchases.create_material_request', data),

  createRfq: (data: Record<string, any>) =>
    call('trader_app.api.purchases.create_supplier_quotation', data),

  createOrderFromRfq: (name: string) =>
    call('trader_app.api.purchases.create_purchase_order_from_supplier_quotation', { name }),

  submitInvoice: (name: string) =>
    call('trader_app.api.purchases.submit_purchase_invoice', { name }),

  submitOrder: (name: string) =>
    call('trader_app.api.purchases.submit_purchase_order', { name }),

  submitRfq: (name: string) =>
    call('trader_app.api.purchases.submit_supplier_quotation', { name }),

  cancelInvoice: (name: string) =>
    call('trader_app.api.purchases.cancel_purchase_invoice', { name }),

  cancelOrder: (name: string) =>
    call('trader_app.api.purchases.cancel_purchase_order', { name }),

  cancelMaterialRequest: (name: string) =>
    call('trader_app.api.purchases.cancel_material_request', { name }),

  cancelSupplierQuotation: (name: string) =>
    call('trader_app.api.purchases.cancel_supplier_quotation', { name }),

  createReturnInvoice: (data: Record<string, any>) =>
    call('trader_app.api.purchases.create_purchase_invoice', { ...data, is_return: 1 }),

  getSummary: (company?: string) =>
    get('trader_app.api.purchases.get_purchase_summary', { company }),
};

// ─── Inventory API ───────────────────────────────────────────────

export const inventoryApi = {
  getStockBalance: (params?: Record<string, any>) =>
    get('trader_app.api.inventory.get_stock_balance', params),

  getStockLedger: (params?: Record<string, any>) =>
    get('trader_app.api.inventory.get_stock_ledger', params),

  getItems: (params?: Record<string, any>) =>
    get('trader_app.api.inventory.get_items', params),

  getItemDetail: (itemCode: string) =>
    get('trader_app.api.inventory.get_item_detail', { item_code: itemCode }),

  getWarehouses: (company?: string) =>
    get('trader_app.api.inventory.get_warehouses', { company }),

  getSummary: (company?: string) =>
    get('trader_app.api.inventory.get_inventory_summary', { company }),

  getInventorySummary: (company?: string) =>
    get('trader_app.api.inventory.get_inventory_summary', { company }),

  getLowStockItems: (params?: Record<string, any>) =>
    get('trader_app.api.inventory.get_low_stock_items', params),

  getItemGroups: () =>
    get('trader_app.api.inventory.get_item_groups'),

  createItem: (data: Record<string, any>) =>
    call('trader_app.api.inventory.create_item', data),

  createStockEntry: (data: Record<string, any>) =>
    call('trader_app.api.inventory.create_stock_entry', data),

  createPurchaseReceipt: (data: Record<string, any>) =>
    call('trader_app.api.inventory.create_purchase_receipt', data),

  createSalesDispatch: (data: Record<string, any>) =>
    call('trader_app.api.inventory.create_sales_dispatch', data),
};

// ─── Customers API ───────────────────────────────────────────────

export const customersApi = {
  getList: (params?: Record<string, any>) =>
    get('trader_app.api.customers.get_customers', params),

  getDetail: (name: string) =>
    get('trader_app.api.customers.get_customer_detail', { name }),

  getGroups: () =>
    get('trader_app.api.customers.get_customer_groups'),

  getTransactions: (customer: string, params?: Record<string, any>) =>
    get('trader_app.api.customers.get_customer_transactions', { customer, ...params }),
  create: (data: Record<string, any>) =>
    call('trader_app.api.customers.create_customer', data),

  update: (data: Record<string, any>) =>
    call('trader_app.api.customers.update_customer', data),

  enable: (name: string) =>
    call('trader_app.api.customers.enable_customer', { name }),

  disable: (name: string) =>
    call('trader_app.api.customers.disable_customer', { name }),};

// ─── Suppliers API ───────────────────────────────────────────────

export const suppliersApi = {
  getList: (params?: Record<string, any>) =>
    get('trader_app.api.suppliers.get_suppliers', params),

  getDetail: (name: string) =>
    get('trader_app.api.suppliers.get_supplier_detail', { name }),

  getGroups: () =>
    get('trader_app.api.suppliers.get_supplier_groups'),

  getTransactions: (supplier: string, params?: Record<string, any>) =>
    get('trader_app.api.suppliers.get_supplier_transactions', { supplier, ...params }),
  create: (data: Record<string, any>) =>
    call('trader_app.api.suppliers.create_supplier', data),

  update: (data: Record<string, any>) =>
    call('trader_app.api.suppliers.update_supplier', data),

  enable: (name: string) =>
    call('trader_app.api.suppliers.enable_supplier', { name }),

  disable: (name: string) =>
    call('trader_app.api.suppliers.disable_supplier', { name }),};

// ─── Finance API ─────────────────────────────────────────────────

export const financeApi = {
  getPaymentEntries: (params?: Record<string, any>) =>
    get('trader_app.api.finance.get_payment_entries', params),

  getPaymentEntryDetail: (name: string) =>
    get('trader_app.api.finance.get_payment_entry_detail', { name }),

  getPaymentEntrySetup: (company?: string) =>
    get('trader_app.api.finance.get_payment_entry_setup', { company }),

  createPaymentEntry: (data: Record<string, any>) =>
    call('trader_app.api.finance.create_payment_entry', data),

  submitPaymentEntry: (name: string) =>
    call('trader_app.api.finance.submit_payment_entry', { name }),

  cancelPaymentEntry: (name: string) =>
    call('trader_app.api.finance.cancel_payment_entry', { name }),

  getJournalEntries: (params?: Record<string, any>) =>
    get('trader_app.api.finance.get_journal_entries', params),

  getJournalEntryDetail: (name: string) =>
    get('trader_app.api.finance.get_journal_entry_detail', { name }),

  getAccounts: (params?: Record<string, any>) =>
    get('trader_app.api.finance.get_accounts', params),

  createJournalEntry: (data: Record<string, any>) =>
    call('trader_app.api.finance.create_journal_entry', data),

  submitJournalEntry: (name: string) =>
    call('trader_app.api.finance.submit_journal_entry', { name }),

  cancelJournalEntry: (name: string) =>
    call('trader_app.api.finance.cancel_journal_entry', { name }),

  getOutstandingSummary: (company?: string) =>
    get('trader_app.api.finance.get_outstanding_summary', { company }),
};

// ─── Reports API ─────────────────────────────────────────────────

export const reportsApi = {
  getSalesReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_sales_report', params),

  getPurchaseReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_purchase_report', params),

  getItemSalesReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_item_sales_report', params),

  getCustomerLedger: (customer: string, params?: Record<string, any>) =>
    get('trader_app.api.reports.get_customer_ledger', { customer, ...params }),

  getSupplierLedger: (supplier: string, params?: Record<string, any>) =>
    get('trader_app.api.reports.get_supplier_ledger', { supplier, ...params }),

  getReceivableAgingSummary: () =>
    get('trader_app.api.reports.get_receivable_aging'),

  getReceivableAgingDetail: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_receivable_aging_detail', params),

  getAccountsPayable: () =>
    get('trader_app.api.reports.get_accounts_payable'),

  getProfitAndLoss: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_profit_and_loss', params),

  getGeneralLedger: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_general_ledger', params),

  // ─── Phase 1: New report endpoints ─────────────────────────────
  getSalesPerformanceReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_sales_performance_report', params),

  getCustomerProfitabilityReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_customer_profitability_report', params),

  getStockAgingReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_stock_aging_report', params),

  getInventoryMovementReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_inventory_movement_report', params),

  getReorderReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_reorder_report', params),

  getSupplierScorecardReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_supplier_scorecard_report', params),

  getPurchasePriceVarianceReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_purchase_price_variance_report', params),

  getReceivableAgingInvoiceDetail: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_receivable_aging_invoice_detail', params),

  getPayableAgingInvoiceDetail: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_payable_aging_invoice_detail', params),

  getTaxSummaryReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_tax_summary_report', params),

  getOpenPurchaseOrdersReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_open_purchase_orders_report', params),

  getCollectionEfficiencyReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_collection_efficiency_report', params),

  // ─── Phase 2: New report endpoints ─────────────────────────────
  getDailySalesReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_daily_sales_report', params),

  getSalesReturnReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_sales_return_report', params),

  getPurchaseReturnReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_purchase_return_report', params),

  getCashflowReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_cashflow_report', params),

  getProfitLossSummaryReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_profit_loss_summary_report', params),

  getStockBalanceReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_stock_balance_report', params),

  getSalespersonPerformanceReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_salesperson_performance_report', params),

  getItemPurchaseReport: (params?: Record<string, any>) =>
    get('trader_app.api.reports.get_item_purchase_report', params),
};

export default http;

// ─── Settings API ────────────────────────────────────────────────

export const settingsApi = {
  get: () =>
    get('trader_app.api.settings.get_settings'),

  save: (data: Record<string, any>) =>
    call('trader_app.api.settings.save_settings', { data }),

  getRoles: () =>
    get('trader_app.api.settings.get_current_user_roles'),

  getTraderRoles: () =>
    get('trader_app.api.settings.get_trader_roles'),
};

// ─── GST / Tax API ───────────────────────────────────────────────

export const gstApi = {
  getSettings: () =>
    get('trader_app.api.gst.get_gst_settings'),

  saveSettings: (data: Record<string, any>) =>
    call('trader_app.api.gst.save_gst_settings', data),

  seedTemplates: (company: string) =>
    call('trader_app.api.gst.seed_punjab_gst_templates', { company }),

  getTaxTemplates: (doctype_filter?: string) =>
    get('trader_app.api.gst.get_tax_templates', { doctype: doctype_filter }),
};

// ─── Bundling API ────────────────────────────────────────────────

export const bundlingApi = {
  getBundles: (params?: Record<string, any>) =>
    get('trader_app.api.bundling.get_item_bundles', params),

  getBundleDetail: (name: string) =>
    get('trader_app.api.bundling.get_item_bundle_detail', { name }),

  createBundle: (data: Record<string, any>) =>
    call('trader_app.api.bundling.create_item_bundle', data),

  updateBundle: (data: Record<string, any>) =>
    call('trader_app.api.bundling.update_item_bundle', data),

  deleteBundle: (name: string) =>
    call('trader_app.api.bundling.delete_item_bundle', { name }),

  expandBundle: (name: string) =>
    call('trader_app.api.bundling.expand_bundle', { name }),
};

// ─── Print API ───────────────────────────────────────────────────

export const printApi = {
  getPrintData: (doctype: string, name: string, viewMode?: string, format?: string) =>
    get('trader_app.api.printing.get_print_data', { doctype, name, view_mode: viewMode, format }),
};

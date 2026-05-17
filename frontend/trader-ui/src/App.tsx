import { lazy, Suspense, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import LoginPage from './pages/LoginPage';
import DashboardLayout from './layouts/DashboardLayout';
import DashboardPage from './pages/DashboardPage';
import NotFoundPage from './pages/NotFoundPage';

/* ---------- lazy-loaded pages ---------- */
const SalesPage = lazy(() => import('./pages/SalesPage'));
const SalesInvoiceDetailPage = lazy(() => import('./pages/SalesInvoiceDetailPage'));
const SalesOrdersPage = lazy(() => import('./pages/SalesOrdersPage'));
const SalesOrderDetailPage = lazy(() => import('./pages/SalesOrderDetailPage'));
const QuotationsPage = lazy(() => import('./pages/QuotationsPage'));
const QuotationDetailPage = lazy(() => import('./pages/QuotationDetailPage'));
const CreateSalesInvoicePage = lazy(() => import('./pages/CreateSalesInvoicePage'));
const CreateSalesOrderPage = lazy(() => import('./pages/CreateSalesOrderPage'));
const CreateQuotationPage = lazy(() => import('./pages/CreateQuotationPage'));
const CreateSalesReturnPage = lazy(() => import('./pages/CreateSalesReturnPage'));
const CreateSalesDispatchPage = lazy(() => import('./pages/CreateSalesDispatchPage'));
const CreateSalesDocumentHubPage = lazy(() => import('./pages/CreateSalesDocumentHubPage'));
const CreatePurchaseDocumentHubPage = lazy(() => import('./pages/CreatePurchaseDocumentHubPage'));
const CreateDeliveryChallanPage = lazy(() => import('./pages/CreateDeliveryChallanPage'));
const DeliveryChallansPage = lazy(() => import('./pages/DeliveryChallansPage'));
const DeliveryChallanDetailPage = lazy(() => import('./pages/DeliveryChallanDetailPage'));
const PurchasesPage = lazy(() => import('./pages/PurchasesPage'));
const PurchaseInvoiceDetailPage = lazy(() => import('./pages/PurchaseInvoiceDetailPage'));
const PurchaseOrdersPage = lazy(() => import('./pages/PurchaseOrdersPage'));
const PurchaseOrderDetailPage = lazy(() => import('./pages/PurchaseOrderDetailPage'));
const PurchaseRequisitionsPage = lazy(() => import('./pages/PurchaseRequisitionsPage'));
const PurchaseRequisitionDetailPage = lazy(() => import('./pages/PurchaseRequisitionDetailPage'));
const SupplierQuotationsPage = lazy(() => import('./pages/SupplierQuotationsPage'));
const SupplierQuotationDetailPage = lazy(() => import('./pages/SupplierQuotationDetailPage'));
const CreatePurchaseInvoicePage = lazy(() => import('./pages/CreatePurchaseInvoicePage'));
const CreatePurchaseOrderPage = lazy(() => import('./pages/CreatePurchaseOrderPage'));
const CreatePurchaseRequisitionPage = lazy(() => import('./pages/CreatePurchaseRequisitionPage'));
const CreateSupplierQuotationPage = lazy(() => import('./pages/CreateSupplierQuotationPage'));
const CreatePurchaseReturnPage = lazy(() => import('./pages/CreatePurchaseReturnPage'));
const CreatePurchaseReceiptPage = lazy(() => import('./pages/CreatePurchaseReceiptPage'));
const InventoryPage = lazy(() => import('./pages/InventoryPage'));
const InventoryItemDetailPage = lazy(() => import('./pages/InventoryItemDetailPage'));
const CreateItemPage = lazy(() => import('./pages/CreateItemPage'));
const ItemBundlesPage = lazy(() => import('./pages/ItemBundlesPage'));
const WarehouseStockPage = lazy(() => import('./pages/WarehouseStockPage'));
const StockMovementPage = lazy(() => import('./pages/StockMovementPage'));
const CustomersPage = lazy(() => import('./pages/CustomersPage'));
const CustomerDetailPage = lazy(() => import('./pages/CustomerDetailPage'));
const EditCustomerPage = lazy(() => import('./pages/EditCustomerPage'));
const CreateCustomerPage = lazy(() => import('./pages/CreateCustomerPage'));
const SuppliersPage = lazy(() => import('./pages/SuppliersPage'));
const SupplierDetailPage = lazy(() => import('./pages/SupplierDetailPage'));
const EditSupplierPage = lazy(() => import('./pages/EditSupplierPage'));
const CreateSupplierPage = lazy(() => import('./pages/CreateSupplierPage'));
const FinancePage = lazy(() => import('./pages/FinancePage'));
const JournalEntriesPage = lazy(() => import('./pages/JournalEntriesPage'));
const JournalEntryDetailPage = lazy(() => import('./pages/JournalEntryDetailPage'));
const CreateJournalEntryPage = lazy(() => import('./pages/CreateJournalEntryPage'));
const PaymentEntriesPage = lazy(() => import('./pages/PaymentEntriesPage'));
const PaymentEntryDetailPage = lazy(() => import('./pages/PaymentEntryDetailPage'));
const CreatePaymentEntryPage = lazy(() => import('./pages/CreatePaymentEntryPage'));
const OperationsPage = lazy(() => import('./pages/OperationsPage'));
const DocumentPrintPage = lazy(() => import('./pages/DocumentPrintPage'));
const GstSettingsPage = lazy(() => import('./pages/GstSettingsPage'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const AuditLogPage = lazy(() => import('./pages/AuditLogPage'));
const PosCheckoutPage = lazy(() => import('./pages/PosCheckoutPage'));

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="spinner" />
    </div>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, initialized } = useAuthStore();
  if (!initialized) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="spinner" />
      </div>
    );
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  const checkAuth = useAuthStore((s) => s.checkAuth);
  useEffect(() => { checkAuth(); }, [checkAuth]);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />

        {/* Sales */}
        <Route path="sales" element={<SalesPage />} />
        <Route path="sales/pos" element={<PosCheckoutPage />} />
        <Route path="sales/documents/new" element={<CreateSalesDocumentHubPage />} />
        <Route path="sales/new" element={<CreateSalesInvoicePage />} />
        <Route path="sales/proforma/new" element={<CreateQuotationPage />} />
        <Route path="sales/challans" element={<DeliveryChallansPage />} />
        <Route path="sales/challans/new" element={<CreateDeliveryChallanPage />} />
        <Route path="sales/challans/:challanId" element={<DeliveryChallanDetailPage />} />
        <Route path="sales/returns/new" element={<CreateSalesReturnPage />} />
        <Route path="sales/dispatches/new" element={<CreateSalesDispatchPage />} />
        <Route path="sales/orders" element={<SalesOrdersPage />} />
        <Route path="sales/orders/new" element={<CreateSalesOrderPage />} />
        <Route path="sales/orders/:orderId" element={<SalesOrderDetailPage />} />
        <Route path="sales/quotations" element={<QuotationsPage />} />
        <Route path="sales/quotations/new" element={<CreateQuotationPage />} />
        <Route path="sales/quotations/:quotationId" element={<QuotationDetailPage />} />
        <Route path="sales/:invoiceId" element={<SalesInvoiceDetailPage />} />

        {/* Purchases */}
        <Route path="purchases" element={<PurchasesPage />} />
        <Route path="purchases/documents/new" element={<CreatePurchaseDocumentHubPage />} />
        <Route path="purchases/new" element={<CreatePurchaseInvoicePage />} />
        <Route path="purchases/returns/new" element={<CreatePurchaseReturnPage />} />
        <Route path="purchases/receipts/new" element={<CreatePurchaseReceiptPage />} />
        <Route path="purchases/orders" element={<PurchaseOrdersPage />} />
        <Route path="purchases/orders/new" element={<CreatePurchaseOrderPage />} />
        <Route path="purchases/orders/:orderId" element={<PurchaseOrderDetailPage />} />
        <Route path="purchases/requisitions" element={<PurchaseRequisitionsPage />} />
        <Route path="purchases/requisitions/new" element={<CreatePurchaseRequisitionPage />} />
        <Route path="purchases/requisitions/:reqId" element={<PurchaseRequisitionDetailPage />} />
        <Route path="purchases/rfqs" element={<SupplierQuotationsPage />} />
        <Route path="purchases/rfqs/new" element={<CreateSupplierQuotationPage />} />
        <Route path="purchases/rfqs/:quotationId" element={<SupplierQuotationDetailPage />} />
        <Route path="purchases/:invoiceId" element={<PurchaseInvoiceDetailPage />} />

        {/* Inventory */}
        <Route path="inventory" element={<InventoryPage />} />
        <Route path="inventory/items/new" element={<CreateItemPage />} />
        <Route path="inventory/items/:itemId" element={<InventoryItemDetailPage />} />
        <Route path="inventory/bundles" element={<ItemBundlesPage />} />
        <Route path="inventory/warehouse" element={<WarehouseStockPage />} />
        <Route path="inventory/movements" element={<StockMovementPage />} />
        <Route path="inventory/dispatches/new" element={<CreateSalesDispatchPage />} />

        {/* Customers */}
        <Route path="customers" element={<CustomersPage />} />
        <Route path="customers/new" element={<CreateCustomerPage />} />
        <Route path="customers/:customerId" element={<CustomerDetailPage />} />
        <Route path="customers/:customerId/edit" element={<EditCustomerPage />} />

        {/* Suppliers */}
        <Route path="suppliers" element={<SuppliersPage />} />
        <Route path="suppliers/new" element={<CreateSupplierPage />} />
        <Route path="suppliers/:supplierId" element={<SupplierDetailPage />} />
        <Route path="suppliers/:supplierId/edit" element={<EditSupplierPage />} />

        {/* Finance */}
        <Route path="finance" element={<FinancePage />} />
        <Route path="finance/journals" element={<JournalEntriesPage />} />
        <Route path="finance/journals/new" element={<CreateJournalEntryPage />} />
        <Route path="finance/journals/:journalId" element={<JournalEntryDetailPage />} />
        <Route path="finance/payments" element={<PaymentEntriesPage />} />
        <Route path="finance/payments/new" element={<CreatePaymentEntryPage />} />
        <Route path="finance/payments/:paymentId" element={<PaymentEntryDetailPage />} />

        <Route path="operations" element={<OperationsPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="settings/audit" element={<AuditLogPage />} />
        <Route path="settings/gst" element={<GstSettingsPage />} />
        <Route path="print" element={<DocumentPrintPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

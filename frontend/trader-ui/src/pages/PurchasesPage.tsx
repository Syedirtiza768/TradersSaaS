import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, DollarSign, Truck, AlertCircle, Search, ChevronLeft, ChevronRight, Plus } from 'lucide-react';
import { purchasesApi } from '../lib/api';
import { formatCurrency, formatDate, getStatusColor, formatCompact, debounce } from '../lib/utils';

const STATUS_TABS = ['All', 'Unpaid', 'Paid', 'Overdue', 'Draft'];

export default function PurchasesPage() {
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('All');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const pageSize = 15;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = { page, page_size: pageSize };
      if (status !== 'All') params.status = status;
      if (search) params.search = search;

      const [invoiceRes, summaryRes] = await Promise.all([
        purchasesApi.getInvoices(params),
        purchasesApi.getSummary(),
      ]);

      const d = invoiceRes.data.message;
      setInvoices(d.data || []);
      setTotal(d.total || 0);
      setSummary(summaryRes.data.message);
    } catch (err) {
      console.error('Failed to load purchases data:', err);
    } finally {
      setLoading(false);
    }
  }, [page, status, search]);

  useEffect(() => { load(); }, [load]);

  const debouncedSearch = useCallback(
    debounce((val: string) => { setSearch(val); setPage(1); }, 400),
    [],
  );

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="page-title">Purchases</h1>
          <p className="text-gray-500 mt-1 text-sm">Manage purchase invoices and orders</p>
        </div>
        <div className="flex items-center gap-2 self-start">
          <button onClick={() => navigate('/purchases/returns/new')} className="btn-secondary flex items-center gap-2 text-sm">
            New Return
          </button>
          <button onClick={() => navigate('/purchases/documents/new')} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> New Document
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <StatCard icon={FileText} label="Total Invoices" value={summary?.total_invoices} color="blue" />
        <StatCard icon={DollarSign} label="Monthly Purchases" value={summary?.monthly_purchases} format="currency" color="green" />
        <StatCard icon={AlertCircle} label="Outstanding Payable" value={summary?.total_outstanding} format="currency" color="red" />
        <StatCard icon={Truck} label="Active Suppliers" value={summary?.total_suppliers} color="purple" />
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
        <div className="flex gap-1 bg-gray-100 p-1 rounded-lg overflow-x-auto scrollbar-hide w-full sm:w-auto">
          {STATUS_TABS.map((s) => (
            <button
              key={s}
              onClick={() => { setStatus(s); setPage(1); }}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
                status === s ? 'bg-white shadow text-brand-700' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search purchases..."
            onChange={(e) => debouncedSearch(e.target.value)}
            className="input-field pl-9"
          />
        </div>
      </div>

      {/* Desktop Table */}
      <div className="hidden md:block table-container">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50">
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Invoice</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Supplier</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Date</th>
              <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Amount</th>
              <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Outstanding</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-gray-400"><div className="spinner mx-auto" /></td></tr>
            ) : invoices.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-gray-400">No invoices found.</td></tr>
            ) : (
              invoices.map((inv) => (
                <tr key={inv.name} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-3 text-sm font-medium text-brand-700">{inv.name}</td>
                  <td className="px-6 py-3 text-sm text-gray-700">{inv.supplier_name || inv.supplier}</td>
                  <td className="px-6 py-3 text-sm text-gray-500">{formatDate(inv.posting_date)}</td>
                  <td className="px-6 py-3 text-sm text-gray-900 text-right font-medium">{formatCurrency(inv.grand_total)}</td>
                  <td className="px-6 py-3 text-sm text-right font-medium text-red-600">{formatCurrency(inv.outstanding_amount)}</td>
                  <td className="px-6 py-3">
                    <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(inv.status)}`}>
                      {inv.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile Card List */}
      <div className="md:hidden card divide-y divide-gray-100">
        {loading ? (
          <div className="px-4 py-12 text-center text-gray-400"><div className="spinner mx-auto" /></div>
        ) : invoices.length === 0 ? (
          <div className="px-4 py-12 text-center text-gray-400 text-sm">No invoices found.</div>
        ) : (
          invoices.map((inv) => (
            <div key={inv.name} className="px-4 py-3 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-brand-700">{inv.name}</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${getStatusColor(inv.status)}`}>
                  {inv.status}
                </span>
              </div>
              <div className="text-xs text-gray-500 truncate">{inv.supplier_name || inv.supplier}</div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">{formatDate(inv.posting_date)}</span>
                <div className="flex gap-3">
                  <span className="font-medium text-gray-900">{formatCurrency(inv.grand_total)}</span>
                  {inv.outstanding_amount > 0 && (
                    <span className="font-medium text-red-600">{formatCurrency(inv.outstanding_amount)}</span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs sm:text-sm text-gray-500">
          <span>Showing {((page - 1) * pageSize) + 1}–{Math.min(page * pageSize, total)} of {total}</span>
          <div className="flex gap-1">
            <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} className="btn-secondary px-2 py-1 text-xs" aria-label="Previous page">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page === totalPages} className="btn-secondary px-2 py-1 text-xs" aria-label="Next page">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, format, color = 'blue' }: {
  icon: any; label: string; value: any; format?: string; color?: string;
}) {
  const bg = `bg-${color}-50`;
  const ic = `text-${color}-600`;
  const display = value == null ? '—' : format === 'currency' ? formatCompact(value) : (value ?? 0).toLocaleString();
  return (
    <div className="card p-4 sm:p-5">
      <div className="flex items-center gap-2 sm:gap-3">
        <div className={`p-1.5 sm:p-2 ${bg} rounded-lg`}><Icon className={`w-4 h-4 sm:w-5 sm:h-5 ${ic}`} /></div>
        <div className="min-w-0">
          <p className="text-[10px] sm:text-xs text-gray-500 truncate">{label}</p>
          <p className="text-sm sm:text-lg font-bold text-gray-900">{display}</p>
        </div>
      </div>
    </div>
  );
}

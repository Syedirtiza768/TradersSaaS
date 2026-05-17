import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, ChevronLeft, ChevronRight, ScrollText } from 'lucide-react';
import { auditApi } from '../lib/api';
import { formatDate } from '../lib/utils';

const DOCTYPE_OPTIONS = [
  '',
  'Sales Invoice',
  'Purchase Invoice',
  'Sales Order',
  'Purchase Order',
  'Payment Entry',
  'Delivery Note',
  'Journal Entry',
  'Quotation',
];

function docPath(doctype: string, name: string): string | null {
  if (!name) return null;
  switch (doctype) {
    case 'Sales Invoice':
      return `/sales/${encodeURIComponent(name)}`;
    case 'Purchase Invoice':
      return `/purchases/${encodeURIComponent(name)}`;
    case 'Sales Order':
      return `/sales/orders/${encodeURIComponent(name)}`;
    case 'Purchase Order':
      return `/purchases/orders/${encodeURIComponent(name)}`;
    case 'Quotation':
      return `/sales/quotations/${encodeURIComponent(name)}`;
    case 'Payment Entry':
      return `/finance/payments/${encodeURIComponent(name)}`;
    case 'Journal Entry':
      return `/finance/journals/${encodeURIComponent(name)}`;
    case 'Delivery Note':
      return `/sales/challans/${encodeURIComponent(name)}`;
    default:
      return null;
  }
}

export default function AuditLogPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [rows, setRows] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const page = Math.max(1, Number(searchParams.get('page') || '1') || 1);
  const fromDate = searchParams.get('from_date') || '';
  const toDate = searchParams.get('to_date') || '';
  const referenceDoctype = searchParams.get('doctype') || '';
  const referenceName = searchParams.get('doc') || '';
  const user = searchParams.get('user') || '';
  const pageSize = 30;

  const updateParams = (updates: Record<string, string | null>) => {
    const next = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, value]) => {
      if (!value) next.delete(key);
      else next.set(key, value);
    });
    if (!('page' in updates)) next.set('page', '1');
    setSearchParams(next);
  };

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await auditApi.getLog({
        page,
        page_size: pageSize,
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
        reference_doctype: referenceDoctype || undefined,
        reference_name: referenceName || undefined,
        user: user || undefined,
      });
      const msg = res.data.message || {};
      setRows(msg.data || []);
      setTotal(msg.total || 0);
    } catch {
      setError('Could not load audit log.');
      setRows([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, fromDate, toDate, referenceDoctype, referenceName, user]);

  useEffect(() => {
    void load();
  }, [load]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Link
            to="/settings"
            className="mb-2 inline-flex items-center gap-2 text-sm text-brand-700 hover:text-brand-800 dark:text-brand-400"
          >
            <ArrowLeft size={16} /> Settings
          </Link>
          <h1 className="page-title flex items-center gap-2">
            <ScrollText size={22} className="text-brand-600" />
            Audit log
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-slate-400">
            Company-scoped activity on sales, purchases, finance, and inventory documents.
          </p>
        </div>
      </div>

      <div className="card grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 lg:grid-cols-5">
        <label className="block text-sm">
          <span className="mb-1 block text-xs font-medium text-gray-600">From</span>
          <input
            type="date"
            value={fromDate}
            onChange={(e) => updateParams({ from_date: e.target.value || null })}
            className="input-field w-full text-sm"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-xs font-medium text-gray-600">To</span>
          <input
            type="date"
            value={toDate}
            onChange={(e) => updateParams({ to_date: e.target.value || null })}
            className="input-field w-full text-sm"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-xs font-medium text-gray-600">Document type</span>
          <select
            value={referenceDoctype}
            onChange={(e) => updateParams({ doctype: e.target.value || null })}
            className="input-field w-full text-sm"
          >
            <option value="">All types</option>
            {DOCTYPE_OPTIONS.filter(Boolean).map((dt) => (
              <option key={dt} value={dt}>{dt}</option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-xs font-medium text-gray-600">Document name</span>
          <input
            type="text"
            value={referenceName}
            onChange={(e) => updateParams({ doc: e.target.value || null })}
            placeholder="e.g. SINV-2024"
            className="input-field w-full text-sm"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-xs font-medium text-gray-600">User</span>
          <input
            type="text"
            value={user}
            onChange={(e) => updateParams({ user: e.target.value || null })}
            placeholder="Email or name"
            className="input-field w-full text-sm"
          />
        </label>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16"><div className="spinner" /></div>
        ) : rows.length === 0 ? (
          <p className="py-12 text-center text-sm text-gray-500">No activity found for these filters.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500 dark:bg-slate-900/50">
                  <th className="px-4 py-3">When</th>
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Subject</th>
                  <th className="px-4 py-3">Document</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const path = docPath(row.reference_doctype, row.reference_name);
                  return (
                    <tr key={row.name} className="border-b border-gray-100 dark:border-slate-800">
                      <td className="whitespace-nowrap px-4 py-3 text-gray-600">{formatDate(row.creation)}</td>
                      <td className="px-4 py-3">{row.full_name || row.owner}</td>
                      <td className="px-4 py-3">
                        <span className="rounded bg-gray-100 px-2 py-0.5 text-xs font-medium dark:bg-slate-800">
                          {row.operation || row.status || '—'}
                        </span>
                      </td>
                      <td className="max-w-xs px-4 py-3 text-gray-700 dark:text-slate-300">{row.subject || '—'}</td>
                      <td className="px-4 py-3">
                        {row.reference_doctype && row.reference_name ? (
                          path ? (
                            <button
                              type="button"
                              onClick={() => navigate(path)}
                              className="text-brand-700 hover:underline dark:text-brand-400"
                            >
                              {row.reference_doctype}: {row.reference_name}
                            </button>
                          ) : (
                            <span>{row.reference_doctype}: {row.reference_name}</span>
                          )
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {total > pageSize && (
          <div className="flex items-center justify-between border-t px-4 py-3 text-sm">
            <span className="text-gray-500">
              Page {page} of {totalPages} ({total} entries)
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => updateParams({ page: String(page - 1) })}
                className="btn-secondary flex items-center gap-1 disabled:opacity-50"
              >
                <ChevronLeft size={14} /> Prev
              </button>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => updateParams({ page: String(page + 1) })}
                className="btn-secondary flex items-center gap-1 disabled:opacity-50"
              >
                Next <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

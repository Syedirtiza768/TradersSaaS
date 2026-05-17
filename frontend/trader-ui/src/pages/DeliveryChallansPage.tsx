import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search } from 'lucide-react';
import { salesApi } from '../lib/api';
import { formatDate } from '../lib/utils';

export default function DeliveryChallansPage() {
  const navigate = useNavigate();
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await salesApi.getDeliveryNotes({ page: 1, page_size: 50, search: search || undefined });
      setRows(res.data.message?.data || []);
    } catch {
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => { void load(); }, [load]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="page-title">Delivery Challans</h1>
          <p className="mt-1 text-sm text-gray-500">Goods dispatched without a sales invoice.</p>
        </div>
        <button type="button" onClick={() => navigate('/sales/challans/new')} className="btn-primary flex items-center gap-2 self-start">
          <Plus className="h-4 w-4" /> New Challan
        </button>
      </div>

      <div className="relative w-full sm:w-72">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input type="text" placeholder="Search challans..." className="input-field pl-9" onChange={(e) => setSearch(e.target.value)} />
      </div>

      {loading ? (
        <div className="flex justify-center py-16"><div className="spinner" /></div>
      ) : rows.length === 0 ? (
        <div className="card p-8 text-center text-gray-500">No delivery challans yet.</div>
      ) : (
        <div className="card overflow-hidden">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Customer</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rows.map((row) => (
                <tr key={row.name} className="cursor-pointer hover:bg-gray-50" onClick={() => navigate(`/sales/challans/${encodeURIComponent(row.name)}`)}>
                  <td className="px-4 py-3 font-medium text-brand-700">{row.name}</td>
                  <td className="px-4 py-3">{row.customer_name || row.customer}</td>
                  <td className="px-4 py-3">{formatDate(row.posting_date)}</td>
                  <td className="px-4 py-3">{row.status || (row.docstatus === 0 ? 'Draft' : 'Submitted')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

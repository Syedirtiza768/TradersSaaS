import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Printer, Truck } from 'lucide-react';
import { salesApi } from '../lib/api';
import { formatDate } from '../lib/utils';

export default function DeliveryChallanDetailPage() {
  const navigate = useNavigate();
  const { challanId } = useParams();
  const [doc, setDoc] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!challanId) return;
    setLoading(true);
    try {
      const res = await salesApi.getDeliveryNoteDetail(decodeURIComponent(challanId));
      setDoc(res.data.message);
    } catch {
      setError('Could not load delivery challan.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, [challanId]);

  const handleSubmit = async () => {
    if (!doc?.name) return;
    setSubmitting(true);
    try {
      await salesApi.submitDeliveryNote(doc.name);
      await load();
    } catch (err: any) {
      setError(err?.response?.data?.exception || 'Submit failed.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center py-16"><div className="spinner" /></div>;
  }

  if (!doc) {
    return <div className="text-red-600">{error || 'Not found.'}</div>;
  }

  const printFormat = doc.print_format || 'delivery_challan';

  return (
    <div className="space-y-6">
      <button type="button" onClick={() => navigate('/sales/challans')} className="inline-flex items-center gap-2 text-sm text-brand-700">
        <ArrowLeft size={16} /> Back to challans
      </button>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-brand-700">
            <Truck className="h-5 w-5" />
            <span className="text-sm font-medium uppercase tracking-wide">Delivery Challan</span>
          </div>
          <h1 className="page-title mt-1">{doc.name}</h1>
          <p className="text-gray-500">{doc.customer_name || doc.customer} · {formatDate(doc.posting_date)}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {doc.docstatus === 0 && (
            <button type="button" onClick={handleSubmit} disabled={submitting} className="btn-primary">
              {submitting ? 'Submitting…' : 'Submit'}
            </button>
          )}
          <button
            type="button"
            onClick={() => navigate(`/print?doctype=Delivery%20Note&name=${encodeURIComponent(doc.name)}&format=${printFormat}`)}
            className="btn-secondary flex items-center gap-2"
          >
            <Printer size={14} /> Print
          </button>
        </div>
      </div>

      <div className="card overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th className="px-4 py-3">Item</th>
              <th className="px-4 py-3 text-right">Qty</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {(doc.items || []).map((line: any) => (
              <tr key={line.name || line.item_code}>
                <td className="px-4 py-3">{line.item_name || line.item_code}</td>
                <td className="px-4 py-3 text-right">{line.qty}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

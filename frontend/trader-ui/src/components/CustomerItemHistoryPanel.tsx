import { useEffect, useState } from 'react';
import { salesApi } from '../lib/api';
import { formatCurrency } from '../lib/utils';

export type CustomerItemHistoryRow = {
  invoice: string;
  posting_date: string;
  item_code: string;
  item_name?: string;
  qty: number;
  rate: number;
  discount_percentage?: number;
  discount_amount?: number;
  line_amount?: number;
};

type Props = {
  customer: string;
  itemCode: string;
  limit?: number;
  className?: string;
};

export default function CustomerItemHistoryPanel({ customer, itemCode, limit = 5, className = '' }: Props) {
  const [rows, setRows] = useState<CustomerItemHistoryRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!customer || !itemCode) {
      setRows([]);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    salesApi
      .getCustomerItemSalesHistory({ customer, item_code: itemCode, limit })
      .then((res) => {
        if (cancelled) return;
        setRows(res.data.message?.data || []);
      })
      .catch((err) => {
        if (cancelled) return;
        console.error('Failed to load customer item sales history:', err);
        setError('Could not load previous sales for this customer and item.');
        setRows([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [customer, itemCode, limit]);

  if (!customer || !itemCode) return null;

  return (
    <div className={`rounded-lg border border-brand-100 bg-brand-50/60 px-3 py-2.5 text-xs ${className}`}>
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="font-semibold text-brand-900">Last {limit} sales to this customer</span>
        {loading && <span className="text-brand-600">Loading…</span>}
      </div>

      {error && <p className="text-red-700">{error}</p>}

      {!loading && !error && rows.length === 0 && (
        <p className="text-gray-600">No prior submitted invoices for this item.</p>
      )}

      {!loading && rows.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[32rem] text-left">
            <thead>
              <tr className="border-b border-brand-200 text-[10px] uppercase tracking-wide text-brand-800">
                <th className="py-1 pr-2 font-medium">Date</th>
                <th className="py-1 pr-2 font-medium">Invoice</th>
                <th className="py-1 pr-2 text-right font-medium">Qty</th>
                <th className="py-1 pr-2 text-right font-medium">Rate</th>
                <th className="py-1 pr-2 text-right font-medium">Disc %</th>
                <th className="py-1 text-right font-medium">Amount</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={`${row.invoice}-${row.posting_date}-${row.rate}`}
                  className="border-b border-brand-100/80 text-gray-800"
                >
                  <td className="py-1 pr-2 whitespace-nowrap">{row.posting_date}</td>
                  <td className="py-1 pr-2 font-mono text-[11px]">{row.invoice}</td>
                  <td className="py-1 pr-2 text-right tabular-nums">{row.qty}</td>
                  <td className="py-1 pr-2 text-right tabular-nums">{formatCurrency(row.rate)}</td>
                  <td className="py-1 pr-2 text-right tabular-nums">
                    {row.discount_percentage
                      ? `${row.discount_percentage}%`
                      : row.discount_amount
                        ? formatCurrency(row.discount_amount)
                        : '—'}
                  </td>
                  <td className="py-1 text-right tabular-nums font-medium">
                    {formatCurrency(row.line_amount ?? row.qty * row.rate)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
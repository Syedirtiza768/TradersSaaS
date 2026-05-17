import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  Download,
  Eye,
  EyeOff,
  FileText,
  Printer,
} from 'lucide-react';
import { printApi } from '../lib/api';
import { formatCurrency, formatDate } from '../lib/utils';

type PrintItem = {
  item_code: string;
  item_name: string;
  description: string;
  qty: number;
  rate: number;
  amount: number;
  uom: string;
  is_bundle: number;
  bundle_description?: string;
  bundle_items?: Array<{ item_code: string; qty: number; rate: number; amount: number }>;
};

type Tax = { description: string; rate: number; tax_amount: number; total: number };

type PrintData = {
  doc_title: string;
  doc_format: string;
  view_mode: string;
  doctype: string;
  name: string;
  status: string;
  date: string;
  due_date: string;
  currency: string;
  company: { name: string; abbr: string; address: string; phone: string; email: string; website: string; tax_id: string };
  party: { name: string; display_name: string; address: string; tax_id: string };
  items: PrintItem[];
  taxes: Tax[];
  net_total: number;
  total_taxes: number;
  grand_total: number;
  rounded_total: number;
  outstanding_amount: number;
  paid_amount: number;
  in_words: string;
  terms: string;
  remarks: string;
  printed_on: string;
  bank_payment?: {
    account: string;
    account_name: string;
    bank: string;
    iban: string;
    branch_code: string;
    account_no: string;
  } | null;
};

type DocFormat = 'tax_invoice' | 'commercial_invoice' | 'proforma_invoice';
type ViewMode = 'external' | 'internal';

const FORMAT_OPTIONS: { value: DocFormat; label: string }[] = [
  { value: 'tax_invoice', label: 'Tax Invoice' },
  { value: 'commercial_invoice', label: 'Commercial Invoice' },
  { value: 'proforma_invoice', label: 'Proforma Invoice' },
];

export default function DocumentPrintPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const doctype = searchParams.get('doctype') || 'Sales Invoice';
  const docName = searchParams.get('name') || '';
  const autoprint = searchParams.get('autoprint') === '1';
  const returnTo = searchParams.get('return') || '';

  const [printData, setPrintData] = useState<PrintData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('external');
  const [docFormat, setDocFormat] = useState<DocFormat>('tax_invoice');
  const printRef = useRef<HTMLDivElement>(null);

  const loadPrintData = useCallback(async () => {
    if (!docName) { setError('Document name not specified.'); setLoading(false); return; }
    setLoading(true);
    setError(null);
    try {
      const res = await printApi.getPrintData(doctype, docName, viewMode, docFormat);
      setPrintData(res.data.message);
    } catch {
      setError('Could not load document data for printing.');
    } finally {
      setLoading(false);
    }
  }, [doctype, docName, viewMode, docFormat]);

  useEffect(() => { void loadPrintData(); }, [loadPrintData]);

  const handlePrint = () => {
    const el = printRef.current;
    if (!el) return;

    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>${printData?.doc_title || 'Document'} — ${docName}</title>
        <style>
          body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; margin: 0; padding: 20px; color: #1a1a1a; }
          @media print { body { padding: 0; } @page { margin: 15mm; } }
        </style>
      </head>
      <body>${el.innerHTML}</body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => { printWindow.print(); printWindow.close(); }, 300);
  };

  useEffect(() => {
    if (!autoprint || loading || !printData) return;
    const timer = window.setTimeout(() => handlePrint(), 400);
    return () => window.clearTimeout(timer);
  }, [autoprint, loading, printData]);

  const backPath = returnTo
    || (doctype === 'Quotation'
      ? `/sales/quotations/${encodeURIComponent(docName)}`
      : doctype === 'Sales Order'
        ? `/sales/orders/${encodeURIComponent(docName)}`
        : `/sales/${encodeURIComponent(docName)}`);

  if (loading) {
    return <div className="flex justify-center py-16"><div className="spinner" /></div>;
  }

  if (error || !printData) {
    return (
      <div className="space-y-4">
        <button onClick={() => navigate(-1)} className="btn-secondary inline-flex items-center gap-2">
          <ArrowLeft size={16} /> Go Back
        </button>
        <div className="card p-8 text-center text-gray-500">{error || 'Document not found.'}</div>
      </div>
    );
  }

  const showFormatToggle = doctype === 'Sales Invoice';

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Toolbar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <button onClick={() => navigate(backPath)} className="mb-3 inline-flex items-center gap-2 text-sm text-brand-700 hover:text-brand-800">
            <ArrowLeft size={16} /> {returnTo === '/sales/pos' ? 'Back to POS' : 'Back to Document'}
          </button>
          <h1 className="page-title">Print Preview</h1>
          <p className="mt-1 text-gray-500">{printData.doc_title} — {docName}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          {/* View Mode Toggle */}
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            <button
              onClick={() => setViewMode('external')}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm ${viewMode === 'external' ? 'bg-brand-50 text-brand-700 font-medium' : 'text-gray-600 hover:bg-gray-50'}`}
            >
              <EyeOff size={14} /> External
            </button>
            <button
              onClick={() => setViewMode('internal')}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm border-l border-gray-200 ${viewMode === 'internal' ? 'bg-brand-50 text-brand-700 font-medium' : 'text-gray-600 hover:bg-gray-50'}`}
            >
              <Eye size={14} /> Internal
            </button>
          </div>

          {/* Document Format Toggle (Invoices only) */}
          {showFormatToggle && (
            <select
              value={docFormat}
              onChange={(e) => setDocFormat(e.target.value as DocFormat)}
              className="input-field text-sm"
            >
              {FORMAT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          )}

          <button onClick={handlePrint} className="btn-primary flex items-center gap-2">
            <Printer size={14} /> Print
          </button>
        </div>
      </div>

      {/* View mode indicator */}
      <div className={`rounded-lg px-4 py-2 text-sm ${viewMode === 'internal' ? 'bg-amber-50 border border-amber-200 text-amber-800' : 'bg-blue-50 border border-blue-200 text-blue-800'}`}>
        {viewMode === 'internal'
          ? 'Internal View — Shows bundled item details for staff reference. Do not share with clients.'
          : 'External View — Client-facing view. Bundled items show only the overarching description.'}
      </div>

      {/* Print Content */}
      <div className="card">
        <div ref={printRef}>
          <div style={{ maxWidth: 800, margin: '0 auto', padding: '40px', fontFamily: "'Segoe UI', system-ui, sans-serif" }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32, borderBottom: '3px solid #1a365d', paddingBottom: 20 }}>
              <div>
                <h1 style={{ fontSize: 28, fontWeight: 800, color: '#1a365d', margin: 0, letterSpacing: 1 }}>{printData.doc_title}</h1>
                <p style={{ fontSize: 14, color: '#666', marginTop: 4 }}>{printData.name}</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <h2 style={{ fontSize: 16, fontWeight: 700, color: '#1a365d', margin: 0 }}>{printData.company.name}</h2>
                {printData.company.address && <p style={{ fontSize: 12, color: '#666', margin: '4px 0 0' }}>{printData.company.address}</p>}
                {printData.company.phone && <p style={{ fontSize: 12, color: '#666', margin: '2px 0 0' }}>Tel: {printData.company.phone}</p>}
                {printData.company.email && <p style={{ fontSize: 12, color: '#666', margin: '2px 0 0' }}>{printData.company.email}</p>}
                {printData.company.tax_id && <p style={{ fontSize: 12, color: '#666', margin: '2px 0 0' }}>NTN: {printData.company.tax_id}</p>}
              </div>
            </div>

            {/* Bill To + Document Info */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 32 }}>
              <div>
                <h3 style={{ fontSize: 11, fontWeight: 600, color: '#999', textTransform: 'uppercase', letterSpacing: 1, margin: '0 0 6px' }}>Bill To</h3>
                <p style={{ fontSize: 14, fontWeight: 600, color: '#1a1a1a', margin: 0 }}>{printData.party.display_name}</p>
                {printData.party.address && <p style={{ fontSize: 12, color: '#666', margin: '4px 0 0' }}>{printData.party.address}</p>}
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>
                  <strong>Date:</strong> {formatDate(printData.date)}
                </div>
                {printData.due_date && (
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>
                    <strong>{doctype === 'Quotation' ? 'Valid Till' : 'Due Date'}:</strong> {formatDate(printData.due_date)}
                  </div>
                )}
                <div style={{ fontSize: 12, color: '#666' }}>
                  <strong>Status:</strong> {printData.status}
                </div>
              </div>
            </div>

            {/* Items Table */}
            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 24 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
                  <th style={{ padding: '10px 12px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: '#666', textTransform: 'uppercase' }}>#</th>
                  <th style={{ padding: '10px 12px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: '#666', textTransform: 'uppercase' }}>Description</th>
                  <th style={{ padding: '10px 12px', textAlign: 'center', fontSize: 11, fontWeight: 600, color: '#666', textTransform: 'uppercase' }}>Qty</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right', fontSize: 11, fontWeight: 600, color: '#666', textTransform: 'uppercase' }}>Rate</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right', fontSize: 11, fontWeight: 600, color: '#666', textTransform: 'uppercase' }}>Amount</th>
                </tr>
              </thead>
              <tbody>
                {printData.items.map((item, idx) => (
                  <>
                    <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '10px 12px', fontSize: 13, color: '#666' }}>{idx + 1}</td>
                      <td style={{ padding: '10px 12px', fontSize: 13 }}>
                        <div style={{ fontWeight: item.is_bundle ? 600 : 400, color: '#1a1a1a' }}>
                          {item.is_bundle && viewMode === 'external'
                            ? (item.bundle_description || item.description)
                            : item.is_bundle
                              ? <><span style={{ color: '#7c3aed', fontSize: 10, fontWeight: 700, textTransform: 'uppercase', marginRight: 6 }}>BUNDLE</span>{item.bundle_description || item.description}</>
                              : item.description || item.item_name}
                        </div>
                        {!item.is_bundle && viewMode === 'internal' && item.item_code && (
                          <div style={{ fontSize: 11, color: '#999', marginTop: 2 }}>{item.item_code}</div>
                        )}
                      </td>
                      <td style={{ padding: '10px 12px', fontSize: 13, textAlign: 'center', color: '#1a1a1a' }}>{item.qty} {item.uom}</td>
                      <td style={{ padding: '10px 12px', fontSize: 13, textAlign: 'right', color: '#1a1a1a' }}>{formatCurrency(item.rate, printData.currency)}</td>
                      <td style={{ padding: '10px 12px', fontSize: 13, textAlign: 'right', fontWeight: 500, color: '#1a1a1a' }}>{formatCurrency(item.amount, printData.currency)}</td>
                    </tr>
                    {/* Internal mode: show bundle sub-items */}
                    {viewMode === 'internal' && item.is_bundle && item.bundle_items && item.bundle_items.map((sub, si) => (
                      <tr key={`${idx}-sub-${si}`} style={{ backgroundColor: '#fafafa' }}>
                        <td style={{ padding: '4px 12px' }}></td>
                        <td style={{ padding: '4px 12px', fontSize: 11, color: '#888', paddingLeft: 32 }}>↳ {sub.item_code}</td>
                        <td style={{ padding: '4px 12px', fontSize: 11, textAlign: 'center', color: '#888' }}>{sub.qty}</td>
                        <td style={{ padding: '4px 12px', fontSize: 11, textAlign: 'right', color: '#888' }}>{formatCurrency(sub.rate, printData.currency)}</td>
                        <td style={{ padding: '4px 12px', fontSize: 11, textAlign: 'right', color: '#888' }}>{formatCurrency(sub.amount, printData.currency)}</td>
                      </tr>
                    ))}
                  </>
                ))}
              </tbody>
            </table>

            {/* Totals */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 24 }}>
              <div style={{ width: 280 }}>
                <TotalRow label="Net Total" value={formatCurrency(printData.net_total, printData.currency)} />
                {printData.taxes.map((tax, i) => (
                  <TotalRow key={i} label={`${tax.description} (${tax.rate}%)`} value={formatCurrency(tax.tax_amount, printData.currency)} />
                ))}
                {printData.total_taxes > 0 && (
                  <TotalRow label="Total Taxes" value={formatCurrency(printData.total_taxes, printData.currency)} />
                )}
                <div style={{ borderTop: '2px solid #1a365d', marginTop: 8, paddingTop: 8 }}>
                  <TotalRow label="Grand Total" value={formatCurrency(printData.grand_total, printData.currency)} bold />
                </div>
                {printData.paid_amount > 0 && (
                  <TotalRow label="Paid Amount" value={formatCurrency(printData.paid_amount, printData.currency)} />
                )}
                {printData.outstanding_amount > 0 && (
                  <TotalRow label="Outstanding" value={formatCurrency(printData.outstanding_amount, printData.currency)} bold />
                )}
              </div>
            </div>

            {printData.bank_payment && (
              <div style={{ backgroundColor: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 6, padding: '12px 14px', marginBottom: 16, fontSize: 12, color: '#1e3a5f' }}>
                <strong style={{ display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 11 }}>Payment details</strong>
                {printData.bank_payment.bank && <div><strong>Bank:</strong> {printData.bank_payment.bank}</div>}
                <div><strong>Account:</strong> {printData.bank_payment.account_name}</div>
                {printData.bank_payment.account_no && <div><strong>Account No:</strong> {printData.bank_payment.account_no}</div>}
                {printData.bank_payment.iban && <div><strong>IBAN:</strong> {printData.bank_payment.iban}</div>}
                {printData.bank_payment.branch_code && <div><strong>Branch:</strong> {printData.bank_payment.branch_code}</div>}
              </div>
            )}

            {/* Amount in Words */}
            {printData.in_words && (
              <div style={{ backgroundColor: '#f8fafc', borderRadius: 6, padding: '10px 14px', marginBottom: 16, fontSize: 12, color: '#444' }}>
                <strong>Amount in Words:</strong> {printData.in_words}
              </div>
            )}

            {/* Terms */}
            {printData.terms && (
              <div style={{ marginBottom: 16, fontSize: 12, color: '#666' }}>
                <strong>Terms & Conditions:</strong>
                <div style={{ marginTop: 4, whiteSpace: 'pre-wrap' }}>{printData.terms}</div>
              </div>
            )}

            {/* Footer */}
            <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: 16, marginTop: 32, display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#999' }}>
              <span>Generated on {formatDate(printData.printed_on)}</span>
              <span>{printData.company.name}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TotalRow({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 13, fontWeight: bold ? 700 : 400, color: bold ? '#1a1a1a' : '#555' }}>
      <span>{label}</span>
      <span>{value}</span>
    </div>
  );
}

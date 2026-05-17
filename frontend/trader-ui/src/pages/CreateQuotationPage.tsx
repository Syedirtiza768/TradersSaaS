import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Plus, Save, Trash2 } from 'lucide-react';
import { customersApi, gstApi, inventoryApi, salesApi } from '../lib/api';
import { appendPreservedListQuery, formatCurrency } from '../lib/utils';
import SearchableSelect from '../components/SearchableSelect';
import useQuickAdd from '../components/useQuickAdd';
import QuickAddProvider from '../components/QuickAddProvider';

type QuotationLine = {
  item_code: string;
  description: string;
  qty: number;
  rate: number;
};

const EMPTY_LINE: QuotationLine = { item_code: '', description: '', qty: 1, rate: 0 };

export default function CreateQuotationPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const isProforma = location.pathname.includes('/proforma/') || searchParams.get('type') === 'proforma_invoice';
  const [customers, setCustomers] = useState<any[]>([]);
  const [items, setItems] = useState<any[]>([]);
  const [customer, setCustomer] = useState('');
  const [transactionDate, setTransactionDate] = useState(today());
  const [validTill, setValidTill] = useState(today());
  const [lines, setLines] = useState<QuotationLine[]>([{ ...EMPTY_LINE }]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [taxTemplates, setTaxTemplates] = useState<any[]>([]);
  const [taxTemplate, setTaxTemplate] = useState('');
  const [taxRate, setTaxRate] = useState(0);
  const [taxInclusive, setTaxInclusive] = useState(false);
  const listSearch = searchParams.get('list');
  const quickAdd = useQuickAdd();
  const quickAddItemLine = useRef<number>(-1);

  useEffect(() => {
    const customerParam = searchParams.get('customer');
    if (customerParam) setCustomer(customerParam);
  }, [searchParams]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [customersRes, itemsRes, taxRes] = await Promise.all([
          customersApi.getList({ page: 1, page_size: 100 }),
          inventoryApi.getItems({ page: 1, page_size: 100 }),
          gstApi.getTaxTemplates('Sales'),
        ]);
        setCustomers(customersRes.data.message?.data || []);
        setItems(itemsRes.data.message?.data || []);
        const templates = taxRes.data.message?.templates || taxRes.data.message || [];
        setTaxTemplates(templates);
        // Auto-select default template if available
        const defaultTpl = templates.find((t: any) => t.is_default);
        if (defaultTpl) {
          setTaxTemplate(defaultTpl.name);
          setTaxRate(parseFloat(defaultTpl.total_tax_rate || defaultTpl.tax_rate || 0));
        }
      } catch (err) {
        console.error('Failed to load quotation form data:', err);
        setError('Could not load customers and items.');
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  const total = useMemo(
    () => lines.reduce((sum, l) => sum + (Number(l.qty) || 0) * (Number(l.rate) || 0), 0),
    [lines],
  );
  const taxAmount = useMemo(() => {
    if (!taxRate) return 0;
    if (taxInclusive) return total - total / (1 + taxRate / 100);
    return total * taxRate / 100;
  }, [total, taxRate, taxInclusive]);
  const grandTotal = useMemo(() => taxInclusive ? total : total + taxAmount, [total, taxAmount, taxInclusive]);
  const validLineCount = useMemo(
    () => lines.filter((l) => l.item_code && Number(l.qty) > 0).length,
    [lines],
  );
  const isReadyToSave = Boolean(customer) && validLineCount > 0;

  const updateLine = (index: number, patch: Partial<QuotationLine>) => {
    setLines((current) => current.map((line, i) => (i === index ? { ...line, ...patch } : line)));
  };

  const addLine = () => setLines((current) => [...current, { ...EMPTY_LINE }]);

  const removeLine = (index: number) => {
    setLines((current) => (current.length > 1 ? current.filter((_, i) => i !== index) : current));
  };

  const handleItemChange = (index: number, itemCode: string) => {
    const selected = items.find((item) => item.item_code === itemCode || item.name === itemCode);
    updateLine(index, {
      item_code: itemCode,
      description: selected?.description || selected?.item_name || '',
      rate: selected?.selling_price ?? selected?.standard_rate ?? 0,
    });
  };

  const handleTaxTemplateChange = (templateName: string) => {
    setTaxTemplate(templateName);
    const tpl = taxTemplates.find((t: any) => t.name === templateName);
    setTaxRate(tpl ? parseFloat(tpl.total_tax_rate || tpl.tax_rate || 0) : 0);
  };

  const handleSubmit = async () => {
    if (!customer) {
      setError('Please select a customer.');
      return;
    }
    const validLines = lines.filter((l) => l.item_code && Number(l.qty) > 0);
    if (validLines.length === 0) {
      setError('Add at least one valid item line.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const response = await salesApi.createQuotation({
        customer,
        transaction_date: transactionDate,
        valid_till: validTill,
        items: validLines.map((l) => ({ item_code: l.item_code, description: l.description || undefined, qty: l.qty, rate: l.rate })),
        taxes_and_charges: taxTemplate || undefined,
        tax_inclusive: taxInclusive ? 1 : 0,
        invoice_type: isProforma ? 'proforma_invoice' : 'quotation',
      });
      const created = response.data.message;
      navigate(appendPreservedListQuery(`/sales/quotations/${encodeURIComponent(created.name)}`, listSearch));
    } catch (err: any) {
      console.error('Failed to create quotation:', err);
      setError(err?.response?.data?.exception || 'Could not create quotation.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <button onClick={() => navigate('/sales/quotations')} className="mb-3 inline-flex items-center gap-2 text-sm text-brand-700 hover:text-brand-800">
            <ArrowLeft size={16} /> Back to Quotations
          </button>
          <h1 className="page-title">{isProforma ? 'New Proforma Invoice' : 'New Quotation'}</h1>
          <p className="mt-1 text-gray-500">
            {isProforma ? 'Create a non-binding proforma before issuing a tax invoice.' : 'Create a draft quotation for a customer.'}
          </p>
        </div>
        <button onClick={handleSubmit} disabled={saving || loading || !isReadyToSave} className="btn-primary flex items-center gap-2 disabled:opacity-60">
          <Save size={14} /> {saving ? 'Creating…' : 'Create Draft'}
        </button>
      </div>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="card p-6 lg:col-span-2 space-y-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Field label="Customer">
              <SearchableSelect
                value={customer}
                onChange={setCustomer}
                options={customers.map((e) => ({ label: e.customer_name || e.name, value: e.name }))}
                placeholder="Select customer"
                disabled={loading}
                creatable
                onCreateNew={(query) => quickAdd.open('customer', query)}
              />
            </Field>
            <Field label="Quotation Date">
              <input type="date" value={transactionDate} onChange={(e) => setTransactionDate(e.target.value)} className="input-field" />
            </Field>
            <Field label="Valid Till">
              <input type="date" value={validTill} onChange={(e) => setValidTill(e.target.value)} className="input-field" />
            </Field>
            <Field label="Tax Template">
              <SearchableSelect
                value={taxTemplate}
                onChange={handleTaxTemplateChange}
                options={[
                  { label: 'No Tax', value: '' },
                  ...taxTemplates.map((t: any) => ({ label: `${t.title || t.name} (${parseFloat(t.total_tax_rate || t.tax_rate || 0)}%)`, value: t.name })),
                ]}
                placeholder="Select tax template"
              />
            </Field>
          </div>

          {taxTemplate && taxRate > 0 && (
            <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 px-4 py-2">
              <span className="text-xs font-medium uppercase tracking-wide text-gray-500">Tax Mode</span>
              <button
                onClick={() => setTaxInclusive(false)}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                  !taxInclusive ? 'bg-brand-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-100'
                }`}
              >
                Exclusive
              </button>
              <button
                onClick={() => setTaxInclusive(true)}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                  taxInclusive ? 'bg-brand-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-100'
                }`}
              >
                Inclusive
              </button>
              <span className="text-xs text-gray-400 ml-1">
                {taxInclusive ? 'Rates entered include tax' : 'Tax added on top of rates'}
              </span>
            </div>
          )}

          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-700">Line Items</h3>
              <button onClick={addLine} className="btn-secondary text-xs flex items-center gap-1">
                <Plus size={12} /> Add Line
              </button>
            </div>

            <div className="space-y-3">
              {lines.map((line, i) => (
                <div key={i} className="rounded-lg border border-gray-200 p-4 space-y-3 hover:border-gray-300 transition-colors">
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-[2fr_1fr_1fr_1fr_auto]">
                    <Field label="Item">
                      <SearchableSelect
                        value={line.item_code}
                        onChange={(v) => handleItemChange(i, v)}
                        options={items.map((item) => ({ label: item.item_name || item.item_code || item.name, value: item.item_code || item.name }))}
                        placeholder="Select item"
                        className="text-sm"
                        creatable
                        onCreateNew={(query) => { quickAddItemLine.current = i; quickAdd.open('item', query); }}
                      />
                    </Field>
                    <Field label="Qty">
                      <input type="number" min="1" value={line.qty} onChange={(e) => updateLine(i, { qty: Number(e.target.value) || 0 })} className="input-field text-right text-sm" />
                    </Field>
                    <Field label="Rate">
                      <input type="number" min="0" step="0.01" value={line.rate} onChange={(e) => updateLine(i, { rate: Number(e.target.value) || 0 })} className="input-field text-right text-sm" />
                    </Field>
                    <Field label="Amount">
                      <div className="input-field bg-gray-50 text-right text-sm font-medium text-gray-900">
                        {formatCurrency((Number(line.qty) || 0) * (Number(line.rate) || 0))}
                      </div>
                    </Field>
                    <div className="flex items-end">
                      <button onClick={() => removeLine(i)} disabled={lines.length <= 1} className="rounded-lg border border-gray-200 p-2.5 text-gray-400 hover:text-red-600 disabled:opacity-30">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                  <Field label="Description (shown on external/client-facing documents)">
                    <textarea
                      value={line.description}
                      onChange={(e) => updateLine(i, { description: e.target.value })}
                      placeholder="Enter line description for client-facing view..."
                      rows={2}
                      className="input-field text-sm resize-none"
                    />
                  </Field>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card p-6 space-y-4">
          <h3 className="text-sm font-semibold text-gray-700">Summary</h3>
          <SummaryLine label="Lines" value={String(validLineCount)} />
          {taxInclusive && taxRate > 0 ? (
            <>
              <SummaryLine label="Entered Total (incl. tax)" value={formatCurrency(total)} />
              <SummaryLine label={`GST (${taxRate}%) included`} value={formatCurrency(taxAmount)} />
              <SummaryLine label="Net Total (excl. tax)" value={formatCurrency(total - taxAmount)} />
            </>
          ) : (
            <>
              <SummaryLine label="Net Total" value={formatCurrency(total)} />
              {taxTemplate && taxRate > 0 && (
                <SummaryLine label={`Tax (${taxRate}%)`} value={formatCurrency(taxAmount)} />
              )}
            </>
          )}
          <hr className="border-gray-100" />
          <SummaryLine label="Grand Total" value={formatCurrency(grandTotal)} highlight />
          <hr className="border-gray-100" />
          <h4 className="text-xs font-medium text-gray-500 uppercase">Readiness</h4>
          <ReadinessCheck label="Customer selected" passed={Boolean(customer)} />
          <ReadinessCheck label="At least one item line" passed={validLineCount > 0} />
        </div>
      </div>

      <QuickAddProvider
        quickAdd={quickAdd}
        customersSetter={setCustomers}
        customerValueSetter={setCustomer}
        itemsSetter={setItems}
        itemValueSetter={(v) => { if (quickAddItemLine.current >= 0) handleItemChange(quickAddItemLine.current, v); }}
      />
    </div>
  );
}

function today(): string {
  return new Date().toISOString().split('T')[0];
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="block">
      <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-500">{label}</span>
      {children}
    </div>
  );
}

function SummaryLine({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-sm text-gray-500">{label}</span>
      <span className={`text-sm font-medium ${highlight ? 'text-gray-900 text-lg' : 'text-gray-700'}`}>{value}</span>
    </div>
  );
}

function ReadinessCheck({ label, passed }: { label: string; passed: boolean }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className={`w-2 h-2 rounded-full ${passed ? 'bg-green-500' : 'bg-red-400'}`} />
      <span className={passed ? 'text-gray-600' : 'text-red-600'}>{label}</span>
    </div>
  );
}

import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Plus, Save, Trash2 } from 'lucide-react';
import BarcodeScanInput from '../components/BarcodeScanInput';
import { currencyApi, gstApi, inventoryApi, purchasesApi, suppliersApi } from '../lib/api';
import { useCompanyStore } from '../stores/companyStore';
import { getPurchaseInvoiceTypeConfig, pickExemptTaxTemplate } from '../lib/invoiceTypes';
import { appendPreservedListQuery, formatCurrency, isOperationsContext } from '../lib/utils';
import SearchableSelect from '../components/SearchableSelect';
import useQuickAdd from '../components/useQuickAdd';
import QuickAddProvider from '../components/QuickAddProvider';

type InvoiceLine = {
  item_code: string;
  qty: number;
  rate: number;
  warehouse: string;
  serial_no: string;
  has_serial_no?: boolean;
  serial_error?: string | null;
};

const EMPTY_LINE: InvoiceLine = {
  item_code: '',
  qty: 1,
  rate: 0,
  warehouse: '',
  serial_no: '',
};

function getLineIssues(line: { item_code: string; qty: number; rate: number }) {
  const issues: string[] = [];
  if (!line.item_code) issues.push('Select an item');
  if (!(Number(line.qty) > 0)) issues.push('Enter a quantity greater than 0');
  if (!(Number(line.rate) > 0)) issues.push('Review the rate');
  return issues;
}

export default function CreatePurchaseInvoicePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [items, setItems] = useState<any[]>([]);
  const [supplier, setSupplier] = useState('');
  const [postingDate, setPostingDate] = useState(today());
  const [dueDate, setDueDate] = useState(today());
  const [lines, setLines] = useState<InvoiceLine[]>([{ ...EMPTY_LINE }]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [taxTemplates, setTaxTemplates] = useState<any[]>([]);
  const [taxTemplate, setTaxTemplate] = useState('');
  const [taxRate, setTaxRate] = useState(0);
  const [taxInclusive, setTaxInclusive] = useState(false);
  const invoiceTypeKey = searchParams.get('type') || 'tax_invoice';
  const typeConfig = getPurchaseInvoiceTypeConfig(invoiceTypeKey);
  const sourceType = searchParams.get('sourceType');
  const sourceName = searchParams.get('sourceName');
  const listSearch = searchParams.get('list');
  const prefillsLineCount = searchParams.get('lines') ? lines.filter((line) => line.item_code).length : 0;
  const backToPath = listSearch
    ? isOperationsContext(listSearch)
      ? `/operations?${listSearch}`
      : '/purchases'
    : '/purchases';
  const backLabel = listSearch && isOperationsContext(listSearch) ? 'Back to Operations' : 'Back to Purchases';
  const quickAdd = useQuickAdd();
  const quickAddItemLine = useRef<number>(-1);
  const [scanValue, setScanValue] = useState('');
  const [defaultWarehouse, setDefaultWarehouse] = useState('');
  const baseCurrency = useCompanyStore((s) => s.currency) || 'PKR';
  const [multiCurrencyOn, setMultiCurrencyOn] = useState(false);
  const [currency, setCurrency] = useState(baseCurrency);
  const [exchangeRate, setExchangeRate] = useState(1);
  const [currencies, setCurrencies] = useState<{ name: string }[]>([]);
  const companyRevision = useCompanyStore((s) => s.revision);

  useEffect(() => {
    const supplierParam = searchParams.get('supplier');
    const postingDateParam = searchParams.get('postingDate') || searchParams.get('transactionDate');
    const dueDateParam = searchParams.get('dueDate') || searchParams.get('scheduleDate');
    const linesParam = searchParams.get('lines');

    if (supplierParam) setSupplier(supplierParam);
    if (postingDateParam) setPostingDate(postingDateParam);
    if (dueDateParam) setDueDate(dueDateParam);
    if (linesParam) {
      try {
        const parsed = JSON.parse(decodeURIComponent(linesParam));
        if (Array.isArray(parsed) && parsed.length > 0) {
          setLines(parsed.map((line) => ({
            item_code: line.item_code || '',
            qty: Number(line.qty) || 1,
            rate: Number(line.rate) || 0,
            warehouse: line.warehouse || '',
            serial_no: line.serial_no || '',
          })));
        }
      } catch (err) {
        console.error('Failed to parse purchase invoice line prefills:', err);
      }
    }
  }, [searchParams]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [suppliersRes, itemsRes, taxRes, warehousesRes, currencyRes] = await Promise.all([
          suppliersApi.getList({ page: 1, page_size: 100 }),
          inventoryApi.getItems({ page: 1, page_size: 100 }),
          gstApi.getTaxTemplates('Purchase'),
          inventoryApi.getWarehouses(),
          currencyApi.getOptions(),
        ]);
        setSuppliers(suppliersRes.data.message?.data || []);
        setItems(itemsRes.data.message?.data || []);
        const warehouseRows = warehousesRes.data.message || [];
        const mainWh = warehouseRows.find((w: any) => /main warehouse/i.test(w.warehouse_name || w.warehouse || ''))
          || warehouseRows[0];
        const wh = mainWh?.warehouse || '';
        setDefaultWarehouse(wh);
        setLines((current) => current.map((line) => ({ ...line, warehouse: line.warehouse || wh })));
        const curMsg = currencyRes.data.message || {};
        const multiOn = Boolean(curMsg.multi_currency_enabled);
        setMultiCurrencyOn(multiOn);
        setCurrencies(curMsg.currencies || []);
        setCurrency(curMsg.base_currency || baseCurrency);
        setExchangeRate(1);
        const templates = taxRes.data.message?.templates || taxRes.data.message || [];
        setTaxTemplates(templates);
        if (typeConfig.noTaxByDefault) {
          setTaxTemplate('');
          setTaxRate(0);
        } else if (typeConfig.useExemptTax) {
          const exempt = pickExemptTaxTemplate(templates);
          setTaxTemplate(exempt);
          const tpl = templates.find((t: any) => t.name === exempt);
          setTaxRate(tpl ? parseFloat(tpl.total_tax_rate || tpl.tax_rate || 0) : 0);
        } else {
          const defaultTpl = templates.find((t: any) => t.is_default);
          if (defaultTpl) {
            setTaxTemplate(defaultTpl.name);
            setTaxRate(parseFloat(defaultTpl.total_tax_rate || defaultTpl.tax_rate || 0));
          }
        }
      } catch (err) {
        console.error('Failed to load purchase form data:', err);
        setError('Could not load suppliers and items for invoice creation.');
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [invoiceTypeKey, companyRevision, baseCurrency]);

  useEffect(() => {
    if (!multiCurrencyOn || !currency || currency === baseCurrency) {
      setExchangeRate(1);
      return;
    }
    const loadRate = async () => {
      try {
        const res = await currencyApi.getExchangeRate(currency, postingDate, 'buying');
        setExchangeRate(Number(res.data.message?.exchange_rate) || 1);
      } catch {
        setExchangeRate(1);
      }
    };
    void loadRate();
  }, [currency, baseCurrency, postingDate, multiCurrencyOn]);

  const total = useMemo(
    () => lines.reduce((sum, line) => sum + (Number(line.qty) || 0) * (Number(line.rate) || 0), 0),
    [lines],
  );
  const taxAmount = useMemo(() => {
    if (!taxRate) return 0;
    if (taxInclusive) return total - total / (1 + taxRate / 100);
    return total * taxRate / 100;
  }, [total, taxRate, taxInclusive]);
  const grandTotal = useMemo(() => taxInclusive ? total : total + taxAmount, [total, taxAmount, taxInclusive]);
  const validLineCount = useMemo(
    () => lines.filter((line) => line.item_code && Number(line.qty) > 0).length,
    [lines],
  );
  const readinessChecks = useMemo(
    () => [
      { label: 'Supplier selected', passed: Boolean(supplier) },
      { label: 'At least one valid item line', passed: validLineCount > 0 },
    ],
    [supplier, validLineCount],
  );
  const readinessIssues = readinessChecks.filter((check) => !check.passed).map((check) => check.label);
  const isReadyToSave = readinessIssues.length === 0;

  const updateLine = (index: number, patch: Partial<InvoiceLine>) => {
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
      rate: selected?.buying_price ?? selected?.last_purchase_rate ?? selected?.valuation_rate ?? selected?.standard_rate ?? 0,
      has_serial_no: Boolean(selected?.has_serial_no),
      serial_no: '',
      serial_error: null,
    });
  };

  const handleBarcodeScan = async (barcode: string) => {
    try {
      const res = await inventoryApi.lookupByBarcode(barcode);
      const msg = res.data.message;
      if (!msg?.found || !msg.item) {
        setError(msg?.message || `No item for barcode ${barcode}`);
        return;
      }
      const item = msg.item;
      setLines((prev) => [
        ...prev,
        {
          item_code: item.item_code,
          qty: 1,
          rate: Number(item.buying_price) || 0,
          warehouse: item.default_warehouse || defaultWarehouse,
          serial_no: '',
          has_serial_no: Boolean(item.has_serial_no),
          serial_error: null,
        },
      ]);
      setError(null);
    } catch (err: any) {
      setError(err?.response?.data?.exception || 'Barcode lookup failed.');
    }
  };

  const validatePurchaseSerial = async (index: number) => {
    const line = lines[index];
    if (!line?.item_code || !line.serial_no?.trim()) {
      updateLine(index, { serial_error: null });
      return true;
    }
    try {
      const res = await inventoryApi.validateSerialForPurchase({
        item_code: line.item_code,
        serial_no: line.serial_no.trim(),
      });
      const result = res.data.message;
      if (!result?.valid) {
        updateLine(index, { serial_error: result?.message || 'Invalid serial.' });
        return false;
      }
      updateLine(index, { serial_error: null });
      return true;
    } catch {
      updateLine(index, { serial_error: 'Could not validate serial.' });
      return false;
    }
  };

  const handleTaxTemplateChange = (templateName: string) => {
    setTaxTemplate(templateName);
    const tpl = taxTemplates.find((t: any) => t.name === templateName);
    setTaxRate(tpl ? parseFloat(tpl.total_tax_rate || tpl.tax_rate || 0) : 0);
  };

  const handleSubmit = async () => {
    if (!supplier) {
      setError('Please select a supplier before creating the invoice.');
      return;
    }

    const validLines = lines.filter((line) => line.item_code && Number(line.qty) > 0);
    if (validLines.length === 0) {
      setError('Add at least one valid item line.');
      return;
    }

    const seenSerials = new Map<string, number>();
    for (let i = 0; i < lines.length; i++) {
      const serial = lines[i].serial_no?.trim();
      if (serial) {
        const prior = seenSerials.get(serial.toLowerCase());
        if (prior !== undefined) {
          setError(`Duplicate serial ${serial} on lines ${prior + 1} and ${i + 1}.`);
          return;
        }
        seenSerials.set(serial.toLowerCase(), i);
      }
    }

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.item_code && line.serial_no?.trim()) {
        const ok = await validatePurchaseSerial(i);
        if (!ok) {
          setError(line.serial_error || `Invalid serial on line ${i + 1}.`);
          return;
        }
      }
    }

    setSaving(true);
    setError(null);
    try {
      const response = await purchasesApi.createInvoice({
        supplier,
        posting_date: postingDate,
        due_date: dueDate,
        items: validLines.map((l) => ({
          item_code: l.item_code,
          qty: l.qty,
          rate: l.rate,
          warehouse: l.warehouse || defaultWarehouse,
          serial_no: l.serial_no?.trim() || undefined,
        })),
        taxes_and_charges: taxTemplate || undefined,
        tax_inclusive: taxInclusive ? 1 : 0,
        invoice_type: invoiceTypeKey,
        currency: currency !== baseCurrency ? currency : undefined,
        exchange_rate: currency !== baseCurrency ? exchangeRate : undefined,
      });
      const created = response.data.message;
      navigate(appendPreservedListQuery(`/purchases/${encodeURIComponent(created.name)}`, listSearch));
    } catch (err: any) {
      console.error('Failed to create purchase invoice:', err);
      const data = err?.response?.data;
      let message = 'Could not create purchase invoice.';
      if (data) {
        if (data.exception) {
          // Strip the Python exception class prefix if present, e.g. "frappe.exceptions.ValidationError: ..."
          message = String(data.exception).replace(/^[\w.]+Error:\s*/i, '').trim() || message;
        } else if (data.message) {
          message = String(data.message);
        } else if (data._server_messages) {
          try {
            const msgs = JSON.parse(data._server_messages) as string[];
            const parsed = msgs.map((m) => { try { return JSON.parse(m).message; } catch { return m; } });
            message = parsed.filter(Boolean).join(' ') || message;
          } catch { /* fallback to generic */ }
        }
      }
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <button onClick={() => navigate(backToPath)} className="mb-3 inline-flex items-center gap-2 text-sm text-brand-700 hover:text-brand-800">
            <ArrowLeft size={16} /> {backLabel}
          </button>
          <h1 className="page-title">New {typeConfig.label}</h1>
          <p className="mt-1 text-gray-500">Create a draft purchase invoice using the existing ERPNext workflow.</p>
        </div>
        <button onClick={handleSubmit} disabled={saving || loading} className="btn-primary flex items-center gap-2 disabled:opacity-60">
          <Save size={14} /> {saving ? 'Creating…' : 'Create Draft'}
        </button>
      </div>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      {(sourceType || sourceName) && (
        <PrefillBanner
          sourceType={sourceType}
          sourceName={sourceName}
          fields={[
            supplier ? 'supplier' : null,
            postingDate ? 'posting date' : null,
            dueDate ? 'due date' : null,
            prefillsLineCount > 0 ? `${prefillsLineCount} item line${prefillsLineCount === 1 ? '' : 's'}` : null,
          ]}
        />
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="card p-6 lg:col-span-2 space-y-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <Field label="Supplier">
              <SearchableSelect
                value={supplier}
                onChange={setSupplier}
                options={suppliers.map((e) => ({ label: e.supplier_name || e.name, value: e.name }))}
                placeholder="Select supplier"
                disabled={loading}
                creatable
                onCreateNew={(query) => quickAdd.open('supplier', query)}
              />
            </Field>
            <Field label="Posting Date">
              <input type="date" value={postingDate} onChange={(e) => setPostingDate(e.target.value)} className="input-field" />
            </Field>
            <Field label="Due Date">
              <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} className="input-field" />
            </Field>
            {multiCurrencyOn && (
              <>
                <Field label="Currency">
                  <select value={currency} onChange={(e) => setCurrency(e.target.value)} className="input-field text-sm">
                    {currencies.map((c) => (
                      <option key={c.name} value={c.name}>{c.name}</option>
                    ))}
                  </select>
                </Field>
                {currency !== baseCurrency && (
                  <Field label={`FX rate (→ ${baseCurrency})`}>
                    <input
                      type="number"
                      min={0}
                      step="0.0001"
                      value={exchangeRate}
                      onChange={(e) => setExchangeRate(Number(e.target.value) || 1)}
                      className="input-field text-sm"
                    />
                  </Field>
                )}
              </>
            )}
            {!typeConfig.hideTaxPicker && (
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
            )}
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

          <div className="space-y-4">
            <BarcodeScanInput
              value={scanValue}
              onChange={setScanValue}
              onScan={handleBarcodeScan}
              disabled={loading || saving}
            />
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Invoice Items</h2>
              <button onClick={addLine} className="btn-secondary flex items-center gap-2">
                <Plus size={14} /> Add Line
              </button>
            </div>

            <div className="space-y-3">
              {lines.map((line, index) => (
                <div key={index} className={`grid grid-cols-1 gap-3 rounded-lg border p-4 md:grid-cols-[2fr_1fr_1fr_auto] ${getLineIssues(line).length > 0 ? 'border-amber-200 bg-amber-50/50' : 'border-gray-200'}`}>
                  <Field label="Item">
                    <SearchableSelect
                      value={line.item_code}
                      onChange={(v) => handleItemChange(index, v)}
                      options={items.map((e) => ({ label: e.item_name || e.item_code || e.name, value: e.item_code || e.name }))}
                      placeholder="Select item"
                      disabled={loading}
                      error={!line.item_code}
                      creatable
                      onCreateNew={(query) => { quickAddItemLine.current = index; quickAdd.open('item', query); }}
                    />
                  </Field>
                  <Field label="Qty">
                    <input type="number" min={1} step="0.01" value={line.qty} onChange={(e) => updateLine(index, { qty: Number(e.target.value) })} className={`input-field ${!(Number(line.qty) > 0) ? 'border-amber-300 focus:border-amber-500 focus:ring-amber-500' : ''}`} />
                  </Field>
                  <Field label="Rate">
                    <input type="number" min={0} step="0.01" value={line.rate} onChange={(e) => updateLine(index, { rate: Number(e.target.value) })} className={`input-field ${!(Number(line.rate) > 0) ? 'border-amber-300 focus:border-amber-500 focus:ring-amber-500' : ''}`} />
                  </Field>
                  {line.has_serial_no && (
                    <Field label="Serial">
                      <input
                        value={line.serial_no}
                        onChange={(e) => updateLine(index, { serial_no: e.target.value, serial_error: null })}
                        onBlur={() => void validatePurchaseSerial(index)}
                        placeholder="Scan serial"
                        className={`input-field font-mono text-sm ${line.serial_error ? 'border-red-300' : ''}`}
                      />
                      {line.serial_error && (
                        <p className="mt-1 text-xs text-red-600">{line.serial_error}</p>
                      )}
                    </Field>
                  )}
                  <div className="flex items-end">
                    <button onClick={() => removeLine(index)} disabled={lines.length === 1} className="rounded-lg border border-gray-200 p-3 text-gray-500 hover:text-red-600 disabled:opacity-40">
                      <Trash2 size={16} />
                    </button>
                  </div>
                  <div className="md:col-span-4 flex items-center justify-between rounded-md bg-gray-50 px-3 py-2 text-sm">
                    <span className="text-gray-500">Line Amount</span>
                    <span className="font-semibold text-gray-900">{formatCurrency((Number(line.qty) || 0) * (Number(line.rate) || 0))}</span>
                  </div>
                  {getLineIssues(line).length > 0 && (
                    <div className="md:col-span-4 rounded-md border border-amber-200 bg-white px-3 py-2 text-xs text-amber-800">
                      Line {index + 1}: {getLineIssues(line).join(' • ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Summary</h2>
          <ReadinessCard ready={isReadyToSave} issues={readinessIssues} />
          <div className="rounded-lg bg-gray-900 px-4 py-3 text-white">
            <div className="text-xs uppercase tracking-wide text-gray-300">Draft Grand Total</div>
            <div className="mt-1 text-2xl font-semibold">{formatCurrency(grandTotal)}</div>
          </div>
          <SummaryRow label="Valid Lines" value={String(validLineCount)} />
          {taxInclusive && taxRate > 0 ? (
            <>
              <SummaryRow label="Entered Total (incl. tax)" value={formatCurrency(total)} />
              <SummaryRow label={`GST (${taxRate}%) included`} value={formatCurrency(taxAmount)} />
              <SummaryRow label="Net Total (excl. tax)" value={formatCurrency(total - taxAmount)} />
            </>
          ) : (
            <>
              <SummaryRow label="Net Total" value={formatCurrency(total)} />
              {taxRate > 0 && (
                <SummaryRow label={`Tax (${taxRate}%)`} value={formatCurrency(taxAmount)} />
              )}
            </>
          )}
          <SummaryRow label="Grand Total" value={formatCurrency(grandTotal)} />
          <SummaryRow label="Posting Date" value={postingDate} />
          <SummaryRow label="Due Date" value={dueDate} />
          <p className="text-xs leading-5 text-gray-500">
            This creates a draft Purchase Invoice through the existing whitelisted backend method and then opens the detail screen.
          </p>
        </div>
      </div>

      <QuickAddProvider
        quickAdd={quickAdd}
        suppliersSetter={setSuppliers}
        supplierValueSetter={setSupplier}
        itemsSetter={setItems}
        itemValueSetter={(v) => { if (quickAddItemLine.current >= 0) handleItemChange(quickAddItemLine.current, v); }}
      />
    </div>
  );
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="block">
      <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-500">{label}</span>
      {children}
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-900">{value}</span>
    </div>
  );
}

function ReadinessCard({ ready, issues }: { ready: boolean; issues: string[] }) {
  return (
    <div className={`rounded-lg border px-4 py-3 text-sm ${ready ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-amber-200 bg-amber-50 text-amber-900'}`}>
      <div className="font-medium">{ready ? 'Ready to create draft' : 'Needs attention before create'}</div>
      {ready ? (
        <p className="mt-1 text-xs text-emerald-700">Required supplier and item line checks are satisfied.</p>
      ) : (
        <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-amber-800">
          {issues.map((issue) => (
            <li key={issue}>{issue}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function PrefillBanner({
  sourceType,
  sourceName,
  fields,
}: {
  sourceType: string | null;
  sourceName: string | null;
  fields: Array<string | null>;
}) {
  const cleanFields = fields.filter(Boolean) as string[];
  const sourceLabel = sourceType === 'purchase-order' ? 'purchase order' : 'upstream document';

  return (
    <div className="rounded-lg border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-900">
      Prefilled from {sourceLabel}{sourceName ? ` ${sourceName}` : ''}
      {cleanFields.length > 0 ? ` with ${cleanFields.join(', ')}.` : '.'}
    </div>
  );
}
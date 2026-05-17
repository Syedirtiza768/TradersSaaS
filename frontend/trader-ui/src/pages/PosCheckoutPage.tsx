import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Minus, Plus, Save, Trash2 } from 'lucide-react';
import BarcodeScanInput from '../components/BarcodeScanInput';
import SearchableSelect from '../components/SearchableSelect';
import { currencyApi, customersApi, financeApi, gstApi, inventoryApi, posApi } from '../lib/api';
import { formatCurrency } from '../lib/utils';
import { useCompanyStore } from '../stores/companyStore';

type CartLine = {
  item_code: string;
  item_name: string;
  qty: number;
  rate: number;
  warehouse: string;
  serial_no: string;
  has_serial_no: boolean;
  serial_error: string | null;
  stock_qty: number | null;
};

export default function PosCheckoutPage() {
  const navigate = useNavigate();
  const companyRevision = useCompanyStore((s) => s.revision);
  const baseCurrency = useCompanyStore((s) => s.currency) || 'PKR';
  const [multiCurrencyOn, setMultiCurrencyOn] = useState(false);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scanValue, setScanValue] = useState('');
  const [customers, setCustomers] = useState<any[]>([]);
  const [customer, setCustomer] = useState('');
  const [warehouse, setWarehouse] = useState('');
  const [cart, setCart] = useState<CartLine[]>([]);
  const [taxTemplates, setTaxTemplates] = useState<any[]>([]);
  const [taxTemplate, setTaxTemplate] = useState('');
  const [taxRate, setTaxRate] = useState(0);
  const [currency, setCurrency] = useState(baseCurrency);
  const [exchangeRate, setExchangeRate] = useState(1);
  const [currencies, setCurrencies] = useState<{ name: string }[]>([]);
  const [recordPayment, setRecordPayment] = useState(true);
  const [paymentAmount, setPaymentAmount] = useState(0);
  const [modeOfPayment, setModeOfPayment] = useState('');
  const [settlementAccount, setSettlementAccount] = useState('');
  const [paymentModes, setPaymentModes] = useState<{ name: string; type?: string }[]>([]);
  const [settlementAccounts, setSettlementAccounts] = useState<{ name: string; account_name?: string; account_type?: string }[]>([]);
  const [modeAccounts, setModeAccounts] = useState<Record<string, string>>({});

  const loadSetup = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [setupRes, customersRes, taxRes, currencyRes, paymentRes] = await Promise.all([
        posApi.getSetup(),
        customersApi.getList({ page: 1, page_size: 100 }),
        gstApi.getTaxTemplates('Sales'),
        currencyApi.getOptions(),
        financeApi.getPaymentEntrySetup(),
      ]);
      const setup = setupRes.data.message || {};
      setWarehouse(setup.default_warehouse || '');
      setCustomer(setup.default_customer || '');
      setCurrency(setup.base_currency || baseCurrency);
      setCustomers(customersRes.data.message?.data || []);
      const templates = taxRes.data.message?.templates || taxRes.data.message || [];
      setTaxTemplates(templates);
      const defaultTpl = templates.find((t: any) => parseFloat(t.total_tax_rate || t.tax_rate || 0) > 0) || templates[0];
      if (defaultTpl) {
        setTaxTemplate(defaultTpl.name);
        setTaxRate(parseFloat(defaultTpl.total_tax_rate || defaultTpl.tax_rate || 0));
      }
      const curMsg = currencyRes.data.message || {};
      setMultiCurrencyOn(Boolean(curMsg.multi_currency_enabled));
      const curOpts = curMsg.currencies || [];
      setCurrencies(curOpts);

      const payMsg = paymentRes.data.message || {};
      const modes = payMsg.modes || [];
      const accounts = payMsg.settlement_accounts || [];
      setPaymentModes(modes);
      setSettlementAccounts(accounts);
      setModeAccounts(payMsg.mode_accounts || {});
      const defaultMode = modes.find((m: { name: string }) => m.name === 'Cash')?.name
        || modes.find((m: { name: string; type?: string }) => m.type === 'Cash')?.name
        || modes[0]?.name
        || '';
      setModeOfPayment((prev) => prev || defaultMode);
      const defaultAccount = payMsg.defaults?.receive_account
        || payMsg.defaults?.cash_account
        || accounts[0]?.name
        || '';
      setSettlementAccount((prev) => prev || defaultAccount);
    } catch (err) {
      console.error('POS setup failed:', err);
      setError('Could not load POS setup.');
    } finally {
      setLoading(false);
    }
  }, [baseCurrency]);

  useEffect(() => {
    void loadSetup();
  }, [loadSetup, companyRevision]);

  useEffect(() => {
    if (!multiCurrencyOn || !currency || currency === baseCurrency) {
      setExchangeRate(1);
      return;
    }
    const loadRate = async () => {
      try {
        const res = await currencyApi.getExchangeRate(currency, undefined, 'selling');
        setExchangeRate(Number(res.data.message?.exchange_rate) || 1);
      } catch {
        setExchangeRate(1);
      }
    };
    void loadRate();
  }, [currency, baseCurrency, multiCurrencyOn]);

  useEffect(() => {
    if (!modeOfPayment || settlementAccounts.length === 0) return;
    const mode = paymentModes.find((m) => m.name === modeOfPayment);
    const wantsBank = mode?.type === 'Bank' || modeOfPayment.toLowerCase().includes('bank');
    const filtered = settlementAccounts.filter((a) =>
      wantsBank ? a.account_type === 'Bank' : a.account_type === 'Cash',
    );
    const list = filtered.length > 0 ? filtered : settlementAccounts;
    const mapped = modeAccounts[modeOfPayment];
    if (mapped && list.some((a) => a.name === mapped)) {
      setSettlementAccount(mapped);
      return;
    }
    setSettlementAccount((prev) => {
      if (prev && list.some((a) => a.name === prev)) return prev;
      return list[0]?.name || prev;
    });
  }, [modeOfPayment, modeAccounts, paymentModes, settlementAccounts]);

  const addItemToCart = async (barcode: string) => {
    setError(null);
    try {
      const res = await inventoryApi.lookupByBarcode(barcode);
      const msg = res.data.message;
      if (!msg?.found || !msg.item) {
        setError(msg?.message || `No item for ${barcode}`);
        return;
      }
      const item = msg.item;
      const code = item.item_code;
      setCart((prev) => {
        const idx = prev.findIndex((l) => l.item_code === code && !l.has_serial_no);
        if (idx >= 0) {
          const next = [...prev];
          next[idx] = { ...next[idx], qty: next[idx].qty + 1 };
          return next;
        }
        return [
          ...prev,
          {
            item_code: code,
            item_name: item.item_name || code,
            qty: 1,
            rate: Number(item.selling_price) || 0,
            warehouse: item.default_warehouse || warehouse,
            serial_no: '',
            has_serial_no: Boolean(item.has_serial_no),
            serial_error: null,
            stock_qty: item.stock_qty ?? null,
          },
        ];
      });
    } catch (err: any) {
      setError(err?.response?.data?.exception || 'Barcode lookup failed.');
    }
  };

  const updateLine = (index: number, patch: Partial<CartLine>) => {
    setCart((prev) => prev.map((line, i) => (i === index ? { ...line, ...patch } : line)));
  };

  const validateSerial = async (index: number) => {
    const line = cart[index];
    if (!line?.item_code || !line.serial_no?.trim()) {
      updateLine(index, { serial_error: null });
      return true;
    }
    try {
      const res = await inventoryApi.validateSerialForItem({
        item_code: line.item_code,
        serial_no: line.serial_no.trim(),
        warehouse: line.warehouse || warehouse,
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

  const subtotal = useMemo(
    () => cart.reduce((sum, l) => sum + (Number(l.qty) || 0) * (Number(l.rate) || 0), 0),
    [cart],
  );
  const taxAmount = subtotal * (taxRate / 100);
  const grandTotal = subtotal + taxAmount;

  useEffect(() => {
    if (!recordPayment) return;
    setPaymentAmount((prev) => {
      if (prev <= 0) return grandTotal;
      if (prev > grandTotal) return grandTotal;
      return prev;
    });
  }, [grandTotal, recordPayment]);

  const handleCheckout = async () => {
    if (!customer) {
      setError('Select a customer.');
      return;
    }
    if (cart.length === 0) {
      setError('Scan at least one item.');
      return;
    }
    for (let i = 0; i < cart.length; i++) {
      const line = cart[i];
      if (line.has_serial_no && !line.serial_no?.trim()) {
        setError(`Serial required for ${line.item_code} on line ${i + 1}.`);
        return;
      }
      if (line.serial_no?.trim()) {
        const ok = await validateSerial(i);
        if (!ok) {
          setError(line.serial_error || `Invalid serial on line ${i + 1}.`);
          return;
        }
      }
    }

    if (recordPayment && !settlementAccount) {
      setError('Select a cash or bank account for payment.');
      return;
    }
    if (recordPayment) {
      const pay = Number(paymentAmount) || 0;
      if (pay <= 0) {
        setError('Enter a payment amount greater than zero.');
        return;
      }
      if (pay > grandTotal + 0.01) {
        setError('Payment amount cannot exceed the invoice total.');
        return;
      }
    }

    setSaving(true);
    setError(null);
    try {
      const response = await posApi.createSale({
        customer,
        warehouse,
        currency: currency !== baseCurrency ? currency : undefined,
        exchange_rate: currency !== baseCurrency ? exchangeRate : undefined,
        taxes_and_charges: taxTemplate || undefined,
        submit: 1,
        record_payment: recordPayment ? 1 : 0,
        payment_amount: recordPayment ? Math.min(Number(paymentAmount) || 0, grandTotal) : undefined,
        mode_of_payment: recordPayment ? modeOfPayment || undefined : undefined,
        settlement_account: recordPayment ? settlementAccount || undefined : undefined,
        items: cart.map((l) => ({
          item_code: l.item_code,
          qty: l.qty,
          rate: l.rate,
          warehouse: l.warehouse || warehouse,
          serial_no: l.serial_no?.trim() || undefined,
        })),
      });
      const created = response.data.message;
      const printUrl = `/print?doctype=${encodeURIComponent('Sales Invoice')}&name=${encodeURIComponent(created.name)}&autoprint=1&return=${encodeURIComponent('/sales/pos')}`;
      navigate(printUrl);
    } catch (err: any) {
      setError(err?.response?.data?.exception || 'Checkout failed.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <button
            type="button"
            onClick={() => navigate('/sales')}
            className="mb-2 inline-flex items-center gap-2 text-sm text-brand-700 hover:text-brand-800"
          >
            <ArrowLeft size={16} /> Back to Sales
          </button>
          <h1 className="page-title">POS Checkout</h1>
          <p className="mt-1 text-sm text-gray-500">Scan barcodes, submit the invoice, and optionally record payment in one step.</p>
        </div>
        <button
          type="button"
          onClick={handleCheckout}
          disabled={saving || loading || cart.length === 0}
          className="btn-primary flex items-center gap-2 disabled:opacity-60"
        >
          <Save size={14} /> {saving ? 'Processing…' : recordPayment ? 'Complete & get paid' : 'Complete sale'}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="card space-y-4 p-4 lg:col-span-2">
          <BarcodeScanInput
            value={scanValue}
            onChange={setScanValue}
            onScan={addItemToCart}
            autoFocus
            disabled={loading || saving}
          />

          {cart.length === 0 ? (
            <p className="py-8 text-center text-sm text-gray-500">Scan a barcode to add items to the cart.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="py-2 pr-2">Item</th>
                    <th className="py-2 pr-2 text-right">Qty</th>
                    <th className="py-2 pr-2 text-right">Rate</th>
                    <th className="py-2 pr-2">Serial</th>
                    <th className="py-2" />
                  </tr>
                </thead>
                <tbody>
                  {cart.map((line, index) => (
                    <tr key={`${line.item_code}-${index}`} className="border-b border-gray-100">
                      <td className="py-2 pr-2">
                        <div className="font-medium text-gray-900">{line.item_name}</div>
                        <div className="text-xs text-gray-500">{line.item_code}</div>
                        {line.stock_qty != null && (
                          <div className="text-xs text-gray-400">Stock: {line.stock_qty}</div>
                        )}
                      </td>
                      <td className="py-2 pr-2">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            type="button"
                            className="rounded border p-1"
                            onClick={() => updateLine(index, { qty: Math.max(1, line.qty - 1) })}
                          >
                            <Minus size={12} />
                          </button>
                          <input
                            type="number"
                            min={1}
                            value={line.qty}
                            onChange={(e) => updateLine(index, { qty: Number(e.target.value) || 1 })}
                            className="input-field w-14 text-center text-sm"
                          />
                          <button
                            type="button"
                            className="rounded border p-1"
                            onClick={() => updateLine(index, { qty: line.qty + 1 })}
                          >
                            <Plus size={12} />
                          </button>
                        </div>
                      </td>
                      <td className="py-2 pr-2 text-right">
                        <input
                          type="number"
                          min={0}
                          step="0.01"
                          value={line.rate}
                          onChange={(e) => updateLine(index, { rate: Number(e.target.value) || 0 })}
                          className="input-field w-24 text-right text-sm"
                        />
                      </td>
                      <td className="py-2 pr-2">
                        {line.has_serial_no ? (
                          <>
                            <input
                              value={line.serial_no}
                              onChange={(e) => updateLine(index, { serial_no: e.target.value, serial_error: null })}
                              onBlur={() => void validateSerial(index)}
                              placeholder="Scan serial"
                              className={`input-field w-full font-mono text-xs ${line.serial_error ? 'border-red-300' : ''}`}
                            />
                            {line.serial_error && (
                              <p className="mt-0.5 text-xs text-red-600">{line.serial_error}</p>
                            )}
                          </>
                        ) : (
                          <span className="text-xs text-gray-400">—</span>
                        )}
                      </td>
                      <td className="py-2 text-right">
                        <button
                          type="button"
                          onClick={() => setCart((prev) => prev.filter((_, i) => i !== index))}
                          className="text-red-600 hover:text-red-800"
                          aria-label="Remove line"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card space-y-4 p-4">
          <Field label="Customer">
            <SearchableSelect
              value={customer}
              onChange={setCustomer}
              options={customers.map((c) => ({ value: c.name, label: c.customer_name || c.name }))}
              placeholder="Select customer"
            />
          </Field>
          <Field label="Warehouse">
            <input value={warehouse} readOnly className="input-field bg-gray-50 text-sm" />
          </Field>
          {multiCurrencyOn && (
            <>
              <Field label="Currency">
                <select
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  className="input-field text-sm"
                >
                  {currencies.map((c) => (
                    <option key={c.name} value={c.name}>{c.name}</option>
                  ))}
                </select>
              </Field>
              {currency !== baseCurrency && (
                <Field label={`Rate (1 ${currency} → ${baseCurrency})`}>
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
          <Field label="Tax template">
            <select
              value={taxTemplate}
              onChange={(e) => {
                const name = e.target.value;
                setTaxTemplate(name);
                const tpl = taxTemplates.find((t) => t.name === name);
                setTaxRate(tpl ? parseFloat(tpl.total_tax_rate || tpl.tax_rate || 0) : 0);
              }}
              className="input-field text-sm"
            >
              <option value="">No tax</option>
              {taxTemplates.map((t) => (
                <option key={t.name} value={t.name}>{t.title || t.name}</option>
              ))}
            </select>
          </Field>

          <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-gray-200 bg-gray-50/80 px-3 py-2">
            <input
              type="checkbox"
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-brand-600"
              checked={recordPayment}
              onChange={(e) => {
                const on = e.target.checked;
                setRecordPayment(on);
                if (on) setPaymentAmount(grandTotal);
              }}
            />
            <span className="text-sm text-gray-700">Record payment now</span>
          </label>

          {recordPayment && (
            <>
              <Field label={`Amount received (total ${formatCurrency(grandTotal, currency)})`}>
                <input
                  type="number"
                  min={0}
                  max={grandTotal}
                  step="0.01"
                  value={paymentAmount || ''}
                  onChange={(e) => setPaymentAmount(Number(e.target.value) || 0)}
                  className="input-field text-sm"
                />
                {paymentAmount > 0 && paymentAmount < grandTotal - 0.01 && (
                  <p className="mt-1 text-xs text-amber-700">
                    Balance due: {formatCurrency(grandTotal - paymentAmount, currency)}
                  </p>
                )}
              </Field>
              <Field label="Payment mode">
                <select
                  value={modeOfPayment}
                  onChange={(e) => setModeOfPayment(e.target.value)}
                  className="input-field text-sm"
                >
                  {paymentModes.map((m) => (
                    <option key={m.name} value={m.name}>{m.name}</option>
                  ))}
                </select>
              </Field>
              <Field label="Deposit to">
                <select
                  value={settlementAccount}
                  onChange={(e) => setSettlementAccount(e.target.value)}
                  className="input-field text-sm"
                >
                  {settlementAccounts.map((a) => (
                    <option key={a.name} value={a.name}>
                      {a.account_type === 'Bank' ? 'Bank' : 'Cash'}: {a.account_name || a.name}
                    </option>
                  ))}
                </select>
              </Field>
            </>
          )}

          <div className="border-t pt-3 space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Subtotal</span>
              <span>{formatCurrency(subtotal, currency)}</span>
            </div>
            {taxRate > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-600">Tax ({taxRate}%)</span>
                <span>{formatCurrency(taxAmount, currency)}</span>
              </div>
            )}
            <div className="flex justify-between text-base font-semibold">
              <span>Total</span>
              <span>{formatCurrency(grandTotal, currency)}</span>
            </div>
            {multiCurrencyOn && currency !== baseCurrency && (
              <p className="text-xs text-gray-500">
                ≈ {formatCurrency(grandTotal * exchangeRate, baseCurrency)} in company currency
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-gray-600">{label}</label>
      {children}
    </div>
  );
}

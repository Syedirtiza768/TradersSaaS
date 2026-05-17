import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Plus, Save, Trash2, Truck } from 'lucide-react';
import { customersApi, inventoryApi, salesApi } from '../lib/api';
import { appendPreservedListQuery } from '../lib/utils';
import SearchableSelect from '../components/SearchableSelect';
import useQuickAdd from '../components/useQuickAdd';
import QuickAddProvider from '../components/QuickAddProvider';

type ChallanLine = {
  item_code: string;
  description: string;
  qty: number;
  warehouse: string;
};

const EMPTY_LINE: ChallanLine = { item_code: '', description: '', qty: 1, warehouse: '' };

export default function CreateDeliveryChallanPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [customers, setCustomers] = useState<any[]>([]);
  const [items, setItems] = useState<any[]>([]);
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [customer, setCustomer] = useState(searchParams.get('customer') || '');
  const [postingDate, setPostingDate] = useState(today());
  const [lines, setLines] = useState<ChallanLine[]>([{ ...EMPTY_LINE }]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listSearch = searchParams.get('list');
  const quickAdd = useQuickAdd();
  const quickAddItemLine = useRef(-1);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [customersRes, itemsRes, warehousesRes] = await Promise.all([
          customersApi.getList({ page: 1, page_size: 100 }),
          inventoryApi.getItems({ page: 1, page_size: 200 }),
          inventoryApi.getWarehouses(),
        ]);
        setCustomers(customersRes.data.message?.data || []);
        setItems(itemsRes.data.message?.data || []);
        setWarehouses(warehousesRes.data.message?.data || warehousesRes.data.message || []);
      } catch {
        setError('Could not load form data.');
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  const updateLine = (index: number, patch: Partial<ChallanLine>) => {
    setLines((current) => current.map((line, i) => (i === index ? { ...line, ...patch } : line)));
  };

  const addLine = () => setLines((current) => [...current, { ...EMPTY_LINE }]);
  const removeLine = (index: number) => {
    setLines((current) => (current.length > 1 ? current.filter((_, i) => i !== index) : current));
  };

  const totalQty = useMemo(
    () => lines.reduce((sum, line) => sum + (Number(line.qty) || 0), 0),
    [lines],
  );

  const handleSubmit = async () => {
    if (!customer) {
      setError('Select a customer.');
      return;
    }
    const validLines = lines.filter((line) => line.item_code && Number(line.qty) > 0);
    if (validLines.length === 0) {
      setError('Add at least one item line.');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const response = await salesApi.createDeliveryNote({
        customer,
        posting_date: postingDate,
        items: validLines.map((line) => ({
          item_code: line.item_code,
          description: line.description || undefined,
          qty: line.qty,
          warehouse: line.warehouse || undefined,
        })),
      });
      const created = response.data.message;
      navigate(appendPreservedListQuery(`/sales/challans/${encodeURIComponent(created.name)}`, listSearch));
    } catch (err: any) {
      setError(err?.response?.data?.exception || 'Could not create delivery challan.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4 sm:space-y-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <button type="button" onClick={() => navigate('/sales/documents/new')} className="mb-3 inline-flex items-center gap-2 text-sm text-brand-700 hover:text-brand-800">
              <ArrowLeft size={16} /> Back to document types
            </button>
            <h1 className="page-title">New Delivery Challan</h1>
            <p className="mt-1 text-gray-500">Record goods dispatched to a customer without billing.</p>
          </div>
          <button type="button" onClick={handleSubmit} disabled={saving || loading} className="btn-primary flex items-center gap-2 disabled:opacity-60">
            <Save size={14} /> {saving ? 'Creating…' : 'Create Draft'}
          </button>
        </div>

        {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="card p-6 lg:col-span-2 space-y-6">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Field label="Customer">
                <SearchableSelect
                  value={customer}
                  onChange={setCustomer}
                  options={customers.map((c) => ({ label: c.customer_name || c.name, value: c.name }))}
                  placeholder="Select customer"
                  disabled={loading}
                  creatable
                  onCreateNew={(query) => quickAdd.open('customer', query)}
                />
              </Field>
              <Field label="Posting Date">
                <input type="date" value={postingDate} onChange={(e) => setPostingDate(e.target.value)} className="input-field" />
              </Field>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">Items</h2>
                <button type="button" onClick={addLine} className="btn-secondary flex items-center gap-2">
                  <Plus size={14} /> Add Line
                </button>
              </div>
              {lines.map((line, index) => (
                <div key={index} className="rounded-lg border border-gray-200 p-4 space-y-3">
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-[2fr_1fr_1fr_auto]">
                    <Field label="Item">
                      <SearchableSelect
                        value={line.item_code}
                        onChange={(code) => {
                          const selected = items.find((item) => (item.item_code || item.name) === code);
                          updateLine(index, {
                            item_code: code,
                            description: selected?.item_name || selected?.description || '',
                          });
                        }}
                        options={items.map((item) => ({ label: item.item_name || item.item_code || item.name, value: item.item_code || item.name }))}
                        placeholder="Select item"
                        creatable
                        onCreateNew={(query) => { quickAddItemLine.current = index; quickAdd.open('item', query); }}
                      />
                    </Field>
                    <Field label="Qty">
                      <input type="number" min={0.01} step="0.01" value={line.qty} onChange={(e) => updateLine(index, { qty: Number(e.target.value) })} className="input-field text-right text-sm" />
                    </Field>
                    <Field label="Warehouse">
                      <SearchableSelect
                        value={line.warehouse}
                        onChange={(warehouse) => updateLine(index, { warehouse })}
                        options={warehouses.map((w) => ({ label: w.warehouse_name || w.name, value: w.name }))}
                        placeholder="Warehouse"
                      />
                    </Field>
                    <div className="flex items-end">
                      <button type="button" onClick={() => removeLine(index)} disabled={lines.length === 1} className="rounded-lg border border-gray-200 p-2.5 text-gray-400 hover:text-red-600 disabled:opacity-30">
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card p-6 space-y-4 h-fit">
            <div className="flex items-center gap-2 text-brand-700">
              <Truck className="h-5 w-5" />
              <h2 className="font-semibold text-gray-900">Summary</h2>
            </div>
            <p className="text-sm text-gray-500">Total quantity: <span className="font-medium text-gray-900">{totalQty}</span></p>
            <p className="text-xs text-gray-400">Submit the challan after creation to update stock.</p>
          </div>
        </div>

      <QuickAddProvider
        quickAdd={quickAdd}
        customersSetter={setCustomers}
        customerValueSetter={setCustomer}
        itemsSetter={setItems}
        itemValueSetter={(v) => {
          const idx = quickAddItemLine.current;
          if (idx >= 0) updateLine(idx, { item_code: v });
          quickAddItemLine.current = -1;
        }}
      />
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1">
      <span className="text-sm font-medium text-gray-700">{label}</span>
      {children}
    </label>
  );
}

function today() {
  return new Date().toISOString().slice(0, 10);
}


import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';
import { inventoryApi } from '../lib/api';
import SearchableSelect from '../components/SearchableSelect';

export default function CreateItemPage() {
  const navigate = useNavigate();
  const [groups, setGroups] = useState<string[]>([]);
  const [form, setForm] = useState({
    item_code: '',
    item_name: '',
    item_group: '',
    stock_uom: 'Nos',
    is_stock_item: 1,
    has_serial_no: 0,
    barcode: '',
    opening_stock: 0,
    standard_rate: 0,
    description: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const groupsRes = await inventoryApi.getItemGroups();
        setGroups(groupsRes.data.message || []);
      } catch (err) {
        console.error('Failed to load item groups:', err);
        setError('Could not load item groups.');
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  const handleSave = async () => {
    if (!form.item_code.trim()) {
      setError('Item code is required.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const response = await inventoryApi.createItem(form);
      const created = response.data.message;
      navigate(`/inventory/items/${encodeURIComponent(created.item_code || created.name)}`);
    } catch (err: any) {
      console.error('Failed to create item:', err);
      setError(err?.response?.data?.exception || 'Could not create item.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <button onClick={() => navigate('/inventory')} className="mb-3 inline-flex items-center gap-2 text-sm text-brand-700 hover:text-brand-800">
            <ArrowLeft size={16} /> Back to Inventory
          </button>
          <h1 className="page-title">Add Item</h1>
          <p className="mt-1 text-gray-500">Create a new inventory item with the minimum required fields.</p>
        </div>
        <button onClick={handleSave} disabled={saving || loading} className="btn-primary flex items-center gap-2 disabled:opacity-60">
          <Save size={14} /> {saving ? 'Creating…' : 'Create Item'}
        </button>
      </div>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <div className="card p-6 grid grid-cols-1 gap-4 md:grid-cols-2">
        <Field label="Item Code">
          <input value={form.item_code} onChange={(e) => setForm((c) => ({ ...c, item_code: e.target.value }))} className="input-field" placeholder="e.g. ITEM-001" />
        </Field>
        <Field label="Item Name">
          <input value={form.item_name} onChange={(e) => setForm((c) => ({ ...c, item_name: e.target.value }))} className="input-field" placeholder="e.g. Steel Pipe 2 inch" />
        </Field>
        <Field label="Item Group">
          <SearchableSelect
            value={form.item_group}
            onChange={(v) => setForm((c) => ({ ...c, item_group: v }))}
            options={groups.map((g) => ({ label: g, value: g }))}
            placeholder="Select group"
            disabled={loading}
          />
        </Field>
        <Field label="Stock UOM">
          <SearchableSelect
            value={form.stock_uom}
            onChange={(v) => setForm((c) => ({ ...c, stock_uom: v }))}
            options={['Nos', 'Kg', 'Ltr', 'Mtr', 'Box', 'Pair', 'Set'].map((u) => ({ label: u, value: u }))}
            placeholder="Select UOM"
          />
        </Field>
        <Field label="Standard Rate">
          <input type="number" min="0" step="0.01" value={form.standard_rate} onChange={(e) => setForm((c) => ({ ...c, standard_rate: Number(e.target.value) || 0 }))} className="input-field" />
        </Field>
        <Field label="Opening Stock">
          <input type="number" min="0" value={form.opening_stock} onChange={(e) => setForm((c) => ({ ...c, opening_stock: Number(e.target.value) || 0 }))} className="input-field" />
        </Field>
        <Field label="Description">
          <textarea value={form.description} onChange={(e) => setForm((c) => ({ ...c, description: e.target.value }))} className="input-field" rows={2} placeholder="Optional item description" />
        </Field>
        <Field label="Is Stock Item">
          <SearchableSelect
            value={String(form.is_stock_item)}
            onChange={(v) => setForm((c) => ({ ...c, is_stock_item: Number(v) }))}
            options={[{ label: 'Yes', value: '1' }, { label: 'No', value: '0' }]}
            placeholder="Select"
          />
        </Field>
        <Field label="Track serial numbers">
          <SearchableSelect
            value={String(form.has_serial_no)}
            onChange={(v) => setForm((c) => ({ ...c, has_serial_no: Number(v) }))}
            options={[{ label: 'Yes', value: '1' }, { label: 'No', value: '0' }]}
            placeholder="Select"
          />
        </Field>
        <Field label="Barcode (EAN)">
          <input
            value={form.barcode}
            onChange={(e) => setForm((c) => ({ ...c, barcode: e.target.value }))}
            className="input-field font-mono"
            placeholder="Scan or enter barcode"
          />
        </Field>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="block">
      <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-500">{label}</span>
      {children}
    </div>
  );
}

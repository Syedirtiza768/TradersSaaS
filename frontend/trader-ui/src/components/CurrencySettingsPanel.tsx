import { useCallback, useEffect, useState } from 'react';
import { Coins, Plus, Save, Trash2 } from 'lucide-react';
import { currencyApi } from '../lib/api';
import { useCompanyStore } from '../stores/companyStore';

type CurrencyRow = { name: string; currency_name?: string; symbol?: string };

type ExchangeRateRow = {
  name: string;
  date: string;
  from_currency: string;
  to_currency: string;
  exchange_rate: number;
  for_selling?: number;
  for_buying?: number;
};

type CurrencySettings = {
  company: string;
  base_currency: string;
  multi_currency_enabled: boolean;
  enabled_currencies: string[];
  available_currencies: CurrencyRow[];
  exchange_rates: ExchangeRateRow[];
};

const emptyRateForm = () => ({
  from_currency: '',
  exchange_rate: '',
  date: new Date().toISOString().slice(0, 10),
  for_selling: true,
  for_buying: false,
});

export default function CurrencySettingsPanel() {
  const companyRevision = useCompanyStore((s) => s.revision);
  const reloadCompany = useCompanyStore((s) => s.load);

  const [settings, setSettings] = useState<CurrencySettings | null>(null);
  const [baseCurrency, setBaseCurrency] = useState('');
  const [multiEnabled, setMultiEnabled] = useState(false);
  const [enabled, setEnabled] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [rateSaving, setRateSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [rateForm, setRateForm] = useState(emptyRateForm);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await currencyApi.getSettings();
      const msg = res.data.message as CurrencySettings;
      setSettings(msg);
      setBaseCurrency(msg.base_currency || 'PKR');
      setMultiEnabled(Boolean(msg.multi_currency_enabled));
      setEnabled(msg.enabled_currencies || []);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { message?: string } } };
      setError(ax.response?.data?.message || 'Could not load currency settings.');
      setSettings(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load, companyRevision]);

  const toggleCurrency = (code: string) => {
    setEnabled((current) => {
      if (current.includes(code)) {
        if (code === baseCurrency) return current;
        return current.filter((c) => c !== code);
      }
      return [...current, code];
    });
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    setFeedback(null);
    setError(null);
    try {
      const res = await currencyApi.saveSettings({
        base_currency: baseCurrency,
        multi_currency_enabled: multiEnabled ? 1 : 0,
        enabled_currencies: multiEnabled ? enabled : [baseCurrency],
      });
      const msg = res.data.message as { message?: string; settings?: CurrencySettings };
      if (msg.settings) {
        setSettings(msg.settings);
        setBaseCurrency(msg.settings.base_currency);
        setMultiEnabled(Boolean(msg.settings.multi_currency_enabled));
        setEnabled(msg.settings.enabled_currencies || []);
      }
      await reloadCompany();
      window.dispatchEvent(new CustomEvent('trader-currency-settings-changed'));
      setFeedback(msg.message || 'Currency settings saved.');
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { message?: string; exc?: string } } };
      setError(ax.response?.data?.message || ax.response?.data?.exc || 'Could not save currency settings.');
    } finally {
      setSaving(false);
    }
  };

  const handleAddRate = async () => {
    if (!rateForm.from_currency || !rateForm.exchange_rate) {
      setError('Select a currency and enter an exchange rate.');
      return;
    }
    setRateSaving(true);
    setError(null);
    try {
      await currencyApi.saveExchangeRate({
        from_currency: rateForm.from_currency,
        exchange_rate: Number(rateForm.exchange_rate),
        date: rateForm.date,
        for_selling: rateForm.for_selling ? 1 : 0,
        for_buying: rateForm.for_buying ? 1 : 0,
      });
      setRateForm(emptyRateForm());
      await load();
      setFeedback('Exchange rate saved.');
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { message?: string; exc?: string } } };
      setError(ax.response?.data?.message || ax.response?.data?.exc || 'Could not save exchange rate.');
    } finally {
      setRateSaving(false);
    }
  };

  const handleDeleteRate = async (name: string) => {
    if (!window.confirm('Delete this exchange rate?')) return;
    setError(null);
    try {
      await currencyApi.deleteExchangeRate(name);
      await load();
      setFeedback('Exchange rate deleted.');
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { message?: string } } };
      setError(ax.response?.data?.message || 'Could not delete exchange rate.');
    }
  };

  if (loading) {
    return (
      <div className="card p-6 flex justify-center">
        <div className="spinner" />
      </div>
    );
  }

  const available = settings?.available_currencies || [];

  return (
    <div className="card p-6 space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center">
            <Coins size={20} className="text-amber-700 dark:text-amber-300" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Currency &amp; exchange rates</h2>
            <p className="text-sm text-gray-500 dark:text-slate-400">
              Base currency, multi-currency mode, and manual FX rates for the active company
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => void handleSaveSettings()}
          disabled={saving}
          className="btn-primary flex items-center justify-center gap-2 self-start"
        >
          <Save size={14} /> {saving ? 'Saving…' : 'Save currency settings'}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-100">
          {error}
        </div>
      )}
      {feedback && !error && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-100">
          {feedback}
        </div>
      )}

      <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-gray-200 dark:border-slate-600 bg-gray-50/80 dark:bg-slate-800/50 px-4 py-3 max-w-xl">
        <input
          type="checkbox"
          className="mt-1 h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
          checked={multiEnabled}
          onChange={(e) => setMultiEnabled(e.target.checked)}
        />
        <span>
          <span className="block text-sm font-medium text-gray-900 dark:text-gray-100">Multi-currency mode</span>
          <span className="block text-xs text-gray-500 dark:text-slate-400 mt-0.5">
            When off, all documents use the base currency only. When on, you can pick from enabled currencies on sales,
            purchases, and POS.
          </span>
        </span>
      </label>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <label className="block">
          <span className="text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wide">Base currency</span>
          <select
            className="input-field mt-1"
            value={baseCurrency}
            onChange={(e) => {
              const next = e.target.value;
              setBaseCurrency(next);
              setEnabled((cur) => (cur.includes(next) ? cur : [next, ...cur]));
            }}
          >
            {available.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name} {c.currency_name && c.currency_name !== c.name ? `— ${c.currency_name}` : ''}
              </option>
            ))}
          </select>
          <span className="text-xs text-gray-400 dark:text-slate-500 mt-1 block">
            Updates the company default in ERPNext. Requires admin or accounts permission.
          </span>
        </label>
      </div>

      {multiEnabled && (
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">Currencies available in Trader</h3>
          <p className="text-xs text-gray-500 dark:text-slate-400 mb-3">
            Select which foreign currencies appear on invoices and POS. Base currency is always included.
          </p>
          <div className="flex flex-wrap gap-2">
            {available.map((c) => {
              const checked = enabled.includes(c.name);
              const isBase = c.name === baseCurrency;
              return (
                <label
                  key={c.name}
                  className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm cursor-pointer ${
                    checked
                      ? 'border-brand-300 bg-brand-50 text-brand-900 dark:border-brand-700 dark:bg-brand-950/40 dark:text-brand-100'
                      : 'border-gray-200 bg-white text-gray-700 dark:border-slate-600 dark:bg-slate-900/30 dark:text-gray-200'
                  } ${isBase ? 'opacity-90' : ''}`}
                >
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-gray-300 text-brand-600"
                    checked={checked}
                    disabled={isBase}
                    onChange={() => toggleCurrency(c.name)}
                  />
                  {c.name}
                  {isBase ? <span className="text-xs text-gray-500">(base)</span> : null}
                </label>
              );
            })}
          </div>
        </div>
      )}

      <div>
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">Manual exchange rates</h3>
        <p className="text-xs text-gray-500 dark:text-slate-400 mb-4">
          Rates are stored in ERPNext Currency Exchange ({`foreign → ${baseCurrency}`}). Selling and buying can use
          different rates on the same date.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3 mb-4 p-4 rounded-lg border border-gray-200 dark:border-slate-600 bg-gray-50/50 dark:bg-slate-800/30">
          <label className="block">
            <span className="text-xs text-gray-500">From currency</span>
            <select
              className="input-field mt-1"
              value={rateForm.from_currency}
              onChange={(e) => setRateForm((f) => ({ ...f, from_currency: e.target.value }))}
            >
              <option value="">Select…</option>
              {available
                .filter((c) => c.name !== baseCurrency)
                .map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name}
                  </option>
                ))}
            </select>
          </label>
          <label className="block">
            <span className="text-xs text-gray-500">Rate → {baseCurrency}</span>
            <input
              type="number"
              min="0"
              step="any"
              className="input-field mt-1"
              value={rateForm.exchange_rate}
              onChange={(e) => setRateForm((f) => ({ ...f, exchange_rate: e.target.value }))}
              placeholder="e.g. 278.5"
            />
          </label>
          <label className="block">
            <span className="text-xs text-gray-500">Date</span>
            <input
              type="date"
              className="input-field mt-1"
              value={rateForm.date}
              onChange={(e) => setRateForm((f) => ({ ...f, date: e.target.value }))}
            />
          </label>
          <label className="flex items-end gap-4 pb-1">
            <span className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={rateForm.for_selling}
                onChange={(e) => setRateForm((f) => ({ ...f, for_selling: e.target.checked }))}
              />
              Selling
            </span>
            <span className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={rateForm.for_buying}
                onChange={(e) => setRateForm((f) => ({ ...f, for_buying: e.target.checked }))}
              />
              Buying
            </span>
          </label>
          <div className="flex items-end">
            <button
              type="button"
              onClick={() => void handleAddRate()}
              disabled={rateSaving}
              className="btn-secondary w-full flex items-center justify-center gap-2"
            >
              <Plus size={14} /> {rateSaving ? 'Saving…' : 'Add rate'}
            </button>
          </div>
        </div>

        {(settings?.exchange_rates?.length ?? 0) > 0 ? (
          <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-slate-600">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 dark:bg-slate-800/80 text-left text-xs uppercase text-gray-500 dark:text-slate-400">
                <tr>
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2">From</th>
                  <th className="px-3 py-2">To</th>
                  <th className="px-3 py-2 text-right">Rate</th>
                  <th className="px-3 py-2">Purpose</th>
                  <th className="px-3 py-2 w-10" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-slate-700">
                {settings?.exchange_rates.map((row) => (
                  <tr key={row.name}>
                    <td className="px-3 py-2 whitespace-nowrap">{row.date}</td>
                    <td className="px-3 py-2">{row.from_currency}</td>
                    <td className="px-3 py-2">{row.to_currency}</td>
                    <td className="px-3 py-2 text-right font-mono">{Number(row.exchange_rate).toLocaleString()}</td>
                    <td className="px-3 py-2 text-xs text-gray-600 dark:text-slate-300">
                      {row.for_selling ? 'Selling' : ''}
                      {row.for_selling && row.for_buying ? ' · ' : ''}
                      {row.for_buying ? 'Buying' : ''}
                      {!row.for_selling && !row.for_buying ? '—' : ''}
                    </td>
                    <td className="px-3 py-2">
                      <button
                        type="button"
                        className="text-red-600 hover:text-red-800 dark:text-red-400"
                        onClick={() => void handleDeleteRate(row.name)}
                        aria-label="Delete rate"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-500 dark:text-slate-400">No manual rates yet for this base currency.</p>
        )}
      </div>
    </div>
  );
}

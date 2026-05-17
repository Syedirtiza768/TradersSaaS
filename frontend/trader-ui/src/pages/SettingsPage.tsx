import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Building2, Users, Shield, Globe, RefreshCw, SlidersHorizontal, Save, ScrollText } from 'lucide-react';
import CurrencySettingsPanel from '../components/CurrencySettingsPanel';
import { settingsApi } from '../lib/api';
import { applyTraderUiTheme, normaliseUiPrefs, type TraderUiPrefs } from '../lib/traderUiTheme';

const TIME_ZONES = [
  'Asia/Karachi',
  'Asia/Dubai',
  'Asia/Riyadh',
  'Asia/Doha',
  'Asia/Singapore',
  'Asia/Tokyo',
  'Europe/London',
  'America/New_York',
  'UTC',
] as const;

const DATE_FORMATS = ['dd-mm-yyyy', 'mm-dd-yyyy', 'yyyy-mm-dd', 'dd/mm/yyyy', 'mm/dd/yyyy'] as const;
const NUMBER_FORMATS = ['#,###.##', '#,##,###.##', '#.###,##', '#,###'] as const;

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'ur', label: 'Urdu' },
] as const;

const SESSION_EXPIRY_MINUTES = [60, 120, 240, 480, 720, 1440] as const;

type SaveResponse = {
  ok?: boolean;
  message?: string;
  settings?: { ui?: Record<string, unknown> };
};

export default function SettingsPage() {
  const [companyInfo, setCompanyInfo] = useState<Record<string, unknown> | null>(null);
  const [roles, setRoles] = useState<{ name: string; disabled?: number }[]>([]);
  const [uiPrefs, setUiPrefs] = useState<TraderUiPrefs | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const loadSettings = async () => {
    setLoading(true);
    setLoadError(null);
    setFeedback(null);
    try {
      const [settingsRes, rolesRes] = await Promise.all([
        settingsApi.get(),
        settingsApi.getTraderRoles(),
      ]);
      const settings = settingsRes.data.message as { company?: typeof companyInfo; ui?: Record<string, unknown> };
      setCompanyInfo(settings?.company || null);
      setRoles(rolesRes.data.message || []);
      const ui = normaliseUiPrefs(settings?.ui);
      setUiPrefs(ui);
      applyTraderUiTheme(ui);
    } catch {
      setLoadError('Could not load settings. Check your connection and try Refresh.');
      setCompanyInfo(null);
      setRoles([]);
      setUiPrefs(null);
    }
    setLoading(false);
  };

  useEffect(() => {
    void loadSettings();
  }, []);

  const handleSave = async () => {
    if (!uiPrefs) return;
    setSaving(true);
    setFeedback(null);
    try {
      const res = await settingsApi.save({
        ui: {
          language: uiPrefs.language,
          time_zone: uiPrefs.time_zone,
          date_format: uiPrefs.date_format,
          number_format: uiPrefs.number_format,
          float_precision: uiPrefs.float_precision,
          session_expiry: uiPrefs.session_expiry,
          enable_two_factor: uiPrefs.enable_two_factor,
          dark_mode: uiPrefs.dark_mode,
          compact_tables: uiPrefs.compact_tables,
          email_notifications: uiPrefs.email_notifications,
        },
      });
      const raw = res.data.message as string | SaveResponse;
      const payload = typeof raw === 'object' && raw && raw !== null ? raw : null;
      const nextUi = payload?.settings?.ui;
      if (nextUi) {
        const n = normaliseUiPrefs(nextUi);
        setUiPrefs(n);
        applyTraderUiTheme(n);
      } else {
        applyTraderUiTheme(uiPrefs);
      }
      const userMsg =
        typeof raw === 'object' && raw && 'message' in raw && typeof raw.message === 'string'
          ? raw.message
          : 'Settings saved.';
      setFeedback({ type: 'success', message: userMsg });
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { message?: string; exc?: string } } };
      const msg =
        ax.response?.data?.message ||
        ax.response?.data?.exc ||
        'Could not save settings. You may need to refresh and sign in again.';
      setFeedback({ type: 'error', message: String(msg) });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 sm:space-y-6">
        <div>
          <h1 className="page-title">Settings</h1>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="spinner" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="text-gray-500 dark:text-slate-400 mt-1">System configuration and your preferences</p>
        </div>
        <button type="button" onClick={() => void loadSettings()} className="btn-secondary flex items-center justify-center gap-2 self-start">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {loadError && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-100" role="alert">
          {loadError}
        </div>
      )}

      {feedback && (
        <div
          className={`rounded-lg border px-4 py-3 text-sm ${
            feedback.type === 'success'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-100'
              : 'border-red-200 bg-red-50 text-red-900 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-100'
          }`}
          role="status"
        >
          {feedback.message}
        </div>
      )}

      {/* Company Info */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-brand-100 dark:bg-brand-900/40 flex items-center justify-center">
            <Building2 size={20} className="text-brand-700 dark:text-brand-300" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Company Information</h2>
            <p className="text-sm text-gray-500 dark:text-slate-400">Primary company details from ERPNext</p>
          </div>
        </div>
        {companyInfo ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
            <InfoRow label="Company Name" value={String(companyInfo.name ?? '')} />
            <p className="text-xs text-gray-500 dark:text-slate-400 px-1">
              Switch the active company from the header menu when you operate multiple legal entities.
            </p>
            <InfoRow label="Abbreviation" value={String(companyInfo.abbr ?? '')} />
            <InfoRow label="Country" value={String(companyInfo.country ?? '')} />
            <InfoRow label="Currency" value={String(companyInfo.default_currency ?? '')} />
            <InfoRow label="Domain" value={String(companyInfo.domain ?? '')} />
            <InfoRow label="Chart of Accounts" value={String(companyInfo.chart_of_accounts ?? '')} />
          </div>
        ) : (
          <p className="text-gray-500 dark:text-slate-400 text-sm">No company configured. Run the setup wizard first.</p>
        )}
      </div>

      {/* User preferences — persisted via trader_app.api.settings.save_settings */}
      {uiPrefs && (
        <div className="card p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-sky-100 dark:bg-sky-900/40 flex items-center justify-center">
                <SlidersHorizontal size={20} className="text-sky-700 dark:text-sky-300" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Your preferences</h2>
                <p className="text-sm text-gray-500 dark:text-slate-400">Saved to your user account (and cache) in ERPNext</p>
              </div>
            </div>
            <button type="button" onClick={() => void handleSave()} disabled={saving} className="btn-primary flex items-center justify-center gap-2 self-start">
              <Save size={14} /> {saving ? 'Saving…' : 'Save preferences'}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-5">
            <label className="block">
              <span className="text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wide">Language</span>
              <select
                className="input-field mt-1"
                value={uiPrefs.language}
                onChange={(e) => setUiPrefs((p) => (p ? { ...p, language: e.target.value } : p))}
              >
                {LANGUAGES.map((l) => (
                  <option key={l.value} value={l.value}>
                    {l.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wide">Time zone</span>
              <select
                className="input-field mt-1"
                value={uiPrefs.time_zone}
                onChange={(e) => setUiPrefs((p) => (p ? { ...p, time_zone: e.target.value } : p))}
              >
                {TIME_ZONES.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wide">Date format</span>
              <select
                className="input-field mt-1"
                value={uiPrefs.date_format}
                onChange={(e) => setUiPrefs((p) => (p ? { ...p, date_format: e.target.value } : p))}
              >
                {DATE_FORMATS.map((df) => (
                  <option key={df} value={df}>
                    {df}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wide">Number format</span>
              <select
                className="input-field mt-1"
                value={uiPrefs.number_format}
                onChange={(e) => setUiPrefs((p) => (p ? { ...p, number_format: e.target.value } : p))}
              >
                {NUMBER_FORMATS.map((nf) => (
                  <option key={nf} value={nf}>
                    {nf}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wide">Decimal places</span>
              <select
                className="input-field mt-1"
                value={String(uiPrefs.float_precision)}
                onChange={(e) =>
                  setUiPrefs((p) => (p ? { ...p, float_precision: parseInt(e.target.value, 10) || 3 } : p))
                }
              >
                {[1, 2, 3, 4, 5, 6].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wide">Session expiry (minutes)</span>
              <select
                className="input-field mt-1"
                value={String(uiPrefs.session_expiry)}
                onChange={(e) =>
                  setUiPrefs((p) => (p ? { ...p, session_expiry: parseInt(e.target.value, 10) || 240 } : p))
                }
              >
                {SESSION_EXPIRY_MINUTES.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
              <span className="text-xs text-gray-400 dark:text-slate-500 mt-1 block">Applied system-wide only if your user can update System Settings.</span>
            </label>
          </div>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
            <ToggleRow
              label="Dark mode"
              description="Easier on the eyes in low light"
              checked={uiPrefs.dark_mode === 1}
              onChange={(on) => setUiPrefs((p) => (p ? { ...p, dark_mode: on ? 1 : 0 } : p))}
            />
            <ToggleRow
              label="Compact tables"
              description="Reserved for future tighter table density"
              checked={uiPrefs.compact_tables === 1}
              onChange={(on) => setUiPrefs((p) => (p ? { ...p, compact_tables: on ? 1 : 0 } : p))}
            />
            <ToggleRow
              label="Email notifications"
              description="Preference flag for future notification features"
              checked={uiPrefs.email_notifications === 1}
              onChange={(on) => setUiPrefs((p) => (p ? { ...p, email_notifications: on ? 1 : 0 } : p))}
            />
            <ToggleRow
              label="Two-factor authentication (intent)"
              description="Stored as preference; enable 2FA in ERPNext User security for enforcement"
              checked={uiPrefs.enable_two_factor === 1}
              onChange={(on) => setUiPrefs((p) => (p ? { ...p, enable_two_factor: on ? 1 : 0 } : p))}
            />
          </div>
        </div>
      )}

      <CurrencySettingsPanel />

      <div className="card p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-violet-100 dark:bg-violet-900/40 flex items-center justify-center">
              <ScrollText size={20} className="text-violet-700 dark:text-violet-300" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Audit log</h2>
              <p className="text-sm text-gray-500 dark:text-slate-400">Who changed sales, purchase, and finance documents</p>
            </div>
          </div>
          <Link to="/settings/audit" className="btn-secondary self-start">
            View activity
          </Link>
        </div>
      </div>

      {/* Custom Roles */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center">
            <Shield size={20} className="text-emerald-700 dark:text-emerald-300" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Trader Roles</h2>
            <p className="text-sm text-gray-500 dark:text-slate-400">Custom roles created by the Trader module</p>
          </div>
        </div>
        {roles.length > 0 ? (
          <div className="divide-y divide-gray-100 dark:divide-slate-700">
            {roles.map((role) => (
              <div key={role.name} className="flex items-center justify-between py-3">
                <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{role.name}</span>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-medium ${
                    role.disabled ? 'bg-red-100 text-red-700 dark:bg-red-950/50 dark:text-red-300' : 'bg-green-100 text-green-700 dark:bg-emerald-950/50 dark:text-emerald-300'
                  }`}
                >
                  {role.disabled ? 'Disabled' : 'Active'}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 dark:text-slate-400 text-sm">No custom Trader roles found. Roles are created during app installation.</p>
        )}
      </div>

      {/* System Info */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/40 flex items-center justify-center">
            <Globe size={20} className="text-purple-700 dark:text-purple-300" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">System Information</h2>
            <p className="text-sm text-gray-500 dark:text-slate-400">Application and environment details</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
          <InfoRow label="Application" value="Trader App v1.0.0" />
          <InfoRow label="Framework" value="Frappe v15 / ERPNext v15" />
          <InfoRow label="Frontend" value="React 18 + TypeScript + Vite" />
          <InfoRow label="CSS Framework" value="Tailwind CSS 3" />
          <InfoRow label="Database" value="MariaDB 10.11" />
          <InfoRow label="Cache" value="Redis 7" />
        </div>
      </div>

      {/* Quick Links */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center">
            <Users size={20} className="text-amber-700 dark:text-amber-300" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Administration Links</h2>
            <p className="text-sm text-gray-500 dark:text-slate-400">Jump to ERPNext admin panels</p>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <AdminLink href="/app/user" label="User Management" description="Manage user accounts and permissions" />
          <AdminLink href="/app/role" label="Role Management" description="Configure roles and access levels" />
          <AdminLink href="/app/company" label="Company Settings" description="Edit company details and defaults" />
          <AdminLink href="/app/fiscal-year" label="Fiscal Year" description="Set active fiscal year period" />
          <AdminLink href="/app/warehouse" label="Warehouses" description="Configure warehouse structure" />
          <AdminLink href="/app/accounts-settings" label="Accounting" description="Configure accounting defaults" />
        </div>
      </div>
    </div>
  );
}

function ToggleRow({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (on: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-gray-200 dark:border-slate-600 bg-gray-50/80 dark:bg-slate-800/50 px-4 py-3 sm:min-w-[240px] sm:flex-1">
      <input type="checkbox" className="mt-1 h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span>
        <span className="block text-sm font-medium text-gray-900 dark:text-gray-100">{label}</span>
        <span className="block text-xs text-gray-500 dark:text-slate-400 mt-0.5">{description}</span>
      </span>
    </label>
  );
}

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <dt className="text-xs font-medium text-gray-500 dark:text-slate-400 uppercase tracking-wide">{label}</dt>
      <dd className="text-sm text-gray-900 dark:text-gray-100 mt-0.5">{value || '—'}</dd>
    </div>
  );
}

function AdminLink({ href, label, description }: { href: string; label: string; description: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="block p-4 rounded-lg border border-gray-200 dark:border-slate-600 hover:border-brand-300 dark:hover:border-brand-600 hover:shadow-sm transition-all dark:bg-slate-900/30"
    >
      <h4 className="text-sm font-medium text-brand-700 dark:text-brand-300">{label}</h4>
      <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">{description}</p>
    </a>
  );
}

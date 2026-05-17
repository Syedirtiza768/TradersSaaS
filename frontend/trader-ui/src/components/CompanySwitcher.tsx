import { useState } from 'react';
import { Building2, ChevronDown, Loader2 } from 'lucide-react';
import { useCompanyStore } from '../stores/companyStore';

export default function CompanySwitcher() {
  const { company, companies, loading, setCompany } = useCompanyStore();
  const [open, setOpen] = useState(false);
  const [switching, setSwitching] = useState(false);

  if (!company || companies.length === 0) return null;

  const handleSelect = async (name: string) => {
    if (name === company) {
      setOpen(false);
      return;
    }
    setSwitching(true);
    try {
      await setCompany(name);
      setOpen(false);
    } catch {
      /* error logged in store */
    } finally {
      setSwitching(false);
    }
  };

  const label = companies.find((c) => c.name === company)?.abbr || company;

  return (
    <div className="relative hidden sm:block">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        disabled={loading || switching || companies.length < 2}
        className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-60 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
        aria-label="Switch company"
        title={company}
      >
        {switching || loading ? (
          <Loader2 className="h-4 w-4 animate-spin text-brand-600" />
        ) : (
          <Building2 className="h-4 w-4 text-brand-600" />
        )}
        <span className="max-w-[140px] truncate">{label}</span>
        {companies.length > 1 && <ChevronDown className="h-4 w-4 text-gray-400" />}
      </button>

      {open && companies.length > 1 && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} aria-hidden="true" />
          <div className="absolute right-0 mt-2 w-64 rounded-lg border border-gray-200 bg-white py-1 shadow-lg z-50 dark:border-slate-600 dark:bg-slate-800">
            <p className="px-3 py-2 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-slate-400">
              Active company
            </p>
            {companies.map((c) => (
              <button
                key={c.name}
                type="button"
                onClick={() => void handleSelect(c.name)}
                className={`w-full px-3 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-slate-700 ${
                  c.name === company ? 'bg-brand-50 text-brand-800 font-medium dark:bg-brand-900/30 dark:text-brand-200' : 'text-gray-800 dark:text-slate-200'
                }`}
              >
                <span className="block truncate">{c.name}</span>
                {c.abbr && <span className="text-xs text-gray-500 dark:text-slate-400">{c.abbr}</span>}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

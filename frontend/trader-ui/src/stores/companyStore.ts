import { create } from 'zustand';
import { companyApi, registerActiveCompanyGetter } from '../lib/api';

export type CompanyOption = {
  name: string;
  abbr: string;
  default_currency?: string;
  country?: string;
  multi_currency_enabled?: boolean;
};

interface CompanyState {
  company: string | null;
  abbr: string | null;
  currency: string | null;
  multiCurrencyEnabled: boolean;
  companies: CompanyOption[];
  initialized: boolean;
  loading: boolean;
  revision: number;

  load: () => Promise<void>;
  setCompany: (company: string) => Promise<void>;
}

registerActiveCompanyGetter(() => useCompanyStore.getState().company || undefined);

export const useCompanyStore = create<CompanyState>((set, get) => ({
  company: null,
  abbr: null,
  currency: null,
  multiCurrencyEnabled: false,
  companies: [],
  initialized: false,
  loading: false,
  revision: 0,

  load: async () => {
    set({ loading: true });
    try {
      const [companiesRes, activeRes] = await Promise.all([
        companyApi.getCompanies(),
        companyApi.getActive(),
      ]);
      const companies = (companiesRes.data.message || []) as CompanyOption[];
      const active = activeRes.data.message || {};
      const company = active.company || companies[0]?.name || null;

      set({
        companies,
        company,
        abbr: active.abbr || companies.find((c) => c.name === company)?.abbr || null,
        currency: active.default_currency || companies.find((c) => c.name === company)?.default_currency || null,
        multiCurrencyEnabled: Boolean(active.multi_currency_enabled),
        initialized: true,
        loading: false,
      });
    } catch (err) {
      console.error('Failed to load company context:', err);
      set({ initialized: true, loading: false });
    }
  },

  setCompany: async (company: string) => {
    if (!company || company === get().company) return;
    set({ loading: true });
    try {
      const res = await companyApi.setActive(company);
      const active = res.data.message?.active || {};
      set((state) => ({
        company: active.company || company,
        abbr: active.abbr || state.companies.find((c) => c.name === company)?.abbr || null,
        currency: active.default_currency || state.companies.find((c) => c.name === company)?.default_currency || null,
        multiCurrencyEnabled: Boolean(active.multi_currency_enabled),
        loading: false,
        revision: state.revision + 1,
      }));
      window.dispatchEvent(new CustomEvent('trader-company-changed', { detail: { company } }));
    } catch (err) {
      console.error('Failed to switch company:', err);
      set({ loading: false });
      throw err;
    }
  },
}));

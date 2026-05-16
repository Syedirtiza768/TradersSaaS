import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';
import { customersApi, financeApi, suppliersApi } from '../lib/api';
import { appendPreservedListQuery, extractFrappeError, formatCurrency, formatDate, isFilterListContext, isOperationsContext, isReportContext, isWorkflowContext } from '../lib/utils';
import SearchableSelect from '../components/SearchableSelect';
import useQuickAdd from '../components/useQuickAdd';
import QuickAddProvider from '../components/QuickAddProvider';

type PartyTransaction = {
  name: string;
  posting_date?: string;
  grand_total?: number;
  outstanding_amount?: number;
  status?: string;
};

type PaymentMode = {
  name: string;
  type?: string;
};

type SettlementAccount = {
  name: string;
  account_name?: string;
  account_type?: string;
  account_number?: string;
};

export default function CreatePaymentEntryPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isBootstrappingFromQuery = useRef(true);
  // Holds the referenceName from the URL until references finish loading,
  // so the loadReferences effect doesn't wipe it before the list arrives.
  const pendingReferenceName = useRef<string>(searchParams.get('referenceName') || '');

  // Initialise state directly from URL params — avoids race conditions between effects
  const _initPaymentType = searchParams.get('paymentType');
  const _initPartyType = searchParams.get('partyType');
  const _initAmount = searchParams.get('amount');

  const [paymentType, setPaymentType] = useState<'Receive' | 'Pay'>(
    _initPaymentType === 'Pay' ? 'Pay' : 'Receive'
  );
  const [partyType, setPartyType] = useState<'Customer' | 'Supplier'>(
    _initPartyType === 'Supplier' ? 'Supplier' : 'Customer'
  );
  const [party, setParty] = useState('');
  const [amount, setAmount] = useState(_initAmount && !Number.isNaN(Number(_initAmount)) ? Number(_initAmount) : 0);
  const [postingDate, setPostingDate] = useState(searchParams.get('postingDate') || today());
  const [modeOfPayment, setModeOfPayment] = useState('');
  const [referenceDoctype, setReferenceDoctype] = useState(
    _initPaymentType === 'Pay' ? 'Purchase Invoice' : 'Sales Invoice'
  );
  const [referenceName, setReferenceName] = useState(searchParams.get('referenceName') || '');
  const [parties, setParties] = useState<any[]>([]);
  const [references, setReferences] = useState<PartyTransaction[]>([]);
  const [paymentModes, setPaymentModes] = useState<PaymentMode[]>([]);
  const [settlementAccounts, setSettlementAccounts] = useState<SettlementAccount[]>([]);
  const [modeAccounts, setModeAccounts] = useState<Record<string, string>>({});
  const [settlementAccount, setSettlementAccount] = useState('');
  const [referenceNo, setReferenceNo] = useState(searchParams.get('referenceName') || '');
  const [referenceDate, setReferenceDate] = useState(searchParams.get('postingDate') || today());
  const [accountDefaults, setAccountDefaults] = useState<Record<string, string>>({});
  const [loadingReferences, setLoadingReferences] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listSearch = searchParams.get('list');
  const quickAdd = useQuickAdd();
  const backToPath = useMemo(() => {
    if (!listSearch) {
      return '/finance/payments';
    }

    if (isReportContext(listSearch)) {
      return `/reports?${listSearch}`;
    }
    if (isOperationsContext(listSearch)) {
      return `/operations?${listSearch}`;
    }
    if (isFilterListContext(listSearch)) {
      if (searchParams.get('partyType') === 'Supplier' || searchParams.get('paymentType') === 'Pay') {
        return `/suppliers?${listSearch}`;
      }
      if (searchParams.get('partyType') === 'Customer' || searchParams.get('paymentType') === 'Receive') {
        return `/customers?${listSearch}`;
      }
    }
    if (isWorkflowContext(listSearch)) {
      return (searchParams.get('partyType') === 'Supplier' || searchParams.get('paymentType') === 'Pay')
        ? `/purchases/orders?${listSearch}`
        : `/sales/orders?${listSearch}`;
    }

    return '/finance/payments';
  }, [listSearch, searchParams]);
  const backLabel = backToPath.startsWith('/reports')
    ? 'Back to Reports'
    : backToPath.startsWith('/operations')
      ? 'Back to Operations'
      : backToPath.startsWith('/customers')
        ? 'Back to Customers'
        : backToPath.startsWith('/suppliers')
          ? 'Back to Suppliers'
          : backToPath.startsWith('/sales/orders')
            ? 'Back to Sales Orders'
            : backToPath.startsWith('/purchases/orders')
              ? 'Back to Purchase Orders'
              : 'Back to Payment Entries';

  // Mark bootstrapping done after first mount so paymentType/partyType changes
  // triggered by the user (not URL init) correctly reset party/references.
  useEffect(() => {
    isBootstrappingFromQuery.current = false;
  }, []);

  // Resolve party from URL param once the parties list is loaded.
  // The URL may pass either the doc name (e.g. "CUST-00001") or the
  // display name (e.g. "Popular Shaikh Hub") — match either field.
  // If not found in the already-loaded page, search the backend.
  useEffect(() => {
    const partyParam = searchParams.get('party');
    if (!partyParam || loading) return;

    // Check if the value already matches an existing option (exact doc name)
    const exactMatch = parties.find((p) => p.name === partyParam);
    if (exactMatch) {
      setParty(exactMatch.name);
      return;
    }

    // Otherwise match by display name (customer_name / supplier_name)
    const normalised = partyParam.trim().toLowerCase();
    const nameMatch = parties.find(
      (p) =>
        (p.customer_name || '').toLowerCase() === normalised ||
        (p.supplier_name || '').toLowerCase() === normalised ||
        p.name.toLowerCase() === normalised,
    );
    if (nameMatch) {
      setParty(nameMatch.name);
      return;
    }

    // Not in the loaded page — search backend by display name
    const search = async () => {
      try {
        const res = partyType === 'Customer'
          ? await customersApi.getList({ search: partyParam, page: 1, page_size: 10 })
          : await suppliersApi.getList({ search: partyParam, page: 1, page_size: 10 });
        const results: any[] = res.data.message?.data || [];
        const found = results.find(
          (p) =>
            p.name === partyParam ||
            (p.customer_name || '').toLowerCase() === normalised ||
            (p.supplier_name || '').toLowerCase() === normalised,
        );
        if (found) {
          // Add to parties list so the dropdown renders the option, then select it
          setParties((prev) => (prev.some((p) => p.name === found.name) ? prev : [...prev, found]));
          setParty(found.name);
        }
      } catch {
        // silently ignore — user can select manually
      }
    };
    void search();
  }, [parties, loading, searchParams, partyType]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [partyResponse, setupResponse] = await Promise.all([
          partyType === 'Customer'
            ? customersApi.getList({ page: 1, page_size: 100 })
            : suppliersApi.getList({ page: 1, page_size: 100 }),
          financeApi.getPaymentEntrySetup(),
        ]);
        const setup = setupResponse.data.message || {};
        const modes: PaymentMode[] = setup.modes || [];
        setParties(partyResponse.data.message?.data || []);
        setPaymentModes(modes);
        setSettlementAccounts(setup.settlement_accounts || []);
        setModeAccounts(setup.mode_accounts || {});
        setAccountDefaults(setup.defaults || {});
        // Set a sensible default mode after loading — prefer "Cash", else first available
        setModeOfPayment((prev) => {
          if (prev) return prev; // already set (e.g. from URL param in future)
          const cash = modes.find((m) => m.name === 'Cash');
          return cash ? cash.name : (modes[0]?.name || '');
        });
      } catch (err) {
        console.error('Failed to load payment form data:', err);
        setError('Could not load available parties and payment settings.');
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [partyType]);

  useEffect(() => {
    if (paymentType === 'Receive') {
      setPartyType('Customer');
      setReferenceDoctype('Sales Invoice');
    } else {
      setPartyType('Supplier');
      setReferenceDoctype('Purchase Invoice');
    }

    if (isBootstrappingFromQuery.current) {
      return;
    }

    setParty('');
    // Only clear referenceName if there's no pending URL param in flight
    if (!pendingReferenceName.current) {
      setReferenceName('');
    }
    setReferences([]);
  }, [paymentType]);

  useEffect(() => {
    const loadReferences = async () => {
      if (!party) {
        setReferences([]);
        // Only clear referenceName state; preserve pendingReferenceName ref
        // so it's still available when party resolves
        setReferenceName((prev) => (pendingReferenceName.current ? prev : ''));
        return;
      }

      setLoadingReferences(true);
      try {
        const response = partyType === 'Customer'
          ? await customersApi.getTransactions(party, { page: 1, page_size: 100 })
          : await suppliersApi.getTransactions(party, { page: 1, page_size: 100 });

        const rows = (response.data.message?.data || []).filter((row: PartyTransaction) => (row.outstanding_amount || 0) > 0);
        setReferences(rows);

        // Apply pending reference name from URL param now that the list is loaded
        const pending = pendingReferenceName.current;
        if (pending) {
          const match = rows.find((row: PartyTransaction) => row.name === pending);
          if (match) {
            setReferenceName(match.name);
            // If no amount was passed in the URL, auto-fill from outstanding amount
            setAmount((prev) => (prev > 0 ? prev : Number(match.outstanding_amount) || 0));
          } else {
            // Invoice not in outstanding list — clear
            setReferenceName('');
          }
          pendingReferenceName.current = '';
        } else if (referenceName && !rows.some((row: PartyTransaction) => row.name === referenceName)) {
          // Active reference no longer outstanding — clear it
          setReferenceName('');
        }
      } catch (err) {
        console.error('Failed to load invoice references:', err);
        setError('Could not load invoice references for the selected party.');
        setReferences([]);
      } finally {
        setLoadingReferences(false);
      }
    };

    void loadReferences();
  }, [party, partyType]);

  const selectedReference = references.find((entry) => entry.name === referenceName);

  const filteredSettlementAccounts = useMemo(() => {
    const mode = paymentModes.find((m) => m.name === modeOfPayment);
    const wantsBank = mode?.type === 'Bank' || modeOfPayment.toLowerCase().includes('bank');
    const typed = settlementAccounts.filter((a) => (wantsBank ? a.account_type === 'Bank' : a.account_type === 'Cash'));
    return typed.length > 0 ? typed : settlementAccounts;
  }, [modeOfPayment, paymentModes, settlementAccounts]);

  useEffect(() => {
    if (filteredSettlementAccounts.length === 0) return;
    const mapped = modeOfPayment ? modeAccounts[modeOfPayment] : '';
    if (mapped && filteredSettlementAccounts.some((a) => a.name === mapped)) {
      setSettlementAccount(mapped);
      return;
    }
    setSettlementAccount((prev) => {
      if (prev && filteredSettlementAccounts.some((a) => a.name === prev)) return prev;
      return filteredSettlementAccounts[0].name;
    });
  }, [filteredSettlementAccounts, modeAccounts, modeOfPayment]);

  // When user manually picks a reference, auto-fill amount from outstanding_amount
  useEffect(() => {
    if (selectedReference && (!amount || amount <= 0)) {
      setAmount(Number(selectedReference.outstanding_amount) || 0);
    }
  }, [selectedReference]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (referenceName && !referenceNo) {
      setReferenceNo(referenceName);
    }
  }, [referenceName, referenceNo]);

  const effectiveAccount = settlementAccount
    || (paymentType === 'Receive'
      ? (modeOfPayment.toLowerCase().includes('bank') ? accountDefaults.bank_account : accountDefaults.receive_account)
      : (modeOfPayment.toLowerCase().includes('bank') ? accountDefaults.bank_account : accountDefaults.pay_account));

  const selectedSettlementAccount = settlementAccounts.find((a) => a.name === settlementAccount);
  const requiresBankReference = selectedSettlementAccount?.account_type === 'Bank'
    || (!selectedSettlementAccount && modeOfPayment.toLowerCase().includes('bank'));

  const settlementLabel = (account: SettlementAccount) => {
    const typeLabel = account.account_type === 'Bank' ? 'Bank' : 'Cash';
    return `${typeLabel}: ${account.account_name || account.name}`;
  };

  const handleSubmit = async () => {
    if (!party) {
      setError('Please select a party before creating the payment entry.');
      return;
    }

    if (!amount || amount <= 0) {
      setError('Enter a valid payment amount.');
      return;
    }

    if (requiresBankReference && !referenceNo.trim()) {
      setError('Reference No is required for bank payments.');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const response = await financeApi.createPaymentEntry({
        payment_type: paymentType,
        party_type: partyType,
        party,
        amount,
        posting_date: postingDate,
        mode_of_payment: modeOfPayment,
        reference_doctype: referenceDoctype || undefined,
        reference_name: referenceName || undefined,
        ...(paymentType === 'Receive'
          ? { paid_to: settlementAccount || undefined }
          : { paid_from: settlementAccount || undefined }),
        reference_no: referenceNo.trim() || referenceName || undefined,
        reference_date: requiresBankReference ? (referenceDate || postingDate) : undefined,
      });
      const created = response.data.message;
      navigate(appendPreservedListQuery(`/finance/payments/${encodeURIComponent(created.name)}`, listSearch));
    } catch (err: any) {
      console.error('Failed to create payment entry:', err);
      setError(extractFrappeError(err, 'Could not create payment entry.'));
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
          <h1 className="page-title">New Payment Entry</h1>
          <p className="mt-1 text-gray-500">Create a draft payment entry for receipts or supplier payments.</p>
        </div>
        <button onClick={handleSubmit} disabled={saving || loading || loadingReferences} className="btn-primary flex items-center gap-2 disabled:opacity-60">
          <Save size={14} /> {saving ? 'Creating…' : 'Create Draft'}
        </button>
      </div>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="card p-6 lg:col-span-2 space-y-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Field label="Payment Type">
              <SearchableSelect
                value={paymentType}
                onChange={(v) => setPaymentType(v as 'Receive' | 'Pay')}
                options={[{ label: 'Receive', value: 'Receive' }, { label: 'Pay', value: 'Pay' }]}
                placeholder="Select type"
              />
            </Field>
            <Field label="Party Type">
              <input value={partyType} disabled className="input-field bg-gray-50" />
            </Field>
            <Field label="Party">
              <SearchableSelect
                value={party}
                onChange={setParty}
                options={parties.map((e) => ({ label: e.customer_name || e.supplier_name || e.name, value: e.name }))}
                placeholder={`Select ${partyType.toLowerCase()}`}
                disabled={loading}
                creatable
                onCreateNew={(q) => quickAdd.open(partyType === 'Customer' ? 'customer' : 'supplier', q)}
              />
            </Field>
            <Field label="Amount">
              <input type="number" min={0} step="0.01" value={amount} onChange={(e) => setAmount(Number(e.target.value))} className="input-field" />
            </Field>
            <Field label="Posting Date">
              <input type="date" value={postingDate} onChange={(e) => setPostingDate(e.target.value)} className="input-field" />
            </Field>
            <Field label="Mode of Payment">
              <div className="space-y-1">
                <SearchableSelect
                  value={modeOfPayment}
                  onChange={setModeOfPayment}
                  options={paymentModes.map((m) => ({ label: m.name, value: m.name }))}
                  placeholder={loading ? 'Loading…' : 'Select mode'}
                  disabled={loading}
                />
                <p className="text-xs text-gray-500">
                  {effectiveAccount
                    ? `${paymentType === 'Receive' ? 'Funds will be received into' : 'Funds will be paid from'} ${effectiveAccount}.`
                    : 'Default account will be derived from company payment settings.'}
                </p>
              </div>
            </Field>
            <Field label={paymentType === 'Receive' ? 'Deposit To' : 'Pay From'}>
              <SearchableSelect
                value={settlementAccount}
                onChange={setSettlementAccount}
                options={filteredSettlementAccounts.map((a) => ({
                  label: settlementLabel(a),
                  value: a.name,
                }))}
                placeholder={loading ? 'Loading…' : 'Select bank or cash account'}
                disabled={loading || filteredSettlementAccounts.length === 0}
              />
            </Field>
            {requiresBankReference && (
              <>
                <Field label="Reference No">
                  <input
                    type="text"
                    value={referenceNo}
                    onChange={(e) => setReferenceNo(e.target.value)}
                    className="input-field"
                    placeholder="Cheque / transfer reference"
                  />
                </Field>
                <Field label="Reference Date">
                  <input
                    type="date"
                    value={referenceDate}
                    onChange={(e) => setReferenceDate(e.target.value)}
                    className="input-field"
                  />
                </Field>
              </>
            )}
            <Field label="Reference Doctype">
              <input value={referenceDoctype} onChange={(e) => setReferenceDoctype(e.target.value)} className="input-field bg-gray-50" placeholder="Optional" disabled />
            </Field>
            <Field label="Reference Name">
              <div className="space-y-1">
                <SearchableSelect
                  value={referenceName}
                  onChange={setReferenceName}
                  options={references.map((e) => ({
                    label: `${e.name} · ${formatDate(e.posting_date)} · ${formatCurrency(e.outstanding_amount || 0)} outstanding`,
                    value: e.name,
                  }))}
                  placeholder={party ? 'Select outstanding invoice' : 'Select party first'}
                  disabled={loadingReferences || !party}
                />
                <p className="text-xs text-gray-500">
                  {selectedReference
                    ? `${selectedReference.status || 'Open'} · Total ${formatCurrency(selectedReference.grand_total || 0)} · Outstanding ${formatCurrency(selectedReference.outstanding_amount || 0)}`
                    : party
                      ? 'Choose an outstanding invoice to allocate this payment automatically.'
                      : 'Select a customer or supplier to load open invoice references.'}
                </p>
              </div>
            </Field>
          </div>
        </div>

        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Summary</h2>
          <SummaryRow label="Payment Type" value={paymentType} />
          <SummaryRow label="Party Type" value={partyType} />
          <SummaryRow label="Reference" value={referenceName || 'Not linked'} />
          <SummaryRow label="Settlement Account" value={effectiveAccount || 'Auto-derived'} />
          <SummaryRow label="Amount" value={formatCurrency(amount)} />
          <SummaryRow label="Posting Date" value={postingDate} />
          <p className="text-xs leading-5 text-gray-500">
            This creates a draft Payment Entry through the existing whitelisted finance API and then opens the detail screen.
          </p>
        </div>
      </div>

      <QuickAddProvider
        quickAdd={quickAdd}
        customersSetter={partyType === 'Customer' ? setParties : undefined}
        customerValueSetter={partyType === 'Customer' ? setParty : undefined}
        suppliersSetter={partyType === 'Supplier' ? setParties : undefined}
        supplierValueSetter={partyType === 'Supplier' ? setParty : undefined}
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
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { CreditCard, Loader2 } from 'lucide-react';
import { financeApi } from '../lib/api';
import { extractFrappeError, formatCurrency } from '../lib/utils';
import SearchableSelect from './SearchableSelect';

type PaymentMode = { name: string; type?: string };

type SettlementAccount = {
  name: string;
  account_name?: string;
  account_type?: string;
  account_number?: string;
};

type Props = {
  referenceDoctype: 'Sales Invoice' | 'Purchase Invoice';
  referenceName: string;
  partyLabel: string;
  outstandingAmount: number;
  currency?: string;
  onRecorded: () => void | Promise<void>;
};

export default function RecordInvoicePaymentPanel({
  referenceDoctype,
  referenceName,
  partyLabel,
  outstandingAmount,
  currency,
  onRecorded,
}: Props) {
  const isReceive = referenceDoctype === 'Sales Invoice';
  const [amount, setAmount] = useState(outstandingAmount);
  const [postingDate, setPostingDate] = useState(today());
  const [modeOfPayment, setModeOfPayment] = useState('');
  const [settlementAccount, setSettlementAccount] = useState('');
  const [referenceNo, setReferenceNo] = useState(referenceName);
  const [referenceDate, setReferenceDate] = useState(today());
  const [paymentModes, setPaymentModes] = useState<PaymentMode[]>([]);
  const [settlementAccounts, setSettlementAccounts] = useState<SettlementAccount[]>([]);
  const [modeAccounts, setModeAccounts] = useState<Record<string, string>>({});
  const [loadingSetup, setLoadingSetup] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    setAmount(outstandingAmount);
  }, [outstandingAmount]);

  useEffect(() => {
    const load = async () => {
      setLoadingSetup(true);
      try {
        const response = await financeApi.getPaymentEntrySetup();
        const message = response.data.message || {};
        const modes: PaymentMode[] = message.modes || [];
        const accounts: SettlementAccount[] = message.settlement_accounts || [];
        setPaymentModes(modes);
        setSettlementAccounts(accounts);
        setModeAccounts(message.mode_accounts || {});

        const defaultMode = modes.find((m) => m.name === 'Bank Transfer')?.name
          || modes.find((m) => m.type === 'Bank')?.name
          || modes[0]?.name
          || '';
        setModeOfPayment((prev) => prev || defaultMode);
      } catch (err) {
        console.error('Failed to load payment setup:', err);
        setError('Could not load bank accounts and payment modes.');
      } finally {
        setLoadingSetup(false);
      }
    };

    void load();
  }, []);

  const filteredAccounts = useMemo(() => {
    const mode = paymentModes.find((m) => m.name === modeOfPayment);
    const wantsBank = mode?.type === 'Bank' || modeOfPayment.toLowerCase().includes('bank');
    const typed = settlementAccounts.filter((a) => (wantsBank ? a.account_type === 'Bank' : a.account_type === 'Cash'));
    if (wantsBank) {
      return typed;
    }
    return typed.length > 0 ? typed : settlementAccounts;
  }, [modeOfPayment, paymentModes, settlementAccounts]);

  useEffect(() => {
    if (loadingSetup || filteredAccounts.length === 0) return;

    const mapped = modeOfPayment ? modeAccounts[modeOfPayment] : '';
    if (mapped && filteredAccounts.some((a) => a.name === mapped)) {
      setSettlementAccount(mapped);
      return;
    }

    setSettlementAccount((prev) => {
      if (prev && filteredAccounts.some((a) => a.name === prev)) return prev;
      return filteredAccounts[0].name;
    });
  }, [filteredAccounts, loadingSetup, modeAccounts, modeOfPayment]);

  const selectedSettlementAccount = settlementAccounts.find((a) => a.name === settlementAccount);
  const requiresBankReference = selectedSettlementAccount?.account_type === 'Bank'
    || (!selectedSettlementAccount && modeOfPayment.toLowerCase().includes('bank'));

  const accountLabel = (account: SettlementAccount) => {
    const typeLabel = account.account_type === 'Bank' ? 'Bank' : 'Cash';
    const name = account.account_name || account.name;
    const number = account.account_number ? ` · ${account.account_number}` : '';
    return `${typeLabel}: ${name}${number}`;
  };

  const handleSubmit = async () => {
    if (!amount || amount <= 0) {
      setError('Enter a valid payment amount.');
      return;
    }
    if (!settlementAccount) {
      setError('Select the bank or cash account for this payment.');
      return;
    }
    if (amount > outstandingAmount + 0.005) {
      setError(`Amount cannot exceed outstanding ${formatCurrency(outstandingAmount, currency)}.`);
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const response = await financeApi.recordInvoicePayment({
        reference_doctype: referenceDoctype,
        reference_name: referenceName,
        amount,
        mode_of_payment: modeOfPayment || undefined,
        settlement_account: settlementAccount,
        posting_date: postingDate,
        reference_no: referenceNo.trim() || referenceName,
        reference_date: referenceDate || postingDate,
        submit: 1,
      });
      const result = response.data.message;
      setSuccess(
        `Payment ${result.name} recorded into ${result.settlement_account || settlementAccount}. `
        + `Outstanding: ${formatCurrency(result.outstanding_amount ?? 0, currency)}.`,
      );
      await onRecorded();
    } catch (err: unknown) {
      console.error('Failed to record invoice payment:', err);
      setError(extractFrappeError(err, 'Could not record payment.'));
    } finally {
      setSaving(false);
    }
  };

  if (outstandingAmount <= 0) {
    return null;
  }

  return (
    <div className="card">
      <div className="card-header flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-brand-600" />
            {isReceive ? 'Record Receipt' : 'Record Payment'}
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            {isReceive ? 'Receive from' : 'Pay'} {partyLabel} · Outstanding {formatCurrency(outstandingAmount, currency)}
          </p>
        </div>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={saving || loadingSetup}
          className="btn-primary inline-flex items-center gap-2 disabled:opacity-60"
        >
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {saving ? 'Recording…' : isReceive ? 'Record Receipt' : 'Record Payment'}
        </button>
      </div>
      <div className="card-body space-y-4">
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
        )}
        {success && (
          <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">{success}</div>
        )}
        {loadingSetup ? (
          <div className="flex justify-center py-6"><div className="spinner" /></div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Field label="Amount">
              <input
                type="number"
                min={0}
                step="0.01"
                max={outstandingAmount}
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                className="input-field"
              />
            </Field>
            <Field label="Posting Date">
              <input type="date" value={postingDate} onChange={(e) => setPostingDate(e.target.value)} className="input-field" />
            </Field>
            <Field label="Mode of Payment">
              <SearchableSelect
                value={modeOfPayment}
                onChange={setModeOfPayment}
                options={paymentModes.map((m) => ({ label: m.name, value: m.name }))}
                placeholder="Select mode"
              />
            </Field>
            <Field label={isReceive ? 'Deposit To' : 'Pay From'}>
              <SearchableSelect
                value={settlementAccount}
                onChange={setSettlementAccount}
                options={filteredAccounts.map((a) => ({ label: accountLabel(a), value: a.name }))}
                placeholder="Select bank or cash account"
              />
            </Field>
            <Field label={requiresBankReference ? 'Reference No' : 'Reference No (optional)'}>
              <input
                type="text"
                value={referenceNo}
                onChange={(e) => setReferenceNo(e.target.value)}
                className="input-field"
                placeholder="Cheque / transfer reference"
              />
            </Field>
            {requiresBankReference && (
              <Field label="Reference Date">
                <input
                  type="date"
                  value={referenceDate}
                  onChange={(e) => setReferenceDate(e.target.value)}
                  className="input-field"
                />
              </Field>
            )}
          </div>
        )}
        <p className="text-xs text-gray-500">
          Payment is submitted immediately and allocated to {referenceName}. Funds are booked into the selected account.
        </p>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="block">
      <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-500">{label}</span>
      {children}
    </div>
  );
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

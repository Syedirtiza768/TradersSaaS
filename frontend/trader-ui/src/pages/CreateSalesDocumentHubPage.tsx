import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, FileText, Plus } from 'lucide-react';
import { salesApi } from '../lib/api';
import { SALES_INVOICE_TYPES, type InvoiceTypeConfig } from '../lib/invoiceTypes';

export default function CreateSalesDocumentHubPage() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<InvoiceTypeConfig[]>(SALES_INVOICE_TYPES);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await salesApi.getDocumentCatalog();
        const rows = res.data.message?.documents;
        if (Array.isArray(rows) && rows.length > 0) {
          setDocuments(rows);
        }
      } catch {
        setDocuments(SALES_INVOICE_TYPES);
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <button
          type="button"
          onClick={() => navigate('/sales')}
          className="mb-3 inline-flex items-center gap-2 text-sm text-brand-700 hover:text-brand-800"
        >
          <ArrowLeft size={16} /> Back to Sales
        </button>
        <h1 className="page-title">Create Sales Document</h1>
        <p className="mt-1 text-gray-500">
          Choose the document type for Pakistan invoicing — tax invoice, commercial bill, proforma, credit note, or delivery challan.
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="spinner" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {documents.map((doc) => (
            <button
              key={doc.key}
              type="button"
              onClick={() => navigate(doc.route)}
              className="card p-5 text-left transition-shadow hover:shadow-md focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="rounded-lg bg-brand-50 p-2 text-brand-700">
                  <FileText className="h-5 w-5" />
                </div>
                <Plus className="h-4 w-4 text-gray-400" />
              </div>
              <h2 className="mt-4 text-base font-semibold text-gray-900">{doc.label}</h2>
              <p className="mt-1 text-sm text-gray-500">{doc.description}</p>
              <p className="mt-3 text-xs font-medium uppercase tracking-wide text-gray-400">{doc.doctype}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}


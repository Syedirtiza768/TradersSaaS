/** Pakistan trader document types — mirrors trader_app.api.invoice_types */

export type SalesInvoiceTypeKey =
  | 'tax_invoice'
  | 'commercial_invoice'
  | 'non_gst_invoice'
  | 'bill_of_supply'
  | 'credit_note';

export type PurchaseInvoiceTypeKey =
  | 'tax_invoice'
  | 'commercial_invoice'
  | 'non_gst_invoice'
  | 'bill_of_supply'
  | 'debit_note';

export type InvoiceTypeConfig = {
  key: string;
  label: string;
  description: string;
  doctype: string;
  route: string;
  /** When true, tax template is cleared on create unless user overrides */
  noTaxByDefault?: boolean;
  /** When true, tax template picker is hidden */
  hideTaxPicker?: boolean;
  /** Prefer exempt/zero template when taxes apply */
  useExemptTax?: boolean;
};

export const SALES_INVOICE_TYPES: InvoiceTypeConfig[] = [
  {
    key: 'tax_invoice',
    label: 'Tax Invoice',
    description: 'GST/sales tax invoice for registered sellers',
    doctype: 'Sales Invoice',
    route: '/sales/new?type=tax_invoice',
  },
  {
    key: 'commercial_invoice',
    label: 'Commercial Invoice',
    description: 'Bill of sale without tax lines',
    doctype: 'Sales Invoice',
    route: '/sales/new?type=commercial_invoice',
    noTaxByDefault: true,
    hideTaxPicker: true,
  },
  {
    key: 'non_gst_invoice',
    label: 'Non-GST Invoice',
    description: 'Sale documented without GST',
    doctype: 'Sales Invoice',
    route: '/sales/new?type=non_gst_invoice',
    noTaxByDefault: true,
    hideTaxPicker: true,
  },
  {
    key: 'bill_of_supply',
    label: 'Bill of Supply',
    description: 'Exempt or zero-rated supplies',
    doctype: 'Sales Invoice',
    route: '/sales/new?type=bill_of_supply',
    useExemptTax: true,
  },
  {
    key: 'credit_note',
    label: 'Credit Note',
    description: 'Return or adjustment against a sales invoice',
    doctype: 'Sales Invoice',
    route: '/sales/returns/new',
  },
  {
    key: 'proforma_invoice',
    label: 'Proforma Invoice',
    description: 'Non-binding quote before final billing',
    doctype: 'Quotation',
    route: '/sales/proforma/new',
  },
  {
    key: 'delivery_challan',
    label: 'Delivery Challan',
    description: 'Dispatch goods without billing',
    doctype: 'Delivery Note',
    route: '/sales/challans/new',
  },
];

export const PURCHASE_INVOICE_TYPES: InvoiceTypeConfig[] = [
  {
    key: 'tax_invoice',
    label: 'Tax Invoice',
    description: 'Purchase with GST/sales tax',
    doctype: 'Purchase Invoice',
    route: '/purchases/new?type=tax_invoice',
  },
  {
    key: 'commercial_invoice',
    label: 'Commercial Invoice',
    description: 'Supplier bill without tax',
    doctype: 'Purchase Invoice',
    route: '/purchases/new?type=commercial_invoice',
    noTaxByDefault: true,
    hideTaxPicker: true,
  },
  {
    key: 'non_gst_invoice',
    label: 'Non-GST Invoice',
    description: 'Purchase without GST on document',
    doctype: 'Purchase Invoice',
    route: '/purchases/new?type=non_gst_invoice',
    noTaxByDefault: true,
    hideTaxPicker: true,
  },
  {
    key: 'bill_of_supply',
    label: 'Bill of Supply',
    description: 'Exempt purchase documentation',
    doctype: 'Purchase Invoice',
    route: '/purchases/new?type=bill_of_supply',
    useExemptTax: true,
  },
  {
    key: 'debit_note',
    label: 'Debit Note',
    description: 'Return or adjustment against a purchase invoice',
    doctype: 'Purchase Invoice',
    route: '/purchases/returns/new',
  },
];

export function getSalesInvoiceTypeConfig(typeKey?: string | null): InvoiceTypeConfig {
  const key = typeKey || 'tax_invoice';
  return SALES_INVOICE_TYPES.find((t) => t.key === key) || SALES_INVOICE_TYPES[0];
}

export function getPurchaseInvoiceTypeConfig(typeKey?: string | null): InvoiceTypeConfig {
  const key = typeKey || 'tax_invoice';
  return PURCHASE_INVOICE_TYPES.find((t) => t.key === key) || PURCHASE_INVOICE_TYPES[0];
}

export function pickExemptTaxTemplate(templates: any[]): string {
  const match = templates.find((t) => {
    const title = `${t.title || ''} ${t.name || ''}`.toLowerCase();
    return title.includes('exempt') || title.includes('0%');
  });
  return match?.name || '';
}

export function documentTypeBadge(
  label?: string | null,
  isReturn?: number,
  doctype?: string,
): string {
  if (isReturn) {
    return doctype === 'Purchase Invoice' ? 'Debit Note' : 'Credit Note';
  }
  return label || 'Tax Invoice';
}

# -*- coding: utf-8 -*-
"""Trader App — Reports API.

Whitelisted endpoints for the Reports module:
- Sales Report
- Purchase Report
- Item Sales Report
- Customer Ledger
- Supplier Ledger
- Receivables Aging
- Payables Aging
- Profit & Loss
- Stock Ledger Report
- General Ledger
"""

from __future__ import unicode_literals

import frappe
from frappe import _
from trader_app.api.company import resolve_active_company
from frappe.utils import nowdate, getdate, add_months, flt, cint


# ────────────────────────────────────────────────────────────────
# 1.  SALES REPORT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_sales_report(company=None, from_date=None, to_date=None,
                     customer=None, item_group=None):
    """Sales report — grouped by month."""
    company = resolve_active_company(company)
    from_date = from_date or add_months(nowdate(), -12)
    to_date = to_date or nowdate()

    conditions = [
        "si.company = %(company)s",
        "si.docstatus = 1",
        "si.posting_date >= %(from_date)s",
        "si.posting_date <= %(to_date)s",
    ]
    params = {"company": company, "from_date": from_date, "to_date": to_date}

    if customer:
        conditions.append("si.customer = %(customer)s")
        params["customer"] = customer

    where = " AND ".join(conditions)

    rows = frappe.db.sql(f"""
        SELECT DATE_FORMAT(si.posting_date, '%%Y-%%m') AS month,
               COUNT(*) AS invoice_count,
               SUM(si.total) AS net_total,
               SUM(si.grand_total) AS grand_total,
               SUM(si.outstanding_amount) AS outstanding
        FROM `tabSales Invoice` si
        WHERE {where}
        GROUP BY month
        ORDER BY month
    """, params, as_dict=True)

    totals = frappe.db.sql(f"""
        SELECT COUNT(*) AS invoice_count,
               SUM(si.grand_total) AS grand_total,
               SUM(si.outstanding_amount) AS outstanding
        FROM `tabSales Invoice` si
        WHERE {where}
    """, params, as_dict=True)

    return {"data": rows, "totals": totals[0] if totals else {}}


# ────────────────────────────────────────────────────────────────
# 2.  PURCHASE REPORT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_purchase_report(company=None, from_date=None, to_date=None,
                        supplier=None):
    """Purchase report — grouped by month."""
    company = resolve_active_company(company)
    from_date = from_date or add_months(nowdate(), -12)
    to_date = to_date or nowdate()

    conditions = [
        "pi.company = %(company)s",
        "pi.docstatus = 1",
        "pi.posting_date >= %(from_date)s",
        "pi.posting_date <= %(to_date)s",
    ]
    params = {"company": company, "from_date": from_date, "to_date": to_date}

    if supplier:
        conditions.append("pi.supplier = %(supplier)s")
        params["supplier"] = supplier

    where = " AND ".join(conditions)

    rows = frappe.db.sql(f"""
        SELECT DATE_FORMAT(pi.posting_date, '%%Y-%%m') AS month,
               COUNT(*) AS invoice_count,
               SUM(pi.grand_total) AS grand_total,
               SUM(pi.outstanding_amount) AS outstanding
        FROM `tabPurchase Invoice` pi
        WHERE {where}
        GROUP BY month
        ORDER BY month
    """, params, as_dict=True)

    totals = frappe.db.sql(f"""
        SELECT COUNT(*) AS invoice_count,
               SUM(pi.grand_total) AS grand_total,
               SUM(pi.outstanding_amount) AS outstanding
        FROM `tabPurchase Invoice` pi
        WHERE {where}
    """, params, as_dict=True)

    return {"data": rows, "totals": totals[0] if totals else {}}


# ────────────────────────────────────────────────────────────────
# 3.  ITEM SALES REPORT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_item_sales_report(company=None, from_date=None, to_date=None,
                          item_group=None, page=1, page_size=20):
    """Top selling items."""
    company = resolve_active_company(company)
    from_date = from_date or add_months(nowdate(), -12)
    to_date = to_date or nowdate()
    page = cint(page) or 1
    page_size = min(cint(page_size) or 20, 100)
    offset = (page - 1) * page_size

    conditions = [
        "si.company = %(company)s",
        "si.docstatus = 1",
        "si.posting_date >= %(from_date)s",
        "si.posting_date <= %(to_date)s",
    ]
    params = {"company": company, "from_date": from_date, "to_date": to_date}

    if item_group:
        conditions.append("sii.item_group = %(item_group)s")
        params["item_group"] = item_group

    where = " AND ".join(conditions)

    total = frappe.db.sql(f"""
        SELECT COUNT(DISTINCT sii.item_code)
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE {where}
    """, params)[0][0]

    rows = frappe.db.sql(f"""
        SELECT sii.item_code, sii.item_name, sii.item_group,
               SUM(sii.qty) AS total_qty,
               SUM(sii.amount) AS total_amount,
               COUNT(DISTINCT si.name) AS invoice_count
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE {where}
        GROUP BY sii.item_code
        ORDER BY total_amount DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ────────────────────────────────────────────────────────────────
# 4.  CUSTOMER LEDGER
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_customer_ledger(customer, company=None, from_date=None, to_date=None):
    """GL entries for a specific customer."""
    company = resolve_active_company(company)
    from_date = from_date or add_months(nowdate(), -12)
    to_date = to_date or nowdate()

    rows = frappe.db.sql("""
        SELECT gle.posting_date, gle.voucher_type, gle.voucher_no,
               gle.debit, gle.credit, gle.remarks
        FROM `tabGL Entry` gle
        WHERE gle.company = %s AND gle.party_type = 'Customer'
              AND gle.party = %s AND gle.is_cancelled = 0
              AND gle.posting_date >= %s AND gle.posting_date <= %s
        ORDER BY gle.posting_date, gle.creation
    """, (company, customer, from_date, to_date), as_dict=True)

    # Running balance
    balance = 0
    for row in rows:
        balance += flt(row.debit) - flt(row.credit)
        row["balance"] = balance

    return rows


# ────────────────────────────────────────────────────────────────
# 5.  SUPPLIER LEDGER
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_supplier_ledger(supplier, company=None, from_date=None, to_date=None):
    """GL entries for a specific supplier."""
    company = resolve_active_company(company)
    from_date = from_date or add_months(nowdate(), -12)
    to_date = to_date or nowdate()

    rows = frappe.db.sql("""
        SELECT gle.posting_date, gle.voucher_type, gle.voucher_no,
               gle.debit, gle.credit, gle.remarks
        FROM `tabGL Entry` gle
        WHERE gle.company = %s AND gle.party_type = 'Supplier'
              AND gle.party = %s AND gle.is_cancelled = 0
              AND gle.posting_date >= %s AND gle.posting_date <= %s
        ORDER BY gle.posting_date, gle.creation
    """, (company, supplier, from_date, to_date), as_dict=True)

    balance = 0
    for row in rows:
        balance += flt(row.credit) - flt(row.debit)
        row["balance"] = balance

    return rows


# ────────────────────────────────────────────────────────────────
# 6.  RECEIVABLE AGING
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_receivable_aging(company=None):
    """Receivable aging summary — buckets 0-30, 31-60, 61-90, 90+."""
    company = resolve_active_company(company)
    today = nowdate()

    rows = frappe.db.sql("""
        SELECT
            SUM(CASE WHEN DATEDIFF(%s, posting_date) <= 30 THEN outstanding_amount ELSE 0 END) AS `0-30`,
            SUM(CASE WHEN DATEDIFF(%s, posting_date) BETWEEN 31 AND 60 THEN outstanding_amount ELSE 0 END) AS `31-60`,
            SUM(CASE WHEN DATEDIFF(%s, posting_date) BETWEEN 61 AND 90 THEN outstanding_amount ELSE 0 END) AS `61-90`,
            SUM(CASE WHEN DATEDIFF(%s, posting_date) > 90 THEN outstanding_amount ELSE 0 END) AS `90+`,
            SUM(outstanding_amount) AS total_outstanding
        FROM `tabSales Invoice`
        WHERE company = %s AND docstatus = 1 AND outstanding_amount > 0
    """, (today, today, today, today, company), as_dict=True)

    return rows[0] if rows else {}


@frappe.whitelist()
def get_receivable_aging_detail(company=None, page=1, page_size=20):
    """Per-customer receivable aging."""
    company = resolve_active_company(company)
    today = nowdate()
    page = cint(page) or 1
    page_size = min(cint(page_size) or 20, 100)
    offset = (page - 1) * page_size

    total = frappe.db.sql("""
        SELECT COUNT(DISTINCT customer)
        FROM `tabSales Invoice`
        WHERE company = %s AND docstatus = 1 AND outstanding_amount > 0
    """, (company,))[0][0]

    rows = frappe.db.sql("""
        SELECT customer, customer_name,
            SUM(CASE WHEN DATEDIFF(%s, posting_date) <= 30 THEN outstanding_amount ELSE 0 END) AS `0-30`,
            SUM(CASE WHEN DATEDIFF(%s, posting_date) BETWEEN 31 AND 60 THEN outstanding_amount ELSE 0 END) AS `31-60`,
            SUM(CASE WHEN DATEDIFF(%s, posting_date) BETWEEN 61 AND 90 THEN outstanding_amount ELSE 0 END) AS `61-90`,
            SUM(CASE WHEN DATEDIFF(%s, posting_date) > 90 THEN outstanding_amount ELSE 0 END) AS `90+`,
            SUM(outstanding_amount) AS total_outstanding
        FROM `tabSales Invoice`
        WHERE company = %s AND docstatus = 1 AND outstanding_amount > 0
        GROUP BY customer
        ORDER BY total_outstanding DESC
        LIMIT %s OFFSET %s
    """, (today, today, today, today, company, page_size, offset), as_dict=True)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ────────────────────────────────────────────────────────────────
# 7.  PAYABLE AGING
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_payable_aging(company=None):
    """Payable aging summary."""
    company = resolve_active_company(company)
    today = nowdate()

    rows = frappe.db.sql("""
        SELECT
            SUM(CASE WHEN DATEDIFF(%s, posting_date) <= 30 THEN outstanding_amount ELSE 0 END) AS `0-30`,
            SUM(CASE WHEN DATEDIFF(%s, posting_date) BETWEEN 31 AND 60 THEN outstanding_amount ELSE 0 END) AS `31-60`,
            SUM(CASE WHEN DATEDIFF(%s, posting_date) BETWEEN 61 AND 90 THEN outstanding_amount ELSE 0 END) AS `61-90`,
            SUM(CASE WHEN DATEDIFF(%s, posting_date) > 90 THEN outstanding_amount ELSE 0 END) AS `90+`,
            SUM(outstanding_amount) AS total_outstanding
        FROM `tabPurchase Invoice`
        WHERE company = %s AND docstatus = 1 AND outstanding_amount > 0
    """, (today, today, today, today, company), as_dict=True)

    return rows[0] if rows else {}


# ────────────────────────────────────────────────────────────────
# 8.  PROFIT & LOSS
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_profit_and_loss(company=None, from_date=None, to_date=None):
    """Simple P&L summary using GL Entries."""
    company = resolve_active_company(company)

    fy = _current_fiscal_year(company)
    from_date = from_date or fy["from"]
    to_date = to_date or fy["to"]

    def _sum_gl(root_type):
        result = frappe.db.sql("""
            SELECT COALESCE(SUM(gle.debit - gle.credit), 0)
            FROM `tabGL Entry` gle
            INNER JOIN `tabAccount` a ON a.name = gle.account
            WHERE gle.company = %s AND a.root_type = %s
                  AND gle.is_cancelled = 0
                  AND gle.posting_date >= %s AND gle.posting_date <= %s
        """, (company, root_type, from_date, to_date))
        return flt(result[0][0]) if result else 0

    total_income = abs(_sum_gl("Income"))
    total_expense = abs(_sum_gl("Expense"))

    # COGS: look for accounts with 'Cost of Goods' in name
    cogs = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(gle.debit - gle.credit), 0)
        FROM `tabGL Entry` gle
        INNER JOIN `tabAccount` a ON a.name = gle.account
        WHERE gle.company = %s AND a.root_type = 'Expense'
              AND a.name LIKE '%%Cost of Goods%%'
              AND gle.is_cancelled = 0
              AND gle.posting_date >= %s AND gle.posting_date <= %s
    """, (company, from_date, to_date))[0][0])

    gross_profit = total_income - cogs
    net_profit = total_income - total_expense

    return {
        "total_income": total_income,
        "cost_of_goods_sold": cogs,
        "gross_profit": gross_profit,
        "total_expense": total_expense,
        "net_profit": net_profit,
        "from_date": from_date,
        "to_date": to_date,
    }


# ────────────────────────────────────────────────────────────────
# 9.  GENERAL LEDGER
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_general_ledger(company=None, account=None, from_date=None, to_date=None,
                       page=1, page_size=50):
    """General Ledger report."""
    company = resolve_active_company(company)
    from_date = from_date or add_months(nowdate(), -3)
    to_date = to_date or nowdate()
    page = cint(page) or 1
    page_size = min(cint(page_size) or 50, 200)
    offset = (page - 1) * page_size

    conditions = [
        "gle.company = %(company)s",
        "gle.is_cancelled = 0",
        "gle.posting_date >= %(from_date)s",
        "gle.posting_date <= %(to_date)s",
    ]
    params = {"company": company, "from_date": from_date, "to_date": to_date}

    if account:
        conditions.append("gle.account = %(account)s")
        params["account"] = account

    where = " AND ".join(conditions)

    total = frappe.db.sql(
        f"SELECT COUNT(*) FROM `tabGL Entry` gle WHERE {where}", params
    )[0][0]

    rows = frappe.db.sql(f"""
        SELECT gle.posting_date, gle.account, gle.debit, gle.credit,
               gle.voucher_type, gle.voucher_no, gle.party_type, gle.party,
               gle.remarks
        FROM `tabGL Entry` gle
        WHERE {where}
        ORDER BY gle.posting_date, gle.creation
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ────────────────────────────────────────────────────────────────
# 10.  ACCOUNTS PAYABLE (for finance page)
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_accounts_payable(company=None):
    """Payable aging summary — same structure as receivable."""
    return get_payable_aging(company)


# ── CONSOLIDATED MULTI-COMPANY SUMMARY ─────────────────────────
@frappe.whitelist()
def get_consolidated_company_summary(from_date=None, to_date=None):
    """Per-company KPI rollup across all companies the user may access."""
    from trader_app.api.company import get_permitted_company_names

    from_date, to_date = _date_range(from_date, to_date)
    companies = get_permitted_company_names()
    rows = []
    summary = {
        "company_count": len(companies),
        "sales": 0,
        "purchases": 0,
        "receivables": 0,
        "payables": 0,
        "stock_value": 0,
    }

    for company in companies:
        currency = frappe.get_cached_value("Company", company, "default_currency") or "PKR"
        sales = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(grand_total), 0)
            FROM `tabSales Invoice`
            WHERE company = %s AND docstatus = 1
              AND posting_date BETWEEN %s AND %s
        """, (company, from_date, to_date))[0][0])

        purchases = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(grand_total), 0)
            FROM `tabPurchase Invoice`
            WHERE company = %s AND docstatus = 1
              AND posting_date BETWEEN %s AND %s
        """, (company, from_date, to_date))[0][0])

        receivables = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(outstanding_amount), 0)
            FROM `tabSales Invoice`
            WHERE company = %s AND docstatus = 1 AND outstanding_amount > 0
        """, (company,))[0][0])

        payables = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(outstanding_amount), 0)
            FROM `tabPurchase Invoice`
            WHERE company = %s AND docstatus = 1 AND outstanding_amount > 0
        """, (company,))[0][0])

        stock_value = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(b.stock_value), 0)
            FROM `tabBin` b
            INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
            WHERE w.company = %s
        """, (company,))[0][0])

        rows.append({
            "company": company,
            "currency": currency,
            "sales": sales,
            "purchases": purchases,
            "receivables": receivables,
            "payables": payables,
            "stock_value": stock_value,
        })
        summary["sales"] += sales
        summary["purchases"] += purchases
        summary["receivables"] += receivables
        summary["payables"] += payables
        summary["stock_value"] += stock_value

    return {
        "data": rows,
        "summary": summary,
        "from_date": from_date,
        "to_date": to_date,
    }


# ────────────────────────────────────────────────────────────────
#    HELPERS
# ────────────────────────────────────────────────────────────────


def _current_fiscal_year(company):
    from erpnext.accounts.utils import get_fiscal_year
    try:
        fy = get_fiscal_year(nowdate(), company=company)
        return {"from": fy[1].isoformat(), "to": fy[2].isoformat()}
    except Exception:
        today = getdate(nowdate())
        return {
            "from": today.replace(month=1, day=1).isoformat(),
            "to": today.replace(month=12, day=31).isoformat(),
        }


def _date_range(from_date, to_date, default_months=12):
    return (
        from_date or add_months(nowdate(), -default_months),
        to_date or nowdate(),
    )


def _paginate(page, page_size, max_size=200):
    page = cint(page) or 1
    page_size = min(cint(page_size) or 20, max_size)
    return page, page_size, (page - 1) * page_size


def _safe_pct(numerator, denominator):
    return round(flt(numerator) / flt(denominator) * 100, 2) if flt(denominator) else 0


def _csv_response(columns, rows, filename="report.csv"):
    """Return a CSV download response if format=csv was requested."""
    import csv
    import io
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    frappe.response["filecontent"] = output.getvalue()
    frappe.response["filename"] = filename
    frappe.response["type"] = "download"


# ────────────────────────────────────────────────────────────────
# 11.  SALES PERFORMANCE REPORT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_sales_performance_report(company=None, from_date=None, to_date=None,
                                  customer=None, item_code=None, item_group=None,
                                  brand=None, sales_person=None, group_by='month',
                                  sort_by='net_sales', sort_order='desc',
                                  page=1, page_size=20, format=None):
    """Sales performance — groupable by month, customer, item, item_group, brand, sales_person."""
    company = resolve_active_company(company)
    from_date, to_date = _date_range(from_date, to_date)
    page, page_size, offset = _paginate(page, page_size)

    allowed_groups = {
        'month': "DATE_FORMAT(si.posting_date, '%%Y-%%m')",
        'customer': 'si.customer',
        'item': 'sii.item_code',
        'item_group': 'sii.item_group',
        'brand': 'i.brand',
        'sales_person': "COALESCE(st.sales_person, 'Unassigned')",
    }
    group_expr = allowed_groups.get(group_by, allowed_groups['month'])
    dim_alias = 'dimension'

    conditions = [
        "si.company = %(company)s",
        "si.docstatus = 1",
        "si.posting_date BETWEEN %(from_date)s AND %(to_date)s",
    ]
    params = {"company": company, "from_date": from_date, "to_date": to_date}

    if customer:
        conditions.append("si.customer = %(customer)s")
        params["customer"] = customer
    if item_code:
        conditions.append("sii.item_code = %(item_code)s")
        params["item_code"] = item_code
    if item_group:
        conditions.append("sii.item_group = %(item_group)s")
        params["item_group"] = item_group
    if brand:
        conditions.append("i.brand = %(brand)s")
        params["brand"] = brand

    where = " AND ".join(conditions)

    joins = """
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        LEFT JOIN `tabItem` i ON i.name = sii.item_code
    """
    if group_by == 'sales_person' or sales_person:
        joins += " LEFT JOIN `tabSales Team` st ON st.parent = si.name AND st.parenttype = 'Sales Invoice'"
        if sales_person:
            conditions.append("st.sales_person = %(sales_person)s")
            params["sales_person"] = sales_person
            where = " AND ".join(conditions)

    # Summary
    summary = frappe.db.sql(f"""
        SELECT
            COALESCE(SUM(sii.amount), 0) AS net_sales,
            COALESCE(SUM(sii.qty * sii.rate), 0) AS gross_sales,
            COALESCE(SUM(sii.qty * sii.rate) - SUM(sii.amount), 0) AS discount_amount,
            COALESCE(SUM(sii.qty * COALESCE(sii.incoming_rate, 0)), 0) AS cogs,
            COALESCE(SUM(sii.amount) - SUM(sii.qty * COALESCE(sii.incoming_rate, 0)), 0) AS gross_profit,
            COALESCE(SUM(sii.qty), 0) AS qty,
            COUNT(DISTINCT si.name) AS invoice_count
        {joins}
        WHERE {where}
    """, params, as_dict=True)[0]
    summary['gross_margin_pct'] = _safe_pct(summary['gross_profit'], summary['net_sales'])

    # Chart data (always by month)
    chart = frappe.db.sql(f"""
        SELECT DATE_FORMAT(si.posting_date, '%%Y-%%m') AS period,
               COALESCE(SUM(sii.amount), 0) AS net_sales,
               COALESCE(SUM(sii.amount) - SUM(sii.qty * COALESCE(sii.incoming_rate, 0)), 0) AS gross_profit
        {joins}
        WHERE {where}
        GROUP BY DATE_FORMAT(si.posting_date, '%%Y-%%m')
        ORDER BY DATE_FORMAT(si.posting_date, '%%Y-%%m')
    """, params, as_dict=True)

    allowed_sort = ['net_sales', 'gross_profit', 'qty', 'invoice_count']
    order_col = sort_by if sort_by in allowed_sort else 'net_sales'
    order_dir = 'ASC' if sort_order == 'asc' else 'DESC'

    total = frappe.db.sql(f"""
        SELECT COUNT(*) FROM (
            SELECT {group_expr} AS dim
            {joins}
            WHERE {where}
            GROUP BY {group_expr}
        ) sub
    """, params)[0][0]

    rows = frappe.db.sql(f"""
        SELECT {group_expr} AS dimension,
               COALESCE(SUM(sii.qty), 0) AS qty,
               COALESCE(SUM(sii.amount), 0) AS net_sales,
               COALESCE(SUM(sii.qty * sii.rate), 0) AS gross_sales,
               COALESCE(SUM(sii.qty * sii.rate) - SUM(sii.amount), 0) AS discount_amount,
               COALESCE(SUM(sii.qty * COALESCE(sii.incoming_rate, 0)), 0) AS cogs,
               COALESCE(SUM(sii.amount) - SUM(sii.qty * COALESCE(sii.incoming_rate, 0)), 0) AS gross_profit,
               COUNT(DISTINCT si.name) AS invoice_count
        {joins}
        WHERE {where}
        GROUP BY {group_expr}
        ORDER BY {order_col} {order_dir}
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    for row in rows:
        row['gross_margin_pct'] = _safe_pct(row['gross_profit'], row['net_sales'])
        row['avg_selling_price'] = round(flt(row['net_sales']) / flt(row['qty']), 2) if flt(row['qty']) else 0

    if format == 'csv':
        cols = ['dimension', 'qty', 'net_sales', 'gross_sales', 'discount_amount', 'cogs', 'gross_profit', 'gross_margin_pct', 'invoice_count', 'avg_selling_price']
        _csv_response(cols, rows, 'sales_performance.csv')
        return

    return {"summary": summary, "chart": chart, "data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ────────────────────────────────────────────────────────────────
# 12.  CUSTOMER PROFITABILITY REPORT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_customer_profitability_report(company=None, from_date=None, to_date=None,
                                       customer_group=None, territory=None,
                                       page=1, page_size=20, format=None):
    """Customer profitability — revenue, GP, margins, outstanding, payment days."""
    company = resolve_active_company(company)
    from_date, to_date = _date_range(from_date, to_date)
    page, page_size, offset = _paginate(page, page_size)

    conditions = [
        "si.company = %(company)s",
        "si.docstatus = 1",
        "si.posting_date BETWEEN %(from_date)s AND %(to_date)s",
    ]
    params = {"company": company, "from_date": from_date, "to_date": to_date}

    if customer_group:
        conditions.append("c.customer_group = %(customer_group)s")
        params["customer_group"] = customer_group
    if territory:
        conditions.append("c.territory = %(territory)s")
        params["territory"] = territory

    where = " AND ".join(conditions)

    total = frappe.db.sql(f"""
        SELECT COUNT(DISTINCT si.customer)
        FROM `tabSales Invoice` si
        LEFT JOIN `tabCustomer` c ON c.name = si.customer
        WHERE {where}
    """, params)[0][0]

    rows = frappe.db.sql(f"""
        SELECT si.customer,
               MAX(si.customer_name) AS customer_name,
               COALESCE(SUM(sii.amount), 0) AS revenue,
               COALESCE(SUM(sii.amount) - SUM(sii.qty * COALESCE(sii.incoming_rate, 0)), 0) AS gross_profit,
               COALESCE(SUM(sii.qty * COALESCE(sii.incoming_rate, 0)), 0) AS cogs,
               COUNT(DISTINCT si.name) AS invoice_count,
               COALESCE(SUM(si.outstanding_amount), 0) AS outstanding_amount
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        LEFT JOIN `tabCustomer` c ON c.name = si.customer
        WHERE {where}
        GROUP BY si.customer
        ORDER BY revenue DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    for row in rows:
        row['gross_margin_pct'] = _safe_pct(row['gross_profit'], row['revenue'])
        row['credit_utilization_pct'] = None

    if format == 'csv':
        cols = ['customer', 'customer_name', 'revenue', 'gross_profit', 'gross_margin_pct', 'outstanding_amount', 'invoice_count']
        _csv_response(cols, rows, 'customer_profitability.csv')
        return

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ────────────────────────────────────────────────────────────────
# 13.  STOCK AGING REPORT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_stock_aging_report(company=None, warehouse=None, item_group=None,
                           brand=None, page=1, page_size=20, format=None):
    """Stock aging — bucket by days since last inward transaction."""
    company = resolve_active_company(company)
    page, page_size, offset = _paginate(page, page_size)

    conditions = ["w.company = %(company)s", "b.actual_qty > 0"]
    params = {"company": company}

    if warehouse:
        conditions.append("b.warehouse = %(warehouse)s")
        params["warehouse"] = warehouse
    if item_group:
        conditions.append("i.item_group = %(item_group)s")
        params["item_group"] = item_group
    if brand:
        conditions.append("i.brand = %(brand)s")
        params["brand"] = brand

    where = " AND ".join(conditions)

    total = frappe.db.sql(f"""
        SELECT COUNT(DISTINCT b.item_code)
        FROM `tabBin` b
        INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
        INNER JOIN `tabItem` i ON i.name = b.item_code
        WHERE {where}
    """, params)[0][0]

    summary = frappe.db.sql(f"""
        SELECT COALESCE(SUM(b.stock_value), 0) AS total_value,
               COALESCE(SUM(b.actual_qty), 0) AS total_qty,
               COUNT(DISTINCT b.item_code) AS item_count
        FROM `tabBin` b
        INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
        INNER JOIN `tabItem` i ON i.name = b.item_code
        WHERE {where}
    """, params, as_dict=True)[0]

    rows = frappe.db.sql(f"""
        SELECT b.item_code, i.item_name, i.item_group, i.brand,
               b.warehouse,
               b.actual_qty AS current_qty,
               b.valuation_rate,
               b.stock_value,
               sle.last_inward_date,
               sle.last_sale_date,
               DATEDIFF(CURDATE(), COALESCE(sle.last_inward_date, '2000-01-01')) AS age_days
        FROM `tabBin` b
        INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
        INNER JOIN `tabItem` i ON i.name = b.item_code
        LEFT JOIN (
            SELECT item_code, warehouse,
                   MAX(CASE WHEN actual_qty > 0 THEN posting_date END) AS last_inward_date,
                   MAX(CASE WHEN actual_qty < 0 THEN posting_date END) AS last_sale_date
            FROM `tabStock Ledger Entry`
            WHERE is_cancelled = 0
            GROUP BY item_code, warehouse
        ) sle ON sle.item_code = b.item_code AND sle.warehouse = b.warehouse
        WHERE {where}
        ORDER BY age_days DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    for row in rows:
        age = cint(row.get('age_days', 0))
        if age <= 30: row['bucket'] = '0-30'
        elif age <= 60: row['bucket'] = '31-60'
        elif age <= 90: row['bucket'] = '61-90'
        elif age <= 180: row['bucket'] = '91-180'
        else: row['bucket'] = '180+'

    if format == 'csv':
        cols = ['item_code', 'item_name', 'item_group', 'warehouse', 'current_qty', 'valuation_rate', 'stock_value', 'age_days', 'bucket']
        _csv_response(cols, rows, 'stock_aging.csv')
        return

    # Bucket summary for chart
    bucket_summary = {'0-30': 0, '31-60': 0, '61-90': 0, '91-180': 0, '180+': 0}
    for row in rows:
        bucket_summary[row['bucket']] = bucket_summary.get(row['bucket'], 0) + flt(row['stock_value'])

    chart = [{'bucket': k, 'stock_value': v} for k, v in bucket_summary.items()]

    return {"summary": summary, "chart": chart, "data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ────────────────────────────────────────────────────────────────
# 14.  INVENTORY MOVEMENT REPORT (Fast/Slow/Non-Moving)
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_inventory_movement_report(company=None, warehouse=None, item_group=None,
                                   brand=None, page=1, page_size=20, format=None):
    """Classify inventory as fast, slow, or non-moving based on sales velocity."""
    company = resolve_active_company(company)
    page, page_size, offset = _paginate(page, page_size)
    today = nowdate()
    d30 = add_months(today, -1)
    d90 = add_months(today, -3)

    conditions = ["w.company = %(company)s", "b.actual_qty > 0"]
    params = {"company": company, "d30": d30, "d90": d90}

    if warehouse:
        conditions.append("b.warehouse = %(warehouse)s")
        params["warehouse"] = warehouse
    if item_group:
        conditions.append("i.item_group = %(item_group)s")
        params["item_group"] = item_group
    if brand:
        conditions.append("i.brand = %(brand)s")
        params["brand"] = brand

    where = " AND ".join(conditions)

    total = frappe.db.sql(f"""
        SELECT COUNT(DISTINCT b.item_code)
        FROM `tabBin` b
        INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
        INNER JOIN `tabItem` i ON i.name = b.item_code
        WHERE {where}
    """, params)[0][0]

    rows = frappe.db.sql(f"""
        SELECT b.item_code, i.item_name, i.item_group, i.brand,
               SUM(b.actual_qty) AS stock_qty,
               SUM(b.stock_value) AS stock_value,
               s30.sold_qty_30d,
               s90.sold_qty_90d,
               last_sale.last_sale_date,
               DATEDIFF(CURDATE(), last_sale.last_sale_date) AS days_since_last_sale
        FROM `tabBin` b
        INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
        INNER JOIN `tabItem` i ON i.name = b.item_code
        LEFT JOIN (
            SELECT sii.item_code, COALESCE(SUM(sii.qty), 0) AS sold_qty_30d
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE si.docstatus = 1 AND si.company = %(company)s AND si.posting_date >= %(d30)s
            GROUP BY sii.item_code
        ) s30 ON s30.item_code = b.item_code
        LEFT JOIN (
            SELECT sii.item_code, COALESCE(SUM(sii.qty), 0) AS sold_qty_90d
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE si.docstatus = 1 AND si.company = %(company)s AND si.posting_date >= %(d90)s
            GROUP BY sii.item_code
        ) s90 ON s90.item_code = b.item_code
        LEFT JOIN (
            SELECT sii.item_code, MAX(si.posting_date) AS last_sale_date
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE si.docstatus = 1 AND si.company = %(company)s
            GROUP BY sii.item_code
        ) last_sale ON last_sale.item_code = b.item_code
        WHERE {where}
        GROUP BY b.item_code
        ORDER BY stock_value DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    for row in rows:
        s30 = flt(row.get('sold_qty_30d'))
        s90 = flt(row.get('sold_qty_90d'))
        days = cint(row.get('days_since_last_sale'))
        if s30 > 0:
            row['movement_class'] = 'fast'
        elif s90 > 0:
            row['movement_class'] = 'slow'
        else:
            row['movement_class'] = 'non_moving'

    class_counts = {'fast': 0, 'slow': 0, 'non_moving': 0}
    class_values = {'fast': 0, 'slow': 0, 'non_moving': 0}
    for row in rows:
        mc = row['movement_class']
        class_counts[mc] += 1
        class_values[mc] += flt(row['stock_value'])

    summary = {
        'total_items': cint(total),
        'fast_count': class_counts['fast'],
        'slow_count': class_counts['slow'],
        'non_moving_count': class_counts['non_moving'],
        'fast_value': class_values['fast'],
        'slow_value': class_values['slow'],
        'non_moving_value': class_values['non_moving'],
    }

    chart = [
        {'label': 'Fast Moving', 'count': class_counts['fast'], 'value': class_values['fast']},
        {'label': 'Slow Moving', 'count': class_counts['slow'], 'value': class_values['slow']},
        {'label': 'Non-Moving', 'count': class_counts['non_moving'], 'value': class_values['non_moving']},
    ]

    if format == 'csv':
        cols = ['item_code', 'item_name', 'item_group', 'stock_qty', 'stock_value', 'sold_qty_30d', 'sold_qty_90d', 'days_since_last_sale', 'movement_class']
        _csv_response(cols, rows, 'inventory_movement.csv')
        return

    return {"summary": summary, "chart": chart, "data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ────────────────────────────────────────────────────────────────
# 15.  REORDER REPORT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_reorder_report(company=None, warehouse=None, item_group=None,
                       page=1, page_size=20, format=None):
    """Items with stock cover analysis and reorder recommendations."""
    company = resolve_active_company(company)
    page, page_size, offset = _paginate(page, page_size)
    d30 = add_months(nowdate(), -1)

    conditions = ["w.company = %(company)s", "b.actual_qty > 0"]
    params = {"company": company, "d30": d30}

    if warehouse:
        conditions.append("b.warehouse = %(warehouse)s")
        params["warehouse"] = warehouse
    if item_group:
        conditions.append("i.item_group = %(item_group)s")
        params["item_group"] = item_group

    where = " AND ".join(conditions)

    total = frappe.db.sql(f"""
        SELECT COUNT(DISTINCT b.item_code)
        FROM `tabBin` b
        INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
        INNER JOIN `tabItem` i ON i.name = b.item_code
        WHERE {where}
    """, params)[0][0]

    rows = frappe.db.sql(f"""
        SELECT b.item_code, i.item_name, i.item_group,
               SUM(b.actual_qty) AS current_stock,
               SUM(b.reserved_qty) AS reserved_stock,
               SUM(b.actual_qty) - SUM(COALESCE(b.reserved_qty, 0)) AS available_stock,
               s30.sold_qty_30d,
               ir.warehouse_reorder_level AS reorder_level,
               ir.warehouse_reorder_qty AS reorder_qty,
               i.lead_time_days,
               d.default_supplier AS preferred_supplier
        FROM `tabBin` b
        INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
        INNER JOIN `tabItem` i ON i.name = b.item_code
        LEFT JOIN `tabItem Reorder` ir ON ir.parent = i.name AND ir.warehouse = b.warehouse
        LEFT JOIN `tabItem Default` d ON d.parent = i.name AND d.company = %(company)s
        LEFT JOIN (
            SELECT sii.item_code, COALESCE(SUM(sii.qty), 0) AS sold_qty_30d
            FROM `tabSales Invoice Item` sii
            INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
            WHERE si.docstatus = 1 AND si.company = %(company)s AND si.posting_date >= %(d30)s
            GROUP BY sii.item_code
        ) s30 ON s30.item_code = b.item_code
        WHERE {where}
        GROUP BY b.item_code
        ORDER BY available_stock ASC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    for row in rows:
        avg_daily = flt(row.get('sold_qty_30d', 0)) / 30
        row['avg_daily_sales'] = round(avg_daily, 2)
        avail = flt(row.get('available_stock', 0))
        row['days_of_cover'] = round(avail / avg_daily, 1) if avg_daily else 9999
        rl = flt(row.get('reorder_level', 0))
        lt = cint(row.get('lead_time_days', 0))
        lt_demand = avg_daily * lt
        row['suggested_reorder'] = max(round(rl + lt_demand - avail, 0), 0) if rl else None
        if avail <= 0:
            row['stock_status'] = 'stockout'
        elif row['days_of_cover'] < 7:
            row['stock_status'] = 'critical'
        elif row['days_of_cover'] < 14:
            row['stock_status'] = 'low'
        else:
            row['stock_status'] = 'healthy'

    summary = {
        'total_items': cint(total),
        'stockout': sum(1 for r in rows if r['stock_status'] == 'stockout'),
        'critical': sum(1 for r in rows if r['stock_status'] == 'critical'),
        'low': sum(1 for r in rows if r['stock_status'] == 'low'),
        'healthy': sum(1 for r in rows if r['stock_status'] == 'healthy'),
    }

    if format == 'csv':
        cols = ['item_code', 'item_name', 'current_stock', 'available_stock', 'avg_daily_sales', 'days_of_cover', 'reorder_level', 'suggested_reorder', 'preferred_supplier', 'stock_status']
        _csv_response(cols, rows, 'reorder_report.csv')
        return

    return {"summary": summary, "data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ────────────────────────────────────────────────────────────────
# 16.  SUPPLIER SCORECARD REPORT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_supplier_scorecard_report(company=None, from_date=None, to_date=None,
                                   supplier=None, page=1, page_size=20, format=None):
    """Supplier scorecard — cost, delivery, and quality metrics."""
    company = resolve_active_company(company)
    from_date, to_date = _date_range(from_date, to_date)
    page, page_size, offset = _paginate(page, page_size)

    conditions = [
        "pi.company = %(company)s",
        "pi.docstatus = 1",
        "pi.posting_date BETWEEN %(from_date)s AND %(to_date)s",
    ]
    params = {"company": company, "from_date": from_date, "to_date": to_date}

    if supplier:
        conditions.append("pi.supplier = %(supplier)s")
        params["supplier"] = supplier

    where = " AND ".join(conditions)

    total = frappe.db.sql(f"""
        SELECT COUNT(DISTINCT pi.supplier)
        FROM `tabPurchase Invoice` pi
        WHERE {where}
    """, params)[0][0]

    rows = frappe.db.sql(f"""
        SELECT pi.supplier, pi.supplier_name,
               COALESCE(SUM(pii.amount), 0) AS purchase_value,
               COALESCE(SUM(pii.qty), 0) AS total_qty,
               COUNT(DISTINCT pi.name) AS invoice_count,
               COALESCE(SUM(pi.outstanding_amount), 0) AS payable_outstanding
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        WHERE {where}
        GROUP BY pi.supplier
        ORDER BY purchase_value DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    for row in rows:
        row['avg_rate'] = round(flt(row['purchase_value']) / flt(row['total_qty']), 2) if flt(row['total_qty']) else 0

    if format == 'csv':
        cols = ['supplier', 'supplier_name', 'purchase_value', 'total_qty', 'avg_rate', 'invoice_count', 'payable_outstanding']
        _csv_response(cols, rows, 'supplier_scorecard.csv')
        return

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ────────────────────────────────────────────────────────────────
# 17.  PURCHASE PRICE VARIANCE REPORT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_purchase_price_variance_report(company=None, from_date=None, to_date=None,
                                        supplier=None, item_code=None, item_group=None,
                                        page=1, page_size=20, format=None):
    """Purchase price variance — detect cost drift per item/supplier."""
    company = resolve_active_company(company)
    from_date, to_date = _date_range(from_date, to_date)
    page, page_size, offset = _paginate(page, page_size)

    conditions = [
        "pi.company = %(company)s",
        "pi.docstatus = 1",
        "pi.posting_date BETWEEN %(from_date)s AND %(to_date)s",
    ]
    params = {"company": company, "from_date": from_date, "to_date": to_date}

    if supplier:
        conditions.append("pi.supplier = %(supplier)s")
        params["supplier"] = supplier
    if item_code:
        conditions.append("pii.item_code = %(item_code)s")
        params["item_code"] = item_code
    if item_group:
        conditions.append("i.item_group = %(item_group)s")
        params["item_group"] = item_group

    where = " AND ".join(conditions)

    total = frappe.db.sql(f"""
        SELECT COUNT(DISTINCT CONCAT(pii.item_code, '||', pi.supplier))
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        LEFT JOIN `tabItem` i ON i.name = pii.item_code
        WHERE {where}
    """, params)[0][0]

    rows = frappe.db.sql(f"""
        SELECT pii.item_code, pii.item_name, i.item_group,
               pi.supplier, pi.supplier_name,
               COALESCE(SUM(pii.qty), 0) AS qty,
               COALESCE(SUM(pii.amount), 0) AS purchase_value,
               ROUND(SUM(pii.amount) / NULLIF(SUM(pii.qty), 0), 2) AS avg_rate,
               MIN(pii.rate) AS min_rate,
               MAX(pii.rate) AS max_rate
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        LEFT JOIN `tabItem` i ON i.name = pii.item_code
        WHERE {where}
        GROUP BY pii.item_code, pi.supplier
        ORDER BY purchase_value DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    for row in rows:
        min_r = flt(row.get('min_rate'))
        max_r = flt(row.get('max_rate'))
        row['price_spread'] = round(max_r - min_r, 2)
        row['variance_pct'] = _safe_pct(max_r - min_r, min_r) if min_r else 0

    if format == 'csv':
        cols = ['item_code', 'item_name', 'supplier', 'qty', 'purchase_value', 'avg_rate', 'min_rate', 'max_rate', 'price_spread', 'variance_pct']
        _csv_response(cols, rows, 'purchase_price_variance.csv')
        return

    return {"data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ────────────────────────────────────────────────────────────────
# 18.  RECEIVABLE AGING — INVOICE DETAIL
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_receivable_aging_invoice_detail(company=None, customer=None,
                                         bucket=None, page=1, page_size=20, format=None):
    """Invoice-level receivable aging detail."""
    company = resolve_active_company(company)
    page, page_size, offset = _paginate(page, page_size)
    today = nowdate()

    conditions = [
        "si.company = %(company)s",
        "si.docstatus = 1",
        "si.outstanding_amount > 0",
    ]
    params = {"company": company, "today": today}

    if customer:
        conditions.append("si.customer = %(customer)s")
        params["customer"] = customer

    where = " AND ".join(conditions)

    total = frappe.db.sql(f"""
        SELECT COUNT(*) FROM `tabSales Invoice` si WHERE {where}
    """, params)[0][0]

    rows = frappe.db.sql(f"""
        SELECT si.name AS invoice_no, si.customer, si.customer_name,
               si.posting_date, si.due_date,
               si.grand_total, si.outstanding_amount,
               DATEDIFF(%(today)s, si.due_date) AS age_days
        FROM `tabSales Invoice` si
        WHERE {where}
        ORDER BY age_days DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    for row in rows:
        age = cint(row.get('age_days', 0))
        if age <= 30: row['bucket'] = '0-30'
        elif age <= 60: row['bucket'] = '31-60'
        elif age <= 90: row['bucket'] = '61-90'
        else: row['bucket'] = '90+'

    if bucket:
        rows = [r for r in rows if r.get('bucket') == bucket]

    summary = frappe.db.sql(f"""
        SELECT
            SUM(CASE WHEN DATEDIFF(%(today)s, si.due_date) <= 30 THEN si.outstanding_amount ELSE 0 END) AS `0-30`,
            SUM(CASE WHEN DATEDIFF(%(today)s, si.due_date) BETWEEN 31 AND 60 THEN si.outstanding_amount ELSE 0 END) AS `31-60`,
            SUM(CASE WHEN DATEDIFF(%(today)s, si.due_date) BETWEEN 61 AND 90 THEN si.outstanding_amount ELSE 0 END) AS `61-90`,
            SUM(CASE WHEN DATEDIFF(%(today)s, si.due_date) > 90 THEN si.outstanding_amount ELSE 0 END) AS `90+`,
            SUM(si.outstanding_amount) AS total_outstanding,
            COUNT(*) AS invoice_count
        FROM `tabSales Invoice` si
        WHERE {where}
    """, params, as_dict=True)[0]

    if format == 'csv':
        cols = ['invoice_no', 'customer', 'customer_name', 'posting_date', 'due_date', 'grand_total', 'outstanding_amount', 'age_days', 'bucket']
        _csv_response(cols, rows, 'receivable_aging_detail.csv')
        return

    return {"summary": summary, "data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ────────────────────────────────────────────────────────────────
# 19.  PAYABLE AGING — INVOICE DETAIL
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_payable_aging_invoice_detail(company=None, supplier=None,
                                      bucket=None, page=1, page_size=20, format=None):
    """Invoice-level payable aging detail."""
    company = resolve_active_company(company)
    page, page_size, offset = _paginate(page, page_size)
    today = nowdate()

    conditions = [
        "pi.company = %(company)s",
        "pi.docstatus = 1",
        "pi.outstanding_amount > 0",
    ]
    params = {"company": company, "today": today}

    if supplier:
        conditions.append("pi.supplier = %(supplier)s")
        params["supplier"] = supplier

    where = " AND ".join(conditions)

    total = frappe.db.sql(f"""
        SELECT COUNT(*) FROM `tabPurchase Invoice` pi WHERE {where}
    """, params)[0][0]

    rows = frappe.db.sql(f"""
        SELECT pi.name AS bill_no, pi.supplier, pi.supplier_name,
               pi.posting_date, pi.due_date,
               pi.grand_total, pi.outstanding_amount,
               DATEDIFF(%(today)s, pi.due_date) AS age_days
        FROM `tabPurchase Invoice` pi
        WHERE {where}
        ORDER BY age_days DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    for row in rows:
        age = cint(row.get('age_days', 0))
        if age <= 30: row['bucket'] = '0-30'
        elif age <= 60: row['bucket'] = '31-60'
        elif age <= 90: row['bucket'] = '61-90'
        else: row['bucket'] = '90+'

    if bucket:
        rows = [r for r in rows if r.get('bucket') == bucket]

    summary = frappe.db.sql(f"""
        SELECT
            SUM(CASE WHEN DATEDIFF(%(today)s, pi.due_date) <= 30 THEN pi.outstanding_amount ELSE 0 END) AS `0-30`,
            SUM(CASE WHEN DATEDIFF(%(today)s, pi.due_date) BETWEEN 31 AND 60 THEN pi.outstanding_amount ELSE 0 END) AS `31-60`,
            SUM(CASE WHEN DATEDIFF(%(today)s, pi.due_date) BETWEEN 61 AND 90 THEN pi.outstanding_amount ELSE 0 END) AS `61-90`,
            SUM(CASE WHEN DATEDIFF(%(today)s, pi.due_date) > 90 THEN pi.outstanding_amount ELSE 0 END) AS `90+`,
            SUM(pi.outstanding_amount) AS total_outstanding,
            COUNT(*) AS invoice_count
        FROM `tabPurchase Invoice` pi
        WHERE {where}
    """, params, as_dict=True)[0]

    if format == 'csv':
        cols = ['bill_no', 'supplier', 'supplier_name', 'posting_date', 'due_date', 'grand_total', 'outstanding_amount', 'age_days', 'bucket']
        _csv_response(cols, rows, 'payable_aging_detail.csv')
        return

    return {"summary": summary, "data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ────────────────────────────────────────────────────────────────
# 20.  TAX SUMMARY REPORT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_tax_summary_report(company=None, from_date=None, to_date=None, format=None):
    """Tax summary — output tax (sales) vs input tax (purchases)."""
    company = resolve_active_company(company)
    from_date, to_date = _date_range(from_date, to_date)
    params = {"company": company, "from_date": from_date, "to_date": to_date}

    output_tax = frappe.db.sql("""
        SELECT stc.account_head AS tax_account,
               stc.description AS tax_template,
               COALESCE(SUM(stc.tax_amount), 0) AS tax_amount,
               COALESCE(SUM(stc.base_total), 0) AS taxable_amount,
               COUNT(DISTINCT si.name) AS invoice_count
        FROM `tabSales Taxes and Charges` stc
        INNER JOIN `tabSales Invoice` si ON si.name = stc.parent
        WHERE si.company = %(company)s AND si.docstatus = 1
              AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY stc.account_head, stc.description
    """, params, as_dict=True)

    input_tax = frappe.db.sql("""
        SELECT ptc.account_head AS tax_account,
               ptc.description AS tax_template,
               COALESCE(SUM(ptc.tax_amount), 0) AS tax_amount,
               COALESCE(SUM(ptc.base_total), 0) AS taxable_amount,
               COUNT(DISTINCT pi.name) AS invoice_count
        FROM `tabPurchase Taxes and Charges` ptc
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = ptc.parent
        WHERE pi.company = %(company)s AND pi.docstatus = 1
              AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY ptc.account_head, ptc.description
    """, params, as_dict=True)

    total_output = sum(flt(r['tax_amount']) for r in output_tax)
    total_input = sum(flt(r['tax_amount']) for r in input_tax)

    summary = {
        'output_tax': total_output,
        'input_tax': total_input,
        'net_tax_payable': total_output - total_input,
        'from_date': from_date,
        'to_date': to_date,
    }

    if format == 'csv':
        all_rows = [{'type': 'Output', **r} for r in output_tax] + [{'type': 'Input', **r} for r in input_tax]
        cols = ['type', 'tax_account', 'tax_template', 'taxable_amount', 'tax_amount', 'invoice_count']
        _csv_response(cols, all_rows, 'tax_summary.csv')
        return

    return {"summary": summary, "output_tax": output_tax, "input_tax": input_tax}


# ────────────────────────────────────────────────────────────────
# 21.  OPEN PURCHASE ORDERS REPORT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_open_purchase_orders_report(company=None, supplier=None, warehouse=None,
                                     page=1, page_size=20, format=None):
    """Open purchase order items — pending receipt."""
    company = resolve_active_company(company)
    page, page_size, offset = _paginate(page, page_size)

    conditions = [
        "po.company = %(company)s",
        "po.docstatus = 1",
        "po.status NOT IN ('Completed', 'Closed', 'Cancelled')",
        "poi.received_qty < poi.qty",
    ]
    params = {"company": company}

    if supplier:
        conditions.append("po.supplier = %(supplier)s")
        params["supplier"] = supplier
    if warehouse:
        conditions.append("poi.warehouse = %(warehouse)s")
        params["warehouse"] = warehouse

    where = " AND ".join(conditions)

    total = frappe.db.sql(f"""
        SELECT COUNT(*)
        FROM `tabPurchase Order Item` poi
        INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
        WHERE {where}
    """, params)[0][0]

    rows = frappe.db.sql(f"""
        SELECT po.name AS po_no, po.supplier, po.supplier_name,
               po.transaction_date, poi.item_code, poi.item_name,
               poi.qty AS ordered_qty, poi.received_qty,
               (poi.qty - poi.received_qty) AS pending_qty,
               poi.rate,
               (poi.qty - poi.received_qty) * poi.rate AS pending_value,
               poi.schedule_date,
               DATEDIFF(CURDATE(), poi.schedule_date) AS delay_days
        FROM `tabPurchase Order Item` poi
        INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
        WHERE {where}
        ORDER BY delay_days DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    summary = frappe.db.sql(f"""
        SELECT COUNT(DISTINCT po.name) AS order_count,
               COALESCE(SUM((poi.qty - poi.received_qty) * poi.rate), 0) AS total_pending_value,
               COALESCE(SUM(CASE WHEN DATEDIFF(CURDATE(), poi.schedule_date) > 0
                            THEN (poi.qty - poi.received_qty) * poi.rate ELSE 0 END), 0) AS delayed_value
        FROM `tabPurchase Order Item` poi
        INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
        WHERE {where}
    """, params, as_dict=True)[0]

    if format == 'csv':
        cols = ['po_no', 'supplier', 'item_code', 'item_name', 'ordered_qty', 'received_qty', 'pending_qty', 'rate', 'pending_value', 'schedule_date', 'delay_days']
        _csv_response(cols, rows, 'open_purchase_orders.csv')
        return

    return {"summary": summary, "data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ────────────────────────────────────────────────────────────────
# 22.  COLLECTION EFFICIENCY REPORT
# ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_collection_efficiency_report(company=None, from_date=None, to_date=None,
                                      group_by='month', page=1, page_size=20, format=None):
    """Collection efficiency — billed vs collected by period or customer."""
    company = resolve_active_company(company)
    from_date, to_date = _date_range(from_date, to_date)
    page, page_size, offset = _paginate(page, page_size)

    params = {"company": company, "from_date": from_date, "to_date": to_date}

    if group_by == 'customer':
        dim_expr = 'si.customer'
    else:
        dim_expr = "DATE_FORMAT(si.posting_date, '%%Y-%%m')"

    rows = frappe.db.sql(f"""
        SELECT {dim_expr} AS dimension,
               COALESCE(SUM(si.grand_total), 0) AS billed_amount,
               COALESCE(SUM(si.grand_total - si.outstanding_amount), 0) AS collected_amount,
               COALESCE(SUM(si.outstanding_amount), 0) AS outstanding_amount,
               COUNT(DISTINCT si.name) AS invoice_count
        FROM `tabSales Invoice` si
        WHERE si.company = %(company)s AND si.docstatus = 1
              AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY dimension
        ORDER BY billed_amount DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    for row in rows:
        row['efficiency_pct'] = _safe_pct(row['collected_amount'], row['billed_amount'])

    total_billed = sum(flt(r['billed_amount']) for r in rows)
    total_collected = sum(flt(r['collected_amount']) for r in rows)
    summary = {
        'total_billed': total_billed,
        'total_collected': total_collected,
        'total_outstanding': total_billed - total_collected,
        'overall_efficiency_pct': _safe_pct(total_collected, total_billed),
    }

    if format == 'csv':
        cols = ['dimension', 'billed_amount', 'collected_amount', 'outstanding_amount', 'efficiency_pct', 'invoice_count']
        _csv_response(cols, rows, 'collection_efficiency.csv')
        return

    return {"summary": summary, "data": rows, "total": len(rows), "page": page, "page_size": page_size}


# ────────────────────────────────────────────────────────────────
# Phase 2 Endpoints
# ────────────────────────────────────────────────────────────────

# ── 24. DAILY SALES REPORT ─────────────────────────────────────
@frappe.whitelist()
def get_daily_sales_report(company=None, from_date=None, to_date=None,
                           page=1, page_size=50, format=None):
    """Daily sales breakdown — invoice count, revenue, outstanding per day."""
    company = resolve_active_company(company)
    from_date, to_date = _date_range(from_date, to_date, default_months=1)
    page, page_size, offset = _paginate(page, page_size)

    params = {"company": company, "from_date": from_date, "to_date": to_date}

    rows = frappe.db.sql("""
        SELECT si.posting_date AS date,
               COUNT(*) AS invoice_count,
               COALESCE(SUM(si.net_total), 0) AS net_total,
               COALESCE(SUM(si.grand_total), 0) AS grand_total,
               COALESCE(SUM(si.outstanding_amount), 0) AS outstanding,
               COALESCE(SUM(si.grand_total - si.outstanding_amount), 0) AS collected
        FROM `tabSales Invoice` si
        WHERE si.company = %(company)s AND si.docstatus = 1
              AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY si.posting_date
        ORDER BY si.posting_date DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    total_row = frappe.db.sql("""
        SELECT COUNT(DISTINCT si.posting_date) AS total_days,
               COALESCE(SUM(si.grand_total), 0) AS total_revenue,
               COALESCE(SUM(si.outstanding_amount), 0) AS total_outstanding,
               COUNT(*) AS total_invoices,
               COALESCE(AVG(si.grand_total), 0) AS avg_invoice_value
        FROM `tabSales Invoice` si
        WHERE si.company = %(company)s AND si.docstatus = 1
              AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
    """, params, as_dict=True)[0]

    summary = {
        'total_days': cint(total_row.get('total_days')),
        'total_revenue': flt(total_row.get('total_revenue')),
        'total_invoices': cint(total_row.get('total_invoices')),
        'avg_daily_revenue': flt(total_row.get('total_revenue')) / max(cint(total_row.get('total_days')), 1),
        'avg_invoice_value': flt(total_row.get('avg_invoice_value')),
    }

    chart = [{"label": str(r['date']), "revenue": flt(r['grand_total']), "invoices": cint(r['invoice_count'])} for r in reversed(rows)]

    if format == 'csv':
        cols = ['date', 'invoice_count', 'net_total', 'grand_total', 'outstanding', 'collected']
        _csv_response(cols, rows, 'daily_sales.csv')
        return

    return {"summary": summary, "data": rows, "chart": chart, "total": summary['total_days'], "page": page, "page_size": page_size}


# ── 25. SALES RETURN REPORT ───────────────────────────────────
@frappe.whitelist()
def get_sales_return_report(company=None, from_date=None, to_date=None,
                            customer=None, page=1, page_size=50, format=None):
    """Sales returns (credit notes) — grouped by customer."""
    company = resolve_active_company(company)
    from_date, to_date = _date_range(from_date, to_date)
    page, page_size, offset = _paginate(page, page_size)

    params = {"company": company, "from_date": from_date, "to_date": to_date}
    extra = ""
    if customer:
        extra = " AND si.customer = %(customer)s"
        params["customer"] = customer

    rows = frappe.db.sql(f"""
        SELECT si.customer, si.customer_name,
               COUNT(*) AS return_count,
               COALESCE(SUM(ABS(si.grand_total)), 0) AS return_value,
               COALESCE(SUM(ABS(si.net_total)), 0) AS net_return_value
        FROM `tabSales Invoice` si
        WHERE si.company = %(company)s AND si.docstatus = 1 AND si.is_return = 1
              AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s{extra}
        GROUP BY si.customer
        ORDER BY return_value DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    total_row = frappe.db.sql(f"""
        SELECT COUNT(*) AS total_returns,
               COALESCE(SUM(ABS(si.grand_total)), 0) AS total_return_value,
               COUNT(DISTINCT si.customer) AS customers_with_returns
        FROM `tabSales Invoice` si
        WHERE si.company = %(company)s AND si.docstatus = 1 AND si.is_return = 1
              AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s{extra}
    """, params, as_dict=True)[0]

    summary = {
        'total_returns': cint(total_row.get('total_returns')),
        'total_return_value': flt(total_row.get('total_return_value')),
        'customers_with_returns': cint(total_row.get('customers_with_returns')),
    }

    if format == 'csv':
        cols = ['customer', 'customer_name', 'return_count', 'return_value', 'net_return_value']
        _csv_response(cols, rows, 'sales_returns.csv')
        return

    return {"summary": summary, "data": rows, "total": cint(total_row.get('customers_with_returns')), "page": page, "page_size": page_size}


# ── 26. PURCHASE RETURN REPORT ────────────────────────────────
@frappe.whitelist()
def get_purchase_return_report(company=None, from_date=None, to_date=None,
                               supplier=None, page=1, page_size=50, format=None):
    """Purchase returns (debit notes) — grouped by supplier."""
    company = resolve_active_company(company)
    from_date, to_date = _date_range(from_date, to_date)
    page, page_size, offset = _paginate(page, page_size)

    params = {"company": company, "from_date": from_date, "to_date": to_date}
    extra = ""
    if supplier:
        extra = " AND pi.supplier = %(supplier)s"
        params["supplier"] = supplier

    rows = frappe.db.sql(f"""
        SELECT pi.supplier, pi.supplier_name,
               COUNT(*) AS return_count,
               COALESCE(SUM(ABS(pi.grand_total)), 0) AS return_value,
               COALESCE(SUM(ABS(pi.net_total)), 0) AS net_return_value
        FROM `tabPurchase Invoice` pi
        WHERE pi.company = %(company)s AND pi.docstatus = 1 AND pi.is_return = 1
              AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s{extra}
        GROUP BY pi.supplier
        ORDER BY return_value DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    total_row = frappe.db.sql(f"""
        SELECT COUNT(*) AS total_returns,
               COALESCE(SUM(ABS(pi.grand_total)), 0) AS total_return_value,
               COUNT(DISTINCT pi.supplier) AS suppliers_with_returns
        FROM `tabPurchase Invoice` pi
        WHERE pi.company = %(company)s AND pi.docstatus = 1 AND pi.is_return = 1
              AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s{extra}
    """, params, as_dict=True)[0]

    summary = {
        'total_returns': cint(total_row.get('total_returns')),
        'total_return_value': flt(total_row.get('total_return_value')),
        'suppliers_with_returns': cint(total_row.get('suppliers_with_returns')),
    }

    if format == 'csv':
        cols = ['supplier', 'supplier_name', 'return_count', 'return_value', 'net_return_value']
        _csv_response(cols, rows, 'purchase_returns.csv')
        return

    return {"summary": summary, "data": rows, "total": cint(total_row.get('suppliers_with_returns')), "page": page, "page_size": page_size}


# ── 27. CASH FLOW REPORT ─────────────────────────────────────
@frappe.whitelist()
def get_cashflow_report(company=None, from_date=None, to_date=None,
                        group_by='month', page=1, page_size=50, format=None):
    """Cash flow — payment entries in vs out, grouped by month or payment type."""
    company = resolve_active_company(company)
    from_date, to_date = _date_range(from_date, to_date)
    page, page_size, offset = _paginate(page, page_size)

    params = {"company": company, "from_date": from_date, "to_date": to_date}

    if group_by == 'payment_type':
        dim_expr = 'pe.payment_type'
    else:
        dim_expr = "DATE_FORMAT(pe.posting_date, '%%Y-%%m')"

    rows = frappe.db.sql(f"""
        SELECT {dim_expr} AS label,
               COALESCE(SUM(CASE WHEN pe.payment_type = 'Receive' THEN pe.paid_amount ELSE 0 END), 0) AS inflow,
               COALESCE(SUM(CASE WHEN pe.payment_type = 'Pay' THEN pe.paid_amount ELSE 0 END), 0) AS outflow,
               COALESCE(SUM(CASE WHEN pe.payment_type = 'Internal Transfer' THEN pe.paid_amount ELSE 0 END), 0) AS transfers,
               COUNT(*) AS entry_count
        FROM `tabPayment Entry` pe
        WHERE pe.company = %(company)s AND pe.docstatus = 1
              AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY label
        ORDER BY label
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    for row in rows:
        row['net_flow'] = flt(row['inflow']) - flt(row['outflow'])

    total_inflow = sum(flt(r['inflow']) for r in rows)
    total_outflow = sum(flt(r['outflow']) for r in rows)

    summary = {
        'total_inflow': total_inflow,
        'total_outflow': total_outflow,
        'net_flow': total_inflow - total_outflow,
        'total_entries': sum(cint(r['entry_count']) for r in rows),
    }

    chart = [{"label": r['label'], "inflow": flt(r['inflow']), "outflow": flt(r['outflow']), "net_flow": flt(r['net_flow'])} for r in rows]

    if format == 'csv':
        cols = ['label', 'inflow', 'outflow', 'net_flow', 'transfers', 'entry_count']
        _csv_response(cols, rows, 'cashflow.csv')
        return

    return {"summary": summary, "data": rows, "chart": chart, "total": len(rows), "page": page, "page_size": page_size}


# ── 28. PROFIT & LOSS SUMMARY REPORT ─────────────────────────
@frappe.whitelist()
def get_profit_loss_summary_report(company=None, from_date=None, to_date=None,
                                    format=None):
    """Enhanced P&L — income, COGS, gross profit, expenses, net profit via GL entries."""
    company = resolve_active_company(company)
    from_date, to_date = _date_range(from_date, to_date)

    params = {"company": company, "from_date": from_date, "to_date": to_date}

    rows = frappe.db.sql("""
        SELECT a.root_type, a.parent_account, a.name AS account,
               COALESCE(SUM(gl.credit - gl.debit), 0) AS net_amount
        FROM `tabGL Entry` gl
        INNER JOIN `tabAccount` a ON a.name = gl.account
        WHERE gl.company = %(company)s AND gl.is_cancelled = 0
              AND gl.posting_date BETWEEN %(from_date)s AND %(to_date)s
              AND a.root_type IN ('Income', 'Expense')
        GROUP BY a.name
        ORDER BY a.root_type, a.parent_account, a.name
    """, params, as_dict=True)

    income_rows = [r for r in rows if r['root_type'] == 'Income']
    expense_rows = [r for r in rows if r['root_type'] == 'Expense']

    total_income = sum(flt(r['net_amount']) for r in income_rows)
    total_expense = sum(abs(flt(r['net_amount'])) for r in expense_rows)

    # Try to identify COGS accounts for gross profit
    cogs_keywords = ['cost of goods', 'cost of sales', 'cogs', 'direct cost']
    cogs_total = 0
    for r in expense_rows:
        acct = (r.get('account') or '').lower()
        parent = (r.get('parent_account') or '').lower()
        if any(kw in acct or kw in parent for kw in cogs_keywords):
            cogs_total += abs(flt(r['net_amount']))

    gross_profit = total_income - cogs_total
    net_profit = total_income - total_expense

    summary = {
        'total_income': total_income,
        'cogs': cogs_total,
        'gross_profit': gross_profit,
        'gp_margin': _safe_pct(gross_profit, total_income),
        'total_expense': total_expense,
        'net_profit': net_profit,
        'net_margin': _safe_pct(net_profit, total_income),
    }

    # Format for display
    for r in rows:
        r['amount'] = abs(flt(r['net_amount']))
        r['type'] = r['root_type']

    if format == 'csv':
        cols = ['account', 'root_type', 'parent_account', 'amount']
        _csv_response(cols, rows, 'profit_and_loss.csv')
        return

    return {"summary": summary, "data": rows, "total": len(rows)}


# ── 29. STOCK BALANCE REPORT ─────────────────────────────────
@frappe.whitelist()
def get_stock_balance_report(company=None, warehouse=None, item_group=None,
                             page=1, page_size=50, format=None):
    """Warehouse-wise stock balance and value from Bin table."""
    company = resolve_active_company(company)
    page, page_size, offset = _paginate(page, page_size)

    conditions = ["b.actual_qty != 0"]
    params: dict = {}

    if warehouse:
        conditions.append("b.warehouse LIKE %(warehouse)s")
        params["warehouse"] = f"%{warehouse}%"
    if item_group:
        conditions.append("i.item_group = %(item_group)s")
        params["item_group"] = item_group

    # filter by company warehouse
    conditions.append("w.company = %(company)s")
    params["company"] = company

    where = " AND ".join(conditions)

    total = frappe.db.sql(f"""
        SELECT COUNT(*)
        FROM `tabBin` b
        INNER JOIN `tabItem` i ON i.name = b.item_code
        INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
        WHERE {where}
    """, params)[0][0]

    rows = frappe.db.sql(f"""
        SELECT b.item_code, i.item_name, i.item_group,
               b.warehouse,
               b.actual_qty, b.reserved_qty, b.ordered_qty, b.planned_qty,
               b.stock_value,
               CASE WHEN b.actual_qty > 0 THEN b.stock_value / b.actual_qty ELSE 0 END AS valuation_rate
        FROM `tabBin` b
        INNER JOIN `tabItem` i ON i.name = b.item_code
        INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
        WHERE {where}
        ORDER BY b.stock_value DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    summary_row = frappe.db.sql(f"""
        SELECT COALESCE(SUM(b.actual_qty), 0) AS total_qty,
               COALESCE(SUM(b.stock_value), 0) AS total_value,
               COUNT(DISTINCT b.item_code) AS unique_items,
               COUNT(DISTINCT b.warehouse) AS warehouses
        FROM `tabBin` b
        INNER JOIN `tabItem` i ON i.name = b.item_code
        INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
        WHERE {where}
    """, params, as_dict=True)[0]

    summary = {
        'total_qty': flt(summary_row.get('total_qty')),
        'total_value': flt(summary_row.get('total_value')),
        'unique_items': cint(summary_row.get('unique_items')),
        'warehouses': cint(summary_row.get('warehouses')),
    }

    if format == 'csv':
        cols = ['item_code', 'item_name', 'item_group', 'warehouse', 'actual_qty', 'reserved_qty', 'ordered_qty', 'stock_value', 'valuation_rate']
        _csv_response(cols, rows, 'stock_balance.csv')
        return

    return {"summary": summary, "data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ── 30. SALESPERSON PERFORMANCE REPORT ────────────────────────
@frappe.whitelist()
def get_salesperson_performance_report(company=None, from_date=None, to_date=None,
                                        page=1, page_size=50, format=None):
    """Revenue, GP, margin and contribution per salesperson."""
    company = resolve_active_company(company)
    from_date, to_date = _date_range(from_date, to_date)
    page, page_size, offset = _paginate(page, page_size)

    params = {"company": company, "from_date": from_date, "to_date": to_date}

    rows = frappe.db.sql("""
        SELECT st.sales_person,
               COALESCE(SUM(sii.amount * st.allocated_percentage / 100), 0) AS revenue,
               COALESCE(SUM((sii.amount - COALESCE(sii.incoming_rate * sii.qty, 0)) * st.allocated_percentage / 100), 0) AS gross_profit,
               COUNT(DISTINCT si.name) AS invoice_count,
               COUNT(DISTINCT si.customer) AS customer_count,
               COALESCE(SUM(sii.qty * st.allocated_percentage / 100), 0) AS qty_sold
        FROM `tabSales Team` st
        INNER JOIN `tabSales Invoice` si ON si.name = st.parent AND si.docstatus = 1
        INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE si.company = %(company)s
              AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY st.sales_person
        ORDER BY revenue DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    for row in rows:
        row['gp_margin'] = _safe_pct(flt(row['gross_profit']), flt(row['revenue']))

    total_rev = sum(flt(r['revenue']) for r in rows)
    for row in rows:
        row['revenue_share'] = _safe_pct(flt(row['revenue']), total_rev)

    total_count = frappe.db.sql("""
        SELECT COUNT(DISTINCT st.sales_person)
        FROM `tabSales Team` st
        INNER JOIN `tabSales Invoice` si ON si.name = st.parent AND si.docstatus = 1
        WHERE si.company = %(company)s
              AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
    """, params)[0][0]

    summary = {
        'total_salespersons': cint(total_count),
        'total_revenue': total_rev,
        'total_gp': sum(flt(r['gross_profit']) for r in rows),
        'avg_margin': _safe_pct(sum(flt(r['gross_profit']) for r in rows), total_rev),
    }

    if format == 'csv':
        cols = ['sales_person', 'revenue', 'gross_profit', 'gp_margin', 'invoice_count', 'customer_count', 'qty_sold', 'revenue_share']
        _csv_response(cols, rows, 'salesperson_performance.csv')
        return

    return {"summary": summary, "data": rows, "total": cint(total_count), "page": page, "page_size": page_size}


# ── 31. ITEM-WISE PURCHASE REPORT ─────────────────────────────
@frappe.whitelist()
def get_item_purchase_report(company=None, from_date=None, to_date=None,
                             item_group=None, supplier=None,
                             page=1, page_size=50, format=None):
    """Item-wise purchase breakdown — qty, value, avg rate, supplier count."""
    company = resolve_active_company(company)
    from_date, to_date = _date_range(from_date, to_date)
    page, page_size, offset = _paginate(page, page_size)

    params = {"company": company, "from_date": from_date, "to_date": to_date}
    extra = ""
    if item_group:
        extra += " AND pii.item_group = %(item_group)s"
        params["item_group"] = item_group
    if supplier:
        extra += " AND pi.supplier = %(supplier)s"
        params["supplier"] = supplier

    total = frappe.db.sql(f"""
        SELECT COUNT(DISTINCT pii.item_code)
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        WHERE pi.company = %(company)s AND pi.docstatus = 1 AND COALESCE(pi.is_return, 0) = 0
              AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s{extra}
    """, params)[0][0]

    rows = frappe.db.sql(f"""
        SELECT pii.item_code, pii.item_name, pii.item_group,
               COALESCE(SUM(pii.qty), 0) AS total_qty,
               COALESCE(SUM(pii.amount), 0) AS total_amount,
               COALESCE(AVG(pii.rate), 0) AS avg_rate,
               MIN(pii.rate) AS min_rate,
               MAX(pii.rate) AS max_rate,
               COUNT(DISTINCT pi.supplier) AS supplier_count,
               COUNT(DISTINCT pi.name) AS invoice_count
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        WHERE pi.company = %(company)s AND pi.docstatus = 1 AND COALESCE(pi.is_return, 0) = 0
              AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s{extra}
        GROUP BY pii.item_code
        ORDER BY total_amount DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    summary_row = frappe.db.sql(f"""
        SELECT COALESCE(SUM(pii.amount), 0) AS total_value,
               COALESCE(SUM(pii.qty), 0) AS total_qty,
               COUNT(DISTINCT pii.item_code) AS unique_items
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        WHERE pi.company = %(company)s AND pi.docstatus = 1 AND COALESCE(pi.is_return, 0) = 0
              AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s{extra}
    """, params, as_dict=True)[0]

    summary = {
        'total_value': flt(summary_row.get('total_value')),
        'total_qty': flt(summary_row.get('total_qty')),
        'unique_items': cint(summary_row.get('unique_items')),
    }

    if format == 'csv':
        cols = ['item_code', 'item_name', 'item_group', 'total_qty', 'total_amount', 'avg_rate', 'min_rate', 'max_rate', 'supplier_count', 'invoice_count']
        _csv_response(cols, rows, 'item_purchases.csv')
        return

    return {"summary": summary, "data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ── 30. TRIAL BALANCE ────────────────────────────────────────────
def _split_debit_credit(net_amount):
    """Split signed net (debit − credit) into debit and credit columns."""
    net = flt(net_amount)
    if net >= 0:
        return net, 0
    return 0, abs(net)


@frappe.whitelist()
def get_trial_balance_report(company=None, from_date=None, to_date=None, format=None):
    """Trial balance — opening, period movement, and closing per account."""
    company = resolve_active_company(company)
    from_date, to_date = _date_range(from_date, to_date, default_months=1)

    params = {"company": company, "from_date": from_date, "to_date": to_date}

    raw = frappe.db.sql("""
        SELECT a.name AS account,
               COALESCE(a.account_name, a.name) AS account_name,
               a.root_type,
               a.parent_account,
               COALESCE(SUM(CASE WHEN gle.posting_date < %(from_date)s THEN gle.debit ELSE 0 END), 0) AS opening_debit,
               COALESCE(SUM(CASE WHEN gle.posting_date < %(from_date)s THEN gle.credit ELSE 0 END), 0) AS opening_credit,
               COALESCE(SUM(CASE WHEN gle.posting_date BETWEEN %(from_date)s AND %(to_date)s THEN gle.debit ELSE 0 END), 0) AS debit,
               COALESCE(SUM(CASE WHEN gle.posting_date BETWEEN %(from_date)s AND %(to_date)s THEN gle.credit ELSE 0 END), 0) AS credit
        FROM `tabAccount` a
        INNER JOIN `tabGL Entry` gle
            ON gle.account = a.name
           AND gle.company = %(company)s
           AND gle.is_cancelled = 0
        WHERE a.company = %(company)s
        GROUP BY a.name
        HAVING opening_debit + opening_credit + debit + credit > 0.005
        ORDER BY a.root_type, a.parent_account, a.name
    """, params, as_dict=True)

    rows = []
    totals = {
        "opening_debit": 0,
        "opening_credit": 0,
        "debit": 0,
        "credit": 0,
        "closing_debit": 0,
        "closing_credit": 0,
    }

    for row in raw:
        opening_net = flt(row.opening_debit) - flt(row.opening_credit)
        opening_dr, opening_cr = _split_debit_credit(opening_net)
        closing_net = opening_net + flt(row.debit) - flt(row.credit)
        closing_dr, closing_cr = _split_debit_credit(closing_net)

        entry = {
            "account": row.account,
            "account_name": row.account_name,
            "root_type": row.root_type,
            "parent_account": row.parent_account,
            "opening_debit": opening_dr,
            "opening_credit": opening_cr,
            "debit": flt(row.debit),
            "credit": flt(row.credit),
            "closing_debit": closing_dr,
            "closing_credit": closing_cr,
        }
        rows.append(entry)
        for key in totals:
            totals[key] += flt(entry[key])

    difference = flt(totals["closing_debit"]) - flt(totals["closing_credit"])
    summary = {
        **totals,
        "difference": difference,
        "is_balanced": abs(difference) < 0.05,
        "from_date": from_date,
        "to_date": to_date,
    }

    if format == "csv":
        cols = [
            "account", "account_name", "root_type", "parent_account",
            "opening_debit", "opening_credit", "debit", "credit",
            "closing_debit", "closing_credit",
        ]
        _csv_response(cols, rows, "trial_balance.csv")
        return

    return {"summary": summary, "data": rows, "total": len(rows)}


# ── 31. BALANCE SHEET ────────────────────────────────────────────
@frappe.whitelist()
def get_balance_sheet_report(company=None, as_on_date=None, format=None):
    """Balance sheet — asset, liability, and equity balances as of a date."""
    company = resolve_active_company(company)
    as_on_date = getdate(as_on_date or nowdate())

    params = {"company": company, "as_on_date": as_on_date}

    raw = frappe.db.sql("""
        SELECT a.name AS account,
               COALESCE(a.account_name, a.name) AS account_name,
               a.root_type,
               a.account_type,
               a.parent_account,
               COALESCE(SUM(gle.debit - gle.credit), 0) AS balance
        FROM `tabAccount` a
        INNER JOIN `tabGL Entry` gle
            ON gle.account = a.name
           AND gle.company = %(company)s
           AND gle.is_cancelled = 0
           AND gle.posting_date <= %(as_on_date)s
        WHERE a.company = %(company)s
          AND a.root_type IN ('Asset', 'Liability', 'Equity')
        GROUP BY a.name
        HAVING ABS(balance) > 0.005
        ORDER BY a.root_type, a.parent_account, a.name
    """, params, as_dict=True)

    rows = []
    section_totals = {"Asset": 0, "Liability": 0, "Equity": 0}

    for row in raw:
        balance = flt(row.balance)
        root = row.root_type
        if root in ("Liability", "Equity"):
            display_balance = -balance
        else:
            display_balance = balance
        section_totals[root] = section_totals.get(root, 0) + display_balance
        rows.append({
            "account": row.account,
            "account_name": row.account_name,
            "root_type": root,
            "account_type": row.account_type,
            "parent_account": row.parent_account,
            "balance": display_balance,
        })

    total_assets = flt(section_totals.get("Asset"))
    total_liabilities = flt(section_totals.get("Liability"))
    total_equity = flt(section_totals.get("Equity"))
    accounting_equation_diff = total_assets - total_liabilities - total_equity

    summary = {
        "as_on_date": as_on_date,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity,
        "accounting_equation_diff": accounting_equation_diff,
        "is_balanced": abs(accounting_equation_diff) < 0.05,
    }

    if format == "csv":
        cols = ["account", "account_name", "root_type", "account_type", "parent_account", "balance"]
        _csv_response(cols, rows, "balance_sheet.csv")
        return

    return {"summary": summary, "data": rows, "total": len(rows)}


# ── 32. SERIAL TRACE ─────────────────────────────────────────────
@frappe.whitelist()
def get_serial_trace_report(company=None, serial_no=None, item_code=None,
                            status=None, page=1, page_size=50, format=None):
    """Serial numbers with purchase/delivery document links and current status."""
    company = resolve_active_company(company)
    page, page_size, offset = _paginate(page, page_size)

    conditions = ["1=1"]
    params = {}

    if frappe.db.has_column("Serial No", "company"):
        conditions.append("sn.company = %(company)s")
        params["company"] = company

    if serial_no:
        conditions.append("sn.name LIKE %(serial_no)s")
        params["serial_no"] = f"%{serial_no.strip()}%"
    if item_code:
        conditions.append("sn.item_code = %(item_code)s")
        params["item_code"] = item_code.strip()
    if status:
        conditions.append("sn.status = %(status)s")
        params["status"] = status.strip()

    where = " AND ".join(conditions)

    total = frappe.db.sql(f"""
        SELECT COUNT(*) FROM `tabSerial No` sn WHERE {where}
    """, params)[0][0]

    select_cols = [
        "sn.name AS serial_no",
        "sn.item_code",
        "i.item_name",
        "sn.warehouse",
        "sn.status",
    ]
    if frappe.db.has_column("Serial No", "purchase_document_type"):
        select_cols.extend(["sn.purchase_document_type", "sn.purchase_document_no"])
    if frappe.db.has_column("Serial No", "delivery_document_type"):
        select_cols.extend(["sn.delivery_document_type", "sn.delivery_document_no"])

    rows = frappe.db.sql(f"""
        SELECT {", ".join(select_cols)}
        FROM `tabSerial No` sn
        LEFT JOIN `tabItem` i ON i.name = sn.item_code
        WHERE {where}
        ORDER BY sn.modified DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**params, "page_size": page_size, "offset": offset}, as_dict=True)

    status_counts = frappe.db.sql(f"""
        SELECT sn.status, COUNT(*) AS count
        FROM `tabSerial No` sn
        WHERE {where}
        GROUP BY sn.status
        ORDER BY count DESC
    """, params, as_dict=True)

    summary = {
        "total_serials": cint(total),
        "by_status": {r.status or "Unknown": cint(r.count) for r in status_counts},
    }

    if format == "csv":
        cols = list(rows[0].keys()) if rows else ["serial_no", "item_code", "status"]
        _csv_response(cols, rows, "serial_trace.csv")
        return

    return {"summary": summary, "data": rows, "total": cint(total), "page": page, "page_size": page_size}


# ── 33. FX GAIN / LOSS (UNREALIZED) ─────────────────────────────
@frappe.whitelist()
def get_fx_gain_loss_report(company=None, as_on_date=None, format=None):
    """Unrealized FX exposure from open foreign-currency invoices."""
    from trader_app.api.currency import _fetch_exchange_rate, get_company_currency_settings

    company = resolve_active_company(company)
    as_on_date = getdate(as_on_date or nowdate())
    settings = get_company_currency_settings(company)
    base = settings["base_currency"]

    if not settings["multi_currency_enabled"]:
        summary = {
            "as_on_date": as_on_date,
            "base_currency": base,
            "multi_currency_enabled": False,
            "total_unrealized_gain_loss": 0,
            "receivable_gain_loss": 0,
            "payable_gain_loss": 0,
            "open_documents": 0,
        }
        if format == "csv":
            _csv_response(
                ["doctype", "name", "party", "currency"],
                [],
                "fx_gain_loss.csv",
            )
            return
        return {"summary": summary, "data": [], "total": 0}

    rows = []

    si_rows = frappe.db.sql(
        """
        SELECT 'Sales Invoice' AS doctype,
               si.name,
               si.customer AS party,
               si.posting_date,
               si.currency,
               si.conversion_rate AS book_rate,
               si.outstanding_amount AS outstanding_fcy
        FROM `tabSales Invoice` si
        WHERE si.company = %(company)s
          AND si.docstatus = 1
          AND si.outstanding_amount > 0.005
          AND si.currency != %(base)s
        ORDER BY si.posting_date DESC, si.name DESC
        """,
        {"company": company, "base": base},
        as_dict=True,
    )

    pi_rows = frappe.db.sql(
        """
        SELECT 'Purchase Invoice' AS doctype,
               pi.name,
               pi.supplier AS party,
               pi.posting_date,
               pi.currency,
               pi.conversion_rate AS book_rate,
               pi.outstanding_amount AS outstanding_fcy
        FROM `tabPurchase Invoice` pi
        WHERE pi.company = %(company)s
          AND pi.docstatus = 1
          AND pi.outstanding_amount > 0.005
          AND pi.currency != %(base)s
        ORDER BY pi.posting_date DESC, pi.name DESC
        """,
        {"company": company, "base": base},
        as_dict=True,
    )

    receivable_gl = 0
    payable_gl = 0

    for row in si_rows + pi_rows:
        currency = row.currency
        fcy = flt(row.outstanding_fcy)
        book_rate = flt(row.book_rate) or 1.0
        for_selling = row.doctype == "Sales Invoice"
        current_rate = _fetch_exchange_rate(
            currency,
            base,
            as_on_date,
            for_selling=for_selling,
        )
        book_base = fcy * book_rate
        current_base = fcy * current_rate
        if row.doctype == "Sales Invoice":
            unrealized = current_base - book_base
            receivable_gl += unrealized
        else:
            unrealized = book_base - current_base
            payable_gl += unrealized

        rows.append({
            "doctype": row.doctype,
            "name": row.name,
            "party": row.party,
            "posting_date": row.posting_date,
            "currency": currency,
            "outstanding_fcy": fcy,
            "book_rate": book_rate,
            "book_base": book_base,
            "current_rate": current_rate,
            "current_base": current_base,
            "unrealized_gain_loss": unrealized,
            "exposure_type": "Receivable" if row.doctype == "Sales Invoice" else "Payable",
        })

    total_gl = receivable_gl + payable_gl
    summary = {
        "as_on_date": as_on_date,
        "base_currency": base,
        "multi_currency_enabled": True,
        "total_unrealized_gain_loss": total_gl,
        "receivable_gain_loss": receivable_gl,
        "payable_gain_loss": payable_gl,
        "open_documents": len(rows),
    }

    if format == "csv":
        cols = [
            "doctype", "name", "party", "posting_date", "currency", "exposure_type",
            "outstanding_fcy", "book_rate", "book_base", "current_rate", "current_base",
            "unrealized_gain_loss",
        ]
        _csv_response(cols, rows, "fx_gain_loss.csv")
        return

    return {"summary": summary, "data": rows, "total": len(rows)}

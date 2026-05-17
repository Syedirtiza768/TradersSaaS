# -*- coding: utf-8 -*-
"""Trader App — Activity / version audit log for the SPA."""

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import getdate, nowdate, cint

from trader_app.api.company import resolve_active_company

# DocTypes whose `company` field scopes activity to the active company.
_COMPANY_DOCTYPES = (
    "Sales Invoice",
    "Purchase Invoice",
    "Sales Order",
    "Purchase Order",
    "Payment Entry",
    "Delivery Note",
    "Journal Entry",
    "Quotation",
    "Purchase Receipt",
    "Stock Entry",
)


def _company_activity_clause():
    """SQL OR-chains: activity references a document in the user's company."""
    parts = []
    for dt in _COMPANY_DOCTYPES:
        table = f"tab{dt}"
        parts.append(
            "(al.reference_doctype = {dt} AND EXISTS ("
            "SELECT 1 FROM `{table}` d "
            "WHERE d.name = al.reference_name AND d.company = %(company)s"
            "))".format(dt=frappe.db.escape(dt), table=table)
        )
    return " OR ".join(parts)


@frappe.whitelist()
def get_audit_log(
    company=None,
    from_date=None,
    to_date=None,
    reference_doctype=None,
    reference_name=None,
    user=None,
    page=1,
    page_size=50,
):
    """Paginated activity log for the active company."""
    company = resolve_active_company(company)
    page = cint(page) or 1
    page_size = min(cint(page_size) or 50, 100)
    offset = (page - 1) * page_size

    from frappe.utils import add_days

    from_date = getdate(from_date or add_days(nowdate(), -30))
    to_date = getdate(to_date or nowdate())

    conditions = [
        "al.creation >= %(from_datetime)s",
        "al.creation <= %(to_datetime)s",
        "({company_clause})".format(company_clause=_company_activity_clause()),
    ]
    params = {
        "company": company,
        "from_datetime": f"{from_date} 00:00:00",
        "to_datetime": f"{to_date} 23:59:59",
    }

    if reference_doctype:
        conditions.append("al.reference_doctype = %(reference_doctype)s")
        params["reference_doctype"] = reference_doctype.strip()
    if reference_name:
        conditions.append("al.reference_name LIKE %(reference_name)s")
        params["reference_name"] = f"%{reference_name.strip()}%"
    if user:
        conditions.append("(al.owner = %(user)s OR al.full_name LIKE %(user_like)s)")
        params["user"] = user.strip()
        params["user_like"] = f"%{user.strip()}%"

    where = " AND ".join(conditions)

    total = frappe.db.sql(
        f"SELECT COUNT(*) FROM `tabActivity Log` al WHERE {where}",
        params,
    )[0][0]

    rows = frappe.db.sql(
        f"""
        SELECT al.name,
               al.creation,
               al.owner,
               al.full_name,
               al.operation,
               al.subject,
               al.reference_doctype,
               al.reference_name,
               al.status
        FROM `tabActivity Log` al
        WHERE {where}
        ORDER BY al.creation DESC
        LIMIT %(page_size)s OFFSET %(offset)s
        """,
        {**params, "page_size": page_size, "offset": offset},
        as_dict=True,
    )

    return {
        "company": company,
        "from_date": str(from_date),
        "to_date": str(to_date),
        "data": rows,
        "total": cint(total),
        "page": page,
        "page_size": page_size,
    }


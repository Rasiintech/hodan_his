import frappe
from frappe import _
from frappe.utils import getdate, flt
from erpnext.accounts.utils import get_balance_on


def execute(filters=None):
    filters = frappe._dict(filters or {})

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "fieldname": "document",
            "label": _("Document"),
            "fieldtype": "Link",
            "options": "Discharge And Clearance",
            "width": 180,
        },
        {
            "fieldname": "date",
            "label": _("Date"),
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "fieldname": "patient",
            "label": _("Patient"),
            "fieldtype": "Link",
            "options": "Patient",
            "width": 180,
        },
        {
            "fieldname": "patient_name",
            "label": _("Patient Name"),
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "fieldname": "customer",
            "label": _("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            "width": 180,
        },
        {
            "fieldname": "net_balance",
            "label": _("Net Balance"),
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "fieldname": "reason",
            "label": _("Reason"),
            "fieldtype": "Data",
            "width": 400,
        },
    ]


def get_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    company = filters.get("company") or frappe.defaults.get_user_default("Company")

    if not from_date or not to_date:
        frappe.throw(_("From Date and To Date are required."))

    if not company:
        frappe.throw(_("Company is required."))

    rows = frappe.db.sql(
        """
        SELECT
            dac.name AS document,
            DATE(dac.creation) AS date,
            dac.patient,
            dac.patient_name,
            dac.customer,
            dac.reason
        FROM
            `tabDischarge And Clearance` dac
        WHERE
            DATE(dac.creation) BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY
            dac.creation DESC
        """,
        {
            "from_date": from_date,
            "to_date": to_date,
        },
        as_dict=True,
    )

    balance_cache = {}

    for row in rows:
        if not row.customer:
            row.net_balance = 0
            continue

        cache_key = (row.customer, company, to_date)

        if cache_key not in balance_cache:
            balance_cache[cache_key] = flt(
                get_balance_on(
                    party_type="Customer",
                    party=row.customer,
                    company=company,
                    date=getdate(to_date),
                )
            )

        row.net_balance = balance_cache[cache_key]

    return rows
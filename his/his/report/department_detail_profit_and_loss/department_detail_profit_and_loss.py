# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


VIEW_CONFIG = {
    "Department": {
        "fieldname": "department",
        "column_label": "Department",
        "filter_label": "Department",
    },
    "Consultant": {
        "fieldname": "consultant",
        "column_label": "Consultant",
        "filter_label": "Consultant",
    },
}


def execute(filters=None):
    filters = filters or {}
    view_by = filters.get("view_by") or "Department"

    if view_by not in VIEW_CONFIG:
        frappe.throw("Please select a valid View By option")

    filter_field = VIEW_CONFIG[view_by]["fieldname"]
    filter_value = filters.get(filter_field)

    if not filter_value:
        frappe.throw(f"Please select a {VIEW_CONFIG[view_by]['filter_label']}")

    columns = get_columns(view_by)
    data = get_data(filters, view_by, filter_value)
    return columns, data


def get_columns(view_by):
    return [
        {
            "label": VIEW_CONFIG[view_by]["column_label"],
            "fieldname": "entity",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": "Account",
            "fieldname": "account",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": "Amount",
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 140,
        },
    ]


def get_data(filters, view_by, filter_value):
    filter_field = VIEW_CONFIG[view_by]["fieldname"]
    conditions = [f"c.{filter_field} = %(filter_value)s"]
    values = {"filter_value": filter_value}

    if filters.get("from_date"):
        conditions.append("p.from_date >= %(from_date)s")
        values["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions.append("p.to_date <= %(to_date)s")
        values["to_date"] = filters.get("to_date")

    rows = frappe.db.sql(
        f"""
        SELECT
            p.type,
            p.account,
            SUM(c.allocatated_amount) AS amount
        FROM `tabDepartment Wise Profit and Loss` p
        INNER JOIN `tabAllocation Table` c
            ON c.parent = p.name
        WHERE p.docstatus < 2
          AND {' AND '.join(conditions)}
        GROUP BY p.type, p.account
        ORDER BY
            CASE
                WHEN p.type = 'Income' THEN 1
                WHEN p.type = 'Direct Expense' THEN 2
                WHEN p.type = 'Indirect Expense' THEN 3
                ELSE 4
            END,
            p.account
    """,
        values,
        as_dict=True,
    )

    data = []
    direct_income_total = 0
    direct_expense_total = 0
    indirect_expense_total = 0

    income_rows = []
    direct_expense_rows = []
    indirect_expense_rows = []

    for row in rows:
        amount = flt(row.amount)

        if row.type == "Income":
            income_rows.append({"entity": "", "account": row.account, "amount": amount})
            direct_income_total += amount
        elif row.type == "Direct Expense":
            direct_expense_rows.append({"entity": "", "account": row.account, "amount": amount})
            direct_expense_total += amount
        elif row.type == "Indirect Expense":
            indirect_expense_rows.append({"entity": "", "account": row.account, "amount": amount})
            indirect_expense_total += amount

    total_expense = direct_expense_total + indirect_expense_total
    net_profit = direct_income_total - total_expense

    data.append({"entity": filter_value, "account": "", "amount": ""})
    data.append({"entity": "Income", "account": "", "amount": ""})
    data.extend(income_rows)

    data.append({"entity": "Expenses", "account": "", "amount": ""})
    data.append({"entity": "Direct Expense", "account": "", "amount": ""})
    data.extend(direct_expense_rows)

    data.append({"entity": "Indirect Expense", "account": "", "amount": ""})
    data.extend(indirect_expense_rows)

    data.append({"entity": "Total Expense", "account": "", "amount": total_expense})
    data.append({})
    data.append({"entity": "Net Profit & Loss", "account": "", "amount": net_profit})

    return data

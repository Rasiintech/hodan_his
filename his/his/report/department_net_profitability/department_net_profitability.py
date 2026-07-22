# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt
# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, None, chart


def get_columns():
    return [
        {
            "label": "Department",
            "fieldname": "department",
            "fieldtype": "Data",
            "width": 220
        },
        {
            "label": "Direct Income",
            "fieldname": "direct_income",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": "Direct Expense",
            "fieldname": "direct_expense",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": "Indirect Expense",
            "fieldname": "indirect_expense",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": "Net Profit",
            "fieldname": "net_profit",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": "Net Profit %",
            "fieldname": "net_profit_percent",
            "fieldtype": "Percent",
            "width": 130
        }
    ]


def get_data(filters):
    conditions = ""
    values = {}

    if filters.get("from_date"):
        conditions += " AND p.from_date >= %(from_date)s"
        values["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions += " AND p.to_date <= %(to_date)s"
        values["to_date"] = filters.get("to_date")

    if filters.get("department"):
        conditions += " AND c.department = %(department)s"
        values["department"] = filters.get("department")

    rows = frappe.db.sql(f"""
        SELECT
            c.department,
            c.consultant,
            p.type,
            SUM(c.allocatated_amount) AS amount
        FROM `tabDepartment Wise Profit and Loss` p
        INNER JOIN `tabAllocation Table` c
            ON c.parent = p.name
        WHERE p.docstatus < 2
        {conditions}
        GROUP BY c.department, c.consultant, p.type
        ORDER BY c.department, c.consultant
    """, values, as_dict=True)

    summary = {}

    for row in rows:
        department = row.department or "Not Assigned"
        consultant = row.consultant or "Not Assigned"
        key = (department, consultant)

        if key not in summary:
            summary[key] = {
                "department": department,
                "consultant": consultant,
                "direct_income": 0,
                "direct_expense": 0,
                "indirect_expense": 0,
                "net_profit": 0,
                "net_profit_percent": 0
            }

        if row.type == "Income":
            summary[key]["direct_income"] += flt(row.amount)
        elif row.type == "Direct Expense":
            summary[key]["direct_expense"] += flt(row.amount)
        elif row.type == "Indirect Expense":
            summary[key]["indirect_expense"] += flt(row.amount)

    department_map = {}
    for (department, consultant), row in summary.items():
        row["net_profit"] = (
            flt(row["direct_income"])
            - flt(row["direct_expense"])
            - flt(row["indirect_expense"])
        )
        row["net_profit_percent"] = (
            (flt(row["net_profit"]) / flt(row["direct_income"]) * 100)
            if flt(row["direct_income"]) else 0
        )

        if department not in department_map:
            department_map[department] = {
                "department": department,
                "direct_income": 0,
                "direct_expense": 0,
                "indirect_expense": 0,
                "net_profit": 0,
                "net_profit_percent": 0,
                "consultants": []
            }

        department_map[department]["direct_income"] += flt(row["direct_income"])
        department_map[department]["direct_expense"] += flt(row["direct_expense"])
        department_map[department]["indirect_expense"] += flt(row["indirect_expense"])
        department_map[department]["consultants"].append(row)

    data = []
    total_row = {
        "row_name": "Grand Total",
        "parent_row": None,
        "indent": 0,
        "is_group": 1,
        "department": "Grand Total",
        "consultant": "",
        "direct_income": 0,
        "direct_expense": 0,
        "indirect_expense": 0,
        "net_profit": 0,
        "net_profit_percent": 0
    }

    for department in sorted(department_map.keys()):
        dept = department_map[department]
        dept["net_profit"] = (
            flt(dept["direct_income"])
            - flt(dept["direct_expense"])
            - flt(dept["indirect_expense"])
        )
        dept["net_profit_percent"] = (
            (flt(dept["net_profit"]) / flt(dept["direct_income"]) * 100)
            if flt(dept["direct_income"]) else 0
        )

        # Department parent row
        data.append({
            "row_name": department,
            "parent_row": None,
            "indent": 0,
            "is_group": 1,
            "department": department,
            "consultant": "",
            "direct_income": dept["direct_income"],
            "direct_expense": dept["direct_expense"],
            "indirect_expense": dept["indirect_expense"],
            "net_profit": dept["net_profit"],
            "net_profit_percent": dept["net_profit_percent"]
        })

        # Consultant child rows
        for c in sorted(dept["consultants"], key=lambda x: x["consultant"]):
            data.append({
                "row_name": f"{department}::{c['consultant']}",
                "parent_row": department,
                "indent": 1,
                "is_group": 0,
                "department": c["consultant"],  # same first column, indented by tree
                "consultant": c["consultant"],
                "direct_income": c["direct_income"],
                "direct_expense": c["direct_expense"],
                "indirect_expense": c["indirect_expense"],
                "net_profit": c["net_profit"],
                "net_profit_percent": c["net_profit_percent"]
            })

        total_row["direct_income"] += flt(dept["direct_income"])
        total_row["direct_expense"] += flt(dept["direct_expense"])
        total_row["indirect_expense"] += flt(dept["indirect_expense"])
        total_row["net_profit"] += flt(dept["net_profit"])

    total_row["net_profit_percent"] = (
        (flt(total_row["net_profit"]) / flt(total_row["direct_income"]) * 100)
        if flt(total_row["direct_income"]) else 0
    )

    data.append({})
    data.append(total_row)

    return data


def get_chart(data):
    chart_data = [
        d for d in data
        if d.get("department") and d.get("department") != "Grand Total"
    ]

    return {
        "data": {
            "labels": [d["department"] for d in chart_data],
            "datasets": [
                {
                    "name": "Net Profit",
                    "values": [flt(d["net_profit"]) for d in chart_data]
                }
            ]
        },
        "type": "bar",
        "height": 300
    }
# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from functools import lru_cache

# from his.his.report.anomaly_report_utils import as_filters


LAB_ACCOUNT_KEYWORDS = "Laboratory - HH"


def execute(filters=None):
    filters = filters
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": _("Test Name"),
            "fieldname": "test_name",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": _("Qty Sold"),
            "fieldname": "qty_sold",
            "fieldtype": "Float",
            "width": 110,
        },
        {
            "label": _("Avg Selling Rate"),
            "fieldname": "avg_selling_rate",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Selling Amount"),
            "fieldname": "selling_amount",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Cost Per Test"),
            "fieldname": "cost_per_test",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": _("Cost of Sold Item"),
            "fieldname": "cost_of_sold_item",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Profit or Loss"),
            "fieldname": "profit_or_loss",
            "fieldtype": "Currency",
            "width": 130,
        },
    ]


def get_data(filters):
    rows = frappe.db.sql(
        """
        SELECT
            ltt.name AS template_name,
            MAX(COALESCE(NULLIF(ltt.lab_test_name, ''), NULLIF(sii.item_name, ''), sii.item_code)) AS test_name,
            SUM(IFNULL(sii.qty, 0)) AS qty_sold,
            SUM(IFNULL(sii.net_amount, 0)) AS selling_amount
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii
            ON sii.parent = si.name
        INNER JOIN `tabLab Test Template` ltt
            ON ltt.item = sii.item_code
        LEFT JOIN `tabAccount` acc
            ON acc.name = sii.income_account
        WHERE si.docstatus = 1
            AND IFNULL(si.is_return, 0) = 0
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            and sii.income_account =  %(lab_account_names)s
         
        GROUP BY ltt.name
        HAVING SUM(IFNULL(sii.qty, 0)) > 0
        ORDER BY selling_amount DESC, test_name ASC
        """,
        {
            "from_date": filters.from_date,
            "to_date": filters.to_date,
            "lab_account_names": LAB_ACCOUNT_KEYWORDS,
        },
        as_dict=True,
    )

    data = []
    for row in rows:
        qty_sold = flt(row.qty_sold)
        selling_amount = flt(row.selling_amount)
        cost_per_test = get_lab_test_cost(row.template_name)
        cost_of_sold_item = qty_sold * cost_per_test

        data.append(
            {
                "test_name": row.test_name,
                "qty_sold": qty_sold,
                "avg_selling_rate": selling_amount / qty_sold if qty_sold else 0,
                "selling_amount": selling_amount,
                "cost_per_test": cost_per_test,
                "cost_of_sold_item": cost_of_sold_item,
                "profit_or_loss": selling_amount - cost_of_sold_item,
            }
        )

    return data


@lru_cache(maxsize=None)
def get_lab_test_cost(template_name):
    meta = frappe.get_meta("Lab Test Template")
    for fieldname in ("cost", "lab_test_cost", "total_cost"):
        if meta.has_field(fieldname):
            value = frappe.db.get_value("Lab Test Template", template_name, fieldname)
            if value not in (None, ""):
                return flt(value)

    template_doc = frappe.get_doc("Lab Test Template", template_name)
    total_cost = 0
    for row in template_doc.get("inventory") or []:
        valuation_rate = frappe.db.get_value("Item", row.item, "valuation_rate")
        total_cost += flt(row.qty) * flt(valuation_rate)

    return total_cost

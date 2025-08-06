# File: custom_sales_invoice_report.py

import frappe
from frappe.utils import getdate

def execute(filters=None):
    if not filters:
        filters = {}

    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))
    source_order = filters.get("source_order")
    item_code = filters.get("item_code")

    conditions = []
    params = {
        "from_date": from_date,
        "to_date": to_date
    }

    if source_order:
        conditions.append("si.source_order = %(source_order)s")
        params["source_order"] = source_order

    if item_code:
        conditions.append("sii.item_code = %(item_code)s")
        params["item_code"] = item_code

    condition_clause = ""
    if conditions:
        condition_clause = " AND (" + " OR ".join(conditions) + ")"

    query = f"""
        SELECT 
            si.name,
            si.patient,
            si.posting_date,
            si.source_order,
            sii.item_code
        FROM `tabSales Invoice` AS si
        LEFT JOIN `tabSales Invoice Item` AS sii ON si.name = sii.parent
        WHERE si.posting_date BETWEEN %(from_date)s AND %(to_date)s
        {condition_clause}
    """

    data = frappe.db.sql(query, params, as_dict=True)

    columns = [
        {"label": "Invoice", "fieldname": "name", "fieldtype": "Link", "options": "Sales Invoice", "width": 150},
        {"label": "Patient", "fieldname": "patient", "fieldtype": "Data", "width": 150},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": "Source Order", "fieldname": "source_order", "fieldtype": "Link", "options": "Sales Order", "width": 150},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 180},
    ]

    return columns, data

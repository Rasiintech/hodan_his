# Copyright (c) 2025, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _, msgprint
from frappe.utils import flt
def execute(filters=None):
    if not filters:
        filters = {}
    
    if not filters.get("ref_practitioner"):
        msgprint(_("Please select a doctor to generate the report."), raise_exception=True)

    commission_data = []
    if filters.get("ref_practitioner"):
        ref_practitioner_doc = frappe.get_doc("Healthcare Practitioner", filters.get("ref_practitioner"))
        
        if ref_practitioner_doc.commission:
            for item in ref_practitioner_doc.commission:
                item_group = item.item_group
                percentage = item.percent
                
                item_group_doc = frappe.get_doc("Item Group", item_group)
                item_income_account = None
                if item_group_doc.item_group_defaults:
                    item_income_account = item_group_doc.item_group_defaults[0].income_account
                
                if item_income_account:
                    commission_data.append({
                        "item_group": item_group,
                        "percentage": percentage,
                        "income_account": item_income_account
                    })

    item_group_data = get_item_group_data(filters)

    # frappe.errprint(item_group_data)
    columns = get_columns()
    
    if not item_group_data:
        msgprint(_("No item group data found for the selected doctor."))
        return columns, []
    
    data = []
    expense_percentage = 25
    for item_group_record in item_group_data:
        for commission in commission_data:
            if item_group_record.item_group == commission["item_group"]:
                gross_sales = item_group_record.net_sales
                sales_amount = (gross_sales * 0.25)
                adjusted_total = gross_sales - (gross_sales * 0.25)
                net_commission = adjusted_total * (commission["percentage"] / 100)
                
                data.append({
                    "income_account": commission["income_account"],
                    "item_group": commission["item_group"],
                    "gross_sales": gross_sales,
                    "net_sales": adjusted_total,
                    "sales_amount": sales_amount,
                    "expense_percentage": expense_percentage,
                    "percentage": commission["percentage"],
                    "net_commission": net_commission
                })
    
    return columns, data


def get_columns():
    return [
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 150},
        # {"label": _("Income Account"), "fieldname": "income_account", "fieldtype": "Data", "width": 200},
        {"label": _("Gross Sales"), "fieldname": "gross_sales", "fieldtype": "Currency", "options": "currency", "width": 180},
        {"label": _("Sales Expense %"), "fieldname": "expense_percentage", "fieldtype": "percent", "options": "currency", "width": 180},
        {"label": _("Sales Amount"), "fieldname": "sales_amount", "fieldtype": "Currency", "options": "currency", "width": 180},
        {"label": _("Net Sales Amount"), "fieldname": "net_sales", "fieldtype": "Currency", "options": "currency", "width": 180},
        {"label": _("Percentage"), "fieldname": "percentage", "fieldtype": "Data", "width": 100},
        {"label": _("Net Commission"), "fieldname": "net_commission", "fieldtype": "Currency", "options": "currency", "width": 150}
    ]


def get_item_group_data(filters):
    conditions = "where si.docstatus = 1"
    if filters.get("ref_practitioner"):
        conditions += " and si.ref_practitioner = %(ref_practitioner)s"
    if filters.get("from_date"):
        conditions += " and si.posting_date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " and si.posting_date <= %(to_date)s"
    
    return frappe.db.sql(
        f"""
        select sum(sii.net_amount) as net_sales, sii.item_group
        from `tabSales Invoice Item` sii
        join `tabSales Invoice` si on si.name = sii.parent
        {conditions}
        group by sii.item_group
        """,
        filters,
        as_dict=True
    )



import frappe
from erpnext.accounts.report.item_wise_sales_register.item_wise_sales_register import execute as item_sales_register_execute

def execute(filters=None):
    # You can pass filters directly or modify them
    columns, data = item_sales_register_execute(filters)
    
    # Optionally filter or modify data here
    filtered_data = [row for row in data if row[3] == "Some Item Code"]

    return columns, filtered_data

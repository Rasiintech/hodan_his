import frappe
from frappe import _, msgprint
from frappe.utils import flt

def execute(filters=None):
    if not filters:
        filters = {}
    
    if not filters.get("ref_practitioner"):
        msgprint(_("Please select a doctor to generate the report."), raise_exception=True)
    
    income_accounts = get_income_accounts(filters)
    columns = get_columns()
    
    if not income_accounts:
        msgprint(_("No income accounts found for the selected doctor."))
        return columns, []
    
    data = []
    for account in income_accounts:
        data.append({
            "income_account": account.income_account,
            "total_amount": account.total_amount
        })
    
    return columns, data

def get_columns():
    return [
        {"label": _( "Income Account"), "fieldname": "income_account", "fieldtype": "Data", "width": 250},
        {"label": _( "Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "options": "currency", "width": 150}
    ]

def get_income_accounts(filters):
    conditions = "where si.docstatus = 1"
    if filters.get("ref_practitioner"):
        conditions += " and si.ref_practitioner = %(ref_practitioner)s"
    if filters.get("from_date"):
        conditions += " and si.posting_date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " and si.posting_date <= %(to_date)s"
    
    return frappe.db.sql(
        f"""
        select sii.income_account, sum(sii.base_net_amount) as total_amount
        from `tabSales Invoice Item` sii
        join `tabSales Invoice` si on si.name = sii.parent
        {conditions}
        group by sii.income_account
        """,
        filters,
        as_dict=True
    )

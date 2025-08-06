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
    for item_group_record in item_group_data:
        for commission in commission_data:
            if item_group_record.item_group == commission["item_group"]:
                original_total = item_group_record.total_amount
                adjusted_total = original_total - (original_total * 0.25)
                net_commission = adjusted_total * (commission["percentage"] / 100)
                
                data.append({
                    "income_account": commission["income_account"],
                    "item_group": commission["item_group"],
                    "total_amount": adjusted_total,
                    "percentage": commission["percentage"],
                    "net_commission": net_commission
                })
    
    return columns, data


def get_columns():
    return [
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 150},
        {"label": _("Income Account"), "fieldname": "income_account", "fieldtype": "Data", "width": 200},
        {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "options": "currency", "width": 180},
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
        select sum(sii.net_amount) as total_amount, sii.item_group
        from `tabSales Invoice Item` sii
        join `tabSales Invoice` si on si.name = sii.parent
        {conditions}
        group by sii.item_group
        """,
        filters,
        as_dict=True
    )

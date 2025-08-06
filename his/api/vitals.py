import frappe
from frappe.utils import pretty_date, now, add_to_date




@frappe.whitelist()
def get_vital(patient):
    return frappe.db.sql(f""" Select MID(modified,1,19) as modified,
        temperature, pulse ,
        bp,respiratory_rate,
        height as height,
        weight,bmi, nutrition_note , owner, spo
        from `tabVital Signs` where patient ='{patient}' Order by modified desc
         """, as_dict=True
       
        )

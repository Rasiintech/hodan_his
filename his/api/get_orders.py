import frappe
from frappe.utils import pretty_date, now, add_to_date , getdate

defalts={}
userdata = {}
if frappe.db.exists('User Defaults', frappe.session.user):
    userdata=frappe.get_doc('User Defaults', frappe.session.user)
if userdata:
    for i in userdata.user_defaults:
        defalts[f'{i.doctype_party}'] = i.value

def has_role(user, role):
    roles = frappe.get_roles(user)
    return role in roles


# condition = ''
# if has_role(frappe.session.user , "Pharmacy"):
#     condition += "and so_type = 'Pharmacy'"
# elif has_role(frappe.session.user , "Cashier"):
#     condition += "and so_type = 'Cashiers'"
# if frappe.session.user == "Administrator":
#     condition = ''
@frappe.whitelist()
def get_opd_orders(currdate):
    condition = ''
    if has_role(frappe.session.user , "Pharmacy"):
        condition += "and so_type = 'Pharmacy'"
    elif has_role(frappe.session.user , "Cashier"):
        condition += "and so_type = 'Cashiers'"
    if frappe.session.user == "Administrator":
        condition = ''
        
 
    # frappe.errprint(condition)
 
    return frappe.db.sql(f""" Select name,
        patient, patient_name ,
        transaction_date,status,
        customer,
        modified as modified,
        per_billed,
        s.group,
        full_name,
        ref_practitioner,total ,allow_credit
        from `tabSales Order`s
        where  transaction_date='{currdate}' {condition} 
         ORDER BY modified DESC """, as_dict=True
       
        )

    
@frappe.whitelist()
def get_canteen_orders(currdate):
    condition = ''
    if has_role(frappe.session.user , "Pharmacy"):
        condition += "and so_type = 'Pharmacy'"
    elif has_role(frappe.session.user , "Cashier"):
        condition += "and so_type = 'Cashiers'"
    if frappe.session.user == "Administrator":
        condition = ''
        
 
    # frappe.errprint(condition)
 
    return frappe.db.sql(f""" Select name,
        customer, customer_name ,
        transaction_date,status,
        modified as modified,
        per_billed,
        ref_practitioner,total 
        from `tabSales Order`
        where source_order= "Canteen" and transaction_date='{currdate}' {condition}
         ORDER BY modified DESC """, as_dict=True
       
        )

@frappe.whitelist()
def get_que_em(currdate):

    return frappe.db.sql(f""" Select name,
        patient, patient_name ,
        date,
        department,   
        district,
        mobile,
        age,
        practitioner,

        modified as modified
      
        from `tabQue`
        where   date='{currdate}' 
         ORDER BY modified DESC """, as_dict=True
       
        )



@frappe.whitelist()
def get_ipd_orders(currdate):
    condition = ''
    if has_role(frappe.session.user , "Pharmacy"):
        condition += "and so_type = 'Pharmacy'"
    elif has_role(frappe.session.user , "Cashier"):
        condition += "and so_type = 'Cashiers'"
    if frappe.session.user == "Administrator":
        condition = ''


    return frappe.db.sql(f""" Select name,
        patient, patient_name ,
        transaction_date,status,
        modified as modified,
        per_billed,
        ref_practitioner,total 
        from `tabSales Order`
        where  transaction_date='{currdate}' and status != "Completed"  {condition} 
        ORDER BY modified DESC """, as_dict=True
       
        )


@frappe.whitelist()
def get_em_orders(currdate):
    condition = ''
    if has_role(frappe.session.user , "Pharmacy"):
        condition += "and so_type = 'Pharmacy'"
    elif has_role(frappe.session.user , "Cashier"):
        condition += "and so_type = 'Cashiers'"
    if frappe.session.user == "Administrator":
        condition = ''


    return frappe.db.sql(f""" Select name,
        patient, patient_name ,
        transaction_date,status,
        modified as modified,
        per_billed,
        ref_practitioner,total 
        from `tabSales Order`
        where source_order= "E.R"  and transaction_date='{currdate}' {condition} 
        ORDER BY modified DESC """, as_dict=True
       
        )

import frappe
from erpnext.stock.get_item_details import get_pos_profile
from his.api.make_invoice import make_sales_invoice_direct
from his.api.make_invoice import make_credit_invoice

def create_que_order_bill(doc):
    company = frappe.defaults.get_user_default("company")
    pos_profile = get_pos_profile(company)
    mode_of_payment = "Cash"
    if doc.paid_amount:
        mode_of_payment = doc.mode_of_payment
        default_account = frappe.db.get_value('Mode of Payment Account', {"parent": mode_of_payment},  'default_account')
    # mode_of_payment = "Cash"
    
    customer = frappe.db.get_value("Patient" , doc.patient , "customer")
    if doc.bill_to:
         customer = frappe.db.get_value("Patient" , doc.patient , "customer")

    items = []
    # empty_items = ""
    # for item in self.items:

    items.append({
            "item_code" : "OPD Consultation",
            "rate" : doc.doctor_amount,
            "qty" : 1,
            
        })



        
    
    


    sales_doc = frappe.get_doc({
        "doctype" : "Sales Order",
        
        "transaction_date" : doc.date,
        "customer": customer,
        "patient" : doc.patient,
    
        # "discout_amount" : doc.discount_amount,
        
        "voucher_no" : doc.name,
        "source_order" : "OPD",
        "ref_practitioner" : doc.practitioner,
        # "additional_discount_percentage": self.additional_discount_percentage,
        "items" : items,
    
    })

    sales_doc.insert()
    sales_doc.submit()
    sale_inv = make_sales_invoice_direct(sales_doc.name , doc.paid_amount , mode_of_payment , doc.reference)
    
    doc.sales_order  = sales_doc.name
    doc.sales_invoice = sale_inv
    doc.save()
    return sales_doc




def create_inp_order_bill(doc):
    company = frappe.defaults.get_user_default("company")

    # mode_of_payment = "Cash"
    
    customer = frappe.db.get_value("Patient" , doc.patient , "customer")
    items = []
    # empty_items = ""
    # for item in self.items:

    items.append({
            "item_code" : "OPD Consultation",
            "rate" : doc.doctor_amount,
            "qty" : 1,
            
        })



        
    
    


    sales_doc = frappe.get_doc({
        "doctype" : "Sales Order",
        "so_type": "Cashiers",
        "transaction_date" : doc.date,
        "customer": customer,
        "patient" : doc.patient,
    
        # "discout_amount" : doc.discount_amount,
        
        "voucher_no" : doc.name,
        "source_order" : "OPD",
        "ref_practitioner" : doc.practitioner,
        # "additional_discount_percentage": self.additional_discount_percentage,
        "items" : items,
    
    })

    sales_doc.insert()
    sales_doc.submit()
    sale_inv = make_sales_invoice_direct(sales_doc.name , doc.paid_amount)
    
    doc.sales_order  = sales_doc.name
    doc.sales_invoice = sale_inv
    doc.save()
    return sales_doc




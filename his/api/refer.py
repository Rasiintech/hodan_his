import frappe
@frappe.whitelist()
def refer(**args):
    q = frappe.get_doc({
    "doctype" : "Que",
    "patient": args.get('patient'),
    "practitioner": args.get('practitioner'),
   
  
    "emergency": args.get('name'),
    "date" : frappe.utils.getdate(),
    "que_type" : "Refer",
    "paid_amount" : 0
    
        
                    
    })           
    q.insert(ignore_permissions=1) 

@frappe.whitelist()
def refer_out_side(docname , practitioner,to,rtype,patient,request):
   # pre_app = frappe.get_doc("Patient Appointment" , docname)
    new_app = frappe.get_doc({
        "doctype" : "Referral Form",
        "patient" : patient,
        "referred_by" : practitioner,
        "to": to,
        "rtype": rtype,
        "requested": request,
    
         
    })
    new_app.insert(ignore_permissions = True)
    return "Success"



@frappe.whitelist()
def refer_from_doctor(patient,request, type,ref_practitioner, rtype = None,to=None,practitioner = None):
   # pre_app = frappe.get_doc("Patient Appointment" , docname)
    new_refer = frappe.get_doc({
        "doctype" : "Referral Form",
        "patient" : patient,
        "referred_by" :ref_practitioner,
        "referred_to" : practitioner,
        "to" : to,
        "rtype": rtype,
        "requested": request
         
    })
    
    new_refer.insert(ignore_permissions = True)
    if type == 'Internal' and practitioner != "Walk In Doctor":
        q = frappe.get_doc({
        "doctype" : "Que",
        "patient": patient,
        "practitioner": practitioner,
        "refer_request" : request,
        "referring_practitioner": ref_practitioner,
        "date" : frappe.utils.getdate(),
        "que_type" : "Refer", 
            "paid_amount" : 0             
        })           
        q.insert(ignore_permissions=1) 
     
        
    if type == 'E.R':
        emergency = frappe.get_doc({
        "doctype" : "Emergency",
        "patient": patient,
        "ref_practitioner": ref_practitioner,
        "request":request
             
        })           
        emergency.insert(ignore_permissions=1) 
    return new_refer


import frappe
from frappe.utils import pretty_date, now, add_to_date




@frappe.whitelist()
def sendsms():
    tomorow = frappe.utils.add_to_date(frappe.utils.getdate(), days=1 )
    followUp = frappe.db.get_list("Fee Validity", filters={"valid_till":tomorow}, fields=['patient', 'practitioner'])
    # msg=''
    total=0
    # fromat_date = frappe.utils.formatters.format_value("2021-10-30" , "Date")

    if followUp:
        for i in followUp:
            mobile= frappe.db.get_value("Patient", i.patient, "mobile")
            patient = frappe.db.get_value("Patient", i.patient, "patient_name")
            
            if mobile:
                frappe.call("frappe.core.doctype.sms_settings.sms_settings.send_sms", 
                msg= f""" {patient}, waxaan ku xasuusinaynaa in la gaaray xiligii aad  lahayd ballanta  soo noqoshada {i.practitioner} Taariikhda: {tomorow}. Fadlan soo qaado (Dokumentiyada Muhiimka ah) Waad ku mahadsan tahay inaad nagu dooratay daryeel caafimaad oo sax ah.
                        ISBITAALKA BARAKA """,  
                        receiver_list= [mobile])
                
              
              
              
                return followUp



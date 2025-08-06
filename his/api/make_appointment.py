import frappe
import requests
import time
import psutil

@frappe.whitelist()
def get_doctors():
    # Fetch all healthcare practitioners (doctors) with their name, charges, department, and image
    doctors = frappe.get_all(
        "Healthcare Practitioner",
        filters={"status": "Active",  "hide_doctor": 0},
        fields=["practitioner_name", "op_consulting_charge", "department", "image", "services" , "experience", "available_time"]
    )
    if not doctors:
        frappe.response['message'] = {"Data": []}
        
    # Get the first non-loopback IPv4 address
    eth_ip = next(
            (addr.address for addrs in psutil.net_if_addrs().values()
            for addr in addrs if addr.family == 2 and addr.address != "127.0.0.1"),
            None  # Default to None if no valid IP is found
        )
    # Format the image URLs if available
    system_host_url = f"http://{eth_ip}"


    for doctor in doctors:
         if doctor.image:
                # Ensure image starts with /files/ and add a cache-busting query parameter
                if not doctor.image.startswith('/files/'):
                    doctor.image = f"/files/{doctor.image}"
                doctor.image = f"{system_host_url}{doctor.image}?v={int(time.time())}"
         else:
            doctor.image = None  # If no image, set it to None

    frappe.response['message'] = {"Data": doctors}

@frappe.whitelist()
def check_patient():
    mobile = frappe.form_dict.get('mobile')

    patient = frappe.get_list("Patient", filters={"mobile": mobile}, fields=["name"])
    if not patient:
        frappe.response['message'] = "Patient was not registered. Register now" 
    else:
        frappe.response['message'] = "Patient is registered."

@frappe.whitelist()
def make_appointment():
    mobile = frappe.form_dict.get('mobile')

    patient = frappe.get_list("Patient", filters={"mobile": mobile}, fields=["name"])
    if not patient:
        frappe.response['message'] = "Patient was not registered. Register now"
    else:
        # patient = "PID-00001"
        patient_name = patient[0].get("name")
        doctor = frappe.form_dict.doctor
        date = frappe.form_dict.date
        
        visit_charge = frappe.db.get_value("Healthcare Practitioner" , doctor, 'op_consulting_charge')
        que_doc = frappe.new_doc("Que")
        que_doc.patient = patient_name
        que_doc.practitioner = doctor
        que_doc.payable_amount = visit_charge
        que_doc.mode_of_payment = "Cash"
        que_doc.source =  "Mobile App"
        que_doc.cost_center = "Main - HH" 
        # que_doc.insert()
        que_doc.insert(ignore_mandatory=True)
        
        frappe.response['message'] = "Booked Successfully."
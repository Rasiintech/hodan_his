
import json

import frappe
from frappe import _
from frappe.desk.reportview import get_match_cond
from frappe.model.document import Document
from frappe.utils import get_datetime, get_link_to_form, getdate, now_datetime, today

from healthcare.healthcare.doctype.nursing_task.nursing_task import NursingTask
from healthcare.healthcare.utils import validate_nursing_tasks







@frappe.whitelist()
def schedule_inpatient(args):
    admission_order = json.loads(args)  # admission order via Encounter
    frappe.errprint(admission_order)
    if (
        not admission_order
        or not admission_order["patient"]
        # or not admission_order["admission_encounter"]
    ):
        frappe.throw(_("Missing required details, did not create Inpatient Record"))

    inpatient_record = frappe.new_doc("Inpatient Record")

    # Admission order details
    # set_details_from_ip_order(inpatient_record, admission_order)

    # Patient details
    patient = frappe.get_doc("Patient", admission_order["patient"])
    inpatient_record.patient = patient.name
    inpatient_record.patient_name = patient.patient_name
    inpatient_record.gender = patient.sex
    inpatient_record.blood_group = patient.blood_group
    inpatient_record.dob = patient.dob
    inpatient_record.mobile = patient.mobile
    inpatient_record.email = patient.email
    inpatient_record.phone = patient.phone
    inpatient_record.scheduled_date = today()

    # Set encounter details
    # encounter = frappe.get_doc("Patient Encounter", admission_order["admission_encounter"])
    # if encounter and encounter.symptoms:  # Symptoms
    # 	set_ip_child_records(inpatient_record, "chief_complaint", encounter.symptoms)

    # if encounter and encounter.diagnosis:  # Diagnosis
    # 	set_ip_child_records(inpatient_record, "diagnosis", encounter.diagnosis)

    # if encounter and encounter.drug_prescription:  # Medication
    # 	set_ip_child_records(inpatient_record, "drug_prescription", encounter.drug_prescription)

    # if encounter and encounter.lab_test_prescription:  # Lab Tests
    # 	set_ip_child_records(inpatient_record, "lab_test_prescription", encounter.lab_test_prescription)

    # if encounter and encounter.procedure_prescription:  # Procedure Prescription
    # 	set_ip_child_records(
    # 		inpatient_record, "procedure_prescription", encounter.procedure_prescription
    # 	)

    # if encounter and encounter.therapies:  # Therapies
    # 	inpatient_record.therapy_plan = encounter.therapy_plan
    # 	set_ip_child_records(inpatient_record, "therapies", encounter.therapies)

    inpatient_record.status = "Admission Scheduled"

    inpatient_record.admission_practitioner= admission_order["primary_practitioner"]
    inpatient_record.diagnose= admission_order["diagnosis"]




    inpatient_record.save(ignore_permissions=True)


    customer = frappe.db.get_value("Patient", inpatient_record.patient, "customer" )
    patient_name = frappe.db.get_value("Patient", inpatient_record.patient, "patient_name" )
    if not frappe.db.exists("Customer Group", patient_name+ "."):
        customer_group = frappe.get_doc({
            'doctype' : "Customer Group" ,
            'customer_group_name' : patient_name + ".",
            'debtor_type' : 'Inpatient' ,
            'debtor_type' : 'Inpatient', 
            'patient' : inpatient_record.patient,
            'patient_name' : patient_name,

        })
        customer_group.insert(ignore_permissions=1)
        # frappe.errprint(patient_name)

        Customer_doc = frappe.get_doc('Customer', customer)
        Customer_doc.customer_group= customer_group.name
        Customer_doc.save()
    else:
        customer_group= frappe.get_doc("Customer Group", patient_name+ ".")
        if customer_group.status== "Closed":
            customer_group.status= "Active"
            customer_group.save()
        Customer_doc = frappe.get_doc('Customer', customer)
        Customer_doc.customer_group= customer_group.name

        Customer_doc.save()


@frappe.whitelist()
def cancel_admision(inp_doc):
    in_d = frappe.get_doc("Inpatient Record" , inp_doc)
    in_d.status = "Cancelled"
    in_d.save()

# Copyright (c) 2024, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.desk.reportview import get_match_cond
from frappe.model.document import Document
from frappe.utils import get_datetime, get_link_to_form, getdate, now_datetime, today

from healthcare.healthcare.doctype.nursing_task.nursing_task import NursingTask
from healthcare.healthcare.utils import validate_nursing_tasks

class AdmissionOrderingRequest(Document):

	def on_submit(self):
	
		inpatient_record = frappe.new_doc("Inpatient Record")
		patient = frappe.get_doc("Patient", self.patient)
		inpatient_record.patient = patient.name
		inpatient_record.patient_name = patient.patient_name
		inpatient_record.gender = patient.sex
		inpatient_record.blood_group = patient.blood_group
		inpatient_record.dob = patient.dob
		inpatient_record.type=self.type
		inpatient_record.mobile = patient.mobile
		inpatient_record.email = patient.email
		inpatient_record.phone = patient.phone
		inpatient_record.scheduled_date = today()
		inpatient_record.status = "Admission Scheduled"
		inpatient_record.admission_practitioner= self.practitioner
		inpatient_record.diagnose= self.diagnose
		record = inpatient_record.save(ignore_permissions=True)
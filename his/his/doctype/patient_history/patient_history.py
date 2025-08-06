# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PatientHistory(Document):
	pass


@frappe.whitelist()
def refer(inpatient_record, practitioner):
	inpatient_rec = frappe.get_doc('Inpatient Record', inpatient_record)
	inpatient_rec.primary_practitioner = practitioner
	inpatient_rec.admission_practitioner = practitioner
	inpatient_rec.secondary_practitioner = practitioner
	inpatient_rec.discharge_practitioner = practitioner
	inpatient_rec.save(ignore_permissions=1 )
	
	return "Refered Successfully"


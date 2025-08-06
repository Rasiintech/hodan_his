# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt
import datetime
import frappe
from frappe.model.document import Document
from his.api.make_order import set_so_values_from_db
from his.api.make_order import enqueue_sales_orders

class Emergency(Document):
	def before_validate(self):
		set_so_values_from_db(self)
	
	def on_update(self):
		enqueue_sales_orders(self)
	def on_update_after_submit(self):
		enqueue_sales_orders(self)

@frappe.whitelist()
def transfer(**args):
	# frappe.db.set_value("Healthcare Service Unit", service_unit, "occupancy_status", "Vacant")
	# name.service_unit=service_unit
	inp = frappe.get_doc({
		'doctype': 'Inpatient Record',
		'patient': args.get('patient'),
		'diagnose': args.get('diagnose'),
		"admission_practitioner": args.get('practitioner'),
		"status":"Admission Scheduled"
		})
	inp.insert(ignore_permissions = True)
	frappe.db.set_value("Emergency", args.get('name'), "status", "Transferred")
	
@frappe.whitelist() 
def make_ot_schedule(docname, procedure, method=None):
    current_datetime = datetime.datetime.now()
    doc = frappe.get_doc("Emergency", docname)
    ot_schedule = frappe.get_doc({
            'doctype': 'OT Schedule',
            'patient': doc.patient,
            "appointment_date" : current_datetime.date(),
            "appointment_time": current_datetime.time(),
            "company":frappe.defaults.get_user_default("company"),
            "practitioner": doc.practitioner,
            "duration": 15,
            "procedure_template":procedure,
            "status": "Scheduled"
            
            })
    ot_schedule.insert(ignore_permissions = True)



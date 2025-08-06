# Copyright (c) 2024, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from his.api.inpatient_order import set_so_values_from_db
from his.api.inpatient_order import enqueue_sales_orders


class HealthcareRequests(Document):
	def before_validate(self):
		pass
		# set_so_values_from_db(self)
	
	def on_update(self):
		# pass
		enqueue_sales_orders(self)
		if self.source_order:
			frappe.db.set_value('Emergency Triage', self.source_order, 'requests', "E.R")
		if self.opthalmology:
			frappe.db.set_value('opthalmology exam form', self.opthalmology, 'opthalmology', self.name)
		if self.obs:
			frappe.db.set_value('OBS-GYN AND OPD', self.obs, 'obs', self.name)

			# frappe.db.set_value("Emergency Triage", )
	
	def on_update_after_submit(self):
		pass
		enqueue_sales_orders(self)

	# def on_submit(self):
	# 	enqueue_sales_orders(self)
		# pass
		# Call function to update the Doctor Plan
		# update_doctor_plan(self)
	def on_cancel(self):
		# if self.medication_so:
		# 	sales_drug=frappe.get_doc("Sales Order",self.medication_so)
		# 	sales_drug.cancel()
		if self.services_so:
			sales_service=frappe.get_doc("Sales Order",self.services_so)
			sales_service.cancel()


		# enqueue_sales_orders(self)
















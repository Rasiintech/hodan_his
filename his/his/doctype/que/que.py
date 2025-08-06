# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from his.api.Que_to_make_sales_invove import make_invoice
from his.api.Que_to_fee_validity import make_fee_validity
from his.api.que_token_number import token_numebr
# from his.api.order_to_bill import create_que_order_bill
from rasiin_healthcare_insurance.api.que import create_que_order_bill
class Que(Document):
	def before_insert(self):
		# pass
		token_numebr(self)
	def on_update(self):
		event = "que_update"

		frappe.publish_realtime(event)

	def after_insert(self):
		# frappe.errprint(self.workflow_state)
		if self.que_type != 'Refer' and not self.is_free and  not self.follow_up and   self.que_type !="Renew" and self.que_type !="Revisit" and self.doctor_amount > 0:
			# create_que_order_bill(self)
			# make_invoice(self)
			create_que_order_bill(self)
		
		if self.que_type=="New Patient" or self.que_type== "Refer" or self.que_type== "Refer With Payment":
				make_fee_validity(self)
		
		# if self.workflow_state == "Approved":
		# 	if self.que_type != 'Refer' and not self.is_free and  not self.follow_up and   self.que_type !="Renew" and self.que_type !="Revisit":
		# 		# create_que_order_bill(self)
		# 		# make_invoice(self)
		# 		create_que_order_bill(self)
		# 	# pass
		# if self.que_type=="New Patient" or self.que_type== "Refer":
		# 		make_fee_validity(self)
			
		# make_invoice(self)
			
	#def before_save(self):
		#doc=self
		#if not doc.discount:
		#	doc.discount = 0
		#is_gr = frappe.db.get_value("Customer Group",  frappe.db.get_value("Customer", doc.customer, "customer_group"), "is_group")
		#if is_gr and doc.paid_amount<(doc.doctor_amount - doc.discount) and doc.que_type=="New Patient" and  doc.is_free==0 and not doc.bill_to:
			#frappe.throw("This Patient is not linked with valid Debtor!")
			








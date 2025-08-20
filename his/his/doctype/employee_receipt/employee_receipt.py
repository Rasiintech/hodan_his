# Copyright (c) 2024, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from his.api.get_mode_of_payments import mode_of_payments
from erpnext.stock.get_item_details import get_pos_profile
from erpnext.accounts.utils import get_balance_on
from frappe.model.document import Document

class EmployeeReceipt(Document):
	def on_submit(self):
		account=[]
		his_settings = frappe.get_doc("HIS Settings", "HIS Settings")
		if his_settings.discount_account:
			discount_account= his_settings.discount_account
		doc = self	
		if not doc.paid_amount > doc.balance and not doc.discount_amount:
  
			account = [
				{
					"account": doc.paid_from,
					'party_type': "Employee",
					"party" : doc.employee,
					"credit_in_account_currency": doc.paid_amount
				},
				{
					"account": doc.paid_to,
					"debit_in_account_currency": doc.paid_amount,
				},
			]
		if not doc.paid_amount > (doc.balance - doc.discount_amount) and doc.discount_amount:
  
			account = [
				{
					"account": doc.paid_from,
					'party_type': "Employee",
					"party" : doc.employee,
					"credit_in_account_currency": doc.paid_amount + doc.discount_amount,
					 "cost_center": doc.cost_center		
				},
				{
					"account": doc.paid_to,
					"debit_in_account_currency": doc.paid_amount,
					"cost_center": doc.cost_center
				},
				{
					"account": discount_account,
					"debit_in_account_currency": doc.discount_amount,
					"cost_center": doc.cost_center
				},
			]
   
			# frappe.errprint(account)
		if account:
			Journal = frappe.get_doc({
					'doctype': 'Journal Entry',
					'voucher_type': 'Journal Entry',
					"posting_date" : doc.date,
					"user_remark": doc.remarks,
					"accounts": account,
					"employee_receipt" : doc.name
					
				})
			Journal.insert(ignore_permissions = True)
			Journal.submit()
		else:
			frappe.throw('Paid amount is greater then employee Balance')
	def on_cancel(self):
		doc=self
		if frappe.db.get_value("Journal Entry", {"employee_receipt": doc.name}, "name"):
			journal= frappe.get_doc("Journal Entry",frappe.db.get_value("Journal Entry", {"employee_receipt": doc.name}, "name"))
			if journal.docstatus==1:
				journal.cancel()


	 
	 
	 
@frappe.whitelist()
def get_account():
	pos_profile = get_pos_profile(frappe.defaults.get_user_default("company"))
	mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
	account= frappe.get_doc("Mode of Payment", mode_of_payment)
	acc= account.accounts[0].default_account

		
	return  acc
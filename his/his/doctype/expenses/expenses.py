# Copyright (c) 2021, Rasiin and contributors
# For license information, please see license.txt
from erpnext.stock.get_item_details import get_pos_profile

import frappe
from frappe.model.document import Document

class Expenses(Document):
	@frappe.whitelist()
	def mode_of_payments(company):
		pos_profile = get_pos_profile(company)
		mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
		default_account = frappe.db.get_value('Mode of Payment Account', {"parent": mode_of_payment},  'default_account')
		return default_account
	
	def on_submit(self):

		account = [
			
		{
			"account":self.account,
			"debit_in_account_currency":self.amount,
			"source_order" : self.source_order,
		},
		{
			"account":self.paid_from,
			"credit_in_account_currency":self.amount,	
			"source_order" : self.source_order,
		},
   ]
		doc = frappe.get_doc({
		'doctype': 'Journal Entry',
		'voucher_type': 'Journal Entry',
		"posting_date" : self.date,
		"user_remark":self.remark,
		"accounts": account
		
		})
		doc.insert(ignore_permissions = True)
		doc.submit()
		self.journal_entry = doc.name
		self.save()
	def on_cancel(self):
		# frappe.throw(('This is an Error Message'))
		journal = frappe.get_doc("Journal Entry" , self.journal_entry)
		journal.cancel()

# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from erpnext.accounts.utils import get_balance_on
from frappe.model.document import Document
from frappe.utils import money_in_words


class PaymentVoucher(Document):
	def validate(self):
		self.amount_in_words = money_in_words(self.amount or 0, self.currency)
		self.vendor_balance = get_supplier_net_balance(self.supplier, self.posting_date)

		if self.payment_method == "Cash":
			self.bank_name = None
			self.cheque_no = None
		elif self.payment_method == "Cheque":
			self.cash_no = None


@frappe.whitelist()
def get_supplier_net_balance(supplier=None, posting_date=None):
	if not supplier:
		return None

	company = frappe.defaults.get_user_default("Company")
	if not company:
		return None

	return get_balance_on(
		party_type="Supplier",
		party=supplier,
		company=company,
		date=posting_date,
		in_account_currency=False,
	)

# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_balance_on


class CustomerBalanceTransfer(Document):
	def validate(self):
		self.set_missing_values()
		self.validate_transfer()

	def on_submit(self):
		self.set_missing_values()
		self.validate_transfer()
		journal_entry = self.make_journal_entry()
		self.db_set("journal_entry", journal_entry.name)

	def on_cancel(self):
		if not self.journal_entry:
			return

		journal_entry = frappe.get_doc("Journal Entry", self.journal_entry)
		if journal_entry.docstatus == 1:
			journal_entry.cancel()

	def set_missing_values(self):
		if not self.company:
			self.company = frappe.defaults.get_user_default("company")

		if not self.source_account:
			self.source_account = get_balance_transfer_account("Customer", self.source_customer, self.company)

		if self.target_party_type and self.target_party and not self.target_account:
			self.target_account = get_balance_transfer_account(
				self.target_party_type,
				self.target_party,
				self.company,
			)

		self.source_balance = get_party_balance("Customer", self.source_customer, self.company, self.source_account)
		if self.target_party_type and self.target_party:
			self.target_party_name = get_party_display_name(self.target_party_type, self.target_party)
			self.target_balance = get_party_balance(
				self.target_party_type,
				self.target_party,
				self.company,
				self.target_account,
			)
		else:
			self.target_party_name = None

	def validate_transfer(self):
		settings = frappe.get_doc("HIS Settings", "HIS Settings")
		if not settings.allow_transfer_balance:
			frappe.throw(_("Transfer Balance is not allowed in HIS Settings"))

		if not self.company:
			frappe.throw(_("Company is required"))

		if not self.source_customer:
			frappe.throw(_("Source Customer is required"))

		if not self.target_party_type or not self.target_party:
			frappe.throw(_("Target Party is required"))

		if self.target_party_type not in ("Customer", "Employee", "Supplier"):
			frappe.throw(_("Target Party Type must be Customer, Employee, or Supplier"))

		if self.target_party_type == "Customer" and self.source_customer == self.target_party:
			frappe.throw(_("Source Customer and Target Customer cannot be the same"))

		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero"))

		if flt(self.discount_amount) < 0:
			frappe.throw(_("Discount Amount cannot be negative"))

		if not self.source_account:
			frappe.throw(_("Source Account is required"))

		if not self.target_account:
			frappe.throw(_("Target Account is required"))

		total_reduction = flt(self.amount) + flt(self.discount_amount)
		if flt(self.source_balance) > 0 and total_reduction > flt(self.source_balance):
			frappe.throw(_("Transfer amount plus discount cannot be greater than Source Customer Balance"))

	def make_journal_entry(self):
		total_source_credit = flt(self.amount) + flt(self.discount_amount)
		accounts = [
			{
				"account": self.target_account,
				"party_type": self.target_party_type,
				"party": self.target_party,
				"debit_in_account_currency": flt(self.amount),
			},
			{
				"account": self.source_account,
				"party_type": "Customer",
				"party": self.source_customer,
				"credit_in_account_currency": total_source_credit,
			},
		]

		if flt(self.discount_amount):
			accounts.append(
				{
					"account": get_discount_account(self.company),
					"debit_in_account_currency": flt(self.discount_amount),
				}
			)

		if self.cost_center:
			for row in accounts:
				row["cost_center"] = self.cost_center

		journal_entry = frappe.get_doc(
			{
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"company": self.company,
				"posting_date": self.date,
				"user_remark": self.get_user_remark(),
				"accounts": accounts,
			}
		)
		journal_entry.insert(ignore_permissions=True)
		journal_entry.submit()
		return journal_entry

	def get_user_remark(self):
		if self.remarks:
			return self.remarks

		return _("Customer balance transferred from {0} to {1} {2}").format(
			self.source_customer,
			self.target_party_type,
			self.target_party,
		)


def get_balance_transfer_account(party_type, party, company):
	if not party_type or not party or not company:
		return None

	if party_type == "Employee":
		settings = frappe.get_doc("HIS Settings", "HIS Settings")
		if settings.employee_receivable:
			return settings.employee_receivable

	if party_type == "Customer":
		settings = frappe.get_doc("HIS Settings", "HIS Settings")
		party_account = frappe.db.get_value(
			"Party Account",
			{"parenttype": "Customer", "parent": party, "company": company},
			"account",
		)
		if party_account:
			return party_account
		if settings.debtors_account:
			return settings.debtors_account

	return get_party_account(party_type, party, company)


def get_party_display_name(party_type, party):
	if not party_type or not party:
		return None

	fieldname_map = {
		"Customer": "customer_name",
		"Employee": "employee_name",
		"Supplier": "supplier_name",
	}
	display_field = fieldname_map.get(party_type)
	if not display_field:
		return party

	return frappe.db.get_value(party_type, party, display_field) or party


def get_discount_account(company):
	settings = frappe.get_doc("HIS Settings", "HIS Settings")
	if settings.discount_account:
		return settings.discount_account

	if company:
		abbr = frappe.db.get_value("Company", company, "abbr")
		if abbr:
			account_name = f"Discount - {abbr}"
			if frappe.db.exists("Account", account_name):
				return account_name

	if frappe.db.exists("Account", "Discount - HH"):
		return "Discount - HH"

	frappe.throw(_("Discount account is not configured in HIS Settings"))


def get_party_balance(party_type, party, company, account=None):
	if not party_type or not party or not company:
		return 0

	return flt(
		get_balance_on(
			party_type=party_type,
			party=party,
			company=company,
			account=account,
		)
	)


@frappe.whitelist()
def get_transfer_details(
	source_customer=None,
	source_account=None,
	target_party_type=None,
	target_party=None,
	target_account=None,
	company=None,
):
	company = company or frappe.defaults.get_user_default("company")

	source_account = source_account or (
		get_balance_transfer_account("Customer", source_customer, company) if source_customer else None
	)
	target_account = (
		target_account or get_balance_transfer_account(target_party_type, target_party, company)
		if target_party_type and target_party
		else None
	)

	return {
		"company": company,
		"source_account": source_account,
		"source_balance": get_party_balance("Customer", source_customer, company, source_account)
		if source_customer
		else 0,
		"target_account": target_account,
		"target_party_name": get_party_display_name(target_party_type, target_party)
		if target_party_type and target_party
		else None,
		"target_balance": get_party_balance(target_party_type, target_party, company, target_account)
		if target_party_type and target_party
		else 0,
	}

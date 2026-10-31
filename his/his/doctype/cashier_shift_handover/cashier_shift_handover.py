import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate

from erpnext.accounts.utils import get_balance_on


DEFAULT_COLLECTIONS = (
	"Merchant OPD 6 (734611)",
	"Evc-Plus",
	"E-Dahab (129131)",
	"Wallet - Premier (117584)",
	"Cash Available",
	"Salaam Bank",
	"Premier Bank",
	"T-Plus",
	"Cash Out",
)


class CashierShiftHandover(Document):
	def before_insert(self):
		if not self.cashier:
			self.cashier = get_user_pos_profile(self.company)
		if not self.cash_collections:
			for description in DEFAULT_COLLECTIONS:
				self.append("cash_collections", {"description": description})

	def validate(self):
		self.cashier_name = self.cashier
		self.update(get_cashier_account_details(self.cashier, self.company, self.posting_date))

		for row in self.cash_available:
			row.exchange = flt(row.cash_receipt) - flt(row.served)

		self.total_opening_balance = sum(flt(row.opening_balance) for row in self.cash_collections)
		self.total_collection_today = sum(flt(row.collection_today) for row in self.cash_collections)
		self.grand_total = self.total_opening_balance + self.total_collection_today
		self.total_cash_receipt = sum(flt(row.cash_receipt) for row in self.cash_available)
		self.total_served = sum(flt(row.served) for row in self.cash_available)
		self.total_exchange = sum(flt(row.exchange) for row in self.cash_available)
		self.total_withdraw = sum(flt(row.withdraw) for row in self.merchant_withdrawals)


@frappe.whitelist()
def get_user_pos_profile(company=None):
	filters = {"disabled": 0}
	if company:
		filters["company"] = company
	profiles = frappe.get_all(
		"POS Profile",
		filters={**filters, "name": ["in", frappe.get_all("POS Profile User", {"user": frappe.session.user}, pluck="parent")]},
		pluck="name",
		limit=1,
	)
	return profiles[0] if profiles else None


@frappe.whitelist()
def get_cashier_account_details(cashier, company, posting_date=None):
	details = {"mode_of_payment": None, "account": None, "account_balance": 0}
	if not (cashier and company):
		return details

	mode_of_payment = frappe.get_all(
		"POS Payment Method",
		filters={"parent": cashier, "parenttype": "POS Profile"},
		pluck="mode_of_payment",
		order_by="`default` desc, idx asc",
		limit=1,
	)
	if not mode_of_payment:
		return details

	details["mode_of_payment"] = mode_of_payment[0]
	details["account"] = frappe.db.get_value(
		"Mode of Payment Account", {"parent": mode_of_payment[0], "company": company}, "default_account"
	)
	if details["account"]:
		details["account_balance"] = flt(
			get_balance_on(account=details["account"], date=posting_date or nowdate(), company=company), 2
		)
	return details

import frappe
from frappe.model.document import Document
from frappe.utils import flt


DEFAULT_COLLECTIONS = (
	"Merchant OPD 4 (734609)",
	"Evc-Plus",
	"E-Dahab (129129)",
	"Wallet - Premier (016698)",
	"Cash Available",
	"Salaam Bank",
	"Premier Bank",
	"My-Cash OPD 4 (936736)",
	"E-Besa OPD 4",
	"T-Plus OPD 4",
	"Cash Out",
)


class CashierHandOver(Document):
	def before_insert(self):
		if not self.cashier:
			self.cashier = frappe.session.user
		if not self.cash_collections:
			for description in DEFAULT_COLLECTIONS:
				self.append("cash_collections", {"description": description})

	def validate(self):
		self.total_opening_balance = sum(flt(row.opening_balance) for row in self.cash_collections)
		self.total_collection_today = sum(flt(row.collection_today) for row in self.cash_collections)
		self.total_cash_receipt = sum(flt(row.cash_receipt) for row in self.cash_available)
		self.total_served = sum(flt(row.served) for row in self.cash_available)
		self.total_exchange = sum(flt(row.exchange) for row in self.cash_available)
		self.total_withdraw = sum(flt(row.withdraw) for row in self.merchant_report)
		self.net_cash_available = self.total_cash_receipt - self.total_served - self.total_exchange


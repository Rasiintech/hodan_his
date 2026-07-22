# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_first_day, nowdate


class SupplierPaymentPlan(Document):
	def validate(self):
		self.validate_rows()
		self.sync_row_balances()
		self.validate_plan_amounts()
		self.set_totals()

	def validate_rows(self):
		if not self.payment_schedule:
			frappe.throw(_("Add at least one supplier row."))

		seen_suppliers = set()

		for row in self.payment_schedule:
			if not row.supplier:
				frappe.throw(_("Row {0}: Supplier is required.").format(row.idx))

			if row.supplier in seen_suppliers:
				frappe.throw(_("Supplier {0} is selected more than once.").format(frappe.bold(row.supplier)))

			seen_suppliers.add(row.supplier)

	def sync_row_balances(self):
		for row in self.payment_schedule:
			row.balance_amount = get_supplier_outstanding_amount(
				row.supplier,
				self.company,
				self.plan_date,
			)
			row.last_month_credited = get_last_month_credited(
				row.supplier,
				self.company,
				self.plan_date,
			)
			row.balance_after_payment = flt(row.balance_amount) - flt(row.payment_amount)

	def validate_plan_amounts(self):
		total_balance = 0
		total_plan = 0

		for row in self.payment_schedule:
			if flt(row.balance_amount) <= 0:
				frappe.throw(
					_("Row {0}: Supplier {1} has no outstanding payable balance.")
					.format(row.idx, frappe.bold(row.supplier))
				)

			if flt(row.payment_amount) < 0:
				frappe.throw(_("Row {0}: Plan Amount cannot be negative.").format(row.idx))

			if flt(row.payment_amount) > flt(row.balance_amount):
				frappe.throw(
					_("Row {0}: Plan Amount cannot be greater than the supplier balance.")
					.format(row.idx)
				)

			total_balance += flt(row.balance_amount)
			total_plan += flt(row.payment_amount)

		if total_plan > total_balance:
			frappe.throw(_("Total Plan cannot be greater than Total Balance."))

	def set_totals(self):
		self.total_amount = sum(flt(row.balance_amount) for row in self.payment_schedule)
		self.total_scheduled_amount = sum(flt(row.payment_amount) for row in self.payment_schedule)
		self.balance_amount = flt(self.total_amount) - flt(self.total_scheduled_amount)


@frappe.whitelist()
def get_supplier_outstanding_amount(supplier, company, date=None):
	report_date = date or nowdate()
	rows = get_supplier_outstanding_rows(company=company, date=report_date, supplier=supplier)
	if not rows:
		return 0

	return abs(flt(rows[0].get("balance_amount")))


@frappe.whitelist()
def get_last_month_credited(supplier, company, plan_date=None):
	plan_date = plan_date or nowdate()
	current_month_start = get_first_day(plan_date)
	last_month_end = frappe.utils.add_days(current_month_start, -1)
	last_month_start = get_first_day(last_month_end)

	credited = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(amount), 0)
		FROM `tabPayment Ledger Entry`
		WHERE
			company = %(company)s
			AND party_type = 'Supplier'
			AND party = %(supplier)s
			AND delinked = 0
			AND posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND amount > 0
		""",
		{
			"company": company,
			"supplier": supplier,
			"from_date": last_month_start,
			"to_date": last_month_end,
		},
	)[0][0]

	return flt(credited)


@frappe.whitelist()
def get_supplier_plan_rows(company, date=None, supplier=None):
	rows = []

	for supplier_row in get_supplier_outstanding_rows(company=company, date=date, supplier=supplier):
		outstanding = abs(flt(supplier_row.get("balance_amount")))
		if outstanding <= 0:
			continue

		rows.append(
			{
				"supplier": supplier_row.get("supplier"),
				"balance_amount": outstanding,
				"last_month_credited": get_last_month_credited(
					supplier_row.get("supplier"),
					company,
					date,
				),
				"payment_amount": 0,
				"balance_after_payment": outstanding,
			}
		)

	return rows


def get_supplier_outstanding_rows(company, date=None, supplier=None):
	report_date = date or nowdate()

	conditions = [
		"ple.company = %(company)s",
		"ple.party_type = 'Supplier'",
		"ple.delinked = 0",
		"ple.posting_date <= %(report_date)s",
	]
	values = {
		"company": company,
		"report_date": report_date,
	}

	if supplier:
		conditions.append("ple.party = %(supplier)s")
		values["supplier"] = supplier

	return frappe.db.sql(
		f"""
		SELECT
			ple.party AS supplier,
			COALESCE(s.supplier_name, ple.party) AS supplier_name,
			SUM(ple.amount) AS balance_amount
		FROM `tabPayment Ledger Entry` ple
		LEFT JOIN `tabSupplier` s
			ON s.name = ple.party
		WHERE {" AND ".join(conditions)}
		GROUP BY ple.party, s.supplier_name
		HAVING ABS(SUM(ple.amount)) > 0.005
		ORDER BY SUM(ple.amount) DESC
		""",
		values,
		as_dict=True,
	)

# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate

DEFAULT_DISCOUNT_ACCOUNT = "4999001 - Patient Service Discounts - HH"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("account"):
		filters.account = DEFAULT_DISCOUNT_ACCOUNT

	months = get_months(filters)
	discounts = get_discount_data(filters)
	returns = get_cash_return_data(filters)

	columns = get_columns()
	data = build_rows(discounts, returns, months)
	chart = get_chart(discounts, returns, months)
	return columns, data, None, chart


def get_months(filters):
	# list of (month_key, label) from from_date to to_date
	start, end = getdate(filters.from_date), getdate(filters.to_date)
	multi_year = start.year != end.year
	months = []
	year, month = start.year, start.month
	while (year, month) <= (end.year, end.month):
		key = f"{year}-{month:02d}"
		label = getdate(f"{key}-01").strftime("%B %Y" if multi_year else "%B")
		months.append((key, label))
		if month == 12:
			year, month = year + 1, 1
		else:
			month += 1
	return months


def get_columns():
	return [
		{
			"label": _("Month"),
			"fieldname": "month",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Discount"),
			"fieldname": "discount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"label": _("Cash Sales Return"),
			"fieldname": "cash_sales_return",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
	]


def get_discount_data(filters):
	# net movement (debit - credit) on the discount account, per month
	conditions = [
		"gle.account = %(account)s",
		"gle.is_cancelled = 0",
		"gle.posting_date BETWEEN %(from_date)s AND %(to_date)s",
	]
	if filters.get("company"):
		conditions.append("gle.company = %(company)s")

	return frappe.db.sql(
		f"""
		SELECT
			DATE_FORMAT(gle.posting_date, '%%Y-%%m') AS month_key,
			SUM(gle.debit - gle.credit) AS amount
		FROM `tabGL Entry` gle
		WHERE {" AND ".join(conditions)}
		GROUP BY month_key
		HAVING amount != 0
		""",
		filters,
		as_dict=1,
	)


def get_cash_return_data(filters):
	# settled (refunded/adjusted) portion of return credit notes, shown positive
	conditions = [
		"si.docstatus = 1",
		"si.is_return = 1",
		"si.posting_date BETWEEN %(from_date)s AND %(to_date)s",
	]
	if filters.get("company"):
		conditions.append("si.company = %(company)s")

	return frappe.db.sql(
		f"""
		SELECT
			DATE_FORMAT(si.posting_date, '%%Y-%%m') AS month_key,
			SUM(si.outstanding_amount - si.base_grand_total) AS amount
		FROM `tabSales Invoice` si
		WHERE {" AND ".join(conditions)}
		GROUP BY month_key
		HAVING amount != 0
		""",
		filters,
		as_dict=1,
	)


def sum_by_month(rows, month_keys):
	totals = dict.fromkeys(month_keys, 0)
	for r in rows:
		if r.month_key in totals:
			totals[r.month_key] += r.amount
	return totals


def build_rows(discounts, returns, months):
	month_keys = [key for key, _label in months]
	discount_totals = sum_by_month(discounts, month_keys)
	return_totals = sum_by_month(returns, month_keys)

	data = []
	for key, label in months:
		data.append(
			frappe._dict(
				month=label,
				discount=discount_totals[key],
				cash_sales_return=return_totals[key],
			)
		)

	data.append(
		frappe._dict(
			month=_("Total"),
			discount=sum(discount_totals.values()),
			cash_sales_return=sum(return_totals.values()),
			bold=1,
		)
	)
	return data


def get_chart(discounts, returns, months):
	if not discounts and not returns:
		return None

	month_keys = [key for key, _label in months]
	discount_totals = sum_by_month(discounts, month_keys)
	return_totals = sum_by_month(returns, month_keys)

	return {
		"data": {
			"labels": [label for _key, label in months],
			"datasets": [
				{"name": _("Discount"), "values": [discount_totals[k] for k in month_keys]},
				{"name": _("Cash Sales Return"), "values": [return_totals[k] for k in month_keys]},
			],
		},
		"type": "bar",
		"colors": ["#7C44AD", "#FF8C00"],
	}

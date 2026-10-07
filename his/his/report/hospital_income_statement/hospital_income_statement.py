# Copyright (c) 2026, Hodan Hospital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.financial_statements import get_period_list

REVENUE_PARENT = "400000"
CONTRA_PARENT = "4999000"
EXPENSE_ROOT = "500000"
COGS_NUMBERS = ("510000", "520000")
TAX_NUMBER = "570012"

# Legacy (unnumbered) accounts folded into the numbered revenue groups,
# matching the Excel income statement layout.
LEGACY_REVENUE_MAP = {
	"E.R": "410000",
	"Cytology": "420000",
	"Imaging": "430000",
	"Radiology": "430000",
	"OT Sales": "440000",
	"Pharmacy Sales": "460000",
	"Procedures": "480000",
	"OPD Procedure": "480000",
	"Opd Procedures": "480000",
	"Other Procedures": "490000",
}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.company:
		filters.company = frappe.defaults.get_user_default("Company")

	period_list = get_periods(filters)
	accounts = get_accounts(filters.company)
	balances = get_balances(filters, period_list)

	columns = get_columns(filters, period_list)
	data = build_data(period_list, accounts, balances)

	currency = frappe.get_cached_value("Company", filters.company, "default_currency")
	for row in data:
		if row:
			row["currency"] = currency

	return columns, data


def get_periods(filters):
	from_fy = frappe.get_value(
		"Fiscal Year", {"year_start_date": ["<=", filters.from_date]}, "name", order_by="year_start_date desc"
	)
	to_fy = frappe.get_value(
		"Fiscal Year", {"year_start_date": ["<=", filters.to_date]}, "name", order_by="year_start_date desc"
	)
	return get_period_list(
		period_start_date=filters.from_date,
		period_end_date=filters.to_date,
		from_fiscal_year=from_fy,
		to_fiscal_year=to_fy,
		periodicity=filters.periodicity or "Monthly",
		company=filters.company,
		filter_based_on="Date Range",
	)


def get_accounts(company):
	accounts = frappe.db.sql(
		"""
		select name, account_name, account_number, root_type, is_group, lft, rgt
		from `tabAccount`
		where company = %s and root_type in ('Income', 'Expense')
		""",
		company,
		as_dict=1,
	)
	return {d.name: d for d in accounts}


def get_balances(filters, period_list):
	"""Return {account: {period_key: credit - debit}}."""
	conditions = ""
	if filters.get("cost_center"):
		lft, rgt = frappe.db.get_value("Cost Center", filters.cost_center, ["lft", "rgt"])
		conditions += """ and cost_center in (
			select name from `tabCost Center` where lft >= {0} and rgt <= {1})""".format(
			flt(lft), flt(rgt)
		)
	if filters.get("finance_book"):
		conditions += " and ifnull(finance_book, '') in (%(finance_book)s, '')"

	rows = frappe.db.sql(
		"""
		select account, date_format(posting_date, '%%Y-%%m') as mkey,
			sum(credit) - sum(debit) as bal
		from `tabGL Entry`
		where company = %(company)s
			and is_cancelled = 0
			and posting_date between %(from_date)s and %(to_date)s
			and voucher_type != 'Period Closing Voucher'
			{conditions}
		group by account, mkey
		""".format(conditions=conditions),
		{
			"company": filters.company,
			"from_date": filters.from_date,
			"to_date": filters.to_date,
			"finance_book": filters.get("finance_book"),
		},
		as_dict=1,
	)

	month_to_period = {}
	for period in period_list:
		start, end = period.from_date, period.to_date
		cur = frappe.utils.getdate(start).replace(day=1)
		end = frappe.utils.getdate(end)
		while cur <= end:
			month_to_period[cur.strftime("%Y-%m")] = period.key
			cur = frappe.utils.add_months(cur, 1)

	balances = {}
	for row in rows:
		key = month_to_period.get(row.mkey)
		if not key:
			continue
		balances.setdefault(row.account, {})[key] = (
			balances.get(row.account, {}).get(key, 0) + flt(row.bal)
		)
	return balances


def subtree_balance(account, accounts, balances, period_list, exclude=None):
	"""Sum credit - debit of an account and all its descendants, per period."""
	acc = accounts.get(account)
	totals = {p.key: 0.0 for p in period_list}
	if not acc:
		return totals
	excluded_ranges = []
	for ex in exclude or []:
		ex_acc = accounts.get(ex)
		if ex_acc:
			excluded_ranges.append((ex_acc.lft, ex_acc.rgt))
	for name, d in accounts.items():
		if d.lft >= acc.lft and d.rgt <= acc.rgt and name in balances:
			if any(d.lft >= lft and d.rgt <= rgt for lft, rgt in excluded_ranges):
				continue
			for key, val in balances[name].items():
				totals[key] = totals.get(key, 0) + val
	return totals


def by_number(accounts, number):
	for name, d in accounts.items():
		if d.account_number == number:
			return name
	return None


def children_of(accounts, parent_name):
	parent = accounts.get(parent_name)
	if not parent:
		return []
	children = frappe.get_all(
		"Account",
		filters={"parent_account": parent_name},
		fields=["name", "account_number"],
	)
	children.sort(key=lambda d: (d.account_number is None, str(d.account_number or ""), d.name))
	return [d.name for d in children]


def make_row(label, values, period_list, **kwargs):
	row = {"account": label}
	for p in period_list:
		row[p.key] = flt(values.get(p.key)) if values else None
	row.update(kwargs)
	return row


def add_rows(a, b, period_list, sign_b=1):
	return {p.key: flt(a.get(p.key)) + sign_b * flt(b.get(p.key)) for p in period_list}


def negate(values, period_list):
	return {p.key: -flt(values.get(p.key)) for p in period_list}


def has_value(values):
	return any(abs(flt(v)) > 0.004 for v in values.values())


def pct_row(label, numerator, denominator, period_list):
	values = {}
	for p in period_list:
		den = flt(denominator.get(p.key))
		values[p.key] = (flt(numerator.get(p.key)) / den * 100) if den else 0
	return make_row(label, values, period_list, bold=1, is_percent=1)


def build_data(period_list, accounts, balances):
	data = []
	zero = {p.key: 0.0 for p in period_list}

	revenue_parent = by_number(accounts, REVENUE_PARENT)
	contra_parent = by_number(accounts, CONTRA_PARENT)
	expense_root = by_number(accounts, EXPENSE_ROOT)
	tax_account = by_number(accounts, TAX_NUMBER)

	# --- Sales Revenue (Note 1) ---
	data.append(
		make_row(
			_("Sales Revenue (Dakhliga)   Note 1"),
			None,
			period_list,
			bold=1,
			section=1,
			note_report="Income Statement Notes",
			note_filter="Note 1 - Sales Revenue",
		)
	)

	total_revenue = dict(zero)
	numbered_rows = {}  # account_number -> values dict (mutated in place)
	revenue_rows = []  # (label, values) in display order
	unmapped_legacy = []

	for child in children_of(accounts, revenue_parent):
		values = subtree_balance(child, accounts, balances, period_list)
		number = accounts[child].account_number
		if number:
			numbered_rows[number] = values
			revenue_rows.append((child, values))
		else:
			legacy_target = LEGACY_REVENUE_MAP.get(accounts[child].account_name)
			if legacy_target and legacy_target in numbered_rows:
				target = numbered_rows[legacy_target]
				for p in period_list:
					target[p.key] = flt(target.get(p.key)) + flt(values.get(p.key))
			elif has_value(values):
				unmapped_legacy.append((child, values))

	# fold legacy accounts whose numbered target appears later in the sort order
	for child, values in list(unmapped_legacy):
		legacy_target = LEGACY_REVENUE_MAP.get(accounts[child].account_name)
		if legacy_target and legacy_target in numbered_rows:
			target = numbered_rows[legacy_target]
			for p in period_list:
				target[p.key] = flt(target.get(p.key)) + flt(values.get(p.key))
			unmapped_legacy.remove((child, values))

	for label, values in revenue_rows + unmapped_legacy:
		if not has_value(values):
			continue
		data.append(make_row(label, values, period_list, indent=1))
		total_revenue = add_rows(total_revenue, values, period_list)

	data.append(make_row(_("Total Revenue"), total_revenue, period_list, bold=1, total=1))

	# --- Contra Revenue ---
	data.append(make_row(_("Less Contra Revenue"), None, period_list, bold=1, section=1, red=1))
	total_contra = dict(zero)
	for child in children_of(accounts, contra_parent):
		values = subtree_balance(child, accounts, balances, period_list)
		data.append(make_row(child, values, period_list, indent=1))
		total_contra = add_rows(total_contra, values, period_list)
	data.append(make_row(_("Total Contra Revenue"), total_contra, period_list, bold=1, total=1, red=1))

	gross_sales = add_rows(total_revenue, total_contra, period_list)
	data.append(make_row(_("Gross Sales Income"), gross_sales, period_list, bold=1, total=1))

	# --- Cost of Revenue (Note 2) ---
	data.append(
		make_row(
			_("Less Cost of Revenue Note 2"),
			None,
			period_list,
			bold=1,
			section=1,
			red=1,
			note_report="Income Statement Notes",
			note_filter="Note 2 - Cost of Revenue",
		)
	)
	total_cogs = dict(zero)
	for number in COGS_NUMBERS:
		name = by_number(accounts, number)
		if not name:
			continue
		values = negate(subtree_balance(name, accounts, balances, period_list), period_list)
		data.append(make_row(name, values, period_list, indent=1))
		total_cogs = add_rows(total_cogs, values, period_list)
	data.append(make_row(_("Total Cost of Revenue"), total_cogs, period_list, bold=1, total=1))

	gross_profit = add_rows(gross_sales, total_cogs, period_list, sign_b=-1)
	data.append(make_row(_("Gross profit (Faa'iido duuduub ah )"), gross_profit, period_list, bold=1, total=1))
	data.append(pct_row(_("Gross Margin %"), gross_profit, total_revenue, period_list))

	data.append({})

	# --- Operating Expenses (Note 3) ---
	data.append(
		make_row(
			_("Operating Expenses Note 3"),
			None,
			period_list,
			bold=1,
			section=1,
			red=1,
			note_report="Income Statement Notes",
			note_filter="Note 3 - Operating Expenses",
		)
	)
	total_opex = dict(zero)
	for child in children_of(accounts, expense_root):
		number = accounts[child].account_number
		if number in COGS_NUMBERS:
			continue
		exclude = [tax_account] if tax_account and accounts[tax_account].lft >= accounts[child].lft and accounts[tax_account].rgt <= accounts[child].rgt else None
		values = negate(subtree_balance(child, accounts, balances, period_list, exclude=exclude), period_list)
		if not has_value(values):
			continue
		data.append(make_row(child, values, period_list, indent=1))
		total_opex = add_rows(total_opex, values, period_list)

	data.append(make_row(_("Total Operating Expenses"), total_opex, period_list, bold=1, total=1))

	profit_before_tax = add_rows(gross_profit, total_opex, period_list, sign_b=-1)
	data.append(make_row(_("Profit before Tax"), profit_before_tax, period_list, bold=1, total=1))
	data.append(pct_row(_("Operating Profit Margin %"), profit_before_tax, total_revenue, period_list))

	tax_values = dict(zero)
	if tax_account:
		tax_values = negate(subtree_balance(tax_account, accounts, balances, period_list), period_list)
		data.append(make_row(tax_account, tax_values, period_list, indent=1))

	net_profit = add_rows(profit_before_tax, tax_values, period_list, sign_b=-1)
	data.append(make_row(_("NET PROFIT FOR THE PERIOD"), net_profit, period_list, bold=1, net_profit=1))

	return data


def get_columns(filters, period_list):
	columns = [
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Data",
			"width": 420,
		}
	]
	currency = frappe.get_cached_value("Company", filters.company, "default_currency")
	# newest period first, like the Excel layout
	for period in reversed(period_list):
		columns.append(
			{
				"fieldname": period.key,
				"label": period.label,
				"fieldtype": "Currency",
				"options": "currency",
				"width": 150,
			}
		)
	columns.append(
		{"fieldname": "currency", "label": _("Currency"), "fieldtype": "Data", "hidden": 1}
	)
	return columns

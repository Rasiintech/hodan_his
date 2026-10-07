# Copyright (c) 2026, Hodan Hospital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_months, flt, getdate

from his.his.report.hospital_income_statement.hospital_income_statement import get_periods

TOTAL_ASSETS = "100000"
CURRENT_ASSETS = "110000"
NON_CURRENT_ASSETS = "120000"
CURRENT_LIABILITIES = "210000"
TAXES_LIABILITIES = "220000"
SHORT_TERM_BORROWINGS = "230000"
LONG_TERM_LOANS = "240000"
TOTAL_EQUITY = "300000"
RETAINED_EARNINGS = "330000"
DIVIDENDS = "3200"

# Legacy (unnumbered) fixed-asset accounts folded into the numbered groups,
# matching the Excel balance sheet layout.
LEGACY_ASSET_MAP = {
	"Medical Equipment": "122000",
	"Dental equipment": "122000",
	"Electronic Equipments": "123000",
	"Fixtures Equipment": "124000",
}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.company:
		filters.company = frappe.defaults.get_user_default("Company")

	period_list = get_periods(filters)
	accounts = get_all_accounts(filters.company)
	balances = get_cumulative_balances(filters, period_list)

	columns = get_columns(filters, period_list)
	data = build_data(filters, period_list, accounts, balances)

	currency = frappe.get_cached_value("Company", filters.company, "default_currency")
	for row in data:
		if row:
			row["currency"] = currency

	return columns, data


def get_all_accounts(company):
	accounts = frappe.db.sql(
		"""
		select name, account_name, trim(ifnull(account_number, '')) as account_number,
			root_type, is_group, lft, rgt, parent_account
		from `tabAccount`
		where company = %s
		""",
		company,
		as_dict=1,
	)
	return {d.name: d for d in accounts}


def get_cumulative_balances(filters, period_list):
	"""Return {account: {period_key: debit - credit cumulative as of period end}}."""
	conditions = ""
	if filters.get("cost_center"):
		lft, rgt = frappe.db.get_value("Cost Center", filters.cost_center, ["lft", "rgt"])
		conditions += """ and cost_center in (
			select name from `tabCost Center` where lft >= {0} and rgt <= {1})""".format(
			flt(lft), flt(rgt)
		)

	rows = frappe.db.sql(
		"""
		select account, date_format(posting_date, '%%Y-%%m') as mkey,
			sum(debit) - sum(credit) as bal
		from `tabGL Entry`
		where company = %(company)s
			and is_cancelled = 0
			and posting_date <= %(to_date)s
			and voucher_type != 'Period Closing Voucher'
			{conditions}
		group by account, mkey
		""".format(conditions=conditions),
		{"company": filters.company, "to_date": filters.to_date},
		as_dict=1,
	)

	monthly = {}
	for row in rows:
		monthly.setdefault(row.account, {})[row.mkey] = flt(row.bal)

	period_ends = [(p.key, getdate(p.to_date).strftime("%Y-%m")) for p in period_list]

	balances = {}
	for account, months in monthly.items():
		cumulative = {}
		ordered = sorted(months.items())
		idx, running = 0, 0.0
		for key, end_month in period_ends:
			while idx < len(ordered) and ordered[idx][0] <= end_month:
				running += ordered[idx][1]
				idx += 1
			cumulative[key] = running
		balances[account] = cumulative
	return balances


def subtree_cumulative(account, accounts, balances, period_list, exclude=None):
	"""Sum debit - credit of an account and its descendants, per period.

	Walks parent_account links (the nested-set lft/rgt values in this chart
	are stale for some accounts and would double-count).
	"""
	totals = {p.key: 0.0 for p in period_list}
	if account not in accounts:
		return totals
	children_map = {}
	for name, d in accounts.items():
		children_map.setdefault(d.parent_account, []).append(name)

	excluded = set(exclude or [])
	stack = [account]
	while stack:
		name = stack.pop()
		if name in excluded:
			continue
		if name in balances:
			for key, val in balances[name].items():
				totals[key] = totals.get(key, 0) + val
		stack.extend(children_map.get(name, []))
	return totals


def by_number(accounts, number):
	for name, d in accounts.items():
		if d.account_number == number:
			return name
	return None


def sorted_children(accounts, parent_name):
	children = [name for name, d in accounts.items() if d.parent_account == parent_name]

	def sort_key(name):
		number = accounts[name].account_number
		if number and number.isdigit():
			return (0 if len(number) == 6 else 1, int(number), name)
		return (2, 0, name)

	return sorted(children, key=sort_key)


def has_value(values):
	return any(abs(flt(v)) > 0.004 for v in values.values())


def add_rows(a, b, period_list, sign_b=1):
	return {p.key: flt(a.get(p.key)) + sign_b * flt(b.get(p.key)) for p in period_list}


def negate(values, period_list):
	return {p.key: -flt(values.get(p.key)) for p in period_list}


def group_rows(accounts, balances, period_list, parent, legacy_map=None, sign=1):
	"""Rows for the direct children of parent, legacy accounts folded in.

	Returns (rows, total): rows are (account_name, values) with sign applied.
	"""
	zero = {p.key: 0.0 for p in period_list}
	numbered = {}
	rows = []
	legacy = []
	for child in sorted_children(accounts, parent):
		values = subtree_cumulative(child, accounts, balances, period_list)
		if sign < 0:
			values = negate(values, period_list)
		number = accounts[child].account_number
		if number:
			numbered[number] = values
			rows.append((child, values))
		else:
			target = (legacy_map or {}).get(accounts[child].account_name)
			if target and target in numbered:
				for p in period_list:
					numbered[target][p.key] += flt(values.get(p.key))
			elif has_value(values):
				legacy.append((child, values))

	rows = [(name, values) for name, values in rows if has_value(values) or accounts[name].account_number]
	rows += legacy

	total = dict(zero)
	for _name, values in rows:
		total = add_rows(total, values, period_list)
	return rows, total


def row(label, values, period_list, **kwargs):
	d = {"account": label}
	for p in period_list:
		d[p.key] = flt(values.get(p.key)) if values is not None else None
	d.update(kwargs)
	return d


def build_data(filters, period_list, accounts, balances):
	data = []
	zero = {p.key: 0.0 for p in period_list}

	current_assets = by_number(accounts, CURRENT_ASSETS)
	non_current_assets = by_number(accounts, NON_CURRENT_ASSETS)
	total_assets_acc = by_number(accounts, TOTAL_ASSETS)
	current_liab = by_number(accounts, CURRENT_LIABILITIES)
	taxes = by_number(accounts, TAXES_LIABILITIES)
	short_term = by_number(accounts, SHORT_TERM_BORROWINGS)
	long_term = by_number(accounts, LONG_TERM_LOANS)
	equity_root = by_number(accounts, TOTAL_EQUITY)
	retained = by_number(accounts, RETAINED_EARNINGS)
	dividends = by_number(accounts, DIVIDENDS)

	# ------------------------------- Assets --------------------------------
	data.append(row(_("Assets"), None, period_list, title=1))
	data.append(
		row(
			_("Current Assets"),
			None,
			period_list,
			bold=1,
			section=1,
			note_report="Balance Sheet Notes",
			note_filter="Note 1 - Current Assets",
		)
	)
	ca_rows, total_ca = group_rows(accounts, balances, period_list, current_assets)
	for name, values in ca_rows:
		data.append(row(name, values, period_list, indent=1))
	data.append(row(_("Total Current Assets"), total_ca, period_list, bold=1, total=1))
	data.append({})

	data.append(
		row(
			_("Non-current Assets"),
			None,
			period_list,
			bold=1,
			section=1,
			note_report="Balance Sheet Notes",
			note_filter="Note 2 - Fixed Assets",
		)
	)
	nca_rows, total_nca = group_rows(
		accounts, balances, period_list, non_current_assets, legacy_map=LEGACY_ASSET_MAP
	)
	for name, values in nca_rows:
		data.append(row(name, values, period_list, indent=1))
	data.append(row(_("Total Non-current Assets"), total_nca, period_list, bold=1, total=1))

	# other assets outside 110000/120000 (investments, temporary accounts, ...)
	other_assets = dict(zero)
	if total_assets_acc:
		all_assets = subtree_cumulative(total_assets_acc, accounts, balances, period_list)
		other_assets = add_rows(
			add_rows(all_assets, total_ca, period_list, sign_b=-1), total_nca, period_list, sign_b=-1
		)
		if has_value(other_assets):
			data.append(row(_("Other Assets"), other_assets, period_list, indent=1))

	total_assets = add_rows(add_rows(total_ca, total_nca, period_list), other_assets, period_list)
	data.append(row(_("Total Assets"), total_assets, period_list, bold=1, grand_total=1))

	# ------------------------- Liabilities & Equity ------------------------
	data.append(row(_("Liabilities & Equity"), None, period_list, title=1))
	data.append(
		row(
			_("Current Liabilities"),
			None,
			period_list,
			bold=1,
			section=1,
			note_report="Balance Sheet Notes",
			note_filter="Note 3 - Current Liabilities",
		)
	)
	total_cl = dict(zero)
	cl_rows, total_cl = group_rows(accounts, balances, period_list, current_liab, sign=-1)
	for name, values in cl_rows:
		data.append(row(name, values, period_list, indent=1))
	for extra_group in (taxes, short_term):
		if not extra_group:
			continue
		values = negate(
			subtree_cumulative(extra_group, accounts, balances, period_list), period_list
		)
		data.append(row(extra_group, values, period_list, indent=1))
		total_cl = add_rows(total_cl, values, period_list)
	data.append(row(_("Total Current Liabilities"), total_cl, period_list, bold=1, total=1))

	data.append(row(_("Non-current liabilities"), None, period_list, bold=1, section=1))
	ncl_rows, total_ncl = group_rows(accounts, balances, period_list, long_term, sign=-1)
	for name, values in ncl_rows:
		data.append(row(name, values, period_list, indent=1))
	data.append(row(_("Total Non-current Liabilities"), total_ncl, period_list, bold=1, total=1))

	total_liabilities = add_rows(total_cl, total_ncl, period_list)
	data.append(row(_("TOTAL LIABILITIES"), total_liabilities, period_list, bold=1, grand_total=1))
	data.append({})

	# -------------------------------- Equity -------------------------------
	data.append(row(_("Equity"), None, period_list, bold=1, section=1))

	capital = negate(
		subtree_cumulative(
			equity_root, accounts, balances, period_list,
			exclude=[a for a in (retained, dividends) if a],
		),
		period_list,
	)
	data.append(row(_("Share Capital / Owner Capital"), capital, period_list, bold=1))

	# profit & loss accumulated in income/expense accounts (closing vouchers excluded)
	pl_accounts = [n for n, d in accounts.items() if d.root_type in ("Income", "Expense")]
	pl_cumulative = dict(zero)
	for name in pl_accounts:
		for key, val in balances.get(name, {}).items():
			pl_cumulative[key] -= val  # credit - debit = profit

	current_profit = get_period_profit(filters, period_list, accounts)
	retained_balance = (
		negate(subtree_cumulative(retained, accounts, balances, period_list), period_list)
		if retained
		else dict(zero)
	)
	prior_retained = {
		p.key: retained_balance[p.key] + pl_cumulative[p.key] - current_profit[p.key]
		for p in period_list
	}
	data.append(row(_("Prior Retained Earnings"), prior_retained, period_list))
	data.append(row(_("Current Period Profit"), current_profit, period_list))

	drawings = (
		subtree_cumulative(dividends, accounts, balances, period_list) if dividends else dict(zero)
	)
	data.append(row(_("Dividends / Drawings"), drawings, period_list))

	closing_retained = {
		p.key: prior_retained[p.key] + current_profit[p.key] - flt(drawings.get(p.key))
		for p in period_list
	}
	data.append(row(_("Closing Retained Earnings"), closing_retained, period_list, bold=1, total=1))

	total_equity = add_rows(capital, closing_retained, period_list)
	data.append(row(_("TOTAL EQUITY"), total_equity, period_list, bold=1, grand_total=1))

	total_liab_equity = add_rows(total_liabilities, total_equity, period_list)
	data.append(
		row(_("TOTAL LIABILITIES & EQUITY"), total_liab_equity, period_list, bold=1, grand_total=1)
	)

	balance_check = add_rows(total_assets, total_liab_equity, period_list, sign_b=-1)
	data.append(row(_("BALANCE CHECK"), balance_check, period_list, bold=1, check=1))

	return data


def get_period_profit(filters, period_list, accounts):
	"""Profit (credit - debit of P&L accounts) within each period on its own."""
	conditions = ""
	if filters.get("cost_center"):
		lft, rgt = frappe.db.get_value("Cost Center", filters.cost_center, ["lft", "rgt"])
		conditions += """ and cost_center in (
			select name from `tabCost Center` where lft >= {0} and rgt <= {1})""".format(
			flt(lft), flt(rgt)
		)

	rows = frappe.db.sql(
		"""
		select gle.account, date_format(gle.posting_date, '%%Y-%%m') as mkey,
			sum(gle.credit) - sum(gle.debit) as bal
		from `tabGL Entry` gle
		inner join `tabAccount` acc on acc.name = gle.account
		where gle.company = %(company)s
			and gle.is_cancelled = 0
			and acc.root_type in ('Income', 'Expense')
			and gle.posting_date between %(from_date)s and %(to_date)s
			and gle.voucher_type != 'Period Closing Voucher'
			{conditions}
		group by gle.account, mkey
		""".format(conditions=conditions),
		{"company": filters.company, "from_date": filters.from_date, "to_date": filters.to_date},
		as_dict=1,
	)

	month_profit = {}
	for r in rows:
		month_profit[r.mkey] = month_profit.get(r.mkey, 0) + flt(r.bal)

	profit = {}
	for p in period_list:
		total = 0.0
		cur = getdate(p.from_date).replace(day=1)
		end = getdate(p.to_date)
		while cur <= end:
			total += month_profit.get(cur.strftime("%Y-%m"), 0)
			cur = add_months(cur, 1)
		profit[p.key] = total
	return profit


def get_columns(filters, period_list):
	columns = [
		{
			"fieldname": "account",
			"label": _("Description"),
			"fieldtype": "Data",
			"width": 420,
		}
	]
	for period in reversed(period_list):
		columns.append(
			{
				"fieldname": period.key,
				"label": period.label,
				"fieldtype": "Currency",
				"options": "currency",
				"width": 160,
			}
		)
	columns.append(
		{"fieldname": "currency", "label": _("Currency"), "fieldtype": "Data", "hidden": 1}
	)
	return columns

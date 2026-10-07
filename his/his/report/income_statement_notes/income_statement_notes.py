# Copyright (c) 2026, Hodan Hospital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

from his.his.report.hospital_income_statement.hospital_income_statement import (
	COGS_NUMBERS,
	EXPENSE_ROOT,
	LEGACY_REVENUE_MAP,
	REVENUE_PARENT,
	TAX_NUMBER,
	by_number,
	children_of,
	get_accounts,
	get_balances,
	get_periods,
	has_value,
	negate,
	subtree_balance,
)

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.company:
		filters.company = frappe.defaults.get_user_default("Company")
	note = filters.note or "All Notes"

	period_list = get_periods(filters)
	accounts = get_accounts(filters.company)
	balances = get_balances(filters, period_list)

	columns = get_columns(filters, period_list)
	data = []
	if note in ("All Notes", "Note 1 - Sales Revenue"):
		data += build_note(
			_("Note 1  Sales Revenue (Dakhliga)"),
			get_note1_groups(accounts, balances, period_list),
			period_list,
		)
	if note in ("All Notes", "Note 2 - Cost of Revenue"):
		data += build_note(
			_("Note 2  COST OF REVENUE"),
			get_note2_groups(accounts, balances, period_list),
			period_list,
		)
	if note in ("All Notes", "Note 3 - Operating Expenses"):
		data += build_note(
			_("Note 3  Operating Expense"),
			get_note3_groups(accounts, balances, period_list),
			period_list,
		)

	currency = frappe.get_cached_value("Company", filters.company, "default_currency")
	for row in data:
		if row:
			row["currency"] = currency

	return columns, data


def get_note1_groups(accounts, balances, period_list):
	"""[(group_name, group_values, [(leaf, values), ...]), ...] for revenue."""
	revenue_parent = by_number(accounts, REVENUE_PARENT)
	zero = {p.key: 0.0 for p in period_list}

	legacy_children = {}
	for child in children_of(accounts, revenue_parent):
		if accounts[child].account_number:
			continue
		values = subtree_balance(child, accounts, balances, period_list)
		if not has_value(values):
			continue
		target = LEGACY_REVENUE_MAP.get(accounts[child].account_name)
		legacy_children.setdefault(target, []).append((child, values))

	groups = []
	for child in children_of(accounts, revenue_parent):
		number = accounts[child].account_number
		if not number:
			continue
		leaves = []
		group_values = dict(zero)
		if accounts[child].is_group:
			for leaf in children_of(accounts, child):
				values = subtree_balance(leaf, accounts, balances, period_list)
				for p in period_list:
					group_values[p.key] += flt(values.get(p.key))
				if has_value(values):
					leaves.append((leaf, values))
		else:
			group_values = subtree_balance(child, accounts, balances, period_list)
		for name, values in legacy_children.pop(number, []):
			for p in period_list:
				group_values[p.key] += flt(values.get(p.key))
			leaves.append((name, values))
		if has_value(group_values):
			groups.append((child, group_values, leaves))

	for target, rows in legacy_children.items():
		for name, values in rows:
			groups.append((name, values, []))
	return groups


def expense_group(accounts, balances, period_list, group_name, exclude=None):
	zero = {p.key: 0.0 for p in period_list}
	leaves = []
	group_values = dict(zero)
	excluded = set(exclude or [])
	for leaf in children_of(accounts, group_name):
		if leaf in excluded:
			continue
		values = negate(subtree_balance(leaf, accounts, balances, period_list), period_list)
		for p in period_list:
			group_values[p.key] += flt(values.get(p.key))
		if has_value(values):
			leaves.append((leaf, values))
	return group_name, group_values, leaves


def get_note2_groups(accounts, balances, period_list):
	groups = []
	for number in COGS_NUMBERS:
		name = by_number(accounts, number)
		if name:
			groups.append(expense_group(accounts, balances, period_list, name))
	return [g for g in groups if has_value(g[1]) or g[2]]


def get_note3_groups(accounts, balances, period_list):
	expense_root = by_number(accounts, EXPENSE_ROOT)
	tax_account = by_number(accounts, TAX_NUMBER)
	groups = []
	for child in children_of(accounts, expense_root):
		number = accounts[child].account_number
		if number in COGS_NUMBERS:
			continue
		group = expense_group(
			accounts, balances, period_list, child, exclude=[tax_account] if tax_account else None
		)
		if has_value(group[1]):
			groups.append(group)
	return groups


def build_note(title, groups, period_list):
	grand_total = {p.key: 0.0 for p in period_list}
	for _group, group_values, _leaves in groups:
		for p in period_list:
			grand_total[p.key] += flt(group_values.get(p.key))

	def pct(part, whole, key):
		base = flt(whole.get(key))
		return (flt(part.get(key)) / base * 100) if base else 0

	data = [{"sn": "", "account": title, "note_title": 1}]
	for idx, (group, group_values, leaves) in enumerate(groups):
		letter = LETTERS[idx] if idx < len(LETTERS) else str(idx + 1)
		header = {"sn": letter, "account": group, "group_header": 1}
		for p in period_list:
			header[p.key] = flt(group_values.get(p.key))
			header[p.key + "_pct"] = pct(group_values, grand_total, p.key)
		data.append(header)

		for n, (leaf, values) in enumerate(leaves, start=1):
			row = {"sn": n, "account": leaf}
			for p in period_list:
				row[p.key] = flt(values.get(p.key))
				row[p.key + "_pct"] = pct(values, group_values, p.key)
			data.append(row)

		total_row = {"sn": "", "account": _("Total"), "total": 1}
		for p in period_list:
			total_row[p.key] = flt(group_values.get(p.key))
			total_row[p.key + "_pct"] = pct(group_values, grand_total, p.key)
		data.append(total_row)
		data.append({})
	return data


def get_columns(filters, period_list):
	columns = [
		{"fieldname": "sn", "label": _("S.No"), "fieldtype": "Data", "width": 60},
		{
			"fieldname": "account",
			"label": _("Description"),
			"fieldtype": "Data",
			"width": 400,
		},
	]
	for period in reversed(period_list):
		columns.append(
			{
				"fieldname": period.key,
				"label": _("Amount {0}").format(period.label),
				"fieldtype": "Currency",
				"options": "currency",
				"width": 160,
			}
		)
		columns.append(
			{
				"fieldname": period.key + "_pct",
				"label": _("% {0}").format(period.label),
				"fieldtype": "Data",
				"width": 120,
				"align": "right",
			}
		)
	columns.append(
		{"fieldname": "currency", "label": _("Currency"), "fieldtype": "Data", "hidden": 1}
	)
	return columns

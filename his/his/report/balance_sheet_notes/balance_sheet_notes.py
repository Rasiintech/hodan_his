# Copyright (c) 2026, Hodan Hospital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

from his.his.report.hospital_balance_sheet.hospital_balance_sheet import (
	CURRENT_ASSETS,
	CURRENT_LIABILITIES,
	LEGACY_ASSET_MAP,
	NON_CURRENT_ASSETS,
	SHORT_TERM_BORROWINGS,
	TAXES_LIABILITIES,
	by_number,
	get_all_accounts,
	get_cumulative_balances,
	has_value,
	negate,
	sorted_children,
	subtree_cumulative,
)
from his.his.report.hospital_income_statement.hospital_income_statement import get_periods

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.company:
		filters.company = frappe.defaults.get_user_default("Company")
	note = filters.note or "All Notes"

	period_list = get_periods(filters)
	accounts = get_all_accounts(filters.company)
	balances = get_cumulative_balances(filters, period_list)

	columns = get_columns(filters, period_list)
	data = []
	if note in ("All Notes", "Note 1 - Current Assets"):
		data += build_note(
			_("Note 1  Current Assets (A-E)"),
			get_asset_groups(accounts, balances, period_list, by_number(accounts, CURRENT_ASSETS)),
			period_list,
		)
	if note in ("All Notes", "Note 2 - Fixed Assets"):
		data += build_note(
			_("Note 2  Fixed Assets (Non-current Assets)"),
			get_asset_groups(
				accounts, balances, period_list,
				by_number(accounts, NON_CURRENT_ASSETS), legacy_map=LEGACY_ASSET_MAP,
			),
			period_list,
		)
	if note in ("All Notes", "Note 3 - Current Liabilities"):
		data += build_note(
			_("Note 3  Current Liabilities"),
			get_liability_groups(accounts, balances, period_list),
			period_list,
		)

	currency = frappe.get_cached_value("Company", filters.company, "default_currency")
	for row in data:
		if row:
			row["currency"] = currency

	return columns, data


def make_group(accounts, balances, period_list, group_name, sign=1, folded=None):
	"""(group_name, group_values, [(leaf, values), ...]) for one section."""
	zero = {p.key: 0.0 for p in period_list}
	leaves = []
	group_values = dict(zero)
	if accounts[group_name].is_group:
		for leaf in sorted_children(accounts, group_name):
			values = subtree_cumulative(leaf, accounts, balances, period_list)
			if sign < 0:
				values = negate(values, period_list)
			for p in period_list:
				group_values[p.key] += flt(values.get(p.key))
			if has_value(values):
				leaves.append((leaf, values))
	else:
		group_values = subtree_cumulative(group_name, accounts, balances, period_list)
		if sign < 0:
			group_values = negate(group_values, period_list)
	for name, values in folded or []:
		for p in period_list:
			group_values[p.key] += flt(values.get(p.key))
		leaves.append((name, values))
	return group_name, group_values, leaves


def get_asset_groups(accounts, balances, period_list, parent, legacy_map=None):
	# collect legacy (unnumbered) accounts folded into their numbered siblings
	folded = {}
	loose = []
	for child in sorted_children(accounts, parent):
		if accounts[child].account_number:
			continue
		values = subtree_cumulative(child, accounts, balances, period_list)
		if not has_value(values):
			continue
		target = (legacy_map or {}).get(accounts[child].account_name)
		if target:
			folded.setdefault(target, []).append((child, values))
		else:
			loose.append((child, values))

	groups = []
	for child in sorted_children(accounts, parent):
		number = accounts[child].account_number
		if not number:
			continue
		group = make_group(
			accounts, balances, period_list, child, folded=folded.pop(number, None)
		)
		if has_value(group[1]) or group[2]:
			groups.append(group)

	for name, values in loose:
		groups.append((name, values, []))
	return groups


def get_liability_groups(accounts, balances, period_list):
	groups = []
	for child in sorted_children(accounts, by_number(accounts, CURRENT_LIABILITIES)):
		group = make_group(accounts, balances, period_list, child, sign=-1)
		if has_value(group[1]) or group[2]:
			groups.append(group)
	for number in (TAXES_LIABILITIES, SHORT_TERM_BORROWINGS):
		name = by_number(accounts, number)
		if name:
			group = make_group(accounts, balances, period_list, name, sign=-1)
			if has_value(group[1]) or group[2]:
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
				"label": _("Percentage {0}").format(period.label),
				"fieldtype": "Data",
				"width": 120,
				"align": "right",
			}
		)
	columns.append(
		{"fieldname": "currency", "label": _("Currency"), "fieldtype": "Data", "hidden": 1}
	)
	return columns

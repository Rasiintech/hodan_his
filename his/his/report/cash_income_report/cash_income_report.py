# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)

	currency = frappe.get_cached_value("Company", filters.company, "default_currency")
	entries = get_entries(filters)

	if filters.get("view") == "Summarized":
		return get_summarized_columns(currency), build_summarized_data(entries)

	return get_columns(currency), build_data(entries)


def validate_filters(filters):
	for fieldname in ("company", "from_date", "to_date"):
		if not filters.get(fieldname):
			frappe.throw(_("{0} is required").format(_(fieldname.replace("_", " ").title())))

	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date cannot be after To Date"))

	if filters.get("account"):
		account_company, account_type = frappe.db.get_value(
			"Account", filters.account, ["company", "account_type"]
		) or (None, None)
		if account_company != filters.company or account_type not in ("Cash", "Bank"):
			frappe.throw(_("Account must be a Cash or Bank account belonging to the selected company"))


def get_entries(filters):
	# Resolving the handful of Cash/Bank accounts first and querying GL Entry
	# by account list uses the `account` index; filtering the whole GL table
	# by date range alone is ~35x slower on this dataset.
	account_types = dict(
		frappe.get_all(
			"Account",
			filters={
				"company": filters.company,
				"is_group": 0,
				"account_type": ["in", ["Cash", "Bank"]],
			},
			fields=["name", "account_type"],
			as_list=True,
		)
	)
	if not account_types:
		return []

	debit_accounts = list(account_types)
	if filters.get("account"):
		debit_accounts = [filters.account]

	values = {
		"from_date": filters.from_date,
		"to_date": filters.to_date,
		"debit_accounts": debit_accounts,
		"cash_bank_accounts": list(account_types),
	}

	# A voucher that credits another Cash/Bank account is an internal
	# transfer (cash-to-cash, cash-to-bank or bank-to-bank), not income.
	entries = frappe.db.sql(
		"""
		SELECT
			gle.posting_date,
			gle.account,
			gle.debit,
			gle.against AS against_account,
			gle.remarks,
			gle.voucher_type,
			gle.voucher_no
		FROM `tabGL Entry` gle
		LEFT JOIN `tabAccount` against_account
			ON against_account.name = gle.against
			AND against_account.company = gle.company
		LEFT JOIN (
			SELECT DISTINCT g2.voucher_type, g2.voucher_no
			FROM `tabGL Entry` g2
			WHERE g2.account IN %(cash_bank_accounts)s
				AND g2.posting_date BETWEEN %(from_date)s AND %(to_date)s
				AND g2.is_cancelled = 0
				AND g2.credit > 0
		) transfer_voucher
			ON transfer_voucher.voucher_type = gle.voucher_type
			AND transfer_voucher.voucher_no = gle.voucher_no
		WHERE gle.account IN %(debit_accounts)s
			AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND gle.is_cancelled = 0
			AND gle.debit > 0
			AND COALESCE(against_account.account_type, '') NOT IN ('Cash', 'Bank')
			AND transfer_voucher.voucher_no IS NULL
		ORDER BY gle.debit DESC, gle.posting_date, gle.creation
		""",
		values,
		as_dict=True,
	)

	for entry in entries:
		entry.account_type = account_types.get(entry.account)

	entries.sort(key=lambda entry: 0 if entry.account_type == "Cash" else 1)
	return entries


def build_data(entries):
	data = []
	grand_total = 0
	groups = (
		("Cash", _("Total of cash income")),
		("Bank", _("Total of bank income")),
	)

	for account_type, total_label in groups:
		rows = [entry for entry in entries if entry.account_type == account_type]
		if not rows:
			continue

		group_total = 0
		for entry in rows:
			amount = flt(entry.debit)
			group_total += amount
			data.append(
				{
					"posting_date": entry.posting_date,
					"account": entry.account,
					"debit": amount,
					"against_account": entry.against_account,
					"remarks": entry.remarks,
					"voucher_type": entry.voucher_type,
					"voucher_no": entry.voucher_no,
				}
			)

		data.append({"account": total_label, "debit": group_total, "is_group_total": 1})
		grand_total += group_total

		if account_type == "Cash" and any(entry.account_type == "Bank" for entry in entries):
			data.append({"is_blank": 1})

	if entries:
		data.append({"account": _("Total cash income"), "debit": grand_total, "is_grand_total": 1})

	return data


def build_summarized_data(entries):
	data = []
	grand_total = 0
	grand_count = 0
	groups = (
		("Cash", _("Total of cash income")),
		("Bank", _("Total of bank income")),
	)

	for account_type, total_label in groups:
		accounts = {}
		for entry in entries:
			if entry.account_type != account_type:
				continue
			row = accounts.setdefault(
				entry.account,
				{
					"account": entry.account,
					"no_of_entries": 0,
					"debit": 0,
					"first_date": entry.posting_date,
					"last_date": entry.posting_date,
				},
			)
			row["no_of_entries"] += 1
			row["debit"] += flt(entry.debit)
			if entry.posting_date < row["first_date"]:
				row["first_date"] = entry.posting_date
			if entry.posting_date > row["last_date"]:
				row["last_date"] = entry.posting_date

		if not accounts:
			continue

		rows = sorted(accounts.values(), key=lambda row: row["debit"], reverse=True)
		group_total = sum(row["debit"] for row in rows)
		group_count = sum(row["no_of_entries"] for row in rows)
		data.extend(rows)
		data.append(
			{
				"account": total_label,
				"no_of_entries": group_count,
				"debit": group_total,
				"is_group_total": 1,
			}
		)
		grand_total += group_total
		grand_count += group_count

		if account_type == "Cash" and any(entry.account_type == "Bank" for entry in entries):
			data.append({"is_blank": 1})

	if entries:
		data.append(
			{
				"account": _("Total cash income"),
				"no_of_entries": grand_count,
				"debit": grand_total,
				"is_grand_total": 1,
			}
		)

	return data


def get_summarized_columns(currency):
	return [
		{"label": _("Account"), "fieldname": "account", "fieldtype": "Link", "options": "Account", "width": 330},
		{"label": _("No of Entries"), "fieldname": "no_of_entries", "fieldtype": "Int", "width": 115},
		{
			"label": _("Total Income ({0})").format(currency),
			"fieldname": "debit",
			"fieldtype": "Currency",
			"options": currency,
			"width": 150,
		},
		{"label": _("First Entry"), "fieldname": "first_date", "fieldtype": "Date", "width": 110},
		{"label": _("Last Entry"), "fieldname": "last_date", "fieldtype": "Date", "width": 110},
	]


def get_columns(currency):
	return [
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 105},
		{"label": _("Account"), "fieldname": "account", "fieldtype": "Link", "options": "Account", "width": 330},
		{
			"label": _("Debit ({0})").format(currency),
			"fieldname": "debit",
			"fieldtype": "Currency",
			"options": currency,
			"width": 125,
		},
		{"label": _("Against Account"), "fieldname": "against_account", "fieldtype": "Data", "width": 310},
		{"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 170,
		},
		{"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 430},
	]

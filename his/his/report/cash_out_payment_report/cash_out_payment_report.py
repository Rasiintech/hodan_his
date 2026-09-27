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
	data = build_data(entries)

	return get_columns(currency), data


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
	values = {
		"company": filters.company,
		"from_date": filters.from_date,
		"to_date": filters.to_date,
		"customer_allowed_account": "111002 - Abdullahi Mohamed Elmi (Petty Cash) - HH",
		"excluded_account": "111028 - Cash Close - HH",
	}
	account_condition = ""
	if filters.get("account"):
		values["account"] = filters.account
		account_condition = "AND gle.account = %(account)s"

	return frappe.db.sql(
		f"""
		SELECT
			gle.posting_date,
			gle.account,
			gle.credit,
			gle.against AS against_account,
			gle.remarks,
			gle.voucher_type,
			gle.voucher_no,
			a.account_type
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` a ON a.name = gle.account
		LEFT JOIN `tabAccount` against_account
			ON against_account.name = gle.against
			AND against_account.company = gle.company
		LEFT JOIN `tabCustomer` against_customer
			ON against_customer.name = gle.against
		WHERE gle.company = %(company)s
			AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND gle.is_cancelled = 0
			AND gle.credit > 0
			AND gle.account != %(excluded_account)s
			AND a.is_group = 0
			AND a.account_type IN ('Cash', 'Bank')
			AND COALESCE(against_account.account_type, '') NOT IN ('Cash', 'Bank')
			AND (
				gle.account = %(customer_allowed_account)s
				OR against_customer.name IS NULL
			)
			{account_condition}
		ORDER BY
			CASE WHEN a.account_type = 'Cash' THEN 0 ELSE 1 END,
			gle.credit DESC,
			gle.posting_date,
			gle.creation
		""",
		values,
		as_dict=True,
	)


def build_data(entries):
	data = []
	grand_total = 0
	groups = (
		("Cash", _("Total of petty cash payment")),
		("Bank", _("Total of Banks payment")),
	)

	for account_type, total_label in groups:
		rows = [entry for entry in entries if entry.account_type == account_type]
		if not rows:
			continue

		group_total = 0
		for entry in rows:
			amount = flt(entry.credit)
			group_total += amount
			data.append(
				{
					"posting_date": entry.posting_date,
					"account": entry.account,
					"credit": amount,
					"against_account": entry.against_account,
					"remarks": entry.remarks,
					"voucher_type": entry.voucher_type,
					"voucher_no": entry.voucher_no,
				}
			)

		data.append({"account": total_label, "credit": group_total, "is_group_total": 1})
		grand_total += group_total

		if account_type == "Cash" and any(entry.account_type == "Bank" for entry in entries):
			data.append({"is_blank": 1})

	if entries:
		data.append({"account": _("Total cash out payment"), "credit": grand_total, "is_grand_total": 1})

	return data


def get_columns(currency):
	return [
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 105},
		{"label": _("Account"), "fieldname": "account", "fieldtype": "Link", "options": "Account", "width": 330},
		{
			"label": _("Credit ({0})").format(currency),
			"fieldname": "credit",
			"fieldtype": "Currency",
			"options": currency,
			"width": 125,
		},
		{"label": _("Against Account"), "fieldname": "against_account", "fieldtype": "Data", "width": 310},
		{"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 430},
		{"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "hidden": 1},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"hidden": 1,
		},
	]

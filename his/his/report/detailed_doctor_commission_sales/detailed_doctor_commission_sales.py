# Copyright (c) 2025, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _, msgprint

from his.his.report.doctor_commission.doctor_commission import get_data as get_doctor_commission_data


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("ref_practitioner"):
		msgprint(_("Please select a doctor to generate the report."), raise_exception=True)

	data = []
	for row in get_doctor_commission_data(filters):
		income_account = get_income_account(row.item_group)
		if not income_account:
			continue
		data.append(
			frappe._dict(
				{
					"income_account": income_account,
					"item_group": row.item_group,
					"gross_sales": row.gross_sales,
					"expense_percentage": row.expense_percent,
					"sales_amount": row.sales_expense_amount,
					"net_sales": row.net_sales,
					"percentage": row.commission_percent,
					"net_commission": row.net_commission,
				}
			)
		)

	if not data:
		msgprint(_("No item group data found for the selected doctor."))
	return get_columns(), data


def get_income_account(item_group):
	return frappe.db.get_value(
		"Item Default",
		{
			"parent": item_group,
			"parenttype": "Item Group",
			"parentfield": "item_group_defaults",
		},
		"income_account",
		order_by="idx asc",
	)


def get_columns():
	return [
		{"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 150},
		{"label": _("Gross Sales"), "fieldname": "gross_sales", "fieldtype": "Currency", "options": "currency", "width": 180},
		{"label": _("Sales Expense %"), "fieldname": "expense_percentage", "fieldtype": "percent", "options": "currency", "width": 180},
		{"label": _("Sales Amount"), "fieldname": "sales_amount", "fieldtype": "Currency", "options": "currency", "width": 180},
		{"label": _("Net Sales Amount"), "fieldname": "net_sales", "fieldtype": "Currency", "options": "currency", "width": 180},
		{"label": _("Percentage"), "fieldname": "percentage", "fieldtype": "Data", "width": 100},
		{"label": _("Net Commission"), "fieldname": "net_commission", "fieldtype": "Currency", "options": "currency", "width": 150},
	]


def get_item_group_data(filters):
	"""Compatibility helper retained for callers of the old report API."""
	return [
		frappe._dict({"item_group": row.item_group, "net_sales": row.gross_sales})
		for row in get_doctor_commission_data(frappe._dict(filters or {}))
	]

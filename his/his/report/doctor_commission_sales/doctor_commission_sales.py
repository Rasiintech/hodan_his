import frappe
from frappe import _, msgprint

from his.his.report.doctor_commission.doctor_commission import get_data as get_doctor_commission_data


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("ref_practitioner"):
		msgprint(_("Please select a doctor to generate the report."), raise_exception=True)

	rows = get_doctor_commission_data(filters)
	data = []
	for row in rows:
		income_account = get_income_account(row.item_group)
		if not income_account:
			continue
		data.append(
			frappe._dict(
				{
					"income_account": income_account,
					"item_group": row.item_group,
					"total_amount": row.net_sales,
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
		{"label": _("Income Account"), "fieldname": "income_account", "fieldtype": "Data", "width": 200},
		{"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "options": "currency", "width": 180},
		{"label": _("Percentage"), "fieldname": "percentage", "fieldtype": "Data", "width": 100},
		{"label": _("Net Commission"), "fieldname": "net_commission", "fieldtype": "Currency", "options": "currency", "width": 150},
	]


def get_item_group_data(filters):
	"""Compatibility helper retained for callers of the old report API."""
	return [
		frappe._dict({"item_group": row.item_group, "total_amount": row.net_sales})
		for row in get_doctor_commission_data(frappe._dict(filters or {}))
	]

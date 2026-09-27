# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate


DEFAULT_COMPANY = "Hodan Hospital"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	return get_columns(), get_data(filters)


def validate_filters(filters):
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are required"))

	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date cannot be after To Date"))


def get_columns():
	return [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{
			"label": _("Sales Partner"),
			"fieldname": "sales_partner",
			"fieldtype": "Link",
			"options": "Sales Partner",
			"width": 180,
		},
		{
			"label": _("Patient ID"),
			"fieldname": "patient",
			"fieldtype": "Link",
			"options": "Patient",
			"width": 140,
		},
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 210},
		{
			"label": _("Item Group"),
			"fieldname": "item_group",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 120,
		},
		{
			"label": _("Net Amount"),
			"fieldname": "net_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		},
		{
			"label": _("Sales Invoice"),
			"fieldname": "sales_invoice",
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 170,
		},
		{
			"label": _("Payment Status"),
			"fieldname": "payment_status",
			"fieldtype": "Data",
			"width": 120,
		},
	]


def get_data(filters):
	conditions = [
		"si.docstatus = 1",
		"IFNULL(si.sales_partner, '') != ''",
		"sii.item_group IN ('MRI', 'CT Scan')",
		"si.company = %(company)s",
		"si.posting_date BETWEEN %(from_date)s AND %(to_date)s",
	]
	values = {
		"company": DEFAULT_COMPANY,
		"from_date": filters.from_date,
		"to_date": filters.to_date,
	}

	for fieldname in ("sales_partner", "patient"):
		if filters.get(fieldname):
			conditions.append(f"si.{fieldname} = %({fieldname})s")
			values[fieldname] = filters[fieldname]

	if filters.get("item_group"):
		conditions.append("sii.item_group = %(item_group)s")
		values["item_group"] = filters.item_group

	if filters.get("payment_status"):
		conditions.append(
			"""CASE
				WHEN IFNULL(si.is_return, 0) = 1 THEN 'Return'
				WHEN si.status = 'Paid' THEN 'Paid'
				ELSE 'Pending'
			END = %(payment_status)s"""
		)
		values["payment_status"] = filters.payment_status

	return frappe.db.sql(
		f"""
			SELECT
				si.posting_date AS date,
				si.sales_partner,
				si.patient,
				COALESCE(NULLIF(si.patient_name, ''), p.patient_name) AS patient_name,
				sii.item_group,
				sii.net_amount,
				si.currency,
				si.name AS sales_invoice,
				CASE
					WHEN IFNULL(si.is_return, 0) = 1 THEN 'Return'
					WHEN si.status = 'Paid' THEN 'Paid'
					ELSE 'Pending'
				END AS payment_status
			FROM `tabSales Invoice` si
			INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
			LEFT JOIN `tabPatient` p ON p.name = si.patient
			WHERE {' AND '.join(conditions)}
			ORDER BY si.posting_date DESC, si.creation DESC, sii.idx ASC
		""",
		values,
		as_dict=True,
	)

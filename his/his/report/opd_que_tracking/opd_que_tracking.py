# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	data = get_data(filters)
	apply_refunds(data)
	return get_columns(), data


def apply_refunds(data):
	invoice_names = list({row.sales_invoice for row in data if row.sales_invoice})
	if not invoice_names:
		return

	refunds = frappe.db.get_all(
		"Sales Invoice",
		filters={
			"return_against": ["in", invoice_names],
			"docstatus": 1,
			"is_return": 1,
		},
		fields=["return_against", "SUM(ABS(net_total)) AS refunded_amount"],
		group_by="return_against",
	)
	refunded_amounts = {row.return_against: row.refunded_amount or 0 for row in refunds}

	for row in data:
		refunded_amount = refunded_amounts.get(row.sales_invoice, 0)
		if not refunded_amount:
			continue

		row.net_amount = max((row.net_amount or 0) - refunded_amount, 0)
		row.payment_status = "Refunded" if row.net_amount == 0 else "Partially Refunded"


def validate_filters(filters):
	if filters.get("from_date") and filters.get("to_date"):
		if getdate(filters.from_date) > getdate(filters.to_date):
			frappe.throw(_("From Date cannot be after To Date"))


def get_columns():
	return [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{
			"label": _("Patient ID"),
			"fieldname": "patient_id",
			"fieldtype": "Link",
			"options": "Patient",
			"width": 140,
		},
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 200},
		{
			"label": _("Consultant"),
			"fieldname": "consultant",
			"fieldtype": "Link",
			"options": "Healthcare Practitioner",
			"width": 190,
		},
		{"label": _("Que Type"), "fieldname": "que_type", "fieldtype": "Data", "width": 110},
		{"label": _("Is Free"), "fieldname": "is_free", "fieldtype": "Data", "width": 80},
		{"label": _("Remark"), "fieldname": "remark", "fieldtype": "Data", "width": 180},
		{
			"label": _("Net Amount"),
			"fieldname": "net_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{"label": _("Status"), "fieldname": "payment_status", "fieldtype": "Data", "width": 100},
		{"label": _("Created By"), "fieldname": "created_by", "fieldtype": "Data", "width": 170},
		{
			"label": _("Que"),
			"fieldname": "que",
			"fieldtype": "Link",
			"options": "Que",
			"width": 130,
		},
		{
			"label": _("Sales Invoice"),
			"fieldname": "sales_invoice",
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 150,
		},
	]


def get_data(filters):
	conditions = [
		"q.que_type IN ('New Patient', 'Follow Up', 'Refer')",
		"q.status != 'Canceled'",
	]
	values = {}

	if filters.get("from_date"):
		conditions.append("q.date >= %(from_date)s")
		values["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("q.date <= %(to_date)s")
		values["to_date"] = filters.to_date

	if filters.get("consultant"):
		conditions.append("q.practitioner = %(consultant)s")
		values["consultant"] = filters.consultant

	return frappe.db.sql(
		f"""
			SELECT
				q.date,
				q.name AS que,
				COALESCE(direct_si.name, linked_si.name) AS sales_invoice,
				q.patient AS patient_id,
				q.patient_name,
				q.practitioner AS consultant,
				CASE
					WHEN q.que_type = 'Follow Up' THEN 'Followup'
					ELSE q.que_type
				END AS que_type,
				CASE
					WHEN q.que_type = 'New Patient' AND IFNULL(q.is_free, 0) = 1 THEN 'Free'
					ELSE ''
				END AS is_free,
				COALESCE(NULLIF(q.reference, ''), NULLIF(q.remarks, ''), '') AS remark,
				IFNULL(COALESCE(direct_si.net_total, linked_si.net_total), 0) AS net_amount,
				COALESCE(direct_si.currency, linked_si.currency) AS currency,
				CASE
					WHEN EXISTS (
						SELECT 1
						FROM `tabSales Invoice` return_si
						WHERE return_si.return_against = COALESCE(direct_si.name, linked_si.name)
							AND return_si.docstatus = 1
							AND IFNULL(return_si.is_return, 0) = 1
					) THEN 'Refunded'
					WHEN COALESCE(direct_si.status, linked_si.status) = 'Paid' THEN 'Paid'
					WHEN COALESCE(direct_si.status, linked_si.status) IN ('Unpaid', 'Overdue') THEN 'Unpaid'
					WHEN COALESCE(direct_si.name, linked_si.name) IS NOT NULL
						AND IFNULL(COALESCE(direct_si.outstanding_amount, linked_si.outstanding_amount), 0) <= 0
					THEN 'Paid'
					ELSE 'Unpaid'
				END AS payment_status,
				COALESCE(NULLIF(u.full_name, ''), q.owner) AS created_by
			FROM `tabQue` q
			LEFT JOIN `tabSales Invoice` direct_si
				ON direct_si.name = q.sales_invoice
				AND direct_si.docstatus = 1
				AND IFNULL(direct_si.is_return, 0) = 0
			LEFT JOIN `tabSales Invoice` linked_si
				ON linked_si.que_reference = q.name
				AND linked_si.docstatus = 1
				AND IFNULL(linked_si.is_return, 0) = 0
			LEFT JOIN `tabUser` u ON u.name = q.owner
			WHERE {' AND '.join(conditions)}
			ORDER BY q.date DESC, q.time DESC, q.creation DESC
		""",
		values,
		as_dict=True,
	)

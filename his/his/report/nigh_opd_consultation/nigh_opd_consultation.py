# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	data = get_data(filters)

	for index, row in enumerate(data, start=1):
		row.number = index

	return get_columns(), data


def get_columns():
	return [
		{"label": _("No."), "fieldname": "number", "fieldtype": "Int", "width": 60},
		{
			"label": _("Patient"),
			"fieldname": "patient",
			"fieldtype": "Link",
			"options": "Patient",
			"width": 140,
		},
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 240},
		{
			"label": _("Consultant"),
			"fieldname": "consultant",
			"fieldtype": "Link",
			"options": "Healthcare Practitioner",
			"width": 220,
		},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": _("Time"), "fieldname": "time", "fieldtype": "Time", "width": 100},
		{
			"label": _("Paid Amount"),
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		},
	]


def get_data(filters):
	conditions = [
		"q.practitioner = %(consultant)s",
		"TIME(q.time) BETWEEN '16:00:00' AND '22:00:00'",
	]
	values = {"consultant": "Dr Mohamed Mukhtar Kassim"}

	if filters.get("from_date"):
		conditions.append("q.date >= %(from_date)s")
		values["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("q.date <= %(to_date)s")
		values["to_date"] = filters.to_date

	return frappe.db.sql(
		f"""
			SELECT
				q.patient,
				q.patient_name,
				q.practitioner AS consultant,
				q.date,
				q.time,
				si.paid_amount,
				si.currency
			FROM `tabQue` q
			INNER JOIN `tabSales Invoice` si
				ON si.que_reference = q.name
				AND si.docstatus = 1
				AND IFNULL(si.is_return, 0) = 0
				AND si.paid_amount > 0
			WHERE {' AND '.join(conditions)}
				AND EXISTS (
					SELECT 1
					FROM `tabPatient Encounter` pe
					WHERE pe.que = q.name
						AND pe.patient = q.patient
						AND pe.practitioner = q.practitioner
						AND pe.encounter_date = q.date
						AND pe.docstatus = 1
				)
				AND NOT EXISTS (
					SELECT 1
					FROM `tabSales Invoice` returned_si
					WHERE returned_si.return_against = si.name
						AND returned_si.docstatus = 1
						AND returned_si.is_return = 1
				)
			ORDER BY q.date DESC, q.time DESC
		""",
		values,
		as_dict=True,
	)

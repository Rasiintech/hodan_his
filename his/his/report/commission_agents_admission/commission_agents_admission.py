# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	data = get_data(filters)
	admitted = sum(row.status == "Admitted" for row in data)
	discharged = sum(row.status == "Discharged" for row in data)
	report_summary = [
		{
			"value": len(data),
			"label": _("Total Patients"),
			"datatype": "Int",
			"indicator": "Blue",
		},
		{
			"value": admitted,
			"label": _("Admitted"),
			"datatype": "Int",
			"indicator": "Green",
		},
		{
			"value": discharged,
			"label": _("Discharged"),
			"datatype": "Int",
			"indicator": "Orange",
		},
	]
	return get_columns(), data, None, None, report_summary


def get_columns():
	return [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{
			"label": _("Sales Partner"),
			"fieldname": "sales_partner",
			"fieldtype": "Link",
			"options": "Sales Partner",
			"width": 190,
		},
		{
			"label": _("Patient ID"),
			"fieldname": "patient",
			"fieldtype": "Link",
			"options": "Patient",
			"width": 140,
		},
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 240},
		{
			"label": _("Admission Type"),
			"fieldname": "admission_type",
			"fieldtype": "Link",
			"options": "Inpatient Type",
			"width": 140,
		},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
	]


def get_data(filters):
	conditions = ["ir.status IN ('Admitted', 'Discharged')"]
	values = {}

	if filters.get("from_date"):
		conditions.append("DATE(ir.admitted_datetime) >= %(from_date)s")
		values["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("DATE(ir.admitted_datetime) <= %(to_date)s")
		values["to_date"] = filters.to_date

	if filters.get("sales_partner"):
		conditions.append("si.sales_partner = %(sales_partner)s")
		values["sales_partner"] = filters.sales_partner

	if filters.get("admission_type"):
		conditions.append("ir.type = %(admission_type)s")
		values["admission_type"] = filters.admission_type

	return frappe.db.sql(
		f"""
			SELECT
				DATE(ir.admitted_datetime) AS date,
				MIN(si.sales_partner) AS sales_partner,
				ir.patient,
				ir.patient_name,
				ir.type AS admission_type,
				ir.status
			FROM `tabInpatient Record` ir
			INNER JOIN `tabSales Invoice` si
				ON si.inpatient_record = ir.name
				AND si.docstatus = 1
				AND IFNULL(si.sales_partner, '') != ''
			WHERE {' AND '.join(conditions)}
			GROUP BY ir.name, DATE(ir.admitted_datetime), ir.patient, ir.patient_name, ir.type, ir.status
			ORDER BY DATE(ir.admitted_datetime) DESC, ir.admitted_datetime DESC
		""",
		values,
		as_dict=True,
	)

# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
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
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 220},
		{"label": _("Status"), "fieldname": "admission_status", "fieldtype": "Data", "width": 120},
		{
			"label": _("Admission Type"),
			"fieldname": "admission_type",
			"fieldtype": "Data",
			"width": 140,
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
	]


def get_data(filters):
	conditions = [
		"si.docstatus = 1",
		"IFNULL(si.patient, '') != ''",
		"IFNULL(si.sales_partner, '') != ''",
	]
	values = {}

	for fieldname in ("company", "sales_partner", "patient"):
		if filters.get(fieldname):
			conditions.append(f"si.{fieldname} = %({fieldname})s")
			values[fieldname] = filters[fieldname]

	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
		values["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
		values["to_date"] = filters.to_date

	if filters.get("admission_type"):
		conditions.append(
			"""(
				IFNULL(si.inpatient_record, '') != ''
				OR UPPER(TRIM(IFNULL(si.source_order, ''))) IN ('IPD', 'ADMISSION')
			) AND COALESCE(NULLIF(si.type, ''), NULLIF(ir.type, ''), 'IPD') = %(admission_type)s"""
		)
		values["admission_type"] = filters.admission_type

	status_expression = """
		CASE
			WHEN IFNULL(si.inpatient_record, '') != ''
				OR UPPER(TRIM(IFNULL(si.source_order, ''))) IN ('IPD', 'ADMISSION')
				THEN CASE WHEN ir.status = 'Discharged' THEN 'Discharged' ELSE 'Admitted' END
			WHEN UPPER(REPLACE(TRIM(IFNULL(si.source_order, '')), '.', '')) IN ('ER', 'EMERGENCY') THEN 'ER'
			ELSE 'OPD'
		END
	"""

	if filters.get("admission_status"):
		conditions.append(f"({status_expression}) = %(admission_status)s")
		values["admission_status"] = filters.admission_status

	return frappe.db.sql(
		f"""
			SELECT
				si.name AS sales_invoice,
				si.posting_date,
				si.sales_partner,
				si.patient,
				si.patient_name,
				{status_expression} AS admission_status,
				CASE
					WHEN IFNULL(si.inpatient_record, '') != ''
						OR UPPER(TRIM(IFNULL(si.source_order, ''))) IN ('IPD', 'ADMISSION')
						THEN COALESCE(NULLIF(si.type, ''), NULLIF(ir.type, ''), 'IPD')
					ELSE NULL
				END AS admission_type,
				si.net_total AS net_amount,
				si.currency
			FROM `tabSales Invoice` si
			LEFT JOIN `tabInpatient Record` ir ON ir.name = si.inpatient_record
			WHERE {' AND '.join(conditions)}
			ORDER BY si.posting_date DESC, si.creation DESC
		""",
		values,
		as_dict=True,
	)

# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = [], []
	




	filters = filters or {}

	columns = [
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": "Patient ID", "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 140},
		{"label": "Patient Name", "fieldname": "patient_name", "fieldtype": "Data", "width": 220},
		{"label": "Trauma Category", "fieldname": "trauma_category", "fieldtype": "Data", "width": 130},
		{"label": "ER Type", "fieldname": "er_type", "fieldtype": "Data", "width": 120},
		{"label": "Practitioner", "fieldname": "practitioner", "fieldtype": "Data", "width": 180},
	]

	conditions = ["IFNULL(et.mrp, '') IN ('Trauma', 'Non-Trauma')"]
	sql_filters = {}

	if filters.get("from_date"):
		conditions.append("COALESCE(em.encounter_date, et.date) >= %(from_date)s")
		sql_filters["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("COALESCE(em.encounter_date, et.date) <= %(to_date)s")
		sql_filters["to_date"] = filters.get("to_date")

	if filters.get("patient"):
		conditions.append("et.patient = %(patient)s")
		sql_filters["patient"] = filters.get("patient")

	if filters.get("practitioner"):
		conditions.append("COALESCE(NULLIF(em.practitioner, ''), et.practitioner) = %(practitioner)s")
		sql_filters["practitioner"] = filters.get("practitioner")

	if filters.get("trauma_category"):
		conditions.append("et.mrp = %(trauma_category)s")
		sql_filters["trauma_category"] = filters.get("trauma_category")

	if filters.get("er_type"):
		conditions.append("et.er_type = %(er_type)s")
		sql_filters["er_type"] = filters.get("er_type")

	query = """
		SELECT
			COALESCE(em.encounter_date, et.date) AS date,
			et.patient AS patient,
			et.patient_name AS patient_name,
			IFNULL(et.mrp, '') AS trauma_category,
			IFNULL(et.er_type, '') AS er_type,
			COALESCE(NULLIF(em.practitioner_name, ''), NULLIF(em.practitioner, ''), et.practitioner) AS practitioner
		FROM `tabEmergency Triage` et
		LEFT JOIN `tabEmergency` em ON em.que = et.que
		WHERE """ + " AND ".join(conditions) + """
		ORDER BY COALESCE(em.encounter_date, et.date) DESC, et.patient_name ASC, et.creation DESC
	"""

	result = frappe.db.sql(query, sql_filters, as_dict=True)

	data = [columns, result]




	return columns, result
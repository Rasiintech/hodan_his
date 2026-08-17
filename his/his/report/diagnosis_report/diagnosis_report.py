import frappe
from frappe import _
from frappe.utils import add_months, getdate, nowdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	filters.from_date = getdate(filters.get("from_date") or add_months(nowdate(), -1))
	filters.to_date = getdate(filters.get("to_date") or nowdate())

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be after To Date"))

	conditions = [
		"pe.docstatus < 2",
		"pe.encounter_date BETWEEN %(from_date)s AND %(to_date)s",
	]
	if filters.get("patient"):
		conditions.append("pe.patient = %(patient)s")
	if filters.get("sex"):
		conditions.append("pe.patient_sex = %(sex)s")
	if filters.get("district"):
		conditions.append("q.district = %(district)s")

	data = frappe.db.sql(
		f"""
		SELECT
			pe.patient,
			pe.encounter_date,
			pe.patient_age AS age,
			pe.patient_sex AS sex,
			GROUP_CONCAT(DISTINCT ped.diagnosis ORDER BY ped.idx SEPARATOR ', ') AS differential_diagnosis,
			GROUP_CONCAT(DISTINCT diagnosis.diagnosis ORDER BY diagnosis.idx SEPARATOR ', ') AS diagnosis_a,
			q.district
		FROM `tabPatient Encounter` pe
		LEFT JOIN `tabPatient Encounter Diagnosis` ped
			ON ped.parent = pe.name
			AND ped.parenttype = 'Patient Encounter'
			AND ped.parentfield = 'differential_diagnosis'
		LEFT JOIN `tabPatient Encounter Diagnosis` diagnosis
			ON diagnosis.parent = pe.name
			AND diagnosis.parenttype = 'Patient Encounter'
			AND diagnosis.parentfield = 'diagnosis_a'
		LEFT JOIN `tabQue` q ON q.name = pe.que
		WHERE {" AND ".join(conditions)}
		GROUP BY pe.name
		ORDER BY pe.encounter_date DESC, pe.encounter_time DESC, pe.creation DESC
		""",
		filters,
		as_dict=True,
	)
	for row_number, row in enumerate(data, start=1):
		row["row_number"] = row_number

	return get_columns(), data


def get_columns():
	return [
		{"label": _("No."), "fieldname": "row_number", "fieldtype": "Int", "width": 60},
		{"label": _("Encounter Date"), "fieldname": "encounter_date", "fieldtype": "Date", "width": 120},
		{"label": _("Patient ID"), "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 160},
				{"label": _("Age"), "fieldname": "age", "fieldtype": "Data", "width": 100},
		{"label": _("Sex"), "fieldname": "sex", "fieldtype": "Data", "width": 100},
		{"label": _("Differential Diagnosis"), "fieldname": "differential_diagnosis", "fieldtype": "Small Text", "width": 300},
		{"label": _("Diangosis"), "fieldname": "diagnosis_a", "fieldtype": "Small Text", "width": 300},
		{"label": _("District"), "fieldname": "district", "fieldtype": "Data", "width": 160},
	]

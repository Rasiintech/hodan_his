import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate


def as_filters(filters):
    filters = frappe._dict(filters or {})
    to_date = getdate(filters.get("to_date") or nowdate())
    from_date = getdate(filters.get("from_date") or add_days(to_date, -30))
    filters.from_date = from_date
    filters.to_date = to_date
    filters.from_datetime = f"{from_date} 00:00:00"
    filters.to_datetime = f"{add_days(to_date, 1)} 00:00:00"
    return filters


def execute(filters=None):
    filters = as_filters(filters)
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": _("Encounter ID"), "fieldname": "name", "fieldtype": "Link", "options": "Patient Encounter", "width": 140},
        {"label": _("Patient"), "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 120},
        {"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 180},
        {"label": _("Consultant"), "fieldname": "practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 180},
        {"label": _("Date"), "fieldname": "encounter_date", "fieldtype": "Date", "width": 100},
        {"label": _("Chief Complaint"), "fieldname": "cheif_complaint", "fieldtype": "Small Text", "width": 220},
        {"label": _("Past Medical History"), "fieldname": "past_medical_history", "fieldtype": "Small Text", "width": 220},
        {"label": _("Review of Systems (ROS)"), "fieldname": "ros", "fieldtype": "Small Text", "width": 220},
        {"label": _("Drug History"), "fieldname": "drug_history", "fieldtype": "Small Text", "width": 180},
        {"label": _("Nitration History"), "fieldname": "nitration_history", "fieldtype": "Small Text", "width": 180},
        {"label": _("Development History"), "fieldname": "development_history", "fieldtype": "Small Text", "width": 180},
        {"label": _("Vaccination History"), "fieldname": "vaccination_history", "fieldtype": "Small Text", "width": 180},
        {"label": _("Plan of Management"), "fieldname": "plan_of_management_", "fieldtype": "Small Text", "width": 220},
        {"label": _("Social History"), "fieldname": "social_history", "fieldtype": "Small Text", "width": 180},
        {"label": _("Family History"), "fieldname": "family_history", "fieldtype": "Small Text", "width": 180},
        {"label": _("Physical Examination"), "fieldname": "physical_examinationzzzzzzzzzzzs", "fieldtype": "Small Text", "width": 220},
    ]


def get_data(filters):
    conditions = ["pe.docstatus < 2", "pe.encounter_date BETWEEN %(from_date)s AND %(to_date)s"]

    if filters.get("patient"):
        conditions.append("pe.patient = %(patient)s")

    if filters.get("practitioner"):
        conditions.append("pe.practitioner = %(practitioner)s")

    return frappe.db.sql(
        f"""
        SELECT
            pe.name,
            pe.patient,
            pe.patient_name,
            pe.practitioner,
            pe.encounter_date,
            pe.cheif_complaint,
            pe.past_medical_history,
            pe.ros,
            pe.drug_history,
            pe.nitration_history,
            pe.development_history,
            pe.vaccination_history,
            pe.plan_of_management_,
            pe.social_history,
            pe.family_history,
            pe.physical_examinationzzzzzzzzzzzs
        FROM `tabPatient Encounter` pe
        WHERE {" AND ".join(conditions)}
        ORDER BY pe.encounter_date DESC, pe.creation DESC
        """,
        filters,
        as_dict=True,
    )

# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    if not filters or not filters.get("from_date") or not filters.get("to"):
        frappe.throw("Please select a valid date range.")

    columns, data = get_columns(), get_data(filters)
    return columns, data


def get_data(filters):
    _from, to = filters.get('from_date'), filters.get('to')
    cond = ""

    if filters.get("doctor"):
        cond += f" AND admission_practitioner = '{filters.get('doctor')}'"

    if filters.get("type"):
        cond += f" AND type = '{filters.get('type')}'"

    data = frappe.db.sql(f"""
        SELECT 
            patient,
            patient_name,
            type,
            room,
            bed,
            admission_practitioner,
            SUBSTRING(admitted_datetime, 1, 19) AS admitted_datetime,
            SUBSTRING(discharge_datetime, 1, 19) AS discharge_datetime,
            status
        FROM `tabInpatient Record`
        WHERE 
            date(creation) BETWEEN '{_from}' AND '{to}'
            AND status NOT IN ('Cancelled', 'Admission Scheduled')
            {cond}
        ORDER BY admitted_datetime DESC
    """, as_dict=1)

    return data


def get_columns():
    columns = [

        {
            "label": ("Patient"),
            "fieldtype": "Data",
            "fieldname": "patient_name",
            "width": 250,
        },
        {
            "label": ("Doctor"),
            "fieldtype": "Data",
            "fieldname": "admission_practitioner",
            "width": 250,
        },
        {
            "label": ("Room"),
            "fieldtype": "Data",
            "fieldname": "room",
            "width": 250,
        },
        {
            "label": ("Bed"),
            "fieldtype": "Data",
            "fieldname": "bed",
            "width": 250,
        },
        {
            "label": ("Type"),
            "fieldtype": "Data",
            "fieldname": "type",
            "width": 250,
        },
        {
            "label": ("Status"),
            "fieldtype": "Data",
            "fieldname": "status",
            "width": 250,
        },
        {
            "label": ("Admission Date"),
            "fieldtype": "Datetime",
            "fieldname": "admitted_datetime",
            "width": 200,
        },
        {
            "label": ("Discharged Date"),
            "fieldtype": "Datetime",
            "fieldname": "discharge_datetime",
            "width": 200,
        },
        {
            "label": ("Discharged Status"),
            "fieldtype": "Data",
            "fieldname": "status_",
            "width": 150,
        }
    ]
    return columns

# Copyright (c) 2025, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder import DocType

def execute(filters=None):
    filters = frappe._dict(filters or {})
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": "Patient Name", "fieldname": "patient_name", "fieldtype": "Data", "width": 250},
        {"label": "Age",          "fieldname": "age",          "fieldtype": "Data", "width": 200},
        {"label": "Type",         "fieldname": "age_type",     "fieldtype": "Data", "width": 100},
        {"label": "Sex",          "fieldname": "sex",          "fieldtype": "Data", "width": 100},
        {"label": "Test Name",    "fieldname": "test_name",    "fieldtype": "Data", "width": 250},
        {"label": "Result",       "fieldname": "result_value", "fieldtype": "Data", "width": 200},
        # {"label": "Flag",         "fieldname": "flag", "fieldtype": "Data", "width": 200},
        {"label": "Normal Range",         "fieldname": "normal_range", "fieldtype": "Data", "width": 200},
    ]


def get_data(filters):
    LR  = DocType("Lab Result")
    NTR = DocType("Normal Test Result")
    PT  = DocType("Patient")

    q = (
        frappe.qb.from_(LR)
        .join(NTR).on(NTR.parent == LR.name)
        .join(PT).on(PT.name == LR.patient)
        .select(
            LR.patient_name.as_("patient_name"),
            LR.patient_age.as_("age"),
            PT.age_type.as_("age_type"),
            PT.sex.as_("sex"),
            NTR.lab_test_name.as_("test_name"),
            NTR.result_value.as_("result_value"),
            NTR.flag.as_("flag"),
            NTR.normal_range.as_("normal_range"),
        )
        .where(LR.docstatus != 2)
    )

    # Date range (inclusive)
    if filters.get("from_date"):
        q = q.where(LR.date >= filters.from_date)
    if filters.get("to_date"):
        q = q.where(LR.date <= filters.to_date)

    # Optional filters
    if filters.get("lab_test_name"):
        q = q.where(NTR.lab_test_name == filters.lab_test_name)

    if filters.get("patient"):
        # filters.patient should be the Patient ID (name)
        q = q.where(LR.patient == filters.patient)

    # Run the query and return as dict rows
    return q.run(as_dict=True)

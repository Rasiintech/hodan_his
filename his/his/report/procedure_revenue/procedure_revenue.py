import frappe
from frappe import _

# Function to define the report columns
def get_detailed_columns():
    return [
        {"label": _("Patient"), "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 150},
        {"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 200},
        {"label": _("Practitioner"), "fieldname": "ref_practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 150},  # Changed to Data for Practitioner
        {"label": _("Invoice Number"), "fieldname": "invoice_number", "fieldtype": "Link", "options": "Sales Invoice", "width": 150},
        {"label": _("Procedure Name"), "fieldname": "procedure_name", "fieldtype": "Link", "options": "Clinical Procedure Template",  "width": 200},  # Changed to Data for Procedure Name
        {"label": _("Medical Department"), "fieldname": "medical_department", "fieldtype": "Link", "options": "Medical Department", "width": 200},  # Changed to Data for Procedure Name
        {"label": _("Rate"), "fieldname": "procedure_rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Net Rate"), "fieldname": "net_rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Discount Amount"), "fieldname": "discount_amount", "fieldtype": "Currency", "width": 100},
    ]

# Function to execute the report logic
def execute(filters=None):
    columns = get_detailed_columns()  # Use the new column definition function

    # Build query filters
    conditions = []
    if filters.get("patient"):
        conditions.append(f"si.patient = '{filters.get('patient')}'")
    if filters.get("practitioner"):
        conditions.append(f"si.ref_practitioner = '{filters.get('practitioner')}'")
    if filters.get("medical_department"):
        conditions.append(f"cpt.medical_department = '{filters.get('medical_department')}'")
    if filters.get("procedure_name"):
        conditions.append(f"cpt.template = '{filters.get('procedure_name')}'")
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append(f"si.posting_date BETWEEN '{filters.get('from_date')}' AND '{filters.get('to_date')}'")

    # SQL query to fetch the data
    query = f"""
        SELECT
            si.patient,
            si.patient_name,
            si.ref_practitioner,
            si.name AS invoice_number,
            cpt.template AS procedure_name,  # Correct field for procedure name
            cpt.medical_department AS medical_department,  # Correct field for procedure name
            ROUND(cpt.rate, 2) AS procedure_rate,      # Correct field for rate
            ROUND(sii.net_amount, 2) AS net_rate,
            ROUND((cpt.rate - sii.net_amount), 2) AS discount_amount
        FROM
            `tabSales Invoice` si
        JOIN
            `tabSales Invoice Item` sii ON sii.parent = si.name
        JOIN
            `tabClinical Procedure Template` cpt ON cpt.template = sii.item_code
        WHERE
            si.docstatus = 1
            {f"AND {' AND '.join(conditions)}" if conditions else ''}
        ORDER BY
            si.posting_date
    """

    # Execute the query
    data = frappe.db.sql(query, as_dict=True)

    return columns, data

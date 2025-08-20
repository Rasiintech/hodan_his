import frappe
from frappe import _

# Function to define the report columns
def get_detailed_columns():
    return [
        {"label": _("Sales Order"), "fieldname": "sn", "fieldtype": "Link", "options": "Sales Order", "width": 150},  # Updated to match "S.name"
        {"label": _("Transaction Date"), "fieldname": "transaction_date", "fieldtype": "Date", "width": 100},  # Updated to match "S.transaction_date"
        {"label": _("Patient"), "fieldname": "patient", "fieldtype": "Link", "options": "Patient", "width": 150},  # Updated to match "S.patient"
        {"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 200},  # Updated to match "S.patient_name"
        {"label": _("Customer Group"), "fieldname": "customer_group", "fieldtype": "Data", "width": 200},  # Updated to match "S.patient_name"
        {"label": _("Mobile No"), "fieldname": "mobile_no", "fieldtype": "Data", "width": 120},  # Updated to match "P.mobile_no"
        {"label": _("Practitioner"), "fieldname": "ref_practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 150},  # Updated to match "S.ref_practitioner"
        {"label": _("Medical Department"), "fieldname": "medical_department", "fieldtype": "Link", "options": "Medical Department", "width": 200},  # Updated to match "S.medical_department"
        {"label": _("Service Name"), "fieldname": "item_code", "fieldtype": "Link", "options": "Clinical Procedure Template", "width": 250},  # Updated to match "I.item_code"
        {"label": _("Service Type"), "fieldname": "item_group", "fieldtype": "Data", "width": 120},  # Updated to match "I.item_group"
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},  # Updated to match the CASE result "Status"
        {"label": _("Quantity"), "fieldname": "qty", "fieldtype": "Int", "width": 100},  # Updated to match "I.qty"
        {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 100},  # Updated to match "I.rate"
        {"label": _("Sales Rate"), "fieldname": "sales_net_rate", "fieldtype": "Currency", "width": 100},  # Updated to match "I.net_amount"
        {"label": _("Discount"), "fieldname": "discount", "fieldtype": "Currency", "width": 100},  # Updated to match "I.net_amount"
    ]

# Function to execute the report logic
def execute(filters=None):
    columns = get_detailed_columns()  # Use the new column definition function

    # Build query filters
    conditions = []
    if filters.get("patient"):
        conditions.append(f"S.patient = '{filters.get('patient')}'")
    if filters.get("practitioner"):
        conditions.append(f"S.ref_practitioner = '{filters.get('practitioner')}'")
    if filters.get("medical_department"):
        conditions.append(f"R.medical_department = '{filters.get('medical_department')}'")
    if filters.get("customer_group"):
        conditions.append(f"S.customer_group = '{filters.get('customer_group')}'")
    if filters.get("item_group"):
        conditions.append(f"R.item_group = '{filters.get('item_group')}'")
    if filters.get("procedure_name"):
        conditions.append(f"R.template = '{filters.get('procedure_name')}'")
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append(f"S.transaction_date BETWEEN '{filters.get('from_date')}' AND '{filters.get('to_date')}'")

    # SQL query to fetch the data
    query = f"""
       SELECT
            R.name as "procedure",
            S.name AS "sn",  -- Sales Order Name
            S.transaction_date AS "transaction_date", 
            S.patient AS "patient", 
            S.patient_name AS "patient_name", 
            S.customer_group AS "customer_group", 
            P.mobile_no AS "mobile_no",  
            S.ref_practitioner AS "ref_practitioner", 
            S.medical_department AS "medical_department", 
            I.item_code AS "item_code", 
            R.item_group AS "item_group",
            I.name as "sales_order_item",
            S.name as sales_order,
            -- CASE statement for the status based on qty
            CASE 
                WHEN I.delivered_qty = 1 THEN 'Completed'
                WHEN I.delivered_qty = 0 THEN 'To Deliver and Bill'
                ELSE S.status
            END AS "status",
            I.qty AS "qty", 
            ROUND(R.rate, 2) AS "rate"
        FROM 
            `tabSales Order` S
        JOIN 
            `tabSales Order Item` I ON S.name = I.parent
        JOIN 
            `tabClinical Procedure Template` R ON I.item_code = R.name  
        LEFT JOIN 
            `tabPatient` P ON S.patient = P.name  
        WHERE 
            S.docstatus = 1
            {f"AND {' AND '.join(conditions)}" if conditions else ''}
        ORDER BY 
            S.transaction_date DESC;
    """

    # Execute the query
    data = frappe.db.sql(query, as_dict=True)
        # Initialize the result list
    result = []
    
    # Loop through the data and update the rate with anesthesia charges
    for i in data:
        pro = frappe.get_doc("Clinical Procedure Template", {"name": i.procedure})

        # Sum the anesthesia charges
        sum_of_anes = 0
        for j in pro._aneasthesia_prescription:  # Assuming _aneasthesia_prescription is a child table
            sum_of_anes += j.amount

        # Update the rate
        updated_rate = i.rate + sum_of_anes
        
        
        
        # Append the updated data to the result list
        rate_doc = frappe.get_doc("Sales Invoice Item", {"so_detail": i.sales_order_item, "docstatus": 1}) if frappe.get_all("Sales Invoice Item", filters={"so_detail": i.sales_order_item, "docstatus": 1}) else None
        

        rate_doc_anesthia_charge = frappe.get_doc("Sales Invoice Item", {"sales_order": i.sales_order, "item_code": "Anesthesia Charge", "docstatus": 1}) if frappe.get_all("Sales Invoice Item", filters={"sales_order": i.sales_order, "item_code": "Anesthesia Charge", "docstatus": 1}) else None
        
        rate_doc_ot_charge = frappe.get_doc("Sales Invoice Item", {"sales_order": i.sales_order, "item_code": "OT Charge", "docstatus": 1}) if frappe.get_all("Sales Invoice Item", filters={"sales_order": i.sales_order, "item_code": "OT Charge", "docstatus": 1}) else None
        
        rate = rate_doc.net_rate if rate_doc else 0
        rate = rate + (rate_doc_anesthia_charge.net_rate if rate_doc_anesthia_charge else 0)
        rate = rate + (rate_doc_ot_charge.net_rate if rate_doc_ot_charge else 0)
        discount=0
        if rate:
            discount= updated_rate - rate
        result.append({
            **i,  # Include all original fields
            "rate": updated_rate , # Override the rate field with the updated rate
            "sales_net_rate": rate,
            "discount" : discount
        })
        
        
    
    return columns, result
// Copyright (c) 2025, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Procedure Revenue"] = {
	"filters": [
		{
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 0,
			"default": frappe.datetime.get_today()
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "reqd": 0,
			"default": frappe.datetime.get_today()
        },
		{
            "fieldname": "patient",
            "label": __("Patient"),
            "fieldtype": "Link",
            "options": "Patient",
            "reqd": 0
        },
        {
            "fieldname": "customer_group",
            "label": __("Customer Group"),
            "fieldtype": "Link",
            "options": "Customer Group",
            "reqd": 0
        },
        {
            "fieldname": "practitioner",
            "label": __("Practitioner"),
            "fieldtype": "Link",
            "options": "Healthcare Practitioner",
            "reqd": 0
        },
		{
            "fieldname": "medical_department",
            "label": __("Medical Department"),
            "fieldtype": "Link",
            "options": "Medical Department",
            "reqd": 0
        },
        {
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group",
            "reqd": 0
        },
		{
            "fieldname": "procedure_name",
            "label": __("Procedure Template"),
            "fieldtype": "Link",
            "options": "Clinical Procedure Template",
            "reqd": 0
        },
		
        
	]
};

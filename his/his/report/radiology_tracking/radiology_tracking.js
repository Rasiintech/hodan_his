// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Radiology Tracking"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "consultant",
			"label": __("Consultant"),
			"fieldtype": "Link",
			"options": "Healthcare Practitioner"
		},
		{
			"fieldname": "patient",
			"label": __("Patient ID"),
			"fieldtype": "Link",
			"options": "Patient"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nCompleted\nPending\nRefunded"
		}
	]
};

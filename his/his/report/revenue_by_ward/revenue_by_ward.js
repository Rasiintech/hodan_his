// Copyright (c) 2025, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Revenue by Ward"] = {
	"filters": [
		{
			"fieldname": "start_date",
			"label": "Start Date",
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
		},
		{
			"fieldname": "end_date",
			"label": "End Date",
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
		},
		{
			"fieldname": "ward",
			"label": "Ward",
			"fieldtype": "Link",
			"options": "Ward"
		}
	]
};

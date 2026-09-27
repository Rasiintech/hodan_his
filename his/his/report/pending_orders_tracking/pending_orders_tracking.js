// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Pending Orders Tracking"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "patient",
			label: __("Patient"),
			fieldtype: "Link",
			options: "Patient",
		},
		{
			fieldname: "consultant",
			label: __("Consultant"),
			fieldtype: "Link",
			options: "Healthcare Practitioner",
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
		},
	],
};

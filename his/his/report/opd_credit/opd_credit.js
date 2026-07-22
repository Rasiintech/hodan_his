// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["OPD Credit"] = {
	filters: [
		{
		  fieldname: "from_date",
		  label: __("From Date"),
		  fieldtype: "Date",
		  default: frappe.datetime.now_date(),
		  reqd: 1,
		},
		{
		  fieldname: "to_date",
		  label: __("To Date"),
		  fieldtype:  "Date",
		  default: frappe.datetime.now_date(),
		  reqd: 1,
		}
	  ],
};

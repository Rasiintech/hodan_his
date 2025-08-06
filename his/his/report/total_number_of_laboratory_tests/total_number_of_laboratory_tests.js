// Copyright (c) 2025, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Total Number of Laboratory Tests"] = {
	"filters": [
		{
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "source_order",
            "label": "Source Order",
            "fieldtype": "Link",
            "options": "Source Order"
        },
        {
            "fieldname": "item_code",
            "label": "Test Name",
            "fieldtype": "Link",
            "options": "Item"
        }
	]
};

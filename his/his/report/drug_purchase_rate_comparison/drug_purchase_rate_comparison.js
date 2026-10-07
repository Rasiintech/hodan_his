// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Drug Purchase Rate Comparison"] = {
	filters: [
		{
			fieldname: "previous_from_date",
			label: __("Previous From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -59),
			reqd: 1
		},
		{
			fieldname: "previous_to_date",
			label: __("Previous To Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -30),
			reqd: 1
		},
		{
			fieldname: "from_date",
			label: __("Current From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -29),
			reqd: 1
		},
		{
			fieldname: "to_date",
			label: __("Current To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
			default: "Drug"
		},
		{fieldname: "item_code", label: __("Item"), fieldtype: "Link", options: "Item"},
		{fieldname: "supplier", label: __("Supplier"), fieldtype: "Link", options: "Supplier"},
		{
			fieldname: "top_n",
			label: __("Top Items"),
			fieldtype: "Int",
			default: 10,
			description: __("Enter 0 or leave blank to show all changed items")
		}
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && ["saving", "reduction_percent"].includes(column.fieldname)) {
			const amount = Number(data[column.fieldname]) || 0;
			if (amount !== 0) {
				const color = amount < 0 ? "#dc2626" : "#16803c";
				return `<span style="color:${color};font-weight:600">${value}</span>`;
			}
		}
		return value;
	}
};

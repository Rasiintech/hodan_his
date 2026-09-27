// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.query_reports["Hospital Management Cash Flow"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: "Hodan Hospital",
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.year_start(),
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
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
			get_query: () => ({ filters: { company: frappe.query_report.get_filter_value("company") } }),
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "finance_book",
			label: __("Finance Book"),
			fieldtype: "Link",
			options: "Finance Book",
		},
	],
	formatter(value, row, column, data, default_formatter) {
		if (column.fieldname === "amount" && data && data.amount === 0) {
			value = "-";
		} else if (column.fieldname === "amount" && data && data.amount < 0) {
			value = `(${format_currency(Math.abs(data.amount), column.label)})`;
		} else {
			value = default_formatter(value, row, column, data);
		}
		if (data && (data.is_section || data.is_heading || data.is_subtotal || data.is_total)) {
			value = `<b>${value}</b>`;
		}
		return value;
	},
};

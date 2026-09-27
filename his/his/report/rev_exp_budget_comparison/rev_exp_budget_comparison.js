// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.query_reports["Rev Exp Budget Comparison"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
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
			get_query: () => ({
				filters: { company: frappe.query_report.get_filter_value("company") },
			}),
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.is_title) {
			if (column.fieldname !== "account_group") {
				return "";
			}
			return `<span style="color: red; font-weight: bold">${value}</span>`;
		}
		if (data && data.bold) {
			value = `<b>${value}</b>`;
		}
		if (data && ["budget_variance", "last_month_variance"].includes(column.fieldname)) {
			const amount = flt(data[column.fieldname]);
			if (amount < 0) {
				value = `<span style="color: red">${value}</span>`;
			} else if (amount > 0) {
				value = `<span style="color: green">${value}</span>`;
			}
		}
		return value;
	},
};

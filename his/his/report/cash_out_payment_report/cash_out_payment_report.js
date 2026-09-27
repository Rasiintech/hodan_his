// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.query_reports["Cash Out Payment Report"] = {
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
			fieldname: "account",
			label: __("Cash / Bank Account"),
			fieldtype: "Link",
			options: "Account",
			get_query() {
				return {
					filters: {
						company: frappe.query_report.get_filter_value("company"),
						is_group: 0,
						account_type: ["in", ["Cash", "Bank"]],
					},
				};
			},
		},
	],

	formatter(value, row, column, data, default_formatter) {
		if (data && data.is_blank) {
			return "";
		}

		value = default_formatter(value, row, column, data);
		if (data && data.is_group_total) {
			value = `<span style="font-weight: 700; color: #111;">${value}</span>`;
		}
		if (data && data.is_grand_total) {
			value = `<span style="font-weight: 700; color: #d11;">${value}</span>`;
		}
		return value;
	},
};

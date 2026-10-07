// Copyright (c) 2026, Hodan Hospital and contributors
// For license information, please see license.txt

frappe.query_reports["Balance Sheet Notes"] = {
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
			default: frappe.datetime.add_months(frappe.datetime.month_start(), -2),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
			reqd: 1,
		},
		{
			fieldname: "periodicity",
			label: __("Periodicity"),
			fieldtype: "Select",
			options: ["Monthly", "Quarterly", "Half-Yearly", "Yearly"],
			default: "Monthly",
			reqd: 1,
		},
		{
			fieldname: "note",
			label: __("Note"),
			fieldtype: "Select",
			options: [
				"All Notes",
				"Note 1 - Current Assets",
				"Note 2 - Fixed Assets",
				"Note 3 - Current Liabilities",
			],
			default: "All Notes",
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

	formatter: function (value, row, column, data, default_formatter) {
		if (!data) return default_formatter(value, row, column, data);

		let formatted;
		if (column.fieldname.endsWith("_pct")) {
			if (value == null || value === "") {
				formatted = "";
			} else if (data.group_header || data.total) {
				formatted = Math.round(flt(value)) + "%";
			} else {
				formatted = flt(value).toFixed(1) + "%";
			}
		} else {
			formatted = default_formatter(value, row, column, data);
		}
		let style = "";

		if (data.note_title) {
			style += "background-color:#ffc000;font-weight:700;display:block;padding:3px 6px;";
		}
		if (data.group_header) style += "font-weight:700;";
		if (data.total) style += "font-weight:700;border-top:1px solid #444;display:block;padding:2px 4px;";
		if (
			column.fieldname !== "sn" &&
			!column.fieldname.endsWith("_pct") &&
			!data.note_title &&
			flt(data[column.fieldname]) < 0
		)
			style += "color:#c0392b;";

		if (style) formatted = `<span style="${style}">${formatted}</span>`;
		return formatted;
	},
};

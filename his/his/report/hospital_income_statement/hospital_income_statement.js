// Copyright (c) 2026, Hodan Hospital and contributors
// For license information, please see license.txt

frappe.query_reports["Hospital Income Statement"] = {
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
		if (!data || !data.account) return default_formatter(value, row, column, data);

		let formatted;
		if (data.is_percent && column.fieldname !== "account") {
			formatted = value == null ? "" : flt(value).toFixed(1) + "%";
		} else {
			formatted = default_formatter(value, row, column, data);
		}

		let style = "";
		if (data.bold) style += "font-weight:700;";
		if (data.red && column.fieldname === "account") style += "color:#c0392b;";
		if (column.fieldname !== "account" && flt(data[column.fieldname]) < 0 && !data.is_percent)
			style += "color:#c0392b;";
		if (data.section) style += "background-color:#d9d9d9;display:block;padding:2px 4px;";
		if (data.net_profit) style += "background-color:#ffc000;display:block;padding:2px 4px;";
		if (data.total && column.fieldname === "account") style += "text-transform:none;";

		if (style) formatted = `<span style="${style}">${formatted}</span>`;

		if (data.note_report && column.fieldname === "account") {
			formatted = `<a style="cursor:pointer;text-decoration:underline;"
				onclick="frappe.query_reports['Hospital Income Statement'].open_note('${data.note_report}', '${data.note_filter || ""}')">${formatted}</a>`;
		}
		return formatted;
	},

	open_note: function (report_name, note) {
		frappe.route_options = frappe.query_report.get_filter_values();
		if (note) frappe.route_options.note = note;
		frappe.set_route("query-report", report_name);
	},
};

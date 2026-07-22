// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

const DETAIL_REPORT_VIEWS = {
	Department: {
		filter_field: "department",
	},
	Consultant: {
		filter_field: "consultant",
	},
};

function toggle_detail_filters() {
	const report = frappe.query_report;
	const view_by = report.get_filter_value("view_by") || "Department";
	const active_filter = DETAIL_REPORT_VIEWS[view_by].filter_field;

	["department", "consultant"].forEach((fieldname) => {
		const filter = report.get_filter(fieldname);
		if (!filter) return;

		const is_active = fieldname === active_filter;
		filter.df.hidden = !is_active;
		filter.df.reqd = is_active ? 1 : 0;

		if (!is_active) {
			filter.set_value("");
		}

		filter.refresh();
		filter.$wrapper.toggle(is_active);
	});
}

frappe.query_reports["Department Detail Profit and Loss"] = {
	filters: [
		{
			fieldname: "view_by",
			label: "View By",
			fieldtype: "Select",
			options: "Department\nConsultant",
			default: "Department",
			reqd: 1,
			on_change: function() {
				toggle_detail_filters();
				frappe.query_report.refresh();
			}
		},
		{
			fieldname: "department",
			label: "Department",
			fieldtype: "Link",
			options: "Medical Department",
			reqd: 1
		},
		{
			fieldname: "consultant",
			label: "Consultant",
			fieldtype: "Link",
			options: "Healthcare Practitioner",
			hidden: 1
		},
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
			reqd: 1
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
			reqd: 1
		}
	],

	onload: function(report) {
		toggle_detail_filters();
	},

	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) return value;

		const view_by = frappe.query_report.get_filter_value("view_by") || "Department";
		const header_value = frappe.query_report.get_filter_value(
			DETAIL_REPORT_VIEWS[view_by].filter_field
		);

		if (
			data.entity === header_value ||
			["Income", "Expenses", "Direct Expense", "Indirect Expense", "Total Expense", "Net Profit & Loss"].includes(data.entity)
		) {
			return `<b>${value || ""}</b>`;
		}

		if (
			column.fieldname === "amount" &&
			parseFloat(data.amount || 0) < 0
		) {
			return `<span style="color:red;font-weight:600">${value || ""}</span>`;
		}

		if (
			column.fieldname === "amount" &&
			data.entity === "Net Profit & Loss" &&
			parseFloat(data.amount || 0) > 0
		) {
			return `<span style="color:green;font-weight:700">${value || ""}</span>`;
		}

		return value;
	}
};

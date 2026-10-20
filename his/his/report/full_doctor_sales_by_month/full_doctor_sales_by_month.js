// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Full Doctor Sales by Month"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.month_start(), -5),
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
			fieldname: "ref_practitioner",
			label: __("Doctor"),
			fieldtype: "Link",
			options: "Healthcare Practitioner",
			reqd: 1,
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
	],

	onload(query_report) {
		query_report._no_refresh = true;
		query_report
			.get_filter("from_date")
			.set_value(frappe.datetime.add_months(frappe.datetime.month_start(), -5));
		query_report
			.get_filter("to_date")
			.set_value(frappe.datetime.get_today());
		query_report._no_refresh = false;
		query_report.pdf_report = () => {
			open_url_post(
				"/api/method/his.his.report.full_doctor_sales_by_month.full_doctor_sales_by_month.download_pdf",
				{ filters: JSON.stringify(query_report.get_filter_values(true)) },
				true
			);
		};
	},

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "grand_total") {
			return `<strong style="color:#b66c00">${value}</strong>`;
		}
		return value;
	},

	after_datatable_render(datatable) {
		datatable.footer.innerHTML = "";
		datatable.options.showTotalRow = true;
		datatable.bodyRenderer.renderFooter();
		datatable.options.showTotalRow = false;

		const $wrapper = $(datatable.wrapper);
		const $total = $wrapper.find(".dt-row-totalRow");
		const account_column = datatable.datamanager
			.getColumns()
			.find((column) => column.id === "item");

		$wrapper.find(".dt-footer").css({
			"z-index": 20,
			"box-shadow": "0 -2px 8px rgba(48, 56, 60, 0.14)",
		});
		$total.find(".dt-cell").css({
			background: "#f7f9f8",
			"border-top": "2px solid #dfe5e2",
			"font-weight": 700,
			color: "#b66c00",
		});
		$total.find(".dt-cell--col-0 .dt-cell__content").empty();
		if (account_column) {
			$total
				.find(`.dt-cell--col-${account_column.colIndex} .dt-cell__content`)
				.text(__("Total"))
				.css("color", "#30383c");
		}
	},
};

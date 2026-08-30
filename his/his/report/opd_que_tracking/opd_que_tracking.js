// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["OPD Que Tracking"] = {
	after_datatable_render(datatable) {
		const renumber_visible_rows = () => {
			const rows = datatable.datamanager.rows;
			const visible_rows =
				datatable.datamanager._filteredRows || rows.map((row) => row.meta.rowIndex);
			const number_column = datatable.datamanager.getColumnIndexById("_rowIndex");

			if (number_column < 0) return;

			visible_rows.forEach((row_index, index) => {
				const cell = rows[row_index][number_column];
				cell.content = String(index + 1);
				cell.html = String(index + 1);
				const selector = `.dt-row-${row_index} .dt-cell--col-${number_column} .dt-cell__content`;
				$(selector, frappe.query_report.$report).text(index + 1);
			});
		};

		let renumber_timer;
		frappe.query_report.$report
			.off("keyup.opd_que_tracking", ".dt-filter")
			.on("keyup.opd_que_tracking", ".dt-filter", () => {
				clearTimeout(renumber_timer);
				renumber_timer = setTimeout(renumber_visible_rows, 500);
			});

		renumber_visible_rows();
	},
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
			fieldtype: "Date",
			default: frappe.datetime.now_date(),
			reqd: 1,
		},
		{
			fieldname: "consultant",
			label: __("Consultant"),
			fieldtype: "Link",
			options: "Healthcare Practitioner",
		},
	],
};

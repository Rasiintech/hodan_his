// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["CT-MRI Sales Partner"] = {
	filters: [
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
			default: frappe.datetime.month_end(),
			reqd: 1,
		},
		{
			fieldname: "sales_partner",
			label: __("Sales Partner"),
			fieldtype: "Link",
			options: "Sales Partner",
		},
		{
			fieldname: "patient",
			label: __("Patient ID"),
			fieldtype: "Link",
			options: "Patient",
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Select",
			options: "\nMRI\nCT Scan",
		},
		{
			fieldname: "payment_status",
			label: __("Payment Status"),
			fieldtype: "Select",
			options: "\nPaid\nPending\nReturn",
		},
	],

	after_datatable_render(datatable) {
		if (datatable.__sequential_row_numbers) {
			return;
		}

		const filter_rows = datatable.datamanager.filterRows.bind(datatable.datamanager);
		datatable.datamanager.filterRows = (filters) =>
			filter_rows(filters).then((result) => {
				result.rowsToShow.forEach((row_index, position) => {
					datatable.cellmanager.updateCell(0, row_index, String(position + 1));
				});
				return result;
			});

		datatable.__sequential_row_numbers = true;
	},
};

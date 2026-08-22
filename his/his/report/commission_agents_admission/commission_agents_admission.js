// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Commission-Agents Admission"] = {
	filters: [
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
			fieldname: "sales_partner",
			label: __("Sales Partner"),
			fieldtype: "Link",
			options: "Sales Partner",
		},
		{
			fieldname: "admission_type",
			label: __("Admission Type"),
			fieldtype: "Link",
			options: "Inpatient Type",
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

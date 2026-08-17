frappe.query_reports["Diagnosis Report"] = {
	get_datatable_options(options) {
		options.serialNoColumn = false;
		return options;
	},
	after_datatable_render(datatable) {
		const renumber_visible_rows = () => {
			const rows = datatable.datamanager.rows;
			const visible_rows =
				datatable.datamanager._filteredRows || rows.map((row) => row.meta.rowIndex);
			const number_column = rows[0]?.findIndex(
				(cell) => cell.column && cell.column.id === "row_number"
			);

			if (number_column < 0) return;

			visible_rows.forEach((row_index, index) => {
				const cell = rows[row_index][number_column];
				cell.content = index + 1;
				cell.html = String(index + 1);
				const selector = `.dt-row-${row_index} .dt-cell--col-${number_column} .dt-cell__content`;
				$(selector, frappe.query_report.$report).text(index + 1);
			});
		};

		let renumber_timer;
		frappe.query_report.$report
			.off("keyup.diagnosis_report", ".dt-filter")
			.on("keyup.diagnosis_report", ".dt-filter", () => {
				clearTimeout(renumber_timer);
				renumber_timer = setTimeout(renumber_visible_rows, 400);
			});

		renumber_visible_rows();
	},
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
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
			fieldname: "patient",
			label: __("Patient ID"),
			fieldtype: "Link",
			options: "Patient",
		},
		{
			fieldname: "sex",
			label: __("Sex"),
			fieldtype: "Select",
			options: "\nMale\nFemale",
		},
		{
			fieldname: "district",
			label: __("District"),
			fieldtype: "Data",
		},
	],
};

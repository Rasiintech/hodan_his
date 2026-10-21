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
		$wrapper.addClass("doctor-sales-primary");
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

		this.render_opd_table(datatable);
	},

	render_opd_table(datatable) {
		const query_report = frappe.query_report;
		const filters = query_report.get_filter_values(true);
		const request_key = JSON.stringify(filters);
		const $datatable = $(datatable.wrapper);
		const rendered_widths = $datatable
			.find(".dt-header .dt-row")
			.first()
			.children(".dt-cell")
			.toArray()
			.map((cell) => Math.round(cell.getBoundingClientRect().width))
			.filter((width) => width > 0);
		$datatable.siblings(".doctor-opd-monthly").remove();

		const $section = $(`
			<div class="doctor-opd-monthly">
				<h4>${__("OPD Queue by Month")}</h4>
				<div class="doctor-opd-loading text-muted">${__("Loading OPD queue…")}</div>
			</div>
		`);
		$datatable.before($section);
		query_report._opd_request_key = request_key;

		frappe.call({
			method:
				"his.his.report.full_doctor_sales_by_month.full_doctor_sales_by_month.get_opd_table",
			args: { filters: request_key },
			callback: (response) => {
				if (query_report._opd_request_key !== request_key || !$section.closest("body").length) {
					return;
				}
				const result = response.message || { months: [], rows: [] };
				const months = result.months || [];
				const rows = result.rows || [];
				const month_fields = months.map((month) => month.fieldname);
				const totals = Object.fromEntries(month_fields.map((fieldname) => [fieldname, 0]));
				let grand_total = 0;
				const escape = (value) => $("<div>").text(value == null ? "" : value).html();

				const body = rows
					.map((row, index) => {
						grand_total += Number(row.grand_total || 0);
						month_fields.forEach(
							(fieldname) => (totals[fieldname] += Number(row[fieldname] || 0))
						);
						return `<tr><td class="opd-index">${index + 1}</td><td>${escape(
							row.item
						)}</td>${month_fields
							.map(
								(fieldname) =>
									`<td class="opd-number">${Number(row[fieldname] || 0).toLocaleString()}</td>`
							)
							.join("")}<td class="opd-number opd-grand">${Number(
							row.grand_total || 0
						).toLocaleString()}</td></tr>`;
					})
					.join("");
				const header = months.map((month) => `<th>${escape(month.label)}</th>`).join("");
				const footer = month_fields
					.map((fieldname) => `<td class="opd-number">${totals[fieldname].toLocaleString()}</td>`)
					.join("");
				const expected_columns = months.length + 3;
				const column_widths =
					rendered_widths.length >= expected_columns
						? rendered_widths.slice(0, expected_columns)
						: [40, 360, ...months.map(() => 145), 155];
				const column_group = column_widths
					.map((width) => `<col style="width:${width}px">`)
					.join("");
				const table_width = column_widths.reduce((total, width) => total + width, 0);

				$section.find(".doctor-opd-loading").replaceWith(`
					<div class="doctor-opd-scroll">
						<table style="width:${table_width}px;min-width:${table_width}px;table-layout:fixed">
							<colgroup>${column_group}</colgroup>
							<thead><tr><th class="opd-index">#</th><th>${__("Item")}</th>${header}<th>${__("Grand Total")}</th></tr></thead>
							<tbody>${body}</tbody>
							<tfoot><tr><td></td><td>${__("Total OPD Queue")}</td>${footer}<td class="opd-number">${grand_total.toLocaleString()}</td></tr></tfoot>
						</table>
					</div>
				`);
			},
		});
	},
};

frappe.dom.set_style(`
	.doctor-opd-monthly { margin: 6px 0 18px; }
	.doctor-sales-primary { font-size: 10.5px !important; border: 1px solid #dfe5e2; border-radius: 6px; overflow: hidden; }
	.doctor-sales-primary .dt-row { height: 31px; }
	.doctor-sales-primary .dt-cell__content { padding: 6px 8px !important; font-size: 10.5px; line-height: 18px; }
	.doctor-sales-primary .dt-header .dt-row:not([data-is-filter]) .dt-cell--header { background: #303a3f !important; color: #fff !important; border-color: #4a555a !important; }
	.doctor-sales-primary .dt-header .dt-row:not([data-is-filter]) .dt-cell__content { color: #fff !important; font-size: 10px; font-weight: 600; }
	.doctor-sales-primary .dt-row[data-is-filter] .dt-cell { background: #fff; }
	.doctor-sales-primary .dt-scrollable .dt-row:nth-child(even) .dt-cell { background: #f7f9f8; }
	.doctor-sales-primary .dt-scrollable .dt-cell { border-color: #e2e7e5; }
	.doctor-sales-primary .dt-row-totalRow .dt-cell { background: #eef2f0 !important; }
	.doctor-opd-monthly h4 { margin: 0 0 8px; font-size: 13px; font-weight: 600; color: #30383c; }
	.doctor-opd-loading { padding: 18px; border: 1px solid #e2e7e5; border-radius: 6px; }
	.doctor-opd-scroll { overflow-x: auto; border: 1px solid #dfe5e2; border-radius: 6px; }
	.doctor-opd-monthly table { width: 100%; border-collapse: collapse; background: #fff; font-size: 10.5px; }
	.doctor-opd-monthly th { padding: 7px 8px; background: #303a3f; color: #fff; text-align: right; font-size: 10px; font-weight: 600; white-space: nowrap; }
	.doctor-opd-monthly th:nth-child(2) { text-align: left; }
	.doctor-opd-monthly .opd-index { text-align: center; color: #74817d; }
	.doctor-opd-monthly thead .opd-index { color: #fff; }
	.doctor-opd-monthly td { padding: 7px 8px; border-bottom: 1px solid #e2e7e5; color: #30383c; line-height: 17px; }
	.doctor-opd-monthly tbody tr:nth-child(even) { background: #f7f9f8; }
	.doctor-opd-monthly .opd-number { text-align: right; font-variant-numeric: tabular-nums; }
	.doctor-opd-monthly .opd-grand { color: #b66c00; font-weight: 700; }
	.doctor-opd-monthly tfoot td { background: #eef2f0; border-top: 2px solid #cfd8d4; color: #b66c00; font-weight: 700; }
	.doctor-opd-monthly tfoot td:nth-child(2) { color: #30383c; }
`);

// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Facility Incident Report"] = {
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
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nOpen\nClose",
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
		},
		{
			fieldname: "technician",
			label: __("Technician"),
			fieldtype: "Link",
			options: "Employee",
		},
	],

	onload(query_report) {
		query_report.pdf_report = () => {
			open_url_post(
				"/api/method/his.his.report.facility_incident_report.facility_incident_report.download_pdf",
				{ filters: JSON.stringify(query_report.get_filter_values(true)) },
				true
			);
		};
	},

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "status" && data) {
			if (data.status === "Open") {
				return `<span class="indicator-pill red">${__("Open")}</span>`;
			}
			if (data.status === "Close") {
				return `<span class="indicator-pill green">${__("Close")}</span>`;
			}
		}
		return value;
	},

	after_datatable_render(datatable) {
		$(datatable.wrapper).addClass("facility-incident-report-table");
	},
};

frappe.dom.set_style(`
	.facility-incident-report-table {
		font-size: 10.5px !important;
		border: 1px solid #dfe5e2;
		border-radius: 6px;
		overflow: hidden;
	}
	.facility-incident-report-table .dt-row { height: 33px; }
	.facility-incident-report-table .dt-cell__content {
		padding: 6px 8px !important;
		font-size: 10.5px;
		line-height: 19px;
	}
	.facility-incident-report-table .dt-header .dt-row:not([data-is-filter]) .dt-cell--header {
		background: #303a3f !important;
		color: #fff !important;
		border-color: #4a555a !important;
	}
	.facility-incident-report-table .dt-header .dt-row:not([data-is-filter]) .dt-cell__content {
		color: #fff !important;
		font-size: 10px;
		font-weight: 600;
	}
	.facility-incident-report-table .dt-row[data-is-filter] .dt-cell { background: #fff; }
	.facility-incident-report-table .dt-scrollable .dt-row:nth-child(even) .dt-cell { background: #f7f9f8; }
	.facility-incident-report-table .dt-scrollable .dt-cell { border-color: #e2e7e5; }
	.facility-incident-report-table .indicator-pill { font-size: 10px; font-weight: 600; }
`);

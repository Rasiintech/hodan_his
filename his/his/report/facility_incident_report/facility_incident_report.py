# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.utils import escape_html, format_date, getdate
from frappe.utils.pdf import get_pdf


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	data = get_data(filters)
	return get_columns(), data, None, None, get_report_summary(data)


def validate_filters(filters):
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are required."))
	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date cannot be after To Date."))


def get_columns():
	return [
		{"label": _("ID"), "fieldname": "name", "fieldtype": "Link", "options": "Facility Incident Management", "width": 120},
		{"label": _("Incident Title"), "fieldname": "incident_title", "fieldtype": "Data", "width": 180},
		{"label": _("Incident Area"), "fieldname": "incident_area", "fieldtype": "Data", "width": 130},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
		{"label": _("Incident Time"), "fieldname": "incident_time", "fieldtype": "Time", "width": 105},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150},
		{"label": _("Technician"), "fieldname": "technician_name", "fieldtype": "Data", "width": 180},
		{"label": _("Technician Mobile"), "fieldname": "technician_mobile", "fieldtype": "Data", "width": 130},
		{"label": _("Calling Time"), "fieldname": "technician_calling_time", "fieldtype": "Time", "width": 105},
		{"label": _("Closing Time"), "fieldname": "closing_time", "fieldtype": "Time", "width": 105},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
		{"label": _("Remark"), "fieldname": "remark", "fieldtype": "Data", "width": 220},
	]


def get_data(filters):
	conditions = [
		"fim.date between %(from_date)s and %(to_date)s",
		"fim.status in ('Open', 'Close')",
	]
	if filters.get("status"):
		conditions.append("fim.status = %(status)s")
	if filters.get("department"):
		conditions.append("fim.department = %(department)s")
	if filters.get("technician"):
		conditions.append("fim.technician = %(technician)s")

	return frappe.db.sql(
		f"""
		select
			fim.name,
			fim.incident_title,
			fim.incident_area,
			fim.date,
			fim.incident_time,
			fim.department,
			coalesce(nullif(fim.technician_name, ''), employee.employee_name, fim.technician) as technician_name,
			fim.technician_mobile,
			fim.technician_calling_time,
			fim.closing_time,
			fim.status,
			fim.remark
		from `tabFacility Incident Management` fim
		left join `tabEmployee` employee on employee.name = fim.technician
		where {" and ".join(conditions)}
		order by fim.date desc, fim.incident_time desc, fim.name desc
		""",
		filters,
		as_dict=True,
	)


def get_report_summary(data):
	total = len(data)
	open_count = sum(1 for row in data if row.status == "Open")
	closed_count = sum(1 for row in data if row.status == "Close")
	return [
		{"label": _("Total Incidents"), "value": total, "indicator": "Blue", "datatype": "Int"},
		{"label": _("Open"), "value": open_count, "indicator": "Red", "datatype": "Int"},
		{"label": _("Closed"), "value": closed_count, "indicator": "Green", "datatype": "Int"},
	]


@frappe.whitelist()
def download_pdf(filters=None):
	filters = frappe._dict(json.loads(filters) if isinstance(filters, str) else (filters or {}))
	validate_filters(filters)
	data = get_data(filters)
	total = len(data)
	open_count = sum(1 for row in data if row.status == "Open")
	closed_count = sum(1 for row in data if row.status == "Close")

	def text(value):
		return escape_html(str(value or ""))

	def time_text(value):
		return text(str(value)[:8] if value else "")

	filter_parts = [f"{format_date(filters.from_date)} — {format_date(filters.to_date)}"]
	if filters.get("status"):
		filter_parts.append(filters.status)
	if filters.get("department"):
		filter_parts.append(filters.department)
	if filters.get("technician"):
		technician_name = frappe.get_cached_value("Employee", filters.technician, "employee_name")
		filter_parts.append(technician_name or filters.technician)

	body = "".join(
		f"""<tr>
		<td class='nowrap'>{text(row.name)}</td>
		<td>{text(row.incident_title)}</td>
		<td>{text(row.incident_area)}</td>
		<td class='nowrap'>{text(format_date(row.date))}</td>
		<td class='nowrap'>{time_text(row.incident_time)}</td>
		<td>{text(row.department)}</td>
		<td>{text(row.technician_name)}</td>
		<td class='nowrap'>{text(row.technician_mobile)}</td>
		<td class='nowrap'>{time_text(row.technician_calling_time)}</td>
		<td class='nowrap'>{time_text(row.closing_time)}</td>
		<td><span class='status {"closed" if row.status == "Close" else "open"}'>{text(row.status)}</span></td>
		<td>{text(row.remark)}</td>
		</tr>"""
		for row in data
	)
	if not body:
		body = "<tr><td colspan='12' class='empty'>No records found</td></tr>"

	html = f"""<!doctype html><html><head><meta charset='utf-8'><style>
		@page{{size:A4 landscape;margin:10mm}}body{{font:9px Arial;color:#30383c}}table{{width:100%;border-collapse:collapse}}.report-head{{margin:0 0 14px}}.report-head>tbody>tr>td{{padding:0;border:0;vertical-align:top;background:#fff}}.report-title{{width:52%}}.report-kpis{{width:48%;padding-left:12px!important}}h1{{font-family:Georgia,serif;font-size:20px;margin:0 0 4px}}h2{{font-size:13px;margin:12px 0 6px}}p{{color:#697773;margin:0}}.kpis{{table-layout:fixed;border-collapse:separate;border-spacing:6px 0}}.kpis td{{padding:8px;border:1px solid #dce3e0;border-top:3px solid #f19f21;border-radius:6px;background:#f8faf9;vertical-align:top}}.kpi-label{{display:block;color:#74817d;font-size:7px;font-weight:bold;text-transform:uppercase;letter-spacing:.4px}}.kpi-value{{display:block;margin-top:3px;font-size:15px;font-weight:bold}}.kpis td:nth-child(1) .kpi-value{{color:#1877d2}}.kpis td:nth-child(2) .kpi-value{{color:#d64545}}.kpis td:nth-child(3) .kpi-value{{color:#29965a}}th{{background:#303a3f;color:#fff;padding:6px 4px;text-align:left;font-size:7px;white-space:nowrap}}td{{padding:5px 4px;border-bottom:1px solid #e2e7e5;vertical-align:top;overflow-wrap:anywhere}}tbody tr:nth-child(even){{background:#f7f9f8}}.nowrap{{white-space:nowrap}}.status{{display:inline-block;padding:2px 5px;border-radius:8px;font-weight:bold;white-space:nowrap}}.status.open{{color:#b42318;background:#fee4e2}}.status.closed{{color:#067647;background:#dcfae6}}.empty{{padding:18px;text-align:center;color:#74817d}}
	</style></head><body>
	<table class='report-head'><tr><td class='report-title'><h1>Facility Incident Report</h1><p>{" · ".join(text(part) for part in filter_parts)}</p></td><td class='report-kpis'><table class='kpis'><tr><td><span class='kpi-label'>Total Incidents</span><span class='kpi-value'>{total}</span></td><td><span class='kpi-label'>Open</span><span class='kpi-value'>{open_count}</span></td><td><span class='kpi-label'>Closed</span><span class='kpi-value'>{closed_count}</span></td></tr></table></td></tr></table>
	<h2>Facility Incidents</h2><table><thead><tr><th>ID</th><th>Incident Title</th><th>Incident Area</th><th>Date</th><th>Incident Time</th><th>Department</th><th>Technician</th><th>Mobile</th><th>Calling Time</th><th>Closing Time</th><th>Status</th><th>Remark</th></tr></thead><tbody>{body}</tbody></table>
	</body></html>"""

	frappe.local.response.filename = "Facility-Incident-Report.pdf"
	frappe.local.response.filecontent = get_pdf(html, {"orientation": "Landscape", "page-size": "A4"})
	frappe.local.response.type = "pdf"

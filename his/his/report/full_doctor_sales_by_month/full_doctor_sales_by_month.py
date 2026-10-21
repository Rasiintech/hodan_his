# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import json
import re

import frappe
from frappe import _
from frappe.utils import add_months, escape_html, flt, fmt_money, format_date, get_first_day, getdate
from frappe.utils.pdf import get_pdf


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)

	rows = get_sales(filters)
	months = get_months(filters.from_date, filters.to_date)
	columns = get_columns(months)
	data = build_monthly_data(rows, months)
	opd_data = get_opd_monthly_data(filters, months)
	return columns, data, None, None, get_report_summary(rows, months, opd_data)


def validate_filters(filters):
	if not filters.get("ref_practitioner"):
		frappe.throw(_("Please select a doctor."))
	if not filters.get("company"):
		frappe.throw(_("Please select a company."))
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are required."))
	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date cannot be after To Date."))


def get_columns(months):
	columns = [
		{
			"label": _("Item"),
			"fieldname": "item",
			"fieldtype": "Data",
			"width": 360,
		},
	]
	columns.extend({
		"label": format_date(month, "MMM yyyy"),
		"fieldname": month_fieldname(month),
		"fieldtype": "Currency",
		"options": "currency",
		"width": 145,
	} for month in months)
	columns.extend([
		{
			"label": _("Grand Total"),
			"fieldname": "grand_total",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 155,
		},
		{
			"label": _("Currency"),
			"fieldname": "currency",
			"fieldtype": "Link",
			"options": "Currency",
			"hidden": 1,
		},
	])
	return columns


def get_sales(filters):
	return frappe.db.sql(
		"""
		select
			date_format(si.posting_date, '%%Y-%%m-01') as month_start,
			sii.income_account,
			sum(sii.base_net_amount) as total_amount,
			company.default_currency as currency
		from `tabSales Invoice` si
		inner join `tabSales Invoice Item` sii on sii.parent = si.name
		inner join `tabCompany` company on company.name = si.company
		where si.docstatus = 1
			and si.company = %(company)s
			and si.ref_practitioner = %(ref_practitioner)s
			and si.posting_date between %(from_date)s and %(to_date)s
			and ifnull(sii.income_account, '') != ''
		group by date_format(si.posting_date, '%%Y-%%m-01'), sii.income_account,
			company.default_currency
		order by month_start, sii.income_account
		""",
		filters,
		as_dict=True,
	)


def get_opd_monthly_data(filters, months=None):
	months = months or get_months(filters.from_date, filters.to_date)
	rows = frappe.db.sql(
		"""
		select
			date_format(date, '%%Y-%%m-01') as month_start,
			que_type,
			count(*) as queue_count
		from `tabQue`
		where date between %(from_date)s and %(to_date)s
			and practitioner = %(ref_practitioner)s
			and ifnull(status, '') != 'Canceled'
			and que_type in ('New Patient', 'Follow Up', 'Refer')
		group by date_format(date, '%%Y-%%m-01'), que_type
		order by month_start, que_type
		""",
		filters,
		as_dict=True,
	)

	labels = {"New Patient": _("New"), "Follow Up": _("Followup"), "Refer": _("Refer")}
	result = []
	for que_type in ("New Patient", "Follow Up", "Refer"):
		row = {"item": labels[que_type], "grand_total": 0}
		for month in months:
			row[month_fieldname(month)] = 0
		for value in rows:
			if value.que_type == que_type:
				fieldname = month_fieldname(value.month_start)
				row[fieldname] = int(value.queue_count or 0)
				row["grand_total"] += int(value.queue_count or 0)
		result.append(row)
	return result


@frappe.whitelist()
def get_opd_table(filters=None):
	filters = frappe._dict(json.loads(filters) if isinstance(filters, str) else (filters or {}))
	validate_filters(filters)
	months = get_months(filters.from_date, filters.to_date)
	return {
		"months": [
			{"fieldname": month_fieldname(month), "label": format_date(month, "MMM yyyy")}
			for month in months
		],
		"rows": get_opd_monthly_data(filters, months),
	}


def get_months(from_date, to_date):
	months = []
	month = get_first_day(from_date)
	last_month = get_first_day(to_date)
	while getdate(month) <= getdate(last_month):
		months.append(month)
		month = add_months(month, 1)
	return months


def month_fieldname(month):
	return f"month_{getdate(month).strftime('%Y_%m')}"


def get_item_label(income_account):
	label = re.sub(r"^\s*\d+\s*-\s*", "", income_account or "")
	label = re.sub(r"\s+revenue\s*-\s*hh\s*$", "", label, flags=re.IGNORECASE)
	return label.strip()


def build_monthly_data(rows, months):
	currency = rows[0].currency if rows else None
	accounts = {}
	for row in rows:
		account = accounts.setdefault(row.income_account, {
			"item": get_item_label(row.income_account),
			"currency": row.currency,
			"grand_total": 0.0,
		})
		fieldname = month_fieldname(row.month_start)
		amount = flt(row.total_amount, 2)
		account[fieldname] = amount
		account["grand_total"] += amount

	data = []
	for account in sorted(
		accounts.values(),
		key=lambda row: (-flt(row.get("grand_total")), row.get("item") or ""),
	):
		for month in months:
			account.setdefault(month_fieldname(month), 0.0)
		account["grand_total"] = flt(account["grand_total"], 2)
		account["currency"] = account.get("currency") or currency
		data.append(account)
	return data


def get_report_summary(rows, months, opd_data=None):
	grand_total = flt(sum(flt(row.total_amount) for row in rows), 2)
	currency = rows[0].currency if rows else None
	opd_total = sum(int(row.get("grand_total") or 0) for row in (opd_data or []))
	return [
		{
			"label": _("Grand Total"),
			"value": grand_total,
			"indicator": "Green",
			"datatype": "Currency",
			"currency": currency,
		},
		{
			"label": _("OPD Queue"),
			"value": opd_total,
			"indicator": "Orange",
			"datatype": "Int",
		},
		{
			"label": _("Total Months"),
			"value": len(months),
			"indicator": "Blue",
			"datatype": "Int",
		},
	]


@frappe.whitelist()
def download_pdf(filters=None):
	filters = frappe._dict(json.loads(filters) if isinstance(filters, str) else (filters or {}))
	validate_filters(filters)
	rows = get_sales(filters)
	months = get_months(filters.from_date, filters.to_date)
	data = build_monthly_data(rows, months)
	opd_data = get_opd_monthly_data(filters, months)
	currency = rows[0].currency if rows else frappe.get_cached_value(
		"Company", filters.company, "default_currency"
	)
	month_fields = [(month_fieldname(month), format_date(month, "MMM yyyy")) for month in months]
	month_totals = {
		fieldname: sum(flt(row.get(fieldname)) for row in data) for fieldname, _label in month_fields
	}
	grand_total = sum(flt(row.get("grand_total")) for row in data)
	money = lambda value: escape_html(fmt_money(flt(value), currency=currency))

	headers = "".join(f"<th>{escape_html(label)}</th>" for _fieldname, label in month_fields)
	body = "".join(
		f"<tr><td>{escape_html(row['item'])}</td>"
		+ "".join(f"<td class='num'>{money(row.get(fieldname))}</td>" for fieldname, _label in month_fields)
		+ f"<td class='num total'>{money(row['grand_total'])}</td>"
		+ "</tr>"
		for row in data
	)
	foot = (
		"<tr><td>Total</td>"
		+ "".join(f"<td class='num'>{money(month_totals[fieldname])}</td>" for fieldname, _label in month_fields)
		+ f"<td class='num'>{money(grand_total)}</td>"
		+ "</tr>"
	)
	opd_body = "".join(
		f"<tr><td>{escape_html(row['item'])}</td>"
		+ "".join(f"<td class='num'>{int(row.get(fieldname) or 0)}</td>" for fieldname, _label in month_fields)
		+ f"<td class='num opd-total'>{int(row['grand_total'])}</td>"
		+ "</tr>"
		for row in opd_data
	)
	opd_month_totals = {
		fieldname: sum(int(row.get(fieldname) or 0) for row in opd_data)
		for fieldname, _label in month_fields
	}
	opd_grand_total = sum(int(row.get("grand_total") or 0) for row in opd_data)
	opd_foot = (
		"<tr><td>Total OPD Queue</td>"
		+ "".join(f"<td class='num'>{opd_month_totals[fieldname]}</td>" for fieldname, _label in month_fields)
		+ f"<td class='num'>{opd_grand_total}</td>"
		+ "</tr>"
	)
	doctor = frappe.get_cached_value("Healthcare Practitioner", filters.ref_practitioner, "practitioner_name") or filters.ref_practitioner
	html = f"""<!doctype html><html><head><meta charset='utf-8'><style>
		@page{{size:A4 landscape;margin:10mm}}body{{font:10px Arial;color:#30383c}}table{{width:100%;border-collapse:collapse}}.report-head{{margin:0 0 14px}}.report-head>tbody>tr>td{{padding:0;border:0;vertical-align:top;background:#fff}}.report-title{{width:52%}}.report-kpis{{width:48%;padding-left:12px!important}}h1{{font-size:20px;margin:0 0 4px}}h2{{font-size:13px;margin:16px 0 6px;color:#30383c}}p{{color:#697773;margin:0}}.kpis{{table-layout:fixed;border-collapse:separate;border-spacing:6px 0}}.kpis td{{padding:8px 8px;border:1px solid #dce3e0;border-top:3px solid #f19f21;border-radius:6px;background:#f8faf9;vertical-align:top}}.kpi-label{{display:block;color:#74817d;font-size:7px;font-weight:bold;text-transform:uppercase;letter-spacing:.4px}}.kpi-value{{display:block;margin-top:3px;color:#30383c;font-size:15px;font-weight:bold}}.kpis td:first-child .kpi-value{{color:#b66c00}}th{{background:#303a3f;color:#fff;padding:7px 6px;text-align:right;font-size:8px}}th:first-child{{text-align:left}}td{{padding:6px;border-bottom:1px solid #e2e7e5}}tbody tr:nth-child(even){{background:#f7f9f8}}.num{{text-align:right;white-space:nowrap}}.total,.opd-total{{color:#b66c00;font-weight:bold}}tfoot td{{font-weight:bold;background:#eef2f0;border-top:2px solid #cfd8d4;color:#b66c00}}tfoot td:first-child{{color:#30383c}}
	</style></head><body><table class='report-head'><tr><td class='report-title'><h1>Full Doctor Sales by Month</h1><p><b>{escape_html(doctor)}</b> · {escape_html(format_date(filters.from_date))} — {escape_html(format_date(filters.to_date))}</p></td><td class='report-kpis'><table class='kpis'><tr><td><span class='kpi-label'>Grand Total · Selected Dates</span><span class='kpi-value'>{money(grand_total)}</span></td><td><span class='kpi-label'>OPD Queue</span><span class='kpi-value'>{opd_grand_total}</span></td><td><span class='kpi-label'>Total Months</span><span class='kpi-value'>{len(months)}</span></td></tr></table></td></tr></table><h2>OPD Queue by Month</h2><table><thead><tr><th>Item</th>{headers}<th>Grand Total</th></tr></thead><tbody>{opd_body}</tbody><tfoot>{opd_foot}</tfoot></table><h2>Sales by Month</h2><table><thead><tr><th>Item</th>{headers}<th>Grand Total</th></tr></thead><tbody>{body}</tbody><tfoot>{foot}</tfoot></table></body></html>"""

	frappe.local.response.filename = "Full-Doctor-Sales-by-Month.pdf"
	frappe.local.response.filecontent = get_pdf(html, {"orientation": "Landscape", "page-size": "A4"})
	frappe.local.response.type = "pdf"

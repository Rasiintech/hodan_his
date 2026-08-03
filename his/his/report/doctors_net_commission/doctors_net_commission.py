from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt

from his.his.report.doctor_commission.doctor_commission import get_data as get_doctor_commission_data


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_data(filters):
	commission_rows = get_doctor_commission_data(frappe._dict(filters or {}))
	active_practitioners = get_active_practitioners({row.ref_practitioner for row in commission_rows})
	doctor_totals = defaultdict(
		lambda: {"net_commission": 0.0, "net_sales": 0.0, "weighted_commission_sum": 0.0}
	)

	for row in commission_rows:
		if row.ref_practitioner not in active_practitioners:
			continue
		stats = doctor_totals[row.ref_practitioner]
		stats["net_commission"] += flt(row.net_commission)
		stats["net_sales"] += flt(row.net_sales)
		stats["weighted_commission_sum"] += flt(row.commission_percent) * flt(row.net_sales)

	return [
		frappe._dict(
			{
				"employee_commisison": active_practitioners[doctor].get("employee_commisison"),
				"ref_practitioner": doctor,
				"commission_percent": round(
					stats["weighted_commission_sum"] / stats["net_sales"] if stats["net_sales"] else 0,
					2,
				),
				"net_commission": round(stats["net_commission"], 2),
			}
		)
		for doctor, stats in sorted(doctor_totals.items())
	]


def get_active_practitioners(practitioners):
	if not practitioners:
		return {}
	return {
		row.name: row
		for row in frappe.get_all(
			"Healthcare Practitioner",
			filters={"name": ("in", list(practitioners)), "status": "Active"},
			fields=["name", "employee_commisison"],
		)
	}


def get_columns():
	return [
		{"label": _("Employee ID"), "fieldname": "employee_commisison", "fieldtype": "Link", "options": "Employee", "width": 150},
		{"label": _("Doctor Name"), "fieldname": "ref_practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 200},
		{"label": _("Commission Rate %"), "fieldname": "commission_percent", "fieldtype": "Percent", "width": 150},
		{"label": _("Net Commission"), "fieldname": "net_commission", "fieldtype": "Currency", "options": "currency", "width": 180},
	]

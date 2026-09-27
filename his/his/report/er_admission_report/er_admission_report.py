import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if filters.from_date and filters.to_date and getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date cannot be after To Date."))

	fieldnames = [
		"date", "patient_id", "patient_name", "consultant", "diagnose",
		"admission_type", "er_type", "room", "nurse_transferred", "gp_doctor",
		"specialist_doctor", "emergency_triage",
	]
	columns = []
	meta = frappe.get_meta("ER Admission")
	for fieldname in fieldnames:
		if fieldname == "er_type":
			columns.append({
				"fieldname": "er_type", "label": _("ER Type"),
				"fieldtype": "Data", "width": 120,
			})
			continue
		field = meta.get_field(fieldname)
		columns.append({
			"fieldname": fieldname, "label": _(field.label),
			"fieldtype": "Data" if field.fieldtype == "Select" else field.fieldtype,
			"options": field.options if field.fieldtype == "Link" else None,
			"width": (
				110 if fieldname in ("date", "patient_id")
				else 120 if fieldname == "admission_type"
				else 240 if fieldname == "diagnose"
				else 180
			),
		})
	columns.append({
		"fieldname": "name", "label": _("ER Admission"),
		"fieldtype": "Link", "options": "ER Admission", "width": 160,
	})

	conditions = []
	if filters.from_date:
		conditions.append(["date", ">=", filters.from_date])
	if filters.to_date:
		conditions.append(["date", "<=", filters.to_date])
	for fieldname in ("patient_id", "admission_type"):
		if filters.get(fieldname):
			conditions.append([fieldname, "=", filters[fieldname]])
	if filters.er_type:
		triage_names = frappe.get_list(
			"Emergency Triage",
			filters={"er_type": filters.er_type},
			pluck="name",
			limit_page_length=0,
		)
		if not triage_names:
			return columns, []
		conditions.append(["emergency_triage", "in", triage_names])

	data = frappe.get_list(
		"ER Admission",
		fields=["name"] + [fieldname for fieldname in fieldnames if fieldname != "er_type"]
			+ ["emergency_triage.er_type as er_type"],
		filters=conditions,
		order_by="`tabER Admission`.date desc, `tabER Admission`.creation desc",
		limit_page_length=0,
	)
	return columns, data

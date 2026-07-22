import frappe
from frappe import _
from frappe.utils import flt

from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import (
	AccountsReceivableSummary as ERPNextAccountsReceivableSummary,
)


ADMITTED_STATUS = "Admitted"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	set_default_receivable_filters(filters)
	columns = get_columns()
	data = get_data(filters)
	# report_summary = get_report_summary(data)
	return columns, data, None, None, None


def set_default_receivable_filters(filters):
	defaults = {
		"ageing_based_on": "Due Date",
		"range1": 30,
		"range2": 60,
		"range3": 90,
		"range4": 120,
		"show_future_payments": 0,
		"show_gl_balance": 0,
		"based_on_payment_terms": 0,
	}

	for key, value in defaults.items():
		if filters.get(key) in (None, ""):
			filters[key] = value


def get_columns():
	return [
		{
			"label": _("Customer"),
			"fieldname": "party",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 170,
		},
		{
			"label": _("Customer Name"),
			"fieldname": "party_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Patient"),
			"fieldname": "patient",
			"fieldtype": "Link",
			"options": "Patient",
			"width": 130,
		},
		{
			"label": _("Patient Name"),
			"fieldname": "patient_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Mobile No"),
			"fieldname": "mobile_no",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Responsible"),
			"fieldname": "responsible",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Inpatient Record"),
			"fieldname": "inpatient_record",
			"fieldtype": "Link",
			"options": "Inpatient Record",
			"width": 170,
		},
		{
			"label": _("Inpatient Status"),
			"fieldname": "inpatient_status",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Advance Amount"),
			"fieldname": "advance",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Invoiced Amount"),
			"fieldname": "invoiced",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("Paid Amount"),
			"fieldname": "paid",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Credit Note"),
			"fieldname": "credit_note",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("Outstanding Amount"),
			"fieldname": "outstanding",
			"fieldtype": "Currency",
			"width": 140,
		},
	]


def get_data(filters):
	args = {
		"party_type": "Customer",
		"naming_by": ["Selling Settings", "cust_master_name"],
	}

	base_result = ERPNextAccountsReceivableSummary(filters).run(args)
	base_rows = base_result[1] if len(base_result) > 1 else []
	if not base_rows:
		return []

	patient_map = get_admitted_patient_map(filters)
	data = []

	for row in base_rows:
		patient_info = patient_map.get(row.party)
		if not patient_info:
			continue
		if  patient_info.inpatient_status != "Admitted":
			continue

		row.patient = patient_info.patient
		row.patient_name = patient_info.patient_name
		row.mobile_no = patient_info.mobile_no
		row.responsible = patient_info.responsible
		row.inpatient_record = patient_info.inpatient_record
		row.inpatient_status = patient_info.inpatient_status
		data.append(row)

	return data


def get_admitted_patient_map(filters):
	patient_filters = {}
	if filters.get("customer"):
		patient_filters["customer"] = filters.get("customer")
	if filters.get("patient"):
		patient_filters["name"] = filters.get("patient")

	patients = frappe.get_all(
		"Patient",
		filters=patient_filters,
		fields=["name", "patient_name", "customer", "mobile_no", "mobile"],
	)
	if not patients:
		return {}

	customers = [patient.customer for patient in patients if patient.customer]
	patient_names = [patient.name for patient in patients]

	customer_name_map = {
		row.name: row.customer_name
		for row in frappe.get_all(
			"Customer",
			filters={"name": ["in", customers]},
			fields=["name", "customer_name"],
		)
	}
	responsible_map = {}
	for row in frappe.get_all(
		"Customer Credit Limit",
		filters={"parent": ["in", customers]},
		fields=["parent", "responsible"],
	):
		responsible_map.setdefault(row.parent, row.responsible)

	inpatient_rows = frappe.get_all(
		"Inpatient Record",
		filters={"patient": ["in", patient_names], "status": ADMITTED_STATUS},
		fields=["name", "patient", "status", "modified", "creation"],
		order_by="modified desc, creation desc",
	)
	admitted_by_patient = {}
	for row in inpatient_rows:
		if row.patient not in admitted_by_patient:
			admitted_by_patient[row.patient] = row

	admitted_patient_map = {}
	for patient in patients:
		inpatient = admitted_by_patient.get(patient.name)
		if not inpatient or not patient.customer:
			continue

		admitted_patient_map[patient.customer] = frappe._dict(
			{
				"patient": patient.name,
				"patient_name": patient.patient_name,
				"mobile_no": patient.mobile_no or patient.mobile,
				"customer_name": customer_name_map.get(patient.customer),
				"responsible": responsible_map.get(patient.customer),
				"inpatient_record": inpatient.name,
				"inpatient_status": inpatient.status,
			}
		)

	return admitted_patient_map


def get_report_summary(data):
	total_outstanding = 0

	for row in data:
		total_outstanding += flt(row.outstanding)

	return [
		{
			"value": len(data),
			"label": _("Admitted Patients"),
			"indicator": "Orange",
			"datatype": "Int",
		},
		{
			"value": total_outstanding,
			"label": _("Admitted Outstanding"),
			"indicator": "Orange",
			"datatype": "Currency",
		},
	]

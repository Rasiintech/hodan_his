from datetime import date, datetime, time

import frappe
from frappe import _
from frappe.utils import cint, getdate, nowdate


STANDARD_FIELDS = {
	"name",
	"owner",
	"creation",
	
	"modified_by",
	"docstatus",
	"idx",
	"parent",
	"parentfield",
	"parenttype",
}

EXCLUDED_BILLING_ITEMS = {"opd consultation"}

SUMMARY_STAGES = (
	("patient_registration", "Patient Registration Time"),
	("que_creation", "Que Creation Time"),
	("encounter_creation", "Patient Encounter Creation Time"),
	("sales_order_creation", "Sales Order Creation Time"),
	("sales_invoice_creation", "Sales Invoice Creation Time"),
	("sample_collection_creation", "Sample Collection Creation Time"),
	("lab_result_creation", "Lab Result Creation Time"),
	("lab_result_submitted", "Lab Result Submitted Time"),
)


@frappe.whitelist()
def get_patient_track(patient, from_date=None, to_date=None, practitioner=None, doctor=None):
	"""Return timeline events for the selected patient's operational track."""
	if not patient:
		frappe.throw(_("Please select a Patient"))

	if not frappe.db.exists("Patient", patient):
		frappe.throw(_("Patient {0} was not found").format(frappe.bold(patient)))

	practitioner = practitioner or doctor
	if practitioner and frappe.db.exists("DocType", "Healthcare Practitioner"):
		if not frappe.db.exists("Healthcare Practitioner", practitioner):
			frappe.throw(_("Healthcare Practitioner {0} was not found").format(frappe.bold(practitioner)))

	from_date, to_date = normalize_dates(from_date, to_date)
	if not from_date and not to_date:
		latest_date = get_latest_patient_activity_date(patient, practitioner)
		from_date = latest_date
		to_date = latest_date

	events = []
	events.extend(get_patient_registration_events(patient))
	events.extend(get_que_events(patient, from_date, to_date, practitioner))
	events.extend(get_patient_encounter_events(patient, from_date, to_date, practitioner))
	events.extend(get_sales_order_events(patient, from_date, to_date, practitioner))
	events.extend(get_sales_invoice_events(patient, from_date, to_date, practitioner))
	events.extend(get_sample_collection_events(patient, from_date, to_date, practitioner))
	events.extend(get_lab_result_events(patient, from_date, to_date, practitioner))

	events.sort(key=lambda event: event.get("sort_time") or "")

	return {
		"patient": get_patient_details(patient),
		"practitioner": get_practitioner_details(practitioner),
		"from_date": from_date or "",
		"to_date": to_date or "",
		"summary": build_summary(events),
		"events": events,
	}


def normalize_dates(from_date=None, to_date=None):
	if from_date:
		from_date = getdate(from_date)
	if to_date:
		to_date = getdate(to_date)

	if from_date and to_date and from_date > to_date:
		from_date, to_date = to_date, from_date

	return as_string(from_date), as_string(to_date)


def get_latest_patient_activity_date(patient, practitioner=None):
	date_fields = (
		("Que", "date"),
		("Patient Encounter", "encounter_date"),
		("Sales Order", "transaction_date"),
		("Sales Invoice", "posting_date"),
		("Sample Collection", "date"),
		("Lab Result", "date"),
	)
	latest_date = None

	for doctype, date_field in date_fields:
		if not frappe.db.exists("DocType", doctype) or not has_field(doctype, "patient") or not has_field(doctype, date_field):
			continue

		filters = {"patient": patient}
		if practitioner:
			practitioner_field = get_practitioner_field(doctype)
			if not practitioner_field:
				continue
			filters[practitioner_field] = practitioner

		row = frappe.get_all(
			doctype,
			filters=filters,
			fields=[date_field],
			order_by=f"{date_field} desc, creation desc",
			limit_page_length=1,
		)
		if not row or not row[0].get(date_field):
			continue

		current_date = getdate(row[0].get(date_field))
		if not latest_date or current_date > latest_date:
			latest_date = current_date

	return as_string(latest_date)


def get_patient_details(patient):
	fields = valid_fields(
		"Patient",
		[
			"name",
			"creation",
			"patient_name",
			"sex",
			"mobile",
			"mobile_no",
			"p_age",
			"dob",
			"blood_group",
			"customer",
			"image",
		],
	)
	details = frappe.db.get_value("Patient", patient, fields, as_dict=True) or {}
	details = clean_dict(details)
	details["display_name"] = details.get("patient_name") or patient
	return details


def get_practitioner_details(practitioner=None):
	if not practitioner:
		return {}
	if not frappe.db.exists("DocType", "Healthcare Practitioner"):
		return {"name": practitioner, "display_name": practitioner}

	fields = valid_fields(
		"Healthcare Practitioner",
		["name", "practitioner_name", "employee", "department"],
	)
	details = frappe.db.get_value("Healthcare Practitioner", practitioner, fields, as_dict=True) or {}
	details = clean_dict(details)
	details["display_name"] = details.get("practitioner_name") or practitioner
	return details


def get_patient_registration_events(patient):
	fields = valid_fields(
		"Patient",
		[
			"name",
			"creation",
		
			"docstatus",
			"patient_name",
			"sex",
			"mobile",
			"mobile_no",
		],
	)
	row = frappe.db.get_value("Patient", patient, fields, as_dict=True) or {}
	if not row:
		return []

	return [
		make_event(
			"patient_registration",
			"Patient Registration Time",
			"Patient",
			row,
			row.get("creation"),
			status="Registered",
			details=compact_details(
				("Patient", row.get("patient_name") or row.get("name")),
				("Mobile", row.get("mobile_no") or row.get("mobile")),
			),
		)
	]


def get_que_events(patient, from_date, to_date, practitioner=None):
	records = get_patient_records(
		"Que",
		patient,
		[
			"name",
			"creation",
			
			"docstatus",
			"patient",
			"patient_name",
			"date",
			"time",
			"practitioner",
			"practitioner_name",
			"status",
			"que_steps",
			"que_type",
			"sales_order",
			"sales_invoice",
			"patient_encounter",
			"token_no",
		],
		"date",
		from_date,
		to_date,
		practitioner,
	)
	return [
		make_event(
			"que_creation",
			"Que Creation Time",
			"Que",
			row,
			row.get("creation"),
			status=row.get("status") or row.get("que_steps"),
			details=compact_details(
				("Token", row.get("token_no")),
				("Type", row.get("que_type")),
				("Practitioner", row.get("practitioner_name") or row.get("practitioner")),
				("Encounter", row.get("patient_encounter")),
				("Sales Invoice", row.get("sales_invoice")),
			),
		)
		for row in records
	]


def get_patient_encounter_events(patient, from_date, to_date, practitioner=None):
	records = get_patient_records(
		"Patient Encounter",
		patient,
		[
			"name",
			"creation",
			
			"docstatus",
			"patient",
			"patient_name",
			"encounter_date",
			"encounter_time",
			"practitioner",
			"practitioner_name",
			"medical_department",
			"cheif_complaint",
			"chief_complaint_f",
			"differential__diagnosis",
			"diagnosis_list",
			"management_plan",
			"custom_follow_up_date",
			"fallow_up_days",
			"que_tye",
			"que",
			"status",
		],
		"encounter_date",
		from_date,
		to_date,
		practitioner,
	)
	for row in records:
		row["differential_diagnosis"] = get_differential_diagnosis(row.get("name"))

	return [
		make_event(
			"encounter_creation",
			"Patient Encounter Creation Time",
			"Patient Encounter",
			row,
			row.get("creation"),
			status=row.get("status") or docstatus_label(row.get("docstatus")),
			details=compact_details(
				("Encounter Date", row.get("encounter_date")),
				("Encounter Time", row.get("encounter_time")),
				("Practitioner", row.get("practitioner_name") or row.get("practitioner")),
				("Department", row.get("medical_department")),
				("Visit Type", row.get("que_tye")),
				("Chief Complaint", row.get("chief_complaint_f") or row.get("cheif_complaint")),
				("Differential Diagnosis", row.get("differential_diagnosis") or row.get("differential__diagnosis")),
				("Que", row.get("que")),
			),
		)
		for row in records
	]


def get_differential_diagnosis(encounter):
	if not encounter or not frappe.db.exists("DocType", "Patient Encounter Diagnosis"):
		return ""

	rows = frappe.get_all(
		"Patient Encounter Diagnosis",
		filters={
			"parent": encounter,
			"parenttype": "Patient Encounter",
			"parentfield": "differential_diagnosis",
		},
		fields=["diagnosis"],
		order_by="idx asc",
	)
	return ", ".join(row.get("diagnosis") for row in rows if row.get("diagnosis"))


def get_sales_order_events(patient, from_date, to_date, practitioner=None):
	records = get_patient_records(
		"Sales Order",
		patient,
		[
			"name",
			"creation",
			
			"docstatus",
			"patient",
			"patient_name",
			"transaction_date",
			"status",
			"so_type",
			"source_order",
			"custom_patient_encounter",
			"ref_practitioner",
			"ref_practtioner",
			"grand_total",
			"outstanding_amount",
			"paid_amount",
			"currency",
		],
		"transaction_date",
		from_date,
		to_date,
		practitioner,
	)
	records = exclude_records_with_items("Sales Order", records)
	return [
		make_event(
			"sales_order_creation",
			"Sales Order Creation Time",
			"Sales Order",
			row,
			row.get("creation"),
			status=row.get("status") or docstatus_label(row.get("docstatus")),
			details=compact_details(
				("Type", row.get("so_type")),
				("Source", row.get("source_order")),
				("Encounter", row.get("custom_patient_encounter")),
				("Practitioner", row_practitioner(row)),
				("Total", row.get("grand_total")),
			),
		)
		for row in records
	]


def get_sales_invoice_events(patient, from_date, to_date, practitioner=None):
	records = get_patient_records(
		"Sales Invoice",
		patient,
		[
			"name",
			"creation",
			
			"docstatus",
			"patient",
			"patient_name",
			"posting_date",
			"status",
			"so_type",
			"source_order",
			"custom_patient_encounter",
			"que_reference",
			"ref_practitioner",
			"ref_practtioner",
			"grand_total",
			"outstanding_amount",
			"paid_amount",
			"currency",
			"is_return",
		],
		"posting_date",
		from_date,
		to_date,
		practitioner,
	)
	records = exclude_records_with_items("Sales Invoice", records)
	return [
		make_event(
			"sales_invoice_creation",
			"Sales Invoice Creation Time",
			"Sales Invoice",
			row,
			row.get("creation"),
			status=row.get("status") or docstatus_label(row.get("docstatus")),
			details=compact_details(
				("Type", row.get("so_type")),
				("Source", row.get("source_order")),
				("Encounter", row.get("custom_patient_encounter")),
				("Que", row.get("que_reference")),
				("Practitioner", row_practitioner(row)),
				("Total", row.get("grand_total")),
			),
		)
		for row in records
	]


def get_sample_collection_events(patient, from_date, to_date, practitioner=None):
	records = get_patient_records(
		"Sample Collection",
		patient,
		[
			"name",
			"creation",
		
			"docstatus",
			"patient",
			"patient_name",
			"date",
			"collected_time",
			"practitioner",
			"sample",
			"lab_ref",
			"token_no",
			"reff_invoice",
			"source_order",
			"custom_reff_order",
			"custom_patient_encounter",
		],
		"date",
		from_date,
		to_date,
		practitioner,
	)
	return [
		make_event(
			"sample_collection_creation",
			"Sample Collection Creation Time",
			"Sample Collection",
			row,
			row.get("creation"),
			status=docstatus_label(row.get("docstatus")),
			details=compact_details(
				("Lab Ref", row.get("lab_ref")),
				("Token", row.get("token_no")),
				("Collected", row.get("collected_time")),
				("Sales Invoice", row.get("reff_invoice")),
				("Sales Order", row.get("custom_reff_order")),
				("Encounter", row.get("custom_patient_encounter")),
				("Practitioner", row_practitioner(row)),
			),
		)
		for row in records
	]


def get_lab_result_events(patient, from_date, to_date, practitioner=None):
	records = get_patient_records(
		"Lab Result",
		patient,
		[
			"name",
			"creation",
			
			"docstatus",
			"patient",
			"patient_name",
			"date",
			"time",
			"status",
			"template",
			"lab_test_name",
			"sample",
			"reff_collection",
			"lab_ref",
			"practitioner",
			"practitioner_name",
		],
		"date",
		from_date,
		to_date,
		practitioner,
	)

	events = []
	for row in records:
		submitted_time = get_submitted_time(row)
		details = compact_details(
			("Template", row.get("lab_test_name") or row.get("template")),
			("Sample", row.get("sample")),
			("Collection", row.get("reff_collection")),
			("Lab Ref", row.get("lab_ref")),
			("Practitioner", row.get("practitioner_name") or row.get("practitioner")),
		)
		events.append(
			make_event(
				"lab_result_creation",
				"Lab Result Creation Time",
				"Lab Result",
				row,
				row.get("creation"),
				status=row.get("status") or docstatus_label(row.get("docstatus")),
				details=details,
				submitted_time=submitted_time,
			)
		)
		if submitted_time:
			events.append(
				make_event(
					"lab_result_submitted",
					"Lab Result Submitted Time",
					"Lab Result",
					row,
					submitted_time,
					status=row.get("status") or _("Submitted"),
					details=details,
					creation_time=row.get("creation"),
					submitted_time=submitted_time,
				)
			)

	return events


def get_patient_records(doctype, patient, fields, date_field, from_date, to_date, practitioner=None):
	if not frappe.db.exists("DocType", doctype):
		return []

	filters = {}
	if has_field(doctype, "patient"):
		filters["patient"] = patient
	elif has_field(doctype, "patient_name"):
		patient_name = frappe.db.get_value("Patient", patient, "patient_name")
		filters["patient_name"] = patient_name or patient
	else:
		return []

	if practitioner:
		practitioner_field = get_practitioner_field(doctype)
		if not practitioner_field:
			return []
		filters[practitioner_field] = practitioner

	if from_date or to_date:
		if date_field and has_field(doctype, date_field):
			filters[date_field] = date_filter(from_date, to_date)
		else:
			filters["creation"] = datetime_filter(from_date, to_date)

	return [
		clean_dict(row)
		for row in frappe.get_all(
			doctype,
			filters=filters,
			fields=valid_fields(doctype, fields),
			order_by="creation asc",
			limit_page_length=200,
		)
	]


def exclude_records_with_items(doctype, records):
	if not records:
		return records

	child_doctype = f"{doctype} Item"
	if not frappe.db.exists("DocType", child_doctype):
		return records

	parent_names = [row.get("name") for row in records if row.get("name")]
	if not parent_names:
		return records

	item_rows = frappe.get_all(
		child_doctype,
		filters={
			"parent": ["in", parent_names],
			"parenttype": doctype,
		},
		fields=valid_fields(child_doctype, ["parent", "item_code", "item_name", "description"]),
		limit_page_length=5000,
	)
	excluded_parents = {row.get("parent") for row in item_rows if has_excluded_billing_item(row)}
	if not excluded_parents:
		return records

	return [row for row in records if row.get("name") not in excluded_parents]


def has_excluded_billing_item(row):
	values = (row.get("item_code"), row.get("item_name"), row.get("description"))
	return any(
		excluded_item in as_string(value).strip().lower()
		for value in values
		for excluded_item in EXCLUDED_BILLING_ITEMS
	)


def make_event(
	stage_key,
	stage,
	doctype,
	row,
	event_time,
	status=None,
	details=None,
	creation_time=None,
	submitted_time=None,
):
	event_time = as_string(event_time)
	return {
		"stage_key": stage_key,
		"stage": stage,
		"doctype": doctype,
		"name": row.get("name"),
		"time": event_time,
		"sort_time": event_time,
		"creation_time": as_string(creation_time or row.get("creation")),
		"submitted_time": as_string(submitted_time),
		"status": as_string(status),
		"details": details or [],
		"data": clean_dict(row),
	}


def build_summary(events):
	summary = []
	for stage_key, label in SUMMARY_STAGES:
		stage_events = [event for event in events if event.get("stage_key") == stage_key and event.get("time")]
		first_event = stage_events[0] if stage_events else None
		latest_event = stage_events[-1] if stage_events else None
		summary.append(
			{
				"key": stage_key,
				"label": label,
				"count": len(stage_events),
				"first_time": first_event.get("time") if first_event else "",
				"latest_time": latest_event.get("time") if latest_event else "",
				"doctype": latest_event.get("doctype") if latest_event else "",
				"document": latest_event.get("name") if latest_event else "",
			}
		)
	return summary


def get_submitted_time(row):
	status = row.get("status")
	docstatus = cint(row.get("docstatus"))
	if docstatus == 1 or (docstatus != 2 and status == "Submit"):
		return  row.get("creation")
	return None


def date_filter(from_date, to_date):
	if from_date and to_date:
		return ["between", [from_date, to_date]]
	if from_date:
		return [">=", from_date]
	return ["<=", to_date]


def datetime_filter(from_date, to_date):
	from_datetime = f"{from_date or '1900-01-01'} 00:00:00"
	to_datetime = f"{to_date or nowdate()} 23:59:59"
	return ["between", [from_datetime, to_datetime]]


def valid_fields(doctype, fields):
	return [field for field in fields if field in STANDARD_FIELDS or has_field(doctype, field)]


def has_field(doctype, fieldname):
	if fieldname in STANDARD_FIELDS:
		return True
	return bool(frappe.get_meta(doctype).has_field(fieldname))


def get_practitioner_field(doctype):
	for fieldname in ("practitioner", "ref_practitioner", "ref_practtioner"):
		if has_field(doctype, fieldname):
			return fieldname
	return None


def row_practitioner(row):
	return (
		row.get("practitioner_name")
		or row.get("practitioner")
		or row.get("ref_practitioner")
		or row.get("ref_practtioner")
	)


def clean_dict(row):
	return {key: as_string(value) for key, value in dict(row).items()}


def compact_details(*items):
	return [f"{label}: {as_string(value)}" for label, value in items if value not in (None, "")]


def docstatus_label(docstatus):
	docstatus = cint(docstatus)
	if docstatus == 0:
		return _("Draft")
	if docstatus == 1:
		return _("Submitted")
	if docstatus == 2:
		return _("Cancelled")
	return ""


def as_string(value):
	if value is None:
		return ""
	if isinstance(value, datetime):
		return value.strftime("%Y-%m-%d %H:%M:%S")
	if isinstance(value, date):
		return value.strftime("%Y-%m-%d")
	if isinstance(value, time):
		return value.strftime("%H:%M:%S")
	return str(value)

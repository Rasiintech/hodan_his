# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	return get_columns(), get_data(filters)


def validate_filters(filters):
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are required"))

	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date cannot be after To Date"))


def get_columns():
	return [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{
			"label": _("Consultant"),
			"fieldname": "consultant",
			"fieldtype": "Link",
			"options": "Healthcare Practitioner",
			"width": 210,
		},
		{
			"label": _("Patient ID"),
			"fieldname": "patient",
			"fieldtype": "Link",
			"options": "Patient",
			"width": 130,
		},
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 210},
		{"label": _("Mobile"), "fieldname": "mobile", "fieldtype": "Data", "width": 130},
		{
			"label": _("Item Group"),
			"fieldname": "item_group",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 120,
		},
		{
			"label": _("Sales Order"),
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"options": "Sales Order",
			"width": 160,
		},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
	]


def get_data(filters):
	conditions = ["so.docstatus < 2", "soi.item_group IN ('MRI', 'CT Scan')"]
	values = {}

	conditions.extend(
		[
			"so.transaction_date >= %(from_date)s",
			"so.transaction_date <= %(to_date)s",
		]
	)
	values.update({"from_date": filters.from_date, "to_date": filters.to_date})

	if filters.get("consultant"):
		conditions.append("so.ref_practitioner = %(consultant)s")
		values["consultant"] = filters.consultant

	if filters.get("patient"):
		conditions.append("so.patient = %(patient)s")
		values["patient"] = filters.patient

	if filters.get("item_group"):
		conditions.append("soi.item_group = %(item_group)s")
		values["item_group"] = filters.item_group

	status_expression = """
		CASE
			WHEN EXISTS (
				SELECT 1
				FROM `tabSales Invoice Item` original_item
				INNER JOIN `tabSales Invoice` original_invoice
					ON original_invoice.name = original_item.parent
				INNER JOIN `tabSales Invoice` return_invoice
					ON return_invoice.return_against = original_invoice.name
					AND return_invoice.docstatus = 1
					AND return_invoice.is_return = 1
				INNER JOIN `tabSales Invoice Item` return_item
					ON return_item.parent = return_invoice.name
					AND return_item.item_code = soi.item_code
				WHERE original_item.so_detail = soi.name
			) THEN 'Refunded'
			WHEN EXISTS (
				SELECT 1
				FROM `tabSales Invoice Item` invoice_item
				INNER JOIN `tabSales Invoice` invoice
					ON invoice.name = invoice_item.parent
				WHERE invoice_item.so_detail = soi.name
					AND IFNULL(invoice.is_return, 0) = 0
					AND invoice.status != 'Draft'
			) THEN 'Completed'
			ELSE 'Pending'
		END
	"""

	if filters.get("status"):
		conditions.append(f"({status_expression}) = %(status)s")
		values["status"] = filters.status

	return frappe.db.sql(
		f"""
			SELECT DISTINCT
				so.transaction_date AS date,
				so.ref_practitioner AS consultant,
				so.patient,
				COALESCE(NULLIF(so.patient_name, ''), p.patient_name) AS patient_name,
				COALESCE(NULLIF(p.mobile, ''), so.contact_mobile) AS mobile,
				soi.item_group,
				so.name AS sales_order,
				{status_expression} AS status
			FROM `tabSales Order` so
			INNER JOIN `tabSales Order Item` soi ON soi.parent = so.name
			LEFT JOIN `tabPatient` p ON p.name = so.patient
			WHERE {' AND '.join(conditions)}
			ORDER BY so.transaction_date DESC, so.creation DESC, soi.idx ASC
		""",
		values,
		as_dict=True,
	)

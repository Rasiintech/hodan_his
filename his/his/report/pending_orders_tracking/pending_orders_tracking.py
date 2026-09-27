# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, nowdate
from frappe.utils.nestedset import get_descendants_of


def execute(filters=None):
	frappe.has_permission("Sales Order", "read", throw=True)
	filters = frappe._dict(filters or {})
	from_date = getdate(filters.from_date) if filters.get("from_date") else getdate(nowdate())
	to_date = getdate(filters.to_date) if filters.get("to_date") else getdate(nowdate())
	if from_date > to_date:
		frappe.throw(_("From Date cannot be after To Date"))

	conditions = ["so.transaction_date BETWEEN %(from_date)s AND %(to_date)s"]
	query_filters = {"from_date": from_date, "to_date": to_date}
	if filters.get("consultant"):
		conditions.append("so.ref_practitioner = %(consultant)s")
		query_filters["consultant"] = filters.consultant
	if filters.get("patient"):
		conditions.append("so.patient = %(patient)s")
		query_filters["patient"] = filters.patient
	if filters.get("item_group"):
		conditions.append("pending_items.item_group IN %(item_groups)s")
		query_filters["item_groups"] = tuple(
			[filters.item_group, *get_descendants_of("Item Group", filters.item_group)]
		)

	data = frappe.db.sql(
		f"""
			SELECT
				so.transaction_date AS date,
				so.name AS sales_order,
				so.patient AS patient_id,
				COALESCE(NULLIF(so.patient_name, ''), so.patient) AS patient_name,
				COALESCE(
					(
						SELECT CASE
							WHEN ip.status IN ('Admitted', 'Discharge Scheduled') THEN 'Admitted'
							WHEN ip.status = 'Discharged' THEN 'Discharged'
							ELSE 'OPD'
						END
						FROM `tabInpatient Record` ip
						WHERE ip.patient = so.patient AND ip.docstatus < 2
						ORDER BY ip.creation DESC
						LIMIT 1
					),
					'OPD'
				) AS patient_status,
				COALESCE(NULLIF(hp.practitioner_name, ''), so.ref_practitioner) AS consultant,
				GROUP_CONCAT(DISTINCT pending_items.item_group ORDER BY pending_items.item_group SEPARATOR ', ') AS item_group,
				SUM(pending_items.pending_amount) AS total_amount,
				so.currency
			FROM `tabSales Order` so
			INNER JOIN (
				SELECT
					soi.parent,
					soi.item_group,
					GREATEST(soi.amount - IFNULL(billed_items.billed_amount, 0), 0) AS pending_amount
				FROM `tabSales Order Item` soi
				LEFT JOIN (
					SELECT
						sii.so_detail,
						SUM(ABS(sii.qty)) AS billed_qty,
						SUM(ABS(sii.amount)) AS billed_amount
					FROM `tabSales Invoice Item` sii
					INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
					WHERE
						si.docstatus = 1
						AND IFNULL(si.is_return, 0) = 0
						AND IFNULL(sii.so_detail, '') != ''
					GROUP BY sii.so_detail
				) billed_items ON billed_items.so_detail = soi.name
				WHERE GREATEST(soi.qty - IFNULL(billed_items.billed_qty, 0), 0) > 0
			) pending_items ON pending_items.parent = so.name
			LEFT JOIN `tabHealthcare Practitioner` hp ON hp.name = so.ref_practitioner
			WHERE
				so.docstatus = 1
				AND IFNULL(so.status, '') NOT IN ('Closed', 'Cancelled')
				AND IFNULL(so.patient, '') != ''
				AND {" AND ".join(conditions)}
			GROUP BY
				so.name,
				so.transaction_date,
				so.patient,
				so.patient_name,
				so.ref_practitioner,
				hp.practitioner_name,
				so.currency,
				so.creation
			ORDER BY so.transaction_date DESC, so.creation DESC
		""",
		query_filters,
		as_dict=True,
	)
	return get_columns(), data


def get_columns():
	return [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": _("Sales Order"), "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 160},
		{"label": _("Patient ID"), "fieldname": "patient_id", "fieldtype": "Link", "options": "Patient", "width": 140},
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 190},
		{"label": _("Patient Status"), "fieldname": "patient_status", "fieldtype": "Data", "width": 120},
		{"label": _("Consultant"), "fieldname": "consultant", "fieldtype": "Data", "width": 180},
		{"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 150},
		{"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "options": "currency", "width": 140},
	]

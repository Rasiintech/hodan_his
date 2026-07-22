# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today
from his.his.doctype.general_email_setting.general_email_setting import send_configured_doctype_email


class DepartmentAudit(Document):
	def on_submit(self):
		send_configured_doctype_email(self, "on_submit")


@frappe.whitelist()
def get_ceo_daily_view(audit_date=None, frequency="Daily", department=None):
	audit_date = getdate(audit_date or today())
	audit_frequency = normalize_frequency(frequency)
	department = (department or "").strip()
	frequency_values = get_frequency_values(audit_frequency)

	draft_departments = frappe.db.get_all(
		"Department Audit",
		filters={
			"docstatus": 0,
			"date": audit_date,
			"frequency": ["in", frequency_values],
			**({"department": department} if department else {}),
		},
		fields=["name", "department", "date", "frequency"],
		order_by="department asc",
	)

	rows = frappe.db.sql(
		"""
		select
			parent.name as audit_name,
			parent.department,
			parent.date,
			parent.frequency,
			child.area,
			child.task,
			child.follow_up,
			child.status,
			child.remarks
		from `tabDepartment Audit` parent
		inner join `tabDepartment Audit Item` child on child.parent = parent.name
		where parent.docstatus = 1
			and parent.date = %(audit_date)s
			and parent.frequency in %(frequency_values)s
			and (%(department)s = '' or parent.department = %(department)s)
		order by parent.department asc, child.idx asc
		""",
		{
			"audit_date": audit_date,
			"frequency_values": tuple(frequency_values),
			"department": department,
		},
		as_dict=True,
	)

	departments = []
	department_map = {}
	summary = {
		"departments": 0,
		"pending": 0,
		"done": 0,
		"na": 0,
	}

	for row in rows:
		department_name = row.department or "Unassigned"
		department_data = department_map.get(department_name)

		if not department_data:
			department_data = {
				"department": department_name,
				"audit_name": row.audit_name,
				"date": row.date,
				"frequency": row.frequency,
				"pending_tasks": [],
				"done_tasks": [],
				"na_tasks": [],
				"counts": {"pending": 0, "done": 0, "na": 0},
			}
			department_map[department_name] = department_data
			departments.append(department_data)

		task_entry = {
			"area": row.area,
			"task": row.task,
			"follow_up": row.follow_up,
			"status": row.status,
			"remarks": row.remarks,
		}

		status = (row.status or "Pending").strip()
		if status == "Done":
			department_data["done_tasks"].append(task_entry)
			department_data["counts"]["done"] += 1
			summary["done"] += 1
		elif status == "N/A":
			department_data["na_tasks"].append(task_entry)
			department_data["counts"]["na"] += 1
			summary["na"] += 1
		else:
			department_data["pending_tasks"].append(task_entry)
			department_data["counts"]["pending"] += 1
			summary["pending"] += 1

	submitted_departments = {
		(department.get("department") or "").strip()
		for department in departments
		if (department.get("department") or "").strip()
	}
	unique_draft_departments = []
	seen_draft_departments = set()
	for draft_department in draft_departments:
		department_name = (draft_department.get("department") or "").strip()
		if not department_name:
			continue
		if department_name in submitted_departments or department_name in seen_draft_departments:
			continue
		seen_draft_departments.add(department_name)
		unique_draft_departments.append(draft_department)

	summary["departments"] = len(departments)

	return {
		"date": str(audit_date),
		"frequency": audit_frequency,
		"department": department,
		"summary": summary,
		"departments": departments,
		"draft_departments": unique_draft_departments,
	}

def normalize_frequency(value):
	value = (value or "").strip()
	if value in ("Weekly", "Weakly"):
		return "Weekly"
	return value or "Daily"

def get_frequency_values(frequency):
	if frequency == "Weekly":
		return ("Weekly", "Weakly")
	return (frequency,)

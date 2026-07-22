# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DepartmentChecklist(Document):
	def validate(self):
		existing = frappe.db.get_value(
			"Department Checklist",
			{
				"department": self.department,
				"name": ["!=", self.name],
			},
			"name",
		)
		if existing:
			frappe.throw(
				_("Department Checklist {0} already exists for department {1}.").format(
					existing, self.department
				)
			)


@frappe.whitelist()
def get_checklist_items(department, frequency=None):
	checklist_name = frappe.db.get_value(
		"Department Checklist",
		{"department": department},
		"name",
	)
	if not checklist_name:
		return []

	checklist = frappe.get_doc("Department Checklist", checklist_name)
	selected_frequency = normalize_frequency(frequency)

	return [
		{
			"area": row.area,
			"task": row.task,
			"frequency": row.frequency,
			"follow_up": row.follow_up,
			"status": "Pending",
			"remarks": "",
		}
		for row in checklist.checklist_items
		if not selected_frequency or normalize_frequency(row.frequency) == selected_frequency
	]


def normalize_frequency(value):
	value = (value or "").strip()
	if value in ("Weekly", "Weakly"):
		return "Weekly"
	return value

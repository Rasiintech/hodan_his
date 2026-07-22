# Copyright (c) 2025, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class MembershipRegistration(Document):
	def before_insert(self):
		self.validate_adult_family_member_mobile_unique()

	def validate_adult_family_member_mobile_unique(self):
		adult_mobile_rows = {}

		for row in self.family_members or []:
			age = cint(row.age)
			mobile = (row.mobile or "").strip()
			normalized_mobile = self.get_mobile_last_nine_digits(mobile)

			if age <= 15 or not normalized_mobile:
				continue

			adult_mobile_rows.setdefault(normalized_mobile, []).append(
				{
					"full_name": row.full_name or _("Row {0}").format(row.idx),
					"mobile": mobile,
				}
			)

		duplicate_rows = {
			mobile: rows for mobile, rows in adult_mobile_rows.items() if len(rows) > 1
		}
		if duplicate_rows:
			duplicate_details = ", ".join(
				_("{0} for {1}").format(
					mobile, ", ".join(row["full_name"] for row in rows)
				)
				for mobile, rows in duplicate_rows.items()
			)
			frappe.throw(
				_(
					"Family member mobile number must be unique by last 9 digits for members older than 15. {0}"
				).format(duplicate_details)
			)

		existing_rows = frappe.db.sql(
			"""
			select child.parent, child.full_name, child.mobile
			from `tabFamily Members` child
			where child.parenttype = 'Membership Registration'
				and ifnull(child.age, 0) > 15
				and child.parent != %s
				and ifnull(child.mobile, '') != ''
			""",
			(self.name or "",),
			as_dict=True,
		)

		existing_rows_by_last_nine = {}
		for existing_row in existing_rows:
			normalized_mobile = self.get_mobile_last_nine_digits(existing_row.mobile)
			if normalized_mobile:
				existing_rows_by_last_nine.setdefault(normalized_mobile, []).append(existing_row)

		for mobile, rows in adult_mobile_rows.items():
			matches = existing_rows_by_last_nine.get(mobile) or []
			if matches:
				existing_row = matches[0]
				frappe.throw(
					_(
						"Family member mobile number with last 9 digits {0} is already used by adult member {1} in Membership Registration {2}."
					).format(
						mobile,
						existing_row.full_name or _("an existing member"),
						existing_row.parent,
					)
				)

	def get_mobile_last_nine_digits(self, mobile):
		digits_only = "".join(ch for ch in (mobile or "") if ch.isdigit())
		if len(digits_only) < 9:
			return digits_only
		return digits_only[-9:]

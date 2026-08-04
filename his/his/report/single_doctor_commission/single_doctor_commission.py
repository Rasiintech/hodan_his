import frappe
from frappe import _

from his.his.report.doctor_commission.doctor_commission import (
	get_columns as get_doctor_commission_columns,
	get_data as get_doctor_commission_data,
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	filters.ref_practitioner = resolve_practitioner(filters.ref_practitioner)
	return get_columns(), get_data(filters)


def validate_filters(filters):
	if not filters.get("ref_practitioner"):
		frappe.throw(_("Doctor is required"))


def resolve_practitioner(requested_practitioner):
	if frappe.session.user == "Administrator":
		return requested_practitioner

	linked_practitioner = frappe.db.get_value(
		"Healthcare Practitioner",
		{"user_id": frappe.session.user},
		"name",
	)
	if not linked_practitioner:
		frappe.throw(
			_("Your user is not linked to a Healthcare Practitioner."),
			frappe.PermissionError,
		)

	if requested_practitioner != linked_practitioner:
		frappe.throw(_("You can only view your own doctor commission."), frappe.PermissionError)

	return linked_practitioner


def get_columns():
	columns_by_field = {
		column.get("fieldname"): column.copy()
		for column in get_doctor_commission_columns()
	}
	columns_by_field["net_sales"]["label"] = _("Net Sales")
	columns_by_field["commission_percent"]["label"] = _("Percentage")
	return [
		columns_by_field[fieldname]
		for fieldname in (
			"item_group",
			"net_sales",
			"commission_percent",
			"net_commission",
		)
	]


def get_data(filters):
	return get_doctor_commission_data(frappe._dict(filters or {}))

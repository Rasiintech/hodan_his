# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)

	currency = frappe.get_cached_value("Company", filters.company, "default_currency")
	payments = get_payments(filters)
	invoices = get_invoices(filters)

	if filters.view == "Detailed":
		return get_detailed_columns(currency), build_detailed_data(invoices, payments)

	return get_summarized_columns(currency), build_summarized_data(invoices, payments)


def validate_filters(filters):
	for fieldname in ("company", "from_date", "to_date"):
		if not filters.get(fieldname):
			frappe.throw(_("{0} is required").format(_(fieldname.replace("_", " ").title())))

	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date cannot be after To Date"))

	if filters.get("view") not in ("Summarized", "Detailed"):
		filters.view = "Summarized"


def get_payments(filters):
	values = {
		"company": filters.company,
		"from_date": filters.from_date,
		"to_date": filters.to_date,
	}
	conditions = ""
	if filters.get("supplier"):
		values["supplier"] = filters.supplier
		conditions += " AND pe.party = %(supplier)s"
	if filters.get("mode_of_payment"):
		values["mode_of_payment"] = filters.mode_of_payment
		conditions += " AND pe.mode_of_payment = %(mode_of_payment)s"

	return frappe.db.sql(
		f"""
		SELECT
			pe.name,
			pe.posting_date,
			pe.party AS supplier,
			pe.party_name AS supplier_name,
			pe.mode_of_payment,
			pe.paid_from,
			pe.base_paid_amount,
			pe.reference_no,
			pe.reference_date,
			pe.remarks
		FROM `tabPayment Entry` pe
		WHERE pe.docstatus = 1
			AND pe.payment_type = 'Pay'
			AND pe.party_type = 'Supplier'
			AND pe.company = %(company)s
			AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
			{conditions}
		ORDER BY pe.party_name, pe.posting_date, pe.creation
		""",
		values,
		as_dict=True,
	)


def get_invoices(filters):
	values = {
		"company": filters.company,
		"from_date": filters.from_date,
		"to_date": filters.to_date,
	}
	conditions = ""
	if filters.get("supplier"):
		values["supplier"] = filters.supplier
		conditions += " AND pi.supplier = %(supplier)s"

	return frappe.db.sql(
		f"""
		SELECT
			pi.name,
			pi.posting_date,
			pi.supplier,
			pi.supplier_name,
			pi.base_grand_total,
			pi.bill_no AS reference_no,
			pi.bill_date AS reference_date,
			pi.remarks
		FROM `tabPurchase Invoice` pi
		WHERE pi.docstatus = 1
			AND pi.company = %(company)s
			AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
			{conditions}
		ORDER BY pi.supplier_name, pi.posting_date, pi.creation
		""",
		values,
		as_dict=True,
	)


def build_detailed_data(invoices, payments):
	rows = []
	for invoice in invoices:
		rows.append(
			{
				"posting_date": invoice.posting_date,
				"voucher_type": "Purchase Invoice",
				"voucher_no": invoice.name,
				"supplier": invoice.supplier,
				"supplier_name": invoice.supplier_name,
				"invoiced_amount": flt(invoice.base_grand_total),
				"paid_amount": 0,
				"reference_no": invoice.reference_no,
				"reference_date": invoice.reference_date,
				"remarks": invoice.remarks,
			}
		)
	for payment in payments:
		rows.append(
			{
				"posting_date": payment.posting_date,
				"voucher_type": "Payment Entry",
				"voucher_no": payment.name,
				"supplier": payment.supplier,
				"supplier_name": payment.supplier_name,
				"invoiced_amount": 0,
				"paid_amount": flt(payment.base_paid_amount),
				"mode_of_payment": payment.mode_of_payment,
				"paid_from": payment.paid_from,
				"reference_no": payment.reference_no,
				"reference_date": payment.reference_date,
				"remarks": payment.remarks,
			}
		)

	rows.sort(key=lambda row: ((row["supplier_name"] or "").strip().lower(), row["posting_date"]))

	if rows:
		rows.append(
			{
				"supplier_name": _("Total"),
				"invoiced_amount": sum(row["invoiced_amount"] for row in rows),
				"paid_amount": sum(row["paid_amount"] for row in rows),
				"is_grand_total": 1,
			}
		)

	return rows


def build_summarized_data(invoices, payments):
	suppliers = {}

	def get_supplier_row(supplier, supplier_name):
		return suppliers.setdefault(
			supplier,
			{
				"supplier": supplier,
				"supplier_name": supplier_name,
				"no_of_invoices": 0,
				"invoiced_amount": 0,
				"no_of_payments": 0,
				"paid_amount": 0,
				"last_payment_date": None,
			},
		)

	for invoice in invoices:
		row = get_supplier_row(invoice.supplier, invoice.supplier_name)
		row["no_of_invoices"] += 1
		row["invoiced_amount"] += flt(invoice.base_grand_total)

	for payment in payments:
		row = get_supplier_row(payment.supplier, payment.supplier_name)
		row["no_of_payments"] += 1
		row["paid_amount"] += flt(payment.base_paid_amount)
		if not row["last_payment_date"] or payment.posting_date > row["last_payment_date"]:
			row["last_payment_date"] = payment.posting_date

	for row in suppliers.values():
		row["balance"] = row["invoiced_amount"] - row["paid_amount"]

	data = sorted(suppliers.values(), key=lambda row: row["paid_amount"], reverse=True)

	if data:
		data.append(
			{
				"supplier_name": _("Total"),
				"no_of_invoices": sum(row["no_of_invoices"] for row in data),
				"invoiced_amount": sum(row["invoiced_amount"] for row in data),
				"no_of_payments": sum(row["no_of_payments"] for row in data),
				"paid_amount": sum(row["paid_amount"] for row in data),
				"balance": sum(row["balance"] for row in data),
				"is_grand_total": 1,
			}
		)

	return data


def get_detailed_columns(currency):
	return [
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 105},
		{"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 125},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 160,
		},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 330,
		},
		# {"label": _("Supplier Name"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 200},
		{
			"label": _("Invoiced ({0})").format(currency),
			"fieldname": "invoiced_amount",
			"fieldtype": "Currency",
			"options": currency,
			"width": 130,
		},
		{
			"label": _("Paid ({0})").format(currency),
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"options": currency,
			"width": 130,
		},
		# {
		# 	"label": _("Mode of Payment"),
		# 	"fieldname": "mode_of_payment",
		# 	"fieldtype": "Link",
		# 	"options": "Mode of Payment",
		# 	"width": 130,
		# },
		# {
		# 	"label": _("Paid From Account"),
		# 	"fieldname": "paid_from",
		# 	"fieldtype": "Link",
		# 	"options": "Account",
		# 	"width": 220,
		# },
		{"label": _("Reference No"), "fieldname": "reference_no", "fieldtype": "Data", "width": 125},
		{"label": _("Reference Date"), "fieldname": "reference_date", "fieldtype": "Date", "width": 110},
		{"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 320},
	]


def get_summarized_columns(currency):
	return [
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 340,
		},
		# {"label": _("Supplier Name"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 240},
		{"label": _("No of Invoices"), "fieldname": "no_of_invoices", "fieldtype": "Int", "width": 115},
		{
			"label": _("Total Invoiced ({0})").format(currency),
			"fieldname": "invoiced_amount",
			"fieldtype": "Currency",
			"options": currency,
			"width": 150,
		},
		{"label": _("No of Payments"), "fieldname": "no_of_payments", "fieldtype": "Int", "width": 125},
		{
			"label": _("Total Paid ({0})").format(currency),
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"options": currency,
			"width": 150,
		},
		{
			"label": _("Balance ({0})").format(currency),
			"fieldname": "balance",
			"fieldtype": "Currency",
			"options": currency,
			"width": 140,
		},
		{
			"label": _("Last Payment"),
			"fieldname": "last_payment_date",
			"fieldtype": "Date",
			"width": 115,
		},
	]

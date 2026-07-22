# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data


import frappe
from frappe.utils import add_days, getdate, nowdate

DRUG_INCOME_ACCOUNT = "Drug - HH"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	to_date = getdate(filters.get("to_date") or nowdate())
	from_date = getdate(filters.get("from_date") or add_days(to_date, -30))

	sql_filters = {
		"from_date": from_date,
		"to_date": to_date,
		"drug_income_account": DRUG_INCOME_ACCOUNT,
	}

	invoice_conditions = [
		"si.docstatus = 1",
		"IFNULL(si.is_return, 0) = 0",
		"si.posting_date >= %(from_date)s",
		"si.posting_date <= %(to_date)s",
		"IFNULL(si.ref_practitioner, '') != ''",
	]

	if filters.get("consultant"):
		invoice_conditions.append("si.ref_practitioner = %(consultant)s")
		sql_filters["consultant"] = filters.get("consultant")

	columns = [
		{
			"label": "Consultant",
			"fieldname": "consultant",
			"fieldtype": "Data",
			"width": 260,
		},
		{
			"label": "Total",
			"fieldname": "total_amount",
			"fieldtype": "Float",
			"width": 140,
		},
		{
			"label": "Discount",
			"fieldname": "discount_amount",
			"fieldtype": "Float",
			"width": 140,
		},
		{
			"label": "Net Sales",
			"fieldname": "net_sales",
			"fieldtype": "Float",
			"width": 160,
		},
		{
			"label": "Drug",
			"fieldname": "drug_amount",
			"fieldtype": "Float",
			"width": 140,
		},
		{
			"label": "Net After Drug",
			"fieldname": "after_drug",
			"fieldtype": "Float",
			"width": 160,
		},
	]

	data = frappe.db.sql(
		"""
		SELECT
			base.consultant,
			SUM(base.total_amount) AS total_amount,
			SUM(base.discount_amount) AS discount_amount,
			SUM(base.total_amount - base.discount_amount) AS net_sales,
			SUM(base.drug_amount) AS drug_amount,
			SUM((base.total_amount - base.discount_amount) - base.drug_amount) AS after_drug
		FROM (
			SELECT
				si.name AS sales_invoice,
				si.patient AS Patient,
				COALESCE(NULLIF(hp.practitioner_name, ''), si.ref_practitioner) AS consultant,
				MAX(IFNULL(si.total, 0)) AS total_amount,
				MAX(IFNULL(si.discount_amount, 0)) AS discount_amount,
				SUM(
					CASE
						WHEN sii.income_account = %(drug_income_account)s
						THEN IFNULL(sii.amount, 0)
						ELSE 0
					END
				) AS drug_amount
			FROM `tabSales Invoice` si
			LEFT JOIN `tabSales Invoice Item` sii
				ON sii.parent = si.name
			LEFT JOIN `tabHealthcare Practitioner` hp
				ON hp.name = si.ref_practitioner
			WHERE {invoice_conditions}
			GROUP BY
				si.name,
				si.patient,
				COALESCE(NULLIF(hp.patient_name, ''), si.patient)
		) base
		GROUP BY base.patient, base.patient
		ORDER BY base.patient ASC
		""".format(invoice_conditions=" AND ".join(invoice_conditions)),
		sql_filters,
		as_dict=True,
	)

	return columns, data

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt


COMMISSION_START_DATE = "2026-07-25"
DISCOUNT_EXCLUDED_SO_TYPE = "Pharmacy"
DISCOUNT_EXCLUDED_ITEM_GROUPS = ("OT",)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{
			"label": _("Ref Practitioner"),
			"fieldname": "ref_practitioner",
			"fieldtype": "Link",
			"options": "Healthcare Practitioner",
			"width": 180,
		},
		{"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 180},
		{
			"label": _("Total Invoiced"),
			"fieldname": "total_invoiced",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"label": _("Allocated Amount"),
			"fieldname": "allocated_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"label": _("Deduction Amount"),
			"fieldname": "deduction_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"label": _("Paid Amount"),
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"label": _("Gross Sales"),
			"fieldname": "gross_sales",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"label": _("Sales Expense %"),
			"fieldname": "expense_percent",
			"fieldtype": "Percent",
			"width": 130,
		},
		{
			"label": _("Sales Expense Amount"),
			"fieldname": "sales_expense_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 180,
		},
		{
			"label": _("Net Sales Amount"),
			"fieldname": "net_sales",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 180,
		},
		{
			"label": _("Commission %"),
			"fieldname": "commission_percent",
			"fieldtype": "Percent",
			"width": 130,
		},
		{
			"label": _("Net Commission"),
			"fieldname": "net_commission",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
	]


def get_data(filters):
	validate_filters(filters)

	amounts_by_group = defaultdict(new_group_totals)

	for row in get_invoiced_items(filters):
		key = (row.ref_practitioner, row.item_group)
		amounts_by_group[key]["total_invoiced"] += flt(row.base_net_amount)

	payment_rows = get_payment_rows(filters)
	if payment_rows:
		items_by_invoice = get_items_by_invoice([row.invoice for row in payment_rows])
		for payment in payment_rows:
			allocate_payment(amounts_by_group, payment, items_by_invoice.get(payment.invoice, []))

	return build_output(amounts_by_group)


def validate_filters(filters):
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are required"))

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be after To Date"))


def get_invoiced_items(filters):
	conditions = get_invoice_conditions(filters, date_field="si.posting_date")
	query_filters = dict(filters)
	query_filters["commission_start_date"] = COMMISSION_START_DATE
	return frappe.db.sql(
		f"""
			SELECT
				si.name AS invoice,
				si.ref_practitioner,
				sii.item_group,
				sii.base_net_amount
			FROM `tabSales Invoice` si
			INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
			WHERE
				si.docstatus = 1
				AND IFNULL(si.is_return, 0) = 0
				AND IFNULL(si.ref_practitioner, '') != ''
				AND {conditions}
		""",
		query_filters,
		as_dict=True,
	)


def get_payment_rows(filters):
	company_condition = "AND si.company = %(company)s" if filters.get("company") else ""
	practitioner_condition = (
		"AND si.ref_practitioner = %(ref_practitioner)s"
		if filters.get("ref_practitioner")
		else ""
	)

	query_filters = dict(filters)
	query_filters["commission_start_date"] = COMMISSION_START_DATE
	query_filters["discount_excluded_so_type"] = DISCOUNT_EXCLUDED_SO_TYPE
	query_filters["discount_excluded_item_groups"] = DISCOUNT_EXCLUDED_ITEM_GROUPS

	return frappe.db.sql(
		f"""
			SELECT
				payments.invoice,
				payments.ref_practitioner,
				payments.base_grand_total,
				payments.base_net_total,
				SUM(payments.base_allocated_amount) AS base_allocated_amount,
				SUM(payments.base_deduction_amount) AS base_deduction_amount,
				SUM(payments.base_insurance_coverage_amount) AS base_insurance_coverage_amount,
				SUM(payments.base_insurance_discount_amount) AS base_insurance_discount_amount,
				SUM(payments.base_employee_billed_amount) AS base_employee_billed_amount
			FROM (
				SELECT
					si.name AS invoice,
					si.ref_practitioner,
					si.base_grand_total,
					si.base_net_total,
					si.insurance_coverage_amount * IFNULL(NULLIF(si.conversion_rate, 0), 1)
						AS base_allocated_amount,
					si.insurance_coverage_amount * IFNULL(NULLIF(si.conversion_rate, 0), 1)
						* GREATEST(LEAST(IFNULL(ic.discount_percentage, 0), 100), 0) / 100
						AS base_deduction_amount,
					si.insurance_coverage_amount * IFNULL(NULLIF(si.conversion_rate, 0), 1)
						AS base_insurance_coverage_amount,
					si.insurance_coverage_amount * IFNULL(NULLIF(si.conversion_rate, 0), 1)
						* GREATEST(LEAST(IFNULL(ic.discount_percentage, 0), 100), 0) / 100
						AS base_insurance_discount_amount,
					0 AS base_employee_billed_amount
				FROM `tabSales Invoice` si
				LEFT JOIN `tabInsurance Company` ic ON ic.name = si.insurance_company
				WHERE
					si.docstatus = 1
					AND IFNULL(si.is_return, 0) = 0
					AND IFNULL(si.insurance_coverage_amount, 0) > 0
					AND IFNULL(si.ref_practitioner, '') != ''
					AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
					AND si.posting_date >= %(commission_start_date)s
					{company_condition}
					{practitioner_condition}

				UNION ALL

				SELECT
					si.name AS invoice,
					si.ref_practitioner,
					si.base_grand_total,
					si.base_net_total,
					GREATEST(
						si.base_net_total
							- IFNULL(si.insurance_coverage_amount, 0)
								* IFNULL(NULLIF(si.conversion_rate, 0), 1),
						0
					) AS base_allocated_amount,
					0 AS base_deduction_amount,
					0 AS base_insurance_coverage_amount,
					0 AS base_insurance_discount_amount,
					GREATEST(
						si.base_net_total
							- IFNULL(si.insurance_coverage_amount, 0)
								* IFNULL(NULLIF(si.conversion_rate, 0), 1),
						0
					) AS base_employee_billed_amount
				FROM `tabSales Invoice` si
				WHERE
					si.docstatus = 1
					AND IFNULL(si.is_return, 0) = 0
					AND IFNULL(si.bill_to_employee, 0) = 1
					AND IFNULL(si.bill_to_patient, '') = ''
					AND IFNULL(si.ref_practitioner, '') != ''
					AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
					AND si.posting_date >= %(commission_start_date)s
					AND GREATEST(
						si.base_net_total
							- IFNULL(si.insurance_coverage_amount, 0)
								* IFNULL(NULLIF(si.conversion_rate, 0), 1),
						0
					) > 0
					{company_condition}
					{practitioner_condition}

				UNION ALL

				SELECT
					si.name AS invoice,
					si.ref_practitioner,
					si.base_grand_total,
					si.base_net_total,
					GREATEST(
						si.base_net_total
							- IFNULL(si.insurance_coverage_amount, 0)
								* IFNULL(NULLIF(si.conversion_rate, 0), 1),
						0
					) AS base_allocated_amount,
					0 AS base_deduction_amount,
					0 AS base_insurance_coverage_amount,
					0 AS base_insurance_discount_amount,
					GREATEST(
						si.base_net_total
							- IFNULL(si.insurance_coverage_amount, 0)
								* IFNULL(NULLIF(si.conversion_rate, 0), 1),
						0
					) AS base_employee_billed_amount
				FROM `tabSales Invoice` si
				WHERE
					si.docstatus = 1
					AND IFNULL(si.is_return, 0) = 0
					AND IFNULL(si.bill_to_patient, '') != ''
					AND IFNULL(si.ref_practitioner, '') != ''
					AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
					AND si.posting_date >= %(commission_start_date)s
					AND GREATEST(
						si.base_net_total
							- IFNULL(si.insurance_coverage_amount, 0)
								* IFNULL(NULLIF(si.conversion_rate, 0), 1),
						0
					) > 0
					{company_condition}
					{practitioner_condition}

				UNION ALL

				SELECT
					si.name AS invoice,
					si.ref_practitioner,
					si.base_grand_total,
					si.base_net_total,
					si.base_paid_amount AS base_allocated_amount,
					0 AS base_deduction_amount,
					0 AS base_insurance_coverage_amount,
					0 AS base_insurance_discount_amount,
					0 AS base_employee_billed_amount
				FROM `tabSales Invoice` si
				WHERE
					si.docstatus = 1
					AND IFNULL(si.is_return, 0) = 0
					AND IFNULL(si.bill_to_employee, 0) = 0
					AND IFNULL(si.bill_to_patient, '') = ''
					AND IFNULL(si.ref_practitioner, '') != ''
					AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
					AND si.posting_date >= %(commission_start_date)s
					AND IFNULL(si.base_paid_amount, 0) > 0
					{company_condition}
					{practitioner_condition}

				UNION ALL

				SELECT
					si.name AS invoice,
					si.ref_practitioner,
					si.base_grand_total,
					si.base_net_total,
					per.allocated_amount
						* CASE
							WHEN IFNULL(per.exchange_rate, 0) > 0 THEN per.exchange_rate
							WHEN IFNULL(si.conversion_rate, 0) > 0 THEN si.conversion_rate
							ELSE 1
						END AS base_allocated_amount,
					CASE
						WHEN IFNULL(si.so_type, '') = %(discount_excluded_so_type)s
							OR NOT EXISTS (
								SELECT 1
								FROM `tabSales Invoice Item` commission_item
								INNER JOIN `tabCommission` commission_rule
									ON commission_rule.parent = si.ref_practitioner
									AND commission_rule.item_group = commission_item.item_group
									AND IFNULL(commission_rule.percent, 0) > 0
								WHERE commission_item.parent = si.name
									AND commission_item.item_group NOT IN %(discount_excluded_item_groups)s
							)
							THEN 0
						ELSE IFNULL(discounts.base_deduction_amount, 0)
							* (
								per.allocated_amount
								* CASE
									WHEN IFNULL(per.exchange_rate, 0) > 0 THEN per.exchange_rate
									WHEN IFNULL(si.conversion_rate, 0) > 0 THEN si.conversion_rate
									ELSE 1
								END
							)
							/ NULLIF(eligible_allocations.base_allocated_amount, 0)
					END AS base_deduction_amount,
					0 AS base_insurance_coverage_amount,
					0 AS base_insurance_discount_amount,
					0 AS base_employee_billed_amount
				FROM `tabPayment Entry` pe
				INNER JOIN `tabPayment Entry Reference` per ON per.parent = pe.name
				LEFT JOIN (
					SELECT parent, SUM(amount) AS base_deduction_amount
					FROM `tabPayment Entry Deduction`
					WHERE IFNULL(amount, 0) > 0
					GROUP BY parent
				) discounts ON discounts.parent = pe.name
				LEFT JOIN (
					SELECT
						eligible_per.parent,
						SUM(
							eligible_per.allocated_amount
							* CASE
								WHEN IFNULL(eligible_per.exchange_rate, 0) > 0
									THEN eligible_per.exchange_rate
								WHEN IFNULL(eligible_si.conversion_rate, 0) > 0
									THEN eligible_si.conversion_rate
								ELSE 1
							END
						) AS base_allocated_amount
					FROM `tabPayment Entry Reference` eligible_per
					INNER JOIN `tabPayment Entry` eligible_pe
						ON eligible_pe.name = eligible_per.parent
					INNER JOIN `tabSales Invoice` eligible_si
						ON eligible_per.reference_doctype = 'Sales Invoice'
						AND eligible_per.reference_name = eligible_si.name
					WHERE
						eligible_pe.docstatus = 1
						AND eligible_pe.payment_type = 'Receive'
						AND eligible_pe.party_type = 'Customer'
						AND eligible_pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
						AND IFNULL(eligible_per.allocated_amount, 0) > 0
						AND eligible_si.docstatus = 1
						AND IFNULL(eligible_si.is_return, 0) = 0
						AND eligible_si.posting_date >= %(commission_start_date)s
						AND IFNULL(eligible_si.bill_to_employee, 0) = 0
						AND IFNULL(eligible_si.bill_to_patient, '') = ''
						AND IFNULL(eligible_si.so_type, '') != %(discount_excluded_so_type)s
						AND EXISTS (
							SELECT 1
							FROM `tabSales Invoice Item` eligible_commission_item
							INNER JOIN `tabCommission` eligible_commission_rule
								ON eligible_commission_rule.parent = eligible_si.ref_practitioner
								AND eligible_commission_rule.item_group = eligible_commission_item.item_group
								AND IFNULL(eligible_commission_rule.percent, 0) > 0
							WHERE eligible_commission_item.parent = eligible_si.name
								AND eligible_commission_item.item_group NOT IN %(discount_excluded_item_groups)s
						)
					GROUP BY eligible_per.parent
				) eligible_allocations ON eligible_allocations.parent = pe.name
				INNER JOIN `tabSales Invoice` si
					ON per.reference_doctype = 'Sales Invoice'
					AND per.reference_name = si.name
				WHERE
					pe.docstatus = 1
					AND pe.payment_type = 'Receive'
					AND pe.party_type = 'Customer'
					AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
					AND IFNULL(per.allocated_amount, 0) > 0
					AND si.docstatus = 1
					AND IFNULL(si.is_return, 0) = 0
					AND si.posting_date >= %(commission_start_date)s
					AND IFNULL(si.bill_to_employee, 0) = 0
					AND IFNULL(si.bill_to_patient, '') = ''
						AND IFNULL(si.ref_practitioner, '') != ''
						{company_condition}
						{practitioner_condition}

					UNION ALL

					SELECT
						si.name AS invoice,
						si.ref_practitioner,
						si.base_grand_total,
						si.base_net_total,
						transfer_reference.allocated_amount
							* CASE
								WHEN IFNULL(transfer_reference.exchange_rate, 0) > 0
									THEN transfer_reference.exchange_rate
								WHEN IFNULL(si.conversion_rate, 0) > 0 THEN si.conversion_rate
								ELSE 1
							END AS base_allocated_amount,
						CASE
							WHEN IFNULL(si.so_type, '') = %(discount_excluded_so_type)s
								OR NOT EXISTS (
									SELECT 1
									FROM `tabSales Invoice Item` commission_item
									INNER JOIN `tabCommission` commission_rule
										ON commission_rule.parent = si.ref_practitioner
										AND commission_rule.item_group = commission_item.item_group
										AND IFNULL(commission_rule.percent, 0) > 0
									WHERE commission_item.parent = si.name
										AND commission_item.item_group NOT IN %(discount_excluded_item_groups)s
								)
								THEN 0
							ELSE LEAST(
								GREATEST(IFNULL(cbt.discount, 0), 0),
								IFNULL(eligible_transfer_allocations.base_allocated_amount, 0)
							)
								* (
									transfer_reference.allocated_amount
									* CASE
										WHEN IFNULL(transfer_reference.exchange_rate, 0) > 0
											THEN transfer_reference.exchange_rate
										WHEN IFNULL(si.conversion_rate, 0) > 0 THEN si.conversion_rate
										ELSE 1
									END
								)
								/ NULLIF(eligible_transfer_allocations.base_allocated_amount, 0)
						END AS base_deduction_amount,
						0 AS base_insurance_coverage_amount,
						0 AS base_insurance_discount_amount,
						0 AS base_employee_billed_amount
					FROM `tabCustomer Balance Transfer` cbt
					INNER JOIN `tabJournal Entry` transfer_journal
						ON transfer_journal.name = cbt.journal_entry
						AND transfer_journal.docstatus = 1
					INNER JOIN `tabPayment Entry Reference` transfer_reference
						ON transfer_reference.parent = cbt.name
						AND transfer_reference.parenttype = 'Customer Balance Transfer'
					LEFT JOIN (
						SELECT
							eligible_reference.parent,
							SUM(
								eligible_reference.allocated_amount
								* CASE
									WHEN IFNULL(eligible_reference.exchange_rate, 0) > 0
										THEN eligible_reference.exchange_rate
									WHEN IFNULL(eligible_si.conversion_rate, 0) > 0
										THEN eligible_si.conversion_rate
									ELSE 1
								END
							) AS base_allocated_amount
						FROM `tabPayment Entry Reference` eligible_reference
						INNER JOIN `tabCustomer Balance Transfer` eligible_transfer
							ON eligible_transfer.name = eligible_reference.parent
							AND eligible_reference.parenttype = 'Customer Balance Transfer'
						INNER JOIN `tabJournal Entry` eligible_transfer_journal
							ON eligible_transfer_journal.name = eligible_transfer.journal_entry
							AND eligible_transfer_journal.docstatus = 1
						INNER JOIN `tabSales Invoice` eligible_si
							ON eligible_reference.reference_doctype = 'Sales Invoice'
							AND eligible_reference.reference_name = eligible_si.name
						WHERE
							eligible_transfer.docstatus = 1
							AND eligible_transfer.date BETWEEN %(from_date)s AND %(to_date)s
							AND IFNULL(eligible_reference.allocated_amount, 0) > 0
							AND eligible_si.docstatus = 1
							AND IFNULL(eligible_si.is_return, 0) = 0
							AND eligible_si.posting_date >= %(commission_start_date)s
							AND IFNULL(eligible_si.bill_to_employee, 0) = 0
							AND IFNULL(eligible_si.bill_to_patient, '') = ''
							AND IFNULL(eligible_si.so_type, '') != %(discount_excluded_so_type)s
							AND EXISTS (
								SELECT 1
								FROM `tabSales Invoice Item` eligible_commission_item
								INNER JOIN `tabCommission` eligible_commission_rule
									ON eligible_commission_rule.parent = eligible_si.ref_practitioner
									AND eligible_commission_rule.item_group = eligible_commission_item.item_group
									AND IFNULL(eligible_commission_rule.percent, 0) > 0
								WHERE eligible_commission_item.parent = eligible_si.name
									AND eligible_commission_item.item_group NOT IN %(discount_excluded_item_groups)s
							)
						GROUP BY eligible_reference.parent
					) eligible_transfer_allocations
						ON eligible_transfer_allocations.parent = cbt.name
					INNER JOIN `tabSales Invoice` si
						ON transfer_reference.reference_doctype = 'Sales Invoice'
						AND transfer_reference.reference_name = si.name
					WHERE
						cbt.docstatus = 1
						AND cbt.date BETWEEN %(from_date)s AND %(to_date)s
						AND IFNULL(transfer_reference.allocated_amount, 0) > 0
						AND si.docstatus = 1
						AND IFNULL(si.is_return, 0) = 0
						AND si.posting_date >= %(commission_start_date)s
						AND IFNULL(si.bill_to_employee, 0) = 0
						AND IFNULL(si.bill_to_patient, '') = ''
						AND IFNULL(si.ref_practitioner, '') != ''
						{company_condition}
						{practitioner_condition}
				) payments
			GROUP BY
				payments.invoice,
				payments.ref_practitioner,
				payments.base_grand_total,
				payments.base_net_total
		""",
		query_filters,
		as_dict=True,
	)


def get_invoice_conditions(filters, date_field):
	conditions = [
		f"{date_field} BETWEEN %(from_date)s AND %(to_date)s",
		f"{date_field} >= %(commission_start_date)s",
	]

	if filters.get("company"):
		conditions.append("si.company = %(company)s")
	if filters.get("ref_practitioner"):
		conditions.append("si.ref_practitioner = %(ref_practitioner)s")

	return " AND ".join(conditions)


def get_items_by_invoice(invoice_names):
	if not invoice_names:
		return {}

	rows = frappe.get_all(
		"Sales Invoice Item",
		filters={"parent": ("in", invoice_names)},
		fields=["parent", "item_group", "base_net_amount"],
		order_by="parent, idx",
	)
	items_by_invoice = defaultdict(list)
	for row in rows:
		items_by_invoice[row.parent].append(row)

	return items_by_invoice


def allocate_payment(amounts_by_group, payment, invoice_items):
	base_grand_total = flt(payment.base_grand_total)
	base_net_total = flt(payment.base_net_total)
	if base_grand_total <= 0 or base_net_total == 0:
		return

	base_allocated_amount = min(max(flt(payment.base_allocated_amount), 0), base_grand_total)
	# Preserve contractual and payment deductions, but never let them create negative commission.
	base_deduction_amount = max(flt(payment.base_deduction_amount), 0)
	base_insurance_coverage_amount = min(
		max(flt(payment.base_insurance_coverage_amount), 0),
		base_allocated_amount,
		base_net_total,
	)
	base_insurance_discount_amount = min(
		max(flt(payment.base_insurance_discount_amount), 0),
		base_insurance_coverage_amount,
	)
	base_employee_billed_amount = min(
		max(flt(payment.base_employee_billed_amount), 0),
		max(base_allocated_amount - base_insurance_coverage_amount, 0),
		max(base_net_total - base_insurance_coverage_amount, 0),
	)
	base_cash_allocated_amount = max(
		base_allocated_amount - base_insurance_coverage_amount - base_employee_billed_amount,
		0,
	)
	base_cash_deduction_amount = max(base_deduction_amount - base_insurance_discount_amount, 0)
	deduction_eligible_total = sum(
		flt(item.base_net_amount)
		for item in invoice_items
		if item.item_group not in DISCOUNT_EXCLUDED_ITEM_GROUPS
	)

	for item in invoice_items:
		item_amount = flt(item.base_net_amount)
		key = (payment.ref_practitioner, item.item_group)
		item_share = item_amount / base_net_total
		cash_deduction_share = 0
		if item.item_group not in DISCOUNT_EXCLUDED_ITEM_GROUPS and deduction_eligible_total > 0:
			cash_deduction_share = base_cash_deduction_amount * item_amount / deduction_eligible_total

		insurance_allocated_share = base_insurance_coverage_amount * item_share
		insurance_discount_share = base_insurance_discount_amount * item_share
		employee_billed_share = base_employee_billed_amount * item_share
		cash_allocated_share = base_cash_allocated_amount * item_share
		cash_paid_share = max(cash_allocated_share - cash_deduction_share, 0)
		paid_share = (
			insurance_allocated_share
			- insurance_discount_share
			+ employee_billed_share
			+ cash_paid_share
		)
		commissionable_share = (
			insurance_allocated_share
			- insurance_discount_share
			+ employee_billed_share
			+ cash_paid_share * base_net_total / base_grand_total
		)

		amounts_by_group[key]["allocated_amount"] += base_allocated_amount * item_share
		amounts_by_group[key]["deduction_amount"] += insurance_discount_share + cash_deduction_share
		amounts_by_group[key]["paid_amount"] += paid_share
		amounts_by_group[key]["gross_sales"] += commissionable_share


def new_group_totals():
	return {
		"total_invoiced": 0.0,
		"allocated_amount": 0.0,
		"deduction_amount": 0.0,
		"paid_amount": 0.0,
		"gross_sales": 0.0,
	}


def build_output(amounts_by_group):
	practitioner_names = {key[0] for key in amounts_by_group if key[0]}
	commission_percent_map = {}
	expense_percent_map = {}

	for practitioner in practitioner_names:
		try:
			doc = frappe.get_doc("Healthcare Practitioner", practitioner)
		except frappe.DoesNotExistError:
			continue

		expense_percent_map[practitioner] = flt(doc.deduction_commission_percentage)
		for item in doc.get("commission", []):
			if item.item_group:
				commission_percent_map[(practitioner, item.item_group)] = flt(item.percent)

	output = []
	for (ref_practitioner, item_group), amounts in sorted(
		amounts_by_group.items(), key=lambda entry: (entry[0][0] or "", entry[0][1] or "")
	):
		commission_percent = commission_percent_map.get((ref_practitioner, item_group), 0)
		if not commission_percent:
			continue

		gross_sales = flt(amounts["gross_sales"])
		expense_percent = expense_percent_map.get(ref_practitioner, 0)
		if item_group == "Consultation":
			expense_percent = 0

		sales_expense_amount = gross_sales * expense_percent / 100
		net_sales = gross_sales - sales_expense_amount
		net_commission = net_sales * commission_percent / 100
		allocated_amount = round(amounts["allocated_amount"], 2)
		deduction_amount = round(amounts["deduction_amount"], 2)
		paid_amount = max(round(allocated_amount - deduction_amount, 2), 0)

		output.append(
			frappe._dict(
				{
					"ref_practitioner": ref_practitioner,
					"item_group": item_group,
					"total_invoiced": round(amounts["total_invoiced"], 2),
					"allocated_amount": allocated_amount,
					"deduction_amount": deduction_amount,
					"paid_amount": paid_amount,
					"gross_sales": round(gross_sales, 2),
					"expense_percent": expense_percent,
					"sales_expense_amount": round(sales_expense_amount, 2),
					"net_sales": round(net_sales, 2),
					"commission_percent": commission_percent,
					"net_commission": round(net_commission, 2),
				}
			)
		)

	return output

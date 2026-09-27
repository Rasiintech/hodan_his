# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


PAYMENT_DISCOUNT_ACCOUNT = "4999001 - Patient Service Discounts - HH"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	_validate_filters(filters)

	invoices = _get_invoices(filters)
	if not invoices:
		return _get_columns(), []

	payment_allocations = _get_payment_allocations([row.name for row in invoices])
	data = []

	for invoice in invoices:
		payment = payment_allocations.get(invoice.name)
		item_group_amount = flt(invoice.item_group_amount)
		item_group_share = _get_item_group_share(invoice)
		# The Sales Invoice discount is already applied to each item's net_amount.
		# Payment Entries are invoice-level, so only the selected Item Group's
		# proportional share is shown for invoices containing other item groups.
		allocated = (
			flt(payment.allocated_amount) * item_group_share
			if payment
			else item_group_amount
		)
		payment_discount = (
			flt(payment.discount_amount) * item_group_share if payment else 0
		)
		is_paid_insurance = invoice.status == "Paid" and (
			invoice.is_insurance or invoice.insurance_company
		)
		insurance_discount = item_group_amount * 0.15 if is_paid_insurance else 0
		total_discount = payment_discount + insurance_discount

		data.append(
			{
				"referring_practitioner": invoice.referring_practitioner,
				"item_group": invoice.item_group,
				"invoice": invoice.name,
				"posting_date": invoice.posting_date,
				"customer": invoice.customer,
				"customer_name": invoice.customer_name,
				"currency": invoice.currency,
				"amount": flt(item_group_amount, 2),
				"allocated": flt(allocated, 2),
				"discount": flt(total_discount, 2),
				"net_amount": flt(allocated - total_discount, 2),
			}
		)

	return _get_columns(), data


def _get_item_group_share(invoice):
	"""Return the selected Item Group's share of the invoice net item value."""
	invoice_net_total = abs(flt(invoice.net_total))
	if not invoice_net_total:
		return 0
	return abs(flt(invoice.item_group_amount)) / invoice_net_total


def _validate_filters(filters):
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("From Date and To Date are required."))
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be after To Date."))


def _get_invoices(filters):
	filters.item_group = filters.get("item_group") or "EEG"
	conditions = [
		"si.docstatus = 1",
		"coalesce(si.is_return, 0) = 0",
		"si.return_against is null",
		"si.grand_total >= 0",
		"not exists (select 1 from `tabSales Invoice` return_invoice "
		"where return_invoice.return_against = si.name "
		"and return_invoice.docstatus = 1)",
		"si.posting_date between %(from_date)s and %(to_date)s",
		"exists (select 1 from `tabSales Invoice Item` item_filter "
		"where item_filter.parent = si.name and item_filter.item_group = %(item_group)s "
		"and item_filter.net_amount >= 0)",
	]

	if filters.get("company"):
		conditions.append("si.company = %(company)s")
	if filters.get("referring_practitioner"):
		conditions.append("si.ref_practitioner = %(referring_practitioner)s")
	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")
	return frappe.db.sql(
		f"""
			select
				si.name,
				si.ref_practitioner as referring_practitioner,
				%(item_group)s as item_group,
				si.posting_date,
				si.customer,
				si.customer_name,
				si.currency,
				si.is_insurance,
				si.insurance_company,
				si.status,
				si.net_total,
				coalesce(
					(select sum(group_item.net_amount)
					 from `tabSales Invoice Item` group_item
					 where group_item.parent = si.name
						and group_item.item_group = %(item_group)s),
					0
				) as item_group_amount
			from `tabSales Invoice` si
			where {' and '.join(conditions)}
			order by si.posting_date desc, si.name desc
		""",
		filters,
		as_dict=True,
	)


def _get_payment_allocations(invoice_names):
	"""Return PE allocations and an invoice-level share of each PE discount.

	A Payment Entry discount is apportioned across its Sales Invoice references by
	their allocated amounts. This avoids repeating the full Payment Entry discount
	on every invoice when one receipt settles several invoices.
	"""
	rows = frappe.db.sql(
		"""
			select
				per.reference_name as invoice,
				per.parent as payment_entry,
				per.allocated_amount,
				coalesce(discounts.discount_amount, 0)
					/ coalesce(nullif(abs(pe.source_exchange_rate), 0), 1) as payment_discount,
				coalesce(
					(select sum(abs(all_refs.allocated_amount))
					 from `tabPayment Entry Reference` all_refs
					 where all_refs.parent = per.parent
						and all_refs.reference_doctype = 'Sales Invoice'),
					0
				) as payment_total_allocated
			from `tabPayment Entry Reference` per
			inner join `tabPayment Entry` pe on pe.name = per.parent
			left join (
				select
					parent,
					sum(greatest(amount, 0)) as discount_amount
				from `tabPayment Entry Deduction`
				where account = %(discount_account)s
				group by parent
			) discounts on discounts.parent = pe.name
			where pe.docstatus = 1
				and pe.payment_type = 'Receive'
				and per.reference_doctype = 'Sales Invoice'
				and per.reference_name in %(invoice_names)s
		""",
		{
			"invoice_names": tuple(invoice_names),
			"discount_account": PAYMENT_DISCOUNT_ACCOUNT,
		},
		as_dict=True,
	)

	allocations = {}
	for row in rows:
		allocation = allocations.setdefault(
			row.invoice, frappe._dict(allocated_amount=0, discount_amount=0)
		)
		allocation.allocated_amount += flt(row.allocated_amount)

		total_allocated = flt(row.payment_total_allocated)
		if total_allocated:
			allocation.discount_amount += flt(row.payment_discount) * abs(
				flt(row.allocated_amount)
			) / total_allocated

	return allocations


def _get_columns():
	return [
		{"label": _("Referring Practitioner"), "fieldname": "referring_practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 220},
		{"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 130},
		{"label": _("Invoice"), "fieldname": "invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 190},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 130},
		{"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 220},
		{"label": _("Currency"), "fieldname": "currency", "fieldtype": "Link", "options": "Currency", "hidden": 1},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "options": "currency", "precision": 2, "width": 120},
		{"label": _("Allocated"), "fieldname": "allocated", "fieldtype": "Currency", "options": "currency", "precision": 2, "width": 120},
		{"label": _("Discount"), "fieldname": "discount", "fieldtype": "Currency", "options": "currency", "precision": 2, "width": 120},
		{"label": _("Net Amount"), "fieldname": "net_amount", "fieldtype": "Currency", "options": "currency", "precision": 2, "width": 120},
	]

import frappe
from frappe import _
from frappe.utils import flt


DISCOUNT_ACCOUNT = "Discount - HH"


def allocate_discount_to_references(doc, method=None):
	if (
		doc.docstatus != 0
		or doc.payment_type != "Receive"
		or doc.party_type != "Customer"
	):
		return

	discount_in_company_currency = sum(
		max(flt(row.amount), 0)
		for row in doc.get("deductions")
		if row.account == DISCOUNT_ACCOUNT
	)
	if not discount_in_company_currency:
		return

	invoice_references = [
		row
		for row in doc.get("references")
		if row.reference_doctype == "Sales Invoice"
		and (flt(row.outstanding_amount) > 0 or flt(row.allocated_amount) > 0)
	]
	if not invoice_references:
		return

	other_allocations = sum(
		flt(row.allocated_amount)
		for row in doc.get("references")
		if row not in invoice_references
	)
	source_exchange_rate = flt(doc.source_exchange_rate) or 1
	discount_in_party_currency = discount_in_company_currency / source_exchange_rate
	target_invoice_allocation = (
		flt(doc.paid_amount) + discount_in_party_currency - other_allocations
	)
	if target_invoice_allocation < 0:
		return

	precision = _get_allocation_precision(invoice_references[0])
	weights = [flt(row.allocated_amount) for row in invoice_references]
	limits = [max(flt(row.outstanding_amount), 0) for row in invoice_references]
	allocations = distribute_with_limits(weights, limits, target_invoice_allocation, precision)
	if allocations is None:
		frappe.throw(
			_(
				"Discount - HH cannot be fully allocated because the selected Sales Invoices "
				"do not have enough outstanding amount."
			)
		)

	for row, allocated_amount in zip(invoice_references, allocations):
		row.allocated_amount = allocated_amount


def distribute_with_limits(weights, limits, target, precision=2):
	target = _round(target, precision)
	limits = [max(_round(limit, precision), 0) for limit in limits]
	weights = [max(flt(weight), 0) for weight in weights]
	tolerance = 10 ** (-precision)

	if target < 0 or target > _round(sum(limits), precision) + tolerance:
		return None
	if not weights:
		return None
	if not target:
		return [0.0 for _weight in weights]

	allocations = [0.0 for _weight in weights]
	active = {index for index, weight in enumerate(weights) if weight > 0}
	remaining = target

	while active:
		total_weight = sum(weights[index] for index in active)
		capped = [
			index
			for index in active
			if remaining * weights[index] / total_weight > limits[index] + tolerance
		]
		if not capped:
			for index in active:
				allocations[index] = remaining * weights[index] / total_weight
			break

		for index in capped:
			allocations[index] = limits[index]
			remaining -= limits[index]
			active.remove(index)

	allocations = [_round(amount, precision) for amount in allocations]
	difference = _round(target - sum(allocations), precision)
	if difference > 0:
		for index in sorted(range(len(allocations)), key=lambda i: limits[i] - allocations[i], reverse=True):
			increase = min(difference, _round(limits[index] - allocations[index], precision))
			if increase > 0:
				allocations[index] = _round(allocations[index] + increase, precision)
				difference = _round(difference - increase, precision)
			if not difference:
				break
	elif difference < 0:
		for index in sorted(range(len(allocations)), key=lambda i: allocations[i], reverse=True):
			decrease = min(abs(difference), allocations[index])
			if decrease > 0:
				allocations[index] = _round(allocations[index] - decrease, precision)
				difference = _round(difference + decrease, precision)
			if not difference:
				break

	return allocations if abs(_round(sum(allocations) - target, precision)) <= tolerance else None


def _round(value, precision):
	return round(flt(value), precision)


def _get_allocation_precision(reference):
	try:
		return reference.precision("allocated_amount")
	except (AttributeError, TypeError):
		return 2

from unittest import TestCase

import frappe

from his.api.payment_entry import allocate_discount_to_references, distribute_with_limits


class TestPaymentEntryDiscountAllocation(TestCase):
	def test_distributes_discount_proportionally(self):
		self.assertEqual(
			distribute_with_limits([60, 30], [100, 100], 100),
			[66.67, 33.33],
		)

	def test_redistributes_when_an_invoice_reaches_outstanding_limit(self):
		self.assertEqual(
			distribute_with_limits([60, 30], [62, 100], 100),
			[62, 38],
		)

	def test_returns_none_when_outstanding_cannot_absorb_discount(self):
		self.assertIsNone(distribute_with_limits([60, 30], [60, 35], 100))

	def test_uses_zero_allocated_invoice_when_paid_invoices_are_full(self):
		self.assertEqual(
			distribute_with_limits([70, 30, 0], [70, 30, 10], 110),
			[70, 30, 10],
		)

	def test_payment_entry_reference_allocations_include_discount(self):
		doc = frappe._dict(
			{
				"docstatus": 0,
				"payment_type": "Receive",
				"party_type": "Customer",
				"paid_amount": 90,
				"source_exchange_rate": 1,
				"deductions": [frappe._dict({"account": "Discount - HH", "amount": 10})],
				"references": [
					frappe._dict(
						{
							"reference_doctype": "Sales Invoice",
							"reference_name": "SINV-1",
							"outstanding_amount": 70,
							"allocated_amount": 60,
						}
					),
					frappe._dict(
						{
							"reference_doctype": "Sales Invoice",
							"reference_name": "SINV-2",
							"outstanding_amount": 50,
							"allocated_amount": 30,
						}
					),
				],
			}
		)

		allocate_discount_to_references(doc)

		self.assertEqual(doc.references[0].allocated_amount, 66.67)
		self.assertEqual(doc.references[1].allocated_amount, 33.33)

		allocate_discount_to_references(doc)
		self.assertEqual(doc.references[0].allocated_amount, 66.67)
		self.assertEqual(doc.references[1].allocated_amount, 33.33)

	def test_hook_keeps_zero_allocated_invoice_for_discount(self):
		doc = frappe._dict(
			{
				"docstatus": 0,
				"payment_type": "Receive",
				"party_type": "Customer",
				"paid_amount": 100,
				"source_exchange_rate": 1,
				"deductions": [frappe._dict({"account": "Discount - HH", "amount": 10})],
				"references": [
					frappe._dict(
						{
							"reference_doctype": "Sales Invoice",
							"reference_name": "SINV-70",
							"outstanding_amount": 70,
							"allocated_amount": 70,
						}
					),
					frappe._dict(
						{
							"reference_doctype": "Sales Invoice",
							"reference_name": "SINV-30",
							"outstanding_amount": 30,
							"allocated_amount": 30,
						}
					),
					frappe._dict(
						{
							"reference_doctype": "Sales Invoice",
							"reference_name": "SINV-10",
							"outstanding_amount": 10,
							"allocated_amount": 0,
						}
					),
				],
			}
		)

		allocate_discount_to_references(doc)

		self.assertEqual([row.allocated_amount for row in doc.references], [70, 30, 10])

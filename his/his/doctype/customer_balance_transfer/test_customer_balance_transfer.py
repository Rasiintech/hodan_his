# Copyright (c) 2026, Rasiin Tech and Contributors
# See license.txt

from unittest import TestCase

import frappe

from his.his.doctype.customer_balance_transfer.customer_balance_transfer import (
	CustomerBalanceTransfer,
	get_transfer_discount,
)


class TestCustomerBalanceTransfer(TestCase):
	def test_allocates_amount_and_discount_to_zero_allocated_invoice(self):
		doc = frappe._dict(
			{
				"amount": 100,
				"discount": 10,
				"reference": [
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

		CustomerBalanceTransfer.allocate_invoice_references(doc)

		self.assertEqual([row.allocated_amount for row in doc.reference], [70, 30, 10])

	def test_uses_discount_field_from_doctype(self):
		self.assertEqual(get_transfer_discount(frappe._dict({"discount": 10})), 10)

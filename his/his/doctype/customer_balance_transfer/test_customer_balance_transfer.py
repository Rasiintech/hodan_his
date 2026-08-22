# Copyright (c) 2026, Rasiin Tech and Contributors
# See license.txt

from unittest import TestCase
from unittest.mock import Mock, patch

import frappe

from his.his.doctype.customer_balance_transfer.customer_balance_transfer import (
	CustomerBalanceTransfer,
	get_customer_outstanding_invoices,
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

	def test_allocates_across_sales_invoice_and_journal_entry(self):
		doc = frappe._dict(
			{
				"amount": 300,
				"discount": 0,
				"reference": [
					frappe._dict(
						{
							"reference_doctype": "Sales Invoice",
							"reference_name": "SINV-200",
							"outstanding_amount": 200,
							"allocated_amount": 200,
						}
					),
					frappe._dict(
						{
							"reference_doctype": "Journal Entry",
							"reference_name": "JV-100",
							"outstanding_amount": 100,
							"allocated_amount": 100,
						}
					),
				],
			}
		)

		CustomerBalanceTransfer.allocate_invoice_references(doc)

		self.assertEqual([row.allocated_amount for row in doc.reference], [200, 100])

	@patch("his.his.doctype.customer_balance_transfer.customer_balance_transfer.frappe.get_doc")
	def test_journal_entry_preserves_reference_doctypes(self, get_doc):
		journal_entry = Mock()
		journal_entry.name = "JV-TRANSFER"
		get_doc.return_value = journal_entry
		doc = frappe._dict(
			{
				"target_account": "Employee Receivable - HH",
				"target_party_type": "Employee",
				"target_party": "HR-EMP-1",
				"source_account": "Debtors - HH",
				"source_customer": "CUST-1",
				"amount": 300,
				"discount": 0,
				"cost_center": "Main - HH",
				"company": "Hodan Hospital",
				"date": "2026-08-22",
				"reference": [
					frappe._dict(
						{
							"reference_doctype": "Sales Invoice",
							"reference_name": "SINV-200",
							"allocated_amount": 200,
						}
					),
					frappe._dict(
						{
							"reference_doctype": "Journal Entry",
							"reference_name": "JV-100",
							"allocated_amount": 100,
						}
					),
				],
				"get_user_remark": lambda: "Balance transfer",
			}
		)

		CustomerBalanceTransfer.make_journal_entry(doc)

		accounts = get_doc.call_args.args[0]["accounts"]
		self.assertEqual(
			[(row.get("reference_type"), row.get("reference_name")) for row in accounts[1:]],
			[("Sales Invoice", "SINV-200"), ("Journal Entry", "JV-100")],
		)
		journal_entry.insert.assert_called_once_with(ignore_permissions=True)
		journal_entry.submit.assert_called_once_with()

	@patch(
		"his.his.doctype.customer_balance_transfer.customer_balance_transfer."
		"get_outstanding_reference_documents"
	)
	def test_fetches_sales_invoice_and_journal_entry_outstanding(self, get_outstanding):
		get_outstanding.return_value = [
			frappe._dict(
				{
					"voucher_type": "Sales Invoice",
					"voucher_no": "SINV-200",
					"due_date": "2026-08-22",
					"invoice_amount": 200,
					"outstanding_amount": 200,
					"exchange_rate": 1,
					"payment_term": None,
				}
			),
			frappe._dict(
				{
					"voucher_type": "Journal Entry",
					"voucher_no": "JV-100",
					"due_date": None,
					"invoice_amount": 100,
					"outstanding_amount": 100,
					"exchange_rate": 1,
					"payment_term": None,
				}
			),
		]

		rows = get_customer_outstanding_invoices(
			"CUST-1",
			"Debtors - HH",
			"Hodan Hospital",
			"2026-08-22",
		)

		self.assertEqual(
			[(row["reference_doctype"], row["outstanding_amount"]) for row in rows],
			[("Sales Invoice", 200), ("Journal Entry", 100)],
		)

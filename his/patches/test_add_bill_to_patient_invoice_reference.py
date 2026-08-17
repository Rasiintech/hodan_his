from unittest import TestCase

from his.patches.add_bill_to_patient_invoice_reference import (
	ORIGINAL_CREDIT_ROW,
	REFERENCED_CREDIT_ROW,
	add_invoice_reference,
)


class TestBillToPatientInvoiceReferencePatch(TestCase):
	def test_adds_reference_only_to_first_credit_row(self):
		script = f"{ORIGINAL_CREDIT_ROW}\n{ORIGINAL_CREDIT_ROW}"

		updated = add_invoice_reference(script)

		self.assertEqual(updated.count(REFERENCED_CREDIT_ROW), 1)
		self.assertEqual(updated.count(ORIGINAL_CREDIT_ROW), 1)

	def test_is_idempotent(self):
		self.assertEqual(
			add_invoice_reference(REFERENCED_CREDIT_ROW),
			REFERENCED_CREDIT_ROW,
		)

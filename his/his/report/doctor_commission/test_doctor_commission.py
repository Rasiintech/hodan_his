from collections import defaultdict
from unittest import TestCase

import frappe

from his.his.report.doctor_commission.doctor_commission import allocate_payment, new_group_totals


class TestDoctorCommission(TestCase):
	def test_partial_payment_is_allocated_across_item_groups(self):
		amounts = defaultdict(new_group_totals)
		payment = frappe._dict(
			{
				"ref_practitioner": "Doctor",
				"base_grand_total": 100,
				"base_net_total": 100,
				"base_allocated_amount": 50,
				"base_deduction_amount": 0,
			}
		)
		items = [
			frappe._dict({"item_group": "X-ray", "base_net_amount": 60}),
			frappe._dict({"item_group": "Laboratory", "base_net_amount": 40}),
		]

		allocate_payment(amounts, payment, items)

		self.assertEqual(amounts[("Doctor", "X-ray")]["allocated_amount"], 30)
		self.assertEqual(amounts[("Doctor", "X-ray")]["deduction_amount"], 0)
		self.assertEqual(amounts[("Doctor", "X-ray")]["paid_amount"], 30)
		self.assertEqual(amounts[("Doctor", "X-ray")]["gross_sales"], 30)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["paid_amount"], 20)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["gross_sales"], 20)

	def test_paid_amount_includes_tax_but_gross_sales_does_not(self):
		amounts = defaultdict(new_group_totals)
		payment = frappe._dict(
			{
				"ref_practitioner": "Doctor",
				"base_grand_total": 105,
				"base_net_total": 100,
				"base_allocated_amount": 52.5,
				"base_deduction_amount": 0,
			}
		)
		items = [frappe._dict({"item_group": "Laboratory", "base_net_amount": 100})]

		allocate_payment(amounts, payment, items)

		self.assertEqual(amounts[("Doctor", "Laboratory")]["paid_amount"], 52.5)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["gross_sales"], 50)

	def test_insurance_coverage_is_directly_commissionable(self):
		amounts = defaultdict(new_group_totals)
		payment = frappe._dict(
			{
				"ref_practitioner": "Doctor",
				"base_grand_total": 105,
				"base_net_total": 100,
				"base_allocated_amount": 50,
				"base_deduction_amount": 0,
				"base_insurance_coverage_amount": 50,
			}
		)
		items = [frappe._dict({"item_group": "Laboratory", "base_net_amount": 100})]

		allocate_payment(amounts, payment, items)

		self.assertEqual(amounts[("Doctor", "Laboratory")]["allocated_amount"], 50)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["paid_amount"], 50)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["gross_sales"], 50)

	def test_insurance_company_discount_reduces_covered_commission(self):
		amounts = defaultdict(new_group_totals)
		payment = frappe._dict(
			{
				"ref_practitioner": "Doctor",
				"base_grand_total": 100,
				"base_net_total": 100,
				"base_allocated_amount": 100,
				"base_deduction_amount": 8,
				"base_insurance_coverage_amount": 80,
				"base_insurance_discount_amount": 8,
			}
		)
		items = [frappe._dict({"item_group": "Laboratory", "base_net_amount": 100})]

		allocate_payment(amounts, payment, items)

		self.assertEqual(amounts[("Doctor", "Laboratory")]["allocated_amount"], 100)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["deduction_amount"], 8)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["paid_amount"], 92)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["gross_sales"], 92)

	def test_bill_to_employee_net_amount_is_directly_commissionable(self):
		amounts = defaultdict(new_group_totals)
		payment = frappe._dict(
			{
				"ref_practitioner": "Doctor",
				"base_grand_total": 105,
				"base_net_total": 100,
				"base_allocated_amount": 100,
				"base_deduction_amount": 0,
				"base_employee_billed_amount": 100,
			}
		)
		items = [frappe._dict({"item_group": "Laboratory", "base_net_amount": 100})]

		allocate_payment(amounts, payment, items)

		self.assertEqual(amounts[("Doctor", "Laboratory")]["allocated_amount"], 100)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["paid_amount"], 100)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["gross_sales"], 100)

	def test_payment_is_capped_at_invoice_grand_total(self):
		amounts = defaultdict(new_group_totals)
		payment = frappe._dict(
			{
				"ref_practitioner": "Doctor",
				"base_grand_total": 100,
				"base_net_total": 100,
				"base_allocated_amount": 120,
				"base_deduction_amount": 0,
			}
		)
		items = [frappe._dict({"item_group": "Consultation", "base_net_amount": 100})]

		allocate_payment(amounts, payment, items)

		self.assertEqual(amounts[("Doctor", "Consultation")]["paid_amount"], 100)
		self.assertEqual(amounts[("Doctor", "Consultation")]["gross_sales"], 100)

	def test_discount_reduces_paid_amount_and_commission_gross_sales(self):
		amounts = defaultdict(new_group_totals)
		payment = frappe._dict(
			{
				"ref_practitioner": "Doctor",
				"base_grand_total": 100,
				"base_net_total": 100,
				"base_allocated_amount": 100,
				"base_deduction_amount": 20,
			}
		)
		items = [
			frappe._dict({"item_group": "X-ray", "base_net_amount": 60}),
			frappe._dict({"item_group": "Laboratory", "base_net_amount": 40}),
		]

		allocate_payment(amounts, payment, items)

		self.assertEqual(amounts[("Doctor", "X-ray")]["allocated_amount"], 60)
		self.assertEqual(amounts[("Doctor", "X-ray")]["deduction_amount"], 12)
		self.assertEqual(amounts[("Doctor", "X-ray")]["paid_amount"], 48)
		self.assertEqual(amounts[("Doctor", "X-ray")]["gross_sales"], 48)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["allocated_amount"], 40)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["deduction_amount"], 8)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["paid_amount"], 32)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["gross_sales"], 32)

	def test_discount_cannot_make_commissionable_payment_negative(self):
		amounts = defaultdict(new_group_totals)
		payment = frappe._dict(
			{
				"ref_practitioner": "Doctor",
				"base_grand_total": 100,
				"base_net_total": 100,
				"base_allocated_amount": 100,
				"base_deduction_amount": 120,
			}
		)
		items = [frappe._dict({"item_group": "Laboratory", "base_net_amount": 100})]

		allocate_payment(amounts, payment, items)

		self.assertEqual(amounts[("Doctor", "Laboratory")]["allocated_amount"], 100)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["deduction_amount"], 120)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["paid_amount"], 0)
		self.assertEqual(amounts[("Doctor", "Laboratory")]["gross_sales"], 0)

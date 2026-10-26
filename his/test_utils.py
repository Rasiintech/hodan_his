import unittest
from unittest.mock import MagicMock, patch

from his.utils import get_allowed_discount


class TestAllowedDiscount(unittest.TestCase):
    def test_customer_group_allowance_preserves_role_authority(self):
        cases = [
            # Ignore approvals, group default, role limit, effective limit.
            (1, 50, 10, 50),
            (1, 50, 100, 100),
            (0, 50, 10, 10),
            (0, 50, 100, 100),
            (1, 150, 10, 100),
            (1, -10, 10, 10),
        ]
        for ignore, default, role_limit, expected in cases:
            with self.subTest(ignore=ignore, default=default, role_limit=role_limit):
                with (
                    patch("his.utils.frappe.db", new=MagicMock()) as db,
                    patch("his.utils.frappe.get_roles", return_value=["Approver"]),
                    patch("his.utils.get_discount_levels", return_value={"Approver": role_limit}),
                ):
                    db.get_value.side_effect = ["Membership", (ignore, default)]
                    limit = get_allowed_discount("Customer")
                    self.assertEqual(limit, expected)

    def test_without_customer_uses_role_limit(self):
        with (
            patch("his.utils.frappe.get_roles", return_value=["Approver"]),
            patch("his.utils.get_discount_levels", return_value={"Approver": 100}),
        ):
            self.assertEqual(get_allowed_discount(), 100)

    def test_group_allowance_applies_without_matching_role(self):
        with (
            patch("his.utils.frappe.db", new=MagicMock()) as db,
            patch("his.utils.frappe.get_roles", return_value=[]),
            patch("his.utils.get_discount_levels", return_value={"Approver": 100}),
        ):
            db.get_value.side_effect = ["Membership", (1, 50)]
            self.assertEqual(get_allowed_discount("Customer"), 50)


# import frappe
# from frappe.utils import flt

# def get_discount_levels(doctype="Discount Level"):
#     """Fetch role-based discount limits from the specified doctype."""
#     return {
#         row.role: flt(row.discount_allowed)
#         for row in frappe.get_all(doctype, fields=("role", "discount_allowed"))
#     }

# def get_allowed_discount(doctype="Discount Level"):
#     """Return the highest discount allowed for the current user based on their roles."""
#     discount_levels = get_discount_levels(doctype)
#     if not discount_levels:
#         return 100  # fallback to full permission

#     roles = frappe.get_roles()
#     allowed_discounts = [
#         discount_allowed
#         for role, discount_allowed in discount_levels.items()
#         if role in roles
#     ]
#     return max(allowed_discounts) if allowed_discounts else 0



import frappe
from frappe.utils import flt


def get_discount_levels():
    return {
        row.role: flt(row.discount_allowed)
        for row in frappe.get_all("Discount Level", fields=("role", "discount_allowed"))
    }


def get_allowed_discount(customer = None):
    # Customer Groups marked to bypass role limits use their configured default.
    if customer:
        customer_group = frappe.db.get_value("Customer", customer, "customer_group")
        ignore_discount, default_discount_percentage = frappe.db.get_value(
            "Customer Group",
            customer_group,
            ["ignore_discount", "default_discount_percentage"],
        ) or (0, 0)
        if ignore_discount:
            return min(max(flt(default_discount_percentage), 0), 100)
        
    discount_levels = get_discount_levels()
    if not discount_levels:
        return 100

    roles = frappe.get_roles()
    discount_levels = [
        discount_allowed
        for role, discount_allowed in discount_levels.items()
        if role in roles
    ]
    return max(discount_levels) if discount_levels else 0



# import frappe
# from frappe.utils import flt


# def get_discount_levels():
#     return {
#         row.role: flt(row.discount_allowed)
#         for row in frappe.get_all("Discount Level", fields=("role", "discount_allowed"))
#     }


# def get_allowed_discount():
#     discount_levels = get_discount_levels()
#     if not discount_levels:
#         return 100

#     roles = frappe.get_roles()
#     discount_levels = [
#         discount_allowed
#         for role, discount_allowed in discount_levels.items()
#         if role in roles
#     ]
#     return max(discount_levels) if discount_levels else 0

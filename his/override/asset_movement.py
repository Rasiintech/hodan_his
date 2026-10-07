import frappe
from frappe import _

from erpnext.assets.doctype.asset_movement.asset_movement import AssetMovement


class CustomAssetMovement(AssetMovement):
	def validate_location(self):
		if self.purpose != "Transfer":
			return super().validate_location()

		for item in self.assets:
			if not item.source_location:
				item.source_location = frappe.db.get_value("Asset", item.asset, "location")

			if not item.source_location:
				frappe.throw(_("Source Location is required for the Asset {0}").format(item.asset))

			current_location = frappe.db.get_value("Asset", item.asset, "location")
			if current_location != item.source_location:
				frappe.throw(
					_("Asset {0} does not belongs to the location {1}").format(
						item.asset, item.source_location
					)
				)

			if item.to_employee:
				if not item.from_employee:
					frappe.throw(
						_("From Employee is required while transferring Asset {0} to an employee").format(
							item.asset
						)
					)

				if item.from_employee == item.to_employee:
					frappe.throw(_("From Employee and To Employee cannot be the same"))

				# Changing custodians does not imply a physical movement.
				item.target_location = item.source_location
				continue

			if not item.target_location:
				frappe.throw(_("Target Location is required while transferring Asset {0}").format(item.asset))

			if item.source_location == item.target_location:
				frappe.throw(_("Source and Target Location cannot be same"))

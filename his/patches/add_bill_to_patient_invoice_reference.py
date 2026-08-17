import frappe


SERVER_SCRIPT_NAME = "Bill To"
ORIGINAL_CREDIT_ROW = (
	'"credit_in_account_currency": doc.outstanding_amount,\n'
	'\t\t\t"cost_center": doc.cost_center'
)
REFERENCED_CREDIT_ROW = (
	'"credit_in_account_currency": doc.outstanding_amount,\n'
	'\t\t\t"reference_type": "Sales Invoice",\n'
	'\t\t\t"reference_name": doc.name,\n'
	'\t\t\t"cost_center": doc.cost_center'
)


def execute():
	if not frappe.db.exists("Server Script", SERVER_SCRIPT_NAME):
		return

	script = frappe.db.get_value("Server Script", SERVER_SCRIPT_NAME, "script") or ""
	updated_script = add_invoice_reference(script)
	if updated_script == script:
		return

	frappe.db.set_value(
		"Server Script",
		SERVER_SCRIPT_NAME,
		"script",
		updated_script,
		update_modified=False,
	)
	frappe.cache().delete_value("server_script_map")


def add_invoice_reference(script):
	if REFERENCED_CREDIT_ROW in script:
		return script
	return script.replace(ORIGINAL_CREDIT_ROW, REFERENCED_CREDIT_ROW, 1)

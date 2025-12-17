from erpnext.stock.get_item_details import get_pos_profile
import  frappe

@frappe.whitelist()
def make_cancel(**args):

	si = args.get("sales_invoice")
	so = args.get("sales_order")
	fee_name = args.get("fee")
	que = args.get("que")

	# Cancel Sales Order
	if so and frappe.db.exists("Sales Order", so):
		sales_order = frappe.get_doc("Sales Order", so)
		if sales_order.docstatus == 1:
			sales_order.cancel()

	# Cancel Sales Invoice
	if si and frappe.db.exists("Sales Invoice", si):
		sales_invoice = frappe.get_doc("Sales Invoice", si)
		if sales_invoice.docstatus == 1:
			sales_invoice.cancel()

	# Mark Fee Validity as Cancelled
	if fee_name and frappe.db.exists("Fee Validity", fee_name):
		frappe.db.set_value("Fee Validity", fee_name, "is_cancel", 1)

	# Update Queue
	if que:
		frappe.db.set_value("Que", que, "status", "Canceled")

	frappe.db.commit()

# @frappe.whitelist()
# def make_cancel(**args):
	
# 	si= args.get("sales_invoice")	
# 	so = args.get("sales_order")
# 	if so:
# 		sales_order =  frappe.get_doc("Sales Order",args.get("sales_order"))
# 		sales_order.cancel()
# 	# f= frappe.get_doc("Fee Validity",args.get("fee"))
# 	# f.cancel()
# 	if si:
# 		sales_invoice = frappe.get_doc("Sales Invoice",args.get("sales_invoice"))
# 		sales_invoice.cancel()
 

# 	fee_name = args.get("fee")
# 	frappe.errprint(fee_name)
# 	if fee_name and frappe.db.exists("Fee Validity", fee_name):
# 		fee_validity = frappe.get_doc("Fee Validity", fee_name)
# 		if fee_validity.docstatus == 1:
# 			fee_validity.cancel()

# 	frappe.db.set_value('Que', args.get("que"), 'status', 'Canceled')
	





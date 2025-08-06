import frappe;
def make_sample_collection(doc, method=None , items = None):
	itms= []
	if items:
		itms = items
	else:
	
	

   
		count=0
		for i in doc.items:
			# if i.item_group == "Laboratory":
			if frappe.db.exists("Lab Test Template", {"item": i.item_code}, cache=True):
				count=count+1
				itms.append(
							{
							"lab_test":  frappe.db.get_value("Lab Test Template",  {"item": i.item_code},"name")

							
				}
				)

	if itms:
		sm_doc = frappe.get_doc({
			'doctype': 'Sample Collection',
			'sample_qty': 1,
			'practitioner':doc.ref_practitioner,
			'patient': doc.patient,
			'lab_test': itms,
			'reff_invoice' : doc.name,
			'source_order' : doc.source_order,
			'doner' : doc.doner,
			"for_patient" : doc.ref_patient,
			# "blood_donar" : 1
		})
		sm_doc.insert(ignore_permissions = True)
		tok = token_numebr(sm_doc)
		frappe.msgprint(tok)
		sm_doc.Token_no = tok
		event = "sample_msg"
		frappe.publish_realtime(event)
	



	
@frappe.whitelist()
def token_numebr(doc, method=None):
	date = doc.date
	b = frappe.db.sql(f""" select Max(token_no) as max from `tabSample Collection` where date = '{date}'  ; """ , as_dict = True)
	num = b[0]['max'] 
	# frappe.msgprint(num)
	if num == None:
		num = 0
	
	doc.token_no = int(num) + 1
	# doc.appointment_time = ""
	col = frappe.get_last_doc("Sample Collection")
	
	if col:
		if col.lab_ref:
			doc.lab_ref = int(col.lab_ref) + 1
	# doc.appointment_time = ""
	if frappe.db.exists("Sample Collection", {}):
		col = frappe.get_last_doc("Sample Collection")
		if col.token_no:
			return col.token_no + 1
		else:
			return 1
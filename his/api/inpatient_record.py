import frappe
from frappe.utils import now_datetime
import json
@frappe.whitelist()
def inpatient_record(docname,admitted_status,reason = None,  method=None):
	if docname:
		
		ipr_data = frappe.get_doc("Inpatient Record" , docname)
		ipr_data.accepted_nurse =  frappe.session.user
		ipr_data.accepted_or_rejected = admitted_status
		if reason:
			ipr_data.reason = reason
			frappe.errprint(reason)
		ipr_data.save()


@frappe.whitelist()
def clearance(**args):
	reason=args.get("reason")
	name=args.get("name")
	docname= frappe.get_doc("Discharge And Clearance",name)
	reason=frappe.db.set_value('Discharge And Clearance', name, 'reason', reason )
	# frappe.errprint(name)
	patient = docname.patient
	doc = frappe.get_doc('Inpatient Record', {"patient":patient})
	doc.clearance_status="Cleared"
	doc.save()

@frappe.whitelist()
def clear_patient(inpatient_record):
	doc = frappe.get_doc('Inpatient Record', inpatient_record)
	doc.clearance_status="Cleared"
	doc.save()
	
# @frappe.whitelist()
# def check_out_inpatient(inpatient_record):
# 	# frappe.msgprint(inpatient_record)
# 	if frappe.db.exists("Inpatient Record" , inpatient_record):
# 		inpatient_record = frappe.get_doc("Inpatient Record" , inpatient_record)
# 		if inpatient_record.inpatient_occupancies:
# 			for inpatient_occupancy in inpatient_record.inpatient_occupancies:
# 				if inpatient_occupancy.left != 1:
# 					inpatient_occupancy.left = True
# 					inpatient_occupancy.check_out = now_datetime()
# 					frappe.db.set_value(
# 						"Healthcare Service Unit", inpatient_occupancy.service_unit, "occupancy_status", "Vacant"
# 					)
# 		inpatient_record.status = "Discharged"
# 		inpatient_record.discharge_datetime = frappe.utils.now()
# 		inpatient_record.save()
		
# 		customer = frappe.db.get_value("Patient", inpatient_record.patient, "customer")
# 		cust_gr = frappe.db.get_value("Customer", customer, "customer_group")
		
# 		customer_group=frappe.get_doc("Customer Group" ,cust_gr)
# 		if customer_group.debtor_type=="Inpatient":
# 			customer_group.status= "Closed"
# 			customer_group.save()

@frappe.whitelist()
def check_out_inpatient(inpatient_record):
	if frappe.db.exists("Inpatient Record", inpatient_record):
		inpatient_record = frappe.get_doc("Inpatient Record", inpatient_record)
		if inpatient_record.inpatient_occupancies:
			for inpatient_occupancy in inpatient_record.inpatient_occupancies:
				if not inpatient_occupancy.left:
					inpatient_occupancy.left = True
					inpatient_occupancy.check_out = now_datetime()

					frappe.db.set_value(
						"Healthcare Service Unit",
						inpatient_occupancy.service_unit,
						{
							"occupancy_status": "Vacant",
							"patient": ""
						}
					)

		inpatient_record.status = "Discharged"
		inpatient_record.discharge_datetime = frappe.utils.now()
		inpatient_record.save(ignore_permissions=True)
		frappe.db.commit()  # Ensure changes are flushed

		if inpatient_record.doctor_plan:
			inpatient_record.doctor_plan.submit()

		customer = frappe.db.get_value("Patient", inpatient_record.patient, "customer")
		cust_gr = frappe.db.get_value("Customer", customer, "customer_group")
		
		if cust_gr:
			customer_group = frappe.get_doc("Customer Group", cust_gr)
			if customer_group.debtor_type == "Inpatient":
				customer_group.status = "Closed"
				customer_group.save()

# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now_datetime
from datetime import datetime
from frappe.model.document import Document
from his.api.discharge import patient_clearance
from his.api.doctor_plan import set_so_values_from_db
from his.api.doctor_plan import enqueue_sales_orders
from frappe.utils import get_datetime, get_link_to_form, getdate, now_datetime, today

class DischargeSummary(Document):
    def on_submit(self):
        if self.emergency_triage:
            emergency_doc = frappe.get_doc("Emergency Triage", self.emergency_triage)
            emergency_doc.status = "Discharged"
            emergency_doc.save()
        else:
            patient_clearance(self.patient , self.ref_practitioner , self.inpatient_record)
            patient_doc = frappe.get_doc("Patient", self.patient)
            if frappe.db.exists("Inpatient Record" , frappe.db.get_value("Inpatient Record",{"patient": self.patient}, "name")):
                inpatient_record = frappe.get_doc("Inpatient Record" , frappe.db.get_value("Inpatient Record",{"patient": self.patient}, "name"))
                # Get check-out time
                check_out = now_datetime()  
                hours_difference = 0
                for bed in inpatient_record.inpatient_occupancies:
                    if bed.left == 0:
                        # Convert check_in to a datetime object if it's a string
                        if isinstance(bed.check_in, str):
                            check_in_time = datetime.strptime(bed.check_in, "%Y-%m-%d %H:%M:%S.%f")
                        else:
                            check_in_time = bed.check_in 

                        # Calculate the difference
                        time_difference = check_out - check_in_time

                        # Convert the difference to hours
                        hours_difference = round(time_difference.total_seconds() / 3600)

                room = frappe.get_doc("Healthcare Service Unit Type" , inpatient_record.room)
                if inpatient_record.status == "Admitted":
                    if inpatient_record.type == "Day Care":
                        if patient_doc.insurance_policy:
                            policy = frappe.get_doc("Insurance Policy", patient_doc.insurance_policy) 
                            sales_doc = frappe.get_doc({
                                "doctype" : "Sales Invoice",
                                "patient" : patient_doc.name,
                                "patient_name" : patient_doc.patient_name,
                                "customer" : patient_doc.customer,
                                "ref_practitioner" : self.ref_practitioner,
                                "source_order": "IPD",
                                "so_type": "Cashiers",
                                "cost_center": "Main - HH",
                                "is_pos" : 0,
                                "posting_date" : frappe.utils.getdate(),
                                "insurance_coverage_amount": ((room.rate * hours_difference) * policy.coverage_limits) / 100,
                                "payable_amount": (room.rate * hours_difference) - (((room.rate * hours_difference) * policy.coverage_limits) / 100),
                                "items": [{
                                        "item_code": inpatient_record.room,
                                        "item_name": inpatient_record.room,
                                        "qty": hours_difference,
                                        "rate": room.rate,				
                                        "doctype": "Sales Invoice Item"
                                }],
                        
                            })
                            sales_doc.insert(ignore_permissions=1)
                            sales_doc.save()
                            sales_doc.submit()
                            frappe.db.set_value("Discharge Summary", self.name, "reference_invoice", sales_doc.name)
                        else:
                            sales_doc = frappe.get_doc({
                                "doctype" : "Sales Invoice",
                                "patient" : patient_doc.name,
                                "patient_name" : patient_doc.patient_name,
                                "customer" : patient_doc.customer,
                                "ref_practitioner" : self.ref_practitioner,
                                "source_order": "IPD",
                                "so_type": "Cashiers",
                                "cost_center": "Main - HH",
                                "is_pos" : 0,
                                "posting_date" : frappe.utils.getdate(),
                                "items": [{
                                        "item_code": inpatient_record.room,
                                        "item_name": inpatient_record.room,
                                        "qty": hours_difference,
                                        "rate": room.rate,				
                                        "doctype": "Sales Invoice Item"
                                }],
                            
                            })
                            
    
                            sales_doc.insert(ignore_permissions=1)
                            sales_doc.save()
                            sales_doc.submit()
                            frappe.db.set_value("Discharge Summary", self.name, "reference_invoice", sales_doc.name)
                        # frappe.errprint(sales_doc.name)
                        # frappe.throw("Stop")
                        
                        
                    inpatient_record.status = "Discharge Scheduled"
                    check_out_inpatient(inpatient_record)
                    inpatient_record.save()
                    frappe.db.commit()
                
			
			# doc.sales_invoice=sales_doc.name
			# doc.save()
                
                
    def before_validate(self):
        # frappe.msgprint("discharge order")
        set_so_values_from_db(self)
    def on_update(self):
        enqueue_sales_orders(self)
        event = "new_msg"
        frappe.publish_realtime(event)
    def on_update_after_submit(self):
        enqueue_sales_orders(self)
    
    def on_cancel(self):
        if frappe.db.exists("Inpatient Record" , self.inpatient_record):
            inpatient_record = frappe.get_doc("Inpatient Record" , self.inpatient_record)
            if inpatient_record.status == "Discharge Scheduled":
                inpatient_record.status = "Admitted"
                cancel_check_out_inpatient(inpatient_record)
                inpatient_record.save()
                if self.reference_invoice:
                    sales_doc = frappe.get_doc("Sales Invoice", self.reference_invoice)
                    if sales_doc.reference_journal:
                        journal_doc = frappe.get_doc("Journal Entry", sales_doc.reference_journal)
                        journal_doc.cancel()
                    sales_doc.cancel()
                    frappe.db.set_value("Discharge Summary", self.name, "reference_invoice", "")

def check_out_inpatient(inpatient_record):
    if inpatient_record.inpatient_occupancies:
        for inpatient_occupancy in inpatient_record.inpatient_occupancies:
            if inpatient_occupancy.left != 1:
            
                frappe.db.set_value(
                    "Healthcare Service Unit", inpatient_occupancy.service_unit, "occupancy_status", "Discharge Ordered"
                )

def cancel_check_out_inpatient(inpatient_record):
    if inpatient_record.inpatient_occupancies:
        for inpatient_occupancy in inpatient_record.inpatient_occupancies:
            if inpatient_occupancy.left == 1:
            
                frappe.db.set_value(
                    "Healthcare Service Unit", inpatient_occupancy.service_unit, "occupancy_status", "Occupied"
                )


@frappe.whitelist()
def cancel_schedule(inpatient_record):
    inpatient_record_name = inpatient_record  # keep the original string name

    if frappe.db.exists("Inpatient Record", inpatient_record_name):
        inpatient_doc = frappe.get_doc("Inpatient Record", inpatient_record_name)
        inpatient_doc.status = "Admitted"
        inpatient_doc.save()

        if frappe.db.exists("Discharge And Clearance", {"inpatient_record": inpatient_record_name}):
            clearance_doc = frappe.get_doc("Discharge And Clearance", {"inpatient_record": inpatient_record_name})
            clearance_doc.delete()

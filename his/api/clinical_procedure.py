# Copyright (c) 2021, Rasiin and contributors
# For license information, please see license.txt
import frappe
from healthcare.healthcare.doctype.clinical_procedure.clinical_procedure import ClinicalProcedure
from his.his.doctype.aneasthesia_sheet.aneasthesia_sheet import transfer
class CustomClinicalProcedure(ClinicalProcedure):
		@frappe.whitelist()
		def complete_procedure(self):
			if self.ot_schedule:
				ot_doc = frappe.get_doc("OT Schedule" , self.ot_schedule)
				ot_doc.status = "Closed"
				ot_doc.save()
				
			transfer(self.service_unit ,  self.patient , self.procedure_template ,self.practitioner)
			if self.consumable_items:
				items = []
				for item in self.consumable_items:
						items.append({
							"item_code" : item.item_code,
							"qty" : item.qty,
							
						})
				frappe.errprint(items)
				stock_ent = frappe.get_doc({
					"doctype" : "Stock Entry",
					"posting_date" : frappe.utils.nowdate(),
					"stock_entry_type": "Material Issue",
					"company" : self.company,
					"from_warehouse": self.source_warehouse,
					"items" : items,
					})
				stock_ent.insert(ignore_permissions = True)
				stock_ent.submit()
				# self.db_set("status", "Completed")
				# return stock_ent
			
			if self.procedure_items:
				pro_items = []
				for item in self.procedure_items:
						pro_items.append({
							"item_code" : item.item_code,
							"qty" : item.qty
						})
				customer_to = frappe.db.get_value("Patient", self.patient, "customer")
				sales_doc = frappe.get_doc({
					"doctype" : "Sales Invoice",
					"posting_date" : frappe.utils.nowdate(),
					"customer": customer_to,
					"patient" : self.patient,
					"is_pos" : 0,
					"items" : pro_items,
					})
				sales_doc.insert(ignore_permissions = True)
				sales_doc.submit()
				self.db_set("status", "Completed")
				# return sales_doc
			if self.consume_stock and self.items:
				stock_entry = make_stock_entry(self)

			if self.items:
				consumable_total_amount = 0
				consumption_details = False
				customer = frappe.db.get_value("Patient", self.patient, "customer")
				if customer:
					for item in self.items:
						if item.invoice_separately_as_consumables:
							price_list, price_list_currency = frappe.db.get_values(
								"Price List", {"selling": 1}, ["name", "currency"]
							)[0]
							args = {
								"doctype": "Sales Invoice",
								"item_code": item.item_code,
								"company": self.company,
								"warehouse": self.warehouse,
								"customer": customer,
								"selling_price_list": price_list,
								"price_list_currency": price_list_currency,
								"plc_conversion_rate": 1.0,
								"conversion_rate": 1.0,
							}
							item_details = get_item_details(args)
							item_price = item_details.price_list_rate * item.qty
							item_consumption_details = (
								item_details.item_name + " " + str(item.qty) + " " + item.uom + " " + str(item_price)
							)
							consumable_total_amount += item_price
							if not consumption_details:
								consumption_details = _("Clinical Procedure ({0}):").format(self.name)
							consumption_details += "\n\t" + item_consumption_details

					if consumable_total_amount > 0:
						frappe.db.set_value(
							"Clinical Procedure", self.name, "consumable_total_amount", consumable_total_amount
						)
						frappe.db.set_value(
							"Clinical Procedure", self.name, "consumption_details", consumption_details
						)
				else:
					frappe.throw(
						_("Please set Customer in Patient {0}").format(frappe.bold(self.patient)),
						title=_("Customer Not Found"),
					)

			self.db_set("status", "Completed")
			self.db_set("end_time",frappe.utils.now())
			type = frappe.db.get_value("Healthcare Service Unit", self.service_unit, "service_unit_type")
			frappe.db.set_value("Healthcare Service Unit Type", type, "patient", "")
			frappe.db.set_value("Healthcare Service Unit Type", type, "patient_name", "")
			frappe.db.set_value("Healthcare Service Unit", self.service_unit, "patient", "")
			
			
			# post op nursing tasks
			if self.procedure_template:
				self.create_nursing_tasks()

			if self.consume_stock and self.items:
				return stock_entry



@frappe.whitelist()	
def clinical_pro_comm(doc , method = None):
		his_settings = frappe.get_doc("HIS Settings", "HIS Settings")
		if his_settings.allow_comm_doc:
			# if doc.ref_practitioner:
			# 	hpr = frappe.get_doc("Healthcare Practitioner" , doc.ref_practitioner)
			# 	if not hpr.employee:
			# 		return
			# 	if hpr.commission_configuration:
			# 		total_rate = 0
			# 		for item in doc.items:
						
			# 			item_commison = frappe.get_doc("Item" , item.item_code)
			# 			if item_commison.is_commissionable:
			# 				for comm_data in hpr.commission_configuration:
								
			# 					if item_commison.commission ==  comm_data.commission_configuration:
			# 						total_rate += (comm_data.percentage/100)* item.net_rate
			if doc.ref_practitioner:
				item_com=[]
				hpr = frappe.get_doc("Healthcare Practitioner" , doc.ref_practitioner)
				if hpr.commission:
					total_rate = 0
					for item in doc.items:
						

						for comm_data in hpr.commission:
							if item.item_group ==  comm_data.item_group:
								total_rate += (comm_data.percent/100)* item.net_rate
								
								item_com.append({
									"item": item.item_code,
									"item_group": item.item_group,
									"net_rate": -item.net_rate if doc.is_return else item.net_rate,
									"commission": -(comm_data.percent / 100) * item.net_rate if doc.is_return else (comm_data.percent / 100) * item.net_rate,
									"invoice": doc.name,
								})


					if total_rate == 0:
						remarks=''
						pass
					else:
						if not doc.is_return:
							account = [
								{
								"account":his_settings.doctor_exp_account,
								"debit_in_account_currency":total_rate,
								"source_order" : doc.source_order,
								},
								{
								"account": his_settings.doctor_commission_account,
								"party_type" : "Employee",
								"party": hpr.employee,
								"credit_in_account_currency":total_rate,
								"source_order" : doc.source_order,
								},
								]
							remarks= 'Doctor Commission'
						elif doc.is_return:
							account = [
								{
								"account":his_settings.doctor_exp_account,
								# "debit_in_account_currency":total_rate,
								"credit_in_account_currency":total_rate,
								"source_order" : doc.source_order,
								},
								{
								"account": his_settings.doctor_commission_account,
								"party_type" : "Employee",
								"party": hpr.employee,
								"debit_in_account_currency":total_rate,
								# "credit_in_account_currency":total_rate,
								"source_order" : doc.source_order,
								},
								]
							remarks= 'Refunded Doctor Commission'

						frappe.errprint(hpr)
						journal = frappe.get_doc({
										'doctype': 'Journal Entry',
										'voucher_type': 'Journal Entry',
										"posting_date" : doc.posting_date,
										"user_remark": remarks,
										"accounts": account,
										"sales_invoice": doc.name,
										"commission_reference": item_com,
										"practitioner": doc.ref_practitioner
										
										})
						journal.insert(ignore_permissions = True)
						# journal.submit()
						doc.journal_entry = journal.name
						# jename = frappe.db.get_value("Journal Entry", {'sales_invoice':doc.name, }, "name")
						# doc.journal_entry = jename
						doc.save()
						# "Commisions Reference": item_commison

@frappe.whitelist()
def ot_schedule(doc , method = None):
	service_unit = frappe.db.get_value("Healthcare Service Unit",{"service_unit_type":service_unit_type},"healthcare_service_unit_name")
	if service_unit:
		return service_unit
		frappe.db.set_value("Healthcare Service Unit", service_unit, "occupancy_status", "Occupied")
	# for item in doc.items:
	# 		if item.item_group == "OT":
	# 			# template = frappe.get_doc("Clinical Procedure Template" , item.item_code)
	# 			papp = frappe.get_doc({
	# 				'doctype': 'OT Schedule',
	# 				'patient': doc.patient,
	# 				"appointment_date" : doc.posting_date,
	# 				"appointment_time": doc.posting_time,
	# 				"company":frappe.defaults.get_user_default("company"),
	# 				"practitioner": doc.ref_practitioner,
	# 				"procedure_template": item.item_code,
	# 				"duration": 15,
	# 				})
	# 			papp.insert(ignore_permissions = True)
	# 			papp.save()

@frappe.whitelist()
def aneasthesia_sheet(docname,patient ,procedure_template,operative_doctor, method = None):
	papp = frappe.get_doc({
		'doctype': 'Aneasthesia Sheet',
		'ot_schedule': docname,
		'patient': patient,
		"clinical_procedure" : procedure_template,
		"operative_doctor":operative_doctor,
		"date": frappe.utils.nowdate()
		})
	# frappe.msgprint(str(docname))
	papp.insert(ignore_permissions = True)

	frappe.db.set_value("OT Schedule" , docname, "status", "In Progress")
	# papp.save()



# @frappe.whitelist()
def make_procedures(doc, method=None):
	for i in doc.items:
		if i.item_group == "Procedures" or i.item_group == "E.R":
			# frappe.errprint(doc.patient)
			pro = frappe.get_doc({
			'doctype': 'Procedures',
			
			'patient': doc.patient,
			'procedure': i.item_code,
			'practitioner' : doc.ref_practitioner,
			'reff_invoice' : doc.name,
			
			})
			# frappe.msgprint("OK")
			pro.insert(ignore_permissions=True)

@frappe.whitelist()
def make_anethesia(doc, method=None):
	recovery= frappe.get_doc({
		'doctype': 'Recovery',
		'patient': doc.patient,
		'procedure_template': doc.procedure_template,
		'practitioner' : doc.practitioner
		
		
		})
	recovery.insert(ignore_permissions = True)
	# frappe.msgprint("Transfered to Recovery")
	# ot_doc = frappe.get_doc("OT Schedule" , doc.ot_schedule)
	# if ot_doc:
	# 	ot_doc.status = "Closed"
	# 	ot_doc.save()




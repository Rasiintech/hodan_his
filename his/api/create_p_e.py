import frappe
from his.api.inpatient_record import clear_patient
from erpnext.accounts.utils import get_balance_on
from erpnext.stock.get_item_details import get_pos_profile
@frappe.whitelist()
def payment(doc_name ,dt):
	pay = frappe.get_doc(dt , doc_name)
	pos_profile = get_pos_profile(pay.company)
	mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
	default_account = frappe.db.get_value('Mode of Payment Account', {"parent": mode_of_payment},  'default_account')
  
	
	references = []
	if pay.references:
		for i in pay.references:
			references.append({"reference_doctype": i.reference_doctype, "reference_name": i.reference_name, "total_amount": i.total_amount, "outstanding_amount": i.outstanding_amount, "allocated_amount": i.allocated_amount})
	
	payment_entry = frappe.get_doc({
		"doctype" : "Payment Entry",
		"payment_type" : pay.payment_type,
		"posting_date" : pay.posting_date,
		"company" : pay.company,
		"party_type": pay.party_type,
		"party" : pay.party,
		"paid_from" : pay.paid_from,
		"paid_to": default_account,
		"received_amount": pay.received_amount,
		"paid_amount": pay.paid_amount,
		"voucher_no" : pay.name,
		"source_order" : "OPD"
		#"references" : references,
	   
	})
   
	payment_entry.save()
	payment_entry.submit()
	frappe.msgprint('Billed successfully')
	return payment_entry
	# cash_sales.sales_invoice = sales_doc.name
	# cash_sales.save()
	

@frappe.whitelist()
def payment_re(party , inpatient_record, paid_amount, posting_date, company, discount = 0, cost_center = 0, invoices = [] ,remark = "" ):
	pos_profile = get_pos_profile(company)
	mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
	default_account = frappe.db.get_value('Mode of Payment Account', {"parent": mode_of_payment},  'default_account')
	company_details = frappe.get_doc("Company" ,company)
 
	
	party_type = "Customer"
	payment_type = "Receive"
	
	references = []
	# if party_details:
	#     for i in party_details:
	#         references.append({"reference_doctype": i.voucher_type, "reference_name": i.voucher_no, "total_amount": i.invoice_amount, "outstanding_amount": i["outstanding_amount"], "allocated_amount": i.allocated_amount})
	references = invoices

	deductions = []
	discount = float(discount)
	if discount:
		# frappe.errprint(type(discount))
		deductions.append({
			"account": "Discount - " + frappe.db.get_value("Company", frappe.defaults.get_user_default("company"), "abbr"),
			"cost_center": frappe.db.get_value("Company", frappe.defaults.get_user_default("company"), "cost_center"),
			"amount" : discount

		})
	
	payment_entry = frappe.get_doc({
		"doctype" : "Payment Entry",
		"payment_type" : payment_type,
		"posting_date" : posting_date,
		"company" : company,
		"party_type": party_type,
		"party" : party,
		"paid_from" : company_details.default_receivable_account,
		"paid_to": default_account,
		"received_amount": float(paid_amount),
		"paid_amount": float(paid_amount),
		"source_order" : "OPD",
		"deductions" : deductions,
		"references" : references,
		"custom_remarks" : 1,
		"cost_center" : cost_center
	   
	})
   
	payment_entry.save()
	payment_entry.submit()
	frappe.msgprint('Recieved successfully')
	if inpatient_record:
		patient_balance = get_balance_on(company = company, party_type = party_type,party = party, date = posting_date)
		if not patient_balance:
			clear_patient(inpatient_record)
	return payment_entry
 

@frappe.whitelist()
def create_payment_entry(party, paid_amount):
	his_settings = frappe.get_doc("HIS Settings", "HIS Settings")
	debtor_account = ""
	if his_settings.debtors_account:
		debtor_account = his_settings.debtors_account

	pos_profile = get_pos_profile(frappe.defaults.get_user_default("company"))
	mode_of_payment = frappe.db.get_value('POS Payment Method', {"parent": pos_profile.name},  'mode_of_payment')
	default_account = frappe.db.get_value('Mode of Payment Account', {"parent": mode_of_payment},  'default_account')

	payment = frappe.new_doc("Payment Entry")
	payment.party_type = "Customer"
	payment.paid_from = frappe.db.get_value("Party Account", {"parent": party}, "account") or debtor_account
	payment.party_name = frappe.db.get_value("Customer", party, "customer_name")
	payment.party = party 
	payment.paid_amount = paid_amount 
	payment.received_amount = paid_amount
	payment.paid_from_account_currency ="USD"
	# payment.mode_of_payment = mode_of_payment
	payment.paid_to =default_account
	payment.paid_to_account_currency ="USD"


	return payment
	

# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import timedelta , date
from frappe.utils import getdate


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)[0]
	return columns, data

def get_data(filters):
	cash_bank_acc = ('Cash' , 'Bank')
	cash_accounts =  frappe.db.sql_list(f""" select name from tabAccount  where account_type in {cash_bank_acc} and is_group = 0 and root_type = "Asset" """)
	daily_cash = []
	account_names = []
	
	
	for acc in cash_accounts:
		daily = {}
		daily['sales'] = 0
		daily['rec'] = 0
		daily['tran_to'] = 0
		daily['pay'] = 0
		daily['expense'] = 0
		daily['sales'] = 0
		daily['return'] = 0
		daily['tran_from'] = 0
		daily['balance'] = 0
		for date in daterange(getdate(filters.from_date) , getdate(filters.to_date)):
			
			
				
		
		
			
			report_gl = frappe.get_doc("Report", "General Ledger")

			report_gl_filters = {
					"company" :frappe.defaults.get_user_default("company"),
			
					"from_date": frappe.utils.getdate(date),
					"to_date": frappe.utils.getdate(date),
					"account" : [acc]
			
				}
			
			columns_gl, data_gl = report_gl.get_data(
						limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
					)
			
			# {
		
			# "sales" : 0,
			# "rec" : 0,
			# "tran_to" : 0,
			# "pay" : 0,
			# "expense" : 0,
			# "return" : 0,
			# "tran_from" : 0
			# }
			daily["account"] = acc
			for d in data_gl:
				
				if d.posting_date:
					daily['balance'] += d.balance
					if d.voucher_type == "Sales Invoice":
						daily['sales'] += d.debit
						daily['return'] += d.credit
					if d.voucher_type == "Payment Entry":
						daily['rec'] += d.debit
						daily['pay'] += d.credit
					
					if d.voucher_type == "Journal Entry":
						daily['tran_to'] += d.debit
						root_type , type= frappe.db.get_value("Account" , d.against , ["root_type" , "account_type"])
						if root_type == "Expense":
							daily['expense'] += d.credit
						if type == "Cash" or "Bank":
							daily['tran_from'] += d.credit

		daily_cash.append(daily)
		frappe.errprint(daily)
			
	return daily_cash , account_names





def daterange(start_date, end_date):
		for n in range(int ((end_date - start_date).days)+1):
			yield start_date + timedelta(n)

def get_columns(filters):
	columns = [
			{
				"label": "Account",
				"fieldname": "account",
				"fieldtype": "Data",
				
				"width": 120,
			}
	]
	cash_bank_acc = ('Cash' , 'Bank')
	income_accounts = frappe.db.sql_list(f""" select name from tabAccount where account_type in {cash_bank_acc} and is_group = 0 """)

	report_cols = get_data(filters)[1]
	cols = [
		{	
		"label" : "Cash Sales", "fieldname" : "sales"
	 } ,
	 	{	
		"label" : "Receipt", "fieldname" : "rec"
	 } ,
	 {	
		"label" : "Transfred in", "fieldname" : "tran_to"
	 } ,
	 	{	
		"label" : "Payment", "fieldname" : "pay"
	 } ,

	 	{	
		"label" : "Expense", "fieldname" : "expense"
	 } ,
	  	{	
		"label" : "Refund", "fieldname" : "return"
	 } 
	 ,
	 	{	
		"label" : "Transfred", "fieldname" : "tran_from"
	 } 
			


			
			

	]

	for col in cols:
		
		columns.append(
				{
					"label": col['label'],
					"fieldname": frappe.scrub(col['fieldname']),
					"fieldtype": "Currency",
					
					"width": 220,
				}
			)
	columns.append(
		{
					"label": "Balance",
					"fieldname": "balance",
					"fieldtype": "Currency",
					
					"width": 100,
				}
	)
	return columns
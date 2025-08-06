# Copyright (c) 2022, Anfac Tech and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	
	return get_columns(), get_data(filters)

def get_data(filters):
	
	_from ,to  = filters.get('from_date'), filters.get('to') 
	
	data = frappe.db.sql(f"""
	select 
	posting_date,
	ref_practitioner,
	name, 
	customer_name ,
	total,
	
	discount_amount,
 	net_total,
	
	owner,
	comment

from `tabSales Invoice`
where posting_date between "{_from}" and "{to}"  and docstatus = 1
 ;""")
	return data
def get_columns():
	return [

		"Date: Date:120",
		"Doctor:Data:200",
		"Invoice No:Link/Sales Invoice:220",
		"Customer Name:Link/Customer:200", 
		"Total:Currency:110",
		"Discount:Currency:110",
		"Net Amount:Currency:110",
		"User:Link/User:220",
		"Reason:Data:150"

	
		
	]


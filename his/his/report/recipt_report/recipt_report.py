# Copyright (c) 2022, Anfac Tech and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	
	return get_columns(), get_data(filters)
def get_data(filters):
	
	_from ,to , center = filters.get('from_date'), filters.get('to')  , filters.get('center')
	# if sts == "Unpaid":
	# 	cond += f'and is_pos = 0'
	# elif sts == "Paid":
	# 	cond += f'and is_pos = 1 ' 
	# frappe.msgprint(cond)
	# sel_cent =""
	# if center == "Tahliil 2 - TTC":
	# 	sel_cent = "and cost_center = 'Tahliil 2 - TTC' "
	# else:
	# 	sel_cent = "and cost_center is null "
	# if center:
	# 	sel_cent += f"and cost_center = '{center}'"
	
	data = frappe.db.sql(f"""
	select 
	name, 
	posting_date,
	party ,
	party_name ,
	cost_center,
	paid_amount  

from `tabPayment Entry` 
where posting_date between "{_from}" and "{to}" and party_type = "Customer"  and docstatus = 1
 ;""")
	return data
def get_columns():
	return [
		
		"Voucher:Link/Payment Entry:220",
		"Date: Date:120",
		"PID:Link/Customer:200", 
		"Patient Name:Data:250", 
		"Cost Center:Data:200", 
		"Paid Amount:Currency:110",
	
		
	]


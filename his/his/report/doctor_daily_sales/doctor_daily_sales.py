# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate
import pandas as pd
from frappe import _
def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data

@frappe.whitelist()
def get_data(filters):
	source_con = ''
	curr_date = getdate()
	source_con = 'and `tabSales Invoice`.source_order != "IPD" '
	if filters.source == "IPD":
		source_con = 'and `tabSales Invoice`.source_order = "IPD"'

	# Your data
	data = frappe.db.sql(f"""
			select
				`tabSales Invoice`.patient,
				`tabSales Invoice`.ref_practitioner,
				`tabSales Invoice Item`.parenttype, `tabSales Invoice Item`.parent,
				`tabSales Invoice`.posting_date, `tabSales Invoice`.posting_time,
				`tabSales Invoice`.project, `tabSales Invoice`.update_stock,
				`tabSales Invoice`.customer, `tabSales Invoice`.customer_group,
				`tabSales Invoice`.territory, `tabSales Invoice Item`.item_code,
				`tabSales Invoice Item`.item_name, `tabSales Invoice Item`.description,
				`tabSales Invoice Item`.warehouse, `tabSales Invoice Item`.item_group,
				`tabSales Invoice Item`.brand, `tabSales Invoice Item`.so_detail,
				`tabSales Invoice Item`.sales_order, `tabSales Invoice Item`.dn_detail,
				`tabSales Invoice Item`.delivery_note, `tabSales Invoice Item`.stock_qty as qty,
				`tabSales Invoice Item`.base_net_rate, `tabSales Invoice Item`.base_net_amount,
				`tabSales Invoice Item`.name as "item_row", `tabSales Invoice`.is_return,
				`tabSales Invoice Item`.cost_center
		
			from
				`tabSales Invoice` inner join `tabSales Invoice Item`
					on `tabSales Invoice Item`.parent = `tabSales Invoice`.name
				join `tabItem` item on item.name = `tabSales Invoice Item`.item_code
		
			where
				`tabSales Invoice`.docstatus=1 and `tabSales Invoice`.is_opening!='Yes' 
				and `tabSales Invoice`.posting_date between "{filters.from_date}"  and "{filters.to_date}"
				{source_con}
		
			order by
				`tabSales Invoice`.posting_date desc """ , as_dict =1 )

	# Create a DataFrame from the data
	if data:
		my_d = [{}]
		for d in data:
			my_d.append(d)
		df = pd.DataFrame(my_d)
		
		# Group by "ref_practitioner" and "item_group" and calculate sum
		result_df = df.groupby(['ref_practitioner', 'item_group']).agg({
			'patient': 'count',
			'base_net_amount': 'sum'
		}).reset_index()

		# Rename the columns
		# result_df.rename(columns={'qty': 'patient_qty'}, inplace=True)

		# Convert the result to a list of dictionaries
		result_list = result_df.to_dict(orient='records')

		# Print the result
		return result_list
	return []


def get_columns():
	columns = [
			{
				"label": _("Doctor"),
				"fieldname": "ref_practitioner",
				"fieldtype": "Link",
				"options": "Healthcare Practitioner",
				"width": 320,
			},
		{
				"label": _("Group"),
				"fieldname": "item_group",
				"fieldtype": "Link",
				"options": "Item Group",
				"width": 220,
			},
			 {
				"label": _("Count"),
				"fieldname": "patient",
				"fieldtype": "Int",
				"width": 100,
			},
			 {
				"label": _("REVENUE"),
				"fieldname": "base_net_amount",
				"fieldtype": "Currency",
				"width": 200,
			},
	]
	return columns
	

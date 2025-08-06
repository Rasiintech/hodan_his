# Copyright (c) 2023, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import timedelta , date
from frappe.utils import getdate

def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	frappe.errprint(columns)
	return columns, data


def get_columns(filters):
	columns = [
			{
						"label": "Date",
						"fieldname": "posting_date",
						"fieldtype": "Date",
						
						"width": 100,
					}
			
		
	]
	income_accounts = frappe.db.sql_list(""" select name from tabAccount """)

	report_cols = get_report_columns(filters)
	for col in report_cols:
		if col.label in  income_accounts:
			columns.append(
					{
						"label": col.label,
						"fieldname": frappe.scrub(col.fieldname),
						"fieldtype": col.fieldtype,
						"options": col.options,
						"width": 120,
					}
				)
	
	columns.append(
			{
			"label": _("Net Total"),
			"fieldname": "net_total",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		}
	)
	columns.append(	
		{
			"label": _("Cash"),
			"fieldname": "cash",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		})
	columns.append(	
		{
			"label": _("Credit"),
			"fieldname": "outstanding_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		})
	
	return columns

def get_data(filter):
	daily_sales = []
	for date in daterange(getdate(filter.from_date) , getdate(filter.to_date)):

		report_gl = frappe.get_doc("Report", "Sales Register")

		report_gl_filters = {
		
		
		
		
				"from_date": frappe.utils.getdate(date),
				"to_date": frappe.utils.getdate(date),
		
			}
		
		columns_gl, data_gl = report_gl.get_data(
					limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
				) 
		d = data_gl[-1]
		if d.outstanding_amount:
			d['posting_date'] = date
			d['cash'] = d.net_total - d.outstanding_amount
		daily_sales.append(d)
	return daily_sales


def daterange(start_date, end_date):
		for n in range(int ((end_date - start_date).days)+1):
			yield start_date + timedelta(n)
def get_report_columns(filters):
	report_gl = frappe.get_doc("Report", "Sales Register")

	report_gl_filters = {
	
	
	
	
			"from_date": frappe.utils.getdate(),
			"to_date": frappe.utils.getdate(),
	
		}
	
	columns_gl, data_gl = report_gl.get_data(
				limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
			) 
	return columns_gl 
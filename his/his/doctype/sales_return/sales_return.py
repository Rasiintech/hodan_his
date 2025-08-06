# Copyright (c) 2022, Anfac Tech and contributors
# For license information, please see license.txt

import frappe
from his.api.create_inv import create_inv
from frappe.model.document import Document

class SalesReturn(Document):
    def on_submit(self):
        # retail_setup = frappe.get_doc("Retail Setup", "Retail Setup")
        # if retail_setup.allow_retail:
        # 	if self.items:
        # 		for item in self.items:
        # 			item_doc = frappe.get_doc("Item" , item.item_code)
        # 			if item.streps and item_doc.strep:
                        
        # 				item_doc.uoms[1].conversion_factor = 1/float(item.streps)
        # 				item_doc.uoms[1].no_of_streps = float(item.streps)
        # 				item_doc.save() 
        # frappe.msgprint("ok")
        sales_doc = create_inv(self.name ,dt = 'Sales Return' , is_sales_return = True , mode_of_payment = self.mode_of_payment)
        self.sales_invoice = sales_doc.name
        self.save()
    def on_cancel(self):
        if self.sales_invoice:
            sales_doc = frappe.get_doc("Sales Invoice" , self.sales_invoice)
            sales_doc.cancel()

@frappe.whitelist()
def get_billed_items(patient, from_date, to_date):
    list_of_bills = frappe.db.get_list("Sales Invoice",
                                        filters={"patient": patient,
                                                 "docstatus": 1,
                                                 "is_return": 0,
                                                 "posting_date": ['between', [from_date, to_date]]},
                                        pluck="name")

    items_of_bills = frappe.db.get_list("Sales Invoice Item",
                                         filters={"parent": ["in", list_of_bills]},
                                         fields="*")

    stock_items = []
    for item in items_of_bills:
        is_stock_item = frappe.db.get_value("Item", {"item_code": item.item_code},"is_stock_item")
        if is_stock_item:
            stock_items.append(item)

    return stock_items

    # list_of_bills = frappe.db.get_list("Sales Invoice" , filters = {"patient" : patient , "docstatus" : 1 , "is_return" :0 ,'posting_date': ['between', [from_date, to_date]]},pluck = "name")
    # items_of_bills = frappe.db.get_list("Sales Invoice Item" , filters = {"parent" : ['in', list_of_bills] } , fields= "*")
    # items = []
    # for item in items_of_bills:
    # 	if frappe.db.get_value("Item" , filters = {"item_code" : item.item_code } , "is_stock_item"):
    # 		items.append(item)

    # return items

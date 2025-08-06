# Copyright (c) 2022, Anfac and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form, getdate
from his.his.doctype.radiology.radiology import update_check_tests_stat

class LabResult(Document):
    def on_submit(self):
        event = "lab_result_update"
        frappe.publish_realtime(event)
        doc=self
        company = frappe.defaults.get_global_default("company")
        abbr = frappe.get_value("Company", company, "abbr")
        update_check_tests_stat(self)
        itms= []
        for i in self.normal_test_items:
            itms.append({
                "test_name" : i.lab_test_name,
                "result" : i.result_value
            })
            name=frappe.db.get_value("Lab Test preparion", {"test":i.lab_test_name }, "name")
            frappe.db.set_value("Lab Test preparion", name, "result" , i.result_value)  
            frappe.db.set_value("Lab Test preparion", name, "status" , 1)  
        items = []
        multiple_items=[]
        stock =''
        if doc.type == "Blood":
            for i in doc.normal_test_items:
                stock= frappe.get_doc("Lab Test Template",frappe.db.get_value("Lab Test Template", {"lab_test_name":i.lab_test_name }, 'name'))
                
                if stock.inventory:
                    for inv in stock.inventory:
                        items.append({
                            "item_code" : inv.item,
                            "qty" : inv.qty,
                            "s_warehouse" : m_i.warehouse,
                            "expense_account" : m_i.expense_account
                            
                    
                        })
               
                
        elif doc.type == "Group":
            # stock=frappe.db.get_value("Lab Test Template", {"lab_test_name":doc.template }, 'inventory')
            docname= frappe.db.get_value("Lab Test Template", {"lab_test_name":doc.template }, 'name')
            m_items = frappe.get_doc("Lab Test Template", docname)
            if m_items.inventory:
                for m_i in m_items.inventory:
                    items.append({
                        "item_code" : m_i.item,
                        "qty" : m_i.qty,
                        "s_warehouse" : m_i.warehouse,
                        "expense_account" : m_i.expense_account
                
                    })
            

            
        if items:
            mat_req = frappe.get_doc({
                "doctype" : "Stock Entry",
                "stock_entry_type" : "Material Issue",
                "posting_date" : frappe.utils.getdate(),
        # 		"schedule_date" : frappe.utils.getdate(),
                "items" : items
            })
        # frappe.errprint(items)
            mat_req.insert(ignore_permissions = 1, ignore_mandatory=1)
            mat_req.submit()
            frappe.msgprint("Stock Issued")


            
    def get_lab_tests_hor(self):
            test ={}
            for item in self.normal_test_items:
                
                # frappe.errprint(test)
                is_template = 0
                template = {}
                if item.test:
                    is_template = frappe.db.exists("Lab Test Template", item.test)
                    if is_template:
                        template = frappe.get_doc('Lab Test Template', item.test)
                # else:
                # 	is_template = frappe.db.exists("Lab Test Template", item.lab_test_name)
                # 	if is_template:
                # 		template = frappe.get_doc('Lab Test Template', item.lab_test_name)
                if template:
                    if template.department:
                        # template = frappe.get_doc('Lab Test Template', item.test)
                        
                        
                        if not f'{template.department}' in test:
                            test[f'{template.department}'] = [{'test':item.test , 'flag': item.flag, 'lab_event' : '', 'lab_test_name' : item.lab_test_name , 'result_value' : item.result_value , 'normal_range' :item.normal_range}]

                            if template.lab_test_template_type == "Compound":
                                # frappe.msgprint(template.name)
                                events = frappe.db.get_list('Normal Test Result',
                                    filters={
                                        'template': template.name,
                                        'parent' : self.name
                                    },
                                    fields=['lab_test_name', 'result_value' , 'normal_range'],
                                
                                )
                                # frappe.errprint(events)	
                                # lab_test_events= frappe.db.get_all("Normal Test Result", filters, or_filters, fields, order_by, group_by, start, page_length)
                                for event in events:
                                    
                                    test[f'{template.department}'].append({ "lab_event":'', 'flag': item.flag, 'lab_test_name' : event.lab_test_name ,  'normal_range' :event.normal_range , 'result_value' : event.result_value})
                            
                            
                            if template.lab_test_template_type == "Grouped":
                                events = frappe.db.get_list('Normal Test Result',
                                    filters={
                                        'template': template.name,
                                        'parent' : self.name
                                    },
                                    fields=['lab_test_name', 'result_value' , 'normal_range'],
                                
                                )
                                
                                # frappe.errprint(events)	
                                # lab_test_events= frappe.db.get_all("Normal Test Result", filters, or_filters, fields, order_by, group_by, start, page_length)
                                for event in events:
                                    test[f'{template.department}'].append({'test':'' , 'flag': item.flag, "lab_event":'', 'lab_test_name' : event.lab_test_name , 'result_value' : event.result_value , 'normal_range' :event.normal_range})
                    
                                    lab_events = frappe.db.get_list('Normal Test Result',
                                        filters={
                                            'template': event.lab_test_name,
                                            'parent' : self.name
                                        },
                                        
                                        fields=['lab_test_event', 'result_value' , 'normal_range'],
                                    
                                    )
                                    for eve in lab_events:

                                        test[f'{template.department}'].append({ 'lab_test_name' : '', 'flag': item.flag, 'lab_event' : eve.lab_test_event  ,  'normal_range' :eve.normal_range , 'result_value' : eve.result_value})

                        
                        else:
                            test[f'{template.department}'].append({'test':item.test ,"lab_event":'', 'flag': item.flag, 'lab_test_name' : '' , 'result_value' : item.result_value , 'normal_range' :item.normal_range})

                            if template.lab_test_template_type == "Compound":
                                # frappe.msgprint(template.name)
                                events = frappe.db.get_list('Normal Test Result',
                                    filters={
                                        'template': template.name,
                                        'parent' : self.name
                                    },
                                    fields=['lab_test_name', 'result_value' , 'normal_range'],
                                
                                )
                                # frappe.errprint(events)	
                                # lab_test_events= frappe.db.get_all("Normal Test Result", filters, or_filters, fields, order_by, group_by, start, page_length)
                                for event in events:
                                    
                                    test[f'{template.department}'].append({ "lab_event":'', 'flag': item.flag, 'lab_test_name' : event.lab_test_name ,  'normal_range' :event.normal_range , 'result_value' : event.result_value})
                            
                            
            # frappe.errprint(test)					
            return test


    def get_lab_tests(self):
        test ={}
        for item in self.normal_test_items:
            
            # frappe.errprint(test)
            is_template = 0
            template = {}
            if item.test:
                is_template = frappe.db.exists("Lab Test Template", item.test)
                if is_template:
                    template = frappe.get_doc('Lab Test Template', item.test)
            # else:
            # 	is_template = frappe.db.exists("Lab Test Template", item.lab_test_name)
            # 	if is_template:
            # 		template = frappe.get_doc('Lab Test Template', item.lab_test_name)
            if template:
                if template.department:
                    # template = frappe.get_doc('Lab Test Template', item.test)
                    # frappe.msgprint(template.name)
                    if not f'{template.department}' in test:
                        test[f'{template.department}'] = [{'test':item.test , 'flag': item.flag, 'lab_event' : '', 'lab_test_name' : item.lab_test_name , 'result_value' : item.result_value , 'normal_range' :item.normal_range}]

                        if template.lab_test_template_type == "Compound":
                            events = frappe.db.get_list('Normal Test Result',
                                filters={
                                    'template': template.name,
                                    'parent' : self.name
                                },
                                fields=['lab_test_name', 'result_value' , 'normal_range'],
                            
                            )
                            # frappe.errprint(events)	
                            # lab_test_events= frappe.db.get_all("Normal Test Result", filters, or_filters, fields, order_by, group_by, start, page_length)
                            for event in events:
                                test[f'{template.department}'].append({ "lab_event":'', 'flag': item.flag, 'lab_test_name' : event.lab_test_name ,  'normal_range' :event.normal_range , 'result_value' : event.result_value})
                        if template.lab_test_template_type == "Grouped":
                            events = frappe.db.get_list('Normal Test Result',
                                filters={
                                    'template': template.name,
                                    'parent' : self.name
                                },
                                fields=['lab_test_name', 'result_value' , 'normal_range'],
                            
                            )
                            
                            # frappe.errprint(events)	
                            # lab_test_events= frappe.db.get_all("Normal Test Result", filters, or_filters, fields, order_by, group_by, start, page_length)
                            for event in events:
                                test[f'{template.department}'].append({'test':'' , 'flag': item.flag, "lab_event":'', 'lab_test_name' : event.lab_test_name , 'result_value' : event.result_value , 'normal_range' :event.normal_range})
                
                                lab_events = frappe.db.get_list('Normal Test Result',
                                    filters={
                                        'template': event.lab_test_name,
                                        'parent' : self.name
                                    },
                                    
                                    fields=['lab_test_event', 'result_value' , 'normal_range'],
                                
                                )
                                for eve in lab_events:

                                    test[f'{template.department}'].append({ 'lab_test_name' : '', 'flag': item.flag, 'lab_event' : eve.lab_test_event  ,  'normal_range' :eve.normal_range , 'result_value' : eve.result_value})

                    
                    else:
                        test[f'{template.department}'].append({'test':item.lab_test_name ,"lab_event":'',  'flag': item.flag, 'lab_test_name' : '' , 'result_value' : item.result_value , 'normal_range' :item.normal_range})
                
        # frappe.errprint(test)					
        return test
        

    # def after_insert(self):
    # 	if self.prescription:
    # 		frappe.db.set_value("Lab Prescription", self.prescription, "lab_test_created", 1)
    # 		if frappe.db.get_value("Lab Prescription", self.prescription, "invoiced"):
    # 			self.invoiced = True
    # 	if self.template:
    # 		self.load_test_from_template()
    # 		self.reload()
    # def load_test_from_template(self):
    # 	lab_test = self
    # 	create_test_from_template(lab_test)
    # 	self.reload()




def create_test_from_template(lab_test):
    template = frappe.get_doc("Lab Test Template", lab_test.template)
    patient = frappe.get_doc("Patient", lab_test.patient)

    lab_test.lab_test_name = template.lab_test_name
    lab_test.result_date = getdate()
    lab_test.department = template.department
    lab_test.lab_test_group = template.lab_test_group
    lab_test.legend_print_position = template.legend_print_position
    lab_test.result_legend = template.result_legend
    lab_test.worksheet_instructions = template.worksheet_instructions

    # lab_test = create_sample_collection(lab_test, template, patient, None)
    lab_test = load_result_format(lab_test, template, None, None)



def load_result_format(lab_test, template, prescription, invoice):
    if template.lab_test_template_type == "Single":
        create_normals(template, lab_test)

    elif template.lab_test_template_type == "Compound":
        create_compounds(template, lab_test, False)

    elif template.lab_test_template_type == "Descriptive":
        create_descriptives(template, lab_test)

    elif template.lab_test_template_type == "Grouped":
        # Iterate for each template in the group and create one result for all.
        for lab_test_group in template.lab_test_groups:
            # Template_in_group = None
            if lab_test_group.lab_test_template:
                template_in_group = frappe.get_doc("Lab Test Template", lab_test_group.lab_test_template)
                if template_in_group:
                    if template_in_group.lab_test_template_type == "Single":
                        create_normals(template_in_group, lab_test)

                    elif template_in_group.lab_test_template_type == "Compound":
                        normal_heading = lab_test.append("normal_test_items")
                        normal_heading.lab_test_name = template_in_group.lab_test_name
                        normal_heading.require_result_value = 0
                        normal_heading.allow_blank = 1
                        normal_heading.template = template_in_group.name
                        create_compounds(template_in_group, lab_test, True)

                    elif template_in_group.lab_test_template_type == "Descriptive":
                        descriptive_heading = lab_test.append("descriptive_test_items")
                        descriptive_heading.lab_test_name = template_in_group.lab_test_name
                        descriptive_heading.require_result_value = 0
                        descriptive_heading.allow_blank = 1
                        descriptive_heading.template = template_in_group.name
                        create_descriptives(template_in_group, lab_test)

            else:  # Lab Test Group - Add New Line
                normal = lab_test.append("normal_test_items")
                normal.lab_test_name = lab_test_group.group_event
                normal.lab_test_uom = lab_test_group.group_test_uom
                normal.secondary_uom = lab_test_group.secondary_uom
                normal.conversion_factor = lab_test_group.conversion_factor
                normal.normal_range = lab_test_group.group_test_normal_range
                normal.allow_blank = lab_test_group.allow_blank
                normal.require_result_value = 1
                normal.template = template.name

    if template.lab_test_template_type != "No Result":
        if prescription:
            lab_test.prescription = prescription
            if invoice:
                frappe.db.set_value("Lab Prescription", prescription, "invoiced", True)
        lab_test.save(ignore_permissions=True)  # Insert the result
        return lab_test


def create_compounds(template, lab_test, is_group):
    lab_test.normal_toggle = 1
    for normal_test_template in template.normal_test_templates:
        normal = lab_test.append("normal_test_items")
        if is_group:
            normal.lab_test_event = normal_test_template.lab_test_event
        else:
            normal.lab_test_name = normal_test_template.lab_test_event

        normal.lab_test_uom = normal_test_template.lab_test_uom
        normal.secondary_uom = normal_test_template.secondary_uom
        normal.conversion_factor = normal_test_template.conversion_factor
        normal.normal_range = normal_test_template.normal_range
        normal.require_result_value = 1
        normal.allow_blank = normal_test_template.allow_blank
        normal.template = template.name




def create_normals(template, lab_test):
    lab_test.normal_toggle = 1
    normal = lab_test.append("normal_test_items")
    normal.lab_test_name = template.lab_test_name
    normal.lab_test_uom = template.lab_test_uom
    normal.secondary_uom = template.secondary_uom
    normal.conversion_factor = template.conversion_factor
    normal.normal_range = template.lab_test_normal_range
    normal.require_result_value = 1
    normal.allow_blank = 0
    normal.template = template.name


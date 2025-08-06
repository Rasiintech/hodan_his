import frappe
from frappe.utils import getdate
@frappe.whitelist()
def get_ordered(from_date , to_date):
    
    ordered_tests = frappe.db.sql(f"""

    select * from `tabSample Collection` where docstatus = 0
    and Date(creation) between '{from_date}' and '{to_date}'
    order by  modified desc
                                  
    """, as_dict = 1)
    
    # for d in ordered_tests:

    return ordered_tests



@frappe.whitelist()
def get_collected(from_date , to_date):
    collected_tests = frappe.db.sql(f"""

    select * from `tabSample Collection` where docstatus = 1
    and Date(creation) between '{from_date}' and '{to_date}'
    order by  modified desc
    """, as_dict = 1)
    return collected_tests



@frappe.whitelist()
def get_lab_result(from_date , to_date):
    lab_result = frappe.db.sql(f"""

    select * from `tabLab Result` where docstatus = 0
    and Date(creation) between '{from_date}' and '{to_date}'
    order by  modified desc

    """, as_dict = 1)
  
    
    for d in lab_result:
         sam_lis = []
         if not d.sample:
            normals = frappe.db.get_all('Normal Test Result', filters = {"parent" : d.name} ,pluck='name')
            for noraml in normals:
                normal_doc = frappe.get_doc("Normal Test Result" , noraml)
                

              
                if normal_doc.custom_sample and normal_doc.custom_sample not in sam_lis:
                    sam_lis.append(normal_doc.custom_sample)
                    if  d['sample']:
                        d['sample'] =  d['sample'] + str(normal_doc.custom_sample) + ","
                    else:
                        d['sample'] = str(normal_doc.custom_sample) + ","
    # frappe.errprint(sam_lis)
    return lab_result

@frappe.whitelist()
def completed(from_date , to_date):
    # frappe.msgprint(from_date , to_date)
    lab_result = frappe.db.sql(f"""

    select * from `tabLab Result` where docstatus = 1
    and Date(creation) between '{from_date}' and '{to_date}'
    order by  modified desc

    """, as_dict = 1)
  
    
    # for d in lab_result:
    #      sam_lis = []
    #      if not d.sample:
    #         normals = frappe.db.get_list('Normal Test Result', filters = {"parent" : d.name} ,pluck='name')
    #         for noraml in normals:
    #             normal_doc = frappe.get_doc("Normal Test Result" , noraml)
                

                
    #             if normal_doc.custom_sample and normal_doc.custom_sample not in sam_lis:
    #                 sam_lis.append(normal_doc.custom_sample)
                    
    #                 d['sample'] = d['sample'] +  normal_doc.custom_sample + ","
    # frappe.errprint(sam_lis)
    return lab_result
    




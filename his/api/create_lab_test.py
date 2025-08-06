import frappe
from his.api.tests_sts_check import create_tests_sts
@frappe.whitelist()
def create_lab_tests(doc , method = None):
    # lab_test = frappe.get_doc({
    # 'doctype': 'Lab Result',
    # 'patient': doc.patient
    # })
    # lab_test.insert()
    sam = frappe.get_doc('Sales Invoice', doc.reff_invoice)
    lab_test_itmes = []
    urine_lab_test_itmes = []
    hor_lab_test_itmes = []

    for item in sam.items:
        # if item.item_group == "Laboratory":
        if frappe.db.exists("Lab Test Template", {"item": item.item_code}, cache=True):
            template = frappe.get_doc("Lab Test Template" , {"item":item.item_code})
            # if template.department == "Hormones":

            # 	if template.lab_test_template_type == "Single":
            # 		hor_lab_test_itmes.append(
            # 				{
            # 					"test" : template.lab_test_name,
            # 					"lab_test_name": template.lab_test_name,
            # 					"lab_test_uom": template.lab_test_uom,
            # 					"secondary_uom": template.secondary_uom,
            # 					"conversion_factor": template.conversion_factor,
            # 					"normal_range": template.lab_test_normal_range,
            # 					"require_result_value": 1,
            # 					"allow_blank ":0
            # 				}
            # 			)

            # 	elif template.lab_test_template_type == "Compound":
            # 		hor_lab_test_itmes.append({

                        
                            
            # 				"test" : template.name

            # 		})
                
            # 		for normal_test_template in template.normal_test_templates:
            # 		# normal = {}
            # 		# if is_group:
            # 		# 	normal.lab_test_event = normal_test_template.lab_test_event
            # 			# else:
            # 			hor_lab_test_itmes.append({

                        
            # 				"lab_test_name": normal_test_template.lab_test_event,
                            

            # 				"lab_test_uom": normal_test_template.lab_test_uom,
            # 				"secondary_uom": normal_test_template.secondary_uom,
            # 				"conversion_factor": normal_test_template.conversion_factor,
            # 				"normal_range": normal_test_template.normal_range,
            # 				"require_result_value": 1,
            # 				"allow_blank": normal_test_template.allow_blank,
            # 				"template": template.name
            # 			})
            
            
            
            # else:
            if template.department:
                if template.lab_test_template_type == "Single":
                    lab_test_itmes.append(
                            {
                                "test" : template.lab_test_name,
                                "lab_test_name": template.lab_test_name,
                                "lab_test_uom": template.lab_test_uom,
                                "secondary_uom": template.secondary_uom,
                                "conversion_factor": template.conversion_factor,
                                "normal_range": template.lab_test_normal_range,
                                "require_result_value": 1,
                                "allow_blank ":0
                            }
                        )

                # elif template.lab_test_template_type == "Compound":
                # 	group_test = []
                # 	lab_test_itmes.append({

                        
                            
                # 			"test" : template.name

                # 	})
                    
                # 	for normal_test_template in template.normal_test_templates:
                # 		lab_test_itmes.append({

                        
                            
                # 			"test" : template.name

                # 	})
                # 		# normal = {}
                # 		# if is_group:
                # 		# 	normal.lab_test_event = normal_test_template.lab_test_event
                # 		# else:
                # 		lab_test_itmes.append({

                        
                # 			"lab_test_name": normal_test_template.lab_test_event,
                            

                # 			"lab_test_uom": normal_test_template.lab_test_uom,
                # 			"secondary_uom": normal_test_template.secondary_uom,
                # 			"conversion_factor": normal_test_template.conversion_factor,
                # 			"normal_range": normal_test_template.normal_range,
                # 			"require_result_value": 1,
                # 			"allow_blank": normal_test_template.allow_blank,
                # 			"template": template.name
                # 		})
                if template.lab_test_template_type == "Compound":
                    cbc_lab_test_itmes = []
                    # cbc_lab_test_itmes.append({
                            
                        
                    # 		"test" : template.name,
                        
                    # 		"template": template.name

                    # 		})
                    # if template.name == "Stool Examination":
                    
                    for normal_test_template in template.normal_test_templates:
                    # normal = {}
                    # if is_group:
                    # 	normal.lab_test_event = normal_test_template.lab_test_event
                        # else:

                        cbc_lab_test_itmes.append({

                        
                            "lab_test_event": normal_test_template.lab_test_event,
                            

                            "lab_test_uom": normal_test_template.lab_test_uom,
                            "secondary_uom": normal_test_template.secondary_uom,
                            "conversion_factor": normal_test_template.conversion_factor,
                            "normal_range": normal_test_template.normal_range,
                            "require_result_value": 1,
                            "allow_blank": normal_test_template.allow_blank,
                            "template": template.name
                        })

                    lab_test = frappe.get_doc({
                    'doctype': 'Lab Result',
                    'patient' : sam.patient,
                    'practitioner' : sam.ref_practitioner,
                    "invoice_no" : sam.name,
                    "lab_ref" : doc.lab_ref,
                    'normal_test_items' : cbc_lab_test_itmes,
                    "template" : template.name,
                    "lab_test_name" : template.name,
                    "type" : "Group",
                    "reff_collection": doc.name
                    
                    })
                    lab_test.insert()
                    event = "lab_resul_update"
                    frappe.publish_realtime(event)

                elif template.lab_test_template_type == "Grouped" : 
                    
            
                    
                    urine_lab_test_itmes = []
                    # if template.name == "Stool Examination":
                    
                    for normal_test_template in template.lab_test_groups:
                        # normal = {}
                        # if is_group:
                        # 	normal.lab_test_event = normal_test_template.lab_test_event
                        # else:
                        uom, normal_range = frappe.db.get_value("Lab Test Template" ,normal_test_template.lab_test_template,  ['lab_test_uom' ,'lab_test_normal_range'] )
                        urine_lab_test_itmes.append({
                            
                        
                            "test" : template.name,
                            "lab_test_name" : normal_test_template.lab_test_template,
                            "template": template.name,
                            "normal_range": normal_range,
                            "lab_test_uom":  uom,

                            })
                        group_test = frappe.get_doc("Lab Test Template" , normal_test_template.lab_test_template)
                        for test in group_test.normal_test_templates:
                            urine_lab_test_itmes.append({

                            
                                "lab_test_event": test.lab_test_event,
                                
                                
                                "lab_test_uom": test.lab_test_uom,
                                "secondary_uom": test.secondary_uom,
                                "conversion_factor": test.conversion_factor,
                                "normal_range": test.normal_range,
                                "require_result_value": 1,
                                "allow_blank": test.allow_blank,
                                "template": normal_test_template.lab_test_template
                            })

                    lab_test = frappe.get_doc({
                    'doctype': 'Lab Result',
                    'patient' : sam.patient,
                    'practitioner' : sam.ref_practitioner,
                    "invoice_no" : sam.name,
                    "lab_ref" : doc.lab_ref,
                    'normal_test_items' : urine_lab_test_itmes,
                    "template" : template.name,
                    "lab_test_name" : template.name,
                    "type" : "Group",
                    "reff_collection": doc.name
                    
                    })
        
        # for item in doc.items:
        #     create_lab_tests(item.item_code)
                    lab_test.insert()
                    event = "lab_resul_update"
                    frappe.publish_realtime(event)


                    
        
    
                    
       
    if lab_test_itmes :
        lab_test = frappe.get_doc({
            'doctype': 'Lab Result',
            'patient' : sam.patient,
            'practitioner' : sam.ref_practitioner,
            "invoice_no" : sam.name,
            "lab_ref" : doc.lab_ref,
            'normal_test_items' : lab_test_itmes,
            "type" : "Blood",
            "reff_collection": doc.name
            
            
            })
        
        # for item in doc.items:
        #     create_lab_tests(item.item_code)
        lab_test.insert(ignore_permissions = 1)
        create_tests_sts(lab_test.doctype , lab_test.name)
        event = "lab_resul_update"
        frappe.publish_realtime(event)

    if hor_lab_test_itmes:

        ho_lab_test = frappe.get_doc({
                    'doctype': 'Lab Result',
                    'patient' : sam.patient,
                    'practitioner' : sam.ref_practitioner,
                    "invoice_no" : sam.name,
                    "lab_ref" : doc.lab_ref,
                    'normal_test_items' : hor_lab_test_itmes,
                    "reff_collection": doc.name,
                
                    "type" : "Hormones"
                    
                    })
        ho_lab_test.insert()
        event = "lab_resul_update"
        frappe.publish_realtime(event)


def create_normals(item_code):
        # for item in doc.items:
        #     frappe.errprint(item.item_code)
            # lab_test.normal_toggle = 1
        template = frappe.get_doc("Lab Test Template" , item_code)
        normal = lab_test.append("normal_test_items")
        normal.lab_test_name = template.lab_test_name
        normal.lab_test_uom = template.lab_test_uom
        normal.secondary_uom = template.secondary_uom
        normal.conversion_factor = template.conversion_factor
        normal.normal_range = template.lab_test_normal_range
        normal.require_result_value = 1
        normal.allow_blank = 0



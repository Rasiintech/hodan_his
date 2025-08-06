// Copyright (c) 2024, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('opthalmology exam form', {
	refresh: function(frm) {
		
		
			var  Admission_request= frm.add_custom_button('Admission Request', () => {
				
				
					frappe.new_doc("Admission Ordering Request", { 
					"patient": frm.doc.patient, 
					"practitioner": frm.doc.practitioner, 
					
					})
		})
		Admission_request.addClass('btn-danger');
	
        	var btn1 = frm.add_custom_button('Requests', () => {
				
					if (frm.doc.opthalmology){
							
							frappe.set_route("Form","Healthcare Requests", frm.doc.opthalmology) 
					
					}
					else{
						frappe.new_doc("Healthcare Requests", { 
						"patient": frm.doc.patient, 
						"practitioner": frm.doc.practitioner, 
						"source_order": "OPD", 
						"opthalmology" : frm.doc.name
					})
		
						}
					
				
				
			
						
		
			
        
	
		})
		btn1.addClass('btn-danger');
		
		
		
	
	 }
	 
});

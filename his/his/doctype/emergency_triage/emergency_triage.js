// Copyright (c) 2024, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Emergency Triage', {
	refresh: function(frm) {
		
		
			var  Admission_request= frm.add_custom_button('Admission Request', () => {
				
				
					frappe.new_doc("Admission Ordering Request", { 
					"patient": frm.doc.patient, 
					"practitioner": frm.doc.practitioner, 
					
					})
		})
		Admission_request.addClass('btn-danger');
	
        	var btn1 = frm.add_custom_button('Requests', () => {
				
					if (frm.doc.requests){
							
							frappe.set_route("Form","Healthcare Requests", frm.doc.requests) 
					
					}
					else{
						frappe.new_doc("Healthcare Requests", { 
						"patient": frm.doc.patient, 
						"practitioner": frm.doc.practitioner, 
						"source_order": "E.R", 
						"source" : frm.doc.name
					})
		
						}
					
				
				
			
						
		
			
        
	
		})
		btn1.addClass('btn-danger');
		
		if(frm.doc.status != "Discharged" && frm.doc.status != "Admitted") {

		
		let dischargebtn = frm.add_custom_button(__("Discharge"), function() {
			// frappe.confirm(`<strong>${frappe.session.user_fullname}</strong> Are you sure you want to Discharge <strong>${frm.doc.patient_name}</strong>?`,
			// 	() => {
			// 		frappe.utils.play_sound("submit");

			// 		frappe.show_alert({
			// 			message: __('Patient Discharged Successfully'),
			// 			indicator: 'green',
			// 		}, 5);

			// 		// Update the status field
			// 		frm.set_value('status', 'Discharge');
			// 		frm.save_or_update();

			// 		// Change button color
			// 		dischargebtn.addClass('btn-danger');
			// 	}
			// );

			if (frm.doc.discharge_summary){
							
				frappe.set_route("Form","Discharge Summary", frm.doc.discharge_summary) 
		
			}
			else{
				frappe.new_doc("Discharge Summary", { 
				"patient": frm.doc.patient, 
				"emergency_triage": frm.doc.name, 
				"source_order": "E.R", 
				})

			}
		});
	}
	 }
});


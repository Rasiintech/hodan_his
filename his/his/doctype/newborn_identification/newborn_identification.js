// Copyright (c) 2024, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Newborn identification', {
	refresh: function(frm) {
		if (frm.doc.patient || !frm.is_new()){
			var  Admission_request= frm.add_custom_button('Admission Request', () => {
				
				
				frappe.new_doc("Admission Ordering Request", { 
				"patient": frm.doc.patient, 
				"practitioner": frm.doc.practitioner, 
				
				})
	})
	Admission_request.addClass('btn-danger');
		}
	}
});

// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Post Delivery', {
	refresh: function(frm) {
		if(!frm.is_new()){
			var btn1 = frm.add_custom_button('Orders', () => {
				frappe.new_doc("Inpatient Order", { "patient": frm.doc.patient, "practitioner": frm.doc.ref_practitioner, "doctor_plan": frm.doc.name })
		
			})
			btn1.addClass('btn-danger');

			
		}
	}
});

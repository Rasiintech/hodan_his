// Copyright (c) 2024, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('OPERATION PROCEDURE SCHEDULE', {
	refresh: function (frm) {
		if (!frm.is_new()) {
			frm.add_custom_button('Preoperative Checklist', () => {
				frappe.new_doc("Preoperative Checklist Inpatient", {
					"patient": frm.doc.patient,
					// "surgial_consent": frm.doc.surgeon,
					"procedure": frm.doc.procedure,
					//  "date_of_procedure" : frm.doc.date

				})
			}, 'Create')
			frm.add_custom_button('POST OPERATIVE STANDING ORDERS', () => {
				frappe.new_doc("POST OPERATIVE STANDING ORDERS", {
					"patient": frm.doc.patient,
					// "surgial_consent": frm.doc.surgeon,
					"procedure": frm.doc.procedure,
					//  "date_of_procedure" : frm.doc.date

				})
			}, 'Create')

			frm.add_custom_button('Clinical Procedure', () => {
				frappe.new_doc("Clinical Procedure", {
					"patient": frm.doc.patient, "practitioner": frm.doc.surgeon, "procedure_template": frm.doc.procedure,
				})
			}, 'Create')


			// frm.add_custom_button('SURGICAL PROCEDURE VERIFICATION', () => {
			// 	frappe.new_doc("PSURGICAL PROCEDURE VERIFICATION FORM", { "patient": frm.doc.patient, 
			// 	// "surgial_consent": frm.doc.surgeon,
			// 	 "procedure" :frm.doc.procedure ,
			// 	//  "date_of_procedure" : frm.doc.date

			// 	})
			// }, 'Create')

			frm.add_custom_button('OPERATIVE REPORT', () => {
				frappe.new_doc("OPERATIVE REPORT", {
					"patient": frm.doc.patient,
					// "surgial_consent": frm.doc.surgeon,
					"procedure": frm.doc.procedure,
					//  "date_of_procedure" : frm.doc.date

				})
			}, 'Create')
		}
	}

});

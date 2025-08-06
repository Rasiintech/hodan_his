// Copyright (c) 2024, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pre Anesthesia Evaluation and Re Evaluation Form', {
	refresh: function(frm) {
		if (!frm.doc.__islocal){
			frm.add_custom_button(__('OR Confirmation'), function() {
				// Disable the button immediately after it's clicked
				var button = $(this);
				button.prop('disabled', true);  // Disable the button
			
				// Check if the data has already been sent using a flag
				if (frm.doc._data_sent) {
					frappe.show_alert({
						message: __("Data has already been sent to OR Confirmation."),
						indicator: 'yellow'
					}, 3);
					return;  // Exit early if the data is already sent
				}

				// Create a new Recovery document without opening the form
				frappe.db.insert({
					doctype: 'OR Confirmation Form',
					patient: frm.doc.pid,
					date_of_procedure:frm.doc.proposed_date_of_surgury,
					surgeon: frm.doc.surgeon,
					planned_procedure: frm.doc.surgical_procedure,
					diagnose:frm.doc.diagnosis,
					lenght_of_stay:frm.doc.lenght_of_stay,
					// frm.doc.surgeon,
					// patient_name: frm.doc.patient_name,
					// patient_age: frm.doc.patient_age,
					// practitioner: frm.doc.practitioner,
					// procedure_template: frm.doc.procedure_template,
					// appointment_date:frm.doc.date,
					// status: "Scheduled",
					// procedure_date: frm.doc.procedure_date,
					// Add any other fields you need to map here
				}).then(doc => {
					// Mark the data as sent by setting the flag
					frm.doc._data_sent = true;
					frappe.show_alert({
						message: __("Patient Successfully Transferred into OR Confirmation Form"),
						indicator: 'green'
					}, 3);
				}).catch((error) => {
					// Handle error if insertion fails
					frappe.show_alert({
						message: __("Error in transferring patient to Anesthesia. Please try again."),
						indicator: 'red'
					}, 3);
			
					// Re-enable the button if there was an error
					button.prop('disabled', false);
				});
			}).addClass("btn-primary");
		}
		
	}
});

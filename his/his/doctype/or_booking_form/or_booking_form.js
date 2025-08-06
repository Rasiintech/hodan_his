// Copyright (c) 2024, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('OR BOOKING FORM', {
	refresh: function(frm) {
		if (!frm.doc.__islocal){
			frm.add_custom_button(__('Send to Anesthesia'), function() {
				// Disable the button immediately after it's clicked
				var button = $(this);
				button.prop('disabled', true);  // Disable the button
			
				// Check if the data has already been sent using a flag
				if (frm.doc._data_sent) {
					frappe.show_alert({
						message: __("Data has already been sent to Anesthesia."),
						indicator: 'yellow'
					}, 3);
					return;  // Exit early if the data is already sent
				}
			
				// Create a new Recovery document without opening the form
				frappe.db.insert({
					doctype: 'Pre Anesthesia Evaluation and Re Evaluation Form',
					pid: frm.doc.patient,
					surgical_procedure: frm.doc.procedure,
					weight: frm.doc.weight,
					diagnosis: frm.doc.diagnosis,
					proposed_date_of_surgury: frm.doc.proposed_date_of_surgury,
					surgeon: frm.doc.surgeon,
					lenght_of_stay:frm.doc.surgery_lenght_of_time,
				}).then(doc => {
					// Mark the data as sent by setting the flag
					frm.doc._data_sent = true;
			
					// Show success message
					frappe.show_alert({
						message: __("Patient Successfully Transferred into Anesthesia"),
						indicator: 'green'
					}, 3);
			
					// Optionally, hide the button after successful submission
					button.hide(); // You can also disable it if you prefer not to hide it
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

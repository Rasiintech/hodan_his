// Copyright (c) 2024, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('OR Confirmation Form', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1){
			var  Admission_request= frm.add_custom_button('Admission Request', () => {
				
				
				frappe.new_doc("Admission Ordering Request", { 
				"patient": frm.doc.patient, 
				"practitioner": frm.doc.practitioner, 
				"practitioner":frm.doc.surgeon,
				"diagnose": frm.doc.diagnose,
				"lenght_of_stay":frm.doc.lenght_of_stay,
				
				})

			})
			frm.add_custom_button(__('Send to OR Schedule'), function() {
				// Disable the button immediately after it's clicked
				var button = $(this);
				button.prop('disabled', true);  // Disable the button
			
				// Check if the data has already been sent using a flag
				if (frm.doc._data_sent) {
					frappe.show_alert({
						message: __("Data has already been sent to OR Schedule"),
						indicator: 'yellow'
					}, 3);
					return;  // Exit early if the data is already sent
				}
			
				// Create a new Recovery document without opening the form
				frappe.db.insert({
					doctype: 'OT Schedule',
					patient: frm.doc.patient,
					procedure_template:frm.doc.planned_procedure,
					// surgical_procedure: frm.doc.procedure,
					// weight: frm.doc.weight,
					// diagnosis: frm.doc.diagnosis,
					// proposed_date_of_surgury: frm.doc.proposed_date_of_surgury,
					practitioner: frm.doc.surgeon,
					name_of_anaesthetist:frm.doc.anesthetist_name,
					appointment_date: get_today(),
					status: "Scheduled",
				}).then(doc => {
					// Mark the data as sent by setting the flag
					frm.doc._data_sent = true;
			
					// Show success message
					frappe.show_alert({
						message: __("Patient Successfully Transferred into OR Schedule"),
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

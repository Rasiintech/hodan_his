            // Copyright (c) 2022, Anfac and contributors
            // For license information, please see license.txt

frappe.ui.form.on('Lab Result', {

    onload: function(frm) {
        if (frm.doc.patient && frm.is_new()) {
            frappe.db.get_doc('Patient', frm.doc.patient)
                .then(patient_doc => {
                    let age = calculate_age(patient_doc.dob);
                    frappe.model.set_value(frm.doctype, frm.docname, 'patient_age', age);
                })
                .catch(err => {
                    console.error("Failed to fetch patient document:", err);
                });
        }
    
    },

    refresh: function(frm) {

        frm.add_custom_button('Print', () => {

        if(frm.doc.type == "Group"){
            if(frm.doc.template === "STOOL ROUTINE" || frm.doc.template  === "Urine Routine" ||  frm.doc.template  === "CBC" ){
                window.open(`
                    ${frappe.urllib.get_base_url()}/printview?doctype=Lab%20Result&name=${frm.doc.name}&trigger_print=1&format=Urine%20Report&no_letterhead=0&letterhead=Logo&settings=%7B%7D&_lang=en-US
            `);
            }
            else {
                window.open(`
                    ${frappe.urllib.get_base_url()}/printview?doctype=Lab%20Result&name=${frm.doc.name}&trigger_print=1&format=Urine%20Report2&no_letterhead=0&letterhead=Logo&settings=%7B%7D&_lang=en-US
                `);
            } 
        }
        else {
            window.open(`
                ${frappe.urllib.get_base_url()}/printview?doctype=Lab%20Result&name=${frm.doc.name}&trigger_print=1&format=lab%20result%20report&no_letterhead=0&letterhead=Logo&settings=%7B%7D&_lang=en-US`);
            }
        })

        frm.add_custom_button('Send SMS', () => {
            if (frm.is_new()) {
                frappe.msgprint(__('Please save the document before sending an SMS.'));
                return;
            }

            // Show confirmation dialog
            frappe.confirm(
                'Are you sure you want to send an SMS?',
                () => {
                    // User clicked Yes
                    frappe.db.get_value('Healthcare Settings', 'Healthcare Settings', 'sms_printed')
                        .then(response => {
                            let sms_text = response.message.sms_printed || '';
                            let message = `${frm.doc.patient_name} ${sms_text}`;

                            // Send SMS via server-side method
                            frappe.call({
                                method: "his.api.send_sms.send_sms",
                                args: {
                                    mobile: frm.doc.mobile,
                                    message: message
                                },
                                callback: function (r) {
                                    if (r.message) {
                                        frappe.msgprint(__('SMS sent successfully.'));
                                    } else {
                                        frappe.msgprint(__('Failed to send SMS.'));
                                    }
                                },
                                error: function (err) {
                                    frappe.msgprint(__('An error occurred while sending SMS.'));
                                    console.error(err);
                                }
                            });
                        })
                        .catch(err => {
                            frappe.msgprint(__('Could not fetch SMS template.'));
                            console.error(err);
                        });
                },
                () => {
                    // User clicked No
                    frappe.msgprint(__('SMS sending cancelled.'));
                }
            );
        });


    },

   patient: function(frm) {
        if (frm.doc.patient) {
            frappe.db.get_doc('Patient', frm.doc.patient)
                .then(patient_doc => {
                    let age = calculate_age(patient_doc.dob);
                    frappe.model.set_value(frm.doctype, frm.docname, 'patient_age', age);
                })
                .catch(err => {
                    console.error("Failed to fetch patient document:", err);
                });
        }
    }
});



let calculate_age = function(birth) {
	let ageMS = Date.parse(Date()) - Date.parse(birth);
	let age = new Date();
	age.setTime(ageMS);
	let years =  age.getFullYear() - 1970;
	return `${years} ${__('Years(s)')} ${age.getMonth()} ${__('Month(s)')} ${age.getDate()} ${__('Day(s)')}`;
};

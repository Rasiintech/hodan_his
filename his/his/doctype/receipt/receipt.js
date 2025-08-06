// Copyright (c) 2024, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Receipt', {
	refresh: function(frm) {
		

	},
	customer: function(frm){
		frappe.call({
			method: "erpnext.accounts.utils.get_balance_on",
			args: {
				company: frappe.defaults.get_user_default("Company"),
				party_type: "Customer",
				party: frm.doc.customer,
				date: frappe.datetime.get_today()
			},
			callback: function(r, rt) {
				if(r.message) {
				 
				frm.set_value("current_balance", r.message)
				}
			}
		});
	},
	discount : function(frm){
		let dis = parseFloat(frm.doc.discount) / parseFloat(frm.doc.reference.length)
		frm.doc.reference.forEach((el, indx)=>{
			el.discount=dis
			el.balance = (el.balance-dis || el.balances)
			frm.refresh_field("reference")
		})
	}
	,

	patient: function(frm){
		
		// args = {
		// 	"customer" : frm.doc.customer
		// 	"from_date" : frm.doc.from_date,
		// 	"to_date" : frm.doc.to_date,

		// }
		let patient = frm.doc.patient.split(',')[0].trim();
		let paying_balance = 0
		// alert(patient)
		
		if(!frm.doc.from_date || !frm.doc.to_date){
			frappe.throw("Please Select Customer and Date")
		}
		else{
		if(frm.doc.customer){
		frappe.call({
			method: "his.his.doctype.receipt.receipt.get_patient",
			args: {
			
				customer: frm.doc.customer,
				from_date : frm.doc.from_date,
				to_date : frm.doc.to_date,
				patient: patient
				
			},
			callback: function(r, rt) {
				if(r.message[0]) {
				    r.message[0].forEach(element => {
						paying_balance += element.balance
						

						// link_patient.push(`${element.patient } ,${element.patient_name } , ${element.balance} `)
					});
					setTimeout(() => {
				frm.set_value("reference", r.message[0])
				frm.set_value("balance", paying_balance)
				
				
			}, 100);
				}

			}
		});
	}
	else{
		if(!frm.doc.from_date || !frm.doc.to_date){
			frappe.throw("Please Select Customer and Date")
		}
		else{
		frappe.call({
			method: "his.his.doctype.receipt.receipt.get_customers",
			args: {
			
				customer_group: frm.doc.customer_group,
				from_date : frm.doc.from_date,
				to_date : frm.doc.to_date,
				patient: patient
				
			},
			callback: function(r, rt) {
				if(r.message[0]) {
				    r.message[0].forEach(element => {
						paying_balance += element.balance
						// link_patient.push(`${element.patient } ,${element.patient_name } , ${element.balance} `)
					});
					setTimeout(() => {
				frm.set_value("reference", r.message[0])
				frm.set_value("balance", paying_balance)
			}, 100);
				}

			}
		});
	}
	}
	}

		
	},
	from_date : function(frm){
		let link_patient = []
		let total_balance = 0
		if(frm.doc.to_date){
			if(frm.doc.customer){
		frappe.call({
			method: "his.his.doctype.receipt.receipt.get_patient",
			args: {
			
				customer: frm.doc.customer,
				from_date : frm.doc.from_date,
				to_date : frm.doc.to_date
				
			},
			callback: function(r, rt) {
				if(r.message[0]) {
			
					r.message[0].forEach(element => {
						total_balance += element.balance
						link_patient.push(`${element.patient } ,${element.patient_name } , ${element.balance} `)
					});
					setTimeout(() => {
						link_patient.unshift(`All , ${total_balance} `)
						frappe.meta.get_docfield('Receipt', 'patient', frm.doc.name).options = link_patient;
						frm.refresh_field('patient');
						
						
					}, 100);

				
		
				}
			}
		});
	}
	else{
		frappe.call({
			method: "his.his.doctype.receipt.receipt.get_customers",
			args: {
			
				customer_group: frm.doc.customer_group,
				from_date : frm.doc.from_date,
				to_date : frm.doc.to_date,
				// patient: patient
				
			},
			callback: function(r, rt) {
				if(r.message[0]) {
					
					r.message[0].forEach(element => {
						total_balance += element.balance
						link_patient.push(`${element.patient } ,${element.patient_name } , ${element.balance} `)
					});
					setTimeout(() => {
						link_patient.unshift(`All , ${total_balance} `)
						frappe.meta.get_docfield('Receipt', 'patient', frm.doc.name).options = link_patient;
						frm.refresh_field('patient');
						
						
					}, 100);

				
			
				}
			}
		});
	}
	}
		},
		to_date : function(frm){
			let link_patient = []
			let total_balance = 0
			if(frm.doc.from_date){
				if(frm.doc.customer){
			frappe.call({
				method: "his.his.doctype.receipt.receipt.get_patient",
				args: {
				
					customer: frm.doc.customer,
					from_date : frm.doc.from_date,
					to_date : frm.doc.to_date
					
				},
				callback: function(r, rt) {
					if(r.message[0]) {
						
						r.message[0].forEach(element => {
							total_balance += element.balance
							link_patient.push(`${element.patient } ,${element.patient_name } , ${element.balance} `)
						});
						setTimeout(() => {
							link_patient.unshift(`All , ${total_balance} `)
							frappe.meta.get_docfield('Receipt', 'patient', frm.doc.name).options = link_patient;
							frm.refresh_field('patient');
							
							
						}, 100);
	
					
				
					}
				}
			});
		}
		else{
			frappe.call({
				method: "his.his.doctype.receipt.receipt.get_customers",
				args: {
				
					customer_group: frm.doc.customer_group,
					from_date : frm.doc.from_date,
					to_date : frm.doc.to_date,
					// patient: patient
					
				},
				callback: function(r, rt) {
					if(r.message[0]) {
						
						r.message[0].forEach(element => {
							total_balance += element.balance
							link_patient.push(`${element.patient } ,${element.patient_name } , ${element.balance} `)
						});
						setTimeout(() => {
							link_patient.unshift(`All , ${total_balance} `)
							frappe.meta.get_docfield('Receipt', 'patient', frm.doc.name).options = link_patient;
							frm.refresh_field('patient');
							
							
						}, 100);
	
					
				
					}
				}
			});
		}


		}
			}


		
});

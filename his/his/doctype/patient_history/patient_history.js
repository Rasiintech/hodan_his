// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Patient History', {
	onload: function(frm) {
		if (frm.doc.patient) {
			frappe.db.get_doc('Patient', frm.doc.patient)
				.then(patient_doc => {
					let age = calculate_age(patient_doc.dob);
					frm.set_value('age', age);
				})
				.catch(err => {
					console.error("Failed to fetch patient document:", err);
				});
		}
		// if (frm.doc.patient && frm.is_new()) {
		// 	frm.save()
		// }
	},
	// view_as_chart:function(frm){
	// 	$("#vitals").html(`<div id="vitalSignsChart"> <img src = "/files/F2.large(2).png" /></canvas>`)
	// 	// alert("Test")
	// 	// setup_chart()
		
	// },
	add_new_progress:function(frm){
		frappe.new_doc("Progress Note", { "patient": frm.doc.patient})
	},
	add_new_nursing_note:function(frm){
		frappe.new_doc("NURSES PROGRESS NOTE", { "patient": frm.doc.patient})
	},
	add_new_blood: function(frm){
		frappe.new_doc("BLOOD TRANSFUSION OBSERVATION CHART", { "patient": frm.doc.patient})
	},
	// 
	add_new_blood_t_f: function(frm){
		frappe.new_doc("BLOOD TRANSFUSION FORM", { "patient": frm.doc.patient})
	}
	// 
	,
	add_history: function(frm){
		frappe.new_doc("History Taken", { "patient": frm.doc.patient})
	},
	refresh: function(frm) {

		if (frm.doc.patient) {
            frappe.call({
                method: "rasiin_design.api.p_history.get_history", //dotted path to server method
                args: { "patient": frm.doc.patient },
                //  args : {"load_a" : currdate , to_date : to_date},
                callback: function (r) {
                    $('#history').html(r.message)

                    // console.log(window.open.document)
                    // 	var x = window;
                    // 	x.document.open().write(r.message);



                }
            })
        }


		if (frappe.user_roles.includes('Cashier')) {
			frm.add_custom_button(__("Transfer"), function(){
				transfer_patient_dialog(frm);
			
				//perform desired action such as routing to new form or fetching etc.
			  })
		
			// btn.addClass('btn-danger');
		} 

		if (frappe.user_roles.includes('Doctor') || frappe.user_roles.includes('Nurse')) {
			var btn = frm.add_custom_button('Discharge', () => {
				frappe.new_doc("Discharge Summary", { "patient": frm.doc.patient, "ref_practitioner": frm.doc.consultant, "doctor_plan": frm.doc.name })
			
			})
			btn.addClass('btn-danger');
		}
		if (frappe.user_roles.includes('Doctor')) {
			frm.add_custom_button(__("Ready To Surgery"), function(){
				frappe.new_doc("Surgery Preparation", { "patient": frm.doc.patient, "practitioner": frm.doc.ref_practitioner, })
			
				//perform desired action such as routing to new form or fetching etc.
			  })
			//   frm.add_custom_button(__("Transfer"), function(){
			// 	transfer_patient_dialog(frm);
			
			// 	//perform desired action such as routing to new form or fetching etc.
			//   }, __("IPD Forms"))

			  frm.add_custom_button(__("Share to another Doctor"), function(){
				// refer(frm);
				let d = new frappe.ui.Dialog({
				title: 'Refer Doctor',
				fields: [
					{
						label: 'Consultant',
						fieldname: 'practitioner',
						fieldtype: 'Link',
						options : "Healthcare Practitioner",
						reqd : 1
					},
					{
						label: 'Access',
						fieldname: 'access',
						fieldtype: 'Select',
						options : "Give Access\nRemove Access",
						reqd : 1
					}
				
				],
				size: 'small', // small, large, extra-large 
				primary_action_label: 'Submit',
				primary_action(values) {
					d.hide();
					// console.log()
						// let inpatient_rec = frappe.get_doc('Inpatient Record', ip.name)
						// inpatient_rec.ref_practitioner = "Dr Mohamed Dahir Aden"
						// inpatient_rec.save()

						frappe.call({
							method: 'his.his.doctype.patient_history.patient_history.share',
							args: {
								'patient': frm.doc.patient,

								'practitioner' : values.practitioner,
								'doctype': "Inpatient Record",
								'access': values.access
								
							},
							callback: function(r) {
								
								// console.log(r)
								// if (!r.exc) {
								// 	// code snippet
								// }
							}
						});
						
				}
				 
			});
			
			d.show();

			
				//perform desired action such as routing to new form or fetching etc.
			  },__("Share or Refer"))

			  frm.add_custom_button(__("Refer"), function(){
				refer(frm);
			
				//perform desired action such as routing to new form or fetching etc.
			  },__("Share or Refer"))
			if (frappe.user_roles.includes('Doctor') || frappe.user_roles.includes('Nurse')) {
			var btn = frm.add_custom_button('Discharge', () => {
				frappe.new_doc("Discharge Summary", { "patient": frm.doc.patient, "ref_practitioner": frm.doc.ref_practitioner, "doctor_plan": frm.doc.name })
			
			})
			btn.addClass('btn-danger');
		}


			var btn5 = frm.add_custom_button('Medication Administration Record', () => {
				frappe.new_doc("medication administration form", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button('Admission Ordering Request Form', () => {
				frappe.new_doc("Admission Ordering Request Form", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button('Emergency Triage Form', () => {
				frappe.new_doc("Emergency Triage", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button('Anesthesia Sheet', () => {
				frappe.new_doc("Anesthesia", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button('Anesthesia Evaluation and Reevaluation', () => {
				frappe.new_doc("Anesthesia", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button('Pre Anesthesia Questionnaire', () => {
				frappe.new_doc("Anesthesia", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button('Blood Bank Transfusion', () => {
				frappe.new_doc("BLOOD BANK TRANSFUSION REQUEST FORM", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button('Central Venous Catheter Insertion', () => {
				frappe.new_doc("CENTRAL VENOUS CATHETER INSERTION CHECKLIST", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button('Daily Handover Sheet', () => {
				frappe.new_doc("DAILY HANDOVER SHEET", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button('ICU Standard Progress Notes', () => {
				frappe.new_doc("ICU Standard progress note", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button('Endorsement and Followup', () => {
				frappe.new_doc("ENDORSEMENT AND FOLLOW-UP FORM", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button('Medical Report', () => {
				frappe.new_doc("MEDICAL REPORTS", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button('Patient Progress Notes', () => {
				frappe.new_doc("Patient Progress Notes", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button('Radiology Request', () => {
				frappe.new_doc("Radiology", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button('Discharge Summary', () => {
				frappe.new_doc("Discharge Summary Medical Report", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button('Non Formulary Drug Form', () => {
				frappe.new_doc("Non Formulary Drug Request", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Physician Order's Form", () => {
				frappe.new_doc("physician orders form", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Vital Sign Sheet", () => {
				frappe.new_doc("Vital Signs", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Labor Birth Record Initial Assessment", () => {
				frappe.new_doc("Labour Birth Record IInitial Assessment", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Newborn Identification", () => {
				frappe.new_doc("Newborn identification", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Partogram", () => {
				frappe.new_doc("Partogram", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Postnal Discharge Summary", () => {
				frappe.new_doc("Postnatal Discharge Summary", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Growth Chart - Birth - 36 months Boys", () => {
				frappe.new_doc("growth chart birth to 36 months boy", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Growth Chart - Birth - 36 months- girls", () => {
				frappe.new_doc("growth chart birth to 36 months girls", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Growth Chart - 2-20 years - boys", () => {
				frappe.new_doc("growth chart 2 to 20 boys", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Growth Chart - 2-20 years - girls", () => {
				frappe.new_doc("growth chart 2 to 20 girls", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Neonatal Database", () => {
				frappe.new_doc("Neonatal database", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Pediatric Database", () => {
				frappe.new_doc("PEDIATRIC DATABASE", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Bone Marrow Request", () => {
				frappe.new_doc("Bone Marrow Request Form", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Discharge from ICU", () => {
				frappe.new_doc("Discharge FROM ICU", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
	
			
			var btn5 = frm.add_custom_button("Physician Consultation form", () => {
				frappe.new_doc("physican consultation report", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Postpartum Visit", () => {
				frappe.new_doc("Postpartum Visit Form", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Prenatal Visit", () => {
				frappe.new_doc("Prenatal Visits", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
			
			var btn5 = frm.add_custom_button("Physical Examination", () => {
				frappe.new_doc("Physical Examination", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button("History and Physical Exam", () => {
				frappe.new_doc("History and Physical Exam", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button("OB-GYN OPD Admission & Physical Exam", () => {
				frappe.new_doc("OBS-GYN AND OPD", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button("Ordering Form", () => {
				frappe.new_doc("Admission ORDERING Form", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button("Outpatient Visit", () => {
				frappe.new_doc("Visit", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button("Neonatal TPN", () => {
				frappe.new_doc("Neonatal TPN Form", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button("Newborn Nursery Discharge Summary", () => {
				frappe.new_doc("NEWBORN NURSERY DISCHARGE SUMMARY", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button("Weight for Stature percentile - boys", () => {
				frappe.new_doc("weight for stature percentiles Boys", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button("Weight for Stature percentile - girls", () => {
				frappe.new_doc("weight for stature percentiles girls", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button("General Pre Operative Orders", () => {
				frappe.new_doc("General Surgery", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button("Operative Report ", () => {
				frappe.new_doc("OPERATIVE REPORT", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button("Post Operative Standing Reports ", () => {
				frappe.new_doc("POST OPERATIVE STANDING ORDERS", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button("Preoperative Checklist", () => {
				frappe.new_doc("Preoperative Checklist Inpatient", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');

			var btn5 = frm.add_custom_button("Surgical Verification Form", () => {
				frappe.new_doc("SURGICAL PROCEDURE VERIFICATION FORM", { "patient": frm.doc.patient})
		
			},__("Doctor Forms"))
			btn5.addClass('btn-danger');
		} 

		
			var btn1 = frm.add_custom_button('Requests', () => {
				frappe.new_doc("Healthcare Requests", { "patient": frm.doc.patient, "practitioner": frm.doc.ref_practitioner, "source_order": "IPD" })
		
			})
	
			btn1.addClass('btn-primary');

			var bt = frm.add_custom_button('Procedure Request', () => {
				frappe.new_doc("Healthcare Requests", { "patient": frm.doc.patient, "practitioner": frm.doc.consultant, "hide" : 1, "source_order": "IPD" })
		
			})
			bt.addClass('btn-danger');
		// if (frappe.user_roles.includes('NICU')) {
		// 	var btn1 = frm.add_custom_button('NICU', () => {
		// 		frappe.new_doc("NICU", { "patient": frm.doc.patient})
		
		// 	},__("Action"))
		// 	btn1.addClass('btn-primary');
		// } 
		// if (frappe.user_roles.includes('Nurse')) {
			var btn3 = frm.add_custom_button('Vital Sign', () => {
				frappe.new_doc("Vital Signs", { "patient": frm.doc.patient })
		
			})
			btn3.addClass('btn-primary');
		
			var btn2 = frm.add_custom_button('Medication', () => {
				frappe.new_doc("Inpatient Medication", { "patient": frm.doc.patient, "practitioner": frm.doc.ref_practitioner, "doctor_plan": frm.doc.name })
		
			})
			btn2.addClass('btn-danger');
			// var btn4 = frm.add_custom_button('fluid chart', () => {
			// 	frappe.new_doc("fluid chart monitoring", { "patient": frm.doc.patient, "practitioner": frm.doc.ref_practitioner, "doctor_plan": frm.doc.name })
		
			// },__("IPD Forms") )
			// btn4.addClass('btn-danger');
			// if (frm.doc.type=="IPD"){
		if (frappe.user_roles.includes('Nurse')) {
			var btn5 = frm.add_custom_button('Dressing flow chart', () => {
				frappe.new_doc("Dressing", { "patient": frm.doc.patient})
		
			},__("Nurse Forms"))
			btn5.addClass('btn-danger');

			var btn6 = frm.add_custom_button('Emergency Nursing Assessment', () => {
				frappe.new_doc("Emergency Nursing Assessment form", { "patient": frm.doc.patient})
		
			},__("Nurse Forms"))
			btn6.addClass('btn-danger');

			var btn6 = frm.add_custom_button("Nurse's Progress Notes", () => {
				frappe.new_doc("NURSES PROGRESS NOTE", { "patient": frm.doc.patient})
		
			},__("Nurse Forms"))
			btn6.addClass('btn-danger');

			var btn6 = frm.add_custom_button("Diabetic Flow Sheet", () => {
				frappe.new_doc("Diabetic Flow Sheet", { "patient": frm.doc.patient})
		
			},__("Nurse Forms"))
			btn6.addClass('btn-danger');

			var btn6 = frm.add_custom_button("Fluid Balance Record (Intake & Output)", () => {
				frappe.new_doc("Fluid Balance Record", { "patient": frm.doc.patient})
		
			},__("Nurse Forms"))
			btn6.addClass('btn-danger');

			var btn6 = frm.add_custom_button("Medication Administration Record", () => {
				frappe.new_doc("medication administration form", { "patient": frm.doc.patient})
		
			},__("Nurse Forms"))
			btn6.addClass('btn-danger');

			var btn6 = frm.add_custom_button("Blood Gases Results", () => {
				frappe.new_doc("BLOOD GASES RESULTS", { "patient": frm.doc.patient})
		
			},__("Nurse Forms"))
			btn6.addClass('btn-danger');

			var btn6 = frm.add_custom_button("Central Venous Catheter Insertion", () => {
				frappe.new_doc("CENTRAL VENOUS CATHETER INSERTION CHECKLIST", { "patient": frm.doc.patient})
		
			},__("Nurse Forms"))
			btn6.addClass('btn-danger');

			var btn6 = frm.add_custom_button("Daily Handover Sheet", () => {
				frappe.new_doc("DAILY HANDOVER SHEET", { "patient": frm.doc.patient})
		
			},__("Nurse Forms"))
			btn6.addClass('btn-danger');

			var btn6 = frm.add_custom_button("ICU - CCU Kardex", () => {
				frappe.new_doc("ICU CCU Kardex", { "patient": frm.doc.patient})
		
			},__("Nurse Forms"))
			btn6.addClass('btn-danger');

			var btn6 = frm.add_custom_button("Inpatient Kardex", () => {
				frappe.new_doc("INPATIENT KARDEX", { "patient": frm.doc.patient})
		
			},__("Nurse Forms"))
			btn6.addClass('btn-danger');

			var btn6 = frm.add_custom_button("Adult Pain Assessment", () => {
				frappe.new_doc("ADULT PAIN ASSESSMENT FORM", { "patient": frm.doc.patient})
		
			},__("Nurse Forms"))
			btn6.addClass('btn-danger');

			var btn6 = frm.add_custom_button("Vital Sign Sheet", () => {
				frappe.new_doc("Vital Signs", { "patient": frm.doc.patient})
		
			},__("Nurse Forms"))
			btn6.addClass('btn-danger');
		}
			var btn6 = frm.add_custom_button('BLOOD TRANSFUSION', () => {
				frappe.new_doc("BLOOD BANK TRANSFUSION REQUEST FORM", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn6.addClass('btn-danger');
			
			

			var btn7 = frm.add_custom_button('Bone Marrow Request', () => {
				frappe.new_doc("Bone Marrow Request Form", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn7.addClass('btn-danger');

			var btn8 = frm.add_custom_button('CENTRAL VENOUS CATHETER INSERTION CHECKLIST', () => {
				frappe.new_doc("CENTRAL VENOUS CATHETER INSERTION CHECKLIST", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn8.addClass('btn-danger');

			var btn9 = frm.add_custom_button('MEDICAL REPORTS', () => {
				frappe.new_doc("MEDICAL REPORTS", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn9.addClass('btn-danger');
			var btn10 = frm.add_custom_button('PHYSICIANS CONSULTATION', () => {
				frappe.new_doc("PHYSICIANS CONSULTATION REPORT", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn10.addClass('btn-danger');

			var btn11 = frm.add_custom_button('Non Formulary Drug Request', () => {
				frappe.new_doc("Non Formulary Drug Request", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn11.addClass('btn-danger');
			var btn11 = frm.add_custom_button('NURSES PROGRESS NOTE', () => {
				frappe.new_doc("NURSES PROGRESS NOTE", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn11.addClass('btn-danger');
			var btn11 = frm.add_custom_button('medication administration', () => {
				frappe.new_doc("medication administration form", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn11.addClass('btn-danger');
			var btn11 = frm.add_custom_button('HOMEGOING INSTRUCTIONS', () => {
				frappe.new_doc("HOMEGOING INSTRUCTIONS", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn11.addClass('btn-danger');
			var btn11 = frm.add_custom_button('Physician Orders and Plan', () => {
				frappe.new_doc("physician orders form", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn11.addClass('btn-danger');
			var btn11 = frm.add_custom_button('Dressing', () => {
				frappe.new_doc("Dressing", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn11.addClass('btn-danger');
			var btn11 = frm.add_custom_button('Discharge Summary', () => {
				frappe.new_doc("Discharge Summary", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn11.addClass('btn-danger');
			var btn11 = frm.add_custom_button('Admission Ordering Request', () => {
				frappe.new_doc("Admission Ordering Request Form", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn11.addClass('btn-danger');
			var btn11 = frm.add_custom_button('ADULT PAIN ASSESSMENT', () => {
				frappe.new_doc("ADULT PAIN ASSESSMENT FORM", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn11.addClass('btn-danger');
			var btn11 = frm.add_custom_button('Patient Progress', () => {
				frappe.new_doc("DIH Patient Progress Notes", { "patient": frm.doc.patient})
		
			},__("IPD Forms"))
			btn11.addClass('btn-danger');
		
		// }

			
// ----------------------------------------------------------Pediatrics Forms  Starts-----------------------------------------------
if (frm.doc.type=="Pediatric" || frm.doc.type=="NICU"){
frm.add_custom_button('Growth chart 2 to 20 Boys', () => {
	frappe.new_doc("growth chart 2 to 20 boys", { "patient": frm.doc.patient})

},__("Pediatric Forms"))

frm.add_custom_button('Growth Chart 2 to 20 girls', () => {
	frappe.new_doc("growth chart 2 to 20 girls", { "patient": frm.doc.patient})

},__("Pediatric Forms"))
frm.add_custom_button('Growth Chart 2 to 20 girls', () => {
	frappe.new_doc("growth chart 2 to 20 girls", { "patient": frm.doc.patient})

},__("Pediatric Forms"))
frm.add_custom_button('Neonatal TPN Form', () => {
	frappe.new_doc("Neonatal TPN Form", { "patient": frm.doc.patient})

},__("Pediatric Forms"))
frm.add_custom_button('PEDIATRIC DATABASE', () => {
	frappe.new_doc("PEDIATRIC DATABASE", { "patient": frm.doc.patient})

},__("Pediatric Forms"))

frm.add_custom_button('Weight for Stature Percentiles Boys', () => {
	frappe.new_doc("weight for stature percentiles Boys", { "patient": frm.doc.patient})

},__("Pediatric Forms"))
frm.add_custom_button('Weight for Stature percentiles Girls', () => {
	frappe.new_doc("weight for stature percentiles girls", { "patient": frm.doc.patient})

},__("Pediatric Forms"))

frm.add_custom_button('NEWBORN NURSERY DISCHARGE', () => {
	frappe.new_doc("NEWBORN NURSERY DISCHARGE SUMMARY", { "patient": frm.doc.patient})

},__("Pediatric Forms"))


frm.add_custom_button('NEWBORN  IDENTIFICATION', () => {
	frappe.new_doc("NEWBORN  IDENTIFICATION", { "patient": frm.doc.patient})

},__("Pediatric Forms"))


}
// ----------------------------------------------------------ICU Forms  Starts-----------------------------------------------
if (frm.doc.type=="ICU"){
frm.add_custom_button('ICU CCU Kardex', () => {
	frappe.new_doc("ICU CCU Kardex", { "patient": frm.doc.patient})

},__("ICU Forms"))

frm.add_custom_button('CENTRAL VENOUS CATHETER INSERTION CHECKLIST', () => {
	frappe.new_doc("CENTRAL VENOUS CATHETER INSERTION CHECKLIST", { "patient": frm.doc.patient})

},__("ICU Forms"))

frm.add_custom_button('BLOOD GASES RESULTS', () => {
	frappe.new_doc("BLOOD GASES RESULTS", { "patient": frm.doc.patient})

},__("ICU Forms"))

frm.add_custom_button('ICU Standard progress note', () => {
	frappe.new_doc("ICU Standard progress note", { "patient": frm.doc.patient})

},__("ICU Forms"))

frm.add_custom_button('BLOOD BANK TRANSFUSION REQUEST FORM', () => {
	frappe.new_doc("BLOOD BANK TRANSFUSION REQUEST FORM", { "patient": frm.doc.patient})

},__("ICU Forms"))
frm.add_custom_button('Discharge FROM ICU', () => {
	frappe.new_doc("Discharge FROM ICU", { "patient": frm.doc.patient})

},__("ICU Forms"))

frm.add_custom_button('DAILY HANDOVER SHEET', () => {
	frappe.new_doc("DAILY HANDOVER SHEET", { "patient": frm.doc.patient})

},__("ICU Forms"))

}

// ----------------------------------------------------------Maternity Forms  Starts-----------------------------------------------
if (frm.doc.type=="Maternity"){
frm.add_custom_button('History and Physical Exam Outpatient', () => {
	frappe.new_doc("History and Physical Exam Outpatient", { "patient": frm.doc.patient})

},__("Maternity Forms"))
frm.add_custom_button('DIH Labour Birth Record IInitial Assessment', () => {
	frappe.new_doc("DIH Labour Birth Record IInitial Assessment", { "patient": frm.doc.patient})

},__("Maternity Forms"))
frm.add_custom_button('DIH Midwife Progress Notes', () => {
	frappe.new_doc("DIH Midwife Progress Notes", { "patient": frm.doc.patient})

},__("Maternity Forms"))

frm.add_custom_button('DIH Newborn identification', () => {
	frappe.new_doc("DIH Newborn identification", { "patient": frm.doc.patient})

},__("Maternity Forms"))

frm.add_custom_button('DIH Partogram', () => {
	frappe.new_doc("DIH Partogram", { "patient": frm.doc.patient})

},__("Maternity Forms"))

frm.add_custom_button('DIH Patient Progress Notes', () => {
	frappe.new_doc("DIH Patient Progress Notes", { "patient": frm.doc.patient})

},__("Maternity Forms"))

frm.add_custom_button('DIH Postnatal Discharge Summary', () => {
	frappe.new_doc("DIH Postnatal Discharge Summary", { "patient": frm.doc.patient})

},__("Maternity Forms"))

frm.add_custom_button('OBs and Gyne Outpatient Admission and physical History form', () => {
	frappe.new_doc("OBs and Gyne Outpatient Admission and physical History form", { "patient": frm.doc.patient})

},__("Maternity Forms"))


			
		} 
		
		  
	
		// frm.set_df_property('view_as_chart', 'css_class', 'align-right');
		
			$('.indicator-pill').hide()
		// $('.standard-actions').hide()
		// frm.disable_save();

	
		
		get_history(frm.doc.patient , "vitals")

		var tabs = $('.form-tabs');
		var parentElement = $('.parent');

// Get all child elements of the parent
		var childElements = tabs.children();

		// Loop through each child element and attach click event handler
		childElements.each(function() {
		var childElement = $(this);
		var tab = childElement[0].innerText.replace(/ /g, '_').toLowerCase()
		if(tab == "prescription"){
			tab = "med"
		}
		// Attach click event handler to the current child element
		childElement.click(function() {
			get_history(frm.doc.patient , tab)
			// Code to execute when the current child element is clicked
			// ...
		});
		});

		// $('#patient-history-vitals_tab-tab').on('click', function() {
        //     // Get the clicked tab name
        //     var tabName = $(this).attr('data-fieldname');
		// 	alert("")
            
        //     // Handle tab click event
      
        // });
	
		// var htmlContent = "<div id = 'vitals' >Test </div>";

        // Set the HTML content to a field in the form
        // frm.set_value('vitals', htmlContent);
		// setupdata_table("PID-00265")

	},
	patient:function(frm){
		get_history(frm.doc.patient , "vitals")

		// alert("")
	},
	
});

function setup_chart(){

// Sample vital signs data
const vitalSignsData = [
	{ datetime: '8:00:00', temperature: 98.6, heartRate: 80, bloodPressure: '120' },
	{ datetime: '12:00:00', temperature: 70.1, heartRate: 82, bloodPressure: '150' },
	{ datetime: '16:00:00', temperature: 97.9, heartRate: 78, bloodPressure: '160' },
	// Add more data entries as needed
  ];
  
  // Function to generate a random color
  function getRandomColor() {
	const letters = '0123456789ABCDEF';
	let color = '#';
	for (let i = 0; i < 6; i++) {
	  color += letters[Math.floor(Math.random() * 16)];
	}
	return color;
  }
  
  // Extract datetimes and vital signs data
  const datetimes = vitalSignsData.map((data) => new Date(data.datetime));
  const vitalSigns = Object.keys(vitalSignsData[0]).filter((key) => key !== 'datetime');
  
  // Create datasets for each vital sign
  const datasets = vitalSigns.map((sign) => ({
	label: sign,
	data: vitalSignsData.map((data) => data[sign]),
	borderColor: getRandomColor(),
	fill: false,
  }));
  
  // Create a new Chart instance
  const ctx = document.getElementById('vitalSignsChart').getContext('2d');
  const chart = new Chart(ctx, {
	type: 'line',
	data: {
	  labels: datetimes,
	  datasets: datasets,
	},
	options: {
	  responsive: true,
	  scales: {
		x: {
		  type: 'time',
		  time: {
			tooltipFormat: 'YYYY-MM-DD HH:mm:ss',
			unit: 'minute',
			displayFormats: {
			  minute: 'YYYY-MM-DD HH:mm',
			},
		  },
		  title: {
			display: true,
			text: 'Date and Time',
		  },
		},
	  },
	},
  });
  
  
  
  
}


function getRandomColor() {
	const letters = '0123456789ABCDEF';
	let color = '#';
	for (let i = 0; i < 6; i++) {
	  color += letters[Math.floor(Math.random() * 16)];
	}
	return color;
  }

function get_history(patient ,tab) {
	// alert(tab)
	
	let tbldata = []
	let lab_data = []
	
	frappe.call({
        method: "his.dashboard_and_history.p_history.get_p_histy", //dotted path to server method
        args : {"patient" : patient},
        callback: function(r) {
           let columns =  r.message[0][tab]
		   let data = r.message[1][tab]
			// console.log(data)
		   if(tab == "labs"){
			// alert()
			data.forEach(element => {
				frappe.db.get_doc("Lab Result" , element.name).then( r => {
					if(r.template == "CBC"){
						lab_data.push({"date": r.date , "practitioner": r.practitioner, "test": "CBC"})
 
					}
					
					r.normal_test_items.forEach(result => {

						lab_data.push({"date": r.date , "practitioner": r.practitioner, "test": result.test ,"lab_test_name":result.lab_test_name , "lab_test_event" : result.lab_test_event , "result_value" : result.result_value, "normal_range" : result.normal_range})
 
					})
				})
				
			});
			setTimeout(() => {
			
				columns = [{title : "Date" , field : "date"},{title : "Practitioner" , field : "practitioner"},{title : "Test" , field : "test"} , {title : "Test Name" , field : "lab_test_name"} ,  {title : "Event" , field : "lab_test_event"} , {title : "Result" , field : "result_value"}, {title: "Normal Range", field: "normal_range"}  ]
				setup_datatable(columns , lab_data , "date" , tab)
			   }, 1000);
		   }
		   else if (tab == "doctor_progress_note"){
			// alert()
			let prog_htm = progress_note(data)
			$('#doctor_progress_note').html(prog_htm)
			// console.log(prog_htm)
		   }
		   else if (tab == "nursing_progress_note"){
			// alert()
			let prog_htm = progress_note(data)
			$('#nursing_progress_note').html(prog_htm)
			// console.log(prog_htm)
		   }
		   else if (tab == "doctor_plan"){
			
			let note_row = ``;
			let note_html= ``;
			let drug_row = ``;
			let drug_html= ``;

			let lab_html=``;
			let lab_row =``;
			let imaging_html=``;
			let imaging_row =``;

			let procedure_html=``;
			let procedure_row =``;

			
		
			frappe.db.get_doc('Doctor Plan', data[0].name)
			.then(doc => {
				if (doc.note){
					doc.note.forEach((el) => {
						note_row += `
				
						<tr>
						
						<td class="td--1">
						  ${el.date}
						</td> 
						<td class="td--2">
						  <strong>${el.by}</strong>
						</td> 
						
						<td class="td--3">
						<strong>${el.note || ""}</strong>
					  </td> 
					  
						</tr>
				
							`;
							
						
					  });
					  if(note_row){
						note_html += `
						
						<style>
					
					/*****************************************
					 truncate styles
					******************************************/
					.table-truncate {
					position: relative;
					}
					
					.table-truncate__body {
					position: absolute;
					max-width: 95%;
					white-space: nowrap;
					overflow: hidden;         
					text-overflow: ellipsis;
					}
					
					/*****************************************
					 just some design styles
					*****************************progress_note*************/
					body {
					font-family: 'helvetica neue', 'arial', sans-serif;
					
					}
					
					table {
					width: 100%;
					border-collapse: collapse;
					color: #262626;
					background: #fff;
					}
					
					
					td {
					padding: 15px;
					border: 1px solid #262626;
					}
					
					.td--1 {
					width: 15%;
					}
					
					.td--2 {
					width: 10%;
					}
					
					.qty {
					width: 10%;
					vertical-align: top;
					}
					.comment {
						width: 35%;
						vertical-align: top;
						}
					
					</style>
					<table>
					<tr>
					<td class="td--1" style="text-align:left; background:grey; color:white">
					Date
					</td> 
					<td class="td--2" style="text-align:left; background:grey; color:white">
					User
					</td> 
					<td class="td--3" style="text-align:left; background:grey; color:white">
					Note
					</td> 
				
					

					
					
					</tr>
					${note_row}
					</table> 
						`

					  }
					 
					
				
				}

				if (doc.drug_prescription){
					doc.drug_prescription.forEach((el) => {
						drug_row += `
				
						<tr>
						<td class="td--1">
						  ${el.date}
						</td> 
						<td class="td--1">
						  ${el.drug_code}
						</td> 
						<td class="td--2">
						  <strong>${el.dosage}</strong>
						</td> 
						<td class="qty">
						${el.quantity}
							</td>

							<td class="td--4">
						${el.period}
							</td>

							<td class="td--5">
						${el.dosage_form}
							</td>

							<td class="comment">
						${el.comment || ""}
							</td>
							
						</tr>
				
							`;
							
						
					  });
					  if(drug_row){
						drug_html += `
						
							<style>
						
						/*****************************************
						 truncate styles
						******************************************/
						.table-truncate {
						position: relative;
						}
						
						.table-truncate__body {
						position: absolute;
						max-width: 95%;
						white-space: nowrap;
						overflow: hidden;         
						text-overflow: ellipsis;
						}
						
						/*****************************************
						 just some design styles
						*****************************progress_note*************/
						body {
						font-family: 'helvetica neue', 'arial', sans-serif;
						
						}
						
						table {
						width: 100%;
						border-collapse: collapse;
						color: #262626;
						background: #fff;
						}
						
						
						td {
						padding: 15px;
						border: 1px solid #262626;
						}
						
						.td--1 {
						width: 15%;
						}
						
						.td--2 {
						width: 10%;
						}
						
						.qty {
						width: 10%;
						vertical-align: top;
						}
						.comment {
							width: 35%;
							vertical-align: top;
							}
						
						</style>
						<table>
						<tr>
						<td class="td--1" style="text-align:left; background:grey; color:white">
						Date 
						</td> 
						<td class="td--1" style="text-align:left; background:grey; color:white">
						Drug Name 
						</td> 
						<td class="td--2" style="text-align:left; background:grey; color:white">
						Dosage
						</td> 
						<td class="qty table-truncate" style="text-align:left; background:grey; color:white">
						Qty
						</td>

						<td class="td--4 table-truncate" style="text-align:left; background:grey; color:white">
						Period
						</td>

						<td class="td--5 table-truncate" style="text-align:left; background:grey; color:white"> 
						Frequency
						</td>
						<td class="comment table-truncate" style="text-align:left; background:grey; color:white"> 
						Comment
						</td>
						
						</tr>
						${drug_row}
						</table> 
							`
					  }
					  

				}

				if (doc.lab_tests){
					doc.lab_tests.forEach((el) => {
						lab_row += `
				
						<tr>
						
						<td class="td--1">
						  ${el.lab_test_code}
						</td> 
						<td class="td--2">
						  <strong>1</strong>
						</td> 
						
							
						</tr>
				
							`;
							
						
					  });
					  if(lab_row){
						lab_html += `
						
							<style>
						
						/*****************************************
						 truncate styles
						******************************************/
						.table-truncate {
						position: relative;
						}
						
						.table-truncate__body {
						position: absolute;
						max-width: 95%;
						white-space: nowrap;
						overflow: hidden;         
						text-overflow: ellipsis;
						}
						
						/*****************************************
						 just some design styles
						*****************************progress_note*************/
						body {
						font-family: 'helvetica neue', 'arial', sans-serif;
						
						}
						
						table {
						width: 100%;
						border-collapse: collapse;
						color: #262626;
						background: #fff;
						}
						
						
						td {
						padding: 15px;
						border: 1px solid #262626;
						}
						
						.td--1 {
						width: 15%;
						}
						
						.td--2 {
						width: 10%;
						}
						
						.qty {
						width: 10%;
						vertical-align: top;
						}
						.comment {
							width: 35%;
							vertical-align: top;
							}
						
						</style>
						<table>
						<tr>
						<td class="td--1" style="text-align:left; background:grey; color:white">
						Test Name 
						</td> 
						<td class="td--2" style="text-align:left; background:grey; color:white">
						Qty
						</td> 
					
						

						
						
						</tr>
						${lab_row}
						</table> 
							`
					  }
					  

				}

				if (doc.imaging){
					doc.imaging.forEach((el) => {
						imaging_row += `
				
						<tr>
						
						<td class="td--1">
						  ${el.image}
						</td> 
						<td class="td--2">
						  <strong>1</strong>
						</td> 
						
						<td class="td--3">
						<strong>${el.lab_test_comment || ""}</strong>
					  </td> 
					  
						</tr>
				
							`;
							
						
					  });
					  if(imaging_row){
						imaging_html += `
						
						<style>
					
					/*****************************************
					 truncate styles
					******************************************/
					.table-truncate {
					position: relative;
					}
					
					.table-truncate__body {
					position: absolute;
					max-width: 95%;
					white-space: nowrap;
					overflow: hidden;         
					text-overflow: ellipsis;
					}
					
					/*****************************************
					 just some design styles
					*****************************progress_note*************/
					body {
					font-family: 'helvetica neue', 'arial', sans-serif;
					
					}
					
					table {
					width: 100%;
					border-collapse: collapse;
					color: #262626;
					background: #fff;
					}
					
					
					td {
					padding: 15px;
					border: 1px solid #262626;
					}
					
					.td--1 {
					width: 15%;
					}
					
					.td--2 {
					width: 10%;
					}
					
					.qty {
					width: 10%;
					vertical-align: top;
					}
					.comment {
						width: 35%;
						vertical-align: top;
						}
					
					</style>
					<table>
					<tr>
					<td class="td--1" style="text-align:left; background:grey; color:white">
					Radiology Name 
					</td> 
					<td class="td--2" style="text-align:left; background:grey; color:white">
					Qty
					</td> 
					<td class="td--3" style="text-align:left; background:grey; color:white">
					Comment
					</td> 
				
					

					
					
					</tr>
					${imaging_row}
					</table> 
						`

					  }
					 

				}

				if (doc.clinical_procedures){
					doc.clinical_procedures.forEach((el) => {
						procedure_row += `
				
						<tr>
						
						<td class="td--1">
						  ${el.procedure}
						</td> 
						<td class="td--2">
						  <strong>1</strong>
						</td> 
						
						<td class="td--3">
						<strong>${el.comments || ""}</strong>
					  </td> 
					  
						</tr>
				
							`;
							
						
					  });
					  if(procedure_row){
						procedure_html += `
						
						<style>
					
					/*****************************************
					 truncate styles
					******************************************/
					.table-truncate {
					position: relative;
					}
					
					.table-truncate__body {
					position: absolute;
					max-width: 95%;
					white-space: nowrap;
					overflow: hidden;         
					text-overflow: ellipsis;
					}
					
					/*****************************************
					 just some design styles
					*****************************progress_note*************/
					body {
					font-family: 'helvetica neue', 'arial', sans-serif;
					
					}
					
					table {
					width: 100%;
					border-collapse: collapse;
					color: #262626;
					background: #fff;
					}
					
					
					td {
					padding: 15px;
					border: 1px solid #262626;
					}
					
					.td--1 {
					width: 15%;
					}
					
					.td--2 {
					width: 10%;
					}
					
					.qty {
					width: 10%;
					vertical-align: top;
					}
					.comment {
						width: 35%;
						vertical-align: top;
						}
					
					</style>
					<table>
					<tr>
					<td class="td--1" style="text-align:left; background:grey; color:white">
					Procedure Name 
					</td> 
					<td class="td--2" style="text-align:left; background:grey; color:white">
					Qty
					</td> 
					<td class="td--3" style="text-align:left; background:grey; color:white">
					Comment
					</td> 
				
					

					
					
					</tr>
					${procedure_row}
					</table> 
						`

					  }
					 

				}
				// console.log(note_html)
				// return note_html
				
				$('#procedure_doctor_plan').html(imaging_html)
				$('#image_doctor_plan').html(imaging_html)

				$('#lab_doctor_plan').html(lab_html)
				
				$('#drug_doctor_plan').html(drug_html)
				$('#doctor_note').html(note_html)
			})
			
			// setTimeout(() => {
			// 	let notes = doctorplan(data);
			// 	$('#doctor_note').html(notes)
			// 	console.log(notes)
			//   }, 5000);
			
			// setTimeout(() => {
				
			 
			  
			
			
		   }
			else{
			if(columns){
			
				setup_datatable(columns , data , "date", tab)
			}
			else{
				
				setup_datatable([] , [] , "date", tab)

			}
			
		}
        }})



// 	frappe.call({
// 		method: "his.api.vitals.get_vital", //dotted path to server method
// 		args :{ "patient": patient
// 			},
// 		callback: function(r) {
			
// 			tbldata = r.message
	
   

			
		
// 		 let me = this
// 		//  let fields = frappe.get_meta("Sales Order").fields
// 			let columns = [
// 			// {title:"ID", field:"name"},
// 			// {title:"Patient", field:"customer"},
// 			{title:"Date / Time", field:"modified"},
// 			{title:"Temperature", field:"temperature"},
// 			{title:"Pulse", field:"pulse"},
// 			{title:"BP", field:"bp"},
// 			{title:"Respiration", field:"respiratory_rate"},
// 			{title:"SpO2", field:"spo"},
// 			{title:"Height", field:"height"},
// 			{title:"Weight", field:"weight"},
// 			{title:"BMI", field:"bmi"},
// 			{title:"Nurse", field:"owner"},
			
// 			// {title:"Action", field:"action", hozAlign:"center" , formatter:"html"},
			
// 		 ]
	


//
// this.table = new Tabulator("#vitals", {
// 			// layout:"fitDataFill",
// 			layout:"fitDataStretch",
// 			//  layout:"fitColumns",
// 			// responsiveLayout:"collapse",
// 			 rowHeight:30, 
// 			//  selectable:true,
// 			//  dataTree:true,
// 			//  dataTreeStartExpanded:true,
// 			 groupStartOpen:false,
// 			 printAsHtml:true,
// 			//  printHeader:`<img src = '/private/files/WhatsApp Image 2022-10-20 at 6.19.02 PM.jpeg'>`,
// 			//  printFooter:"<h2>Example Table Footer<h2>",
// 			 // groupBy:"customer",
// 			 groupHeader:function(value, count, data, group){
// 				 //value - the value all members of this group share
// 				 //count - the number of rows in this group
// 				 //data - an array of all the row data objects in this group
// 				 //group - the group component for the group
// 			
// 				 return value + "<span style=' margin-left:0px;'>(" + count + "   )</span>";
// 			 },
// 			 groupToggleElement:"header",
// 			//  groupBy:groupbyD.length >0 ? groupbyD : "",
// 			 textDirection: frappe.utils.is_rtl() ? "rtl" : "ltr",
	 
// 			 columns: columns,
			 
		
			 
// 			 data: new_data
// 		 });
		 

// 		}
	
// });
}

function setup_datatable(columns , data , group , tabid){
	
	let doctypes = {"vitals" : "Vital Signs" , "drug_sheet" :"Inpatient Medication" , "imaging" : "Radiology" , "operation" : "Clinical Procedure" , "blood_transfusion" : "Healthcare Requests"}  
	// console.log(data)

	// alert(tabid)
	let groupBy = []
	if(group){
		groupBy.push(group)
	}

	let table = new Tabulator(`#${tabid}`, {
		// layout:"fitDataFill",
		layout:"fitDataFill",
		//  layout:"fitColumns",
		// responsiveLayout:"collapse",
		 rowHeight:30, 
		 placeholder:"No Data Available",
		//  selectable:true,
		//  dataTree:true,
		//  dataTreeStartExpanded:true,
		 groupStartOpen:false,
		 printAsHtml:true,
		//  printHeader:`<img src = '/private/files/WhatsApp Image 2022-10-20 at 6.19.02 PM.jpeg'>`,
		 printFooter:"<h2>Example Table Footer<h2>",
		 groupBy:groupBy,
		 groupHeader:function(value, count, data, group){
			 //value - the value all members of this group share
			 //count - the number of rows in this group
			 //data - an array of all the row data objects in this group
			 //group - the group component for the group
		
			 return value + "<span style=' margin-left:0px;'>(" + count + "   )</span>";
		 },
		 groupToggleElement:"header",
		//  groupBy:groupbyD.length >0 ? groupbyD : "",
		//  textDirection: frappe.utils.is_rtl() ? "rtl" : "ltr",
 
		 columns: columns,
		 
		 // [
		 // 	{formatter:"rowSelection", titleFormatter:"rowSelection", hozAlign:"center", headerSort:false, cellClick:function(e, cell){
		 // 		cell.getRow().toggleSelect();
		 // 	  }},
		 // 	{
		 // 		title:"Name", field:"name", width:200,
		 // 	},
		 // 	{title:"Group", field:"item_group", width:200},
		 // ],
		 // [
		 // {title:"Name", field:"name" , formatter:"link" , formatterParams:{
		 // 	labelField:"name",
		 // 	urlPrefix:`/app/${doct}/`,
			 
		 // }},
		 // {title:"Customer", field:"customer" },
		 // {title:"Total", field:"net_total" , bottomCalc:"sum",},
	 
		 // ],
		 
		 data: data
	 });
	 let row = this
	 table.on("rowClick", function(e ,rows){
	
		
		 frappe.set_route("Form" ,doctypes[tabid] ,  rows._row.data.sr)
	   });
}

let transfer_patient_dialog = function(frm) {
	let inp_record = frappe.db.get_value("Inpatient Record" , {"patient" : frm.doc.patient , "status": "Admitted"},"name")
	inp_record.then( inp  => {
		frappe.db.get_doc("Inpatient Record" , inp.message.name)
		.then( ip => {
			
			let dialog = new frappe.ui.Dialog({

				title: 'Transfer Patient',
				width: 100,
				fields: [
					{fieldtype: 'Link', label: 'Inpatient Type', fieldname: 'inpatient_type', default: ip.type, options: 'Inpatient Type', reqd: 1, read_only:0},
					{fieldtype: 'Link', label: 'Leave From', fieldname: 'leave_from', options: 'Healthcare Service Unit', reqd: 1, read_only:1},
					{fieldtype: 'Link', label: 'Service Unit Type', fieldname: 'service_unit_type', options: 'Healthcare Service Unit Type'},
					{fieldtype: 'Link', label: 'Transfer To', fieldname: 'service_unit', options: 'Healthcare Service Unit', reqd: 1},
					{fieldtype: 'Datetime', label: 'Check In', fieldname: 'check_in', reqd: 1, default: frappe.datetime.now_datetime()}
				],
				primary_action_label: __('Transfer'),
				primary_action : function() {
					let service_unit = null;
					let check_in = dialog.get_value('check_in');
					let leave_from = null;
					let in_type = dialog.get_value('inpatient_type');
					
					if(dialog.get_value('leave_from')){
						leave_from = dialog.get_value('leave_from');
					}
					if(dialog.get_value('service_unit')){
						service_unit = dialog.get_value('service_unit');
					}
					if(check_in > frappe.datetime.now_datetime()){
						frappe.msgprint({
							title: __('Not Allowed'),
							message: __('Check-in time cannot be greater than the current time'),
							indicator: 'red'
						});
						return;
					}
					
					frappe.call({
						// doc: frm.doc,
						method: 'his.api.transfer_ip.transfer_ip',
						args:{
							'self' : ip.name,
							'service_unit': service_unit,
							'check_in': check_in,
							'leave_from': leave_from,
							"inpatient_type": in_type
						},
						callback: function(data) {
				
							frappe.db.get_value("Healthcare Service Unit" , service_unit , ["service_unit_type", 'name'])
							.then( room => {
								
								let ip_room = room.message.service_unit_type
								let bed = room.message.name

								// frappe.db.set_value("Inpatient Record" , ip.name , {"bed" : bed ,"room" : ip_room })
								// frappe.db.set_value("Inpatient Record" , ip.name , "room" , ip_room)
								// frappe.db.set_value("Inpatient Record" , ip.name , "type" , dialog.get_value('inpatient_type'))

								
								// ip.bed = service_unit
								// ip.save()
							})
							// if (!data.exc) {
							// 	frm.reload_doc();
							// }
						},
						freeze: true,
						freeze_message: __('Process Transfer')
					});
					// frm.refresh_fields();
					dialog.hide();
				}
			});
		
			dialog.fields_dict['leave_from'].get_query = function(){
				return {
					query : 'healthcare.healthcare.doctype.inpatient_record.inpatient_record.get_leave_from',
					filters: {docname:frm.doc.name}
				};
			};
			dialog.fields_dict['service_unit_type'].get_query = function(){
				return {
					filters: {
						'inpatient_occupancy': 1,
						'allow_appointments': 0
					}
				};
			};
			dialog.fields_dict['service_unit'].get_query = function(){
				return {
					filters: {
						'is_group': 0,
						'service_unit_type': dialog.get_value('service_unit_type'),
						'occupancy_status' : 'Vacant'
					}
				};
			};
		
			dialog.show();
		
			let not_left_service_unit = null;
			for (let inpatient_occupancy in ip.inpatient_occupancies) {
				if (ip.inpatient_occupancies) {
				
					not_left_service_unit = ip.inpatient_occupancies[inpatient_occupancy].service_unit;
				}
			}
		
			
			dialog.set_values({
				'leave_from': not_left_service_unit
			});

		})
	})
	



	
		

};


let refer = function(frm) {
	let inp_record = frappe.db.get_value("Inpatient Record" , {"patient" : frm.doc.patient , "status": "Admitted"},"name")
	inp_record.then( inp  => {
		frappe.db.get_doc("Inpatient Record" , inp.message.name)
		.then( ip => {
			// console.log(ip.name);
			let d = new frappe.ui.Dialog({
				title: 'Refer Doctor',
				fields: [
					{
						label: 'Consultant',
						fieldname: 'practitioner',
						fieldtype: 'Link',
						options : "Healthcare Practitioner",
						reqd : 1
					}
				
				],
				size: 'small', // small, large, extra-large 
				primary_action_label: 'Submit',
				primary_action(values) {
					d.hide();
					// console.log()
						// let inpatient_rec = frappe.get_doc('Inpatient Record', ip.name)
						// inpatient_rec.ref_practitioner = "Dr Mohamed Dahir Aden"
						// inpatient_rec.save()

						frappe.call({
							method: 'his.his.doctype.patient_history.patient_history.refer',
							args: {
								'inpatient_record': ip.name,
								'practitioner' : values.practitioner
								
								
							},
							callback: function(r) {
								
								// console.log(r)
								// if (!r.exc) {
								// 	// code snippet
								// }
							}
						});
						
				}
				 
			});
			
			d.show();
			

		})
		
	})
}



function progress_note(data){
	// console.log(data)
	let row = ``
	data.forEach( d => {

		row += `
		
		<tr>
		<td class="td--1">
		  <strong>${d.date}</strong>
		</td> 
		<td class="td--2">
		  ${d.user}
		</td> 
		<td class="td--3">
		${d.note}
			</td>
		</tr>

		`
		
	})
	let html = `
	
	<style>
  
  /*****************************************
 truncate styles
******************************************/
.table-truncate {
   position: relative;
}

.table-truncate__body {
  position: absolute;
  max-width: 95%;
  white-space: nowrap;
  overflow: hidden;         
  text-overflow: ellipsis;
}

/*****************************************
 just some design styles
*****************************progress_note*************/
body {
  font-family: 'helvetica neue', 'arial', sans-serif;

}

table {
  width: 100%;
  border-collapse: collapse;
  color: #262626;
  background: #fff;
}

td {
  padding: 15px;
  border: 1px solid #262626;
}

.td--1 {
  width: 15%;
}

.td--2 {
  width: 10%;
}

.td--3 {
  width: 50%;
  vertical-align: top;
}
</style>
<table>
<tr>
<td class="td--1">
  Date 
</td> 
<td class="td--2">
  User
</td> 
<td class="td--3 table-truncate">
 Note
</td>
</tr>
 ${row}
</table> 
	`

	return html
}



function doctorplan(data){
	let note_row = ``;
	let note_html= ``;

	frappe.db.get_doc('Doctor Plan', data[0].name)
    .then(doc => {
		if (doc.comment){
			
			// alert(doc.comment)
			
			note_row += `
		
		<tr>
		<td class="td--1">
		  <strong>${frappe.session.user}</strong>
		</td> 
		<td class="td--2">
		  ${doc.date}
		</td> 
		<td class="td--3">
		${doc.comment}
			</td>
		</tr>

			`;
			note_html += `
		
			<style>
		
		/*****************************************
		 truncate styles
		******************************************/
		.table-truncate {
		position: relative;
		}
		
		.table-truncate__body {
		position: absolute;
		max-width: 95%;
		white-space: nowrap;
		overflow: hidden;         
		text-overflow: ellipsis;
		}
		
		/*****************************************
		 just some design styles
		*****************************progress_note*************/
		body {
		font-family: 'helvetica neue', 'arial', sans-serif;
		
		}
		
		table {
		width: 100%;
		border-collapse: collapse;
		color: #262626;
		background: #fff;
		}
		
		td {
		padding: 15px;
		border: 1px solid #262626;
		}
		
		.td--1 {
		width: 15%;
		}
		
		.td--2 {
		width: 10%;
		}
		
		.td--3 {
		width: 50%;
		vertical-align: top;
		}
		</style>
		<table>
		<tr>
		<td class="td--1">
		Date 
		</td> 
		<td class="td--2">
		User
		</td> 
		<td class="td--3 table-truncate">
		Note
		</td>
		</tr>
		${note_row}
		</table> 
			`
		
		}
		// console.log(note_html)
		return note_html
    })
	
		
}
let calculate_age = function(birth) {
    let birthDate = new Date(birth);
    let today = new Date();

    let years = today.getFullYear() - birthDate.getFullYear();
    let months = today.getMonth() - birthDate.getMonth();
    let days = today.getDate() - birthDate.getDate();

    // Adjust for negative days
    if (days < 0) {
        months--;
        // Get total days in previous month
        let prevMonth = new Date(today.getFullYear(), today.getMonth(), 0);
        days += prevMonth.getDate();
    }

    // Adjust for negative months
    if (months < 0) {
        years--;
        months += 12;
    }

    return `${years} Year(s) ${months} Month(s) ${days} Day(s)`;
};

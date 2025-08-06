// Copyright (c) 2024, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Healthcare Requests', {

	    select_lab_tests: function(frm){
        select_lab_tests(frm)
    },

    select_imaging: function(frm){
        // alert("ok")
        select_imaging(frm)
    },
	practitioner: function(frm) {
	    let hide_field = frm.doc.medical_department != "Dental"
            
		// Hide the "rate" column completely from the grid
		frm.fields_dict["services_prescription"].grid.update_docfield_property("rate", "hidden", hide_field);

		// Refresh the grid to apply the change
		frm.fields_dict["services_prescription"].grid.refresh();
	},
	refresh: function(frm) {
		let html = `
		
		<style>
	
		.container_rd {
		  max-width: 1200px;
		  /* margin: 0 auto; */
		  /* padding: 20px; */
		  /* border: 1px solid #ccc;
		  border-radius: 5px; */
		}
		h1 {
		  text-align: center;
		}
		label {
		  font-weight: bold;
		}
		input[type="text"],
		input[type="number"],
		select {
		  width: 100%;
		  padding: 8px;
		  margin-bottom: 10px;
		  border: 1px solid #ccc;
		  border-radius: 3px;
		}
		.title {
		  text-align: center; /* Centers the content horizontally */
		}
  
		.title h1 {
		  display: inline-block;
		  background-color: #ccc;
		}
  
		.checkbox-group {
		  display: flex;
		  flex-direction: column;
		  gap: 10px;
		}
  
		textarea {
		  width: 100%;
		  height: 100px;
		  padding: 8px;
		  margin-bottom: 10px;
		  border: 1px solid #ccc;
		  border-radius: 3px;
		}
		button {
		  background-color: #0074d9;
		  color: #fff;
		  border: none;
		  padding: 10px 20px;
		  border-radius: 3px;
		  cursor: pointer;
		}
		.patientNames {
		  display: flex;
		  align-items: center;
		}
		.patientNames h3 {
		  padding: 0;
		  margin: 0;
		}
		.patientNames span {
		  padding: 0;
		  margin: 0;
		}
	
		.logo {
		  width: 400px;
		}
		.info_continer {
		  padding: 1rem;
		  border: 2px solid black;
		}
		.checkbox-table {
		  width: 100%;
		  border-collapse: collapse;
		  text-align: center; /* Center align for aesthetics */
		  margin-bottom: 20px; /* Space between tables */
		}
  
		.checkbox-column,
		.label-column {
		  border: 1px solid black;
		  padding: 8px;
		}
  
		.modality-checkbox {
		  /* Additional styling for checkboxes can go here */
		  cursor: pointer; /* Indicate that the element is clickable */
		  margin-bottom: 4px; /* Space between checkbox and label */
		}
  
		.modality-label {
		  display: block; /* Ensures the label takes its own line */
		  cursor: pointer; /* Indicate that the element is clickable */
		}
		.subtitle_label {
		  width: fit-content;
		  font-size: 16px;
		  padding: 5px;
		  background-color: #ccc;
		}
		.signture {
		  display: flex;
		  justify-content: space-between;
		  margin-bottom: 15px;
		}
		.signture span {
		  font-size: 18px;
		  font-weight: bold;
		}
  
		.empty-lines {
		  border: 1px solid black;
		  height: 100px;
		  overflow: hidden;
		}
		.empty-lines span {
		  color: #ccc;
		  line-height: 20px;
		  padding: 5px;
		}
		.examination-table {
		  width: 100%;
		  border-collapse: collapse;
		  margin-bottom: 20px;
		  table-layout: fixed; /* Fixed layout for even column spacing */
		}
		.examination-table th,
		.examination-table td {
		  border: 1px solid black;
		  padding-left: 5px;
		  padding-right: 5px;
		}
		.examination-table th {
		  background-color: #f2f2f2;
		  text-align: left;
		}
		.left-column,
		.right-column {
		  width: 50%;
		}
		.input-line {
		  width: 100%;
		  border: none;
		  border-bottom: 1px solid black;
		  /* padding: 2px; */
		  /* margin-top: 2px; */
		}
		.input-block {
		  margin: 5px 0;
		}
		.check-in-out {
		  display: flex;
		  justify-content: space-between;
		}
		.check-in-out div {
		  width: 48%;
		}
		.request-form-table {
		  width: 100%;
		  border-collapse: collapse;
		}
  
		.request-form-table th,
		.request-form-table td {
		  border: 1px solid black;
		  padding: 8px;
		  text-align: left;
		}
	  </style>
		<div class="container_rd">
		
		<div class="checkbox-group">
		  <label class="subtitle_label">Requested Modality:</label>
		  <table class="checkbox-table">
			<tr class="checkbox-row">
			  <!-- Repeat this block for each modality -->
			  <th class="checkbox-column">
				<input
				  type="checkbox"
				  id="USI"
				  value="USI"
				  class="modality-checkbox"
				/>
			  </th>
			  <th class="checkbox-column">
				<input
				  type="checkbox"
				  id="US"
				  value="US"
				  class="modality-checkbox"
				/>
			  </th>
			  <th class="checkbox-column">
				<input
				  type="checkbox"
				  id="FLU"
				  value="FLU"
				  class="modality-checkbox"
				/>
			  </th>
			  <th class="checkbox-column">
				<input
				  type="checkbox"
				  id="CT"
				  value="CT"
				  class="modality-checkbox"
				/>
			  </th>
			  <th class="checkbox-column">
				<input
				  type="checkbox"
				  id="MRI"
				  value="MRI"
				  class="modality-checkbox"
				/>
			  </th>
			  <th class="checkbox-column">
				<input
				  type="checkbox"
				  id="MAMMO"
				  value="MAMMO"
				  class="modality-checkbox"
				/>
			  </th>
			  <th class="checkbox-column">
				<input
				  type="checkbox"
				  id="BMD"
				  value="BMD"
				  class="modality-checkbox"
				/>
			  </th>
			  <th class="checkbox-column">
				<input
				  type="checkbox"
				  id="ANGIO"
				  value="ANGIO"
				  class="modality-checkbox"
				/>
			  </th>
			  <th class="checkbox-column">
				<input
				  type="checkbox"
				  id="NM"
				  value="NM"
				  class="modality-checkbox"
				/>
			  </th>
			  <th class="checkbox-column">
				<input
				  type="checkbox"
				  id="OTHERS"
				  value="OTHERS"
				  class="modality-checkbox"
				/>
			  </th>
			  <!-- ... Other checkbox th elements -->
			</tr>
			<tr class="label-row">
			  <!-- Repeat this block for each modality label -->
			  <td class="label-column">
				<label for="USI" class="modality-label">USI</label>
			  </td>
			  <td class="label-column">
				<label for="US" class="modality-label">US</label>
			  </td>
			  <td class="label-column">
				<label for="FLU" class="modality-label">FLU</label>
			  </td>
			  <td class="label-column">
				<label for="CT" class="modality-label">CT</label>
			  </td>
			  <td class="label-column">
				<label for="MRI" class="modality-label">MRI</label>
			  </td>
			  <td class="label-column">
				<label for="MAMMO" class="modality-label">MAMMO</label>
			  </td>
			  <td class="label-column">
				<label for="BMD" class="modality-label">BMD</label>
			  </td>
			  <td class="label-column">
				<label for="ANGIO" class="modality-label">ANGIO</label>
			  </td>
			  <td class="label-column">
				<label for="NM" class="modality-label">NM</label>
			  </td>
			  <td class="label-column">
				<label for="OTHERS" class="modality-label">OTHERS</label>
			  </td>
			  <!-- ... Other label td elements -->
			</tr>
			<!-- ... Other rows if needed -->
		  </table>
		</div>
		<div class="checkbox-group">
		  <label class="subtitle_label">Requested Modality:</label>
		  <table class="checkbox-table">
			<tr class="checkbox-row">
			  <th class="checkbox-column">
				<input
				  type="checkbox"
				  id="Priority"
				  value="Priority"
				  class="modality-checkbox"
				/>
			  </th>
			  <th class="checkbox-column">
				<input
				  type="checkbox"
				  id="Routine"
				  value="Routine"
				  class="modality-checkbox"
				/>
			  </th>
			  <th class="checkbox-column">
				<input
				  type="checkbox"
				  id="ASAP"
				  value="ASAP"
				  class="modality-checkbox"
				/>
			  </th>
			  <th class="checkbox-column">
				<input
				  type="checkbox"
				  id="STAT"
				  value="STAT"
				  class="modality-checkbox"
				/>
			  </th>
			</tr>
			<tr class="label-row">
			  <td class="label-column">
				<label for="Priority" class="modality-label">Priority</label>
			  </td>
			  <td class="label-column">
				<label for="Routine" class="modality-label">Routine</label>
			  </td>
			  <td class="label-column">
				<label for="ASAP" class="modality-label">ASAP</label>
			  </td>
			  <td class="label-column">
				<label for="STAT" class="modality-label">STAT</label>
			  </td>
			</tr>
		  </table>
		</div>
  
		<table style="border-collapse: collapse; width: 100%">
		  <label class="subtitle_label">State of Patient:</label>
		  <tr>
			<td style="border: 1px solid black; padding: 5px; font-weight: bold">
			  Patient Category
			</td>
			<td colspan="5" style="border: 1px solid black; padding: 5px">
			  ED &nbsp; <input type="checkbox" /> &nbsp; &nbsp; &nbsp; OPD
			  &nbsp;<input type="checkbox" />&nbsp; &nbsp; &nbsp; Inpatient &nbsp;
			  <input type="checkbox" /> &nbsp; &nbsp; &nbsp; External referral
			  &nbsp; <input type="checkbox" />
			</td>
		  </tr>
		  <tr>
			<td style="border: 1px solid black; padding: 5px; font-weight: bold">
			  Pregnant Status
			</td>
			<td colspan="5" style="border: 1px solid black; padding: 5px">
			  Yes &nbsp; <input type="checkbox" /> &nbsp; &nbsp; &nbsp; LMP Date:
			  &nbsp;<input type="checkbox" />&nbsp; &nbsp; &nbsp; Not Sure &nbsp;
			  <input type="checkbox" /> &nbsp; &nbsp; &nbsp; No &nbsp;
			  <input type="checkbox" />
			</td>
		  </tr>
		  <tr>
			<td style="border: 1px solid black; padding: 5px; font-weight: bold">
			  Patient Mobility
			</td>
			<td colspan="5" style="border: 1px solid black; padding: 5px">
			  ED &nbsp; <input type="checkbox" /> &nbsp; &nbsp; &nbsp; OPD
			  &nbsp;<input type="checkbox" />&nbsp; &nbsp; &nbsp; Inpatient &nbsp;
			  <input type="checkbox" /> &nbsp; &nbsp; &nbsp; External referral
			  &nbsp; <input type="checkbox" />
			</td>
		  </tr>
		  <tr>
			<td style="border: 1px solid black; padding: 5px; font-weight: bold">
			  Transporting Patient
			</td>
			<td colspan="5" style="border: 1px solid black; padding: 5px">
			  Walking &nbsp; <input type="checkbox" /> &nbsp; &nbsp; &nbsp;
			  Stretcher &nbsp; <input type="checkbox" /> &nbsp; &nbsp; &nbsp;
			  Trolley &nbsp; <input type="checkbox" /> &nbsp; &nbsp; &nbsp;
			  Wheelchair &nbsp; <input type="checkbox" />
			</td>
		  </tr>
		  <tr>
			<td style="border: 1px solid black; padding: 5px; font-weight: bold">
			  Previous Radiological
			</td>
			<td colspan="5" style="border: 1px solid black; padding: 5px">
			  Yes &nbsp; <input type="checkbox" /> &nbsp; &nbsp; &nbsp; No
			  &nbsp;<input type="checkbox" />
			</td>
		  </tr>
		  <tr>
			<td style="border: 1px solid black; padding: 5px; font-weight: bold">
			  Viral Serology Tests Done:
			</td>
			<td colspan="5" style="border: 1px solid black; padding: 5px">
			  Yes &nbsp; <input type="checkbox" /> &nbsp; &nbsp; &nbsp; No
			  &nbsp;<input type="checkbox" /> &nbsp; &nbsp; &nbsp; HIV
			  &nbsp;<input type="checkbox" /> &nbsp; &nbsp; &nbsp; Hep
			  &nbsp;<input type="checkbox" /> &nbsp; &nbsp; &nbsp; Others
			  &nbsp;<input type="checkbox" />&nbsp; &nbsp; &nbsp; TB &nbsp;<input
				type="checkbox"
			  />
			</td>
		  </tr>
  
		  <tr>
			<td
			  colspan="6"
			  style="
				border: 1px solid black;
				padding: 5px;
				background-color: #ccc;
				font-weight: bold;
			  "
			>
			  Clinical Details : (History / Justification of Exam)
			</td>
		  </tr>
  
		  <tr>
			<td colspan="6" style="border: 1px solid black; padding: 13px"></td>
		  </tr>
		  <tr>
			<td colspan="6" style="border: 1px solid black; padding: 13px"></td>
		  </tr>
		  <tr>
			<td colspan="6" style="border: 1px solid black; padding: 13px"></td>
		  </tr>
		  <tr>
			<td colspan="6" style="border: 1px solid black; padding: 13px"></td>
		  </tr>
		  <tr>
			<td colspan="6" style="border: 1px solid black; padding: 13px"></td>
		  </tr>
		  <tr>
			<td
			  colspan="6"
			  style="
				border: 1px solid black;
				padding: 5px;
				background-color: #ccc;
				font-weight: bold;
			  "
			>
			  Clinical Details : (History / Justification of Exam)
			</td>
		  </tr>
  
		  <tr>
			<td colspan="6" style="border: 1px solid black; padding: 13px"></td>
		  </tr>
		  <tr>
			<td colspan="6" style="border: 1px solid black; padding: 13px"></td>
		  </tr>
		</table>
  
		<table class="examination-table">
		  <tr>
			<th colspan="2">
			  Exams Requiring Intravenous contrast: Creatinine
			  level:________________________________
			</th>
		  </tr>
		  <tr>
			<td class="left-column">
			  <div>
				Does the patient have asthma
				<input type="checkbox" name="asthma" value="Yes" /> Yes
				<input type="checkbox" name="asthma" value="No" /> No
			  </div>
			  <div>
				In case of history of allergy of contrast media please contact
				Radiology Department after eventual appropriate allergy
				consultation
			  </div>
			  <div>
				Is the patient taking any diuretics
				<input type="checkbox" name="diuretics" value="Yes" /> Yes
				<input type="checkbox" name="diuretics" value="No" /> No
			  </div>
			</td>
			<td class="right-column">
			  <div>
				The patient does take metformin
				<input type="checkbox" name="metformin" value="Yes" /> Yes
				<input type="checkbox" name="metformin" value="No" /> No
			  </div>
			  <div>
				(Glucophage® Stagid®, Etc)
				<input type="checkbox" name="metformin" value="Yes" /> Yes
				<input type="checkbox" name="metformin" value="No" /> No
			  </div>
			  <div style="padding: 15px 0">
				<span style="font-weight: bold"
				  >Do not take the medication on the day of exam and do that again
				  after 48hrs if renal function is normal
				</span>
			  </div>
			  <div>
				<span
				  >If the answer is yes: Creatinine clearance: _____ ml/min al
				</span>
			  </div>
			</td>
		  </tr>
		  <tr>
			<th
			  style="
				font-weight: normal;
				font-size: 18px;
				background-color: white;
			  "
			  colspan="2"
			>
			  In all cases to ensure proper hydration of the patient (2-3
			  liter/day) in case of renal failure, beside dehydration, preferably
			  via venous route, please prescribe acetylcysteine (Mucomyst®) 600 mg
			  orally 2 times a day; the day before and on the day of the iodine
			  injection
			</th>
		  </tr>
		  <tr>
			<th colspan="2">For Radiology Department use:</th>
		  </tr>
		  <tr>
			<td class="left-column">
			  <div>
				<span>Receptionist Name: _____________________________ </span>
			  </div>
			</td>
			<td class="right-column">
			  <div
				style="
				  display: flex;
				  gap: 10px;
				  flex-direction: column;
				  padding-bottom: 10px;
				"
			  >
				<span>(RT) Name:______________________________________ </span>
				<span> Examination Done:_________________________ </span>
			  </div>
  
			  <div style="display: flex; gap: 100px">
				<span>Check out Time: </span>
				<span>Check out Time: </span>
			  </div>
			</td>
		  </tr>
		</table>
		<table class="request-form-table">
		  <tr>
			<td>
			  <span>Examination Appointment Date & Time:__________</span>
			</td>
			<td class="narrow-column">
			  <span>DAP:__________</span>
			</td>
			<td class="narrow-column">
			  <span>DAP:__________</span>
			</td>
			<td class="narrow-column">
			  <span>DAP:__________</span>
			</td>
		  </tr>
		</table>
	  </div>
		
		`


		// $('#rad_request_form').html(html)
		if (frm.fields_dict["services_prescription"]) {
            // let hide_field = !frappe.user_roles.includes("HR XX");
            let hide_field = frm.doc.medical_department != "Dental"
            
            // Hide the "rate" column completely from the grid
            frm.fields_dict["services_prescription"].grid.update_docfield_property("rate", "hidden", hide_field);

            // Refresh the grid to apply the change
            frm.fields_dict["services_prescription"].grid.refresh();
        }

	}
	
});
frappe.ui.form.on('Services Prescription', { 
    service: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.service) {
            frappe.db.get_value('Other Service', {'template': row.service}, 'rate')
                .then(r => {
                    if (r.message.rate) {
                        frappe.model.set_value(cdt, cdn, 'rate', r.message.rate);
                    }
                });
        }
		let hide_field = frm.doc.medical_department != "Dental"
            
		// Hide the "rate" column completely from the grid
		frm.fields_dict["services_prescription"].grid.update_docfield_property("rate", "hidden", hide_field);

		// Refresh the grid to apply the change
		frm.fields_dict["services_prescription"].grid.refresh();
    },
	
    
    
});
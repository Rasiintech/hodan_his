// Copyright (c) 2022, Rasiin and contributors
// For license information, please see license.txt

frappe.ui.form.on('Radiology', {
	refresh(frm) {
		add_sales_return_request_button(frm, "Radiology - HH");


frappe.db.get_list('File', {
    fields: ['file_url'],
    filters: {
        attached_to_name: frm.doc.name
    }
}).then(records => {
    let images='';
    records.forEach(im=>{
        images+=`\n<div class="col-4">
                    <img src="${im.file_url}" alt="Image" style="width:100% ; height: 80% ; padding : 10px ; border : 1px solid #000">
                  </div>`
    })
    	let img=`<div class="row">
                  ${images}
                 
            </div>`
    frm.set_df_property("att","options",img);
    // console.log(records);
})


	}
})

function add_sales_return_request_button(frm, department) {
	if (!frm.doc.patient || !frm.doc.reff_invoice || !frm.doc.name) {
		return;
	}

	frappe.call({
		method: "his.his.doctype.sales_return_request.sales_return_request.get_existing_sales_return_request",
		args: {
			reference_doctype: frm.doctype,
			reference_name: frm.doc.name,
			sales_invoice: frm.doc.reff_invoice,
			patient: frm.doc.patient
		},
		callback(r) {
			if (r.message) {
				frm.add_custom_button(__("Open Sales Return Request"), function () {
					frappe.set_route("Form", "Sales Return Request", r.message);
				});
				return;
			}

			frm.add_custom_button(__("Create Sales Return Request"), function () {
				frappe.new_doc("Sales Return Request", {
					initiating_department: department,
					patient: frm.doc.patient,
					sales_invoice: frm.doc.reff_invoice,
					reference_doctype: frm.doctype,
					reference_name: frm.doc.name
				});
			});
		}
	});
}

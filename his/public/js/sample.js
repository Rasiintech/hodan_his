frappe.ui.form.on('Sample Collection', {
	refresh(frm) {
		frm.remove_custom_button('View Lab Tests');

		frm.add_custom_button(__("Call"), function () {
			frm.set_value("que_steps", "Called");
			frm.save();
		});

		add_sales_return_request_button(frm, "Laboratory - HH");
	},
});

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

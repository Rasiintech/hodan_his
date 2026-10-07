frappe.ui.form.on("Asset Movement", {
	onload_post_render(frm) {
		frm.trigger("set_his_transfer_fields");
	},

	purpose(frm) {
		frm.trigger("set_his_transfer_fields");
	},

	set_his_transfer_fields(frm) {
		if (frm.doc.purpose !== "Transfer") {
			return;
		}

		const grid = frm.fields_dict.assets.grid;
		grid.update_docfield_property("target_location", "reqd", 0);
		grid.update_docfield_property("to_employee", "read_only", 0);
		frm.refresh_field("assets");
	},
});

frappe.ui.form.on("Asset Movement Item", {
	to_employee(frm, cdt, cdn) {
		if (frm.doc.purpose !== "Transfer") {
			return;
		}

		const item = locals[cdt][cdn];
		if (item.to_employee && item.source_location) {
			frappe.model.set_value(cdt, cdn, "target_location", item.source_location);
		}
	},
});

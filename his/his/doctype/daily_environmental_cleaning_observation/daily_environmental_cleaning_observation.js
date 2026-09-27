// Copyright (c) 2026, Hodan Hospital and contributors
// For license information, please see license.txt

function set_default_cleaning_observations(frm) {
	if (!frm.is_new() || frm.__loading_default_observation_items) {
		return;
	}

	const has_observation_data = (frm.doc.observation_items || []).some(
		(row) => row.department || row.observation || row.status || row.comments
	);
	if (has_observation_data) {
		return;
	}

	frm.__loading_default_observation_items = true;
	frappe.call({
		method:
			"his.his.doctype.daily_environmental_cleaning_observation.daily_environmental_cleaning_observation.get_default_observation_items",
		callback(r) {
			const rows = r.message || [];
			const still_empty = !(frm.doc.observation_items || []).some(
				(row) => row.department || row.observation || row.status || row.comments
			);

			if (frm.is_new() && still_empty) {
				frm.clear_table("observation_items");
				rows.forEach((row) => frm.add_child("observation_items", row));
				frm.refresh_field("observation_items");
			}
		},
		always() {
			frm.__loading_default_observation_items = false;
		},
	});
}

frappe.ui.form.on("Daily Environmental Cleaning Observation", {
	onload(frm) {
		set_default_cleaning_observations(frm);
	},
	refresh(frm) {
		set_default_cleaning_observations(frm);
	},
});

// Copyright (c) 2026, Ahmed Ibar and contributors
// For license information, please see license.txt

const DEFAULT_PRECAUTIONS = [
	["Tuberculosis TB", "Yes", "Yes", "Yes", "N95 Mask", "Airborne"],
	["Measles", "No", "No", "No", "Surgical Mask", "Droplet"],
	["Meningitis", "", "", "", "Gloves", "Contact"],
	["Pertussis", "", "", "", "Double Gloves", "Standard Precautions"],
	["Diphtheria", "", "", "", "Gown", "Airborne + Contact"],
	["Chickenpox Virus", "", "", "", "Eye Protection", "Droplet + Contact"],
	["Influenza", "", "", "", "", "Airborne + Droplet"],
	["Mumps", "", "", "", "", ""],
	["Scabies", "", "", "", "", ""],
	["Salmonella", "", "", "", "", ""],
	["C. Difficile Diarrhea", "", "", "", "", ""],
	["Hepatitis B Virus", "", "", "", "", ""],
	["Hepatitis C Virus", "", "", "", "", ""],
	["HIV", "", "", "", "", ""],
	["Covid-19", "", "", "", "", ""],
	["Ebola", "", "", "", "", ""],
	["Wound Infection", "", "", "", "", ""],
	["Burn Infection", "", "", "", "", ""],
	["Cellulitis with Sepsis", "", "", "", "", ""],
	["Chemotherapy", "", "", "", "", ""],
];

function set_default_precautions(frm) {
	if (!frm.is_new()) {
		return;
	}

	const has_precaution_data = (frm.doc.precautions || []).some(
		(row) =>
			row.disease ||
			row.contact ||
			row.droplet ||
			row.airborne ||
			row.ppe_required ||
			row.key_precaution
	);
	if (has_precaution_data) {
		return;
	}

	if (!frm.doc.department) {
		frm.set_value("department", "IPD 2nd Floor");
	}

	frm.clear_table("precautions");
	DEFAULT_PRECAUTIONS.forEach(
		([disease, contact, droplet, airborne, ppe_required, key_precaution]) => {
			frm.add_child("precautions", {
				disease,
				contact,
				droplet,
				airborne,
				ppe_required,
				key_precaution,
			});
		}
	);
	frm.refresh_field("precautions");
}

frappe.ui.form.on("Transmission Precaution of Infectious Disease Isolation", {
	// onload(frm) {
	// 	set_default_precautions(frm);
	// },
	// refresh(frm) {
	// 	set_default_precautions(frm);
	// },
});

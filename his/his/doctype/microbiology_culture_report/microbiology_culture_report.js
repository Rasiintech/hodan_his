const DEFAULT_DRUGS = [
	"Amikacin",
	"Amox/Clav",
	"Aztreonam",
	"Ampicillin",
	"Azithromycin",
	"Cefepime",
	"Ceftazidime",
	"Cefoxitin Screen",
	"Cefuroxime",
	"Cephalothin",
	"Ciprofloxin",
	"Colistine",
	"Ertapenem",
	"Clindamyin",
	"Daptomycin",
	"Erythromycin",
	"Fosfomycin",
	"Fusidic Acid",
	"Gentamycin",
	"Imipenem",
	"Inducible Clindamycin",
	"Levofloxacin",
	"Linezolid",
	"Moxifloxacin",
	"Mupirocin",
	"Nitrofurantoin",
	"Nalidixic Acid",
	"Oxacillin",
	"Penicillin",
	"Rifampin",
	"Synercid",
	"Teicoplanin",
	"Tetracyline",
	"Trimeth/Sulfa",
	"Vancomycin",
];

function populate_default_drugs(frm) {
	if (!frm.is_new()) {
		return;
	}

	if ((frm.doc.drugs || []).length === 1 && !frm.doc.drugs[0].drug && !frm.doc.drugs[0].result && !frm.doc.drugs[0].remarks) {
		frm.doc.drugs = [];
	}

	const existing_drugs = new Set((frm.doc.drugs || []).map((row) => row.drug).filter(Boolean));
	let changed = false;

	DEFAULT_DRUGS.forEach((drug) => {
		if (!existing_drugs.has(drug)) {
			const row = frm.add_child("drugs");
			row.drug = drug;
			changed = true;
		}
	});

	if (changed) {
		frm.refresh_field("drugs");
	}
}

frappe.ui.form.on("Microbiology Culture Report", {
	setup(frm) {
		populate_default_drugs(frm);
	},

	onload(frm) {
		populate_default_drugs(frm);
	},

	refresh(frm) {
		populate_default_drugs(frm);
	},
});

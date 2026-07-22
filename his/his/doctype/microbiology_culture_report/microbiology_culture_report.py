# Copyright (c) 2026, contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


DEFAULT_DRUGS = [
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
]


def ensure_default_drugs(doc):
    existing_drugs = {row.drug for row in (doc.drugs or []) if row.drug}
    for drug in DEFAULT_DRUGS:
        if drug not in existing_drugs:
            doc.append("drugs", {"drug": drug})


class MicrobiologyCultureReport(Document):
    def before_insert(self):
        ensure_default_drugs(self)

    def validate(self):
        ensure_default_drugs(self)


@frappe.whitelist()
def get_default_drugs():
    return DEFAULT_DRUGS

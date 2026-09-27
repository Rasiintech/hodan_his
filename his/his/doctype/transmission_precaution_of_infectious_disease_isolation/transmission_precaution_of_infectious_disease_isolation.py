import frappe
from frappe.model.document import Document


DEFAULT_DEPARTMENT = "IPD 2nd Floor"
DEFAULT_TITLE = "Infectious Disease Isolation Precautions"

DEFAULT_PRECAUTIONS = [
	("Tuberculosis TB", "Yes", "Yes", "Yes", "N95 Mask", "Airborne"),
	("Measles", "No", "No", "No", "Surgical Mask", "Droplet"),
	("Meningitis", "", "", "", "Gloves", "Contact"),
	("Pertussis", "", "", "", "Double Gloves", "Standard Precautions"),
	("Diphtheria", "", "", "", "Gown", "Airborne + Contact"),
	("Chickenpox Virus", "", "", "", "Eye Protection", "Droplet + Contact"),
	("Influenza", "", "", "", "", "Airborne + Droplet"),
	("Mumps", "", "", "", "", ""),
	("Scabies", "", "", "", "", ""),
	("Salmonella", "", "", "", "", ""),
	("C. Difficile Diarrhea", "", "", "", "", ""),
	("Hepatitis B Virus", "", "", "", "", ""),
	("Hepatitis C Virus", "", "", "", "", ""),
	("HIV", "", "", "", "", ""),
	("Covid-19", "", "", "", "", ""),
	("Ebola", "", "", "", "", ""),
	("Wound Infection", "", "", "", "", ""),
	("Burn Infection", "", "", "", "", ""),
	("Cellulitis with Sepsis", "", "", "", "", ""),
	("Chemotherapy", "", "", "", "", ""),
]


class TransmissionPrecautionofInfectiousDiseaseIsolation(Document):
	def before_insert(self):
		if not self.department:
			self.department = DEFAULT_DEPARTMENT

		if not self.precautions:
			for disease, contact, droplet, airborne, ppe_required, key_precaution in DEFAULT_PRECAUTIONS:
				self.append(
					"precautions",
					{
						"disease": disease,
						"contact": contact,
						"droplet": droplet,
						"airborne": airborne,
						"ppe_required": ppe_required,
						"key_precaution": key_precaution,
					},
				)

	def validate(self):
		diseases = [row.disease.strip().casefold() for row in self.precautions if row.disease]
		if len(diseases) != len(set(diseases)):
			frappe.throw("Each disease can only appear once in the precautions table.")


def create_default_chart():
	"""Create the standard isolation chart once and return its name."""
	title = DEFAULT_TITLE
	existing_name = frappe.db.exists("Transmission Precaution of Infectious Disease Isolation", {"title": title})
	if existing_name:
		return existing_name

	doc = frappe.new_doc("Transmission Precaution of Infectious Disease Isolation")
	doc.title = title
	doc.insert()
	return doc.name


def populate_default_chart():
	"""Create or replace the standard isolation chart rows."""
	title = DEFAULT_TITLE
	existing_name = frappe.db.exists("Transmission Precaution of Infectious Disease Isolation", {"title": title})
	if existing_name:
		doc = frappe.get_doc("Transmission Precaution of Infectious Disease Isolation", existing_name)
	else:
		doc = frappe.new_doc("Transmission Precaution of Infectious Disease Isolation")
		doc.title = title

	if not doc.department:
		doc.department = DEFAULT_DEPARTMENT

	doc.set("precautions", [])
	for disease, contact, droplet, airborne, ppe_required, key_precaution in DEFAULT_PRECAUTIONS:
		doc.append(
			"precautions",
			{
				"disease": disease,
				"contact": contact,
				"droplet": droplet,
				"airborne": airborne,
				"ppe_required": ppe_required,
				"key_precaution": key_precaution,
			},
		)

	doc.save()
	return doc.name

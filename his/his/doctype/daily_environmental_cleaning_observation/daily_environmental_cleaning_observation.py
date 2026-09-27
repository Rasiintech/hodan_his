import frappe
from frappe.model.document import Document


CHECKLIST_ITEMS = [
	("OPD Environmental Cleaning and Disinfection", "Floor Cleaning are regularly"),
	("OPD Environmental Cleaning and Disinfection", "Chairs and Waiting Area are Cleaning"),
	("OPD Environmental Cleaning and Disinfection", "Room Consultation are Cleaned"),
	("OPD Environmental Cleaning and Disinfection", "High-Touch Surfaces are Cleaned"),
	("OPD Environmental Cleaning and Disinfection", "Toilet are Clean and Disinfected"),
	("OPD Environmental Cleaning and Disinfection", "Bed examination is Cleaned regularly"),
	("OPD Environmental Cleaning and Disinfection", "Ultrasound are Clean and Disinfected regularly"),
	("OPD Environmental Cleaning and Disinfection", "Echo are Clean and Disinfected"),
	("OPD Environmental Cleaning and Disinfection", "Waste Segregated According to Color Coding"),
	("ER Environmental Cleaning and Disinfection", "Floor Cleaning are regularly"),
	("ER Environmental Cleaning and Disinfection", "Wall dusty/dirty are Cleaning"),
	("ER Environmental Cleaning and Disinfection", "Patient Bed Clean and Disinfected"),
	("ER Environmental Cleaning and Disinfection", "Stretcher are Clean and Disinfected"),
	("ER Environmental Cleaning and Disinfection", "Wheelchairs are Clean and Disinfected"),
	("ER Environmental Cleaning and Disinfection", "Toilet are Clean and Disinfected"),
	("ER Environmental Cleaning and Disinfection", "High-Touch Surfaces are Cleaned & Disinfected"),
	("ER Environmental Cleaning and Disinfection", "Medical Equipment are Disinfected"),
	("ER Environmental Cleaning and Disinfection", "Suction Machine Disinfected"),
	("ER Environmental Cleaning and Disinfection", "Waste Segregated According to Color Coding"),
	("ER Environmental Cleaning and Disinfection", "Remove after use waste bin Cleaned"),
	("IPD 2nd Floor Environmental Cleaning and Disinfection", "Floor Cleaning are regularly"),
	("IPD 2nd Floor Environmental Cleaning and Disinfection", "Patient Room are Cleaning"),
	("IPD 2nd Floor Environmental Cleaning and Disinfection", "Wall dusty/dirty are Cleaning"),
	("IPD 2nd Floor Environmental Cleaning and Disinfection", "Labour Room are Cleaned"),
	("IPD 2nd Floor Environmental Cleaning and Disinfection", "Toilet are Clean and Disinfected"),
	("IPD 2nd Floor Environmental Cleaning and Disinfection", "Patient bed rail and frame are Disinfection"),
	("IPD 2nd Floor Environmental Cleaning and Disinfection", "High-Touch Surfaces are Cleaned & Disinfection"),
	("IPD 2nd Floor Environmental Cleaning and Disinfection", "Waste Segregated According to Color Coding"),
	("IPD 2nd Floor Environmental Cleaning and Disinfection", "Remove after use waste bin Cleaned"),
	("IPD 3rd Floor Environmental Cleaning and Disinfection", "Floor Cleaning are regularly"),
	("IPD 3rd Floor Environmental Cleaning and Disinfection", "Patient Room are Cleaning"),
	("IPD 3rd Floor Environmental Cleaning and Disinfection", "Wall dusty/dirty are Cleaning"),
	("IPD 3rd Floor Environmental Cleaning and Disinfection", "Labour Room are Cleaned"),
	("IPD 3rd Floor Environmental Cleaning and Disinfection", "Toilet are Clean and Disinfected"),
	("IPD 3rd Floor Environmental Cleaning and Disinfection", "Patient bed rail and frame are Disinfection"),
	("IPD 3rd Floor Environmental Cleaning and Disinfection", "High-Touch Surfaces are Cleaned & Disinfection"),
	("IPD 3rd Floor Environmental Cleaning and Disinfection", "Waste Segregated According to Color Coding"),
	("IPD 3rd Floor Environmental Cleaning and Disinfection", "Remove after use waste bin Cleaned"),
	("IPD G.Ward Environmental Cleaning and Disinfection", "Floor Cleaning are regularly"),
	("IPD G.Ward Environmental Cleaning and Disinfection", "Patient Room are Cleaning"),
	("IPD G.Ward Environmental Cleaning and Disinfection", "Wall dusty/dirty are Cleaning"),
	("IPD G.Ward Environmental Cleaning and Disinfection", "Labour Room are Cleaned"),
	("IPD G.Ward Environmental Cleaning and Disinfection", "Toilet are Clean and Disinfected"),
	("IPD G.Ward Environmental Cleaning and Disinfection", "Patient bed rail and frame are Disinfection"),
	("IPD G.Ward Environmental Cleaning and Disinfection", "High-Touch Surfaces are Cleaned & Disinfection"),
	("IPD G.Ward Environmental Cleaning and Disinfection", "Waste Segregated According to Color Coding"),
	("IPD G.Ward Environmental Cleaning and Disinfection", "Remove after use waste bin Cleaned"),
	("IPD G.Pediatric Environmental Cleaning and Disinfection", "Floor Cleaning are regularly"),
	("IPD G.Pediatric Environmental Cleaning and Disinfection", "Patient Room are Cleaning"),
	("IPD G.Pediatric Environmental Cleaning and Disinfection", "Wall dusty/dirty are Cleaning"),
	("IPD G.Pediatric Environmental Cleaning and Disinfection", "Labour Room are Cleaned"),
	("IPD G.Pediatric Environmental Cleaning and Disinfection", "Toilet are Clean and Disinfected"),
	("IPD G.Pediatric Environmental Cleaning and Disinfection", "Patient bed rail and frame are Disinfection"),
	("IPD G.Pediatric Environmental Cleaning and Disinfection", "High-Touch Surfaces are Cleaned & Disinfection"),
	("IPD G.Pediatric Environmental Cleaning and Disinfection", "Waste Segregated According to Color Coding"),
	("IPD G.Pediatric Environmental Cleaning and Disinfection", "Remove after use waste bin Cleaned"),
	("ICU Environmental Cleaning and Disinfection", "Floor Cleaning regularly"),
	("ICU Environmental Cleaning and Disinfection", "Wall dusty/dirty are Cleaning"),
	("ICU Environmental Cleaning and Disinfection", "Toilet are Clean and Disinfection"),
	("ICU Environmental Cleaning and Disinfection", "Patient Bed Surrounding are Disinfected"),
	("ICU Environmental Cleaning and Disinfection", "Patient bed rail & frame Clean and Disinfection"),
	("ICU Environmental Cleaning and Disinfection", "Patient bed Air Mattress Clean and Disinfected"),
	("ICU Environmental Cleaning and Disinfection", "Door handle Surface are Disinfection"),
	("ICU Environmental Cleaning and Disinfection", "Medical Equipment are Clean and Disinfection"),
	("ICU Environmental Cleaning and Disinfection", "Suction Machine are Clean and Disinfected"),
	("ICU Environmental Cleaning and Disinfection", "Monitors are Clean and Disinfection"),
	("ICU Environmental Cleaning and Disinfection", "Ventilator are Clean and Disinfection"),
	("ICU Environmental Cleaning and Disinfection", "Dialysis Machine are Clean and Disinfected"),
	("ICU Environmental Cleaning and Disinfection", "Waste Segregated According to Color Coding"),
	("ICU Environmental Cleaning and Disinfection", "Remove after use waste bin Cleaned"),
	("NICU Environmental Cleaning and Disinfection", "Floor Cleaning regularly"),
	("NICU Environmental Cleaning and Disinfection", "High-Touch Surfaces Disinfection"),
	("NICU Environmental Cleaning and Disinfection", "Incubator (Ext-Surfaces Disinfected)"),
	("NICU Environmental Cleaning and Disinfection", "Incubator (Int-Surfaces Disinfection)"),
	("NICU Environmental Cleaning and Disinfection", "Radiant Warmer Disinfection"),
	("NICU Environmental Cleaning and Disinfection", "Suction Machine Disinfected"),
	("NICU Environmental Cleaning and Disinfection", "Monitors Clean and Disinfection"),
	("NICU Environmental Cleaning and Disinfection", "Ventilator are Clean and Disinfection"),
	("NICU Environmental Cleaning and Disinfection", "Wall dusty/dirty are Cleaning"),
	("NICU Environmental Cleaning and Disinfection", "Waste Segregated According to Color Coding"),
	("NICU Environmental Cleaning and Disinfection", "Remove after use waste bin Cleaned"),
	("OT Environmental Cleaning and Disinfection", "Floor Cleaning regularly b/w Patients"),
	("OT Environmental Cleaning and Disinfection", "Wall dusty/dirty are Cleaning"),
	("OT Environmental Cleaning and Disinfection", "Toilet are Clean and Disinfection"),
	("OT Environmental Cleaning and Disinfection", "Sink handwashing Clean and Disinfection"),
	("OT Environmental Cleaning and Disinfection", "High-Touch Surfaces are Cleaned and Disinfection"),
	("OT Environmental Cleaning and Disinfection", "OT Rooms are Clean and Disinfection"),
	("OT Environmental Cleaning and Disinfection", "Pre and Post Operating Room Cleaning"),
	("OT Environmental Cleaning and Disinfection", "Bed Operation are Clean and Disinfection"),
	("OT Environmental Cleaning and Disinfection", "Table and Trolleys are Clean and Disinfection"),
	("OT Environmental Cleaning and Disinfection", "Surgical Instrument Clean and Disinfected"),
	("OT Environmental Cleaning and Disinfection", "Nebulization Mask are Disinfected"),
	("OT Environmental Cleaning and Disinfection", "Anasthesia machine are Disinfected"),
	("OT Environmental Cleaning and Disinfection", "Suction Machine are Clean and Disinfected"),
	("OT Environmental Cleaning and Disinfection", "Spills are Cleaned and Disinfected Immediately"),
	("OT Environmental Cleaning and Disinfection", "Waste Segregated According to Color Coding"),
	("OT Environmental Cleaning and Disinfection", "Remove after use waste bin Cleaned"),
	("Lab Environmental Cleaning and Disinfection", "Floor Cleaning regularly"),
	("Lab Environmental Cleaning and Disinfection", "Work Surface Area Cleaning"),
	("Lab Environmental Cleaning and Disinfection", "Speciment Proces Bench Disinfection"),
	("Lab Environmental Cleaning and Disinfection", "Refrigenator blood bank Disinfected"),
	("Lab Environmental Cleaning and Disinfection", "Lab Machine Proces Surface Disinfection"),
	("Lab Environmental Cleaning and Disinfection", "Lab Equipment Clean and Disinfection"),
	("Lab Environmental Cleaning and Disinfection", "Door handle Surface are Disinfection"),
	("Lab Environmental Cleaning and Disinfection", "Sharps Container Surface Clean"),
	("Lab Environmental Cleaning and Disinfection", "Waste Segregated According to Color Coding"),
	("Radiology Environmental Cleaning and Disinfection", "Floor Cleaning regularly"),
	("Radiology Environmental Cleaning and Disinfection", "Wall dusty/dirty are Cleaning"),
	("Radiology Environmental Cleaning and Disinfection", "CTS Surface Clean dusty/dirty and Disinfection"),
	("Radiology Environmental Cleaning and Disinfection", "MRI Surface Clean dusty/dirty and Disinfection"),
	("Radiology Environmental Cleaning and Disinfection", "X-ray Surface Clean dusty/dirty and Disinfection"),
	("Radiology Environmental Cleaning and Disinfection", "Door handle Surface are Disinfection"),
	("Radiology Environmental Cleaning and Disinfection", "Waste Segregated According to Color Coding"),
]

DEFAULT_STATUSES = {
	("OPD Environmental Cleaning and Disinfection", "Floor Cleaning are regularly"): "Done",
	("OPD Environmental Cleaning and Disinfection", "Chairs and Waiting Area are Cleaning"): "Not Done",
	("ER Environmental Cleaning and Disinfection", "Floor Cleaning are regularly"): "Done",
	("ER Environmental Cleaning and Disinfection", "Patient Bed Clean and Disinfected"): "Not Done",
	("IPD 2nd Floor Environmental Cleaning and Disinfection", "Floor Cleaning are regularly"): "Done",
	("IPD 2nd Floor Environmental Cleaning and Disinfection", "Patient Room are Cleaning"): "Not Done",
	("IPD 3rd Floor Environmental Cleaning and Disinfection", "Floor Cleaning are regularly"): "Done",
	("IPD 3rd Floor Environmental Cleaning and Disinfection", "Patient Room are Cleaning"): "Not Done",
	("IPD G.Ward Environmental Cleaning and Disinfection", "Floor Cleaning are regularly"): "Done",
	("IPD G.Ward Environmental Cleaning and Disinfection", "Patient Room are Cleaning"): "Not Done",
	("IPD G.Pediatric Environmental Cleaning and Disinfection", "Floor Cleaning are regularly"): "Done",
	("IPD G.Pediatric Environmental Cleaning and Disinfection", "Patient Room are Cleaning"): "Not Done",
	("ICU Environmental Cleaning and Disinfection", "Floor Cleaning regularly"): "Done",
	("ICU Environmental Cleaning and Disinfection", "Wall dusty/dirty are Cleaning"): "Not Done",
	("NICU Environmental Cleaning and Disinfection", "Floor Cleaning regularly"): "Done",
	("NICU Environmental Cleaning and Disinfection", "High-Touch Surfaces Disinfection"): "Not Done",
	("OT Environmental Cleaning and Disinfection", "Floor Cleaning regularly b/w Patients"): "Done",
	("OT Environmental Cleaning and Disinfection", "Wall dusty/dirty are Cleaning"): "Not Done",
	("Lab Environmental Cleaning and Disinfection", "Floor Cleaning regularly"): "Done",
	("Lab Environmental Cleaning and Disinfection", "Work Surface Area Cleaning"): "Not Done",
	("Radiology Environmental Cleaning and Disinfection", "Floor Cleaning regularly"): "Done",
	("Radiology Environmental Cleaning and Disinfection", "Wall dusty/dirty are Cleaning"): "Not Done",
}


def get_checklist_items():
	items = []
	previous_department = None
	for department, observation in CHECKLIST_ITEMS:
		if department != previous_department:
			items.append(
				{
					"department": department,
					"observation": "",
					"status": "",
					"comments": "",
				}
			)

		items.append(
			{
				"department": "",
				"observation": observation,
				"status": DEFAULT_STATUSES.get((department, observation), ""),
				"comments": "",
			}
		)
		previous_department = department

	return items


@frappe.whitelist()
def get_default_observation_items():
	"""Return the checklist used to initialize a new observation form."""
	return get_checklist_items()


class DailyEnvironmentalCleaningObservation(Document):
	def before_insert(self):
		self.set_default_observation_items()

	def set_default_observation_items(self):
		if any(row.observation or row.department for row in self.observation_items):
			return

		self.set("observation_items", [])
		for item in get_checklist_items():
			self.append("observation_items", item)

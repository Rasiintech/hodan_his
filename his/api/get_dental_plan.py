import frappe

@frappe.whitelist()
def get_plan(patient, practitioner, medical_department):
    plan = frappe.get_all(
        "Dental Plan",
        filters={"patient": patient, "practitioner": practitioner, "medical_department": medical_department},
        fields=["name"],
        limit=1  # Get only the first match
    )

    

    if plan:
        plan_doc = frappe.get_doc("Dental Plan", plan[0].name)

        return {
            "agreed_fee": plan_doc.agreed_fee,
            "grand_total": plan_doc.grand_total
        }
        # frappe.errprint(plan_doc.agreed_fee)
        # frappe.throw("STOP")

def dental_plan_in_encounter(doc, method=None):
    pass
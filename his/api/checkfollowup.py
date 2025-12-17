import  frappe

# @frappe.whitelist()
# def Check_follow_up(**args):
# 	patient=args.get("patient")
# 	# doc=args.get("doctor_name")
# 	sql=frappe.db.sql(f"""
# 	 SELECT practitioner, start_date, valid_till, patient, status
# 		FROM (
# 			SELECT *,
# 				ROW_NUMBER() OVER (PARTITION BY practitioner ORDER BY valid_till DESC) AS rn
# 			FROM `tabFee Validity`
# 			WHERE patient = '{patient}' AND is_cancel = 0
# 		) AS ranked
# 		WHERE rn = 1;
# 		""" ,  as_dict=True)
# 	return sql

# @frappe.whitelist()
# def Check_follow_up(**args):
# 	patient = args.get("patient")

# 	if not patient:
# 		return []

# 	sql = frappe.db.sql("""
# 		SELECT fv.practitioner, fv.start_date, fv.valid_till, fv.patient, fv.status
# 		FROM `tabFee Validity` fv
# 		INNER JOIN (
# 			SELECT practitioner, MAX(valid_till) AS max_valid_till
# 			FROM `tabFee Validity`
# 			WHERE patient = %s AND is_cancel = 0
# 			GROUP BY practitioner
# 		) latest
# 		ON fv.practitioner = latest.practitioner
# 		AND fv.valid_till = latest.max_valid_till
# 		WHERE fv.patient = %s AND fv.is_cancel = 0
# 	""", (patient, patient), as_dict=True)

# 	return sql

import  frappe
from frappe.utils import getdate, nowdate

@frappe.whitelist()
def Check_follow_up(patient):
    today = getdate(nowdate())

    rows = frappe.db.get_all(
        "Fee Validity",
        filters={
            "patient": patient,
            "is_cancel": 0,
            # if you only want pending/active rows, uncomment:
            # "status": "Pending",
        },
        fields=["name", "patient", "practitioner", "start_date", "valid_till", "status"],
        order_by="valid_till desc, modified desc",
    )

    # Keep only latest row per practitioner
    seen = set()
    out = []
    for r in rows:
        pr = r.get("practitioner")
        if not pr:
            continue
        if pr in seen:
            continue
        seen.add(pr)
        out.append(r)

    return out

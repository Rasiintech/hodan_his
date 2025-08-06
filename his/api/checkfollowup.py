import  frappe

@frappe.whitelist()
def Check_follow_up(**args):
	patient=args.get("patient")
	# doc=args.get("doctor_name")
	sql=frappe.db.sql(f"""
	 SELECT practitioner, start_date, valid_till, patient, status
		FROM (
			SELECT *,
				ROW_NUMBER() OVER (PARTITION BY practitioner ORDER BY valid_till DESC) AS rn
			FROM `tabFee Validity`
			WHERE patient = '{patient}'
		) AS ranked
		WHERE rn = 1;
		""" ,  as_dict=True)
	return sql

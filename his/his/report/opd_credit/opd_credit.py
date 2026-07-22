# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from erpnext.accounts.utils import get_balance_on

def execute(filters=None):
	columns, data =get_columns(), get_data(filters)
	return columns, data

def get_data(filters):
	from_date, to_date = filters.get('from_date'), filters.get('to_date')
	# data = []
	# opd_customers = frappe.db.sql(f"""

	# 		SELECT DISTINCT 
	# 			s.customer,
	# 			s.patient,
	# 			s.patient_name
	# 		FROM 
	# 			`tabSales Invoice` s 
	# 		LEFT JOIN 
	# 			`tabInpatient Record` ip 
	# 			ON s.patient = ip.patient
	# 		WHERE 
	# 			s.posting_date BETWEEN "2026-02-14" AND "2026-02-14"
	# 			AND s.docstatus = 1
	# 			AND NOT EXISTS (
	# 				SELECT 1
	# 				FROM `tabInpatient Record` ip2
	# 				WHERE ip2.patient = s.patient
	# 				and ip2.status = "Admitted"
				
	# 			);


        
    #     ; """ , as_dict=1)

	# for customer in opd_customers:
	# 	balance = get_balance_on(party_type = "Customer",party = customer.customer, date= "2026-2-15")
	# 	if balance > 0:
	# 		data.append({"customer" : customer.customer,"patient" : customer.patient ,"patient_name": customer.patient_name,  "balance" :  balance})
	# 		frappe.errprint(balance)
	# return data
	data = []
# 	data = frappe.db.sql(f"""
# 		SELECT
#     s.customer,
#     s.patient,
#     s.patient_name,
	
#     SUM(s.outstanding_amount) AS balance,
# 	s.comment
# FROM `tabSales Invoice` s
# WHERE
#     s.posting_date BETWEEN "{from_date}" AND "{to_date}"
#     AND s.bill_to_employee = 0
#     AND s.is_inpatient = 0
#     AND s.docstatus = 1
#     AND NOT EXISTS (
#         SELECT 1
#         FROM `tabInpatient Record` ip2
#         WHERE ip2.patient = s.patient
#           AND (
#               ip2.status IN ("Admitted", "Discharge Scheduled")
#               OR (ip2.status = "Discharged" AND ip2.discharge_datetime >= "{to_date}")
#           )
#     )
# GROUP BY
#     s.customer, s.patient, s.patient_name
# HAVING
#     balance > 0;



# 		""", as_dict=1)

	# Add customers with balance to the data list
	# for customer in opd_customers:
	# 	data.append({
	# 		"customer": customer.customer,
	# 		"patient": customer.patient,
	# 		"patient_name": customer.patient_name,
	# 		"balance": customer.total_balance
	# 	})
	data = frappe.db.sql(f"""
	SELECT
    s.customer,
    s.patient,
    s.patient_name,
    SUM(s.outstanding_amount) AS balance,
    s.comment,
    c.responsible
	FROM `tabSales Invoice` s
	JOIN `tabCustomer` c ON c.name = s.customer  -- Join to get the responsible field
	WHERE
		s.posting_date BETWEEN "{from_date}" AND "{to_date}"
		AND s.bill_to_employee = 0
		AND s.is_inpatient = 0
		AND s.docstatus = 1
		AND NOT EXISTS (
			SELECT 1
			FROM `tabInpatient Record` ip2
			WHERE ip2.patient = s.patient
			AND (
				ip2.status IN ("Admitted", "Discharge Scheduled")
				OR (ip2.status = "Discharged" AND ip2.discharge_datetime >= "{to_date}")
			)
		)
	GROUP BY
		s.customer, s.patient, s.patient_name, c.responsible  -- Group by the responsible field
	HAVING
		balance > 0;



		""", as_dict=1)
	for d in data:
		if d.responsible:
			re = frappe.db.get_value("Responsible" , d.responsible , "mobile")
			d["resposible_number"] = re
	return data

	
def get_columns():
   return [
        
        
        # "Practitioner:Link/Healthcare Practitioner:200",
        "customer:Link/Customer:100",
        "patient:Link/Patient:100",
		"patient_name:Data:300",
        "balance:Currency:100",
		"responsible:Link/Responsible:300",
		"resposible_number:Data:300",
		"comment:Data:350",
        # "followup:Data:100",
        # "refer:Data:100",
        # "revisit:Data:100",
        # "total:Data:100",
        
        # "closed:Data:110",
        # "open:Data:100",
      
        
    ]



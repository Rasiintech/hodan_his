from erpnext.stock.get_item_details import get_pos_profile
import  frappe

@frappe.whitelist()
def token_numebr(doc, method=None):
    # Optionally ensure any previous transaction state is committed
    frappe.db.commit()  # Only if needed in your context
    
    # This locks the rows for the given practitioner and date
    b = frappe.db.sql(
        """
        SELECT MAX(token_no) as max 
        FROM `tabQue` 
        WHERE date = %s AND practitioner = %s
        FOR UPDATE
        """, (doc.date, doc.practitioner), as_dict=True
    )
    num = b[0]['max']
    if num is None:
        num = 0
    doc.token_no = int(num) + 1


# @frappe.whitelist()
# def token_numebr(doc, method=None):
#     # Fetch the existing Que record if it exists
#     existing_que = frappe.db.get_value('Que', doc.name, ["practitioner", "token_no"], as_dict=True)

#     if not existing_que:
#         # New record, generate token number for the first time
#         generate_token_number(doc)
#     elif existing_que['practitioner'] != doc.practitioner:
#         # Practitioner has changed, re-generate token number
#         generate_token_number(doc)

# def generate_token_number(doc):
# 	frappe.db.commit()
# 	prac = doc.practitioner
# 	appoinda = doc.date
# 	b = frappe.db.sql(f"""
# 		SELECT MAX(token_no) AS max
# 		FROM `tabQue`
# 		WHERE date = %s AND practitioner = %s
# 		FOR UPDATE
# 	""", (appoinda, prac), as_dict=True)

# 	num = b[0]['max']
# 	if num is None:
# 		num = 0

# 	doc.token_no = int(num) + 1

# File: his/his/number_card/API/total_monthly_opd_visits.py

import frappe
from datetime import datetime
from frappe.utils import nowdate

@frappe.whitelist()
def get_number_card_data():
    today = datetime.today()
    month_start = today.replace(day=1).strftime("%Y-%m-%d")
    current_date = nowdate()

    frappe.errprint(today)
    frappe.errprint(month_start)

    result = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabQue`
        WHERE date >= %s AND date <= %s
    """, (month_start, current_date))

    count = result[0][0] if result else 0

    return {
        "value": count,
        "fieldtype": "Int"
    }

# File: his/his/dashboard_chart_source/opd_visits_trend.py

import frappe
from frappe.utils import getdate
from datetime import timedelta

@frappe.whitelist()
def get_data(filters=None):
    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))

    data = frappe.db.sql("""
        SELECT date, COUNT(*) as total
        FROM `tabQue`
        WHERE date BETWEEN %s AND %s
        GROUP BY date
        ORDER BY date
    """, (from_date, to_date), as_dict=True)

    labels = [d.date.strftime('%Y-%m-%d') for d in data]
    values = [d.total for d in data]

    return {
        "labels": labels,
        "datasets": [{
            "name": "Visits",
            "values": values,
            "chartType": "bar"
        }],
        "type": "bar"
    }

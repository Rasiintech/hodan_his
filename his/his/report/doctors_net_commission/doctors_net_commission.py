import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.item_wise_sales_register.item_wise_sales_register import execute as item_sales_register_execute

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_data(filters):
    results = item_sales_register_execute({
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date")
    })

    report_data = results[1]

    # Step 1: Get invoice->ref_practitioner mapping
    invoice_numbers = {row.get("invoice") for row in report_data if row.get("invoice")}
    invoice_docs = frappe.get_all(
        "Sales Invoice",
        fields=["name", "ref_practitioner"],
        filters={"name": ("in", list(invoice_numbers))}
    )
    invoice_ref_map = {doc.name: doc.ref_practitioner for doc in invoice_docs}

    # Step 2: Prepare filtered rows
    filtered_rows = []
    for row in report_data:
        invoice = row.get("invoice")
        ref_practitioner = invoice_ref_map.get(invoice)

        if filters.get("ref_practitioner") and filters["ref_practitioner"] != ref_practitioner:
            continue

        filtered_rows.append({
            "ref_practitioner": ref_practitioner,
            "item_group": row.get("item_group"),
            "gross_sales": flt(row.get("amount") or 0)
        })

    # Step 3: Group gross_sales by (doctor, item group)
    grouped = {}
    for row in filtered_rows:
        key = (row["ref_practitioner"], row["item_group"])
        grouped.setdefault(key, 0)
        grouped[key] += row["gross_sales"]

    # Step 4: Get active practitioners with commission rules
    commission_percent_map = {}
    practitioner_info = {}
    practitioner_names = {k[0] for k in grouped.keys() if k[0]}

    for practitioner in practitioner_names:
        try:
            doc = frappe.get_doc("Healthcare Practitioner", practitioner)
            if doc.status != "Active" or not doc.get("commission"):
                continue  # skip inactive or no commission entries

            practitioner_info[practitioner] = {
                "employee_commisison": doc.employee_commisison or None
            }

            for item in doc.get("commission", []):
                if item.item_group:
                    commission_percent_map[(practitioner, item.item_group)] = item.percent

        except frappe.DoesNotExistError:
            continue

    # Step 5: Calculate per-doctor totals
    doctor_totals = {}
    expense_percent = 25
    for (ref_practitioner, item_group), gross_sales in grouped.items():
        if ref_practitioner not in practitioner_info:
            continue  # skip if not active or no commission

        commission_percent = flt(commission_percent_map.get((ref_practitioner, item_group), 0))
        net_sales = flt(gross_sales * (1 - expense_percent / 100))
        net_commission = flt(net_sales * commission_percent / 100)

        if ref_practitioner not in doctor_totals:
            doctor_totals[ref_practitioner] = {
                "total_net_commission": 0,
                "total_net_sales": 0,
                "weighted_commission_sum": 0
            }

        doctor_totals[ref_practitioner]["total_net_commission"] += net_commission
        doctor_totals[ref_practitioner]["total_net_sales"] += net_sales
        doctor_totals[ref_practitioner]["weighted_commission_sum"] += commission_percent * net_sales

    # Step 6: Format output
    output = []
    for doctor, stats in doctor_totals.items():
        total_net_sales = stats["total_net_sales"]
        avg_commission_rate = (
            stats["weighted_commission_sum"] / total_net_sales if total_net_sales else 0
        )
        output.append(frappe._dict({
            "employee_commisison": practitioner_info[doctor]["employee_commisison"],
            "ref_practitioner": doctor,
            "commission_percent": round(avg_commission_rate, 2),
            "net_commission": round(stats["total_net_commission"], 2)
        }))

    return output


def get_columns():
    return [
        {"label": _("Employee ID"), "fieldname": "employee_commisison", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": _("Doctor Name"), "fieldname": "ref_practitioner", "fieldtype": "Link", "options": "Healthcare Practitioner", "width": 200},
        {"label": _("Commission Rate %"), "fieldname": "commission_percent", "fieldtype": "Percent", "width": 150},
        {"label": _("Net Commission"), "fieldname": "net_commission", "fieldtype": "Currency", "options": "currency", "width": 180}
    ]


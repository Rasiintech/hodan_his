import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.item_wise_sales_register.item_wise_sales_register import execute as item_sales_register_execute

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Ref Practitioner"), "fieldname": "ref_practitioner", "fieldtype": "Data", "width": 180},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 180},
        {"label": _("Gross Sales"), "fieldname": "gross_sales", "fieldtype": "Currency", "options": "currency", "width": 150},
        {"label": _("Sales Expense %"), "fieldname": "expense_percent", "fieldtype": "Percent", "width": 130},
        {"label": _("Sales Expense Amount"), "fieldname": "sales_expense_amount", "fieldtype": "Currency", "options": "currency", "width": 180},
        {"label": _("Net Sales Amount"), "fieldname": "net_sales", "fieldtype": "Currency", "options": "currency", "width": 180},
        {"label": _("Commission %"), "fieldname": "commission_percent", "fieldtype": "Percent", "width": 130},
        {"label": _("Net Commission"), "fieldname": "net_commission", "fieldtype": "Currency", "options": "currency", "width": 150}
    ]

def get_data(filters):
    his_settings = frappe.get_doc("HIS Settings", "HIS Settings")
    sales_expense = his_settings.sales_expense
    # frappe.errprint(sales_expense)
    results = item_sales_register_execute({
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date")
    })

    report_data = results[1]
    # frappe.errprint(report_data[0])  # Optional debug

    # Step 1: Collect unique invoice numbers
    invoice_numbers = {row.get("invoice") for row in report_data if row.get("invoice")}

    # Step 2: Bulk fetch ref_practitioner mapping
    invoice_docs = frappe.get_all(
        "Sales Invoice",
        fields=["name", "ref_practitioner"],
        filters={"name": ("in", list(invoice_numbers))}
    )
    invoice_ref_map = {doc.name: doc.ref_practitioner for doc in invoice_docs}

    # Step 3: Build raw list and apply optional filtering
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

    # Step 4: Group and summarize by (ref_practitioner, item_group)
    grouped = {}
    for row in filtered_rows:
        key = (row["ref_practitioner"], row["item_group"])
        grouped.setdefault(key, 0)
        grouped[key] += row["gross_sales"]

    # Step 5: Fetch commission mapping from Healthcare Practitioner
    commission_percent_map = {}
    practitioner_names = {k[0] for k in grouped.keys() if k[0]}
    for practitioner in practitioner_names:
        try:
            doc = frappe.get_doc("Healthcare Practitioner", practitioner)
            for item in doc.get("commission", []):
                if item.item_group:
                    commission_percent_map[(practitioner, item.item_group)] = item.percent
        except frappe.DoesNotExistError:
            pass  # Skip if practitioner not found

    # Step 6: Format final output with full calculations
    output = []
    net_sales=0
    for (ref_practitioner, item_group), gross_sales in grouped.items():
        commission_percent = flt(commission_percent_map.get((ref_practitioner, item_group), 0))
        expense_percent = sales_expense
        sales_expense_amount = flt(gross_sales * expense_percent / 100)
        if item_group != "Consultation":
            net_sales = flt(gross_sales - sales_expense_amount)
        else:
            sales_expense_amount=0
            net_sales = flt(gross_sales)
            
        net_commission = flt(net_sales * commission_percent / 100)
        if commission_percent:
            output.append(frappe._dict({
                "ref_practitioner": ref_practitioner,
                "item_group": item_group,
                "gross_sales": round(gross_sales,2),
                "expense_percent": sales_expense,
                "sales_expense_amount": round(sales_expense_amount,2),
                "net_sales": round(net_sales,2),
                "commission_percent": commission_percent,
                "net_commission": round(net_commission,2)
            }))

    return output


# import frappe
# from frappe import _
# from frappe.utils import flt
# from erpnext.accounts.report.item_wise_sales_register.item_wise_sales_register import execute as item_sales_register_execute

# def execute(filters=None):
#     columns = get_columns()
#     data = get_data(filters)
#     return columns, data

# def get_columns():
#     return [
#         {"label": _("Ref Practitioner"), "fieldname": "ref_practitioner", "fieldtype": "Data", "width": 180},
#         {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 180},
#         {"label": _("Total Amount"), "fieldname": "amount", "fieldtype": "Currency", "options": "currency", "width": 150}
#     ]

# def get_data(filters):
#     results = item_sales_register_execute({
#         "from_date": filters.get("from_date"),
#         "to_date": filters.get("to_date")
#     })

#     report_data = results[1]
#     frappe.errprint(report_data[0])  # Optional: sample debug

#     # Step 1: Collect unique invoice numbers
#     invoice_numbers = {row.get("invoice") for row in report_data if row.get("invoice")}

#     # Step 2: Bulk fetch ref_practitioner mapping
#     invoice_docs = frappe.get_all(
#         "Sales Invoice",
#         fields=["name", "ref_practitioner"],
#         filters={"name": ("in", list(invoice_numbers))}
#     )
#     invoice_ref_map = {doc.name: doc.ref_practitioner for doc in invoice_docs}

#     # Step 3: Build raw list and apply optional filtering
#     filtered_rows = []
#     for row in report_data:
#         invoice = row.get("invoice")
#         ref_practitioner = invoice_ref_map.get(invoice)

#         if filters.get("ref_practitioner") and filters["ref_practitioner"] != ref_practitioner:
#             continue

#         filtered_rows.append({
#             "ref_practitioner": ref_practitioner,
#             "item_group": row.get("item_group"),
#             "amount": flt(row.get("amount") or 0)
#         })

#     # Step 4: Group and summarize by (ref_practitioner, item_group)
#     grouped = {}
#     for row in filtered_rows:
#         key = (row["ref_practitioner"], row["item_group"])
#         grouped.setdefault(key, 0)
#         grouped[key] += row["amount"]

#     # Step 5: Format final output
#     output = []
#     for (ref_practitioner, item_group), amount in grouped.items():
#         output.append(frappe._dict({
#             "ref_practitioner": ref_practitioner,
#             "item_group": item_group,
#             "amount": flt(amount)
#         }))

#     return output


# import frappe
# from frappe import _
# from frappe.utils import flt
# from erpnext.accounts.report.item_wise_sales_register.item_wise_sales_register import execute as item_sales_register_execute

# def execute(filters=None):
#     columns = get_columns()
#     data = get_data(filters)
#     return columns, data

# def get_columns():
#     return [
#         {"label": _("Ref Practitioner"), "fieldname": "ref_practitioner", "fieldtype": "Data", "width": 180},
#         {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 180},
#         {"label": _("Gross Sales"), "fieldname": "gross_sales", "fieldtype": "Currency", "options": "currency", "width": 150},
#         {"label": _("Sales Expense %"), "fieldname": "expense_percent", "fieldtype": "Percent", "width": 130},
#         {"label": _("Sales Expense Amount"), "fieldname": "sales_expense_amount", "fieldtype": "Currency", "options": "currency", "width": 180},
#         {"label": _("Net Sales Amount"), "fieldname": "net_sales", "fieldtype": "Currency", "options": "currency", "width": 180},
#         {"label": _("Commission %"), "fieldname": "commission_percent", "fieldtype": "Percent", "width": 130},
#         {"label": _("Net Commission"), "fieldname": "net_commission", "fieldtype": "Currency", "options": "currency", "width": 150}
#     ]

# def get_data(filters):
#     results = item_sales_register_execute({
#         "from_date": filters.get("from_date"),
#         "to_date": filters.get("to_date")
#     })

#     report_data = results[1]
#     frappe.errprint(report_data[0])  # Optional: sample debug

#     # Step 1: Collect unique invoice numbers
#     invoice_numbers = {row.get("invoice") for row in report_data if row.get("invoice")}

#     # Step 2: Bulk fetch ref_practitioner mapping
#     invoice_docs = frappe.get_all(
#         "Sales Invoice",
#         fields=["name", "ref_practitioner"],
#         filters={"name": ("in", list(invoice_numbers))}
#     )
#     invoice_ref_map = {doc.name: doc.ref_practitioner for doc in invoice_docs}

#     # Step 3: Build raw list and apply optional filtering
#     filtered_rows = []
#     for row in report_data:
#         invoice = row.get("invoice")
#         ref_practitioner = invoice_ref_map.get(invoice)

#         if filters.get("ref_practitioner") and filters["ref_practitioner"] != ref_practitioner:
#             continue

#         filtered_rows.append({
#             "ref_practitioner": ref_practitioner,
#             "item_group": row.get("item_group"),
#             "gross_sales": flt(row.get("amount") or 0)
#         })

#     # Step 4: Group and summarize by (ref_practitioner, item_group)
#     grouped = {}
#     for row in filtered_rows:
#         key = (row["ref_practitioner"], row["item_group"])
#         grouped.setdefault(key, 0)
#         grouped[key] += row["gross_sales"]

#     # Step 5: Fetch commission mapping from Healthcare Practitioner
#     commission_percent_map = {}
#     practitioner_names = {k[0] for k in grouped.keys() if k[0]}
#     for practitioner in practitioner_names:
#         try:
#             doc = frappe.get_doc("Healthcare Practitioner", practitioner)
#             for item in doc.get("commission", []):
#                 if item.item_group:
#                     commission_percent_map[(practitioner, item.item_group)] = item.percent
#         except frappe.DoesNotExistError:
#             pass  # Skip if practitioner record not found

#     # Step 6: Format final output
#     output = []
#     for (ref_practitioner, item_group), amount in grouped.items():
#         commission_percent = commission_percent_map.get((ref_practitioner, item_group), 0)
#         output.append(frappe._dict({
#             "ref_practitioner": ref_practitioner,
#             "item_group": item_group,
#             "gross_sales": flt(amount),
#             "expense_percent": 25,
#             "commission_percent": flt(commission_percent)
#         }))
        

#     return output

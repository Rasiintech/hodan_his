# Copyright (c) 2025, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns, data = get_columns_and_data(filters)
    return columns, data


def get_columns_and_data(filters):
    from_date, to_date = filters.get('from_date'), filters.get('to')

    # Fetch source orders that actually have relevant entries
    source_orders = frappe.db.sql("""
        SELECT DISTINCT S.source_order
        FROM `tabSales Invoice` S
        JOIN `tabSales Invoice Item` I ON S.name = I.parent
        WHERE S.docstatus = 1
        AND S.posting_date BETWEEN %s AND %s
        AND I.item_group = 'Laboratory'
        AND S.source_order IS NOT NULL
    """, (from_date, to_date), as_dict=True)

    source_orders = [row.source_order for row in source_orders if row.source_order]

    if not source_orders:
        return get_columns([]), []

    columns = get_columns(source_orders)
    data = get_data(filters, source_orders)
    return columns, data


def get_data(filters, source_orders):
    from_date, to_date = filters.get('from_date'), filters.get('to')

    # Build dynamic SUM clauses for each source order
    sum_clauses = []
    for so in source_orders:
        label = so.lower().replace(" ", "_")  # Safe fieldname
        sum_clause = f"SUM(CASE WHEN S.source_order = '{so}' THEN 1 ELSE 0 END) AS `{label}`"
        sum_clauses.append(sum_clause)

    # Add total clause (includes both source orders and invoices without a source order)
    total_clause = "SUM(CASE WHEN S.source_order IN ({}) THEN 1 ELSE 0 END) + SUM(CASE WHEN S.source_order IS NULL THEN 1 ELSE 0 END) AS total".format(
        ",".join(f"'{so}'" for so in source_orders)
    )

    # Add the 'Without Source Order' clause
    without_source_clause = "SUM(CASE WHEN S.source_order IS NULL THEN 1 ELSE 0 END) AS `without_source_order`"

    query = f"""
        SELECT 
            I.item_code AS test_name,
            {', '.join(sum_clauses)},
            {total_clause},
            {without_source_clause}
        FROM 
            `tabSales Invoice` S
        JOIN 
            `tabSales Invoice Item` I ON S.name = I.parent
        JOIN 
    		`tabLab Test Template` L ON I.item_code = L.Item  
        WHERE  
            S.docstatus = 1
            AND S.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND I.item_group = 'Laboratory'
        GROUP BY 
            I.item_code
        ORDER BY total DESC
    """

    return frappe.db.sql(query, {
        "from_date": from_date,
        "to_date": to_date
    }, as_dict=1)


def get_columns(source_orders):
    columns = [
        {
            "label": "Test Name",
            "fieldname": "test_name",
            "fieldtype": "Link",
            "options": "Item",  # Link to the Item doctype
            "width": 300
            }
    ]

    for so in source_orders:
        label = so.upper()
        fieldname = so.lower().replace(" ", "_")
        columns.append({
            "label": f"{label} No Test",
            "fieldname": fieldname,
            "fieldtype": "Int",
            "width": 120
        })
    columns.append({
        "label": "Without Source",
        "fieldname": "without_source_order",
        "fieldtype": "Int",
        "width": 140
    })

    columns.append({
        "label": "Total No Test",
        "fieldname": "total",
        "fieldtype": "Int",
        "width": 140
    })

    # Add the 'Without Source Order' column
  

    return columns

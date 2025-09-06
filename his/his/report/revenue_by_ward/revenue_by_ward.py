import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = frappe._dict({})

    # Step 1: Fetch distinct income accounts dynamically from Sales Invoice Item
    income_accounts = frappe.db.sql_list(
        """SELECT DISTINCT income_account 
        FROM `tabSales Invoice Item` 
        WHERE docstatus = 1
        ORDER BY income_account"""
    )

    # If no income accounts found, return empty result
    if not income_accounts:
        return [], []

    # Step 2: Dynamically create SQL query for each income account
    income_account_columns = []
    for account in income_accounts:
        column_name = account + " - HH"
        income_account_columns.append(
            f"SUM(CASE WHEN sii.income_account = '{account}' THEN sii.amount ELSE 0 END) AS `{column_name}`"
        )

    # Step 3: Create dynamic SQL query to get all relevant invoices grouped by ward
    query = f"""
        SELECT 
            hsu.ward AS ward,
            {', '.join(income_account_columns)},
            SUM(sii.amount) AS 'Net Total'
        FROM 
            `tabInpatient Record` ir
        JOIN
            `tabSales Invoice` si ON si.inpatient_record = ir.name
        JOIN
            `tabSales Invoice Item` sii ON si.name = sii.parent
        JOIN 
            `tabInpatient Occupancy` io ON ir.name = io.parent
        JOIN 
            `tabHealthcare Service Unit` hsu ON io.service_unit = hsu.name
        WHERE 
            si.creation BETWEEN %(start_date)s AND %(end_date)s  -- Filter based on Sales Invoice creation date
        GROUP BY 
            hsu.ward
    """

    # Step 4: Set up filters for the report
    conditions = {
        'start_date': filters.get('start_date') or '2025-01-01',  # Default to a specific start date
        'end_date': filters.get('end_date') or '2025-12-31',      # Default to a specific end date
    }

    # Execute the query
    result = frappe.db.sql(query, conditions, as_dict=True)

    # Step 5: Prepare columns for the report
    columns = [
        _("Ward") + ":Data",
    ]

    # Add dynamic income account columns
    for account in income_accounts:
        columns.append(f"{account} - HH:Currency")

    columns.append(_("Net Total") + ":Currency")

    return columns, result

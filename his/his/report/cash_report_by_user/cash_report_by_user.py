
import frappe
from frappe import _
from datetime import date

def execute(filters=None):
    return get_columns(filters), get_data(filters)

def get_distinct_accounts(filters):
    _from, to, user = filters.get('from_date'), filters.get('to'), filters.get('user')
    accounts = frappe.db.sql(f"""
        SELECT DISTINCT account
            FROM (
                SELECT m.account 
                FROM `tabSales Invoice Payment` m
                LEFT JOIN `tabSales Invoice` s ON s.name = m.parent
                WHERE s.docstatus = 1 
                AND s.posting_date BETWEEN "{_from}" AND "{to}"
                UNION ALL

                SELECT p.paid_to AS account
                FROM `tabPayment Entry` p 
                WHERE p.docstatus = 1 
                AND p.posting_date BETWEEN "{_from}" AND "{to}"
                AND p.payment_type = "Receive"

                UNION ALL

                SELECT e.from_account AS account
                FROM `tabInternal Transfer` e 
                WHERE e.docstatus = 1 
                AND e.date BETWEEN "{_from}" AND "{to}"
                
                UNION ALL

                SELECT e.to_account AS account
                FROM `tabInternal Transfer` e 
                WHERE e.docstatus = 1 
                AND e.date BETWEEN "{_from}" AND "{to}"
        ) AS accounts
    """, as_dict=True)
    return [account['account'] for account in accounts]

def get_data(filters):
    _from, to, user = filters.get('from_date'), filters.get('to'), filters.get('user')
    
    # Get distinct accounts
    accounts = get_distinct_accounts(filters)
    
    # Fetch the raw data
    data = frappe.db.sql(f"""
        SELECT 
            s.owner AS `User`,
            m.account AS `Account`,
            SUM(m.amount) AS `Amount`
        FROM 
            `tabSales Invoice` s 
        LEFT JOIN 
            `tabSales Invoice Payment` m ON s.name = m.parent
        WHERE 
            s.docstatus = 1 
            AND s.posting_date BETWEEN "{_from}" AND "{to}"
        GROUP BY s.owner, m.account
        UNION ALL
        SELECT 
            p.owner AS `User`,
            p.paid_to AS `Account`,
            SUM(p.paid_amount) AS `Amount`
        FROM 
            `tabPayment Entry` p 
        WHERE 
            p.docstatus = 1 
            AND p.posting_date BETWEEN "{_from}" AND "{to}"
            AND p.payment_type = "Receive"
        GROUP BY p.owner, p.paid_to

        UNION ALL

        SELECT 
            e.from_user AS `User`,
            e.from_account AS `Account`, 
            SUM(-1 * e.transferred_amount) AS `Amount`
        FROM 
            `tabInternal Transfer` e 
        WHERE 
            e.docstatus = 1 
            AND e.date BETWEEN "{_from}" AND "{to}"
        GROUP BY e.from_user, e.from_account
        
        UNION ALL

        SELECT 
            e.to_user AS `User`,
            e.to_account AS `Account`, 
            SUM(e.transferred_amount) AS `Amount`
        FROM 
            `tabInternal Transfer` e 
        WHERE 
            e.docstatus = 1 
            AND e.date BETWEEN "{_from}" AND "{to}"
        GROUP BY e.to_user, e.to_account
    """, as_dict=True)
    
    # Initialize the result list
    result = []

    # Transform the data
    user_data = {}
    for row in data:
        user = row['User']
        account = row['Account']
        amount = row['Amount']

        if account is None:
            continue  # Skip rows where 'Account' is None

        if user not in user_data:
            user_data[user] = {
                'user': frappe.db.get_value("User", user, "full_name"),
                **{acc: 0 for acc in accounts},
                'total': 0  # Initialize total
            }
        user_data[user][account] += amount
        user_data[user]['total'] += amount  # Update the total
    
    # Convert user_data to result list
    result = [value for key, value in user_data.items()]
    
    return result

def get_columns(filters):
    accounts = get_distinct_accounts(filters)
    columns = [
        {
            "label": _("User"),
            "fieldtype": "Data",
            "fieldname": "user",
            "width": 150,
        }
    ]
    
    for account in accounts:
        columns.append({
            "label": _(account),
            "fieldtype": "Currency",
            "fieldname": account,
            "width": 150,
        })
    
    # Adding Total column
    columns.append({
        "label": _("Total"),
        "fieldtype": "Currency",
        "fieldname": "total",
        "width": 100,
    })
    
    return columns
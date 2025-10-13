import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.financial_statements import get_period_list

def execute(filters=None):
    if not filters:
        filters = {}

    # validate_filters(filters)

    company = filters.get("company")
    period_1 = get_periods(filters.get("from_date_1"), filters.get("to_date_1"), filters.get("periodicity"), company)
    period_2 = get_periods(filters.get("from_date_2"), filters.get("to_date_2"), filters.get("periodicity"), company)

    gl_values_1 = get_gl_totals(filters, filters.get("from_date_1"), filters.get("to_date_1"))
    gl_values_2 = get_gl_totals(filters, filters.get("from_date_2"), filters.get("to_date_2"))

    account_tree = build_account_tree(company, gl_values_1, gl_values_2)
    aggregate_account_tree(account_tree)
    data = flatten_tree(account_tree)

    new_data = []

    income_row = next((row for row in data if row.get("account_name") == "Income"), None)
    expense_row = next((row for row in data if row.get("account_name") == "Expenses"), None)

    for row in data:
        if row.get("root_type") == "Income":
            new_data.append(row)

    if income_row:
        new_data.append({
            "account_name": _("Total Income (Credit)"),
            "period_1": income_row["period_1"],
            "period_2": income_row["period_2"],
            "difference": income_row["period_2"] - income_row["period_1"],
            "percentage_change": ((income_row["period_2"] - income_row["period_1"]) / income_row["period_1"] * 100) if income_row["period_1"] else 0,
            "bold": 1
        })

    for row in data:
        if row.get("root_type") == "Expense":
            new_data.append(row)

    if expense_row:
        new_data.append({
            "account_name": _("Total Expense (Debit)"),
            "period_1": expense_row["period_1"],
            "period_2": expense_row["period_2"],
            "difference": expense_row["period_2"] - expense_row["period_1"],
            "percentage_change": ((expense_row["period_2"] - expense_row["period_1"]) / expense_row["period_1"] * 100) if expense_row["period_1"] else 0,
            "bold": 1
        })

    new_data.append({})
    if income_row and expense_row:
        net_profit_1 = income_row["period_1"] - expense_row["period_1"]
        net_profit_2 = income_row["period_2"] - expense_row["period_2"]
        net_diff = net_profit_2 - net_profit_1
        net_pct = (net_diff / abs(net_profit_1) * 100) if net_profit_1 else 0


        new_data.append({
            "account_name": _("Profit for the year"),
            "period_1": net_profit_1,
            "period_2": net_profit_2,
            "difference": net_diff,
            "percentage_change": net_pct,
            "bold": 1
        })

    return get_columns(), new_data

# def validate_filters(filters):
#     if not (filters.get("from_date_1") and filters.get("to_date_1") and filters.get("from_date_2") and filters.get("to_date_2")):
#         frappe.throw(_("Please select both From and To dates for Period 1 and Period 2"))

def get_periods(from_date, to_date, periodicity, company=None):
    from_fy = frappe.get_value("Fiscal Year", {"year_start_date": ["<=", from_date]}, "name")
    to_fy = frappe.get_value("Fiscal Year", {"year_start_date": ["<=", to_date]}, "name")
    return get_period_list(
        period_start_date=from_date,
        period_end_date=to_date,
        from_fiscal_year=from_fy,
        to_fiscal_year=to_fy,
        periodicity=periodicity,
        company=company,
        filter_based_on="Date Range"
    )

def get_gl_totals(filters, from_date, to_date):
    conditions = [
        "gle.posting_date BETWEEN %(from_date)s AND %(to_date)s",
        "gle.company = %(company)s"
    ]
    if filters.get("cost_center"):
        conditions.append("gle.cost_center = %(cost_center)s")
    if filters.get("department"):
        conditions.append("gle.department = %(department)s")

    sql = f"""
        SELECT 
            gle.account, 
            acc.root_type,
            SUM(CASE 
                WHEN acc.root_type = 'Income' THEN gle.credit - gle.debit
                WHEN acc.root_type = 'Expense' THEN gle.debit - gle.credit
                ELSE 0
            END) AS balance
        FROM `tabGL Entry` gle
        JOIN `tabAccount` acc ON gle.account = acc.name
        WHERE {" AND ".join(conditions)}
        AND acc.root_type IN ('Income', 'Expense')
        GROUP BY gle.account
    """

    results = frappe.db.sql(sql, {
        "from_date": from_date,
        "to_date": to_date,
        "company": filters.get("company"),
        "cost_center": filters.get("cost_center"),
        "department": filters.get("department"),
    }, as_dict=True)

    return {r.account: r.balance for r in results}

def build_account_tree(company, values_1, values_2):
    accounts = frappe.get_all("Account", filters={"company": company, "root_type": ["in", ["Income", "Expense"]]}, fields=["name", "parent_account", "account_name", "root_type", "is_group", "lft", "rgt"])
    name_map, children_map = {}, {}

    for acc in accounts:
        acc.update({"children": [], "period_1": flt(values_1.get(acc.name, 0)), "period_2": flt(values_2.get(acc.name, 0)), "indent": 0})
        name_map[acc.name] = acc

    for acc in accounts:
        parent = acc.parent_account
        if parent in name_map:
            acc["indent"] = name_map[parent]["indent"] + 1
            name_map[parent]["children"].append(acc)

    return [acc for acc in name_map.values() if not acc.parent_account]

def aggregate_account_tree(nodes):
    for node in nodes:
        aggregate_account_tree(node["children"])
        for child in node["children"]:
            node["period_1"] += child["period_1"]
            node["period_2"] += child["period_2"]

def flatten_tree(nodes, output=None):
    if output is None:
        output = []
    for node in nodes:
        if node["period_1"] == 0 and node["period_2"] == 0 and not node["children"]:
            continue
        diff = node["period_2"] - node["period_1"]
        pct = (diff / node["period_1"] * 100) if node["period_1"] else 0
        output.append({
            "account": node["name"],
            "account_name": node["account_name"],
            "root_type": node["root_type"],
            "period_1": node["period_1"],
            "period_2": node["period_2"],
            "difference": diff,
            "percentage_change": pct,
            "indent": node["indent"],
            "bold": 1 if node["is_group"] else 0
        })
        flatten_tree(node["children"], output)
    return output

def get_columns():
    return [
        {"label": _("Account"), "fieldname": "account_name", "fieldtype": "Data", "width": 300},
        {"label": _("Period 1"), "fieldname": "period_1", "fieldtype": "Currency", "width": 120},
        {"label": _("Period 2"), "fieldname": "period_2", "fieldtype": "Currency", "width": 120},
        {"label": _("Difference"), "fieldname": "difference", "fieldtype": "Currency", "width": 120},
        {"label": _("Change (%)"), "fieldname": "percentage_change", "fieldtype": "Percent", "width": 100}
    ]
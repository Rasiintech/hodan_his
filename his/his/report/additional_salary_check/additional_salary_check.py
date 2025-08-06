import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    if not from_date or not to_date:
        frappe.throw("Please set both From Date and To Date")

    # Step 1: Get used components in filtered date range
    used_components = frappe.db.sql("""
        SELECT DISTINCT salary_component, type
        FROM `tabAdditional Salary`
        WHERE docstatus = 1
          AND (
              (is_recurring = 1 AND from_date <= %(to_date)s AND (to_date IS NULL OR to_date >= %(from_date)s))
              OR
              (is_recurring = 0 AND payroll_date BETWEEN %(from_date)s AND %(to_date)s)
          )
    """, {"from_date": from_date, "to_date": to_date}, as_dict=True)

    if not used_components:
        return [], []

    # Sort: Earnings first, then Deductions
    sorted_components = sorted(used_components, key=lambda x: (x["type"] != "Earning", x["salary_component"]))

    # Step 2: Build dynamic fields
    dynamic_fields = ["ssa.base AS `Basic Salary`"]

    for comp in sorted_components:
        label = f"{comp['salary_component']} ({comp['type']})"
        sql = f"""SUM(CASE WHEN add_sal.salary_component = '{comp['salary_component']}' THEN add_sal.amount ELSE 0 END) AS `{label}`"""
        dynamic_fields.append(sql)

    # Totals (base + earnings)
    dynamic_fields += [
        """(ssa.base + SUM(CASE WHEN add_sal.type = 'Earning' THEN add_sal.amount ELSE 0 END)) AS `Total Earning`""",
        "SUM(CASE WHEN add_sal.type = 'Deduction' THEN add_sal.amount ELSE 0 END) AS `Total Deduction`",
        """(ssa.base + SUM(CASE WHEN add_sal.type = 'Earning' THEN add_sal.amount ELSE 0 END))
         - SUM(CASE WHEN add_sal.type = 'Deduction' THEN add_sal.amount ELSE 0 END) AS `Net Amount`"""
    ]

    # Step 3: Final query
    query = f"""
    SELECT
        add_sal.employee,
        add_sal.employee_name,
        {','.join(dynamic_fields)}
    FROM `tabAdditional Salary` add_sal
    LEFT JOIN `tabSalary Structure Assignment` ssa
        ON ssa.employee = add_sal.employee
    LEFT JOIN `tabEmployee` emp
        ON emp.name = add_sal.employee
    WHERE
        add_sal.docstatus = 1
        AND emp.status = 'Active'
        AND ssa.base IS NOT NULL
        AND (
            (add_sal.is_recurring = 1 AND add_sal.from_date <= %(to_date)s AND (add_sal.to_date IS NULL OR add_sal.to_date >= %(from_date)s))
            OR
            (add_sal.is_recurring = 0 AND add_sal.payroll_date BETWEEN %(from_date)s AND %(to_date)s)
        )
    GROUP BY add_sal.employee, add_sal.employee_name, ssa.base
    ORDER BY add_sal.employee
    """

    results = frappe.db.sql(query, {"from_date": from_date, "to_date": to_date}, as_dict=True)

    # Step 4: Report columns
    columns = [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee"},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data"},
        {"label": "Basic Salary", "fieldname": "Basic Salary", "fieldtype": "Currency"},
    ]

    for comp in sorted_components:
        label = f"{comp['salary_component']} ({comp['type']})"
        columns.append({"label": label, "fieldname": label, "fieldtype": "Currency"})

    columns += [
        {"label": "Total Earning", "fieldname": "Total Earning", "fieldtype": "Currency"},
        {"label": "Total Deduction", "fieldname": "Total Deduction", "fieldtype": "Currency"},
        {"label": "Net Amount", "fieldname": "Net Amount", "fieldtype": "Currency"},
    ]

    return columns, results

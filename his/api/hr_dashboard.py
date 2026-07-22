from __future__ import annotations

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import add_months, flt, getdate, nowdate
from his.his.report.employee_payable_summary.employee_payable_summary import execute as execute_employee_payable_summary


PAYROLL_RECEIVABLE_ACCOUNT = "Payroll Receivable - HH"
EMPLOYEE_ADVANCE_ACCOUNT = "1610 - Employee Advances - HH"


@frappe.whitelist()
def get_dashboard_data(from_date=None, to_date=None, department=None):
	_require_hr_access()

	to_date = getdate(to_date or nowdate())
	from_date = getdate(from_date or to_date.replace(month=1, day=1))
	department = department or None

	if from_date > to_date:
		from_date, to_date = to_date, from_date

	components = _get_component_columns(from_date, to_date, department)

	return {
		"filters": {
			"from_date": from_date,
			"to_date": to_date,
			"department": department,
		},
		"cards": _get_cards(from_date, to_date, department),
		"employees_by_department": _get_employees_by_department(from_date, to_date, department),
		"salary_trend": _get_salary_trend(from_date, to_date, department),
		"commission_trend": _get_commission_trend(from_date, to_date, department),
		"employee_exit_trend": _get_employee_exit_trend(from_date, to_date, department),
		"department_expense": _get_department_expense(from_date, to_date, components, department),
		"component_columns": components,
		"advances": _get_advances(from_date, to_date, department),
		"leaves": _get_leaves(from_date, to_date, department),
	}


def _require_hr_access():
	if not frappe.has_permission("Employee", "read"):
		frappe.throw(_("Not permitted to view HR dashboard"), frappe.PermissionError)


def _get_cards(from_date, to_date, department=None):
	employee_filters = _with_department({}, department)
	total = _count("Employee", employee_filters)
	active = _count("Employee", _with_department({"status": "Active"}, department))
	left = _count("Employee", _with_department({"status": ["in", ["Left", "Inactive"]]}, department))
	female = _count("Employee", _with_department({"gender": "Female"}, department))
	male = _count("Employee", _with_department({"gender": "Male"}, department))
	retention = (active / total * 100) if total else 0
	salary_stats = _get_salary_stats(from_date, to_date, department)

	return [
		{"label": "Total Hired Employee", "value": total, "format": "number"},
		{"label": "Active Employee", "value": active, "format": "number"},
		{"label": "Left Employee", "value": left, "format": "number"},
		{"label": "Retention Rate", "value": retention, "format": "percent"},
		{"label": "Female", "value": female, "format": "number"},
		{"label": "Male", "value": male, "format": "number"},
		{"label": "Total Salary", "value": salary_stats["total"], "format": "currency"},
		{"label": "Max Salary", "value": salary_stats["max"], "format": "currency_compact"},
		{"label": "Min Salary", "value": salary_stats["min"], "format": "currency"},
	]


def _get_salary_stats(from_date, to_date, department=None):
	if _doctype_exists("Salary Structure Assignment"):
		return _get_structure_salary_stats(to_date, department)

	if not _doctype_exists("Salary Slip"):
		return {"total": 0, "max": 0, "min": 0}

	department_condition, filters = _department_sql("department", department)
	filters.update({"from_date": from_date, "to_date": to_date})
	rows = frappe.db.sql(
		f"""
		select
			coalesce(sum(rounded_total), sum(net_pay), 0) as total,
			coalesce(max(rounded_total), max(net_pay), 0) as max_salary,
			coalesce(min(nullif(rounded_total, 0)), min(nullif(net_pay, 0)), 0) as min_salary
		from `tabSalary Slip`
		where docstatus = 1
			and posting_date between %(from_date)s and %(to_date)s
			{department_condition}
		""",
		filters,
		as_dict=1,
	)
	row = rows[0] if rows else {}
	return {
		"total": flt(row.get("total"), 2),
		"max": flt(row.get("max_salary"), 2),
		"min": flt(row.get("min_salary"), 2),
	}


def _get_structure_salary_stats(to_date, department=None):
	department_condition, filters = _department_sql(
		"coalesce(ssa.department, emp.department, 'No Department')",
		department,
	)
	filters.update({"to_date": to_date})
	rows = frappe.db.sql(
		f"""
		select
			coalesce(sum(ssa.base), 0) as total,
			coalesce(max(ssa.base), 0) as max_salary,
			coalesce(min(nullif(ssa.base, 0)), 0) as min_salary
		from `tabEmployee` emp
		inner join `tabSalary Structure Assignment` ssa
			on ssa.name = (
				select latest_ssa.name
				from `tabSalary Structure Assignment` latest_ssa
				where latest_ssa.docstatus = 1
					and latest_ssa.employee = emp.name
					and latest_ssa.from_date <= %(to_date)s
				order by latest_ssa.from_date desc, latest_ssa.modified desc
				limit 1
			)
		where emp.docstatus < 2
			{department_condition}
		""",
		filters,
		as_dict=1,
	)
	row = rows[0] if rows else {}
	return {
		"total": flt(row.get("total"), 2),
		"max": flt(row.get("max_salary"), 2),
		"min": flt(row.get("min_salary"), 2),
	}


def _get_employees_by_department(from_date, to_date, department=None):
	if not _doctype_exists("Employee"):
		return []

	if _doctype_exists("Salary Structure Assignment"):
		return _get_employee_and_structure_salary_by_department(from_date, to_date, department)

	department_condition, filters = _department_sql("department", department)
	filters.update({"from_date": from_date, "to_date": to_date})
	rows = frappe.db.sql(
		f"""
		select
			coalesce(department, 'No Department') as department,
			count(name) as employees
		from `tabEmployee`
		where docstatus < 2
			and (date_of_joining is null or date_of_joining <= %(to_date)s)
			and (relieving_date is null or relieving_date >= %(from_date)s)
			{department_condition}
		group by coalesce(department, 'No Department')
		order by employees desc, department asc
		limit 28
		""",
		filters,
		as_dict=1,
	)

	departments = [row.department for row in rows]
	salary_by_department = _get_salary_by_department(from_date, to_date, departments, department)

	return [
		{
			"department": row.department,
			"employees": row.employees,
			"salary": flt(salary_by_department.get(row.department), 2),
		}
		for row in rows
	]


def _get_employee_and_structure_salary_by_department(from_date, to_date, department=None):
	department_condition, filters = _department_sql(
		"coalesce(ssa.department, emp.department, 'No Department')",
		department,
	)
	filters.update({"from_date": from_date, "to_date": to_date})
	rows = frappe.db.sql(
		f"""
		select
			coalesce(ssa.department, emp.department, 'No Department') as department,
			count(emp.name) as employees,
			coalesce(sum(ssa.base), 0) as salary
		from `tabEmployee` emp
		left join `tabSalary Structure Assignment` ssa
			on ssa.name = (
				select latest_ssa.name
				from `tabSalary Structure Assignment` latest_ssa
				where latest_ssa.docstatus = 1
					and latest_ssa.employee = emp.name
					and latest_ssa.from_date <= %(to_date)s
				order by latest_ssa.from_date desc, latest_ssa.modified desc
				limit 1
			)
		where emp.docstatus < 2
			and (emp.date_of_joining is null or emp.date_of_joining <= %(to_date)s)
			and (emp.relieving_date is null or emp.relieving_date >= %(from_date)s)
			{department_condition}
		group by coalesce(ssa.department, emp.department, 'No Department')
		order by employees desc, department asc
		limit 28
		""",
		filters,
		as_dict=1,
	)

	return [
		{
			"department": row.department,
			"employees": row.employees,
			"salary": flt(row.salary, 2),
		}
		for row in rows
	]


def _get_salary_by_department(from_date, to_date, departments=None, department=None):
	if not _doctype_exists("Salary Slip"):
		return {}

	filters = {
		"from_date": from_date,
		"to_date": to_date,
	}
	department_condition = ""
	if departments:
		filters["departments"] = departments
		department_condition = "and coalesce(department, 'No Department') in %(departments)s"
	elif department:
		filters["department"] = department
		department_condition = "and department = %(department)s"

	rows = frappe.db.sql(
		f"""
		select
			coalesce(department, 'No Department') as department,
			coalesce(sum(rounded_total), sum(net_pay), 0) as salary
		from `tabSalary Slip`
		where docstatus = 1
			and posting_date between %(from_date)s and %(to_date)s
			{department_condition}
		group by coalesce(department, 'No Department')
		""",
		filters,
		as_dict=1,
	)
	return {row.department: row.salary for row in rows}


def _get_salary_trend(from_date, to_date, department=None):
	return _get_component_trend(from_date, to_date, "Basic", department)


def _get_commission_trend(from_date, to_date, department=None):
	return _get_component_trend(from_date, to_date, "Doctor Commission", department)


def _get_component_trend(from_date, to_date, component, department=None):
	if not _doctype_exists("Salary Slip"):
		return []

	months = _month_ranges(from_date, to_date)
	trend = []

	if not months:
		return trend

	def get_basic_salary(month_start, month_end):
		department_condition, filters = _department_sql("ss.department", department)
		filters.update({"month_start": month_start, "month_end": month_end})
		rows = frappe.db.sql(
			f"""
			select coalesce(sum(sd.amount), 0) as salary
			from `tabSalary Slip` ss
			inner join `tabSalary Detail` sd on sd.parent = ss.name
			where ss.docstatus = 1
				and sd.parentfield = 'earnings'
				and sd.salary_component = %(component)s
				and ss.posting_date between %(month_start)s and %(month_end)s
				{department_condition}
			""",
			{**filters, "component": component},
			as_dict=1,
		)
		return flt(rows[0].salary if rows else 0, 2)

	previous_salary = get_basic_salary(add_months(months[0][0], -1), months[0][0] - timedelta(days=1))

	for month_start, month_end in months:
		salary = get_basic_salary(month_start, month_end)
		trend.append(
			{
				"label": month_start.strftime("%Y-%m"),
				"salary": salary,
				"previous_salary": previous_salary,
			}
		)
		previous_salary = salary

	return trend


def _get_employee_exit_trend(from_date, to_date, department=None):
	if not _doctype_exists("Employee"):
		return []

	months = _month_ranges(from_date, to_date)
	trend = []

	if not months:
		return trend

	def get_exit_count(month_start, month_end):
		department_condition, filters = _department_sql("department", department)
		filters.update({"month_start": month_start, "month_end": month_end})
		rows = frappe.db.sql(
			f"""
			select count(name) as employees
			from `tabEmployee`
			where docstatus < 2
				and relieving_date between %(month_start)s and %(month_end)s
				{department_condition}
			""",
			filters,
			as_dict=1,
		)
		return rows[0].employees if rows else 0

	previous_employees = get_exit_count(add_months(months[0][0], -1), months[0][0] - timedelta(days=1))

	for month_start, month_end in months:
		employees = get_exit_count(month_start, month_end)
		trend.append(
			{
				"label": month_start.strftime("%Y-%m"),
				"value": employees,
				"previous_value": previous_employees,
			}
		)
		previous_employees = employees

	return trend


def _get_department_expense(from_date, to_date, components, department=None):
	if not _doctype_exists("Salary Slip"):
		return []

	department_condition, filters = _department_sql("department", department)
	filters.update({"from_date": from_date, "to_date": to_date})
	rows = frappe.db.sql(
		f"""
		select
			coalesce(department, 'No Department') as department,
			count(distinct employee) as employees,
			coalesce(sum(gross_pay), 0) as salary,
			coalesce(sum(rounded_total), sum(net_pay), 0) as total
		from `tabSalary Slip`
		where docstatus = 1
			and posting_date between %(from_date)s and %(to_date)s
			{department_condition}
		group by coalesce(department, 'No Department')
		order by total desc
		limit 24
		""",
		filters,
		as_dict=1,
	)

	component_totals = _get_component_totals(from_date, to_date, components, department)
	data = []
	for row in rows:
		item = {
			"department": row.department,
			"employees": row.employees,
			"salary": flt(row.salary, 2),
			"total": flt(row.total, 2),
			"components": {},
		}
		for component in components:
			item["components"][component] = flt(
				component_totals.get((row.department, component), 0),
				2,
			)
		data.append(item)

	return data


def _get_component_columns(from_date, to_date, department=None):
	preferred = ["Doctor Commission", "Employee Commission", "Food Allowance", "Eid Bonus"]
	if not _doctype_exists("Salary Slip"):
		return preferred

	department_condition, filters = _department_sql("ss.department", department)
	filters.update({"from_date": from_date, "to_date": to_date, "preferred": preferred})
	existing = frappe.db.sql(
		f"""
		select distinct sd.salary_component
		from `tabSalary Detail` sd
		inner join `tabSalary Slip` ss on ss.name = sd.parent
		where ss.docstatus = 1
			and sd.parentfield = 'earnings'
			and ss.posting_date between %(from_date)s and %(to_date)s
			and sd.salary_component in %(preferred)s
			{department_condition}
		""",
		filters,
		as_dict=1,
	)
	columns = [row.salary_component for row in existing]

	if len(columns) >= 4:
		return columns[:4]

	department_condition, filters = _department_sql("ss.department", department)
	filters.update({"from_date": from_date, "to_date": to_date})
	top_components = frappe.db.sql(
		f"""
		select sd.salary_component, sum(sd.amount) as amount
		from `tabSalary Detail` sd
		inner join `tabSalary Slip` ss on ss.name = sd.parent
		where ss.docstatus = 1
			and sd.parentfield = 'earnings'
			and ss.posting_date between %(from_date)s and %(to_date)s
			{department_condition}
		group by sd.salary_component
		order by amount desc
		limit 8
		""",
		filters,
		as_dict=1,
	)

	for row in top_components:
		if row.salary_component not in columns:
			columns.append(row.salary_component)
		if len(columns) == 4:
			break

	return columns or preferred


def _get_component_totals(from_date, to_date, components, department=None):
	if not components or not _doctype_exists("Salary Slip"):
		return {}

	department_condition, filters = _department_sql("ss.department", department)
	filters.update({"from_date": from_date, "to_date": to_date, "components": components})
	rows = frappe.db.sql(
		f"""
		select
			coalesce(ss.department, 'No Department') as department,
			sd.salary_component,
			sum(sd.amount) as amount
		from `tabSalary Detail` sd
		inner join `tabSalary Slip` ss on ss.name = sd.parent
		where ss.docstatus = 1
			and sd.parentfield = 'earnings'
			and ss.posting_date between %(from_date)s and %(to_date)s
			and sd.salary_component in %(components)s
			{department_condition}
		group by coalesce(ss.department, 'No Department'), sd.salary_component
		""",
		filters,
		as_dict=1,
	)
	return {(row.department, row.salary_component): row.amount for row in rows}


def _get_advances(from_date, to_date, department=None):
	if not _doctype_exists("Employee"):
		return {"rows": [], "total_advance": 0, "total_receivable": 0}

	advance_map = _get_employee_payable_report_balances(EMPLOYEE_ADVANCE_ACCOUNT, to_date)
	receivable_map = _get_employee_payable_report_balances(PAYROLL_RECEIVABLE_ACCOUNT, to_date)

	employees = frappe.get_all(
		"Employee",
		filters=_with_department({"docstatus": ["<", 2]}, department),
		fields=["name", "employee_name"],
		order_by="employee_name asc",
	)

	rows = []
	for employee in employees:
		advance = advance_map.get(employee.name, 0)
		receivable = receivable_map.get(employee.name, 0)

		if advance or receivable:
			rows.append(
				{
					"employee_name": employee.employee_name or employee.name,
					"advance": flt(advance, 2),
					"receivable": flt(receivable, 2),
				}
			)

	total_advance = flt(sum(row["advance"] for row in rows), 2)
	total_receivable = flt(sum(row["receivable"] for row in rows), 2)

	rows.sort(key=lambda row: (abs(row["receivable"]), abs(row["advance"])), reverse=True)
	rows = rows[:24]

	return {
		"rows": rows,
		"total_advance": total_advance,
		"total_receivable": total_receivable,
	}


def _get_leaves(from_date, to_date, department=None):
	if not _doctype_exists("Leave Application"):
		return {"rows": [], "totals": {"active": 0, "pending": 0, "ending_today": 0}}

	department_condition, filters = _department_sql("department", department)
	filters.update({"from_date": from_date, "to_date": to_date})
	rows = frappe.db.sql(
		f"""
		select
			leave_type,
			sum(case when status = 'Approved' and from_date <= %(to_date)s and to_date >= %(from_date)s then 1 else 0 end) as active,
			sum(case when status = 'Open' then 1 else 0 end) as pending,
			sum(case when to_date = %(to_date)s then 1 else 0 end) as ending_today
		from `tabLeave Application`
		where docstatus < 2
			and from_date <= %(to_date)s
			and to_date >= %(from_date)s
			{department_condition}
		group by leave_type
		order by active desc, pending desc, leave_type asc
		limit 12
		""",
		filters,
		as_dict=1,
	)
	data = [
		{
			"leave_type": row.leave_type or "Not Set",
			"active": int(row.active or 0),
			"pending": int(row.pending or 0),
			"ending_today": int(row.ending_today or 0),
		}
		for row in rows
	]

	return {
		"rows": data,
		"totals": {
			"active": sum(row["active"] for row in data),
			"pending": sum(row["pending"] for row in data),
			"ending_today": sum(row["ending_today"] for row in data),
		},
	}


def _month_ranges(from_date, to_date):
	month_start = from_date.replace(day=1)
	months = []
	while month_start <= to_date:
		next_month = add_months(month_start, 1)
		month_end = min(next_month - timedelta(days=1), to_date)
		months.append((month_start, month_end))
		month_start = next_month

	return months[-12:]


def _count(doctype, filters=None):
	if not _doctype_exists(doctype):
		return 0

	return frappe.db.count(doctype, filters or {})


def _with_department(filters, department):
	if department:
		filters = dict(filters)
		filters["department"] = department
	return filters


def _get_employee_payable_report_balances(account, report_date):
	if not frappe.db.exists("Account", account):
		return {}

	company = frappe.defaults.get_user_default("Company") or frappe.db.get_value("Account", account, "company")
	_, data = execute_employee_payable_summary(
		{
			"company": company,
			"report_date": report_date,
			"party_account": account,
			"ageing_based_on": "Due Date",
			"range1": 30,
			"range2": 60,
			"range3": 90,
			"range4": 120,
		}
	)

	return {
		row.party: flt(row.outstanding, 2)
		for row in data
		if row.get("party") and flt(row.get("outstanding"))
	}


def _department_sql(fieldname, department):
	if not department:
		return "", {}

	return f"and {fieldname} = %(department)s", {"department": department}


def _doctype_exists(doctype):
	return frappe.db.exists("DocType", doctype)

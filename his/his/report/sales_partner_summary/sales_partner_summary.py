import frappe
from frappe import _, msgprint

def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_entries(filters)

	return columns, data

def get_columns():
	return [
		{
			"label": _("Employee ID"),
			"fieldname": "employee_ids",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 140,
		},
		{
			"label": _("Sales Partner"),
			"fieldname": "sales_partner",
			"fieldtype": "Link",
			"options": "Sales Partner",
			"width": 180,
		},
		{
			"label": _("Commission Rate (%)"),
			"fieldname": "commission_rate",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Total Commission"),
			"fieldname": "commission",
			"fieldtype": "Currency",
			"width": 140,
		},
	]

def get_entries(filters):
	date_field = "transaction_date" if filters.get("doctype") == "Sales Order" else "posting_date"
	conditions = get_conditions(filters, date_field)

	entries = frappe.db.sql(
		"""
		SELECT
			sp.employee_ids,
			dt.sales_partner,
			dt.commission_rate,
			SUM((dt_item.base_net_amount * dt.commission_rate) / 100) AS commission

		FROM
			`tab{doctype}` dt
		JOIN
			`tab{doctype} Item` dt_item ON dt.name = dt_item.parent
		JOIN
			`tabSales Partner` sp ON dt.sales_partner = sp.name
		WHERE
			{cond}
			AND dt.docstatus = 1
			AND dt.sales_partner IS NOT NULL
			AND dt.sales_partner != ''
			AND sp.partner_type = 'Employee'
			AND dt.so_type="Cashiers"
		GROUP BY
			sp.employee_ids, dt.sales_partner, dt.commission_rate
		ORDER BY
			dt.sales_partner
		""".format(
			date_field=date_field,
			doctype=filters.get("doctype"),
			cond=conditions
		),
		filters,
		as_dict=1,
	)

	return entries

def get_conditions(filters, date_field):
	conditions = "1=1"

	for field in ["company", "customer", "territory", "sales_partner"]:
		if filters.get(field):
			conditions += f" AND dt.{field} = %({field})s"

	if filters.get("from_date"):
		conditions += f" AND dt.{date_field} >= %(from_date)s"

	if filters.get("to_date"):
		conditions += f" AND dt.{date_field} <= %(to_date)s"

	if not filters.get("show_return_entries"):
		conditions += " AND dt_item.qty > 0.0"

	if filters.get("brand"):
		conditions += " AND dt_item.brand = %(brand)s"

	if filters.get("item_group"):
		lft, rgt = frappe.get_cached_value("Item Group", filters["item_group"], ["lft", "rgt"])
		conditions += f""" AND dt_item.item_group IN (
			SELECT name FROM `tabItem Group`
			WHERE lft >= {lft} AND rgt <= {rgt}
		)"""

	return conditions

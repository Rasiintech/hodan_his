# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_months, date_diff, flt, formatdate, getdate


REVENUE_DISCOUNT_RATE = 0.10
ANCILLARY_MONTHLY_BUDGET = -114.0
AMOUNT_FIELDS = (
	"monthly_budget",
	"daily_budget",
	"weekly_budget",
	"period_budget",
	"actual",
	"budget_variance",
	"last_month_actual",
	"last_month_variance",
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.company:
		filters.company = frappe.defaults.get_user_default("Company")

	from_date = getdate(filters.from_date)
	to_date = getdate(filters.to_date)
	if from_date > to_date:
		frappe.throw(_("From Date cannot be after To Date"))

	days = date_diff(to_date, from_date) + 1
	month_label = formatdate(from_date, "MMM yyyy")  # e.g. Sep 2026
	last_from = add_months(from_date, -1)
	last_to = add_months(to_date, -1)
	last_month_label = formatdate(last_from, "MMM")

	columns = get_columns(filters, month_label, days, last_month_label)

	if from_date.month == to_date.month and from_date.year == to_date.year:
		period_label = "{0} - {1} {2}".format(
			from_date.day, to_date.day, formatdate(from_date, "MMMM yyyy")
		)
	else:
		period_label = "{0} - {1}".format(
			formatdate(from_date, "d MMMM yyyy"), formatdate(to_date, "d MMMM yyyy")
		)

	data = []
	rev_total, revenue_discount = build_section(
		filters, "Income", from_date, to_date, last_from, last_to, days, data, period_label
	)
	income_after_discount = add_revenue_discount_rows(data, rev_total, revenue_discount)
	data.append({})
	exp_total, expense_discount = build_section(
		filters, "Expense", from_date, to_date, last_from, last_to, days, data, period_label
	)
	data.append({})

	net = {"account_group": _("Net Income"), "bold": 1}
	for key in AMOUNT_FIELDS:
		net[key] = flt(income_after_discount.get(key)) - flt(exp_total.get(key))
	data.append(net)

	return columns, data


def get_columns(filters, month_label, days, last_month_label):
	def col(label, fieldname, width=140):
		return {
			"label": label,
			"fieldname": fieldname,
			"fieldtype": "Currency",
			"options": "currency",
			"precision": 2,
			"width": width,
		}

	return [
		{
			"label": _("Account Group"),
			"fieldname": "account_group",
			"fieldtype": "Data",
			"width": 280,
		},
		col(_("{0} Budget").format(month_label), "monthly_budget"),
		col(_("Daily"), "daily_budget", 110),
		col(_("Weekly"), "weekly_budget", 110),
		col(_("{0} Days Budget").format(days), "period_budget"),
		col(_("{0} Days System").format(days), "actual"),
		col(_("Variance Budget"), "budget_variance"),
		col(_("{0} Days {1} System").format(days, last_month_label), "last_month_actual", 160),
		col(_("Variance {0} & {1}").format(last_month_label, month_label.split(" ")[0]), "last_month_variance", 160),
		{"label": "", "fieldname": "currency", "fieldtype": "Data", "hidden": 1},
	]


def build_section(filters, root_type, from_date, to_date, last_from, last_to, days, data, period_label):
	"""Append header, group rows and total row for one root type; return the total row."""
	currency = frappe.get_cached_value("Company", filters.company, "default_currency")

	accounts = frappe.get_all(
		"Account",
		filters={"company": filters.company, "root_type": root_type},
		fields=["name", "account_name", "parent_account", "is_group", "lft", "rgt"],
		order_by="lft",
	)
	if not accounts:
		return frappe._dict(), frappe._dict()

	by_name = {d.name: d for d in accounts}
	roots = [d for d in accounts if not d.parent_account or d.parent_account not in by_name]

	rows_accounts = []
	for root in roots:
		children = [account for account in accounts if account.parent_account == root.name]
		if root_type == "Expense":
			# The expense snapshot is grouped by the main accounts directly below
			# TOTAL EXPENSES. Each row includes every account below that group.
			rows_accounts.extend(children)
			continue

		# Revenue keeps its existing presentation: groups one level below the
		# root's main children, or a main child itself when it has no children.
		for child in children:
			grandchildren = [account for account in accounts if account.parent_account == child.name]
			if grandchildren:
				rows_accounts.extend(grandchildren)
			else:
				rows_accounts.append(child)
	rows_accounts.sort(key=lambda d: d.lft)

	actual_map = get_gl_sums(filters, root_type, from_date, to_date)
	last_actual_map = get_gl_sums(filters, root_type, last_from, last_to)
	budget_map = get_budget_plan_map(root_type, from_date)

	leaf_accounts = [d for d in accounts if not d.is_group]

	section_label = (
		_("Revenue Main Group Budget") if root_type == "Income" else _("Expense Main Group Budget")
	)
	data.append({"account_group": f"{section_label} | {period_label}", "is_title": 1})

	total = frappe._dict(
		account_group=_("Total {0}").format(_("Revenue") if root_type == "Income" else _("Expense")),
		bold=1,
		monthly_budget=0,
		daily_budget=0,
		weekly_budget=0,
		period_budget=0,
		actual=0,
		budget_variance=0,
		last_month_actual=0,
		last_month_variance=0,
	)
	discount_row = None

	for grp in rows_accounts:
		monthly = actual = last_actual = 0.0
		for leaf in leaf_accounts:
			if grp.lft <= leaf.lft and leaf.rgt <= grp.rgt:
				monthly += flt(budget_map.get(leaf.name))
				actual += flt(actual_map.get(leaf.name))
				last_actual += flt(last_actual_map.get(leaf.name))

		if (
			root_type == "Income"
			and grp.account_name == "Ancillary & Other Operating Income"
			and not monthly
		):
			monthly = ANCILLARY_MONTHLY_BUDGET

		is_revenue_discount = (
			root_type == "Income" and grp.account_name == "Patient Service Discounts"
		)
		if not (monthly or actual or last_actual or is_revenue_discount):
			continue

		daily = monthly / 30
		weekly = monthly / 4
		period_budget = daily * days
		row = {
			"account_group": grp.account_name,
			"monthly_budget": monthly,
			"daily_budget": daily,
			"weekly_budget": weekly,
			"period_budget": period_budget,
			"actual": actual,
			"budget_variance": actual - period_budget,
			"last_month_actual": last_actual,
			"last_month_variance": actual - last_actual,
			"currency": currency,
		}
		if is_revenue_discount:
			discount_row = row
			data.append(row)
			continue

		data.append(row)
		for key in total:
			if key not in ("account_group", "bold"):
				total[key] += flt(row.get(key))

	if discount_row:
		discount_row["monthly_budget"] = -(total.monthly_budget * REVENUE_DISCOUNT_RATE)
		discount_row["daily_budget"] = discount_row["monthly_budget"] / 30
		discount_row["weekly_budget"] = discount_row["monthly_budget"] / 4
		discount_row["period_budget"] = discount_row["daily_budget"] * days
		discount_row["budget_variance"] = (
			discount_row["actual"] - discount_row["period_budget"]
		)
		discount_row["last_month_variance"] = (
			discount_row["actual"] - discount_row["last_month_actual"]
		)

	total["currency"] = currency
	data.append(total)
	return total, discount_row or frappe._dict()


def add_revenue_discount_rows(data, revenue_total, discount_source):
	"""Add the positive discount deduction and net revenue rows."""
	currency = revenue_total.get("currency")
	discount = frappe._dict(account_group=_("Discount"), bold=1, currency=currency)

	for key in ("monthly_budget", "daily_budget", "weekly_budget", "period_budget"):
		discount[key] = -flt(discount_source.get(key))

	discount.actual = -flt(discount_source.get("actual"))
	discount.last_month_actual = -flt(discount_source.get("last_month_actual"))
	discount.budget_variance = discount.actual - discount.period_budget
	discount.last_month_variance = discount.actual - discount.last_month_actual
	data.append(discount)

	income_after_discount = frappe._dict(
		account_group=_("Income After Discount"), bold=1, currency=currency
	)
	for key in AMOUNT_FIELDS:
		income_after_discount[key] = flt(revenue_total.get(key)) - flt(discount.get(key))
	data.append(income_after_discount)
	return income_after_discount


def get_budget_plan_map(root_type, from_date):
	"""Leaf account -> monthly budget from the Budget Plan doctype.

	Uses the latest Budget Plan (of the matching type) starting on or before the
	selected month, so the budget carries forward unchanged until a new plan is made.
	"""
	budget_type = "Income" if root_type == "Income" else "Expense"

	plan = frappe.db.get_value(
		"Budget Plan",
		{"budget_type": budget_type, "from_date": ("<=", from_date), "docstatus": ("<", 2)},
		"name",
		order_by="from_date desc",
	)
	if not plan:
		# fall back to the earliest plan of this type, if any
		plan = frappe.db.get_value(
			"Budget Plan",
			{"budget_type": budget_type, "docstatus": ("<", 2)},
			"name",
			order_by="from_date asc",
		)
	if not plan:
		return {}

	budget_map = {}
	for d in frappe.get_all(
		"Budget Account",
		filters={"parent": plan, "parenttype": "Budget Plan"},
		fields=["account", "budget_amount"],
	):
		budget_map[d.account] = budget_map.get(d.account, 0) + flt(d.budget_amount)
	return budget_map


def get_gl_sums(filters, root_type, from_date, to_date):
	"""Leaf account -> signed actual (Income: credit-debit, Expense: debit-credit)."""
	sign = "credit - debit" if root_type == "Income" else "debit - credit"
	conditions = ""
	values = {
		"company": filters.company,
		"root_type": root_type,
		"from_date": from_date,
		"to_date": to_date,
	}
	if filters.get("cost_center"):
		lft, rgt = frappe.db.get_value("Cost Center", filters.cost_center, ["lft", "rgt"])
		conditions += """ and gle.cost_center in (
			select name from `tabCost Center` where lft >= %(cc_lft)s and rgt <= %(cc_rgt)s)"""
		values.update({"cc_lft": lft, "cc_rgt": rgt})

	rows = frappe.db.sql(
		f"""
		select gle.account, sum({sign}) as amount
		from `tabGL Entry` gle
		inner join `tabAccount` acc on acc.name = gle.account
		where gle.company = %(company)s
			and gle.is_cancelled = 0
			and acc.root_type = %(root_type)s
			and gle.posting_date between %(from_date)s and %(to_date)s
			{conditions}
		group by gle.account
		""",
		values,
		as_dict=True,
	)
	return {d.account: flt(d.amount) for d in rows}

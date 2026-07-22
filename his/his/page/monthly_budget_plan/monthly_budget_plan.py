import frappe
from frappe import _
from frappe.desk.query_report import run
from frappe.utils import cint, flt, formatdate, get_first_day, get_last_day, getdate, nowdate


NET_PROFIT_BUDGET = 200000.0


@frappe.whitelist()
def get_budget_plan_data(report_month=None):
	month_date = getdate(report_month) if report_month else getdate(nowdate())
	from_date = get_first_day(month_date)
	to_date = get_last_day(month_date)
	company = get_default_company()
	currency = frappe.get_cached_value("Company", company, "default_currency") if company else None
	currency_symbol = frappe.db.get_value("Currency", currency, "symbol") if currency else "$"

	budget_rows = get_budget_rows(from_date, to_date)
	actual_map = get_actual_amounts(company, from_date, to_date, budget_rows)
	sections = build_sections(budget_rows, actual_map, currency, currency_symbol)
	summary = build_summary(sections, currency, currency_symbol, from_date, to_date)

	return {
		"company": company or "Company Not Set",
		"currency": currency or "USD",
		"currency_symbol": currency_symbol or "$",
		"month_label": formatdate(from_date, "MMMM yyyy"),
		"month_input_value": from_date.strftime("%Y-%m"),
		"period_label": _("For the Month of {0}").format(formatdate(from_date, "MMMM yyyy")),
		"report_month": str(from_date),
		"sections": sections,
		"summary": summary,
		"prepared_by": frappe.session.user_fullname or frappe.session.user,
		"reviewed_by": "",
		"approved_by": "",
		"notes": [
			_("All amounts are in {0} unless otherwise stated.").format(currency or "the default currency"),
			_("Income variance is calculated as Actual minus Budget; expense variance is Budget minus Actual."),
		],
	}


def get_budget_rows(from_date, to_date):
	category_select = "COALESCE(ba.category, '') AS category" if frappe.db.has_column("Budget Account", "category") else "'' AS category"

	return frappe.db.sql(
		f"""
		SELECT
			bp.name AS budget_plan,
			bp.budget_type,
			ba.category,
			ba.account,
			ba.budget_amount,
			ba.remarks,
			acc.root_type,
			acc.parent_account,
			acc.account_name
		FROM `tabBudget Plan` bp
		INNER JOIN `tabBudget Account` ba ON ba.parent = bp.name
		LEFT JOIN `tabAccount` acc ON acc.name = ba.account
		WHERE
			bp.docstatus < 2
			AND bp.to_date >= %(from_date)s
			AND bp.from_date <= %(to_date)s
		""".replace("ba.category,", f"{category_select},"),
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)


def get_actual_amounts(company, from_date, to_date, budget_rows):
	accounts = sorted({row.account for row in budget_rows if row.get("account")})
	if not company or not accounts:
		return {}

	rows = frappe.db.sql(
		"""
		SELECT
			gle.account,
			SUM(IFNULL(gle.debit, 0)) AS debit,
			SUM(IFNULL(gle.credit, 0)) AS credit
		FROM `tabGL Entry` gle
		WHERE
			gle.company = %(company)s
			AND gle.is_cancelled = 0
			AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND gle.account IN %(accounts)s
		GROUP BY gle.account
		""",
		{
			"company": company,
			"from_date": from_date,
			"to_date": to_date,
			"accounts": tuple(accounts),
		},
		as_dict=True,
	)

	return {
		row.account: {
			"debit": flt(row.debit),
			"credit": flt(row.credit),
		}
		for row in rows
	}


def build_sections(budget_rows, actual_map, currency, currency_symbol):
	sections = []
	for budget_type in ("Income", "Expense"):
		type_rows = [row for row in budget_rows if (row.get("budget_type") or "") == budget_type]
		if not type_rows:
			continue

		categories = {}
		section_budget = 0.0
		section_actual = 0.0
		section_variance = 0.0

		for row in type_rows:
			account = row.get("account")
			budget_amount = flt(row.get("budget_amount"))
			actual_amount = get_actual_value(row, actual_map.get(account) or {})
			variance = get_variance(budget_type, budget_amount, actual_amount)
			variance_percent = (variance / budget_amount * 100) if budget_amount else 0
			category = (row.get("category") or "").strip() or strip_company_abbr(row.get("parent_account") or account) or _("Uncategorized")

			category_entry = categories.setdefault(
				category,
				{
					"label": category.upper(),
					"rows": [],
					"budget": 0.0,
					"actual": 0.0,
					"variance": 0.0,
				},
			)

			category_entry["rows"].append(
				{
					"account": strip_company_abbr(account),
					"budget_value": budget_amount,
					"actual_value": actual_amount,
					"variance_value": variance,
					"variance_percent_value": variance_percent,
					"budget": format_money(budget_amount, currency_symbol),
					"actual": format_money(actual_amount, currency_symbol),
					"variance": format_money(variance, currency_symbol, use_parentheses=True),
					"variance_percent": format_percent(variance_percent),
					"variance_class": get_variance_class(variance),
				}
			)
			category_entry["budget"] += budget_amount
			category_entry["actual"] += actual_amount
			category_entry["variance"] += variance
			section_budget += budget_amount
			section_actual += actual_amount
			section_variance += variance

		category_list = []
		for category_entry in categories.values():
			category_budget = flt(category_entry["budget"])
			category_variance = flt(category_entry["variance"])
			category_list.append(
				{
					"label": category_entry["label"],
					"rows": category_entry["rows"],
					"budget": format_money(category_budget, currency_symbol),
					"actual": format_money(category_entry["actual"], currency_symbol),
					"variance": format_money(category_variance, currency_symbol, use_parentheses=True),
					"variance_percent": format_percent((category_variance / category_budget * 100) if category_budget else 0),
					"variance_class": get_variance_class(category_variance),
				}
			)

		sections.append(
			{
				"key": budget_type.lower(),
				"label": _("Income") if budget_type == "Income" else _("Expenses"),
				"icon": "fa-line-chart" if budget_type == "Income" else "fa-briefcase",
				"categories": category_list,
				"budget_value": section_budget,
				"actual_value": section_actual,
				"variance_value": section_variance,
				"budget": format_money(section_budget, currency_symbol),
				"actual": format_money(section_actual, currency_symbol),
				"variance": format_money(section_variance, currency_symbol, use_parentheses=True),
				"variance_percent": format_percent((section_variance / section_budget * 100) if section_budget else 0),
				"variance_class": get_variance_class(section_variance),
			}
		)

	return sections


def build_summary(sections, currency, currency_symbol, from_date, to_date):
	income = next((section for section in sections if section["key"] == "income"), None)
	expense = next((section for section in sections if section["key"] == "expense"), None)

	income_budget = flt(income["budget_value"]) if income else 0
	income_actual = flt(income["actual_value"]) if income else 0
	income_variance = flt(income["variance_value"]) if income else 0

	expense_budget = flt(expense["budget_value"]) if expense else 0
	expense_actual = flt(expense["actual_value"]) if expense else 0
	expense_variance = flt(expense["variance_value"]) if expense else 0

	net_budget = NET_PROFIT_BUDGET
	net_actual = get_profit_and_loss_net_profit(from_date, to_date)
	net_variance = net_actual - net_budget
	net_variance_percent = (net_variance / abs(net_budget) * 100) if abs(net_budget) > 0.005 else 0

	actual_margin = (net_actual / income_actual * 100) if abs(income_actual) > 0.005 else 0
	budget_margin = (net_budget / income_budget * 100) if abs(income_budget) > 0.005 else 0

	return {
		"net": {
			"label": _("Net Profit / (Loss)"),
			"budget": format_money(net_budget, currency_symbol, use_parentheses=True),
			"actual": format_money(net_actual, currency_symbol, use_parentheses=True),
			"variance": format_money(net_variance, currency_symbol, use_parentheses=True),
			"variance_percent": format_percent(net_variance_percent),
			"variance_class": get_variance_class(net_variance),
		},
		"cards": [
			{
				"label": _("Total Income"),
				"icon": "fa-usd",
				"value": format_money(income_actual, currency_symbol),
				"delta": format_percent((income_variance / income_budget * 100) if income_budget else 0),
				"delta_class": get_variance_class(income_variance),
				"meta": _("vs Budget"),
			},
			{
				"label": _("Total Expenses"),
				"icon": "fa-briefcase",
				"value": format_money(expense_actual, currency_symbol),
				"delta": format_percent((expense_variance / expense_budget * 100) if expense_budget else 0),
				"delta_class": get_variance_class(expense_variance),
				"meta": _("vs Budget"),
			},
			{
				"label": _("Net Profit / (Loss)"),
				"icon": "fa-line-chart",
				"value": format_money(net_actual, currency_symbol, use_parentheses=True),
				"delta": format_percent(net_variance_percent),
				"delta_class": get_variance_class(net_variance),
				"meta": _("vs Budget"),
			},
			{
				"label": _("Net Profit Margin"),
				"icon": "fa-percent",
				"value": format_percent(actual_margin),
				"delta": _("vs Budget: {0}").format(format_percent(budget_margin)),
				"delta_class": get_variance_class(actual_margin - budget_margin),
				"meta": "",
			},
		],
		"currency": currency,
	}


def get_profit_and_loss_net_profit(from_date, to_date):
	company = get_default_company()
	if not company:
		return 0

	report = run(
		"Profit and Loss Statement",
		{
			"company": company,
			"filter_based_on": "Date Range",
			"period_start_date": from_date,
			"period_end_date": to_date,
			"periodicity": "Yearly",
			"accumulated_values": 0,
			"include_default_book_entries": 1,
			"ignore_prepared_report": True,
		},
	)

	for row in report.get("report_summary") or []:
		label = (row.get("label") or "").lower()
		if "profit" in label:
			return flt(row.get("value"))

	return 0


def get_actual_value(row, actual_row):
	root_type = (row.get("root_type") or row.get("budget_type") or "").strip()
	debit = flt(actual_row.get("debit"))
	credit = flt(actual_row.get("credit"))
	if root_type == "Income":
		return max(credit - debit, 0)
	return max(debit - credit, 0)


def get_variance(budget_type, budget, actual):
	if budget_type == "Expense":
		return budget - actual
	return actual - budget


def get_variance_class(value):
	value = flt(value)
	if value < -0.005:
		return "negative"
	if value > 0.005:
		return "positive"
	return "neutral"


def format_money(value, currency_symbol="$", use_parentheses=False):
	value = flt(value)
	formatted = f"{currency_symbol or '$'} {abs(value):,.2f}"
	if value < -0.005:
		return f"({formatted})" if use_parentheses else f"-{formatted}"
	if use_parentheses and value < 0:
		return f"({formatted})"
	return formatted


def format_percent(value):
	value = flt(value)
	formatted = f"{abs(value):.2f}%"
	if value < -0.005:
		return f"-{formatted}"
	return formatted


def strip_company_abbr(account):
	if not account:
		return ""
	return account.rsplit(" - ", 1)[0] if " - " in account else account


def get_default_company():
	return (
		frappe.defaults.get_user_default("Company")
		or frappe.defaults.get_global_default("company")
		or frappe.db.get_single_value("Global Defaults", "default_company")
	)

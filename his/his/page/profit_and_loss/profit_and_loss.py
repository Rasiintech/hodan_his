import frappe
from frappe.utils import add_days, cint, cstr, date_diff, flt, formatdate, get_first_day, get_last_day, getdate, nowdate
from erpnext.accounts.report.financial_statements import get_data, get_period_list
from erpnext.accounts.report.profit_and_loss_statement.profit_and_loss_statement import get_net_profit_loss

STATEMENT_GROUP_ACCOUNTS_TO_HIDE = {
	"4000 - income",
	"5000 - expenses",
}

STATEMENT_GROUP_ACCOUNTS_ALWAYS_EXPANDED = {
	"4100 - direct income",
	"4200 - indirect income",
	"5100 - direct expenses",
	"5200 - indirect expenses",
}


@frappe.whitelist()
def get_dashboard_data(from_date=None, to_date=None, previous_from_date=None, previous_to_date=None):
	from_date, to_date = get_date_range(from_date, to_date)
	previous_from_date, previous_to_date = get_comparison_period_dates(
		from_date, to_date, previous_from_date, previous_to_date
	)
	company = get_default_company()
	currency = frappe.get_cached_value("Company", company, "default_currency") if company else None

	current_period_rows = get_period_rows(from_date, to_date, company)
	current_account_totals, current_daily_totals = build_period_summaries(current_period_rows)
	previous_account_totals = get_account_totals(previous_from_date, previous_to_date, company)

	expense_categories, expense_donut_style, expense_empty_message = get_expense_category_data(current_account_totals.get("Expense"), currency)
	income_sources, source_donut_style, income_empty_message = get_income_source_data(current_account_totals.get("Income"), currency)
	account_variance_rows, account_variance_total = get_account_variance_rows(current_account_totals, previous_account_totals, currency)
	statement_table = get_statement_table_data(
		from_date, to_date, previous_from_date, previous_to_date, company, currency
	)

	return {
		"from_date": str(from_date),
		"to_date": str(to_date),
		"previous_from_date": str(previous_from_date),
		"previous_to_date": str(previous_to_date),
		"date_range": get_display_date_range(from_date, to_date),
		"comparison_range": get_display_comparison_range(previous_from_date, previous_to_date),
		"metrics": get_metrics(currency, current_account_totals, previous_account_totals),
		"income_expenses": get_income_expense_chart_data(from_date, to_date, current_daily_totals),
		"expense_categories": expense_categories,
		"expense_donut_style": expense_donut_style,
		"expense_empty_message": expense_empty_message,
		"income_sources": income_sources,
		"source_donut_style": source_donut_style,
		"income_empty_message": income_empty_message,
		"account_balances": get_top_income_account_rows(current_account_totals.get("Income"), currency),
		"unpaid_invoices": get_top_expense_account_rows(current_account_totals.get("Expense"), currency),
		"top_supplier_balances": get_profit_period_rows(from_date, to_date, current_daily_totals, currency),
		"budget_variance": account_variance_rows,
		"budget_variance_total": account_variance_total,
		"budget_variance_message": "" if account_variance_rows else "No profit and loss activity overlaps the selected date range.",
		"statement_table": statement_table,
		"cash_flow": [],
		"insights": [],
	}


# @frappe.whitelist(methods=["POST"])
# def get_ai_insights(dashboard_context=None, from_date=None, to_date=None):
# 	try:
# 		context = frappe.parse_json(dashboard_context) if dashboard_context else {}
# 		if not isinstance(context, dict):
# 			context = {}

# 		from coreinsight_ai.api.chatbot import chat

# 		prompt = build_profit_and_loss_ai_prompt(context, from_date=from_date, to_date=to_date)
# 		result = chat(
# 			messages=[{"role": "user", "content": prompt}],
# 			options={"answer_style": "analysis", "temperature": 0.2},
# 		)
# 		content = (result or {}).get("content") or ""
# 		return {"insights": parse_ai_insight_response(content), "raw_content": content}
# 	except Exception:
# 		frappe.log_error(frappe.get_traceback(), "Profit and Loss Dashboard AI Insight")
# 		return {
# 			"insights": [
# 				{
# 					"icon_class": "fa-info-circle",
# 					"text_class": "slate-text",
# 					"text": "Insights are not available right now. Please review the dashboard figures below.",
# 				}
# 			]
# 		}


def get_metrics(currency, current_account_totals, previous_account_totals):
	total_income, total_expenses, net_profit = get_profit_and_loss_metrics(current_account_totals)
	previous_income, previous_expenses, previous_net_profit = get_profit_and_loss_metrics(previous_account_totals)

	profit_margin = (net_profit / total_income * 100) if abs(total_income) > 0.005 else 0
	previous_profit_margin = (previous_net_profit / previous_income * 100) if abs(previous_income) > 0.005 else 0
	income_expense_ratio = (total_income / total_expenses) if abs(total_expenses) > 0.005 else 0
	previous_income_expense_ratio = (previous_income / previous_expenses) if abs(previous_expenses) > 0.005 else 0

	return [
		{
			"class": "income",
			"icon": '<i class="fa fa-line-chart"></i>',
			"label": "Total Income",
			"value": format_metric_currency(total_income, currency),
			**build_metric_trend(total_income, previous_income),
		},
		{
			"class": "expense",
			"icon": '<i class="fa fa-briefcase"></i>',
			"label": "Total Expenses",
			"value": format_metric_currency(total_expenses, currency),
			**build_metric_trend(total_expenses, previous_expenses),
		},
		{
			"class": "profit",
			"icon": '<i class="fa fa-balance-scale"></i>',
			"label": "Net Profit",
			"value": format_metric_currency(net_profit, currency),
			**build_metric_trend(net_profit, previous_net_profit),
		},
		{
			"class": "cash",
			"icon": '<i class="fa fa-percent"></i>',
			"label": "Profit Margin",
			"value": format_percent_value(profit_margin),
			**build_metric_trend(profit_margin, previous_profit_margin, suffix="margin"),
		},
		{
			"class": "bank",
			"icon": '<i class="fa fa-list-alt"></i>',
			"label": "Income to Expense Ratio",
			"value": format_ratio_value(income_expense_ratio),
			**build_metric_trend(income_expense_ratio, previous_income_expense_ratio, suffix="ratio"),
		},
	]


def get_account_totals(from_date, to_date, company):
	rows = get_period_rows(from_date, to_date, company)
	grouped, _daily_rows = build_period_summaries(rows)
	return grouped


def get_period_rows(from_date, to_date, company):
	if not company:
		return []

	return frappe.db.sql(
		"""
		SELECT
			gle.posting_date,
			gle.account,
			acc.root_type,
			SUM(IFNULL(gle.debit, 0)) AS debit,
			SUM(IFNULL(gle.credit, 0)) AS credit,
			COUNT(*) AS entries
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE
			gle.company = %(company)s
			AND gle.is_cancelled = 0
			AND (gle.voucher_type IS NULL OR gle.voucher_type != 'Period Closing Voucher')
			AND acc.root_type IN ('Income', 'Expense')
			AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY gle.posting_date, gle.account, acc.root_type
		ORDER BY gle.posting_date ASC, gle.account ASC
		""",
		{
			"company": company,
			"from_date": from_date,
			"to_date": to_date,
		},
		as_dict=True,
	)


def get_statement_table_data(from_date, to_date, previous_from_date, previous_to_date, company, currency=None):
	if not company:
		return {
			"title": "PROFIT AND LOSS STATEMENT",
			"subtitle": "",
			"currency": currency or "",
			"company": "",
			"actual_period_label": "",
			"previous_period_label": "",
			"rows": [],
		}

	current_payload = get_statement_period_payload(from_date, to_date, company, currency)
	previous_payload = get_statement_period_payload(previous_from_date, previous_to_date, company, currency)

	current_income_total = flt(current_payload.get("income_total"))
	previous_income_total = flt(previous_payload.get("income_total"))

	rows = []
	rows.extend(
		build_statement_section_rows(
			"Income",
			current_payload.get("income_rows") or [],
			previous_payload.get("income_rows") or [],
			current_payload.get("period_key"),
			previous_payload.get("period_key"),
			current_income_total,
			previous_income_total,
		)
	)
	rows.extend(
		build_statement_section_rows(
			"Expenses",
			current_payload.get("expense_rows") or [],
			previous_payload.get("expense_rows") or [],
			current_payload.get("period_key"),
			previous_payload.get("period_key"),
			current_income_total,
			previous_income_total,
		)
	)
	rows.append(
		build_statement_net_row(
			current_payload.get("net_profit_row") or {},
			previous_payload.get("net_profit_row") or {},
			current_payload.get("period_key"),
			previous_payload.get("period_key"),
			current_income_total,
			previous_income_total,
		)
	)

	return {
		"title": "PROFIT AND LOSS STATEMENT",
		"subtitle": f"For the period {formatdate(from_date, 'dd MMM YYYY')} to {formatdate(to_date, 'dd MMM YYYY')}",
		"currency": currency or frappe.get_cached_value("Company", company, "default_currency"),
		"company": company,
		"actual_period_label": f"{formatdate(from_date, 'dd MMM YYYY')} - {formatdate(to_date, 'dd MMM YYYY')}",
		"previous_period_label": f"{formatdate(previous_from_date, 'dd MMM YYYY')} - {formatdate(previous_to_date, 'dd MMM YYYY')}",
		"rows": rows,
	}


def get_statement_period_payload(from_date, to_date, company, currency=None):
	filters = frappe._dict(
		{
			"company": company,
			"filter_based_on": "Date Range",
			"period_start_date": from_date,
			"period_end_date": to_date,
			"periodicity": "Yearly",
			"accumulated_values": 0,
			"presentation_currency": currency,
		}
	)
	period_list = get_period_list(
		None,
		None,
		filters.period_start_date,
		filters.period_end_date,
		filters.filter_based_on,
		filters.periodicity,
		company=filters.company,
	)
	period_key = period_list[0].key if period_list else None

	income_rows = get_data(
		company,
		"Income",
		"Credit",
		period_list,
		filters=filters,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True,
		ignore_accumulated_values_for_fy=True,
	)
	expense_rows = get_data(
		company,
		"Expense",
		"Debit",
		period_list,
		filters=filters,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True,
		ignore_accumulated_values_for_fy=True,
	)
	net_profit_row = get_net_profit_loss(income_rows, expense_rows, period_list, company, currency)

	return {
		"period_key": period_key,
		"income_rows": compact_statement_rows(income_rows),
		"expense_rows": compact_statement_rows(expense_rows),
		"income_total": get_statement_total(income_rows, period_key),
		"net_profit_row": net_profit_row or {},
	}


def compact_statement_rows(rows):
	return [row for row in (rows or []) if row and row.get("account_name")]


def get_statement_total(rows, period_key):
	if not rows or not period_key:
		return 0.0
	for row in rows:
		account_name = cstr(row.get("account_name") or "")
		if account_name.lower().startswith("total "):
			return flt(row.get(period_key))
	return 0.0


def build_statement_section_rows(section_label, current_rows, previous_rows, current_key, previous_key, current_income_total, previous_income_total):
	rows = [
		{
			"row_type": "section",
			"label": section_label.upper(),
		}
	]
	previous_map = {cstr(row.get("account_name")): row for row in previous_rows}
	for row in current_rows:
		account_name = cstr(row.get("account_name") or "")
		if should_skip_statement_account(account_name):
			continue
		previous_row = previous_map.get(account_name) or {}
		is_total = account_name.lower().startswith("total ")
		trend = build_metric_trend(flt(row.get(current_key)), flt(previous_row.get(previous_key)))
		rows.append(
			{
				"row_type": "total" if is_total else "account",
				"label": account_name.replace("'", ""),
				"indent": cint(row.get("indent")),
				"is_group": cint(row.get("is_group")),
				"is_collapsible_group": is_statement_collapsible_group(account_name, row),
				"current_amount": format_metric_currency(row.get(current_key), row.get("currency")),
				"current_trend": trend.get("trend"),
				"current_trend_class": trend.get("trend_class"),
				"current_percent": format_statement_percent(row.get(current_key), current_income_total),
				"previous_amount": format_metric_currency(previous_row.get(previous_key), previous_row.get("currency") or row.get("currency")),
				"previous_percent": format_statement_percent(previous_row.get(previous_key), previous_income_total),
			}
		)
	return rows


def build_statement_net_row(current_row, previous_row, current_key, previous_key, current_income_total, previous_income_total):
	label = cstr(current_row.get("account_name") or "Net Profit for the Period").replace("'", "")
	trend = build_metric_trend(flt(current_row.get(current_key)), flt(previous_row.get(previous_key)))
	return {
		"row_type": "net",
		"label": label.upper(),
		"current_amount": format_metric_currency(current_row.get(current_key), current_row.get("currency")),
		"current_trend": trend.get("trend"),
		"current_trend_class": trend.get("trend_class"),
		"current_percent": format_statement_percent(current_row.get(current_key), current_income_total),
		"previous_amount": format_metric_currency(previous_row.get(previous_key), previous_row.get("currency") or current_row.get("currency")),
		"previous_percent": format_statement_percent(previous_row.get(previous_key), previous_income_total),
	}


def should_skip_statement_account(account_name):
	normalized = cstr(account_name or "").strip().lower()
	return normalized in STATEMENT_GROUP_ACCOUNTS_TO_HIDE


def is_statement_collapsible_group(account_name, row):
	normalized = cstr(account_name or "").strip().lower()
	if not cint(row.get("is_group")):
		return 0
	if normalized in STATEMENT_GROUP_ACCOUNTS_ALWAYS_EXPANDED:
		return 0
	if normalized.startswith("total "):
		return 0
	return 1



def get_income_expense_mapped_totals(from_date, to_date, company):
	gl_rows = get_root_account_gl_totals(from_date, to_date, company)

	# Create fast lookup: account name -> balance
	# account_balance_map = {
	# 	row.account: float(row.balance or 0)
	# 	for row in gl_rows
	# }

	# income_expense_mapping = [
	# 	{
	# 		"income_account": "Campaigns - HH",
	# 		"expense_accounts": [
	# 			"Campaigns Expense - HH",
	# 			"Campain Expenses - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Catering - HH",
	# 		"expense_accounts": [
	# 			"Catering Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Consultation - HH",
	# 		"expense_accounts": [
	# 			"Consultation Expenses - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Delivery - HH",
	# 		"expense_accounts": [
	# 			"Maternity Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Dental Income - HH",
	# 		"expense_accounts": [
	# 			"Dental Supplies Expense - HH",
	# 			"Dental Lab Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Dressing - HH",
	# 		"expense_accounts": [
	# 			"Dressing Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Imaging - HH",
	# 		"expense_accounts": [
	# 			"Imaging Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Laboratory - HH",
	# 		"expense_accounts": [
	# 			"Lab Supplies Expense - HH",
	# 			"Outside Lab Commission - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "OPD Procedure - HH",
	# 		"expense_accounts": [
	# 			"Opd Supplies Expenses - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "OT Sales - HH",
	# 		"expense_accounts": [
	# 			"OT Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Instruments operation - HH",
	# 		"expense_accounts": [
	# 			"Orthopedic Cost of instruments - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "OT - HH",
	# 		"expense_accounts": [
	# 			"OT Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "OT Consumable Campaign - HH",
	# 		"expense_accounts": [
	# 			"OT Supplies Expense - HH",
	# 			"Campaigns Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Opd Procedures - HH",
	# 		"expense_accounts": [
	# 			"Opd Supplies Expenses - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Derma Opd Procedure - HH",
	# 		"expense_accounts": [
	# 			"Dermatology Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Obs&Gyna Opd Procedure - HH",
	# 		"expense_accounts": [
	# 			"Maternity Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Ophthalmology Opd Procedure - HH",
	# 		"expense_accounts": [
	# 			"Ophthalmology Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Orthopedic Opd Procedure - HH",
	# 		"expense_accounts": [
	# 			"Orthopedic Cost of instruments - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Neonate Consultant - HH",
	# 		"expense_accounts": [
	# 			"NICU Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Oxygen - HH",
	# 		"expense_accounts": [
	# 			"Oxygen supply Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Drug - HH",
	# 		"expense_accounts": [
	# 			"Pharmacy Supplies Expense - HH",
	# 			"Cost of Goods Sold - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Optical - HH",
	# 		"expense_accounts": [
	# 			"Pharmacy Supplies Expense - HH",
	# 			"Cost of Goods Sold - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Radiology - HH",
	# 		"expense_accounts": [
	# 			"CT & MRI Supplies Expense - HH",
	# 			"Imaging Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "CT Scan - HH",
	# 		"expense_accounts": [
	# 			"CT & MRI Supplies Expense - HH",
	# 			"CT & MRI Scans Commission - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "ECG-ECHO - HH",
	# 		"expense_accounts": [
	# 			"Imaging Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "EEG - MEG - HH",
	# 		"expense_accounts": [
	# 			"Imaging Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "MRI - HH",
	# 		"expense_accounts": [
	# 			"CT & MRI Supplies Expense - HH",
	# 			"CT & MRI Scans Commission - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Ultrasound - HH",
	# 		"expense_accounts": [
	# 			"Imaging Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "X-ray - HH",
	# 		"expense_accounts": [
	# 			"Imaging Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Rooms - HH",
	# 		"expense_accounts": [
	# 			"Ipd Supplies Expense - HH"
	# 		]
	# 	},
	# 	{
	# 		"income_account": "Ward Service - HH",
	# 		"expense_accounts": [
	# 			"Ipd Supplies Expense - HH"
	# 		]
	# 	}
	# ]

	result = gl_rows

	# for item in income_expense_mapping:
	# 	income_account = item["income_account"]

	# 	# Income normally comes as negative in GL because credit > debit.
	# 	# So we convert it to positive revenue amount.
	# 	income_amount = abs(account_balance_map.get(income_account, 0))

	# 	expense_accounts = []
	# 	total_expense = 0

	# 	for expense_account in item.get("expense_accounts", []):
	# 		expense_amount = account_balance_map.get(expense_account, 0)
	# 		total_expense += expense_amount

	# 		expense_accounts.append({
	# 			"expense_account": expense_account,
	# 			"amount": expense_amount
	# 		})

	# 	result.append({
	# 		"income_account": income_account,
	# 		"amount": income_amount,
	# 		"expense_accounts": expense_accounts,
	# 		"total_expense": total_expense,
	# 		"gross_profit": income_amount - total_expense,
	# 		"gross_profit_margin": (
	# 			((income_amount - total_expense) / income_amount) * 100
	# 			if income_amount else 0
	# 		)
	# 	})

	return result

def get_root_account_gl_totals(from_date, to_date, company):
	if not company:
		return []

	return frappe.db.sql(
		"""
		SELECT
			gle.account,
			acc.root_type,
			SUM(IFNULL(gle.debit, 0) - IFNULL(gle.credit, 0)) AS balance
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE
			gle.company = %(company)s
			AND gle.is_cancelled = 0
			AND (gle.voucher_type IS NULL OR gle.voucher_type != 'Period Closing Voucher')
			AND acc.root_type IN ('Income', 'Expense')
			AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY gle.account, acc.root_type
		ORDER BY acc.root_type ASC, gle.account ASC
		""",
		{
			"company": company,
			"from_date": from_date,
			"to_date": to_date,
		},
		as_dict=True,
	)


def build_period_summaries(rows):
	grouped = {"Income": {}, "Expense": {}}
	daily_map = {}

	for row in rows:
		root_type = row.get("root_type")
		if root_type not in grouped:
			continue

		account = row.get("account")
		amount = get_row_amount(row)
		entries = int(flt(row.get("entries")))
		account_row = grouped[root_type].setdefault(account, {"amount": 0.0, "entries": 0})
		account_row["amount"] += amount
		account_row["entries"] += entries

		daily_key = (str(row.get("posting_date")), root_type)
		daily_row = daily_map.setdefault(
			daily_key,
			{
				"posting_date": row.get("posting_date"),
				"root_type": root_type,
				"debit": 0.0,
				"credit": 0.0,
			},
		)
		daily_row["debit"] += flt(row.get("debit"))
		daily_row["credit"] += flt(row.get("credit"))

	daily_rows = sorted(daily_map.values(), key=lambda row: (str(row.get("posting_date")), row.get("root_type") or ""))
	return grouped, daily_rows


def get_income_expense_chart_data(from_date, to_date, rows):
	buckets = build_chart_buckets(from_date, to_date, 6)
	for row in rows:
		posting_date = getdate(row.get("posting_date"))
		bucket = get_bucket_for_date(buckets, posting_date)
		if not bucket:
			continue

		debit = flt(row.get("debit"))
		credit = flt(row.get("credit"))
		if row.get("root_type") == "Income":
			bucket["income"] += max(credit - debit, 0)
		else:
			bucket["expense"] += max(debit - credit, 0)

	max_value = max([max(bucket["income"], bucket["expense"]) for bucket in buckets] or [0])
	max_bar_height = 154
	min_bar_height = 20

	return [
		{
			"label": formatdate(bucket["label_date"], "MMM d"),
			"income_value": format_compact_amount(bucket["income"]),
			"expense_value": format_compact_amount(bucket["expense"]),
			"income_height": get_scaled_bar_height(bucket["income"], max_value, min_bar_height, max_bar_height),
			"expense_height": get_scaled_bar_height(bucket["expense"], max_value, min_bar_height, max_bar_height),
		}
		for bucket in buckets
	]


def get_expense_category_data(expense_totals, currency):
	return build_donut_rows(expense_totals, currency, empty_message="No expense data for the selected date range.")


def get_income_source_data(income_totals, currency):
	return build_donut_rows(
		income_totals,
		currency,
		colors=("blue", "green", "orange", "purple", "indigo"),
		empty_message="No income data for the selected date range.",
	)


def build_donut_rows(totals, currency, colors=("blue", "green", "indigo", "orange", "slate"), empty_message="No data."):
	color_values = {
		"blue": "#3777f7",
		"green": "#48b892",
		"indigo": "#6d719f",
		"orange": "#ffaf1f",
		"slate": "#8ea0ba",
		"purple": "#825eea",
	}
	top_rows = sorted((totals or {}).items(), key=lambda item: item[1]["amount"], reverse=True)[:5]
	total_amount = sum(values["amount"] for _account, values in top_rows)
	if not top_rows:
		return [], "background: conic-gradient(#e5e7eb 0 100%);", empty_message

	segments = []
	list_rows = []
	current_percent = 0.0
	for index, (account, values) in enumerate(top_rows):
		amount = flt(values.get("amount"))
		color_class = colors[index % len(colors)]
		percent = (amount / total_amount * 100) if total_amount else 0
		next_percent = current_percent + percent
		segments.append(f"{color_values[color_class]} {current_percent:.2f}% {next_percent:.2f}%")
		list_rows.append(
			{
				"class": color_class,
				"label": strip_company_abbr(account),
				"value": f"{format_metric_currency(amount, currency)} ({percent:.1f}%)",
			}
		)
		current_percent = next_percent

	return list_rows, f"background: conic-gradient({', '.join(segments)});", ""


def get_top_income_account_rows(grouped, currency, limit=10):
	return build_account_total_rows(grouped, currency, limit, type_label="Income")


def get_top_expense_account_rows(grouped, currency, limit=10):
	output = []
	for account, values in sorted((grouped or {}).items(), key=lambda item: item[1]["amount"], reverse=True)[:limit]:
		output.append(
			{
				"customer_group": strip_company_abbr(account),
				"customer_count": format_metric_number(values["entries"]),
				"raw_customer_count": values["entries"],
				"outstanding": format_metric_currency(values["amount"], currency),
				"raw_outstanding": values["amount"],
			}
	)
	return output


def build_account_total_rows(grouped, currency, limit, type_label):
	output = []
	for account, values in sorted((grouped or {}).items(), key=lambda item: item[1]["amount"], reverse=True)[:limit]:
		output.append(
			{
				"account": strip_company_abbr(account),
				"type": f"{type_label} · {format_metric_number(values['entries'])} entries",
				"balance": format_metric_currency(values["amount"], currency),
				"raw_balance": values["amount"],
			}
		)
	return output


def get_profit_period_rows(from_date, to_date, rows, currency):
	buckets = build_chart_buckets(from_date, to_date, 6)
	for row in rows:
		posting_date = getdate(row.get("posting_date"))
		bucket = get_bucket_for_date(buckets, posting_date)
		if not bucket:
			continue
		if row.get("root_type") == "Income":
			bucket["income"] += get_row_amount(row)
		else:
			bucket["expense"] += get_row_amount(row)

	output = []
	for bucket in buckets:
		net = flt(bucket["income"]) - flt(bucket["expense"])
		output.append(
			{
				"supplier": formatdate(bucket["label_date"], "MMM d"),
				"supplier_group": "Profit" if net >= 0 else "Loss",
				"balance": format_metric_currency(net, currency),
				"raw_balance": net,
			}
		)
	return sorted(output, key=lambda row: abs(flt(row.get("raw_balance"))), reverse=True)


def get_account_variance_rows(current_account_totals, previous_account_totals, currency, limit=10):
	current_map = build_account_period_map(current_account_totals)
	previous_map = build_account_period_map(previous_account_totals)
	keys = sorted(set(current_map) | set(previous_map))
	output = []

	total_current = 0.0
	total_previous = 0.0
	total_variance = 0.0

	for key in keys:
		current_amount = flt(current_map.get(key, {}).get("amount"))
		previous_amount = flt(previous_map.get(key, {}).get("amount"))
		root_type = current_map.get(key, {}).get("root_type") or previous_map.get(key, {}).get("root_type") or "Expense"
		if root_type == "Income":
			variance = current_amount - previous_amount
		else:
			variance = previous_amount - current_amount

		total_current += current_amount
		total_previous += previous_amount
		total_variance += variance

		change_percent = (variance / previous_amount * 100) if abs(previous_amount) > 0.005 else (100.0 if abs(current_amount) > 0.005 else 0.0)
		indicator_label, indicator_class = get_account_indicator(root_type, variance)
		output.append(
			{
				"category": strip_company_abbr(key),
				"budget": format_metric_currency(current_amount, currency),
				"actual": format_metric_currency(previous_amount, currency),
				"variance": format_metric_currency(variance, currency),
				"variance_class": get_variance_class(variance),
				"indicator_label": indicator_label,
				"indicator_class": indicator_class,
				"utilization": format_percent_value(change_percent),
				"raw_abs_variance": abs(variance),
			}
		)

	output = sorted(output, key=lambda row: flt(row.get("raw_abs_variance")), reverse=True)[:limit]
	for row in output:
		row.pop("raw_abs_variance", None)

	total_indicator_label, total_indicator_class = get_account_indicator("Income", total_variance)
	total_row = {
		"budget": format_metric_currency(total_current, currency),
		"actual": format_metric_currency(total_previous, currency),
		"variance": format_metric_currency(total_variance, currency),
		"variance_class": get_variance_class(total_variance),
		"indicator_label": total_indicator_label,
		"indicator_class": total_indicator_class,
		"utilization": format_percent_value((total_current / total_previous * 100) if abs(total_previous) > 0.005 else 0),
	}
	return output, total_row


def build_account_period_map(account_totals):
	grouped = {}
	for root_type, accounts in (account_totals or {}).items():
		for account, values in (accounts or {}).items():
			grouped[account] = {"amount": flt(values.get("amount")), "root_type": root_type}
	return grouped


def get_account_indicator(root_type, variance):
	variance = flt(variance)
	if abs(variance) <= 0.005:
		return "Flat", "neutral"
	if root_type == "Income":
		return ("Up", "good") if variance > 0 else ("Down", "danger")
	return ("Lower", "good") if variance > 0 else ("Higher", "danger")


def get_row_amount(row):
	debit = flt(row.get("debit"))
	credit = flt(row.get("credit"))
	if row.get("root_type") == "Income":
		return max(credit - debit, 0)
	return max(debit - credit, 0)


def get_profit_and_loss_metrics(account_totals):
	total_income = sum(flt(values.get("amount")) for values in ((account_totals or {}).get("Income") or {}).values())
	total_expenses = sum(flt(values.get("amount")) for values in ((account_totals or {}).get("Expense") or {}).values())
	return total_income, total_expenses, total_income - total_expenses


def build_profit_and_loss_ai_prompt(context, from_date=None, to_date=None):
	date_range = f"From {from_date} to {to_date}" if from_date or to_date else "Current dashboard range"
	comparison_range = context.get("comparison_range") or "the previous comparison period"
	lines = [
		"You are analyzing a hospital profit and loss dashboard.",
		"Each insight must be on its own line.",
		"Prefix each line with one of these labels only: positive:, warning:, opportunity:",
		"Do not use markdown, bullets, headings, or extra intro text.",
		"Use only the figures provided below. Do not invent targets, ratios, percentages, or benchmarks that are not explicitly provided.",
		"If Net Profit is negative, describe it as a loss, not strong performance.",
		"",
		f"Date range: {date_range}",
		f"Metric comparison period: {comparison_range}",
		"",
		"Metrics:",
	]

	for metric in context.get("metrics") or []:
		lines.append(f"- {format_metric_for_ai(metric)}")

	lines.append("")
	lines.append("Top expense accounts:")
	for item in (context.get("expense_categories") or [])[:5]:
		lines.append(f"- {item.get('label')}: {item.get('value')}")

	lines.append("")
	lines.append("Top income accounts:")
	for item in (context.get("income_sources") or [])[:5]:
		lines.append(f"- {item.get('label')}: {item.get('value')}")

	lines.append("")
	lines.append(f"Income account total: {context.get('account_balances_total') or '$ 0'}")
	lines.append(f"Expense account total: {(context.get('unpaid_invoices_total') or {}).get('outstanding') or '$ 0'}")
	lines.append(f"Net by period total: {context.get('top_supplier_balances_total') or '$ 0'}")

	lines.append("")
	lines.append("Top income accounts table:")
	for item in (context.get("account_balances") or [])[:5]:
		lines.append(f"- {item.get('account')}: {item.get('balance')}")

	lines.append("")
	lines.append("Top expense accounts table:")
	for item in (context.get("unpaid_invoices") or [])[:5]:
		lines.append(f"- {item.get('customer_group')}: {item.get('outstanding')}")

	lines.append("")
	lines.append("Period net results:")
	for item in (context.get("top_supplier_balances") or [])[:5]:
		lines.append(f"- {item.get('supplier')}: {item.get('balance')}")

	variance_total = context.get("budget_variance_total") or {}
	lines.append("")
	lines.append("Account variance summary:")
	lines.append(
		f"- Current {variance_total.get('budget')}, Previous {variance_total.get('actual')}, Variance {variance_total.get('variance')}, Indicator {variance_total.get('indicator_label')}"
	)

	return "\n".join(lines)


def parse_ai_insight_response(content):
	insights = []
	icon_map = {
		"positive": ("fa-chart-line", "green-text"),
		"warning": ("fa-exclamation-triangle", "amber-text"),
		"opportunity": ("fa-lightbulb", "gold-text"),
	}

	for raw_line in (content or "").splitlines():
		line = (raw_line or "").strip().lstrip("-").strip()
		if not line:
			continue
		lower_line = line.lower()
		matched = None
		for prefix in icon_map:
			tag = f"{prefix}:"
			if lower_line.startswith(tag):
				matched = prefix
				line = line[len(tag):].strip()
				break
		if not line:
			continue
		icon_class, text_class = icon_map.get(matched or "opportunity", ("fa-info-circle", "slate-text"))
		insights.append({"icon_class": icon_class, "text_class": text_class, "text": line})

	if insights:
		return insights[:5]

	return [
		{
			"icon_class": "fa-info-circle",
			"text_class": "slate-text",
			"text": "Insights are not available right now. Please review the dashboard figures below.",
		}
	]


def strip_html(value):
	text = frappe.safe_decode(value or "")
	for token in ("&uarr;", "&darr;", "&rarr;"):
		text = text.replace(token, "")
	return frappe.utils.strip_html(text).strip()


def format_metric_for_ai(metric):
	metric = metric or {}
	label = metric.get("label") or "Metric"
	value = metric.get("value") or ""
	trend = strip_html(metric.get("trend") or "")
	trend_class = (metric.get("trend_class") or "").strip().lower()

	direction_map = {"up": "up", "down": "down", "flat": "flat"}
	direction = direction_map.get(trend_class)

	if direction and trend:
		return f"{label}: {value} (direction: {direction}; trend: {trend})"
	if direction:
		return f"{label}: {value} (direction: {direction})"
	if trend:
		return f"{label}: {value} ({trend})"
	return f"{label}: {value}"


def build_metric_trend(current_value, previous_value, suffix=""):
	current_value = flt(current_value)
	previous_value = flt(previous_value)
	diff = current_value - previous_value
	if abs(diff) < 0.005:
		return {"trend": "Flat", "trend_class": "flat"}
	if previous_value:
		percent_change = abs(diff) / abs(previous_value) * 100
	else:
		percent_change = 100 if current_value else 0
	direction = "up" if diff > 0 else "down"
	arrow = "&uarr;" if diff > 0 else "&darr;"
	return {"trend": f"{arrow} {percent_change:.1f}%", "trend_class": direction}


def get_variance_class(value):
	value = flt(value)
	if value > 0.005:
		return "positive"
	if value < -0.005:
		return "negative"
	return "neutral"


def build_chart_buckets(from_date, to_date, bucket_count):
	total_days = max(date_diff(to_date, from_date) + 1, 1)
	bucket_count = min(bucket_count, total_days)
	base_size = total_days // bucket_count
	remainder = total_days % bucket_count
	current_start = from_date
	buckets = []
	for index in range(bucket_count):
		size = base_size + (1 if index < remainder else 0)
		if size <= 0:
			size = 1
		current_end = add_days(current_start, size - 1)
		if current_end > to_date:
			current_end = to_date
		buckets.append({"start": current_start, "end": current_end, "label_date": current_start, "income": 0.0, "expense": 0.0})
		next_start = add_days(current_end, 1)
		if next_start > to_date:
			next_start = to_date
		current_start = next_start
	return buckets


def get_bucket_for_date(buckets, posting_date):
	for bucket in buckets:
		if bucket["start"] <= posting_date <= bucket["end"]:
			return bucket
	return None


def get_scaled_bar_height(value, max_value, min_height, max_height):
	if value <= 0 or max_value <= 0:
		return 0
	if value >= max_value:
		return max_height
	return int(min_height + ((value / max_value) * (max_height - min_height)))


def format_compact_amount(value):
	value = flt(value)
	abs_value = abs(value)
	if abs_value >= 1000000:
		return f"{value / 1000000:.1f}M"
	if abs_value >= 1000:
		return f"{value / 1000:.1f}K"
	return f"{value:,.0f}"


def format_metric_currency(value, currency=None):
	symbol = frappe.db.get_value("Currency", currency, "symbol") if currency else None
	return f"{symbol or '$'} {flt(value):,.0f}"


def format_metric_number(value):
	return frappe.format_value(int(flt(value)), {"fieldtype": "Int"})


def format_percent_value(value):
	return f"{flt(value):.1f}%"


def format_statement_percent(value, income_total):
	return format_percent_value((flt(value) / flt(income_total) * 100) if abs(flt(income_total)) > 0.005 else 0)


def format_ratio_value(value):
	return f"{flt(value):.2f}x"


def strip_company_abbr(account):
	return account.rsplit(" - ", 1)[0] if " - " in account else account


def get_date_range(from_date=None, to_date=None):
	if from_date and to_date:
		return getdate(from_date), getdate(to_date)
	if to_date and not from_date:
		to_date = getdate(to_date)
		return get_first_day(to_date), to_date
	if from_date and not to_date:
		from_date = getdate(from_date)
		return from_date, get_last_day(from_date)
	to_date = getdate(nowdate())
	return get_first_day(to_date), to_date


def get_previous_period_dates(from_date, to_date):
	if is_full_month_range(from_date, to_date):
		previous_month_date = add_days(from_date, -1)
		return get_first_day(previous_month_date), get_last_day(previous_month_date)
	period_days = max(date_diff(to_date, from_date) + 1, 1)
	previous_to_date = add_days(from_date, -1)
	previous_from_date = add_days(previous_to_date, -(period_days - 1))
	return previous_from_date, previous_to_date


def get_comparison_period_dates(from_date, to_date, previous_from_date=None, previous_to_date=None):
	if previous_from_date or previous_to_date:
		return get_date_range(previous_from_date, previous_to_date)
	return get_previous_period_dates(from_date, to_date)


def is_full_month_range(from_date, to_date):
	from_date = getdate(from_date)
	to_date = getdate(to_date)
	return from_date == get_first_day(from_date) and to_date == get_last_day(from_date)


def get_display_date_range(from_date, to_date):
	return f"{formatdate(from_date, 'MMM d')} - {formatdate(to_date, 'MMM d, YYYY')}"


def get_display_comparison_range(previous_from_date, previous_to_date):
	return f"{formatdate(previous_from_date, 'MMM d')} - {formatdate(previous_to_date, 'MMM d')}"


def get_default_company():
	return (
		frappe.defaults.get_user_default("Company")
		or frappe.defaults.get_global_default("company")
		or frappe.db.get_single_value("Global Defaults", "default_company")
	)

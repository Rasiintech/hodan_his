import frappe
from frappe.utils import add_days, date_diff, flt, formatdate, get_first_day, get_last_day, getdate, nowdate
import requests
from coreinsight_ai.api.remote_db import remote_db
DEFAULT_VISIBLE_LIMIT = 10
MINIMUM_AMOUNT = 0.005
remote_sql = remote_db.sql
COLOR_VALUES = {
	"blue": "#3777f7",
	"green": "#48b892",
	"indigo": "#6d719f",
	"orange": "#ffaf1f",
	"slate": "#8ea0ba",
	"purple": "#825eea",
}


@frappe.whitelist()
def get_dashboard_data(from_date=None, to_date=None):
	from_date, to_date = get_date_range(from_date, to_date)
	previous_from_date, previous_to_date = get_previous_period_dates(from_date, to_date)

	company = get_default_company()
	currency = get_company_currency(company)
	currency_symbol = get_currency_symbol(currency)


	current_gl_rows = get_finance_gl_rows(
	from_date=from_date,
	to_date=to_date,
		)
	previous_gl_rows = get_finance_gl_rows(
		from_date=previous_from_date,
		to_date=previous_to_date,
	)
	income_expense_chart_rows = get_income_expense_chart_rows(from_date, to_date, bucket_count=6)

	current_pl = calculate_profit_and_loss_from_rows(current_gl_rows)
	previous_pl = calculate_profit_and_loss_from_rows(previous_gl_rows)
	receivable_rows , receivables  = get_party_balances(to_date, "Customer")
	previous_receivables_rows , previous_receivables  = get_party_balances(previous_to_date, "Customer")

	payable_rows , payables  = get_party_balances(to_date, "Supplier")
	previous_payables_rows , previous_payables  = get_party_balances(previous_to_date, "Supplier")
	account_balances_rows = get_finance_gl_rows(from_date=from_date, to_date=to_date, account_type="Bank")



	expense_categories, expense_donut_style, expense_empty_message = get_expense_category_data(
	    from_date, to_date, current_gl_rows, currency_symbol
	)
	income_sources, source_donut_style, income_empty_message = get_income_source_data(
	    from_date, to_date, current_gl_rows, currency_symbol
	)



	account_balances = get_bank_account_balances_from_rows(account_balances_rows, to_date, currency_symbol)


	receivables_by_group = {}
	for row in receivable_rows:
		customer_group = row.get("customer_group") or "Unassigned"
		group_entry = receivables_by_group.setdefault(
			customer_group,
			{
				"customer_group": customer_group,
				"raw_customer_count": 0,
				"customer_count": 0,
				"raw_outstanding": 0.0,
			},
		)
		group_entry["raw_customer_count"] += 1
		group_entry["customer_count"] += 1
		group_entry["raw_outstanding"] += flt(row.get("net_balance"))

	unpaid_invoices = [
		{
			**group_row,
			"outstanding": format_metric_currency(group_row.get("raw_outstanding"), currency_symbol),
		}
		for group_row in sorted(
			receivables_by_group.values(),
			key=lambda item: item.get("raw_outstanding", 0),
			reverse=True,
		)
	]

	top_supplier_balances = [
		{
			"supplier": row.get("party") or "Unknown Supplier",
			"supplier_group": row.get("supplier_group") or "Unassigned",
			"raw_balance": abs(flt(row.get("net_balance"))),
			"balance": format_metric_currency(abs(flt(row.get("net_balance"))), currency_symbol),
		}
		for row in sorted(
			[row for row in payable_rows if abs(flt(row.get("net_balance"))) >= 1],
			key=lambda item: abs(flt(item.get("net_balance"))),
			reverse=True,
		)
	]

	return {
		"from_date": str(from_date),
		"to_date": str(to_date),
		"date_range": get_display_date_range(from_date, to_date),
		"comparison_range": get_display_comparison_range(from_date, to_date),
		"metrics": get_metrics_from_values(
			current_pl,
			previous_pl,
			receivables['net_balance'],
			previous_receivables['net_balance'],
			payables['net_balance'],
			previous_payables['net_balance'],
			# currency_symbol,
		),
		"income_expenses": get_income_expense_chart_data(from_date, to_date, income_expense_chart_rows),
		"expense_categories": expense_categories,
		"expense_donut_style": expense_donut_style,
		"expense_empty_message": expense_empty_message,
		"income_sources": income_sources,
		"source_donut_style": source_donut_style,
		"income_empty_message": income_empty_message,
		"account_balances": account_balances,
		"account_balances_total": format_metric_currency(sum(flt(row.get("raw_balance")) for row in account_balances), currency_symbol),
		"unpaid_invoices": unpaid_invoices,
		"unpaid_invoices_total": {
			"customer_count": sum(int(row.get("raw_customer_count") or 0) for row in unpaid_invoices),
			"outstanding": format_metric_currency(sum(flt(row.get("raw_outstanding")) for row in unpaid_invoices), currency_symbol),
		},
		"top_supplier_balances": top_supplier_balances,
		"top_supplier_balances_total": format_metric_currency(
			sum(flt(row.get("raw_balance")) for row in top_supplier_balances), currency_symbol
		),
	
		"insights": [],
	}


@frappe.whitelist(methods=["POST"])
def get_ai_insights(dashboard_context=None, from_date=None, to_date=None):
	try:
		context = frappe.parse_json(dashboard_context) if dashboard_context else {}
		if not isinstance(context, dict):
			context = {}

		prompt = build_finance_ai_prompt(context, from_date=from_date, to_date=to_date)
		content = call_coreinsight_chat_api(prompt)

		if not content or not content.strip():
			raise ValueError("CoreInsight returned empty content")

		return {"insights": parse_ai_insight_response(content), "raw_content": content}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Finance Dashboard AI Insight")
		return {
			"insights": [
				{
					"icon_class": "fa-info-circle",
					"text_class": "slate-text",
					"text": "Insights are not available right now. Please review the dashboard figures below.",
				}
			]
		}


def call_coreinsight_chat_api(prompt):
	# Recommended: move these values to a Single DocType or site_config.json.
	base_url = "http://192.168.1.112"
	api_key = "f45f9e8743e2728"
	api_secret = "cd3bf5a1fdd1714"

	response = requests.post(
		f"{base_url.rstrip('/')}/api/method/coreinsight_ai.api.chatbot.chat",
		data={
			"messages": frappe.as_json([{"role": "user", "content": prompt}]),
			"options": frappe.as_json({"answer_style": "analysis", "temperature": 0.2}),
		},
		headers={"Authorization": f"token {api_key}:{api_secret}"},
		timeout=120,
	)
	response.raise_for_status()

	data = response.json() or {}
	if data.get("exc"):
		raise Exception(f"Remote frappe exception: {data.get('exc')}")

	message = data.get("message")
	if not isinstance(message, dict):
		raise ValueError(f"Unexpected response shape: {data}")

	content = message.get("content")
	if not content:
		raise ValueError(f"No content in remote response: {data}")
	return content


# -----------------------------------------------------------------------------
# Single-pass SQL loaders
# -----------------------------------------------------------------------------



def get_finance_gl_rows(
	from_date,
	to_date,
	company=None,
	account_type=None,
):
	if account_type:
		account_type_filter = "AND acc.account_type = %(account_type)s"
	else:
		account_type_filter = "AND acc.root_type IN ('Income', 'Expense')"

	return remote_sql(
		f"""
		SELECT
			gle.account,
			acc.root_type,
			acc.account_type,
			SUM(IFNULL(gle.debit, 0)) AS debit,
			SUM(IFNULL(gle.credit, 0)) AS credit,
			SUM(IFNULL(gle.debit, 0) - IFNULL(gle.credit, 0)) AS balance
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc
			ON acc.name = gle.account
		WHERE
			gle.is_cancelled = 0
			AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND (
				gle.voucher_type IS NULL
				OR gle.voucher_type != 'Period Closing Voucher'
			)
			{account_type_filter}
		GROUP BY
			gle.account,
			acc.root_type,
			acc.account_type
		""",
		{
			"from_date": from_date,
			"to_date": to_date,
			"account_type": account_type,
		},
		as_dict=True,
	)


def get_income_expense_chart_rows(from_date, to_date, bucket_count=6):
	buckets = build_chart_buckets(from_date, to_date, bucket_count)
	if not buckets:
		return []

	case_parts = []
	values = {
		"from_date": from_date,
		"to_date": to_date,
	}

	for index, bucket in enumerate(buckets):
		start_key = f"bucket_start_{index}"
		end_key = f"bucket_end_{index}"
		values[start_key] = bucket["start"]
		values[end_key] = bucket["end"]
		case_parts.append(
			f"WHEN gle.posting_date BETWEEN %({start_key})s AND %({end_key})s THEN {index}"
		)

	return remote_sql(
		f"""
		SELECT
			CASE
				{' '.join(case_parts)}
			END AS bucket_index,
			acc.root_type,
			SUM(IFNULL(gle.debit, 0)) AS debit,
			SUM(IFNULL(gle.credit, 0)) AS credit
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc
			ON acc.name = gle.account
		WHERE
			gle.is_cancelled = 0
			AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND (
				gle.voucher_type IS NULL
				OR gle.voucher_type != 'Period Closing Voucher'
			)
			AND acc.root_type IN ('Income', 'Expense')
		GROUP BY
			bucket_index,
			acc.root_type
		HAVING bucket_index IS NOT NULL
		ORDER BY
			bucket_index ASC,
			acc.root_type ASC
		""",
		values,
		as_dict=True,
	)

def get_payment_ledger_rows(company, to_date):
	# Touches Payment Ledger Entry, Customer, and Supplier one time.
	if not company:
		return []

	return frappe.db.sql(
		"""
		SELECT
			ple.posting_date,
			ple.party_type,
			ple.party,
			COALESCE(NULLIF(c.customer_group, ''), 'Unassigned') AS customer_group,
			COALESCE(NULLIF(s.supplier_group, ''), 'Unassigned') AS supplier_group,
			SUM(ple.amount) AS amount
		FROM `tabPayment Ledger Entry` ple
		LEFT JOIN `tabCustomer` c
			ON c.name = ple.party AND ple.party_type = 'Customer'
		LEFT JOIN `tabSupplier` s
			ON s.name = ple.party AND ple.party_type = 'Supplier'
		WHERE
			ple.company = %(company)s
			AND ple.party_type IN ('Customer', 'Supplier')
			AND ple.delinked = 0
			AND ple.posting_date <= %(to_date)s
		GROUP BY
			ple.posting_date,
			ple.party_type,
			ple.party,
			COALESCE(NULLIF(c.customer_group, ''), 'Unassigned'),
			COALESCE(NULLIF(s.supplier_group, ''), 'Unassigned')
		ORDER BY ple.posting_date ASC
		""",
		{"company": company, "to_date": to_date},
		as_dict=True,
	)


# -----------------------------------------------------------------------------
# In-memory calculations from loaded rows
# -----------------------------------------------------------------------------


def calculate_profit_and_loss_from_rows(rows):
    totals = {
        "income": 0.0,
        "expense": 0.0,
        "profit": 0.0,
    }

    for row in rows or []:
        root_type = row.get("root_type")
        debit = flt(row.get("debit"))
        credit = flt(row.get("credit"))

        if root_type == "Income":
            totals["income"] += credit - debit

        elif root_type == "Expense":
            totals["expense"] += debit - credit

    totals["profit"] = totals["income"] - totals["expense"]

    return totals


def get_metrics_from_values(current_pl, previous_pl, receivables , previous_receivables, payables, previous_payables, currency_symbol=None):
	return [
		{
			"class": "income",
			"icon": "$",
			"label": "Total Income",
			"value": format_metric_currency(current_pl.get("income"), currency_symbol),
			**build_metric_trend(current_pl.get("income"), previous_pl.get("income")),
		},
		{
			"class": "expense",
			"icon": '<i class="fa fa-briefcase"></i>',
			"label": "Total Expenses",
			"value": format_metric_currency(current_pl.get("expense"), currency_symbol),
			**build_metric_trend(current_pl.get("expense"), previous_pl.get("expense")),
		},
		{
			"class": "profit",
			"icon": '<i class="fa fa-chart-line"></i>',
			"label": "Net Profit",
			"value": format_metric_currency(current_pl.get("profit"), currency_symbol),
			**build_metric_trend(current_pl.get("profit"), previous_pl.get("profit")),
		},
		{
			"class": "cash",
			"icon": '<i class="fa fa-money-bill"></i>',
			"label": "Receivables",
			"value": format_metric_currency(receivables, currency_symbol),
			**build_metric_trend(receivables, previous_receivables),
		},
		{
			"class": "bank",
			"icon": '<i class="fa fa-university"></i>',
			"label": "Payables",
			"value": format_metric_currency(payables, currency_symbol),
			**build_metric_trend(payables, previous_payables),
		},
	]


def get_bank_account_balances_from_rows(
	gl_rows,
	report_date,
	currency_symbol=None,
	):
	grouped = {}

	for row in gl_rows or []:
		if row.get("account_type") != "Bank":
			continue

		account = row.get("account")
		if not account:
			continue

		grouped[account] = (
			grouped.get(account, 0.0)
			+ flt(row.get("balance"))
		)

	return [
		{
			"account": account,
			"type": "Bank",
			"raw_balance": balance,
			"balance": format_metric_currency(
				balance,
				currency_symbol,
			),
		}
		for account, balance in sorted(
			grouped.items(),
			key=lambda item: item[1],
			reverse=True,
		)
		if abs(balance) > MINIMUM_AMOUNT
	]

# def get_party_balances(to_date , party_type="Customer"):
#     rows = remote_sql(
#         """
#         SELECT
#             gle.party AS customer,
#             SUM(gle.debit) AS debit,
#             SUM(gle.credit) AS credit,
#             SUM(gle.debit - gle.credit) AS net_balance
#         FROM `tabGL Entry` gle
#         FORCE INDEX (idx_customer_balance_fast)
#         WHERE
#             gle.party_type = %(party_type)s
#             AND gle.is_cancelled = 0
#             AND gle.party IS NOT NULL
#             AND gle.posting_date <= %(to_date)s
#         GROUP BY
#             gle.party
#         """,
#         {"to_date": to_date, "party_type": party_type},
#         as_dict=True,
#     )

#     rows = [
#         row for row in rows
#         if abs(float(row.get("net_balance") or 0)) > 0.005
#     ]

#     rows.sort(
#         key=lambda row: float(row.get("net_balance") or 0),
#         reverse=True,
#     )

#     return rows
def get_party_balances(to_date, party_type="Customer"):
    if party_type == "Customer":
        query = """
            SELECT
                cb.party,
                c.customer_name,

                CASE
                    WHEN ip.status = 'Admitted' THEN 'Admitted'
                    ELSE c.customer_group
                END AS customer_group,

                p.name AS patient,
                ip.name AS inpatient_record,
                COALESCE(ip.status, 'Not Admitted') AS inpatient_status,

                cb.debit,
                cb.credit,
                cb.net_balance

            FROM (
                SELECT
                    gle.party,
                    SUM(gle.debit) AS debit,
                    SUM(gle.credit) AS credit,
                    SUM(gle.debit - gle.credit) AS net_balance
                FROM `tabGL Entry` gle
                FORCE INDEX (`idx_customer_balance_fast`)
                WHERE
                    gle.party_type = 'Customer'
                    AND gle.is_cancelled = 0
                    AND gle.party IS NOT NULL
                    AND gle.party != ''
                    AND gle.posting_date <= %(to_date)s
                GROUP BY gle.party
                HAVING ABS(SUM(gle.debit - gle.credit)) > 0.005
            ) cb

            LEFT JOIN `tabCustomer` c
                ON c.name = cb.party

            LEFT JOIN `tabPatient` p
                ON p.customer = cb.party

            LEFT JOIN `tabInpatient Record` ip
                ON ip.name = (
                    SELECT ip2.name
                    FROM `tabInpatient Record` ip2
                    WHERE
                        ip2.patient = p.name
                        AND ip2.docstatus < 2
                    ORDER BY
                        ip2.admitted_datetime DESC,
                        ip2.creation DESC
                    LIMIT 1
                )

            ORDER BY cb.net_balance DESC
        """

        values = {
            "to_date": to_date,
        }

    else:
        # Keep Supplier and other party types unchanged.
        query = """
            SELECT
                gle.party AS party,
                SUM(gle.debit) AS debit,
                SUM(gle.credit) AS credit,
                SUM(gle.debit - gle.credit) AS net_balance
            FROM `tabGL Entry` gle
            FORCE INDEX (`idx_customer_balance_fast`)
            WHERE
                gle.party_type = %(party_type)s
                AND gle.is_cancelled = 0
                AND gle.party IS NOT NULL
                AND gle.posting_date <= %(to_date)s
            GROUP BY gle.party
        """

        values = {
            "to_date": to_date,
            "party_type": party_type,
        }

    rows = remote_sql(
        query,
        values,
        as_dict=True,
    )

    filtered_rows = []

    totals = {
        "debit": 0.0,
        "credit": 0.0,
        "net_balance": 0.0,
        "count": 0,
    }

    for row in rows or []:
        debit = float(row.get("debit") or 0)
        credit = float(row.get("credit") or 0)
        net_balance = float(row.get("net_balance") or 0)

        # Customer rows are already filtered by SQL HAVING.
        # Keep this check for suppliers and numerical safety.
        if abs(net_balance) <= 0.005:
            continue

        row["debit"] = debit
        row["credit"] = credit
        row["net_balance"] = net_balance

        filtered_rows.append(row)

        totals["debit"] += debit
        totals["credit"] += credit
        totals["net_balance"] += net_balance
        totals["count"] += 1

    # Customer results are already sorted in SQL.
    # Suppliers retain the original Python sorting behavior.
    if party_type != "Customer":
        filtered_rows.sort(
            key=lambda row: row["net_balance"],
            reverse=True,
        )

    return filtered_rows, totals



def get_party_outstanding_total_from_rows(payment_rows, report_date, party_type):
	total = 0.0
	for row in payment_rows or []:
		if row.get("party_type") != party_type:
			continue
		posting_date = row.get("posting_date")
		if posting_date and getdate(posting_date) <= report_date:
			total += flt(row.get("amount"))
	return total


def get_receivables_by_customer_group_from_rows(payment_rows, report_date, currency_symbol=None):
	grouped = {}
	for row in payment_rows or []:
		if row.get("party_type") != "Customer":
			continue
		posting_date = row.get("posting_date")
		if not posting_date or getdate(posting_date) > report_date:
			continue

		customer_group = row.get("customer_group") or "Unassigned"
		entry = grouped.setdefault(
			customer_group,
			{"customer_group": customer_group, "customer_set": set(), "outstanding_amount": 0.0},
		)
		entry["customer_set"].add(row.get("party"))
		entry["outstanding_amount"] += flt(row.get("amount"))

	rows = sorted(
		[row for row in grouped.values() if abs(flt(row.get("outstanding_amount"))) > MINIMUM_AMOUNT],
		key=lambda item: item["outstanding_amount"],
		reverse=True,
	)

	formatted_rows = []
	for row in rows:
		customer_count = len(row["customer_set"])
		formatted_rows.append(
			{
				"customer_group": row["customer_group"],
				"raw_customer_count": customer_count,
				"customer_count": customer_count,
				"raw_outstanding": flt(row["outstanding_amount"]),
				"outstanding": format_metric_currency(row["outstanding_amount"], currency_symbol),
			}
		)
	return formatted_rows


def get_top_supplier_balances_from_rows(payment_rows, report_date, currency_symbol=None, limit=10):
	grouped = {}
	for row in payment_rows or []:
		if row.get("party_type") != "Supplier":
			continue
		posting_date = row.get("posting_date")
		if not posting_date or getdate(posting_date) > report_date:
			continue

		supplier = row.get("party") or "Unknown Supplier"
		supplier_group = row.get("supplier_group") or "Unassigned"
		key = (supplier, supplier_group)
		grouped[key] = grouped.get(key, 0.0) + flt(row.get("amount"))

	sorted_rows = sorted(grouped.items(), key=lambda item: item[1], reverse=True)
	return [
		{
			"supplier": supplier,
			"supplier_group": supplier_group,
			"raw_balance": balance,
			"balance": format_metric_currency(balance, currency_symbol),
		}
		for (supplier, supplier_group), balance in sorted_rows[: int(limit or 10)]
		if abs(balance) > MINIMUM_AMOUNT
	]




def get_income_expense_chart_data(from_date, to_date, rows=None):
	rows = rows or []
	buckets = build_chart_buckets(from_date, to_date, 6)
	bucket_map = {index: bucket for index, bucket in enumerate(buckets)}

	for row in rows:
		bucket_index = row.get("bucket_index")
		root_type = row.get("root_type")
		if bucket_index is None or root_type not in ("Income", "Expense"):
			continue

		try:
			bucket_index = int(bucket_index)
		except (TypeError, ValueError):
			continue

		bucket = bucket_map.get(bucket_index)
		if not bucket:
			continue

		debit = flt(row.get("debit"))
		credit = flt(row.get("credit"))
		if root_type == "Income":
			bucket["income"] += max(credit - debit, 0)
		else:
			bucket["expense"] += max(debit - credit, 0)

	max_value = max([max(bucket["income"], bucket["expense"]) for bucket in buckets] or [0])
	return [
		{
			"label": formatdate(bucket["label_date"], "MMM d"),
			"income_value": format_compact_amount(bucket["income"]),
			"expense_value": format_compact_amount(bucket["expense"]),
			"income_height": get_scaled_bar_height(bucket["income"], max_value, 20, 154),
			"expense_height": get_scaled_bar_height(bucket["expense"], max_value, 20, 154),
		}
		for bucket in buckets
	]


def get_expense_category_data(from_date, to_date, rows=None, currency_symbol=None):
	return build_donut_data(
		rows or [],
		from_date,
		to_date,
		root_type="Expense",
		colors=("blue", "green", "indigo", "orange", "slate"),
		currency_symbol=currency_symbol,
		empty_message="No expense data for the selected date range.",
	)


def get_income_source_data(from_date, to_date, rows=None, currency_symbol=None):
	return build_donut_data(
		rows or [],
		from_date,
		to_date,
		root_type="Income",
		colors=("blue", "green", "orange", "purple", "indigo"),
		currency_symbol=currency_symbol,
		empty_message="No income data for the selected date range.",
	)


# def build_donut_data(rows, from_date, to_date, root_type, colors, currency_symbol=None, empty_message="No data for the selected date range."):
# 	totals = {}

# 	for row in rows:
# 		if row.get("root_type") != root_type:
# 			continue

# 		posting_date = row.get("posting_date")
# 		account = row.get("account")
# 		if not posting_date or not account:
# 			continue

# 		posting_date = getdate(posting_date)
# 		if posting_date < from_date or posting_date > to_date:
# 			continue

# 		debit = flt(row.get("debit"))
# 		credit = flt(row.get("credit"))
# 		amount = max(credit - debit, 0) if root_type == "Income" else max(debit - credit, 0)
# 		if amount <= MINIMUM_AMOUNT:
# 			continue

# 		totals[account] = totals.get(account, 0.0) + amount

# 	top_accounts = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:5]
# 	total_amount = sum(amount for _account, amount in top_accounts)
# 	if not top_accounts:
# 		return [], "background: conic-gradient(#e5e7eb 0 100%);", empty_message

# 	list_rows = []
# 	segments = []
# 	current_percent = 0.0
# 	for index, (account, amount) in enumerate(top_accounts):
# 		color_class = colors[index % len(colors)]
# 		percent = (amount / total_amount * 100) if total_amount else 0
# 		next_percent = current_percent + percent
# 		segments.append(f"{COLOR_VALUES[color_class]} {current_percent:.2f}% {next_percent:.2f}%")
# 		list_rows.append(
# 			{
# 				"class": color_class,
# 				"label": strip_company_abbr(account),
# 				"value": f"{format_metric_currency(amount, currency_symbol)} ({percent:.1f}%)",
# 			}
# 		)
# 		current_percent = next_percent

# 	return list_rows, f"background: conic-gradient({', '.join(segments)});", ""
def build_donut_data(
    rows,
    from_date,
    to_date,
    root_type,
    colors,
    currency_symbol=None,
    empty_message="No data for the selected date range.",
):
    totals = {}

    for row in rows or []:
        if row.get("root_type") != root_type:
            continue

        account = row.get("account")
        if not account:
            continue

        debit = flt(row.get("debit"))
        credit = flt(row.get("credit"))

        if root_type == "Income":
            amount = credit - debit
        else:
            amount = debit - credit

        if amount <= MINIMUM_AMOUNT:
            continue

        totals[account] = totals.get(account, 0.0) + amount

    top_accounts = sorted(
        totals.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:5]

    total_amount = sum(amount for _account, amount in top_accounts)

    if not top_accounts:
        return (
            [],
            "background: conic-gradient(#e5e7eb 0 100%);",
            empty_message,
        )

    list_rows = []
    segments = []
    current_percent = 0.0

    for index, (account, amount) in enumerate(top_accounts):
        color_class = colors[index % len(colors)]

        percent = (
            amount / total_amount * 100
            if total_amount
            else 0
        )

        next_percent = current_percent + percent

        segments.append(
            f"{COLOR_VALUES[color_class]} "
            f"{current_percent:.2f}% "
            f"{next_percent:.2f}%"
        )

        list_rows.append(
            {
                "class": color_class,
                "label": strip_company_abbr(account),
                "value": (
                    f"{format_metric_currency(amount, currency_symbol)} "
                    f"({percent:.1f}%)"
                ),
            }
        )

        current_percent = next_percent

    return (
        list_rows,
        f"background: conic-gradient({', '.join(segments)});",
        "",
    )

# -----------------------------------------------------------------------------
# AI prompt and parsing
# -----------------------------------------------------------------------------


def build_finance_ai_prompt(context, from_date=None, to_date=None):
	date_range = f"From {from_date} to {to_date}" if from_date or to_date else "Current dashboard range"
	lines = [
		"You are analyzing an accounting dashboard for hospital finance leadership.",
		"Return exactly 5 short insights.",
		"Each insight must be on its own line.",
		"Prefix each line with one of these labels only: positive:, warning:, opportunity:",
		"Do not use markdown, bullets, headings, or extra intro text.",
		"",
		f"Date range: {date_range}",
		"",
		"Metrics:",
	]

	for metric in context.get("metrics") or []:
		lines.append(f"- {metric.get('label')}: {metric.get('value')} ({strip_html(metric.get('trend') or '')})")

	lines.append("")
	lines.append("Top expense categories:")
	for item in (context.get("expense_categories") or [])[:5]:
		lines.append(f"- {item.get('label')}: {item.get('value')}")

	lines.append("")
	lines.append("Top income sources:")
	for item in (context.get("income_sources") or [])[:5]:
		lines.append(f"- {item.get('label')}: {item.get('value')}")

	lines.append("")
	lines.append(f"Bank total: {context.get('account_balances_total') or '$ 0'}")
	lines.append(f"Receivables total: {(context.get('unpaid_invoices_total') or {}).get('outstanding') or '$ 0'}")
	lines.append(f"Payables total: {context.get('top_supplier_balances_total') or '$ 0'}")

	lines.append("")
	lines.append("Top receivable groups:")
	for item in (context.get("unpaid_invoices") or [])[:5]:
		lines.append(f"- {item.get('customer_group')}: {item.get('outstanding')}")

	lines.append("")
	lines.append("Top supplier balances:")
	for item in (context.get("top_supplier_balances") or [])[:5]:
		lines.append(f"- {item.get('supplier')}: {item.get('balance')}")

	budget_total = context.get("budget_variance_total") or {}
	lines.append("")
	lines.append("Budget variance summary:")
	lines.append(
		f"- Budget {budget_total.get('budget')}, Actual {budget_total.get('actual')}, Variance {budget_total.get('variance')}, Indicator {budget_total.get('indicator_label')}"
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

		matched = None
		lower_line = line.lower()
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


# -----------------------------------------------------------------------------
# Formatting and utility functions
# -----------------------------------------------------------------------------



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
		current_start = add_days(current_end, 1)

	return buckets


def get_bucket_for_date(buckets, posting_date):
	for bucket in buckets:
		if bucket["start"] <= posting_date <= bucket["end"]:
			return bucket
	return None


def get_scaled_bar_height(value, max_value, min_height, max_height):
	value = flt(value)
	max_value = flt(max_value)
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


def format_metric_currency(value, currency_symbol=None):
	return f"{currency_symbol or '$'} {flt(value):,.0f}"


def build_metric_trend(current_value, previous_value):
	current_value = flt(current_value)
	previous_value = flt(previous_value)
	change = current_value - previous_value

	if abs(change) <= MINIMUM_AMOUNT:
		return {"trend_class": "flat", "trend": "&rarr; 0.0%"}

	if abs(previous_value) <= MINIMUM_AMOUNT:
		percent_change = 100.0
	else:
		percent_change = abs(change / previous_value) * 100

	if percent_change < 0.05:
		return {"trend_class": "flat", "trend": "&rarr; 0.0%"}
	if change > 0:
		return {"trend_class": "up", "trend": f"&uarr; {percent_change:.1f}%"}
	return {"trend_class": "down", "trend": f"&darr; {percent_change:.1f}%"}


def get_variance_class(variance):
	if flt(variance) < -MINIMUM_AMOUNT:
		return "negative"
	if flt(variance) > MINIMUM_AMOUNT:
		return "positive"
	return "neutral"


def strip_company_abbr(account):
	account = account or ""
	return account.rsplit(" - ", 1)[0] if " - " in account else account


def strip_html(value):
	text = frappe.safe_decode(value or "")
	for token in ("&uarr;", "&darr;", "&rarr;"):
		text = text.replace(token, "")
	return frappe.utils.strip_html(text).strip()


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
	period_days = max(date_diff(to_date, from_date) + 1, 1)
	previous_to_date = add_days(from_date, -1)
	previous_from_date = add_days(previous_to_date, -(period_days - 1))
	return previous_from_date, previous_to_date


def get_display_date_range(from_date, to_date):
	return f"{formatdate(from_date, 'MMM d')} &ndash; {formatdate(to_date, 'MMM d, yyyy')}"


def get_display_comparison_range(from_date, to_date):
	previous_from_date, previous_to_date = get_previous_period_dates(getdate(from_date), getdate(to_date))
	return f"{formatdate(previous_from_date, 'MMM d')} &ndash; {formatdate(previous_to_date, 'MMM d')}"


def get_default_company():
	return (
		frappe.defaults.get_user_default("Company")
		or frappe.defaults.get_global_default("company")
		or frappe.db.get_single_value("Global Defaults", "default_company")
	)


def get_company_currency(company):
	return frappe.get_cached_value("Company", company, "default_currency") if company else None


def get_currency_symbol(currency):
	return frappe.db.get_value("Currency", currency, "symbol") if currency else "$"


# Backward-compatible wrappers kept for any existing imports. The dashboard itself
# does not use these wrappers, because it loads each source table once and passes
# the loaded rows into calculation functions.
def generate_financial_statement_gl(company=None, from_date=None, to_date=None):
	company = company or get_default_company()
	from_date = getdate(from_date) if from_date else get_first_day(getdate(nowdate()))
	to_date = getdate(to_date) if to_date else getdate(nowdate())
	return get_finance_gl_rows(company, from_date, to_date)


def get_metrics(from_date=None, to_date=None):
	data = get_dashboard_data(from_date, to_date)
	return data.get("metrics") or []


def get_bank_account_balances(company=None, report_date=None, currency=None):
	company = company or get_default_company()
	currency_symbol = get_currency_symbol(currency or get_company_currency(company))
	report_date = getdate(report_date or nowdate())
	return get_bank_account_balances_from_rows(get_finance_gl_rows(company, report_date, report_date), report_date, currency_symbol)


def get_receivables_by_customer_group(company=None, report_date=None, currency=None):
	company = company or get_default_company()
	currency_symbol = get_currency_symbol(currency or get_company_currency(company))
	report_date = getdate(report_date or nowdate())
	return get_receivables_by_customer_group_from_rows(get_payment_ledger_rows(company, report_date), report_date, currency_symbol)


def get_top_supplier_balances(company=None, report_date=None, currency=None, limit=10):
	company = company or get_default_company()
	currency_symbol = get_currency_symbol(currency or get_company_currency(company))
	report_date = getdate(report_date or nowdate())
	return get_top_supplier_balances_from_rows(get_payment_ledger_rows(company, report_date), report_date, currency_symbol, limit)


def get_party_outstanding_total(company, report_date, party_type):
	return get_party_outstanding_total_from_rows(get_payment_ledger_rows(company, report_date), getdate(report_date), party_type)


def get_profit_and_loss_metrics(company, from_date, to_date):
	rows = get_finance_gl_rows(company, getdate(from_date), getdate(to_date))
	totals = calculate_profit_and_loss_from_rows(rows, getdate(from_date), getdate(to_date))
	return totals["income"], totals["expense"], totals["profit"]


def get_budget_variance_data(from_date, to_date, limit=None):
	budget_rows = get_budget_rows(from_date, to_date)
	accounts = {row.get("account") for row in budget_rows if row.get("account")}
	company = get_default_company()
	currency_symbol = get_currency_symbol(get_company_currency(company))
	gl_rows = get_finance_gl_rows(company, getdate(from_date), getdate(to_date), accounts)
	actual_map = get_actual_amount_by_account_from_rows(gl_rows, getdate(from_date), getdate(to_date), accounts)
	return get_budget_variance_data_from_rows(budget_rows, actual_map, currency_symbol, limit)


def get_budget_variance_rows(from_date, to_date, limit=None):
	rows, _total = get_budget_variance_data(from_date, to_date, limit)
	return rows


def get_budget_variance_total(from_date, to_date):
	_rows, total = get_budget_variance_data(from_date, to_date)
	return total


def get_outstanding_total(report_name, company, report_date):
	party_type = "Customer" if "Receivable" in (report_name or "") else "Supplier"
	return get_party_outstanding_total(company, report_date, party_type)


def get_summary_value(summary, label_key):
	for row in summary or []:
		label = (row.get("label") or "").lower()
		if label_key in label:
			return flt(row.get("value"))
	return 0


def get_row_outstanding(row):
	return flt(row.get("outstanding")) if isinstance(row, dict) else 0

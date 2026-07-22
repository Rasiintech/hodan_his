import frappe
from frappe.utils import (
	add_days,
	cint,
	cstr,
	date_diff,
	flt,
	formatdate,
	get_first_day,
	get_last_day,
	getdate,
	nowdate,
)


DASHBOARD_CACHE_SECONDS = 300
DEFAULT_VISIBLE_LIMIT = 10
DEFAULT_QUERY_LIMIT = 100


@frappe.whitelist()
def get_dashboard_data(from_date=None, to_date=None, use_cache=1):
	"""
	Optimized sales dashboard.

	Main performance changes:
	1. Does not load all Sales Invoice rows into Python.
	2. Uses SQL aggregation for metrics, donuts, doctor, department, admission, item group, and matrix.
	3. Only small grouped result sets are processed in Python.
	4. Caches dashboard response for a short time.
	5. Caches DocType metadata column discovery.
	"""

	from_date, to_date = get_date_range(from_date, to_date)
	previous_from_date, previous_to_date = get_previous_period_dates(from_date, to_date)

	cache_key = get_dashboard_cache_key(from_date, to_date)
	if cint(use_cache):
		cached = get_cached_value(cache_key)
		if cached:
			return cached

	# Compute once per request; avoids ~15+ redundant cache lookups per load
	invoice_ctx = get_sales_invoice_sql_context()
	item_ctx = get_sales_item_sql_context()

	# current_summary = get_sales_summary(from_date, to_date, invoice_ctx)
	# previous_summary = get_sales_summary(previous_from_date, previous_to_date, invoice_ctx)
	current_summary, previous_summary = get_sales_summary(
		from_date, to_date, previous_from_date, previous_to_date, invoice_ctx
	)

	# sales_channel_rows, expense_donut_style, expense_empty_message = get_sales_channel_donut_data(
	# 	from_date, to_date, invoice_ctx
	# )
	income_expenses, sales_channel_rows, expense_donut_style, expense_empty_message = get_sales_channel_and_chart_data(
		from_date, to_date, invoice_ctx
	)
	# inpatient_type_rows, source_donut_style, income_empty_message = get_item_admission_type_donut_data(
	# 	from_date, to_date, item_ctx
	# )

	# item_group_performance, item_group_total = get_item_group_performance_rows(from_date, to_date, item_ctx)
	item_group_performance, item_group_total, inpatient_type_rows, source_donut_style, income_empty_message = get_item_group_and_admission_data(
		from_date, to_date, item_ctx
	)
	doctor_item_group_rows, doctor_item_group_total, doctor_item_group_columns = get_doctor_item_group_rows(
		from_date, to_date, item_ctx
	)

	# doctor_performance_rows, doctor_performance_total, doctor_ipd_type_columns = get_entity_sales_rows(
	# 	from_date, to_date, invoice_ctx,
	# 	entity="doctor", label_key="doctor", empty_label="Walk-in",
	# )
	# department_performance_rows, department_performance_total, department_ipd_type_columns = get_entity_sales_rows(
	# 	from_date, to_date, invoice_ctx,
	# 	entity="department", label_key="department", empty_label="Unassigned",
	# )
	(
		doctor_performance_rows, doctor_performance_total, doctor_ipd_type_columns,
		department_performance_rows, department_performance_total, department_ipd_type_columns,
	) = get_doctor_and_department_sales_rows(from_date, to_date, invoice_ctx)

	doctor_performance_rows, doctor_performance_has_more = mark_over_limit_rows(doctor_performance_rows)
	department_performance_rows, department_performance_has_more = mark_over_limit_rows(department_performance_rows)

	admission_rows = get_admission_sales_rows(from_date, to_date, invoice_ctx)
	admission_rows, admission_has_more = mark_over_limit_rows(admission_rows)

	item_group_performance, item_group_performance_has_more = mark_over_limit_rows(item_group_performance)
	doctor_item_group_rows, doctor_item_group_has_more = mark_over_limit_rows(doctor_item_group_rows)

	

	result = {
		"from_date": str(from_date),
		"to_date": str(to_date),
		"date_range": get_display_date_range(from_date, to_date),
		"comparison_range": get_display_comparison_range(from_date, to_date),
		"metrics": get_metrics(current_summary, previous_summary),
		"income_expenses": get_sales_collection_chart_data(from_date, to_date, invoice_ctx),
		"expense_categories": sales_channel_rows,
		"expense_donut_style": expense_donut_style,
		"expense_empty_message": expense_empty_message,
		"income_sources": inpatient_type_rows,
		"source_donut_style": source_donut_style,
		"income_empty_message": income_empty_message,
		"account_balances": get_doctor_sales_rows(from_date, to_date, invoice_ctx),
		"unpaid_invoices": doctor_performance_rows,
		"unpaid_invoices_total": doctor_performance_total,
		"ipd_type_columns": doctor_ipd_type_columns,
		"performance_views": {
			"doctor": {
				"label": "Doctor Performance",
				"entity_label": "Doctor",
				"rows": doctor_performance_rows,
				"total": doctor_performance_total,
				"ipd_type_columns": doctor_ipd_type_columns,
				"has_more": doctor_performance_has_more,
			},
			"department": {
				"label": "Department Performance",
				"entity_label": "Department",
				"rows": department_performance_rows,
				"total": department_performance_total,
				"ipd_type_columns": department_ipd_type_columns,
				"has_more": department_performance_has_more,
			},
		},
		"top_supplier_balances": admission_rows,
		"top_supplier_balances_has_more": admission_has_more,
		"budget_variance": item_group_performance,
		"budget_variance_total": item_group_total,
		"item_group_views": {
			"summary": {
				"label": "Item Group Summary",
				"rows": item_group_performance,
				"total": item_group_total,
				"has_more": item_group_performance_has_more,
			},
			"doctor_matrix": {
				"label": "Doctor by Item Group",
				"entity_label": "Doctor",
				"columns": doctor_item_group_columns,
				"rows": doctor_item_group_rows,
				"total": doctor_item_group_total,
				"has_more": doctor_item_group_has_more,
			},
		},
		"budget_variance_message": "" if item_group_performance else "No sales activity overlaps the selected date range.",
		"cash_flow": [],
		"insights": [],
	}

	if cint(use_cache):
		set_cached_value(cache_key, result, DASHBOARD_CACHE_SECONDS)

	return result


@frappe.whitelist(methods=["POST"])
def get_ai_insights(dashboard_context=None, from_date=None, to_date=None):
	try:
		context = frappe.parse_json(dashboard_context) if dashboard_context else {}
		if not isinstance(context, dict):
			context = {}

		from coreinsight_ai.api.chatbot import chat

		prompt = build_sales_ai_prompt(context, from_date=from_date, to_date=to_date)
		result = chat(
			messages=[{"role": "user", "content": prompt}],
			options={"answer_style": "analysis", "temperature": 0.2},
		)
		content = (result or {}).get("content") or ""
		return {"insights": parse_ai_insight_response(content), "raw_content": content}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Sales Dashboard AI Insight")
		return {
			"insights": [
				{
					"icon_class": "fa-info-circle",
					"text_class": "slate-text",
					"text": "Insights are not available right now. Please review the dashboard figures below.",
				}
			]
		}


# def get_sales_summary(from_date, to_date, ctx):
# 	return frappe.db.sql(
# 		f"""
# 		SELECT
# 			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 0 THEN ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE 0 END), 0) AS gross_sales,
# 			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 0 THEN ABS(IFNULL(si.{ctx.discount_field}, 0)) ELSE 0 END), 0) AS discount,
# 			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE 0 END), 0) AS returns_total,
# 			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN -ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE ABS(IFNULL(si.{ctx.amount_field}, 0)) END), 0) AS net_sales,
# 			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN 0 ELSE ABS(IFNULL(si.{ctx.paid_field}, 0)) END), 0) AS collections,
# 			COALESCE(SUM(
# 				CASE
# 					WHEN IFNULL(si.is_return, 0) = 0 AND ABS(IFNULL(si.{ctx.outstanding_field}, 0)) <= 0.005
# 					THEN ABS(IFNULL(si.{ctx.amount_field}, 0))
# 					ELSE 0
# 				END
# 			), 0) AS cash_sales,
# 			COALESCE(SUM(
# 				CASE
# 					WHEN IFNULL(si.is_return, 0) = 0 AND ABS(IFNULL(si.{ctx.outstanding_field}, 0)) > 0.005
# 					THEN ABS(IFNULL(si.{ctx.amount_field}, 0))
# 					ELSE 0
# 				END
# 			), 0) AS credit_sales
# 		FROM `tabSales Invoice` si
# 		WHERE
# 			si.docstatus = 1
# 			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
# 		""",
# 		{"from_date": from_date, "to_date": to_date},
# 		as_dict=True,
# 	)[0]

def get_sales_summary(from_date, to_date, previous_from_date, previous_to_date, ctx):
	"""
	Computes current and previous period summaries in a single table scan,
	instead of two independent queries against tabSales Invoice.
	"""
	row = frappe.db.sql(
		f"""
		SELECT
			COALESCE(SUM(CASE WHEN si.posting_date BETWEEN %(from_date)s AND %(to_date)s
				AND IFNULL(si.is_return, 0) = 0 THEN ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE 0 END), 0) AS gross_sales,
			COALESCE(SUM(CASE WHEN si.posting_date BETWEEN %(from_date)s AND %(to_date)s
				AND IFNULL(si.is_return, 0) = 0 THEN ABS(IFNULL(si.{ctx.discount_field}, 0)) ELSE 0 END), 0) AS discount,
			COALESCE(SUM(CASE WHEN si.posting_date BETWEEN %(from_date)s AND %(to_date)s
				AND IFNULL(si.is_return, 0) = 1 THEN ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE 0 END), 0) AS returns_total,
			COALESCE(SUM(CASE WHEN si.posting_date BETWEEN %(from_date)s AND %(to_date)s THEN
				(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN -ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE ABS(IFNULL(si.{ctx.amount_field}, 0)) END)
				ELSE 0 END), 0) AS net_sales,
			COALESCE(SUM(CASE WHEN si.posting_date BETWEEN %(from_date)s AND %(to_date)s
				AND IFNULL(si.is_return, 0) = 0 THEN ABS(IFNULL(si.{ctx.paid_field}, 0)) ELSE 0 END), 0) AS collections,
			COALESCE(SUM(
				CASE WHEN si.posting_date BETWEEN %(from_date)s AND %(to_date)s
					AND IFNULL(si.is_return, 0) = 0 AND ABS(IFNULL(si.{ctx.outstanding_field}, 0)) <= 0.005
					THEN ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE 0 END
			), 0) AS cash_sales,
			COALESCE(SUM(
				CASE WHEN si.posting_date BETWEEN %(from_date)s AND %(to_date)s
					AND IFNULL(si.is_return, 0) = 0 AND ABS(IFNULL(si.{ctx.outstanding_field}, 0)) > 0.005
					THEN ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE 0 END
			), 0) AS credit_sales,

			COALESCE(SUM(CASE WHEN si.posting_date BETWEEN %(prev_from_date)s AND %(prev_to_date)s
				AND IFNULL(si.is_return, 0) = 0 THEN ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE 0 END), 0) AS prev_gross_sales,
			COALESCE(SUM(CASE WHEN si.posting_date BETWEEN %(prev_from_date)s AND %(prev_to_date)s
				AND IFNULL(si.is_return, 0) = 0 THEN ABS(IFNULL(si.{ctx.discount_field}, 0)) ELSE 0 END), 0) AS prev_discount,
			COALESCE(SUM(CASE WHEN si.posting_date BETWEEN %(prev_from_date)s AND %(prev_to_date)s
				AND IFNULL(si.is_return, 0) = 1 THEN ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE 0 END), 0) AS prev_returns_total,
			COALESCE(SUM(CASE WHEN si.posting_date BETWEEN %(prev_from_date)s AND %(prev_to_date)s THEN
				(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN -ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE ABS(IFNULL(si.{ctx.amount_field}, 0)) END)
				ELSE 0 END), 0) AS prev_net_sales,
			COALESCE(SUM(CASE WHEN si.posting_date BETWEEN %(prev_from_date)s AND %(prev_to_date)s
				AND IFNULL(si.is_return, 0) = 0 THEN ABS(IFNULL(si.{ctx.paid_field}, 0)) ELSE 0 END), 0) AS prev_collections,
			COALESCE(SUM(
				CASE WHEN si.posting_date BETWEEN %(prev_from_date)s AND %(prev_to_date)s
					AND IFNULL(si.is_return, 0) = 0 AND ABS(IFNULL(si.{ctx.outstanding_field}, 0)) <= 0.005
					THEN ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE 0 END
			), 0) AS prev_cash_sales,
			COALESCE(SUM(
				CASE WHEN si.posting_date BETWEEN %(prev_from_date)s AND %(prev_to_date)s
					AND IFNULL(si.is_return, 0) = 0 AND ABS(IFNULL(si.{ctx.outstanding_field}, 0)) > 0.005
					THEN ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE 0 END
			), 0) AS prev_credit_sales
		FROM `tabSales Invoice` si
		WHERE
			si.docstatus = 1
			AND si.posting_date BETWEEN %(min_date)s AND %(max_date)s
		""",
		{
			"from_date": from_date,
			"to_date": to_date,
			"prev_from_date": previous_from_date,
			"prev_to_date": previous_to_date,
			# widest bound across both ranges, so the WHERE clause can still use
			# an index on posting_date instead of scanning the whole table
			"min_date": min(from_date, previous_from_date),
			"max_date": max(to_date, previous_to_date),
		},
		as_dict=True,
	)[0]

	current_summary = frappe._dict(
		gross_sales=row["gross_sales"], discount=row["discount"], returns_total=row["returns_total"],
		net_sales=row["net_sales"], collections=row["collections"],
		cash_sales=row["cash_sales"], credit_sales=row["credit_sales"],
	)
	previous_summary = frappe._dict(
		gross_sales=row["prev_gross_sales"], discount=row["prev_discount"], returns_total=row["prev_returns_total"],
		net_sales=row["prev_net_sales"], collections=row["prev_collections"],
		cash_sales=row["prev_cash_sales"], credit_sales=row["prev_credit_sales"],
	)
	return current_summary, previous_summary
def get_metrics(current_summary, previous_summary):
	return [
		{
			"class": "income",
			"icon": '<i class="fa fa-money"></i>',
			"label": "Total Sales",
			"value": format_metric_currency(current_summary.get("gross_sales")),
			**build_metric_trend(current_summary.get("gross_sales"), previous_summary.get("gross_sales")),
		},
		{
			"class": "expense",
			"icon": '<i class="fa fa-percent"></i>',
			"label": "Discount",
			"value": format_metric_currency(current_summary.get("discount")),
			**build_metric_trend(current_summary.get("discount"), previous_summary.get("discount")),
		},
		{
			"class": "profit",
			"icon": '<i class="fa fa-undo"></i>',
			"label": "Returns",
			"value": format_metric_currency(current_summary.get("returns_total")),
			**build_metric_trend(current_summary.get("returns_total"), previous_summary.get("returns_total")),
		},
		{
			"class": "cash",
			"icon": '<i class="fa fa-money"></i>',
			"label": "Cash Sales",
			"value": format_metric_currency(current_summary.get("cash_sales")),
			**build_metric_trend(current_summary.get("cash_sales"), previous_summary.get("cash_sales")),
		},
		{
			"class": "bank",
			"icon": '<i class="fa fa-credit-card"></i>',
			"label": "Credit Sales",
			"value": format_metric_currency(current_summary.get("credit_sales")),
			**build_metric_trend(current_summary.get("credit_sales"), previous_summary.get("credit_sales")),
		},
	]


# def get_sales_channel_donut_data(from_date, to_date, ctx):
# 	rows = frappe.db.sql(
# 		f"""
# 		SELECT
# 			{ctx.sales_channel_expr} AS label,
# 			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN -ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE ABS(IFNULL(si.{ctx.amount_field}, 0)) END), 0) AS amount
# 		FROM `tabSales Invoice` si
# 		WHERE
# 			si.docstatus = 1
# 			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
# 		GROUP BY {ctx.sales_channel_expr}
# 		HAVING amount > 0
# 		ORDER BY amount DESC
# 		LIMIT 5
# 		""",
# 		{"from_date": from_date, "to_date": to_date},
# 		as_dict=True,
# 	)

# 	return build_donut_from_grouped_rows(rows, label_fallback="Hospital")


def get_sales_channel_and_chart_data(from_date, to_date, ctx):
	"""
	Single scan producing both the channel donut and the income/collections
	chart. Grouped by (posting_date, channel) so each output can be rolled
	up along its own dimension in Python — safe because both are plain SUMs.
	"""
	rows = frappe.db.sql(
		f"""
		SELECT
			si.posting_date,
			{ctx.sales_channel_expr} AS channel,
			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN 0 ELSE ABS(IFNULL(si.{ctx.amount_field}, 0)) END), 0) AS income,
			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN 0 ELSE ABS(IFNULL(si.{ctx.paid_field}, 0)) END), 0) AS collections,
			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN -ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE ABS(IFNULL(si.{ctx.amount_field}, 0)) END), 0) AS net_amount
		FROM `tabSales Invoice` si
		WHERE
			si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY si.posting_date, {ctx.sales_channel_expr}
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)

	# --- chart: roll up by date, summed across channels ---
	buckets = build_chart_buckets(from_date, to_date, 6)
	for row in rows:
		bucket = get_bucket_for_date(buckets, getdate(row.get("posting_date")))
		if not bucket:
			continue
		bucket["income"] += flt(row.get("income"))
		bucket["expense"] += flt(row.get("collections"))

	max_value = max([max(bucket["income"], bucket["expense"]) for bucket in buckets] or [0])
	max_bar_height = 154
	min_bar_height = 20

	chart_data = [
		{
			"label": formatdate(bucket["label_date"], "MMM d"),
			"income_value": format_compact_amount(bucket["income"]),
			"expense_value": format_compact_amount(bucket["expense"]),
			"income_height": get_scaled_bar_height(bucket["income"], max_value, min_bar_height, max_bar_height),
			"expense_height": get_scaled_bar_height(bucket["expense"], max_value, min_bar_height, max_bar_height),
		}
		for bucket in buckets
	]

	# --- donut: roll up by channel, summed across dates ---
	channel_totals = {}
	for row in rows:
		channel_totals[row["channel"]] = channel_totals.get(row["channel"], 0.0) + flt(row.get("net_amount"))

	donut_rows = [{"label": label, "amount": amount} for label, amount in channel_totals.items()]
	donut_rows.sort(key=lambda r: r["amount"], reverse=True)
	sales_channel_rows, expense_donut_style, expense_empty_message = build_donut_from_grouped_rows(
		donut_rows[:5], label_fallback="Hospital"
	)

	return chart_data, sales_channel_rows, expense_donut_style, expense_empty_message


# def get_item_admission_type_donut_data(from_date, to_date, ctx):
# 	rows = frappe.db.sql(
# 		f"""
# 		SELECT
# 			{ctx.admission_type_expr} AS label,
# 			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN -ABS(IFNULL(sii.{ctx.item_amount_field}, 0)) ELSE ABS(IFNULL(sii.{ctx.item_amount_field}, 0)) END), 0) AS amount
# 		FROM `tabSales Invoice Item` sii
# 		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
# 		{ctx.inpatient_join}
# 		WHERE
# 			si.docstatus = 1
# 			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
# 		GROUP BY {ctx.admission_type_expr}
# 		HAVING amount > 0
# 		ORDER BY amount DESC
# 		LIMIT 5
# 		""",
# 		{"from_date": from_date, "to_date": to_date},
# 		as_dict=True,
# 	)

# 	return build_donut_from_grouped_rows(
# 		rows,
# 		label_fallback="OPD",
# 		colors=("blue", "green", "orange", "purple", "indigo"),
# 	)

def get_item_group_and_admission_data(from_date, to_date, ctx):
	"""
	Single scan of Sales Invoice Item joined to Sales Invoice, producing both
	the item group performance table and the admission-type donut. Grouped
	by (item_group, admission_type). Revenue/qty roll up safely as SUMs in
	either direction; invoice_count (COUNT DISTINCT parent) rolls up safely
	toward item_group because admission_type is an invoice-level attribute —
	a given invoice always has exactly one admission_type, so summing counts
	across admission_type subgroups for a fixed item_group can't double-count.
	"""
	rows = frappe.db.sql(
		f"""
		SELECT
			COALESCE(NULLIF(sii.item_group, ''), 'Uncategorized') AS item_group,
			{ctx.admission_type_expr} AS admission_type,
			COUNT(DISTINCT sii.parent) AS invoice_count,
			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN -ABS(IFNULL(sii.qty, 0)) ELSE ABS(IFNULL(sii.qty, 0)) END), 0) AS qty,
			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN -ABS(IFNULL(sii.{ctx.item_amount_field}, 0)) ELSE ABS(IFNULL(sii.{ctx.item_amount_field}, 0)) END), 0) AS revenue
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		{ctx.inpatient_join}
		WHERE
			si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY COALESCE(NULLIF(sii.item_group, ''), 'Uncategorized'), {ctx.admission_type_expr}
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)

	# --- item group performance: roll up by item_group, summed across admission types ---
	item_group_totals = {}
	for row in rows:
		key = row["item_group"]
		entry = item_group_totals.setdefault(key, {"category": key, "invoice_count": 0, "qty": 0.0, "revenue": 0.0})
		entry["invoice_count"] += cint(row.get("invoice_count"))
		entry["qty"] += flt(row.get("qty"))
		entry["revenue"] += flt(row.get("revenue"))

	item_group_rows = [
		r for r in item_group_totals.values()
		if abs(r["revenue"]) > 0.005 or abs(r["qty"]) > 0.005
	]
	item_group_rows.sort(key=lambda r: r["revenue"], reverse=True)
	item_group_rows = item_group_rows[:DEFAULT_QUERY_LIMIT]

	total_revenue = sum(r["revenue"] for r in item_group_rows)
	total_invoices = sum(r["invoice_count"] for r in item_group_rows)
	total_qty = sum(r["qty"] for r in item_group_rows)

	formatted_item_group_rows = []
	for r in item_group_rows:
		share = (r["revenue"] / total_revenue * 100) if total_revenue else 0
		indicator = get_mix_indicator(share)
		formatted_item_group_rows.append({
			"category": r["category"],
			"budget": format_metric_number(r["invoice_count"]),
			"actual": format_quantity(r["qty"]),
			"variance": format_metric_currency(r["revenue"]),
			"variance_class": get_variance_class(r["revenue"]),
			"indicator_label": indicator["label"],
			"indicator_class": indicator["class"],
			"utilization": f"{share:.1f}%",
		})

	total_share = "100.0%" if total_revenue else "0.0%"
	total_indicator = get_mix_indicator(100 if total_revenue else 0)
	item_group_total = {
		"budget": format_metric_number(total_invoices),
		"actual": format_quantity(total_qty),
		"variance": format_metric_currency(total_revenue),
		"variance_class": get_variance_class(total_revenue),
		"indicator_label": total_indicator["label"],
		"indicator_class": total_indicator["class"],
		"utilization": total_share,
	}

	# --- admission-type donut: roll up by admission_type, summed across item groups ---
	admission_totals = {}
	for row in rows:
		admission_totals[row["admission_type"]] = admission_totals.get(row["admission_type"], 0.0) + flt(row.get("revenue"))

	donut_rows = [{"label": label, "amount": amount} for label, amount in admission_totals.items()]
	donut_rows.sort(key=lambda r: r["amount"], reverse=True)
	inpatient_type_rows, source_donut_style, income_empty_message = build_donut_from_grouped_rows(
		donut_rows[:5], label_fallback="OPD", colors=("blue", "green", "orange", "purple", "indigo")
	)

	return formatted_item_group_rows, item_group_total, inpatient_type_rows, source_donut_style, income_empty_message


def get_sales_collection_chart_data(from_date, to_date, ctx):
	buckets = build_chart_buckets(from_date, to_date, 6)

	rows = frappe.db.sql(
		f"""
		SELECT
			si.posting_date,
			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN 0 ELSE ABS(IFNULL(si.{ctx.amount_field}, 0)) END), 0) AS income,
			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN 0 ELSE ABS(IFNULL(si.{ctx.paid_field}, 0)) END), 0) AS collections
		FROM `tabSales Invoice` si
		WHERE
			si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY si.posting_date
		ORDER BY si.posting_date ASC
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)

	for row in rows:
		bucket = get_bucket_for_date(buckets, getdate(row.get("posting_date")))
		if not bucket:
			continue
		bucket["income"] += flt(row.get("income"))
		bucket["expense"] += flt(row.get("collections"))

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


def get_doctor_sales_rows(from_date, to_date, ctx, limit=DEFAULT_QUERY_LIMIT):
	rows = frappe.db.sql(
		f"""
		SELECT
			COALESCE(NULLIF(si.ref_practitioner, ''), 'Walk-in / Unassigned') AS account,
			COALESCE(NULLIF(hp.department, ''), 'Unassigned') AS type,
			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN -ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE ABS(IFNULL(si.{ctx.amount_field}, 0)) END), 0) AS raw_balance
		FROM `tabSales Invoice` si
		LEFT JOIN `tabHealthcare Practitioner` hp ON hp.name = si.ref_practitioner
		WHERE
			si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND IFNULL(si.is_return, 0) = 0
		GROUP BY account, type
		HAVING raw_balance > 0
		ORDER BY raw_balance DESC
		LIMIT {int(limit)}
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)

	for row in rows:
		row["balance"] = format_metric_currency(row.get("raw_balance"))

	return rows


# def get_entity_sales_rows(from_date, to_date, ctx, entity, label_key, empty_label, limit=DEFAULT_QUERY_LIMIT):
# 	if entity == "department":
# 		entity_expr = "COALESCE(NULLIF(hp.department, ''), 'Unassigned')"
# 	else:
# 		entity_expr = "COALESCE(NULLIF(si.ref_practitioner, ''), 'Walk-in / Unassigned')"

# 	grouped_rows = frappe.db.sql(
# 		f"""
# 		SELECT
# 			{entity_expr} AS entity_label,
# 			{ctx.admission_type_expr} AS admission_type,
# 			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN 0 ELSE ABS(IFNULL(si.{ctx.amount_field}, 0)) END), 0) AS amount
# 		FROM `tabSales Invoice` si
# 		LEFT JOIN `tabHealthcare Practitioner` hp ON hp.name = si.ref_practitioner
# 		{ctx.inpatient_join}
# 		WHERE
# 			si.docstatus = 1
# 			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
# 			AND IFNULL(si.is_return, 0) = 0
# 		GROUP BY {entity_expr}, {ctx.admission_type_expr}
# 		HAVING amount > 0
# 		ORDER BY amount DESC
# 		""",
# 		{"from_date": from_date, "to_date": to_date},
# 		as_dict=True,
# 	)

# 	grouped = {}
# 	ipd_type_labels = set()
# 	total_sales = 0.0
# 	total_opd_sales = 0.0
# 	ipd_type_totals = {}

# 	for row in grouped_rows:
# 		amount = flt(row.get("amount"))
# 		entity_label = (row.get("entity_label") or "").strip() or empty_label
# 		admission_type = normalize_admission_type(row.get("admission_type"))

# 		entry = grouped.setdefault(
# 			entity_label,
# 			{
# 				label_key: entity_label,
# 				"raw_net_sales": 0.0,
# 				"raw_opd_sales": 0.0,
# 				"ipd_type_amounts": {},
# 			},
# 		)

# 		entry["raw_net_sales"] += amount
# 		total_sales += amount

# 		if admission_type.upper() == "OPD":
# 			entry["raw_opd_sales"] += amount
# 			total_opd_sales += amount
# 		else:
# 			entry["ipd_type_amounts"][admission_type] = entry["ipd_type_amounts"].get(admission_type, 0.0) + amount
# 			ipd_type_totals[admission_type] = ipd_type_totals.get(admission_type, 0.0) + amount
# 			ipd_type_labels.add(admission_type)

# 	rows = sorted(grouped.values(), key=lambda item: item["raw_net_sales"], reverse=True)[: int(limit)]
# 	ipd_type_columns = [
# 		{"label": label, "fieldname": scrub_ipd_type_label(label)}
# 		for label in sorted(ipd_type_labels)
# 	]

# 	for row in rows:
# 		row["net_sales"] = format_metric_currency(row["raw_net_sales"])
# 		row["sales_share"] = f"{((row['raw_net_sales'] / total_sales) * 100):.1f}%" if total_sales else "0.0%"
# 		row["opd_sales"] = format_metric_currency(row["raw_opd_sales"])
# 		row["ipd_type_values"] = [
# 			format_metric_currency(row["ipd_type_amounts"].get(column["label"], 0.0))
# 			for column in ipd_type_columns
# 		]

# 	total_row = {
# 		"outstanding": format_metric_currency(total_sales),
# 		"opd_sales": format_metric_currency(total_opd_sales),
# 		"ipd_type_values": [
# 			format_metric_currency(ipd_type_totals.get(column["label"], 0.0))
# 			for column in ipd_type_columns
# 		],
# 	}

# 	return rows, total_row, ipd_type_columns


def get_doctor_and_department_sales_rows(from_date, to_date, ctx):
	"""
	Computes doctor and department performance in a single query instead of
	two separate scans over the same joined rows.
	"""
	rows = frappe.db.sql(
		f"""
		SELECT
			COALESCE(NULLIF(si.ref_practitioner, ''), 'Walk-in / Unassigned') AS doctor_label,
			COALESCE(NULLIF(hp.department, ''), 'Unassigned') AS department_label,
			{ctx.admission_type_expr} AS admission_type,
			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN 0 ELSE ABS(IFNULL(si.{ctx.amount_field}, 0)) END), 0) AS amount
		FROM `tabSales Invoice` si
		LEFT JOIN `tabHealthcare Practitioner` hp ON hp.name = si.ref_practitioner
		{ctx.inpatient_join}
		WHERE
			si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND IFNULL(si.is_return, 0) = 0
		GROUP BY
			COALESCE(NULLIF(si.ref_practitioner, ''), 'Walk-in / Unassigned'),
			COALESCE(NULLIF(hp.department, ''), 'Unassigned'),
			{ctx.admission_type_expr}
		HAVING amount > 0
		ORDER BY amount DESC
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)

	doctor_rows, doctor_total, doctor_columns = build_entity_summary(
		rows, group_field="doctor_label", label_key="doctor", empty_label="Walk-in / Unassigned"
	)
	department_rows, department_total, department_columns = build_entity_summary(
		rows, group_field="department_label", label_key="department", empty_label="Unassigned"
	)

	return (
		doctor_rows, doctor_total, doctor_columns,
		department_rows, department_total, department_columns,
	)

def build_entity_summary(rows, group_field, label_key, empty_label, limit=DEFAULT_QUERY_LIMIT):
	# This is exactly the grouping/formatting body that already exists
	# inside get_entity_sales_rows today — unchanged logic, just extracted
	# so it can be reused for both the doctor grouping and the department
	# grouping without re-querying the database.
	grouped = {}
	ipd_type_labels = set()
	total_sales = 0.0
	total_opd_sales = 0.0
	ipd_type_totals = {}

	for row in rows:
		amount = flt(row.get("amount"))
		entity_label = (row.get(group_field) or "").strip() or empty_label
		admission_type = normalize_admission_type(row.get("admission_type"))

		entry = grouped.setdefault(
			entity_label,
			{label_key: entity_label, "raw_net_sales": 0.0, "raw_opd_sales": 0.0, "ipd_type_amounts": {}},
		)
		entry["raw_net_sales"] += amount
		total_sales += amount

		if admission_type.upper() == "OPD":
			entry["raw_opd_sales"] += amount
			total_opd_sales += amount
		else:
			entry["ipd_type_amounts"][admission_type] = entry["ipd_type_amounts"].get(admission_type, 0.0) + amount
			ipd_type_totals[admission_type] = ipd_type_totals.get(admission_type, 0.0) + amount
			ipd_type_labels.add(admission_type)

	entity_rows = sorted(grouped.values(), key=lambda item: item["raw_net_sales"], reverse=True)[: int(limit)]
	ipd_type_columns = [{"label": label, "fieldname": scrub_ipd_type_label(label)} for label in sorted(ipd_type_labels)]

	for row in entity_rows:
		row["net_sales"] = format_metric_currency(row["raw_net_sales"])
		row["sales_share"] = f"{((row['raw_net_sales'] / total_sales) * 100):.1f}%" if total_sales else "0.0%"
		row["opd_sales"] = format_metric_currency(row["raw_opd_sales"])
		row["ipd_type_values"] = [
			format_metric_currency(row["ipd_type_amounts"].get(column["label"], 0.0)) for column in ipd_type_columns
		]

	total_row = {
		"outstanding": format_metric_currency(total_sales),
		"opd_sales": format_metric_currency(total_opd_sales),
		"ipd_type_values": [format_metric_currency(ipd_type_totals.get(column["label"], 0.0)) for column in ipd_type_columns],
	}

	return entity_rows, total_row, ipd_type_columns

def get_admission_sales_rows(from_date, to_date, ctx, limit=DEFAULT_QUERY_LIMIT):
	rows = frappe.db.sql(
		f"""
		SELECT
			{ctx.admission_type_expr} AS supplier,
			COUNT(DISTINCT COALESCE(NULLIF({ctx.patient_expr}, ''), NULLIF({ctx.patient_name_expr}, ''))) AS supplier_group,
			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN -ABS(IFNULL(si.{ctx.amount_field}, 0)) ELSE ABS(IFNULL(si.{ctx.amount_field}, 0)) END), 0) AS raw_balance
		FROM `tabSales Invoice` si
		LEFT JOIN `tabHealthcare Practitioner` hp ON hp.name = si.ref_practitioner
		{ctx.inpatient_join}
		WHERE
			si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY {ctx.admission_type_expr}
		HAVING raw_balance > 0
		ORDER BY raw_balance DESC
		LIMIT {int(limit)}
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)

	for row in rows:
		row["supplier"] = normalize_admission_type(row.get("supplier"))
		row["balance"] = format_metric_currency(row.get("raw_balance"))

	return rows


def get_item_group_performance_rows(from_date, to_date, ctx, limit=DEFAULT_QUERY_LIMIT):
	rows = frappe.db.sql(
		f"""
		SELECT
			COALESCE(NULLIF(sii.item_group, ''), 'Uncategorized') AS category,
			COUNT(DISTINCT sii.parent) AS invoice_count,
			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN -ABS(IFNULL(sii.qty, 0)) ELSE ABS(IFNULL(sii.qty, 0)) END), 0) AS qty,
			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN -ABS(IFNULL(sii.{ctx.item_amount_field}, 0)) ELSE ABS(IFNULL(sii.{ctx.item_amount_field}, 0)) END), 0) AS revenue
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE
			si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY COALESCE(NULLIF(sii.item_group, ''), 'Uncategorized')
		HAVING ABS(revenue) > 0.005 OR ABS(qty) > 0.005
		ORDER BY revenue DESC
		LIMIT {int(limit)}
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)

	total_revenue = sum(flt(row.get("revenue")) for row in rows)
	total_invoices = sum(cint(row.get("invoice_count")) for row in rows)
	total_qty = sum(flt(row.get("qty")) for row in rows)

	formatted_rows = []
	for row in rows:
		revenue = flt(row.get("revenue"))
		share = (revenue / total_revenue * 100) if total_revenue else 0
		indicator = get_mix_indicator(share)
		formatted_rows.append(
			{
				"category": row.get("category") or "Uncategorized",
				"budget": format_metric_number(row.get("invoice_count")),
				"actual": format_quantity(row.get("qty")),
				"variance": format_metric_currency(revenue),
				"variance_class": get_variance_class(revenue),
				"indicator_label": indicator["label"],
				"indicator_class": indicator["class"],
				"utilization": f"{share:.1f}%",
			}
		)

	total_share = "100.0%" if total_revenue else "0.0%"
	total_indicator = get_mix_indicator(100 if total_revenue else 0)
	return formatted_rows, {
		"budget": format_metric_number(total_invoices),
		"actual": format_quantity(total_qty),
		"variance": format_metric_currency(total_revenue),
		"variance_class": get_variance_class(total_revenue),
		"indicator_label": total_indicator["label"],
		"indicator_class": total_indicator["class"],
		"utilization": total_share,
	}


def get_doctor_item_group_rows(from_date, to_date, ctx, doctor_limit=DEFAULT_QUERY_LIMIT, item_group_limit=DEFAULT_QUERY_LIMIT):
	item_group_columns = frappe.db.sql(
		f"""
		SELECT
			COALESCE(NULLIF(sii.item_group, ''), 'Uncategorized') AS label,
			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN -ABS(IFNULL(sii.{ctx.item_amount_field}, 0)) ELSE ABS(IFNULL(sii.{ctx.item_amount_field}, 0)) END), 0) AS amount
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE
			si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
		GROUP BY COALESCE(NULLIF(sii.item_group, ''), 'Uncategorized')
		HAVING ABS(amount) > 0.005
		ORDER BY amount DESC
		LIMIT {int(item_group_limit)}
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)

	columns = [
		{"label": row.get("label"), "fieldname": scrub_ipd_type_label(row.get("label"))}
		for row in item_group_columns
	]

	if not columns:
		return [], {"total_amount": format_metric_currency(0), "item_group_values": []}, []

	allowed_item_groups = [row.get("label") for row in item_group_columns]
	matrix_rows = frappe.db.sql(
		f"""
		SELECT
			COALESCE(NULLIF(si.ref_practitioner, ''), 'Walk-in / Unassigned') AS doctor,
			COALESCE(NULLIF(sii.item_group, ''), 'Uncategorized') AS item_group,
			COALESCE(SUM(CASE WHEN IFNULL(si.is_return, 0) = 1 THEN -ABS(IFNULL(sii.{ctx.item_amount_field}, 0)) ELSE ABS(IFNULL(sii.{ctx.item_amount_field}, 0)) END), 0) AS amount
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE
			si.docstatus = 1
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND COALESCE(NULLIF(sii.item_group, ''), 'Uncategorized') IN %(item_groups)s
		GROUP BY COALESCE(NULLIF(si.ref_practitioner, ''), 'Walk-in / Unassigned'), COALESCE(NULLIF(sii.item_group, ''), 'Uncategorized')
		HAVING ABS(amount) > 0.005
		ORDER BY amount DESC
		""",
		{"from_date": from_date, "to_date": to_date, "item_groups": tuple(allowed_item_groups)},
		as_dict=True,
	)

	doctor_totals = {}
	for row in matrix_rows:
		doctor = row.get("doctor") or "Walk-in / Unassigned"
		item_group = row.get("item_group") or "Uncategorized"
		amount = flt(row.get("amount"))

		entry = doctor_totals.setdefault(
			doctor,
			{
				"doctor": doctor,
				"raw_total": 0.0,
				"item_group_amounts": {},
			},
		)
		entry["raw_total"] += amount
		entry["item_group_amounts"][item_group] = entry["item_group_amounts"].get(item_group, 0.0) + amount

	rows = sorted(doctor_totals.values(), key=lambda item: item["raw_total"], reverse=True)[: int(doctor_limit)]

	for row in rows:
		row["total_amount"] = format_metric_currency(row["raw_total"])
		row["item_group_values"] = [
			format_metric_currency(row["item_group_amounts"].get(column["label"], 0.0))
			for column in columns
		]

	total_row = {
		"total_amount": format_metric_currency(sum(flt(row["raw_total"]) for row in rows)),
		"item_group_values": [
			format_metric_currency(sum(flt(row["item_group_amounts"].get(column["label"], 0.0)) for row in rows))
			for column in columns
		],
	}

	return rows, total_row, columns


def build_donut_from_grouped_rows(rows, label_fallback, colors=("blue", "green", "indigo", "orange", "slate")):
	color_values = {
		"blue": "#3777f7",
		"green": "#48b892",
		"indigo": "#6d719f",
		"orange": "#ffaf1f",
		"slate": "#8ea0ba",
		"purple": "#825eea",
	}

	top_rows = [
		((row.get("label") or "").strip() or label_fallback, flt(row.get("amount")))
		for row in rows
		if flt(row.get("amount")) > 0
	][:5]

	total_amount = sum(amount for _label, amount in top_rows)
	if not top_rows:
		return [], "background: conic-gradient(#e5e7eb 0 100%);", "No sales data for the selected date range."

	segments = []
	list_rows = []
	current_percent = 0.0

	for index, (label, amount) in enumerate(top_rows):
		color_class = colors[index % len(colors)]
		percent = (amount / total_amount * 100) if total_amount else 0
		next_percent = current_percent + percent
		segments.append(f"{color_values[color_class]} {current_percent:.2f}% {next_percent:.2f}%")
		list_rows.append(
			{
				"class": color_class,
				"label": label,
				"value": f"{format_metric_currency(amount)} ({percent:.1f}%)",
			}
		)
		current_percent = next_percent

	return list_rows, f"background: conic-gradient({', '.join(segments)});", ""


def mark_over_limit_rows(rows, limit=DEFAULT_VISIBLE_LIMIT):
	annotated_rows = []
	for index, row in enumerate(rows or [], start=1):
		annotated_row = dict(row)
		annotated_row["is_over_limit"] = index > int(limit)
		annotated_rows.append(annotated_row)
	return annotated_rows, len(annotated_rows) > int(limit)


def build_sales_ai_prompt(context, from_date=None, to_date=None):
	date_range = f"From {from_date} to {to_date}" if from_date or to_date else "Current dashboard range"
	lines = [
		"You are analyzing a hospital sales dashboard for commercial and clinical leadership.",
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
	lines.append("Sales channels:")
	for item in (context.get("expense_categories") or [])[:5]:
		lines.append(f"- {item.get('label')}: {item.get('value')}")

	lines.append("")
	lines.append("Admission / service mix:")
	for item in (context.get("income_sources") or [])[:5]:
		lines.append(f"- {item.get('label')}: {item.get('value')}")

	lines.append("")
	lines.append(f"Doctor sales total: {context.get('account_balances_total') or '$ 0'}")
	lines.append(f"Department sales total: {(context.get('unpaid_invoices_total') or {}).get('outstanding') or '$ 0'}")
	lines.append(f"Admission sales total: {context.get('top_supplier_balances_total') or '$ 0'}")

	lines.append("")
	lines.append("Top doctors by revenue:")
	for item in (context.get("unpaid_invoices") or [])[:5]:
		lines.append(f"- {item.get('doctor')}: {item.get('net_sales') or item.get('outstanding')}")

	lines.append("")
	lines.append("Top admission segments:")
	for item in (context.get("top_supplier_balances") or [])[:5]:
		lines.append(f"- {item.get('supplier')}: {item.get('balance')}")

	item_group_total = context.get("budget_variance_total") or {}
	lines.append("")
	lines.append("Item group summary:")
	lines.append(
		f"- Invoices {item_group_total.get('budget')}, Qty {item_group_total.get('actual')}, Revenue {item_group_total.get('variance')}, Mix {item_group_total.get('utilization')}"
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
		for prefix in icon_map:
			tag = f"{prefix}:"
			if line.lower().startswith(tag):
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


def build_metric_trend(current_value, previous_value, suffix=""):
	current_value = flt(current_value)
	previous_value = flt(previous_value)
	label_suffix = f" {suffix}" if suffix else ""

	if abs(previous_value) <= 0.005 and abs(current_value) <= 0.005:
		return {"trend": f"0.0%{label_suffix}", "trend_class": "trend-flat"}

	if abs(previous_value) <= 0.005:
		return {"trend": f"&uarr; 100.0%{label_suffix}", "trend_class": "trend-up"}

	change = ((current_value - previous_value) / abs(previous_value)) * 100

	if change > 0.005:
		return {"trend": f"&uarr; {abs(change):.1f}%{label_suffix}", "trend_class": "trend-up"}

	if change < -0.005:
		return {"trend": f"&darr; {abs(change):.1f}%{label_suffix}", "trend_class": "trend-down"}

	return {"trend": f"&rarr; 0.0%{label_suffix}", "trend_class": "trend-flat"}


def get_mix_indicator(share):
	share = flt(share)
	if share >= 30:
		return {"label": "Core", "class": "good"}
	if share >= 15:
		return {"label": "Watch", "class": "warning"}
	if share > 0:
		return {"label": "Niche", "class": "neutral"}
	return {"label": "Idle", "class": "neutral"}


def get_variance_class(value):
	if flt(value) < -0.005:
		return "negative"
	if flt(value) > 0.005:
		return "positive"
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
		current_start = add_days(current_end, 1)

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


def format_metric_currency(value):
	return f"$ {flt(value):,.0f}"


def format_metric_number(value):
	return f"{flt(value):,.0f}"


def format_quantity(value):
	quantity = flt(value)
	if abs(quantity - int(quantity)) <= 0.005:
		return f"{int(quantity):,}"
	return f"{quantity:,.1f}"


def normalize_admission_type(value):
	admission_type = (value or "").strip() or "OPD"
	if admission_type.upper() in ("NOT INPATIENT", "NONE", "NULL"):
		return "OPD"
	return admission_type


def scrub_ipd_type_label(label):
	return "".join(char.lower() if char.isalnum() else "_" for char in cstr(label or "")).strip("_") or "ipd_type"


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


def is_full_month_range(from_date, to_date):
	from_date = getdate(from_date)
	to_date = getdate(to_date)
	return from_date == get_first_day(from_date) and to_date == get_last_day(from_date)


def get_display_date_range(from_date, to_date):
	return f"{formatdate(from_date, 'MMM d')} &ndash; {formatdate(to_date, 'MMM d, yyyy')}"


def get_display_comparison_range(from_date, to_date):
	previous_from_date, previous_to_date = get_previous_period_dates(getdate(from_date), getdate(to_date))
	return f"{formatdate(previous_from_date, 'MMM d')} &ndash; {formatdate(previous_to_date, 'MMM d')}"


def get_dashboard_cache_key(from_date, to_date):
	return f"sales_dashboard:v2:{frappe.local.site}:{from_date}:{to_date}"


def get_cached_value(key):
	try:
		return frappe.cache().get_value(key)
	except Exception:
		return None


def set_cached_value(key, value, expires_in_sec=300):
	try:
		frappe.cache().set_value(key, value, expires_in_sec=expires_in_sec)
	except Exception:
		pass


def get_sales_invoice_sql_context():
	return frappe._dict(
		amount_field="base_net_total",
		paid_field="base_paid_amount",
		outstanding_field="outstanding_amount",
		discount_field="base_discount_amount",
		sales_channel_expr=(
			"CASE WHEN LOWER(TRIM(IFNULL(si.so_type, ''))) = 'pharmacy' "
			"THEN 'Pharmacy' ELSE 'Hospital' END"
		),
		patient_expr="si.patient",
		patient_name_expr="si.patient_name",
		inpatient_join="LEFT JOIN `tabInpatient Record` ip ON ip.name = si.inpatient_record",
		admission_type_expr=(
			"CASE WHEN IFNULL(si.inpatient_record, '') != '' "
			"THEN COALESCE(NULLIF(ip.type, ''), 'Not Inpatient') ELSE 'Not Inpatient' END"
		),
	)


def get_sales_item_sql_context():
	return frappe._dict(
		item_amount_field="base_net_amount",
		inpatient_join="LEFT JOIN `tabInpatient Record` ip ON ip.name = si.inpatient_record",
		admission_type_expr=(
			"CASE WHEN IFNULL(si.inpatient_record, '') != '' "
			"THEN COALESCE(NULLIF(ip.type, ''), 'Not Inpatient') ELSE 'Not Inpatient' END"
		),
	)

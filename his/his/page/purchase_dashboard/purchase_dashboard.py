import frappe
from frappe.utils import add_days, date_diff, flt, formatdate, get_first_day, get_last_day, getdate, nowdate
from erpnext.accounts.report.accounts_payable.accounts_payable import execute as run_accounts_payable_report


DEFAULT_VISIBLE_LIMIT = 10


@frappe.whitelist()
def get_dashboard_data(from_date=None, to_date=None):
	from_date, to_date = get_date_range(from_date, to_date)
	previous_from_date, previous_to_date = get_previous_period_dates(from_date, to_date)

	current_invoices = get_purchase_invoice_rows(from_date, to_date)
	previous_invoices = get_purchase_invoice_rows(previous_from_date, previous_to_date)
	current_receipts = get_purchase_receipt_rows(from_date, to_date)
	previous_receipts = get_purchase_receipt_rows(previous_from_date, previous_to_date)
	current_payments = get_purchase_payment_entry_rows(from_date, to_date)
	previous_payments = get_purchase_payment_entry_rows(previous_from_date, previous_to_date)
	current_payables = get_accounts_payable_total(to_date)
	previous_payables = get_accounts_payable_total(previous_to_date)
	current_supplier_balances = get_accounts_payable_rows(to_date)
	current_items = get_purchase_item_rows(from_date, to_date)
	previous_items = get_purchase_item_rows(previous_from_date, previous_to_date)
	current_receipt_items = get_purchase_receipt_item_rows(from_date, to_date)
	supplier_rows = get_supplier_purchase_rows(current_invoices, current_payments, current_supplier_balances, limit=100)
	supplier_rows, supplier_rows_has_more = mark_over_limit_rows(supplier_rows)

	cost_center_rows, expense_donut_style, expense_empty_message = build_donut_data(
		current_invoices,
		"cost_center",
		value_key="net_purchase",
		label_fallback="Unassigned",
	)
	warehouse_rows, source_donut_style, income_empty_message = build_donut_data(
		current_receipt_items,
		"warehouse",
		value_key="net_amount",
		label_fallback="Unassigned",
		colors=("blue", "green", "orange", "purple", "indigo"),
	)
	purchase_anomalies, purchase_anomalies_total = get_purchase_anomaly_rows(
		current_invoices,
		previous_invoices,
		current_items,
		previous_items,
	)
	purchase_anomalies, purchase_anomalies_has_more = mark_over_limit_rows(purchase_anomalies)

	return {
		"from_date": str(from_date),
		"to_date": str(to_date),
		"date_range": get_display_date_range(from_date, to_date),
		"comparison_range": get_display_comparison_range(from_date, to_date),
		"metrics": get_metrics(
			current_invoices,
			previous_invoices,
			current_receipts,
			previous_receipts,
			current_payments,
			previous_payments,
			current_payables,
			previous_payables,
		),
		"income_expenses": get_purchase_payment_chart_data(from_date, to_date, current_invoices, current_payments),
		"expense_categories": cost_center_rows,
		"expense_donut_style": expense_donut_style,
		"expense_empty_message": expense_empty_message,
		"income_sources": warehouse_rows,
		"source_donut_style": source_donut_style,
		"income_empty_message": income_empty_message,
		"account_balances": supplier_rows,
		"account_balances_has_more": supplier_rows_has_more,
		"unpaid_invoices": get_item_group_purchase_rows(current_items),
		"top_supplier_balances": get_warehouse_purchase_rows(current_items),
		"budget_variance": purchase_anomalies,
		"budget_variance_has_more": purchase_anomalies_has_more,
		"budget_variance_total": purchase_anomalies_total,
		"budget_variance_message": "" if purchase_anomalies else "No material purchase anomalies were detected for the selected date range.",
		"cash_flow": [],
		"insights": [],
	}


@frappe.whitelist(methods=["POST"])
def get_ai_insights(dashboard_context=None, from_date=None, to_date=None):
	try:
		context = frappe.parse_json(dashboard_context) if dashboard_context else {}
		if not isinstance(context, dict):
			context = {}

		from coreinsight_ai.api.chatbot import chat

		prompt = build_purchase_ai_prompt(context, from_date=from_date, to_date=to_date)
		result = chat(
			messages=[{"role": "user", "content": prompt}],
			options={"answer_style": "analysis", "temperature": 0.2},
		)
		content = (result or {}).get("content") or ""
		return {"insights": parse_ai_insight_response(content), "raw_content": content}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Purchase Dashboard AI Insight")
		return {
			"insights": [
				{
					"icon_class": "fa-info-circle",
					"text_class": "slate-text",
					"text": "Insights are not available right now. Please review the dashboard figures below.",
				}
			]
		}


def get_purchase_invoice_rows(from_date, to_date):
	purchase_invoice_columns = get_available_columns("Purchase Invoice")

	amount_field = first_available_column(
		purchase_invoice_columns,
		("total", "base_total", "base_net_total", "net_total", "base_grand_total", "grand_total"),
	)
	paid_field = first_available_column(purchase_invoice_columns, ("base_paid_amount", "paid_amount"))
	outstanding_field = first_available_column(purchase_invoice_columns, ("outstanding_amount",))
	discount_field = first_available_column(purchase_invoice_columns, ("base_discount_amount", "discount_amount"))
	department_field = "pi.medical_department" if "medical_department" in purchase_invoice_columns else "''"
	cost_center_field = "pi.cost_center" if "cost_center" in purchase_invoice_columns else "''"

	return frappe.db.sql(
		f"""
		SELECT
			pi.name,
			pi.posting_date,
			IFNULL(pi.is_return, 0) AS is_return,
			pi.supplier,
			COALESCE(NULLIF(pi.supplier_name, ''), pi.supplier) AS supplier_name,
			COALESCE(NULLIF(s.supplier_group, ''), 'Unassigned') AS supplier_group,
			COALESCE(NULLIF({cost_center_field}, ''), 'Unassigned') AS cost_center,
			COALESCE(NULLIF({department_field}, ''), 'Unassigned') AS department,
			IFNULL(pi.update_stock, 0) AS update_stock,
			CASE
				WHEN IFNULL(pi.is_return, 0) = 1 THEN -ABS(IFNULL(pi.{amount_field}, 0))
				ELSE ABS(IFNULL(pi.{amount_field}, 0))
			END AS net_purchase,
			CASE
				WHEN IFNULL(pi.is_return, 0) = 1 THEN 0
				ELSE ABS(IFNULL(pi.{discount_field}, 0))
			END AS discount_amount,
			CASE
				WHEN IFNULL(pi.is_return, 0) = 1 THEN -ABS(IFNULL(pi.{paid_field}, 0))
				ELSE ABS(IFNULL(pi.{paid_field}, 0))
			END AS payments,
			CASE
				WHEN IFNULL(pi.is_return, 0) = 1 THEN -ABS(IFNULL(pi.{outstanding_field}, 0))
				ELSE ABS(IFNULL(pi.{outstanding_field}, 0))
			END AS outstanding_amount
		FROM `tabPurchase Invoice` pi
		LEFT JOIN `tabSupplier` s ON s.name = pi.supplier
		WHERE
			pi.docstatus = 1
			AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY pi.posting_date ASC, pi.creation ASC
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)


def get_purchase_item_rows(from_date, to_date):
	purchase_invoice_columns = get_available_columns("Purchase Invoice")
	purchase_item_columns = get_available_columns("Purchase Invoice Item")

	item_amount_field = first_available_column(
		purchase_item_columns, ("base_net_amount", "base_amount", "net_amount", "amount")
	)
	item_department_field = "pii.medical_department" if "medical_department" in purchase_item_columns else "''"
	invoice_department_field = "pi.medical_department" if "medical_department" in purchase_invoice_columns else "''"

	return frappe.db.sql(
		f"""
		SELECT
			pii.parent,
			pi.posting_date,
			IFNULL(pi.is_return, 0) AS is_return,
			pi.supplier,
			COALESCE(NULLIF(pi.supplier_name, ''), pi.supplier) AS supplier_name,
			COALESCE(NULLIF(s.supplier_group, ''), 'Unassigned') AS supplier_group,
			COALESCE(NULLIF(pii.item_group, ''), 'Uncategorized') AS item_group,
			COALESCE(NULLIF(pii.warehouse, ''), 'Unassigned') AS warehouse,
			COALESCE(NULLIF({item_department_field}, ''), NULLIF({invoice_department_field}, ''), 'Unassigned') AS department,
			pii.item_code,
			pii.item_name,
			CASE
				WHEN IFNULL(pi.is_return, 0) = 1 THEN -ABS(IFNULL(pii.qty, 0))
				ELSE ABS(IFNULL(pii.qty, 0))
			END AS qty,
			CASE
				WHEN IFNULL(pi.is_return, 0) = 1 THEN -ABS(IFNULL(pii.{item_amount_field}, 0))
				ELSE ABS(IFNULL(pii.{item_amount_field}, 0))
			END AS net_amount
		FROM `tabPurchase Invoice Item` pii
		INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
		LEFT JOIN `tabSupplier` s ON s.name = pi.supplier
		WHERE
			pi.docstatus = 1
			AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY pi.posting_date ASC, pii.idx ASC
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)


def get_purchase_receipt_rows(from_date, to_date):
	purchase_receipt_columns = get_available_columns("Purchase Receipt")

	amount_field = first_available_column(
		purchase_receipt_columns,
		("total", "base_total", "base_net_total", "net_total", "base_grand_total", "grand_total"),
	)

	return frappe.db.sql(
		f"""
		SELECT
			pr.name,
			pr.posting_date,
			IFNULL(pr.is_return, 0) AS is_return,
			CASE
				WHEN IFNULL(pr.is_return, 0) = 1 THEN -ABS(IFNULL(pr.{amount_field}, 0))
				ELSE ABS(IFNULL(pr.{amount_field}, 0))
			END AS net_receipt
		FROM `tabPurchase Receipt` pr
		WHERE
			pr.docstatus = 1
			AND pr.posting_date BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY pr.posting_date ASC, pr.creation ASC
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)


def get_purchase_receipt_item_rows(from_date, to_date):
	purchase_receipt_item_columns = get_available_columns("Purchase Receipt Item")

	item_amount_field = first_available_column(
		purchase_receipt_item_columns, ("base_net_amount", "base_amount", "net_amount", "amount")
	)

	return frappe.db.sql(
		f"""
		SELECT
			pri.parent,
			pr.posting_date,
			IFNULL(pr.is_return, 0) AS is_return,
			COALESCE(NULLIF(pri.warehouse, ''), 'Unassigned') AS warehouse,
			CASE
				WHEN IFNULL(pr.is_return, 0) = 1 THEN -ABS(IFNULL(pri.{item_amount_field}, 0))
				ELSE ABS(IFNULL(pri.{item_amount_field}, 0))
			END AS net_amount
		FROM `tabPurchase Receipt Item` pri
		INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
		WHERE
			pr.docstatus = 1
			AND pr.posting_date BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY pr.posting_date ASC, pri.idx ASC
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)


def get_purchase_payment_entry_rows(from_date, to_date):
	payment_entry_columns = get_available_columns("Payment Entry")
	amount_field = first_available_column(
		payment_entry_columns,
		("base_paid_amount", "paid_amount", "base_received_amount", "received_amount"),
	)
	party_name_field = "pe.party_name" if "party_name" in payment_entry_columns else "pe.party"

	return frappe.db.sql(
		f"""
		SELECT
			pe.name,
			pe.posting_date,
			pe.party AS supplier,
			COALESCE(NULLIF({party_name_field}, ''), pe.party) AS supplier_name,
			ABS(IFNULL(pe.{amount_field}, 0)) AS payment_amount
		FROM `tabPayment Entry` pe
		WHERE
			pe.docstatus = 1
			AND pe.payment_type = 'Pay'
			AND pe.party_type = 'Supplier'
			AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY pe.posting_date ASC, pe.creation ASC
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)


def get_metrics(
	current_invoices,
	previous_invoices,
	current_receipts,
	previous_receipts,
	current_payment_entries,
	previous_payment_entries,
	current_payables,
	previous_payables,
):
	current_positive = [row for row in current_invoices if not cint(row.get("is_return"))]
	previous_positive = [row for row in previous_invoices if not cint(row.get("is_return"))]
	current_returns = [row for row in current_invoices if cint(row.get("is_return"))]
	previous_returns = [row for row in previous_invoices if cint(row.get("is_return"))]
	current_receipt_positive = [row for row in current_receipts if not cint(row.get("is_return"))]
	previous_receipt_positive = [row for row in previous_receipts if not cint(row.get("is_return"))]

	current_total_bills = sum(flt(row.get("net_purchase")) for row in current_positive)
	previous_total_bills = sum(flt(row.get("net_purchase")) for row in previous_positive)

	current_total_receipts = sum(flt(row.get("net_receipt")) for row in current_receipt_positive)
	previous_total_receipts = sum(flt(row.get("net_receipt")) for row in previous_receipt_positive)

	current_returns_total = sum(abs(flt(row.get("net_purchase"))) for row in current_returns)
	previous_returns_total = sum(abs(flt(row.get("net_purchase"))) for row in previous_returns)

	current_payments = sum(flt(row.get("payment_amount")) for row in current_payment_entries)
	previous_payments = sum(flt(row.get("payment_amount")) for row in previous_payment_entries)

	return [
		{
			"class": "income",
			"icon": '<i class="fa fa-shopping-basket"></i>',
			"label": "Total Bills",
			"value": format_metric_currency(current_total_bills),
			**build_metric_trend(current_total_bills, previous_total_bills),
		},
		{
			"class": "expense",
			"icon": '<i class="fa fa-truck"></i>',
			"label": "Total Receipt",
			"value": format_metric_currency(current_total_receipts),
			**build_metric_trend(current_total_receipts, previous_total_receipts),
		},
		{
			"class": "profit",
			"icon": '<i class="fa fa-undo"></i>',
			"label": "Return",
			"value": format_metric_currency(current_returns_total),
			**build_metric_trend(current_returns_total, previous_returns_total),
		},
		{
			"class": "cash",
			"icon": '<i class="fa fa-credit-card"></i>',
			"label": "Payments",
			"value": format_metric_currency(current_payments),
			**build_metric_trend(current_payments, previous_payments),
		},
		{
			"class": "bank",
			"icon": '<i class="fa fa-file-text-o"></i>',
			"label": "Payables",
			"value": format_metric_currency(current_payables),
			**build_metric_trend(current_payables, previous_payables),
		},
	]


def get_accounts_payable_total(report_date):
	data = get_accounts_payable_report_data(report_date)
	return sum(
		flt(row.get("outstanding"))
		for row in data
		if isinstance(row, dict) and not row.get("bold")
	)


def get_accounts_payable_rows(report_date):
	data = get_accounts_payable_report_data(report_date)
	rows = []
	for row in data:
		if not isinstance(row, dict) or row.get("bold"):
			continue

		supplier_id = (row.get("party") or row.get("supplier") or "").strip()
		supplier_name = (row.get("party_name") or row.get("supplier_name") or supplier_id).strip()
		if not supplier_id and not supplier_name:
			continue

		rows.append(
			{
				"supplier": supplier_id or supplier_name,
				"supplier_name": supplier_name or supplier_id,
				"outstanding_amount": flt(row.get("outstanding")),
			}
		)

	return rows


def get_accounts_payable_report_data(report_date):
	filters = {
		"report_date": getdate(report_date),
		"company": frappe.db.get_single_value("Global Defaults", "default_company"),
		"ageing_based_on": "Due Date",
		"range1": 30,
		"range2": 60,
		"range3": 90,
		"range4": 120,
		"based_on_payment_terms": 0,
		"show_future_payments": 0,
	}
	_columns, data, *_rest = run_accounts_payable_report(filters)
	return data or []


def get_purchase_payment_chart_data(from_date, to_date, invoices, payment_entries):
	buckets = build_chart_buckets(from_date, to_date, 6)
	for row in invoices:
		posting_date = row.get("posting_date")
		if not posting_date:
			continue

		bucket = get_bucket_for_date(buckets, getdate(posting_date))
		if not bucket:
			continue

		bucket["income"] += max(flt(row.get("net_purchase")), 0)

	for row in payment_entries:
		posting_date = row.get("posting_date")
		if not posting_date:
			continue

		bucket = get_bucket_for_date(buckets, getdate(posting_date))
		if not bucket:
			continue

		bucket["expense"] += max(flt(row.get("payment_amount")), 0)

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


def build_donut_data(rows, label_key, value_key, label_fallback, colors=("blue", "green", "indigo", "orange", "slate")):
	color_values = {
		"blue": "#3777f7",
		"green": "#48b892",
		"indigo": "#6d719f",
		"orange": "#ffaf1f",
		"slate": "#8ea0ba",
		"purple": "#825eea",
	}
	totals = {}
	for row in rows:
		amount = flt(row.get(value_key))
		if amount <= 0:
			continue
		label = (row.get(label_key) or "").strip() or label_fallback
		totals[label] = totals.get(label, 0) + amount

	top_rows = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:5]
	total_amount = sum(amount for _label, amount in top_rows)
	if not top_rows:
		return [], "background: conic-gradient(#e5e7eb 0 100%);", "No purchase data for the selected date range."

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


def get_supplier_purchase_rows(invoices, payment_entries, payable_rows, limit=10):
	grouped = {}
	payments_by_supplier = {}
	payables_by_supplier = {}
	for row in payment_entries or []:
		supplier = (row.get("supplier") or "").strip()
		if not supplier:
			continue
		payments_by_supplier[supplier] = payments_by_supplier.get(supplier, 0.0) + flt(row.get("payment_amount"))

	for row in payable_rows or []:
		supplier = (row.get("supplier") or "").strip()
		if not supplier:
			continue
		payables_by_supplier[supplier] = payables_by_supplier.get(supplier, 0.0) + flt(row.get("outstanding_amount"))

	for row in invoices:
		amount = flt(row.get("net_purchase"))
		if amount <= 0:
			continue
		supplier_id = (row.get("supplier") or "").strip()
		supplier = (row.get("supplier_name") or row.get("supplier") or "").strip() or "Unknown Supplier"
		supplier_group = (row.get("supplier_group") or "").strip() or "Unassigned"
		key = (supplier_id, supplier, supplier_group)
		grouped[key] = grouped.get(key, 0) + amount

	return [
		{
			"account": supplier,
			"type": supplier_group,
			"raw_balance": amount,
			"balance": format_metric_currency(amount),
			"raw_payment": payments_by_supplier.get(supplier_id, 0.0),
			"payment": format_metric_currency(payments_by_supplier.get(supplier_id, 0.0)),
			"raw_supplier_balance": payables_by_supplier.get(supplier_id, 0.0),
			"supplier_balance": format_metric_currency(payables_by_supplier.get(supplier_id, 0.0)),
		}
		for (supplier_id, supplier, supplier_group), amount in sorted(grouped.items(), key=lambda item: item[1], reverse=True)[: int(limit)]
	]


def get_item_group_purchase_rows(items, limit=10):
	grouped = {}
	for row in items:
		item_group = (row.get("item_group") or "").strip() or "Uncategorized"
		entry = grouped.setdefault(
			item_group,
			{"item_group": item_group, "raw_qty": 0.0, "raw_amount": 0.0},
		)
		entry["raw_qty"] += flt(row.get("qty"))
		entry["raw_amount"] += flt(row.get("net_amount"))

	rows = sorted(grouped.values(), key=lambda item: item["raw_amount"], reverse=True)[: int(limit)]
	for row in rows:
		row["qty"] = format_quantity(row["raw_qty"])
		row["amount"] = format_metric_currency(row["raw_amount"])
	return rows


def get_warehouse_purchase_rows(items, limit=10):
	grouped = {}
	for row in items:
		amount = flt(row.get("net_amount"))
		if amount <= 0:
			continue
		warehouse = (row.get("warehouse") or "").strip() or "Unassigned"
		entry = grouped.setdefault(
			warehouse,
			{"supplier": warehouse, "invoice_set": set(), "raw_balance": 0.0},
		)
		entry["invoice_set"].add(row.get("parent"))
		entry["raw_balance"] += amount

	rows = sorted(grouped.values(), key=lambda item: item["raw_balance"], reverse=True)[: int(limit)]
	return [
		{
			"supplier": row["supplier"],
			"supplier_group": len(row["invoice_set"]),
			"raw_balance": row["raw_balance"],
			"balance": format_metric_currency(row["raw_balance"]),
		}
		for row in rows
	]


def get_purchase_anomaly_rows(current_invoices, previous_invoices, current_items, previous_items, limit=12):
	anomalies = []

	append_item_price_spike_anomalies(anomalies, current_items, previous_items)

	rows = sorted(anomalies, key=lambda row: (flt(row.get("raw_severity")), flt(row.get("raw_current_value"))), reverse=True)[: int(limit)]
	for row in rows:
		row.pop("raw_severity", None)
		row.pop("raw_current_value", None)

	return rows, {"count": format_metric_number(len(rows))}


def append_item_price_spike_anomalies(anomalies, current_items, previous_items):
	current_by_item = build_item_rate_map(current_items)
	previous_by_item = build_item_rate_map(previous_items)

	for item_key, row in current_by_item.items():
		current_rate = flt(row.get("avg_rate"))
		current_amount = flt(row.get("amount"))
		previous_rate = flt(previous_by_item.get(item_key, {}).get("avg_rate"))
		if current_rate <= 0 or current_amount < 500 or previous_rate <= 0:
			continue

		change = ((current_rate - previous_rate) / previous_rate) * 100
		if change < 25:
			continue

		anomalies.append(
			{
				"anomaly_type": "Item Price Spike",
				"reference": row["item_code"],
				"subject": row["item_name"],
				"current_value": format_rate_currency(current_rate),
				"expected_value": format_rate_currency(previous_rate),
				"variance": format_percent(change),
				"variance_class": "positive",
				"reason": "Current average purchase rate is above the previous period average.",
				"raw_severity": change,
				"raw_current_value": current_amount,
			}
		)


def build_item_rate_map(items):
	grouped = {}
	for row in items or []:
		if cint(row.get("is_return")):
			continue
		qty = abs(flt(row.get("qty")))
		amount = max(flt(row.get("net_amount")), 0)
		if qty <= 0.005 or amount <= 0.005:
			continue
		item_code = (row.get("item_code") or "").strip() or "Unknown Item"
		entry = grouped.setdefault(
			item_code,
			{
				"item_code": item_code,
				"item_name": (row.get("item_name") or item_code).strip() or item_code,
				"qty": 0.0,
				"amount": 0.0,
			},
		)
		entry["qty"] += qty
		entry["amount"] += amount

	for row in grouped.values():
		row["avg_rate"] = (flt(row["amount"]) / flt(row["qty"])) if flt(row["qty"]) else 0.0

	return grouped


def build_purchase_ai_prompt(context, from_date=None, to_date=None):
	date_range = f"From {from_date} to {to_date}" if from_date or to_date else "Current dashboard range"
	lines = [
		"You are analyzing a hospital purchase dashboard for procurement and finance leadership.",
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
	lines.append("Top supplier groups:")
	for item in (context.get("expense_categories") or [])[:5]:
		lines.append(f"- {item.get('label')}: {item.get('value')}")

	lines.append("")
	lines.append("Top item groups:")
	for item in (context.get("income_sources") or [])[:5]:
		lines.append(f"- {item.get('label')}: {item.get('value')}")

	lines.append("")
	lines.append(f"Supplier spend total: {context.get('account_balances_total') or '$ 0'}")
	lines.append(f"Item group purchase total: {(context.get('unpaid_invoices_total') or {}).get('amount') or '$ 0'}")
	lines.append(f"Warehouse spend total: {context.get('top_supplier_balances_total') or '$ 0'}")

	lines.append("")
	lines.append("Top item groups by purchase:")
	for item in (context.get("unpaid_invoices") or [])[:5]:
		lines.append(f"- {item.get('item_group')}: {item.get('amount')}")

	lines.append("")
	lines.append("Top warehouses by spend:")
	for item in (context.get("top_supplier_balances") or [])[:5]:
		lines.append(f"- {item.get('supplier')}: {item.get('balance')}")

	anomaly_total = context.get("budget_variance_total") or {}
	lines.append("")
	lines.append(f"Detected purchase anomalies: {anomaly_total.get('count') or '0'}")

	lines.append("")
	lines.append("Top purchase anomalies:")
	for item in (context.get("budget_variance") or [])[:5]:
		lines.append(
			f"- {item.get('anomaly_type')}: {item.get('reference')} | {item.get('variance')} | {item.get('reason')}"
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


def format_rate_currency(value):
	return f"$ {flt(value):,.2f}/unit"


def format_percent(value):
	return f"{flt(value):,.1f}%"


def format_metric_number(value):
	return f"{flt(value):,.0f}"


def format_quantity(value):
	quantity = flt(value)
	if abs(quantity - int(quantity)) <= 0.005:
		return f"{int(quantity):,}"
	return f"{quantity:,.1f}"


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


def get_available_columns(doctype):
	try:
		return {column.get("fieldname") for column in frappe.get_meta(doctype).fields}
	except Exception:
		return set()


def first_available_column(columns, candidates):
	for candidate in candidates:
		if candidate in columns:
			return candidate
	return candidates[-1]


def cint(value):
	try:
		return int(value or 0)
	except Exception:
		return 0

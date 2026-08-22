import frappe
from frappe.utils import add_days, date_diff, flt, formatdate, get_first_day, get_last_day, getdate, nowdate

DEFAULT_VISIBLE_LIMIT = 100


@frappe.whitelist()
def get_dashboard_data(from_date=None, to_date=None):
	from_date, to_date = get_date_range(from_date, to_date)
	previous_from_date, previous_to_date = get_previous_period_dates(from_date, to_date)

	current_sle = get_stock_ledger_rows(from_date, to_date)
	previous_sle = get_stock_ledger_rows(previous_from_date, previous_to_date)
	current_bins = get_bin_rows()

	item_group_rows, expense_donut_style, expense_empty_message = build_donut_data(
		current_bins,
		"item_group",
		value_key="stock_value",
		label_fallback="Uncategorized",
	)
	warehouse_rows, source_donut_style, income_empty_message = build_donut_data(
		current_bins,
		"warehouse",
		value_key="stock_value",
		label_fallback="Unassigned",
		colors=("blue", "green", "orange", "purple", "indigo"),
	)
	stock_anomaly_rows, stock_anomaly_total = get_stock_anomaly_rows(current_bins, current_sle, limit=100)
	low_moving_rows, low_moving_total, low_moving_has_more = get_low_moving_high_balance_rows(current_bins, current_sle)
	stock_anomaly_rows, stock_anomaly_has_more = mark_over_limit_rows(stock_anomaly_rows)
	low_quantity_rows, low_quantity_total, store_balance_columns, low_quantity_has_more = get_fast_moving_drug_low_quantity_rows(
		current_bins,
		current_sle,
		from_date,
		to_date,
	)

	return {
		"from_date": str(from_date),
		"to_date": str(to_date),
		"date_range": get_display_date_range(from_date, to_date),
		"comparison_range": get_display_comparison_range(from_date, to_date),
		"metrics": get_metrics(current_bins, current_sle, previous_sle),
		"income_expenses": get_stock_movement_chart_data(from_date, to_date, current_sle),
		"expense_categories": item_group_rows,
		"expense_donut_style": expense_donut_style,
		"expense_empty_message": expense_empty_message,
		"income_sources": warehouse_rows,
		"source_donut_style": source_donut_style,
		"income_empty_message": income_empty_message,
		"account_balances": get_warehouse_stock_rows(current_bins),
		"unpaid_invoices": get_item_group_inventory_rows(current_bins),
		"low_moving_items": low_moving_rows,
		"low_moving_items_total": low_moving_total,
		"low_moving_items_has_more": low_moving_has_more,
		"top_supplier_balances": low_quantity_rows,
		"top_supplier_balances_total": low_quantity_total,
		"store_balance_columns": store_balance_columns,
		"top_supplier_balances_has_more": low_quantity_has_more,
		"budget_variance": stock_anomaly_rows,
		"budget_variance_has_more": stock_anomaly_has_more,
		"budget_variance_total": stock_anomaly_total,
		"budget_variance_message": "" if stock_anomaly_rows else "No stock anomalies detected for the selected date range.",
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

		prompt = build_stock_ai_prompt(context, from_date=from_date, to_date=to_date)
		result = chat(
			messages=[{"role": "user", "content": prompt}],
			options={"answer_style": "analysis", "temperature": 0.2},
		)
		content = (result or {}).get("content") or ""
		return {"insights": parse_ai_insight_response(content), "raw_content": content}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Stock Dashboard AI Insight")
		return {
			"insights": [
				{
					"icon_class": "fa-info-circle",
					"text_class": "slate-text",
					"text": "Insights are not available right now. Please review the dashboard figures below.",
				}
			]
		}


def get_bin_rows():
	return frappe.db.sql(
		"""
		SELECT
			b.warehouse,
			COALESCE(NULLIF(w.warehouse_type, ''), 'General') AS warehouse_type,
			b.item_code,
			COALESCE(NULLIF(i.item_name, ''), b.item_code) AS item_name,
			COALESCE(NULLIF(i.item_group, ''), 'Uncategorized') AS item_group,
			IFNULL(i.safety_stock, 0) AS safety_stock,
			IFNULL(b.actual_qty, 0) AS actual_qty,
			IFNULL(b.projected_qty, 0) AS projected_qty,
			IFNULL(b.valuation_rate, 0) AS valuation_rate,
			IFNULL(b.stock_value, 0) AS stock_value
		FROM `tabBin` b
		LEFT JOIN `tabItem` i ON i.item_code = b.item_code
		LEFT JOIN `tabWarehouse` w ON w.name = b.warehouse
		WHERE
			IFNULL(i.is_stock_item, 1) = 1
			AND IFNULL(i.disabled, 0) = 0
		""",
		as_dict=True,
	)


def get_stock_ledger_rows(from_date, to_date):
	return frappe.db.sql(
		"""
		SELECT
			sle.posting_date,
			sle.voucher_type,
			sle.voucher_no,
			sle.warehouse,
			COALESCE(NULLIF(w.warehouse_type, ''), 'General') AS warehouse_type,
			sle.item_code,
			COALESCE(NULLIF(i.item_name, ''), sle.item_code) AS item_name,
			COALESCE(NULLIF(i.item_group, ''), 'Uncategorized') AS item_group,
			IFNULL(sle.actual_qty, 0) AS actual_qty,
			IFNULL(sle.stock_value_difference, 0) AS stock_value_difference
		FROM `tabStock Ledger Entry` sle
		LEFT JOIN `tabItem` i ON i.item_code = sle.item_code
		LEFT JOIN `tabWarehouse` w ON w.name = sle.warehouse
		WHERE
			IFNULL(sle.is_cancelled, 0) = 0
			AND sle.posting_date BETWEEN %(from_date)s AND %(to_date)s
		ORDER BY sle.posting_date ASC, sle.creation ASC
		""",
		{"from_date": from_date, "to_date": to_date},
		as_dict=True,
	)


def get_near_expiry_count(report_date, within_days=30):
	result = frappe.db.sql(
		"""
		SELECT COUNT(*) AS near_expiry_count
		FROM `tabBatch` b
		LEFT JOIN `tabItem` i ON i.item_code = b.item
		WHERE
			IFNULL(b.disabled, 0) = 0
			AND IFNULL(b.batch_qty, 0) > 0
			AND b.expiry_date IS NOT NULL
			AND b.expiry_date BETWEEN %(from_date)s AND %(to_date)s
			AND IFNULL(i.disabled, 0) = 0
		""",
		{"from_date": report_date, "to_date": add_days(report_date, within_days)},
		as_dict=True,
	)
	return flt((result or [{}])[0].get("near_expiry_count"))


def get_metrics(current_bins, current_sle, previous_sle):
	current_stock_value = sum(max(flt(row.get("stock_value")), 0) for row in current_bins)
	current_period_value_change = sum(flt(row.get("stock_value_difference")) for row in current_sle)
	previous_stock_value = current_stock_value - current_period_value_change

	current_stock_received = get_stock_received_value(current_sle)
	previous_stock_received = get_stock_received_value(previous_sle)

	current_stock_issued = get_stock_issued_value(current_sle)
	previous_stock_issued = get_stock_issued_value(previous_sle)

	current_stock_adjustment = get_stock_adjustment_value(current_sle)
	previous_stock_adjustment = get_stock_adjustment_value(previous_sle)

	current_low_stock_items = get_low_stock_item_count(current_bins)

	return [
		{
			"class": "income",
			"icon": '<i class="fa fa-cubes"></i>',
			"label": "Total Stock Value",
			"value": format_metric_currency(current_stock_value),
			**build_metric_trend(current_stock_value, previous_stock_value),
		},
		{
			"class": "expense",
			"icon": '<i class="fa fa-arrow-down"></i>',
			"label": "Stock Received",
			"value": format_metric_currency(current_stock_received),
			**build_metric_trend(current_stock_received, previous_stock_received),
		},
		{
			"class": "profit",
			"icon": '<i class="fa fa-arrow-up"></i>',
			"label": "Stock Issued",
			"value": format_metric_currency(current_stock_issued),
			**build_metric_trend(current_stock_issued, previous_stock_issued),
		},
		{
			"class": "cash",
			"icon": '<i class="fa fa-sliders"></i>',
			"label": "Stock Adjustment",
			"value": format_metric_currency(current_stock_adjustment),
			**build_metric_trend(current_stock_adjustment, previous_stock_adjustment),
		},
		{
			"class": "bank",
			"icon": '<i class="fa fa-warning"></i>',
			"label": "Items Low in Stock",
			"value": format_metric_number(current_low_stock_items),
			**build_metric_trend(current_low_stock_items, current_low_stock_items),
		},
	]


def get_stock_received_value(sle_rows):
	return sum(
		max(flt(row.get("stock_value_difference")), 0)
		for row in sle_rows
		if (row.get("voucher_type") or "") != "Stock Reconciliation" and flt(row.get("actual_qty")) > 0
	)


def get_stock_issued_value(sle_rows):
	return sum(
		abs(min(flt(row.get("stock_value_difference")), 0))
		for row in sle_rows
		if (row.get("voucher_type") or "") != "Stock Reconciliation" and flt(row.get("actual_qty")) < 0
	)


def get_stock_adjustment_value(sle_rows):
	return sum(
		abs(flt(row.get("stock_value_difference")))
		for row in sle_rows
		if (row.get("voucher_type") or "") == "Stock Reconciliation"
	)


def get_low_stock_item_count(bins):
	return sum(
		1
		for row in bins
		if flt(row.get("safety_stock")) > 0 and flt(row.get("actual_qty")) < flt(row.get("safety_stock"))
	)


def get_stock_movement_chart_data(from_date, to_date, sle_rows):
	buckets = build_chart_buckets(from_date, to_date, 6)
	for row in sle_rows:
		posting_date = row.get("posting_date")
		if not posting_date:
			continue

		bucket = get_bucket_for_date(buckets, getdate(posting_date))
		if not bucket:
			continue

		qty = flt(row.get("actual_qty"))
		if qty >= 0:
			bucket["income"] += qty
		else:
			bucket["expense"] += abs(qty)

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
		return [], "background: conic-gradient(#e5e7eb 0 100%);", "No stock data for the selected range."

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


def get_warehouse_stock_rows(bins, limit=10):
	grouped = {}
	for row in bins:
		stock_value = flt(row.get("stock_value"))
		if stock_value <= 0:
			continue
		warehouse = (row.get("warehouse") or "").strip() or "Unassigned"
		warehouse_type = (row.get("warehouse_type") or "").strip() or "General"
		key = (warehouse, warehouse_type)
		grouped[key] = grouped.get(key, 0) + stock_value

	return [
		{
			"account": warehouse,
			"type": warehouse_type,
			"raw_balance": amount,
			"balance": format_metric_currency(amount),
		}
		for (warehouse, warehouse_type), amount in sorted(grouped.items(), key=lambda item: item[1], reverse=True)[: int(limit)]
	]


def get_item_group_inventory_rows(bins, limit=10):
	grouped = {}
	for row in bins:
		stock_value = flt(row.get("stock_value"))
		if stock_value <= 0:
			continue
		item_group = (row.get("item_group") or "").strip() or "Uncategorized"
		entry = grouped.setdefault(
			item_group,
			{"customer_group": item_group, "sku_set": set(), "raw_outstanding": 0.0},
		)
		entry["sku_set"].add(row.get("item_code"))
		entry["raw_outstanding"] += stock_value

	rows = sorted(grouped.values(), key=lambda item: item["raw_outstanding"], reverse=True)[: int(limit)]
	for row in rows:
		row["raw_customer_count"] = len(row["sku_set"])
		row["customer_count"] = len(row["sku_set"])
		row["outstanding"] = format_metric_currency(row["raw_outstanding"])
		row.pop("sku_set", None)
	return rows


def get_low_stock_rows(bins, limit=10):
	rows = []
	for row in bins:
		safety_stock = flt(row.get("safety_stock"))
		actual_qty = flt(row.get("actual_qty"))
		if safety_stock <= 0 or actual_qty >= safety_stock:
			continue

		shortfall_qty = max(safety_stock - actual_qty, 0)
		shortfall_value = shortfall_qty * max(flt(row.get("valuation_rate")), 0)
		rows.append(
			{
				"supplier": row.get("item_name") or row.get("item_code") or "Unknown Item",
				"supplier_group": row.get("warehouse") or "Unassigned",
				"raw_balance": shortfall_value,
				"balance": format_metric_currency(shortfall_value),
			}
		)

	return sorted(rows, key=lambda item: item["raw_balance"], reverse=True)[: int(limit)]


def get_low_moving_high_balance_rows(bins, sle_rows, limit=10, max_sell_through=25.0):
	stock_by_item = {}
	for row in bins:
		if (row.get("item_group") or "").strip().lower() != "drug":
			continue
		item_code = (row.get("item_code") or "").strip()
		if not item_code:
			continue
		entry = stock_by_item.setdefault(
			item_code,
			{
				"item_name": row.get("item_name") or item_code or "Unknown Item",
				"total_qty": 0.0,
				"total_value": 0.0,
			},
		)
		entry["total_qty"] += flt(row.get("actual_qty"))
		entry["total_value"] += flt(row.get("stock_value"))

	sold_by_item = {}
	for row in sle_rows:
		item_code = (row.get("item_code") or "").strip()
		issued_qty = abs(min(flt(row.get("actual_qty")), 0))
		if item_code and issued_qty > 0.005:
			sold_by_item[item_code] = sold_by_item.get(item_code, 0.0) + issued_qty

	rows = []
	for item_code, stock_entry in stock_by_item.items():
		total_qty = stock_entry["total_qty"]
		if total_qty <= 0.005:
			continue
		total_sold = sold_by_item.get(item_code, 0.0)
		sell_through = total_sold / total_qty * 100
		if sell_through > max_sell_through:
			continue
		rows.append(
			{
				"item": stock_entry["item_name"],
				"total_qty": format_quantity(total_qty),
				"total_sold": format_quantity(total_sold),
				"item_value": format_metric_currency(stock_entry["total_value"]),
				"sell_through": f"{sell_through:.1f}%",
				"raw_total_qty": total_qty,
			}
		)

	rows = sorted(rows, key=lambda item: item["raw_total_qty"], reverse=True)
	rows, has_more = mark_over_limit_rows(rows, limit)
	return rows, format_metric_number(len(rows)), has_more


def get_fast_moving_drug_low_quantity_rows(bins, sle_rows, from_date, to_date, limit=10):
	weeks = max((date_diff(to_date, from_date) + 1) / 7.0, 1.0)
	current_qty_by_key = {}
	store_qty_by_item = {}

	for row in bins:
		item_code = (row.get("item_code") or "").strip()
		warehouse = (row.get("warehouse") or "").strip() or "Unassigned"
		if item_code:
			store_quantities = store_qty_by_item.setdefault(item_code, {})
			store_quantities[warehouse] = store_quantities.get(warehouse, 0.0) + flt(row.get("actual_qty"))

		if not is_pharmacy_warehouse(row.get("warehouse")):
			continue

		key = (
			item_code,
			warehouse,
		)
		entry = current_qty_by_key.setdefault(
			key,
			{
				"item_code": row.get("item_code"),
				"item_name": row.get("item_name") or row.get("item_code") or "Unknown Item",
				"warehouse": row.get("warehouse") or "Unassigned",
				"actual_qty": 0.0,
			},
		)
		entry["actual_qty"] += flt(row.get("actual_qty"))

	issued_qty_by_key = {}
	for row in sle_rows:
		if not is_pharmacy_warehouse(row.get("warehouse")):
			continue

		issued_qty = abs(min(flt(row.get("actual_qty")), 0))
		if issued_qty <= 0.005:
			continue

		key = (
			(row.get("item_code") or "").strip(),
			(row.get("warehouse") or "").strip() or "Unassigned",
		)
		entry = issued_qty_by_key.setdefault(
			key,
			{
				"item_name": row.get("item_name") or row.get("item_code") or "Unknown Item",
				"warehouse": row.get("warehouse") or "Unassigned",
				"issued_qty": 0.0,
			},
		)
		entry["issued_qty"] += issued_qty

	rows = []
	for key, issued_entry in issued_qty_by_key.items():
		current_entry = current_qty_by_key.get(key)
		if not current_entry:
			continue

		weekly_avg_sold = issued_entry["issued_qty"] / weeks
		actual_qty = current_entry["actual_qty"]
		if weekly_avg_sold <= 0.005 or actual_qty >= weekly_avg_sold:
			continue

		gap_qty = weekly_avg_sold - actual_qty
		rows.append(
			{
				"supplier": current_entry["item_name"],
				"supplier_group": current_entry["warehouse"],
				"total_qty": format_quantity(sum(store_qty_by_item.get(key[0], {}).values())),
				"store_quantities": {
					warehouse: format_quantity(quantity)
					for warehouse, quantity in store_qty_by_item.get(key[0], {}).items()
					if warehouse == current_entry["warehouse"] or abs(flt(quantity)) > 0.005
				},
				"total_sold": format_quantity(issued_entry["issued_qty"]),
				"raw_balance": gap_qty,
				"balance": format_quantity(gap_qty),
			}
		)

	rows = sorted(rows, key=lambda item: item["raw_balance"], reverse=True)
	rows, has_more = mark_over_limit_rows(rows, limit)
	store_balance_columns = sorted({
		warehouse
		for row in rows
		for warehouse in row["store_quantities"]
	})
	for row in rows:
		row["store_balance_values"] = [row["store_quantities"].get(warehouse, "—") for warehouse in store_balance_columns]
		row.pop("store_quantities", None)
	return rows, format_metric_number(len(rows)), store_balance_columns, has_more


def get_fast_moving_rows(sle_rows, limit=10):
	grouped = {}
	for row in sle_rows:
		qty = abs(flt(row.get("actual_qty")))
		value = abs(flt(row.get("stock_value_difference")))
		if qty <= 0.005 and value <= 0.005:
			continue

		item_label = (row.get("item_name") or row.get("item_code") or "").strip() or "Unknown Item"
		entry = grouped.setdefault(
			item_label,
			{"category": item_label, "transaction_count": 0, "qty": 0.0, "movement_value": 0.0},
		)
		entry["transaction_count"] += 1
		entry["qty"] += qty
		entry["movement_value"] += value

	sorted_rows = sorted(grouped.values(), key=lambda item: item["movement_value"], reverse=True)[: int(limit)]
	total_value = sum(flt(row["movement_value"]) for row in sorted_rows)
	total_transactions = sum(int(row["transaction_count"]) for row in sorted_rows)
	total_qty = sum(flt(row["qty"]) for row in sorted_rows)

	formatted_rows = []
	for row in sorted_rows:
		movement_value = flt(row["movement_value"])
		share = (movement_value / total_value * 100) if total_value else 0
		indicator = get_mix_indicator(share)
		formatted_rows.append(
			{
				"category": row["category"],
				"budget": format_metric_number(row["transaction_count"]),
				"actual": format_quantity(row["qty"]),
				"variance": format_metric_currency(movement_value),
				"variance_class": get_variance_class(movement_value),
				"indicator_label": indicator["label"],
				"indicator_class": indicator["class"],
				"utilization": f"{share:.1f}%",
			}
		)

	total_share = "100.0%" if total_value else "0.0%"
	total_indicator = get_mix_indicator(100 if total_value else 0)
	return formatted_rows, {
		"budget": format_metric_number(total_transactions),
		"actual": format_quantity(total_qty),
		"variance": format_metric_currency(total_value),
		"variance_class": get_variance_class(total_value),
		"indicator_label": total_indicator["label"],
		"indicator_class": total_indicator["class"],
		"utilization": total_share,
	}


def get_stock_anomaly_rows(bins, sle_rows, limit=10):
	current_qty_by_item = {}
	rows = []

	for row in bins:
		item_code = (row.get("item_code") or "").strip()
		item_name = (row.get("item_name") or item_code or "").strip() or "Unknown Item"
		actual_qty = flt(row.get("actual_qty"))
		valuation_rate = max(flt(row.get("valuation_rate")), 0)
		safety_stock = flt(row.get("safety_stock"))

		current_qty_by_item[item_code] = current_qty_by_item.get(item_code, 0.0) + actual_qty

		if actual_qty < -0.005:
			rows.append(
				{
					"category": item_name,
					"anomaly": "Negative Stock",
					"actual": format_quantity(actual_qty),
					"variance": f"Below zero by {format_quantity(abs(actual_qty))}",
					"raw_severity": abs(actual_qty) * max(valuation_rate, 1),
				}
			)
			continue

		if safety_stock > 0 and actual_qty < safety_stock:
			shortfall = safety_stock - actual_qty
			rows.append(
				{
					"category": item_name,
					"anomaly": "Below Safety Stock",
					"actual": format_quantity(actual_qty),
					"variance": f"Short by {format_quantity(shortfall)}",
					"raw_severity": shortfall * max(valuation_rate, 1),
				}
			)

	adjustment_by_item = {}
	for row in sle_rows:
		if (row.get("voucher_type") or "").strip() != "Stock Reconciliation":
			continue

		item_code = (row.get("item_code") or "").strip()
		item_name = (row.get("item_name") or item_code or "").strip() or "Unknown Item"
		adjustment_value = abs(flt(row.get("stock_value_difference")))
		adjustment_qty = abs(flt(row.get("actual_qty")))
		if adjustment_value <= 0.005 and adjustment_qty <= 0.005:
			continue

		entry = adjustment_by_item.setdefault(
			item_code,
			{
				"item_name": item_name,
				"qty": 0.0,
				"value": 0.0,
				"count": 0,
			},
		)
		entry["qty"] += adjustment_qty
		entry["value"] += adjustment_value
		entry["count"] += 1

	for item_code, entry in adjustment_by_item.items():
		rows.append(
			{
				"category": entry["item_name"],
				"anomaly": "High Adjustment",
				"actual": format_quantity(current_qty_by_item.get(item_code, 0.0)),
				"variance": f"{entry['count']} rec, {format_metric_currency(entry['value'])}",
				"raw_severity": entry["value"],
			}
		)

	rows = sorted(rows, key=lambda item: item["raw_severity"], reverse=True)[: int(limit)]
	for row in rows:
		row.pop("raw_severity", None)
	return rows, {"count": format_metric_number(len(rows))}


def mark_over_limit_rows(rows, limit=DEFAULT_VISIBLE_LIMIT):
	annotated_rows = []
	for index, row in enumerate(rows or [], start=1):
		annotated_row = dict(row)
		annotated_row["is_over_limit"] = index > int(limit)
		annotated_rows.append(annotated_row)
	return annotated_rows, len(annotated_rows) > int(limit)


def is_pharmacy_warehouse(warehouse):
	return (warehouse or "").strip() == "Pharmacy - HH"


def build_stock_ai_prompt(context, from_date=None, to_date=None):
	date_range = f"From {from_date} to {to_date}" if from_date or to_date else "Current dashboard range"
	lines = [
		"You are analyzing a hospital stock dashboard for inventory and operations leadership.",
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
	lines.append("Top item groups by stock value:")
	for item in (context.get("expense_categories") or [])[:5]:
		lines.append(f"- {item.get('label')}: {item.get('value')}")

	lines.append("")
	lines.append("Top warehouses by stock value:")
	for item in (context.get("income_sources") or [])[:5]:
		lines.append(f"- {item.get('label')}: {item.get('value')}")

	lines.append("")
	lines.append(f"Warehouse stock total: {context.get('account_balances_total') or '$ 0'}")
	lines.append(f"Item group stock total: {(context.get('unpaid_invoices_total') or {}).get('outstanding') or '$ 0'}")
	lines.append(f"Fast moving drug low quantity count: {context.get('top_supplier_balances_total') or '0'}")

	lines.append("")
	lines.append("Top item groups:")
	for item in (context.get("unpaid_invoices") or [])[:5]:
		lines.append(f"- {item.get('customer_group')}: {item.get('outstanding')}")

	lines.append("")
	lines.append("Fast moving drug items below weekly average sold:")
	for item in (context.get("top_supplier_balances") or [])[:5]:
		lines.append(
			f"- {item.get('supplier')} ({item.get('supplier_group')}): Total Qty {item.get('total_qty')}, Total Sold {item.get('total_sold')}"
		)

	stock_anomaly_total = context.get("budget_variance_total") or {}
	lines.append("")
	lines.append("Stock anomaly summary:")
	lines.append(f"- {stock_anomaly_total.get('count') or '0'} anomalies flagged")

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


def cint(value):
	try:
		return int(value or 0)
	except Exception:
		return 0

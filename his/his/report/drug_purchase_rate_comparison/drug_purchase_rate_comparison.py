# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, cint, date_diff, flt, getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	set_default_filters(filters)
	data = get_data(filters)
	return get_columns(filters), data, None, get_chart(data), get_report_summary(data, filters)


def set_default_filters(filters):
	filters.company = get_default_company()

	if not filters.get("to_date"):
		filters.to_date = getdate()
	if not filters.get("from_date"):
		filters.from_date = add_days(filters.to_date, -29)

	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("Current From Date cannot be after Current To Date"))

	period_days = date_diff(filters.to_date, filters.from_date) + 1
	if not filters.get("previous_to_date"):
		filters.previous_to_date = add_days(filters.from_date, -1)
	if not filters.get("previous_from_date"):
		filters.previous_from_date = add_days(filters.previous_to_date, -(period_days - 1))

	if getdate(filters.previous_from_date) > getdate(filters.previous_to_date):
		frappe.throw(_("Previous From Date cannot be after Previous To Date"))


def get_default_company():
	if frappe.db.exists("Company", "Hodan Hospital"):
		return "Hodan Hospital"

	return frappe.defaults.get_global_default("company") or frappe.db.get_value("Company", {}, "name")


def get_columns(filters):
	before_label = _("Previous ({0} to {1})").format(filters.previous_from_date, filters.previous_to_date)
	after_label = _("Current ({0} to {1})").format(filters.from_date, filters.to_date)
	return [
		{"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 220},
		{"label": before_label, "fieldname": "before_rate", "fieldtype": "Currency", "options": "currency", "width": 190},
		{"label": after_label, "fieldname": "after_rate", "fieldtype": "Currency", "options": "currency", "width": 190},
		{"label": _("Qty"), "fieldname": "qty", "fieldtype": "Float", "width": 100},
		{"label": _("Saving"), "fieldname": "saving", "fieldtype": "Currency", "options": "currency", "width": 130},
		{"label": _("Cost Reduction %"), "fieldname": "reduction_percent", "fieldtype": "Percent", "width": 140},
	]


def get_data(filters):
	current = get_period_items(filters, filters.from_date, filters.to_date)
	previous = get_period_items(filters, filters.previous_from_date, filters.previous_to_date)
	rows = []

	for item_code, after in current.items():
		before = previous.get(item_code)
		if not before or flt(before["rate"] - after["rate"], 6) == 0 or after["qty"] <= 0:
			continue

		saving = (before["rate"] - after["rate"]) * after["qty"]
		rows.append({
			"item_code": item_code,
			"item_name": after["item_name"],
			"before_rate": before["rate"],
			"after_rate": after["rate"],
			"qty": after["qty"],
			"saving": saving,
			"reduction_percent": ((before["rate"] - after["rate"]) / before["rate"]) * 100,
			"currency": after["currency"],
		})

	rows.sort(key=lambda row: abs(row["saving"]), reverse=True)
	limit = cint(filters.get("top_n"))
	if limit > 0:
		rows = rows[:limit]

	return rows


def get_period_items(filters, from_date, to_date):
	conditions = ["pi.docstatus = 1", "pi.posting_date between %(from_date)s and %(to_date)s"]
	values = {"from_date": from_date, "to_date": to_date}

	for field in ("company", "supplier"):
		if filters.get(field):
			conditions.append(f"pi.{field} = %({field})s")
			values[field] = filters.get(field)
	if filters.get("item_group"):
		conditions.append("pii.item_group = %(item_group)s")
		values["item_group"] = filters.item_group
	if filters.get("item_code"):
		conditions.append("pii.item_code = %(item_code)s")
		values["item_code"] = filters.item_code

	rows = frappe.db.sql(
		f"""
			select
				pii.item_code, max(pii.item_name) as item_name,
				sum(abs(pii.stock_qty)) as qty,
				sum(abs(pii.base_net_amount)) as amount,
				max(pi.company) as company
			from `tabPurchase Invoice Item` pii
			inner join `tabPurchase Invoice` pi on pi.name = pii.parent
			where {' and '.join(conditions)}
				and pii.item_code is not null and pii.item_code != ''
				and pii.stock_qty != 0 and pi.is_return = 0
			group by pii.item_code
		""",
		values,
		as_dict=True,
	)

	result = {}
	for row in rows:
		qty = flt(row.qty)
		if qty <= 0:
			continue
		result[row.item_code] = {
			"item_name": row.item_name or row.item_code,
			"qty": qty,
			"rate": flt(row.amount) / qty,
			"currency": frappe.get_cached_value("Company", row.company, "default_currency"),
		}
	return result


def get_chart(data):
	if not data:
		return None
	return {
		"data": {
			"labels": [row["item_name"] for row in data],
			"datasets": [
				{"name": _("Current"), "values": [row["after_rate"] for row in data]},
				{"name": _("Previous"), "values": [row["before_rate"] for row in data]},
				{"name": _("Saving"), "values": [row["saving"] for row in data]},
			],
		},
		"type": "bar",
		"colors": ["#94a3b8", "#3b82f6", "#16a34a"],
	}


def get_report_summary(data, filters):
	currency = data[0]["currency"] if data else frappe.get_cached_value("Company", filters.company, "default_currency")
	return [
		{"label": _("Items Changed"), "value": len(data), "indicator": "Blue", "datatype": "Int"},
		{"label": _("Total Purchases"), "value": sum(row["qty"] for row in data), "indicator": "Blue", "datatype": "Float"},
		{"label": _("Total Savings"), "value": sum(row["saving"] for row in data), "indicator": "Green", "datatype": "Currency", "currency": currency},
		{"label": _("Previous Cost"), "value": sum(row["before_rate"] * row["qty"] for row in data), "indicator": "Blue", "datatype": "Currency", "currency": currency},
		{"label": _("Current Cost"), "value": sum(row["after_rate"] * row["qty"] for row in data), "indicator": "Blue", "datatype": "Currency", "currency": currency},
	]

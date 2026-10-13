# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	months = get_months(filters)
	raw = (
		get_raw_data(filters)
		+ get_journal_entry_data(filters)
		+ get_payment_entry_deduction_data(filters)
	)
	columns = get_columns(months)
	data = pivot_data(raw, months)
	chart = get_chart(raw, months)
	return columns, data, None, chart


def get_months(filters):
	# list of (month_key, label) from from_date to to_date
	start, end = getdate(filters.from_date), getdate(filters.to_date)
	multi_year = start.year != end.year
	months = []
	year, month = start.year, start.month
	while (year, month) <= (end.year, end.month):
		key = f"{year}-{month:02d}"
		label = getdate(f"{key}-01").strftime("%b %Y" if multi_year else "%b")
		months.append((key, label))
		if month == 12:
			year, month = year + 1, 1
		else:
			month += 1
	return months


def month_fieldname(month_key):
	return "m_" + month_key.replace("-", "_")


def get_columns(months):
	columns = [
		{
			"label": _("Type"),
			"fieldname": "type",
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"label": _("Service Line"),
			"fieldname": "service_line",
			"fieldtype": "Data",
			"width": 220,
		},
	]

	for key, label in months:
		columns.append(
			{
				"label": _(label),
				"fieldname": month_fieldname(key),
				"fieldtype": "Currency",
				"options": "currency",
				"width": 110,
			}
		)

	columns.append(
		{
			"label": _("Total"),
			"fieldname": "total",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		}
	)
	return columns


def get_conditions(filters):
	conditions = ["si.docstatus = 1", "si.posting_date BETWEEN %(from_date)s AND %(to_date)s"]
	if filters.get("company"):
		conditions.append("si.company = %(company)s")
	if filters.get("customer_group"):
		conditions.append("si.customer_group = %(customer_group)s")
	if filters.get("item_group"):
		conditions.append("sii.item_group = %(item_group)s")
	return " AND ".join(conditions)


def get_raw_data(filters):
	return frappe.db.sql(
		f"""
		SELECT
			DATE_FORMAT(si.posting_date, '%%Y-%%m') AS month_key,
			sii.item_group,
			si.customer_group,
			SUM(sii.base_net_amount) - SUM(
				CASE WHEN si.grand_total != 0
				THEN sii.base_net_amount * si.outstanding_amount / si.grand_total
				ELSE 0 END
			) AS cash_sales,
			SUM(
				CASE WHEN si.grand_total != 0
				THEN sii.base_net_amount * si.outstanding_amount / si.grand_total
				ELSE 0 END
			) AS credit_sales,
			SUM(sii.base_net_amount) AS total_sales
		FROM `tabSales Invoice Item` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE {get_conditions(filters)}
		GROUP BY month_key, sii.item_group, si.customer_group
		""",
		filters,
		as_dict=1,
	)


def get_income_account_map():
	# income account -> item group, from Item Group defaults (first wins for shared accounts)
	account_map = {}
	for item_group, account in frappe.db.sql(
		"""
		SELECT parent, income_account FROM `tabItem Default`
		WHERE parenttype = 'Item Group' AND ifnull(income_account, '') != ''
		ORDER BY parent
		"""
	):
		account_map.setdefault(account, item_group)
	return account_map


def get_journal_entry_data(filters):
	account_map = get_income_account_map()
	if not account_map:
		return []

	je_conditions = ["je.docstatus = 1", "je.posting_date BETWEEN %(from_date)s AND %(to_date)s"]
	if filters.get("company"):
		je_conditions.append("je.company = %(company)s")

	amounts = frappe.db.sql(
		f"""
		SELECT jea.parent AS journal_entry, jea.account,
			DATE_FORMAT(je.posting_date, '%%Y-%%m') AS month_key,
			SUM(jea.credit - jea.debit) AS amt
		FROM `tabJournal Entry Account` jea
		INNER JOIN `tabJournal Entry` je ON je.name = jea.parent
		INNER JOIN `tabAccount` a ON a.name = jea.account
		WHERE {" AND ".join(je_conditions)} AND a.root_type = 'Income'
		GROUP BY jea.parent, jea.account, month_key
		HAVING amt != 0
		""",
		filters,
		as_dict=1,
	)
	if not amounts:
		return []

	account_names = get_account_names([r.account for r in amounts])

	# per journal entry: paid into cash/bank? and the customer party if any
	je_names = list({r.journal_entry for r in amounts})
	je_meta = {
		m.name: m
		for m in frappe.db.sql(
			"""
			SELECT jea.parent AS name,
				MAX(CASE WHEN a.account_type IN ('Cash', 'Bank') AND jea.debit > 0 THEN 1 ELSE 0 END) AS is_cash,
				MAX(CASE WHEN jea.party_type = 'Customer' THEN jea.party ELSE NULL END) AS customer
			FROM `tabJournal Entry Account` jea
			INNER JOIN `tabAccount` a ON a.name = jea.account
			WHERE jea.parent IN %(je_names)s
			GROUP BY jea.parent
			""",
			{"je_names": je_names},
			as_dict=1,
		)
	}

	customers = [m.customer for m in je_meta.values() if m.customer]
	customer_groups = (
		dict(
			frappe.db.sql(
				"SELECT name, customer_group FROM `tabCustomer` WHERE name IN %(customers)s",
				{"customers": customers},
			)
		)
		if customers
		else {}
	)

	rows = []
	for r in amounts:
		# income accounts without an item group mapping (e.g. discount accounts)
		# still belong in the P&L, so show them under the account's own name as
		# one cash-section line that reconciles 1:1 with the P&L account - a
		# discount clears outstanding without money, and the invoice side counts
		# cleared outstanding as cash, so the deduction must land in cash too
		mapped_group = account_map.get(r.account)
		account_label = account_names.get(r.account, r.account)
		item_group = mapped_group or account_label
		if filters.get("item_group") and item_group != filters.item_group:
			continue

		meta = je_meta.get(r.journal_entry) or frappe._dict(is_cash=0, customer=None)
		is_cash = meta.is_cash if mapped_group else 1
		customer_group = (
			customer_groups.get(meta.customer) or _("Journal Entry") if mapped_group else account_label
		)
		if filters.get("customer_group") and customer_group != filters.customer_group:
			continue

		rows.append(
			frappe._dict(
				month_key=r.month_key,
				item_group=item_group,
				customer_group=customer_group,
				cash_sales=r.amt if is_cash else 0,
				credit_sales=0 if is_cash else r.amt,
				total_sales=r.amt,
			)
		)
	return rows


def get_account_names(accounts):
	if not accounts:
		return {}
	return dict(
		frappe.db.sql(
			"SELECT name, account_name FROM `tabAccount` WHERE name IN %(accounts)s",
			{"accounts": list(set(accounts))},
		)
	)


def get_payment_entry_deduction_data(filters):
	# discounts/write-offs booked on income accounts while collecting payments
	# (e.g. Patient Service Discounts) - the P&L includes them, so we must too
	if filters.get("item_group"):
		return []

	pe_conditions = ["pe.docstatus = 1", "pe.posting_date BETWEEN %(from_date)s AND %(to_date)s"]
	if filters.get("company"):
		pe_conditions.append("pe.company = %(company)s")

	rows = frappe.db.sql(
		f"""
		SELECT
			DATE_FORMAT(pe.posting_date, '%%Y-%%m') AS month_key,
			ped.account,
			pe.party_type,
			pe.party,
			MAX(CASE WHEN ifnull(acc_to.account_type, '') IN ('Cash', 'Bank')
				OR ifnull(acc_from.account_type, '') IN ('Cash', 'Bank') THEN 1 ELSE 0 END) AS is_cash,
			SUM(-ped.amount) AS amt
		FROM `tabPayment Entry Deduction` ped
		INNER JOIN `tabPayment Entry` pe ON pe.name = ped.parent
		INNER JOIN `tabAccount` a ON a.name = ped.account
		LEFT JOIN `tabAccount` acc_to ON acc_to.name = pe.paid_to
		LEFT JOIN `tabAccount` acc_from ON acc_from.name = pe.paid_from
		WHERE {" AND ".join(pe_conditions)} AND a.root_type = 'Income'
		GROUP BY month_key, ped.account, pe.party_type, pe.party
		HAVING amt != 0
		""",
		filters,
		as_dict=1,
	)
	if not rows:
		return []

	account_map = get_income_account_map()
	account_names = get_account_names([r.account for r in rows])
	customers = list({r.party for r in rows if r.party_type == "Customer" and r.party})
	customer_groups = (
		dict(
			frappe.db.sql(
				"SELECT name, customer_group FROM `tabCustomer` WHERE name IN %(customers)s",
				{"customers": customers},
			)
		)
		if customers
		else {}
	)

	data = []
	for r in rows:
		mapped_group = account_map.get(r.account)
		account_label = account_names.get(r.account, r.account)
		if mapped_group:
			customer_group = (
				customer_groups.get(r.party) if r.party_type == "Customer" else None
			) or _("Payment Entry")
		else:
			# unmapped accounts (e.g. discounts) go under the account's own name
			# as a single cash-section line that reconciles 1:1 with the P&L:
			# a deduction clears outstanding the invoice side counts as cash
			customer_group = account_label
		is_cash = r.is_cash if mapped_group else 1
		if filters.get("customer_group") and customer_group != filters.customer_group:
			continue

		data.append(
			frappe._dict(
				month_key=r.month_key,
				item_group=mapped_group or account_label,
				customer_group=customer_group,
				cash_sales=r.amt if is_cash else 0,
				credit_sales=0 if is_cash else r.amt,
				total_sales=r.amt,
			)
		)
	return data


def pivot_data(raw, months):
	month_keys = [key for key, _label in months]

	# cash broken down by item group, credit broken down by customer group
	cash_lines, credit_lines = {}, {}
	for r in raw:
		if r.month_key not in month_keys:
			continue
		if r.cash_sales:
			line = cash_lines.setdefault(r.item_group, dict.fromkeys(month_keys, 0))
			line[r.month_key] += r.cash_sales
		if r.credit_sales:
			line = credit_lines.setdefault(r.customer_group, dict.fromkeys(month_keys, 0))
			line[r.month_key] += r.credit_sales

	data = []
	section_headers = []
	for type_label, lines in ((_("Cash"), cash_lines), (_("Credit"), credit_lines)):
		header = frappe._dict(
			{"type": type_label, "service_line": "", "indent": 0, "bold": 1, "total": 0},
			**{month_fieldname(k): 0 for k in month_keys},
		)
		data.append(header)
		section_headers.append(header)

		for name in sorted(lines, key=lambda n: sum(lines[n].values()), reverse=True):
			row = frappe._dict({"type": "", "service_line": name, "indent": 1})
			row_total = 0
			for k in month_keys:
				amount = lines[name][k]
				row[month_fieldname(k)] = amount
				header[month_fieldname(k)] += amount
				row_total += amount
			row.total = row_total
			header.total += row_total
			data.append(row)

	data.append(frappe._dict({"type": "", "service_line": ""}))  # spacer before the summary
	cash_header, credit_header = section_headers
	for label, sources in (
		(_("Total Cash"), [cash_header]),
		(_("Total Credit"), [credit_header]),
		(_("Total Income"), [cash_header, credit_header]),
	):
		summary = frappe._dict({"type": label, "service_line": "", "indent": 0, "bold": 1, "total": 0})
		for k in month_keys:
			summary[month_fieldname(k)] = sum(s[month_fieldname(k)] for s in sources)
		summary.total = sum(s.total for s in sources)
		data.append(summary)

	return data


def get_chart(raw, months):
	if not raw:
		return None

	month_keys = [key for key, _label in months]
	cash = dict.fromkeys(month_keys, 0)
	credit = dict.fromkeys(month_keys, 0)
	for r in raw:
		if r.month_key in cash:
			cash[r.month_key] += r.cash_sales
			credit[r.month_key] += r.credit_sales

	return {
		"data": {
			"labels": [label for _key, label in months],
			"datasets": [
				{"name": _("Cash"), "values": [cash[k] for k in month_keys]},
				{"name": _("Credit"), "values": [credit[k] for k in month_keys]},
			],
		},
		"type": "bar",
		"colors": ["#29CD42", "#FF5858"],
	}

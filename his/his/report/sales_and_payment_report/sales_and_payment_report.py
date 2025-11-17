# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cstr


def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = (
		get_pos_sales_payment_data(filters)
		if filters.get("is_pos")
		else get_sales_payment_data(filters, columns)
	)
	return columns, data


def get_pos_columns():
	return [
		_("Date") + ":Date:80",
		_("Owner") + ":Data:200",
		_("Payment Mode") + ":Data:240",
		_("Sales and Returns") + ":Currency/currency:120",
		_("Taxes") + ":Currency/currency:120",
		_("Payments") + ":Currency/currency:120",
		_("Warehouse") + ":Data:200",
		_("Cost Center") + ":Data:200",
	]


def get_columns(filters):
	if filters.get("is_pos"):
		return get_pos_columns()
	else:
		return [
			_("Date") + ":Date:80",
			_("Owner") + ":Data:200",
			_("Payment Mode") + ":Data:240",
			_("Sales and Returns") + ":Currency/currency:120",
			_("Taxes") + ":Currency/currency:120",
			_("Today Collection") + ":Currency/currency:140",
			_("Previous Collection") + ":Currency/currency:140",
			_("Payments") + ":Currency/currency:120",  # unchanged logic
		]


def get_pos_sales_payment_data(filters):
	sales_invoice_data = get_pos_invoice_data(filters)
	data = [
		[
			row["posting_date"],
			row["owner"],
			row["mode_of_payment"],
			row["net_total"],
			row["total_taxes"],
			row["paid_amount"],
			row["warehouse"],
			row["cost_center"],
		]
		for row in sales_invoice_data
	]

	return data


# def get_sales_payment_data(filters, columns):
# 	data = []
# 	show_payment_detail = False

# 	sales_invoice_data = get_sales_invoice_data(filters)
# 	mode_of_payments = get_mode_of_payments(filters)
# 	mode_of_payment_details = get_mode_of_payment_details(filters)

# 	if filters.get("payment_detail"):
# 		show_payment_detail = True
# 	else:
# 		show_payment_detail = False

# 	for inv in sales_invoice_data:
# 		owner_posting_date = inv["owner"] + cstr(inv["posting_date"])
# 		if show_payment_detail:
# 			row = [inv.posting_date, inv.owner, " ", inv.net_total, inv.total_taxes, 0]
# 			data.append(row)
# 			for mop_detail in mode_of_payment_details.get(owner_posting_date, []):
# 				row = [inv.posting_date, inv.owner, mop_detail[0], 0, 0, mop_detail[1], 0]
# 				data.append(row)
# 		else:
# 			total_payment = 0
# 			for mop_detail in mode_of_payment_details.get(owner_posting_date, []):
# 				total_payment = total_payment + mop_detail[1]
# 			row = [
# 				inv.posting_date,
# 				inv.owner,
# 				", ".join(mode_of_payments.get(owner_posting_date, [])),
# 				inv.net_total,
# 				inv.total_taxes,
# 				total_payment,
# 			]
# 			data.append(row)
# 	unallocated = get_unallocated_total(filters)
# 	if unallocated and unallocated > 0:
# 		data.append([
# 			None,                      # Date
# 			_("Unallocated Payments"), # Owner (label)
# 			"",                        # Payment Mode
# 			0,                         # Sales and Returns
# 			0,                         # Taxes
# 			unallocated,               # Payments
# 		])
# 	return data

def get_sales_payment_data(filters, columns):
	data = []
	show_payment_detail = False

	sales_invoice_data = get_sales_invoice_data(filters)
	mode_of_payments = get_mode_of_payments(filters)
	mode_of_payment_details = get_mode_of_payment_details(filters)

	# NEW: Today vs Previous split
	split_prev_today = get_payment_split_prev_today(filters)

	if filters.get("payment_detail"):
		show_payment_detail = True
	else:
		show_payment_detail = False

	for inv in sales_invoice_data:
		owner_posting_date = inv["owner"] + cstr(inv["posting_date"])

		# NEW: lookup the split
		today_amt = split_prev_today.get(owner_posting_date, {}).get("today", 0) or 0
		prev_amt  = split_prev_today.get(owner_posting_date, {}).get("prev", 0) or 0

		if show_payment_detail:
			# header row; keep Payments shown as 0 in detail mode (your existing behavior)
			row = [inv.posting_date, inv.owner, " ",
			       inv.net_total, inv.total_taxes,
			       today_amt, prev_amt, 0]
			data.append(row)

			# detail rows (leave amounts zero here to keep logic minimal/unchanged)
			for mop_detail in mode_of_payment_details.get(owner_posting_date, []):
				row = [inv.posting_date, inv.owner, mop_detail[0],
				       0, 0,
				       0, 0, 0]
				data.append(row)
		else:
			# summary row; Payments stays as in your original logic
			total_payment = 0
			for mop_detail in mode_of_payment_details.get(owner_posting_date, []):
				total_payment += mop_detail[1]

			row = [
				inv.posting_date,
				inv.owner,
				", ".join(mode_of_payments.get(owner_posting_date, [])),
				inv.net_total,
				inv.total_taxes,
				today_amt,         # NEW
				prev_amt,          # NEW
				total_payment,     # Payments (unchanged)
			]
			data.append(row)

	# Unallocated row (8 columns now)
	unallocated = get_unallocated_total(filters)
	if unallocated and unallocated > 0:
		data.append([
			None,                        # Date
			_("Unallocated Payments"),   # Owner (label)
			"",                          # Payment Mode
			0,                           # Sales and Returns
			0,                           # Taxes
			0,                           # Today
			0,                           # Previous
			unallocated,                 # Payments
		])

	return data


def get_conditions(filters):
	conditions = "1=1"
	if filters.get("from_date"):
		conditions += " and a.posting_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " and a.posting_date <= %(to_date)s"
	if filters.get("company"):
		conditions += " and a.company=%(company)s"
	if filters.get("customer"):
		conditions += " and a.customer = %(customer)s"
	if filters.get("owner"):
		conditions += " and a.owner = %(owner)s"
	if filters.get("is_pos"):
		conditions += " and a.is_pos = %(is_pos)s"
	return conditions


def get_pos_invoice_data(filters):
	conditions = get_conditions(filters)
	result = frappe.db.sql(
		""
		"SELECT "
		'posting_date, owner, sum(net_total) as "net_total", sum(total_taxes) as "total_taxes", '
		'sum(paid_amount) as "paid_amount", sum(outstanding_amount) as "outstanding_amount", '
		"mode_of_payment, warehouse, cost_center "
		"FROM ("
		"SELECT "
		'parent, item_code, sum(amount) as "base_total", warehouse, cost_center '
		"from `tabSales Invoice Item`  group by parent"
		") t1 "
		"left join "
		"(select parent, mode_of_payment from `tabSales Invoice Payment` group by parent) t3 "
		"on (t3.parent = t1.parent) "
		"JOIN ("
		"SELECT "
		'docstatus, company, is_pos, name, posting_date, owner, sum(base_total) as "base_total", '
		'sum(net_total) as "net_total", sum(total_taxes_and_charges) as "total_taxes", '
		'sum(base_paid_amount) as "paid_amount", sum(outstanding_amount) as "outstanding_amount" '
		"FROM `tabSales Invoice` "
		"GROUP BY name"
		") a "
		"ON ("
		"t1.parent = a.name and t1.base_total = a.base_total) "
		"WHERE a.docstatus = 1"
		" AND {conditions} "
		"GROUP BY "
		"owner, posting_date, warehouse".format(conditions=conditions),
		filters,
		as_dict=1,
	)
	return result


def get_sales_invoice_data(filters):
	conditions = get_conditions(filters)
	return frappe.db.sql(
		"""
		select
			a.posting_date, a.owner,
			sum(a.net_total) as "net_total",
			sum(a.total_taxes_and_charges) as "total_taxes",
			sum(a.base_paid_amount) as "paid_amount",
			sum(a.outstanding_amount) as "outstanding_amount"
		from `tabSales Invoice` a
		where a.docstatus = 1
			and {conditions}
			group by
			a.owner, a.posting_date
	""".format(
			conditions=conditions
		),
		filters,
		as_dict=1,
	)


def get_mode_of_payments(filters):
	mode_of_payments = {}
	invoice_list = get_invoices(filters)
	invoice_list_names = ",".join("'" + invoice["name"] + "'" for invoice in invoice_list)
	if invoice_list:
		inv_mop = frappe.db.sql(
			"""select a.owner,a.posting_date, ifnull(b.mode_of_payment, '') as mode_of_payment
			from `tabSales Invoice` a, `tabSales Invoice Payment` b
			where a.name = b.parent
			and a.docstatus = 1
			and a.name in ({invoice_list_names})
			union
			select a.owner,a.posting_date, ifnull(b.mode_of_payment, '') as mode_of_payment
			from `tabSales Invoice` a, `tabPayment Entry` b,`tabPayment Entry Reference` c
			where a.name = c.reference_name
			and b.name = c.parent
			and b.docstatus = 1
			and a.name in ({invoice_list_names})
			union
			select a.owner, a.posting_date,
			ifnull(a.voucher_type,'') as mode_of_payment
			from `tabJournal Entry` a, `tabJournal Entry Account` b
			where a.name = b.parent
			and a.docstatus = 1
			and b.reference_type = 'Sales Invoice'
			and b.reference_name in ({invoice_list_names})
			""".format(
				invoice_list_names=invoice_list_names
			),
			as_dict=1,
		)
		for d in inv_mop:
			mode_of_payments.setdefault(d["owner"] + cstr(d["posting_date"]), []).append(d.mode_of_payment)
	return mode_of_payments


def get_invoices(filters):
	conditions = get_conditions(filters)
	return frappe.db.sql(
		"""select a.name
		from `tabSales Invoice` a
		where a.docstatus = 1 and {conditions}""".format(
			conditions=conditions
		),
		filters,
		as_dict=1,
	)


def get_mode_of_payment_details(filters):
	mode_of_payment_details = {}
	invoice_list = get_invoices(filters)
	invoice_list_names = ",".join("'" + invoice["name"] + "'" for invoice in invoice_list)
	if invoice_list:
		inv_mop_detail = frappe.db.sql(
			"""
			select t.owner,
			       t.posting_date,
				   t.mode_of_payment,
				   sum(t.paid_amount) as paid_amount
			from (
				select a.owner, a.posting_date,
				ifnull(b.mode_of_payment, '') as mode_of_payment, sum(b.base_amount) as paid_amount
				from `tabSales Invoice` a, `tabSales Invoice Payment` b
				where a.name = b.parent
				and a.docstatus = 1
				and a.name in ({invoice_list_names})
				group by a.owner, a.posting_date, mode_of_payment
				union
				select a.owner,a.posting_date,
				ifnull(b.mode_of_payment, '') as mode_of_payment, sum(c.allocated_amount) as paid_amount
				from `tabSales Invoice` a, `tabPayment Entry` b,`tabPayment Entry Reference` c
				where a.name = c.reference_name
				and b.name = c.parent
				and b.docstatus = 1
				and a.name in ({invoice_list_names})
				group by a.owner, a.posting_date, mode_of_payment
				union
				select a.owner, a.posting_date,
				ifnull(a.voucher_type,'') as mode_of_payment, sum(b.credit)
				from `tabJournal Entry` a, `tabJournal Entry Account` b
				where a.name = b.parent
				and a.docstatus = 1
				and b.reference_type = 'Sales Invoice'
				and b.reference_name in ({invoice_list_names})
				group by a.owner, a.posting_date, mode_of_payment
			) t
			group by t.owner, t.posting_date, t.mode_of_payment
			""".format(
				invoice_list_names=invoice_list_names
			),
			as_dict=1,
		)

		inv_change_amount = frappe.db.sql(
			"""select a.owner, a.posting_date,
			ifnull(b.mode_of_payment, '') as mode_of_payment, sum(a.base_change_amount) as change_amount
			from `tabSales Invoice` a, `tabSales Invoice Payment` b
			where a.name = b.parent
			and a.name in ({invoice_list_names})
			and b.type = 'Cash'
			and a.base_change_amount > 0
			group by a.owner, a.posting_date, mode_of_payment""".format(
				invoice_list_names=invoice_list_names
			),
			as_dict=1,
		)

		for d in inv_change_amount:
			for det in inv_mop_detail:
				if (
					det["owner"] == d["owner"]
					and det["posting_date"] == d["posting_date"]
					and det["mode_of_payment"] == d["mode_of_payment"]
				):
					paid_amount = det["paid_amount"] - d["change_amount"]
					det["paid_amount"] = paid_amount

		for d in inv_mop_detail:
			mode_of_payment_details.setdefault(d["owner"] + cstr(d["posting_date"]), []).append(
				(d.mode_of_payment, d.paid_amount)
			)

	return mode_of_payment_details


def get_unallocated_total(filters):
	clauses = ["pe.docstatus = 1", "pe.payment_type = 'Receive'", "pe.party_type = 'Customer'"]
	if filters.get("from_date"):
		clauses.append("pe.posting_date >= %(from_date)s")
	if filters.get("to_date"):
		clauses.append("pe.posting_date <= %(to_date)s")
	if filters.get("company"):
		clauses.append("pe.company = %(company)s")
	if filters.get("owner"):
		clauses.append("pe.owner = %(owner)s")  # optional: remove if you don't want this filter applied

	where_sql = " AND ".join(clauses)

	row = frappe.db.sql(f"""
		SELECT
			SUM(
				GREATEST(
					COALESCE(
						pe.unallocated_amount,
						pe.received_amount - IFNULL((
							SELECT SUM(per.allocated_amount)
							FROM `tabPayment Entry Reference` per
							WHERE per.parent = pe.name
						), 0)
					),
					0
				)
			) AS unallocated
		FROM `tabPayment Entry` pe
		WHERE {where_sql}
	""", filters, as_dict=1)

	return (row[0]["unallocated"] or 0) if row else 0

# def get_payment_split_prev_today(filters):
#     """
#     Returns dict keyed by (owner + posting_date) with:
#         {'today': Y, 'prev': X}
#     """
#     split = {}
#     # reuse your conditions, swap alias a. -> si.
#     conditions = get_conditions(filters).replace("a.", "si.")

#     # # 1) SI child payments (on-invoice): always TODAY
#     # sip_rows = frappe.db.sql(f"""
#     #     SELECT si.owner, si.posting_date AS invoice_date, SUM(sip.base_amount) AS amt
#     #     FROM `tabSales Invoice` si
#     #     JOIN `tabSales Invoice Payment` sip ON sip.parent = si.name
#     #     WHERE si.docstatus = 1 AND {conditions}
#     #     GROUP BY si.owner, si.posting_date
#     # """, filters, as_dict=1)

#     # for d in sip_rows:
#     #     k = d["owner"] + cstr(d["invoice_date"])
#     #     obj = split.setdefault(k, {"prev": 0, "today": 0})
#     #     obj["today"] += (d["amt"] or 0)

#     # 2) Payment Entry allocations: compare PE.posting_date vs SI.posting_date
#     pe_rows = frappe.db.sql(f"""
#         SELECT si.owner,
#                si.posting_date AS invoice_date,
#                pe.posting_date AS payment_date,
#                SUM(per.allocated_amount) AS amt
#         FROM `tabSales Invoice` si
#         JOIN `tabPayment Entry Reference` per ON per.reference_name = si.name
#         JOIN `tabPayment Entry` pe ON pe.name = per.parent
#         WHERE si.docstatus = 1 AND pe.docstatus = 1 AND {conditions}
#         GROUP BY si.owner, si.posting_date, pe.posting_date
#     """, filters, as_dict=1)

#     for d in pe_rows:
#         k = d["owner"] + cstr(d["invoice_date"])
#         obj = split.setdefault(k, {"prev": 0, "today": 0})
#         if d["payment_date"] == d["invoice_date"]:
#             obj["today"] += (d["amt"] or 0)
#         elif d["payment_date"] and d["invoice_date"] and d["payment_date"] > d["invoice_date"]:
#             obj["prev"] += (d["amt"] or 0)

#     # 3) Journal Entry allocations: compare JE.posting_date vs SI.posting_date
#     je_rows = frappe.db.sql(f"""
#         SELECT si.owner,
#                si.posting_date AS invoice_date,
#                je.posting_date AS payment_date,
#                SUM(jea.credit) AS amt
#         FROM `tabSales Invoice` si
#         JOIN `tabJournal Entry Account` jea
#              ON jea.reference_type = 'Sales Invoice' AND jea.reference_name = si.name
#         JOIN `tabJournal Entry` je ON je.name = jea.parent
#         WHERE si.docstatus = 1 AND je.docstatus = 1 AND {conditions}
#         GROUP BY si.owner, si.posting_date, je.posting_date
#     """, filters, as_dict=1)

#     for d in je_rows:
#         k = d["owner"] + cstr(d["invoice_date"])
#         obj = split.setdefault(k, {"prev": 0, "today": 0})
#         if d["payment_date"] == d["invoice_date"]:
#             obj["today"] += (d["amt"] or 0)
#         elif d["payment_date"] and d["invoice_date"] and d["payment_date"] > d["invoice_date"]:
#             obj["prev"] += (d["amt"] or 0)

#     # 4) SUBTRACT cash change from TODAY (avoid overstating collections)
#     change_rows = frappe.db.sql(f"""
#         SELECT si.owner, si.posting_date AS invoice_date,
#                SUM(si.base_change_amount) AS change_amount
#         FROM `tabSales Invoice` si
#         JOIN `tabSales Invoice Payment` sip ON sip.parent = si.name
#         WHERE si.docstatus = 1
#           AND sip.type = 'Cash'
#           AND si.base_change_amount > 0
#           AND {conditions}
#         GROUP BY si.owner, si.posting_date
#     """, filters, as_dict=1)

#     for d in change_rows:
#         k = d["owner"] + cstr(d["invoice_date"])
#         if k in split:
#             split[k]["today"] = max(0, split[k]["today"] - (d["change_amount"] or 0))

#     return split

def get_payment_split_prev_today(filters):
	"""
	Return dict keyed by (owner + posting_date) with:
	    {'today': Y, 'prev': X}
	Counts ONLY:
	  - Payment Entry allocations (PER→PE)
	  - Journal Entry allocations (JEA→JE)
	Excludes:
	  - Sales Invoice Payment (SIP) on-invoice rows
	"""
	split = {}
	# reuse your conditions; swap table alias a. -> si. for Sales Invoice joins
	conditions = get_conditions(filters).replace("a.", "si.")

	# 1) Payment Entry allocations
	pe_rows = frappe.db.sql(f"""
		SELECT si.owner,
		       si.posting_date AS invoice_date,
		       pe.posting_date AS payment_date,
		       SUM(per.allocated_amount) AS amt
		FROM `tabSales Invoice` si
		JOIN `tabPayment Entry Reference` per ON per.reference_name = si.name
		JOIN `tabPayment Entry` pe ON pe.name = per.parent
		WHERE si.docstatus = 1 AND pe.docstatus = 1 AND {conditions}
		GROUP BY si.owner, si.posting_date, pe.posting_date
	""", filters, as_dict=1)

	for d in pe_rows:
		k = d["owner"] + cstr(d["invoice_date"])
		obj = split.setdefault(k, {"prev": 0, "today": 0})
		if d["payment_date"] == d["invoice_date"]:
			obj["today"] += (d["amt"] or 0)
		elif d["payment_date"] and d["invoice_date"] and d["payment_date"] > d["invoice_date"]:
			obj["prev"] += (d["amt"] or 0)
		# if payment_date < invoice_date (unusual), ignore for these buckets

	# 2) Journal Entry allocations
	je_rows = frappe.db.sql(f"""
		SELECT si.owner,
		       si.posting_date AS invoice_date,
		       je.posting_date AS payment_date,
		       SUM(jea.credit) AS amt
		FROM `tabSales Invoice` si
		JOIN `tabJournal Entry Account` jea
		     ON jea.reference_type = 'Sales Invoice' AND jea.reference_name = si.name
		JOIN `tabJournal Entry` je ON je.name = jea.parent
		WHERE si.docstatus = 1 AND je.docstatus = 1 AND {conditions}
		GROUP BY si.owner, si.posting_date, je.posting_date
	""", filters, as_dict=1)

	for d in je_rows:
		k = d["owner"] + cstr(d["invoice_date"])
		obj = split.setdefault(k, {"prev": 0, "today": 0})
		if d["payment_date"] == d["invoice_date"]:
			obj["today"] += (d["amt"] or 0)
		elif d["payment_date"] and d["invoice_date"] and d["payment_date"] > d["invoice_date"]:
			obj["prev"] += (d["amt"] or 0)

	return split

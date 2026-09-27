from collections import defaultdict

import frappe
from frappe import _
from frappe.utils.nestedset import get_descendants_of
from frappe.utils import add_months, cint, flt, get_first_day, get_last_day, getdate


ACTIVITIES = (
	(
		"Operating Inflows",
		(
			("cash_close", "Cash Close"),
			("net_receivables", "Net of Receivables"),
			("opd_collections", "OPD Collections"),
			("inpatient_collections", "Inpatient Collections"),
			("insurance_collections", "Insurance Collections"),
			("pharmacy_sales", "Pharmacy Sales"),
			("lab_collections", "Lab Collections"),
			("radiology_collections", "Radiology Collections"),
			("other_service_collections", "Other Service Collections"),
		),
		"Net Operating Inflows",
	),
	(
		"Operating Outflows",
		(
			("salaries_wages", "Salaries & Wages"),
			("doctor_payments", "Doctor Payments"),
			("medicines_purchased", "Medicines Purchased"),
			("medical_consumables", "Medical Consumables"),
			("utilities", "Utilities"),
			("maintenance", "Maintenance"),
			("other_operating_expenses", "Other Operating Expenses"),
		),
		"Net Operating Outflows",
	),
	(
		"Investing Activities",
		(
			("medical_equipment", "Medical Equipment"),
			("building_construction", "Building / Construction"),
			("vehicles", "Vehicles"),
			("it_equipment", "IT Equipment"),
		),
		"Net Investing Cash Flow",
	),
	(
		"Financing Activities",
		(
			("bank_loans", "Bank Loans"),
			("shareholder_capital", "Shareholder Capital"),
			("grants_donations", "Grants / Donations"),
		),
		"Net Financing Cash Flow",
	),
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)
	periods = get_periods(filters.from_date, filters.to_date)
	currency = frappe.get_cached_value("Company", filters.company, "default_currency")
	accounts = get_cash_accounts(filters.company)
	actual = get_actual(filters, accounts)
	opening_balances, closing_balances = get_opening_and_closing_balances(filters, accounts)
	metrics = get_indirect_metrics(filters, actual, opening_balances, closing_balances)
	data = build_indirect_data(metrics)
	columns = get_indirect_columns(currency)
	chart = None
	summary = get_summary(data, currency)
	return columns, data, None, chart, summary


def get_indirect_metrics(filters, actual_rows, opening_balances, closing_balances):
	receivable_accounts = get_descendants_of("Account", "113000 - Accounts Receivable - HH")
	payable_accounts = get_descendants_of("Account", "211000 - Accounts Payable - HH")
	values = {
		"company": filters.company,
		"from_date": filters.from_date,
		"to_date": filters.to_date,
		"receivable_accounts": receivable_accounts or [""],
		"payable_accounts": payable_accounts or [""],
	}
	extra = common_conditions(filters, values, "gle")
	rows = frappe.db.sql(
		f"""
		SELECT
			SUM(CASE
				WHEN a.root_type='Income' THEN gle.credit-gle.debit
				WHEN a.root_type='Expense' THEN gle.credit-gle.debit ELSE 0 END) AS profit_before_tax,
			SUM(CASE WHEN a.account_type='Depreciation'
				AND LOWER(a.account_name) NOT REGEXP 'right.?of.?use|rou|lease'
				THEN gle.debit-gle.credit ELSE 0 END) AS depreciation_ppe,
			SUM(CASE WHEN a.account_type='Depreciation'
				AND LOWER(a.account_name) REGEXP 'right.?of.?use|rou|lease'
				THEN gle.debit-gle.credit ELSE 0 END) AS depreciation_rou,
			SUM(CASE WHEN LOWER(a.account_name) REGEXP 'interest.*lease|lease.*interest'
				THEN gle.debit-gle.credit ELSE 0 END) AS lease_interest,
			SUM(CASE WHEN LOWER(a.account_name) REGEXP 'finance cost|bank charge|interest expense'
				AND LOWER(a.account_name) NOT REGEXP 'lease'
				THEN gle.debit-gle.credit ELSE 0 END) AS finance_costs,
			SUM(CASE WHEN gle.account IN %(receivable_accounts)s THEN gle.credit-gle.debit ELSE 0 END) AS receivables_change,
			SUM(CASE WHEN gle.account IN %(payable_accounts)s THEN gle.credit-gle.debit ELSE 0 END) AS payables_change,
			SUM(CASE WHEN a.account_type='Stock' THEN gle.credit-gle.debit ELSE 0 END) AS inventory_change
		FROM `tabGL Entry` gle
		JOIN `tabAccount` a ON a.name=gle.account
		WHERE gle.company=%(company)s AND gle.is_cancelled=0
			AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND gle.voucher_type != 'Period Closing Voucher' {extra}
		""",
		values,
		as_dict=True,
	)[0]

	direct = defaultdict(float)
	for row in actual_rows:
		direct[row.line_item] += flt(row.amount)
	opening = sum(opening_balances.values())
	closing = sum(closing_balances.values())
	metrics = frappe._dict({key: flt(value) for key, value in rows.items()})
	metrics.income_tax_paid = direct["income_tax_cash"]
	metrics.purchase_ppe = sum(
		direct[key] for key in ("medical_equipment", "building_construction", "vehicles", "it_equipment")
	)
	metrics.share_capital = direct["shareholder_capital"]
	metrics.bank_loans = direct["bank_loans"]
	metrics.grants = direct["grants_donations"]
	metrics.lease_principal = direct["lease_liability_cash"]
	metrics.opening_cash = opening
	metrics.closing_cash = closing
	metrics.cash_accounts = closing_balances
	return metrics


def build_indirect_data(m):
	adjustments = m.depreciation_ppe + m.depreciation_rou + m.lease_interest + m.finance_costs
	working_capital = m.receivables_change + m.payables_change + m.inventory_change
	cash_generated = m.profit_before_tax + adjustments + working_capital
	net_operating = cash_generated + m.income_tax_paid
	net_investing = m.purchase_ppe
	net_financing = m.share_capital + m.bank_loans + m.grants + m.lease_interest + m.finance_costs + m.lease_principal
	net_change = m.closing_cash - m.opening_cash

	def row(label, amount=None, **kwargs):
		return {"description": _(label), "amount": amount, **kwargs}

	data = [
		row("Cash flows from operating activities", is_section=1),
		row("Profit before tax", m.profit_before_tax),
		row("Adjustments to cash flows from non-cash items", is_heading=1),
		row("Depreciation on property and equipment", m.depreciation_ppe, indent=1),
		row("Depreciation on right-of-use asset", m.depreciation_rou, indent=1),
		row("Interest expenses on lease liability", m.lease_interest, indent=1),
		row("Finance costs", m.finance_costs, indent=1),
		row("Total non-cash adjustments", adjustments, is_subtotal=1),
		row("Working capital adjustments", is_heading=1),
		row("(Increase)/decrease in trade receivables", m.receivables_change, indent=1),
		row("Increase/(decrease) in trade and other payables", m.payables_change, indent=1),
		row("Inventory", m.inventory_change, indent=1),
		row("Total working capital adjustments", working_capital, is_subtotal=1),
		row("Cash generated from operations", cash_generated, is_subtotal=1),
		row("Income tax paid", m.income_tax_paid),
		row("Net cash flow from/(used in) operating activities", net_operating, is_total=1),
		row("", is_blank=1),
		row("Cash flows from investing activities", is_section=1),
		row("Purchase of property and equipment", m.purchase_ppe),
		row("Net cash flows from investing activities", net_investing, is_total=1),
		row("", is_blank=1),
		row("Cash flows from financing activities", is_section=1),
		row("Issue of share capital", m.share_capital),
		row("Bank loans", m.bank_loans),
		row("Grants / donations", m.grants),
		row("Interest expense on lease liabilities", m.lease_interest),
		row("Finance costs", m.finance_costs),
		row("Payment of principal element of lease", m.lease_principal),
		row("Net cash flows used in financing activities", net_financing, is_total=1),
		row("", is_blank=1),
		row("Net increase/(decrease) in cash and cash equivalents", net_change, is_total=1),
		row("Cash and cash equivalents at beginning of period", m.opening_cash),
		row("Cash and cash equivalents at end of period", m.closing_cash, is_total=1),
		row("Reconciliation of cash and cash equivalents", is_section=1),
		row("-    Cash and cash equivalents", m.closing_cash, indent=1),
	]
	for account in sorted(m.cash_accounts):
		data.append(row(account, m.cash_accounts[account], account=account, indent=2, is_detail=1))
	data.append(row("Total cash and cash equivalents", m.closing_cash, is_total=1))
	return data


def get_indirect_columns(currency):
	return [
		{"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 430},
		{"label": currency, "fieldname": "amount", "fieldtype": "Currency", "options": "currency", "width": 180},
	]


def validate_filters(filters):
	for field in ("company", "from_date", "to_date"):
		if not filters.get(field):
			frappe.throw(_("{0} is required").format(_(field.replace("_", " ").title())))
	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date cannot be after To Date"))


def get_periods(from_date, to_date):
	start, end = getdate(from_date), getdate(to_date)
	periods = []
	cursor = get_first_day(start)
	while cursor <= end:
		period_from = max(cursor, start)
		period_to = min(get_last_day(cursor), end)
		periods.append(
			frappe._dict(
				key=cursor.strftime("m_%Y_%m"),
				label=cursor.strftime("%b %Y"),
				from_date=period_from,
				to_date=period_to,
			)
		)
		cursor = get_first_day(add_months(cursor, 1))
	return periods


def get_cash_accounts(company):
	return frappe.db.get_all(
		"Account",
		filters={
			"company": company,
			"is_group": 0,
			"account_type": ["in", ["Cash", "Bank"]],
		},
		pluck="name",
	)


def common_conditions(filters, values, alias="gle"):
	conditions = []
	if filters.get("cost_center"):
		conditions.append(f"{alias}.cost_center = %(cost_center)s")
		values["cost_center"] = filters.cost_center
	if filters.get("project"):
		conditions.append(f"{alias}.project = %(project)s")
		values["project"] = filters.project
	if filters.get("finance_book"):
		conditions.append(f"IFNULL({alias}.finance_book, '') = %(finance_book)s")
		values["finance_book"] = filters.finance_book
	return (" AND " + " AND ".join(conditions)) if conditions else ""


def get_actual(filters, accounts):
	if not accounts:
		return []
	values = {
		"company": filters.company,
		"from_date": filters.from_date,
		"to_date": filters.to_date,
		"accounts": accounts,
	}
	extra = common_conditions(filters, values, "gle")
	cash_rows = frappe.db.sql(
		f"""
		SELECT
			CASE WHEN gle.debit - gle.credit >= 0 THEN 'inflow' ELSE 'outflow' END AS direction,
			gle.voucher_type, gle.voucher_no, gle.account,
			DATE_FORMAT(gle.posting_date, 'm_%%Y_%%m') AS period_key,
			SUM(gle.debit - gle.credit) AS amount
		FROM `tabGL Entry` gle
		WHERE gle.company = %(company)s AND gle.is_cancelled = 0
			AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND gle.account IN %(accounts)s {extra}
		GROUP BY direction, gle.voucher_type, gle.voucher_no, gle.account, period_key
		""",
		values,
		as_dict=True,
	)

	classifications = get_voucher_classifications(filters.company, cash_rows, accounts)
	aggregated = defaultdict(float)
	for row in cash_rows:
		flags = classifications.get((row.voucher_type, row.voucher_no), {})
		counterpart_accounts = flags.get("counterpart_accounts") if flags else None
		source_account = counterpart_accounts.split("|||")[0] if counterpart_accounts else row.account
		if is_cash_close(row.account):
			line_item = "cash_close"
			source_account = row.account
		else:
			line_item = classify_line_item(row.direction, flags, source_account)
			if line_item == "net_receivables" and flags.get("receivable_accounts"):
				source_account = flags.receivable_accounts.split("|||")[0]
		amount = flt(row.amount)
		if is_opd_or_pharmacy_cashier(source_account):
			amount = abs(amount)
		aggregated[(line_item, source_account, row.period_key)] += amount
		if flags.get("has_income_tax"):
			aggregated[("income_tax_cash", source_account, row.period_key)] += amount
		if flags.get("has_lease_liability"):
			aggregated[("lease_liability_cash", source_account, row.period_key)] += amount
	return [
		frappe._dict(line_item=key[0], account=key[1], period_key=key[2], amount=amount)
		for key, amount in aggregated.items()
	]


def classify_line_item(direction, flags, source_account):
	name = (source_account or "").lower()
	if is_opd_or_pharmacy_cashier(source_account):
		return "other_service_collections"
	if flags.get("has_fixed_asset"):
		if any(word in name for word in ("building", "construction", "work in progress")):
			return "building_construction"
		if any(word in name for word in ("vehicle", "motor", "ambulance")):
			return "vehicles"
		if any(word in name for word in ("computer", "software", "server", " it ")):
			return "it_equipment"
		return "medical_equipment"
	if flags.get("has_financing"):
		if any(word in name for word in ("capital", "shareholder", "equity", "share capital")):
			return "shareholder_capital"
		if any(word in name for word in ("grant", "donation")):
			return "grants_donations"
		return "bank_loans"
	if direction == "inflow":
		if flags.get("has_receivable"):
			return "net_receivables"
		if flags.get("has_insurance") or "insurance" in name:
			return "insurance_collections"
		if any(word in name for word in ("inpatient", " ipd", "ward", "bed charge")):
			return "inpatient_collections"
		if any(word in name for word in ("pharmacy", "drug", "medicine sales")):
			return "pharmacy_sales"
		if any(word in name for word in ("laboratory", " lab ", "lab -")):
			return "lab_collections"
		if any(word in name for word in ("radiology", "x-ray", "xray", "ct scan", "mri", "ultrasound")):
			return "radiology_collections"
		if any(word in name for word in ("opd", "outpatient", "consultation")):
			return "opd_collections"
		return "other_service_collections"
	if flags.get("has_salary") or any(word in name for word in ("salary", "salaries", "wage", "payroll")):
		return "salaries_wages"
	if any(word in name for word in ("doctor", "consultant", "physician")):
		return "doctor_payments"
	if any(word in name for word in ("medicine", "medicines", "drug purchase", "pharmacy purchase")):
		return "medicines_purchased"
	if any(word in name for word in ("consumable", "medical supply", "surgical supply")):
		return "medical_consumables"
	if any(word in name for word in ("utility", "electric", "water", "telephone", "internet")):
		return "utilities"
	if any(word in name for word in ("maintenance", "repair")):
		return "maintenance"
	if flags.get("has_supplier"):
		return "other_operating_expenses"
	return "other_operating_expenses"


def is_opd_or_pharmacy_cashier(account):
	name = (account or "").lower()
	return "opd cashier" in name or "pharma cashier" in name or "pharmacy cashier" in name


def is_cash_close(account):
	name = (account or "").lower()
	return "cash close" in name or name.startswith("111028 - cash close")


def get_voucher_classifications(company, cash_rows, cash_accounts):
	vouchers = list({row.voucher_no for row in cash_rows if row.voucher_no})
	classifications = {}
	for start in range(0, len(vouchers), 1000):
		rows = frappe.db.sql(
			"""
			SELECT gle.voucher_type, gle.voucher_no,
				MAX(a.account_type = 'Fixed Asset') AS has_fixed_asset,
				MAX(a.root_type = 'Equity' OR a.account_type = 'Loan') AS has_financing,
				MAX(LOWER(CONCAT_WS(' ', a.account_name, gle.party)) LIKE '%%insurance%%') AS has_insurance,
				MAX(a.account_type = 'Receivable') AS has_receivable,
				GROUP_CONCAT(
					DISTINCT CASE WHEN a.account_type = 'Receivable' THEN a.name END
					SEPARATOR '|||'
				) AS receivable_accounts,
				MAX(LOWER(a.account_name) REGEXP 'salary|salaries|payroll|wage') AS has_salary,
				MAX(gle.party_type = 'Supplier' OR a.account_type = 'Payable') AS has_supplier,
				MAX(LOWER(a.account_name) REGEXP 'income tax|tax payable') AS has_income_tax,
				MAX(LOWER(a.account_name) REGEXP 'lease liability') AS has_lease_liability,
				GROUP_CONCAT(
					DISTINCT CASE WHEN gle.account NOT IN %s THEN a.name END
					ORDER BY ABS(gle.debit - gle.credit) DESC SEPARATOR '|||'
				) AS counterpart_accounts
			FROM `tabGL Entry` gle
			JOIN `tabAccount` a ON a.name = gle.account
			WHERE gle.company=%s AND gle.is_cancelled=0 AND gle.voucher_no IN %s
			GROUP BY gle.voucher_type, gle.voucher_no
			""",
			(tuple(cash_accounts), company, tuple(vouchers[start : start + 1000])),
			as_dict=True,
		)
		for row in rows:
			classifications[(row.voucher_type, row.voucher_no)] = row
	return classifications


def get_opening_and_closing_balances(filters, accounts):
	if not accounts:
		return {}, {}
	values = {
		"company": filters.company,
		"accounts": accounts,
		"from_date": filters.from_date,
		"to_date": filters.to_date,
	}
	extra = common_conditions(filters, values, "gle")
	rows = frappe.db.sql(
		f"""SELECT gle.account,
			SUM(CASE WHEN gle.posting_date < %(from_date)s THEN gle.debit - gle.credit ELSE 0 END) AS opening,
			SUM(gle.debit - gle.credit) AS closing
		FROM `tabGL Entry` gle
		WHERE gle.company=%(company)s AND gle.is_cancelled=0 AND gle.account IN %(accounts)s
			AND gle.posting_date <= %(to_date)s {extra}
		GROUP BY gle.account""",
		values,
		as_dict=True,
	)
	opening = {row.account: flt(row.opening) for row in rows if abs(flt(row.opening)) > 0.000001}
	closing = {row.account: flt(row.closing) for row in rows if abs(flt(row.closing)) > 0.000001}
	return opening, closing


def get_budget(filters):
	values = {"company": filters.company, "from_date": filters.from_date, "to_date": filters.to_date}
	conditions = ["b.company=%(company)s", "b.docstatus=1"]
	if filters.get("cost_center"):
		conditions.append("(b.cost_center=%(cost_center)s OR b.cost_center IS NULL)")
		values["cost_center"] = filters.cost_center
	if filters.get("project"):
		conditions.append("(b.project=%(project)s OR b.project IS NULL)")
		values["project"] = filters.project
	rows = frappe.db.sql(
		f"""
		SELECT ba.account, ba.budget_amount, fy.year_start_date, fy.year_end_date,
			a.root_type, a.account_type
		FROM `tabBudget` b
		JOIN `tabBudget Account` ba ON ba.parent=b.name
		JOIN `tabFiscal Year` fy ON fy.name=b.fiscal_year
		JOIN `tabAccount` a ON a.name=ba.account
		WHERE {' AND '.join(conditions)}
			AND fy.year_end_date >= %(from_date)s AND fy.year_start_date <= %(to_date)s
		""",
		values,
		as_dict=True,
	)
	out = defaultdict(float)
	for row in rows:
		start = max(getdate(filters.from_date), getdate(row.year_start_date))
		end = min(getdate(filters.to_date), getdate(row.year_end_date))
		ratio = (end - start).days + 1
		ratio /= (getdate(row.year_end_date) - getdate(row.year_start_date)).days + 1
		amount = flt(row.budget_amount) * ratio
		if row.account_type == "Fixed Asset":
			out["medical_equipment"] -= amount
		elif row.root_type == "Income":
			out["other_service_collections"] += amount
		elif row.root_type == "Expense":
			out["other_operating_expenses"] -= amount
	return out


def build_data(filters, periods, actual_rows, budget, opening_balances, closing_balances, currency):
	values = defaultdict(lambda: defaultdict(float))
	account_values = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
	for row in actual_rows:
		values[row.line_item][row.period_key] += flt(row.amount)
		account_values[row.line_item][row.account][row.period_key] += flt(row.amount)

	data = []
	net_change = 0
	for section_label, line_items, total_label in ACTIVITIES:
		data.append({"account_name": _(section_label), "is_section": 1, "indent": 0})
		section_total = {"account_name": _(total_label), "is_subtotal": 1, "indent": 0}
		for key, label in line_items:
			row = {"account_name": _(label), "line_item": key, "indent": 1}
			for period in periods:
				row[period.key] = values[key][period.key]
			row["actual_total"] = sum(row.get(period.key, 0) for period in periods)
			row["budget"] = flt(budget.get(key))
			row["variance"] = row["actual_total"] - row["budget"]
			data.append(row)
			for account in sorted(account_values[key]):
				detail_values = account_values[key][account]
				account_row = {
					"account_name": "",
					"erpnext_account": account,
					"account": account,
					"indent": 2,
					"is_detail": 1,
				}
				for period in periods:
					account_row[period.key] = detail_values[period.key]
				account_row["actual_total"] = sum(
					account_row.get(period.key, 0) for period in periods
				)
				data.append(account_row)
			for period in periods:
				section_total[period.key] = section_total.get(period.key, 0) + row[period.key]
			section_total["actual_total"] = section_total.get("actual_total", 0) + row["actual_total"]
			section_total["budget"] = section_total.get("budget", 0) + row["budget"]
		section_total["variance"] = section_total.get("actual_total", 0) - section_total.get("budget", 0)
		data.append(section_total)
		net_change += section_total["actual_total"]

	opening = sum(opening_balances.values())
	closing = sum(closing_balances.values())
	data.append({"account_name": _("Net Increase in Cash"), "actual_total": net_change, "is_balance": 1})
	data.append({"account_name": _("Opening Cash & Bank"), "actual_total": opening, "is_balance": 1})
	add_balance_details(data, opening_balances)
	data.append(
		{
			"account_name": _("Closing Cash & Bank"),
			"actual_total": closing,
			"is_balance": 1,
		}
	)
	add_balance_details(data, closing_balances)
	return data


def add_balance_details(data, balances):
	for account in sorted(balances):
		data.append(
			{
				"account_name": "",
				"erpnext_account": account,
				"account": account,
				"actual_total": balances[account],
				"indent": 1,
				"is_detail": 1,
			}
		)


def get_columns(periods, currency, include_budget):
	columns = [
		{"label": _("Cash Flow Category"), "fieldname": "account_name", "fieldtype": "Data", "width": 250},
		{"label": _("ERPNext Account"), "fieldname": "erpnext_account", "fieldtype": "Data", "width": 260},
	]
	columns.extend(
		{
			"label": period.label,
			"fieldname": period.key,
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		}
		for period in periods
	)
	columns.append({"label": _("Actual Total"), "fieldname": "actual_total", "fieldtype": "Currency", "options": "currency", "width": 140})
	if include_budget:
		columns.extend(
			[
				{"label": _("Budget"), "fieldname": "budget", "fieldtype": "Currency", "options": "currency", "width": 130},
				{"label": _("Variance"), "fieldname": "variance", "fieldtype": "Currency", "options": "currency", "width": 130},
			]
		)
	return columns


def get_chart(periods, data):
	sections = [row for row in data if row.get("is_subtotal")]
	return {
		"data": {
			"labels": [period.label for period in periods],
			"datasets": [
				{"name": row.get("account_name"), "values": [row.get(period.key, 0) for period in periods]}
				for row in sections
			],
		},
		"type": "bar",
	}


def get_summary(data, currency):
	if data and "description" in data[0]:
		lookup = {row.get("description"): row.get("amount") for row in data}
		return [
			{"label": _("Opening Balance"), "value": lookup.get(_("Cash and cash equivalents at beginning of period"), 0), "datatype": "Currency", "currency": currency},
			{"label": _("Net Change"), "value": lookup.get(_("Net increase/(decrease) in cash and cash equivalents"), 0), "datatype": "Currency", "currency": currency},
			{"label": _("Closing Balance"), "value": lookup.get(_("Cash and cash equivalents at end of period"), 0), "datatype": "Currency", "currency": currency},
		]
	lookup = {row.get("account_name"): row.get("actual_total") for row in data if row.get("is_balance")}
	return [
		{"label": _("Opening Balance"), "value": lookup.get(_("Opening Cash & Bank"), 0), "datatype": "Currency", "currency": currency},
		{"label": _("Net Change"), "value": lookup.get(_("Net Increase in Cash"), 0), "datatype": "Currency", "currency": currency},
		{"label": _("Closing Balance"), "value": lookup.get(_("Closing Cash & Bank"), 0), "datatype": "Currency", "currency": currency},
	]

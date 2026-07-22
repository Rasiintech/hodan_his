import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime
from erpnext.stock.get_item_details import get_pos_profile

INSURANCE_FIELDNAMES = (
    "is_insurance",
    "insurance",
    "insurance_id",
    "insurance_policy",
    "insurance_company",
    "policy_number",
    "policyholder_name",
    "coverage_limits",
    "expiry_date",
    "insurance_coverage_amount",
    "insurance_paid",
    "is_claimed",
)

EMPLOYEE_BILLING_FIELDNAMES = (
    "bill_to_employee",
    "employee",
)


class SalesReturnRequest(Document):
    def autoname(self):
        if not self.naming_series:
            self.naming_series = "SRR-.YYYY.-.#####"

    def before_insert(self):
        if not self.requested_by:
            self.requested_by = frappe.session.user
        if not self.requested_by_name:
            self.requested_by_name = frappe.db.get_value("User", self.requested_by, "full_name") or self.requested_by
        if not self.status:
            self.status = "Draft"

    def before_save(self):
        new_state = self.workflow_state or self.status or "Draft"
        if new_state in ("Approved", "Rejected") and not self.finance_reviewer:
            self.finance_reviewer = frappe.session.user
            self.finance_review_date = now_datetime()

        if new_state in ("Refund In Progress", "Refunded") and not self.cashier:
            self.cashier = frappe.session.user
            self.cashier_action_date = now_datetime()

    def validate(self):
        self.sync_status()
        self.validate_invoice()
        self.set_invoice_snapshot()
        self.validate_no_duplicate_open_request()
        self.validate_amounts()

    def on_submit(self):
        self.sync_status()

    def sync_status(self):
        self.status = self.workflow_state or self.status or "Draft"

    def validate_invoice(self):
        if not self.sales_invoice:
            return
        si = frappe.get_doc("Sales Invoice", self.sales_invoice)
        if si.docstatus != 1:
            frappe.throw(_("Original Sales Invoice must be submitted"))
        if getattr(si, "is_return", 0):
            frappe.throw(_("Original Sales Invoice cannot already be a return invoice"))
        if self.customer and si.customer != self.customer:
            frappe.throw(_("Customer must match the original Sales Invoice customer"))
        if not self.customer:
            self.customer = si.customer
        self.currency = si.currency
        self.sales_invoice_date = si.posting_date
        self.company = self.company or si.company
        self.invoice_net_total = flt(si.net_total)
        self.invoice_additional_discount_percentage = flt(si.additional_discount_percentage)
        self.invoice_discount_amount = flt(si.discount_amount)
        self.invoice_grand_total = flt(si.grand_total)
        self.invoice_paid_amount = flt(si.grand_total) - flt(si.outstanding_amount)
        self.invoice_outstanding_amount = flt(si.outstanding_amount)
        self.set_insurance_details(si)

    def set_insurance_details(self, sales_invoice_doc):
        insurance_values = get_sales_invoice_insurance_values(sales_invoice_doc)
        for fieldname, value in insurance_values.items():
            setattr(self, fieldname, value)

    def set_invoice_snapshot(self):
        if not self.sales_invoice:
            return
        self.already_refunded_amount = get_existing_return_total(self.sales_invoice)
        self.eligible_refund_amount = flt(self.invoice_grand_total)
        self.balance_refundable = max(flt(self.eligible_refund_amount) - flt(self.already_refunded_amount), 0)

    def validate_amounts(self):
        if flt(self.requested_amount) <= 0:
            frappe.throw(_("Requested Amount must be greater than zero"))

        row_total = sum(flt(d.return_amount) for d in self.items)
        if self.items and abs(flt(self.requested_amount) - flt(row_total)) > 0.0001:
            frappe.throw(_("Requested Amount must equal the sum of item return amounts"))

        if flt(self.balance_refundable) and flt(self.requested_amount) > flt(self.balance_refundable):
            frappe.throw(_("Requested Amount cannot exceed Balance Refundable"))

        if self.workflow_state == "Rejected" and not self.rejection_reason:
            frappe.throw(_("Rejection Reason is required when rejecting a request"))

        for row in self.items:
            if flt(row.returned_qty) <= 0:
                frappe.throw(_("Returned Qty must be greater than zero in row {0}").format(row.idx))
            if flt(row.return_amount) <= 0:
                frappe.throw(_("Return Amount must be greater than zero in row {0}").format(row.idx))

    def validate_no_duplicate_open_request(self):
        existing_request = get_existing_sales_return_request(
            reference_doctype=self.reference_doctype,
            reference_name=self.reference_name,
            sales_invoice=self.sales_invoice,
            patient=self.patient,
            exclude_name=self.name,
        )
        if existing_request:
            frappe.throw(
                _("Sales Return Request {0} already exists for this source document.").format(
                    existing_request
                )
            )


def get_existing_return_total(sales_invoice):
    data = frappe.get_all(
        "Sales Invoice",
        filters={"return_against": sales_invoice, "docstatus": 1, "is_return": 1},
        fields=["grand_total"],
    )
    return abs(sum(flt(d.grand_total) for d in data))


@frappe.whitelist()
def get_existing_sales_return_request(
    reference_doctype=None,
    reference_name=None,
    sales_invoice=None,
    patient=None,
    exclude_name=None,
):
    filters = [["docstatus", "<", 2], ["status", "not in", ["Rejected", "Cancelled"]]]

    if exclude_name:
        filters.append(["name", "!=", exclude_name])

    if reference_doctype and reference_name:
        filters.extend(
            [
                ["reference_doctype", "=", reference_doctype],
                ["reference_name", "=", reference_name],
            ]
        )
    elif sales_invoice and patient:
        filters.extend(
            [
                ["sales_invoice", "=", sales_invoice],
                ["patient", "=", patient],
            ]
        )
    else:
        return None

    return frappe.db.get_value(
        "Sales Return Request",
        filters=filters,
        fieldname="name",
        order_by="creation desc",
    )


@frappe.whitelist()
def get_invoice_items(sales_invoice, reference_doctype=None, reference_name=None):
    si = frappe.get_doc("Sales Invoice", sales_invoice)
    if si.docstatus != 1:
        frappe.throw(_("Sales Invoice must be submitted"))

    allowed_item_codes = get_reference_item_codes(reference_doctype, reference_name)
    rows = []
    for item in si.items:
        if allowed_item_codes and item.item_code not in allowed_item_codes:
            continue
        item_discount_amount = get_item_discount_amount(item)
        default_return_amount = max(flt(item.amount) - item_discount_amount, 0)
        rows.append({
            "sales_invoice_item": item.name,
            "item_code": item.item_code,
            "item_name": item.item_name,
            "description": item.description,
            "qty": item.qty,
            "rate": flt(item.amount),
            "amount": flt(item.amount),
            "discount_percentage": flt(item.discount_percentage),
            "discount_amount": item_discount_amount,
            "returned_qty": abs(flt(item.qty)),
            "return_amount": default_return_amount,
            "max_return_amount": default_return_amount,
            "service_department": getattr(item, "cost_center", None) or ""
        })
    return rows


@frappe.whitelist()
def get_invoice_summary(sales_invoice):
    if not sales_invoice:
        return {}

    si = frappe.get_doc("Sales Invoice", sales_invoice)
    if si.docstatus != 1:
        frappe.throw(_("Sales Invoice must be submitted"))

    invoice_grand_total = flt(si.grand_total)
    invoice_paid_amount = flt(si.grand_total) - flt(si.outstanding_amount)
    invoice_outstanding_amount = flt(si.outstanding_amount)
    already_refunded_amount = get_existing_return_total(sales_invoice)
    eligible_refund_amount = flt(invoice_paid_amount or invoice_grand_total)
    balance_refundable = max(flt(eligible_refund_amount) - flt(already_refunded_amount), 0)

    return {
        "company": si.company,
        "customer": si.customer,
        "currency": si.currency,
        "sales_invoice_date": si.posting_date,
        "patient": getattr(si, "patient", None),
        "patient_name": getattr(si, "patient_name", None),
        "invoice_net_total": flt(si.net_total),
        "invoice_additional_discount_percentage": flt(si.additional_discount_percentage),
        "invoice_discount_amount": flt(si.discount_amount),
        "invoice_grand_total": invoice_grand_total,
        "invoice_paid_amount": invoice_paid_amount,
        "invoice_outstanding_amount": invoice_outstanding_amount,
        "already_refunded_amount": already_refunded_amount,
        "eligible_refund_amount": eligible_refund_amount,
        "balance_refundable": balance_refundable,
        **get_sales_invoice_insurance_values(si),
    }


def get_sales_invoice_insurance_values(sales_invoice_doc):
    return {
        "is_insurance": flt(getattr(sales_invoice_doc, "is_insurance", 0)),
        "insurance": getattr(sales_invoice_doc, "insurance", None),
        "insurance_id": getattr(sales_invoice_doc, "insurance_id", None),
        "insurance_policy": getattr(sales_invoice_doc, "insurance_policy", None),
        "insurance_company": getattr(sales_invoice_doc, "insurance_company", None),
        "policy_number": getattr(sales_invoice_doc, "policy_number", None),
        "policyholder_name": getattr(sales_invoice_doc, "policyholder_name", None),
        "coverage_limits": getattr(sales_invoice_doc, "coverage_limits", None),
        "expiry_date": getattr(sales_invoice_doc, "expiry_date", None),
        "insurance_coverage_amount": flt(getattr(sales_invoice_doc, "insurance_coverage_amount", 0)),
        "insurance_paid": flt(getattr(sales_invoice_doc, "insurance_paid", 0)),
        "is_claimed": flt(getattr(sales_invoice_doc, "is_claimed", 0)),
    }


def get_reference_item_codes(reference_doctype=None, reference_name=None):
    if not reference_doctype or not reference_name or not frappe.db.exists(reference_doctype, reference_name):
        return set()

    if reference_doctype == "Radiology":
        examination = frappe.db.get_value("Radiology", reference_name, "eximination")
        if not examination:
            return set()

        item_code = frappe.db.get_value("Radiology Template", examination, "item")
        return {item_code} if item_code else set()

    if reference_doctype == "Sample Collection":
        sample_collection = frappe.get_doc("Sample Collection", reference_name)
        item_codes = set()
        for row in sample_collection.get("lab_test") or []:
            if not row.lab_test:
                continue
            item_code = frappe.db.get_value("Lab Test Template", row.lab_test, "item")
            if item_code:
                item_codes.add(item_code)
        return item_codes

    return set()


@frappe.whitelist()
def create_return_invoice(docname):
    doc = frappe.get_doc("Sales Return Request", docname)
    doc.reload()

    if doc.workflow_state not in ("Approved", "Refund In Progress"):
        frappe.throw(_("Only approved requests can create a return invoice"))

    if doc.return_sales_invoice:
        return doc.return_sales_invoice

    if not doc.items:
        frappe.throw(_("Please load invoice items first"))

    source = frappe.get_doc("Sales Invoice", doc.sales_invoice)
    if source.docstatus != 1:
        frappe.throw(_("Original Sales Invoice must be submitted"))

    target = frappe.new_doc("Sales Invoice")
    target.customer = source.customer
    target.patient = getattr(source, "patient", None) or doc.patient
    target.patient_name = getattr(source, "patient_name", None) or doc.patient_name
    target.ref_practitioner = getattr(source, "ref_practitioner", None)
    target.cost_center = getattr(source, "cost_center", None)
    target.company = source.company
    target.currency = source.currency
    target.debit_to = getattr(source, "debit_to", None)
    target.is_return = 1
    target.return_against = source.name
    target.posting_date = frappe.utils.today()
    target.due_date = frappe.utils.today()
    target.update_stock = 0
    target.set_warehouse = getattr(source, "set_warehouse", None)
    target.ignore_pricing_rule = 1
    target.remarks = _("Auto-created from Sales Return Request {0}").format(doc.name)
    apply_source_insurance_fields(target, source)
    apply_source_employee_billing_fields(target, source)

    requested_by_row = {d.sales_invoice_item: d for d in doc.items if flt(d.return_amount) > 0 and flt(d.returned_qty) > 0}
    if not requested_by_row:
        frappe.throw(_("No valid item rows found"))

    for src_row in source.items:
        req = requested_by_row.get(src_row.name)
        if not req:
            continue
        item = target.append("items", {})
        item.item_code = src_row.item_code
        item.item_name = src_row.item_name
        item.description = src_row.description
        item.uom = src_row.uom
        item.stock_uom = getattr(src_row, "stock_uom", None)
        item.conversion_factor = getattr(src_row, "conversion_factor", 1)
        item.qty = -abs(flt(req.returned_qty))
        item.rate = flt(src_row.rate)
        item.income_account = getattr(src_row, "income_account", None)
        item.cost_center = getattr(src_row, "cost_center", None)
        item.warehouse = getattr(src_row, "warehouse", None)
        item.so_detail = getattr(src_row, "so_detail", None)
        item.sales_order = getattr(src_row, "sales_order", None)

    if not target.items:
        frappe.throw(_("No matching invoice items were selected"))

    target.run_method("set_missing_values")
    configure_refund_invoice(target, source, doc)
    apply_source_employee_billing_fields(target, source)
    target.flags.ignore_permissions = True
    target.insert()
    target.submit()

    doc.db_set("return_sales_invoice", target.name)
    doc.db_set("workflow_state", "Refunded")
    doc.db_set("status", "Refunded")
    if is_cash_refund_user():
        doc.db_set("cashier", frappe.session.user)
        doc.db_set("cashier_action_date", now_datetime())

    return target.name


def configure_refund_invoice(target, source, request_doc):
    apply_source_discount(target, source, request_doc)
    if is_cash_refund_user() and request_doc.refund_mode_of_payment:
        apply_cash_refund_settings(target, source, request_doc)
    else:
        apply_credit_refund_settings(target)


def apply_source_insurance_fields(target, source):
    for fieldname in INSURANCE_FIELDNAMES:
        if hasattr(target, fieldname):
            setattr(target, fieldname, getattr(source, fieldname, None))


def apply_source_employee_billing_fields(target, source):
    if not getattr(source, "bill_to_employee", 0):
        return

    for fieldname in EMPLOYEE_BILLING_FIELDNAMES:
        if hasattr(target, fieldname):
            setattr(target, fieldname, getattr(source, fieldname, None))


def apply_source_discount(target, source, request_doc):
    selected_net_total = get_selected_net_total(request_doc, source)
    if not selected_net_total or not flt(source.net_total) or not flt(source.discount_amount):
        return

    proportional_discount = flt(source.discount_amount) * (flt(selected_net_total) / flt(source.net_total))
    target.additional_discount_percentage = flt(source.additional_discount_percentage)
    target.discount_amount = -1 * proportional_discount
    target.run_method("calculate_taxes_and_totals")


def is_cash_refund_user():
    user_roles = set(frappe.get_roles(frappe.session.user))
    return "Cashier" in user_roles or "Cashier Return Processor" in user_roles


def apply_credit_refund_settings(target):
    target.is_pos = 0
    target.pos_profile = None
    target.set("payments", [])
    target.write_off_amount = 0
    target.run_method("set_paid_amount")


def apply_cash_refund_settings(target, source, request_doc):
    pos_profile = get_pos_profile(target.company)
    if not pos_profile:
        frappe.throw(_("Please configure a POS Profile for company {0}").format(target.company))

    if isinstance(pos_profile, dict):
        pos_profile = frappe.get_doc("POS Profile", pos_profile.get("name"))
    else:
        pos_profile = frappe.get_doc("POS Profile", pos_profile)

    mode_of_payment = get_cash_refund_mode_of_payment(pos_profile, source, request_doc)
    mop_account = frappe.db.get_value(
        "Mode of Payment Account",
        {"parent": mode_of_payment, "company": target.company},
        "default_account",
    )
    if not mop_account:
        frappe.throw(
            _("No default account found for Mode of Payment {0} and company {1}").format(
                mode_of_payment, target.company
            )
        )

    target.is_pos = 1
    target.pos_profile = pos_profile.name
    target.set("payments", [])
    target.write_off_amount = 0
    target.run_method("calculate_taxes_and_totals")
    invoice_total = flt(target.rounded_total or target.grand_total)
    target.append(
        "payments",
        {
            "mode_of_payment": mode_of_payment,
            "amount": invoice_total,
            "account": mop_account,
        },
    )
    target.run_method("set_paid_amount")
    target.remarks = request_doc.refund_remarks or _(
        "Cash refund auto-created from Sales Return Request {0}"
    ).format(request_doc.name)


def get_cash_refund_mode_of_payment(pos_profile, source, request_doc):
    if request_doc.refund_mode_of_payment:
        return request_doc.refund_mode_of_payment
    return None


def get_invoice_discount_share(invoice_doc, row_net_amount):
    if not flt(invoice_doc.discount_amount) or not flt(invoice_doc.net_total):
        return 0

    return flt(invoice_doc.discount_amount) * (flt(row_net_amount) / flt(invoice_doc.net_total))


def get_item_discount_amount(invoice_item):
    return flt(invoice_item.amount) - flt(invoice_item.net_amount)


def get_selected_net_total(request_doc, source_invoice):
    source_rows = {row.name: row for row in source_invoice.items}
    total = 0

    for req_row in request_doc.items:
        if flt(req_row.returned_qty) <= 0:
            continue

        source_row = source_rows.get(req_row.sales_invoice_item)
        if not source_row or not flt(source_row.qty):
            continue

        total += flt(source_row.net_amount) * (flt(req_row.returned_qty) / flt(source_row.qty))

    return total

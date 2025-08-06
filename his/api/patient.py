import frappe
from datetime import datetime # from python std library
from frappe.utils import add_to_date
from erpnext.stock.get_item_details import get_pos_profile
from erpnext.accounts.doctype.sales_invoice.sales_invoice import (
    set_account_for_mode_of_payment,
)

def age_todate(doc, method=None):
    if doc.p_age < 0 :
        frappe.throw("Age Can not be Negative ")
    if doc.age_type=="Year":

        # frappe.msgprint(str(doc.p_age)+ " "+ str(doc.age_type))
        add_year = add_to_date(datetime.now(), years=-doc.p_age, as_string=True)
        doc.dob=add_year
        # frappe.msgprint(add_year)
    elif doc.age_type=="Month":
        add_month = add_to_date(datetime.now(), months=-doc.p_age, as_string=True)
        doc.dob=add_month
        # frappe.msgprint(add_month)
    elif doc.age_type=="Day":
        add_day = add_to_date(datetime.now(), days=-doc.p_age, as_string=True)
        doc.dob=add_day
        # frappe.msgprint(add_day)


def invoice_registration(doc, method=None):
    if frappe.db.get_single_value("Healthcare Settings", "collect_registration_fee"):
        rate = frappe.db.get_single_value("Healthcare Settings", "registration_fee")
        # invoice_info = doc.invoice_patient_registration()
        invoice = frappe.new_doc("Sales Invoice")
        invoice.patient = doc.name
        invoice.customer = "Test Patient"
        invoice.source_order = "OPD"

        # fee_item = invoice.items[0]
        # frappe.errpint(fee_item)
        # fee_item.item_code = "Registration Fee"
        # fee_item.item_name = fee_item.description = "Registration Fee"
        invoice.append(
                "items",
                {"item_code": "Registration Fee", "description": "Registration Fee" , "qty" : 1 , "rate" : rate},
            )
        # if doc.collect_registration_fee:
        invoice.is_pos = True
        invoice.append(
            "payments",
            {"mode_of_payment": get_mode_of_payment(), "amount":1},
        )
        invoice.set_missing_values()
        invoice.update_stock = 0
        set_account_for_mode_of_payment(invoice)

        invoice.flags.ignore_permissions = True
        invoice.submit()


@frappe.whitelist()
def get_mode_of_payment():
    company = frappe.defaults.get_user_default("company") or frappe.db.get_single_value(
        "Global Defaults", "default_company"
    )

    if not company:
        return

    pos_profile = get_pos_profile(company)
    if not pos_profile:
        return

    pos_profile = frappe.get_doc("POS Profile", pos_profile.get("name"))
    if not pos_profile.payments:
        return

    for payment in pos_profile.payments:
        if payment.default:
            return payment.mode_of_payment
    else:
        return pos_profile.payments[0].mode_of_payment

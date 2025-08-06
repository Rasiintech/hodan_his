from __future__ import unicode_literals
import frappe
import json
from frappe.utils import (
    today,
    format_time,
    global_date_format,
    now,
    get_first_day,
)
from frappe.utils.pdf import get_pdf
from frappe import _
from frappe.www import printview
import datetime
from frappe import publish_progress
from frappe.utils.background_jobs import enqueue as enqueue_frappe
from frappe.core.doctype.communication.email import make
from erpnext.accounts.utils import get_balance_on
from frappe.utils import getdate
from frappe.utils import now_datetime, format_datetime



@frappe.whitelist()
def get_recipient_list():
    return frappe.db.sql(
        """SELECT
								customer,
								contact,
								email_id,
								MIN(priority) AS priority,
								send_statement
							FROM
								(SELECT
									tab_cus.name AS 'customer',
									tab_con.name AS 'contact',
									tab_con.email_id,
									CASE WHEN is_customer_statement_contact = 1 THEN 1 WHEN tab_con.is_primary_contact = 1 THEN 2 ELSE 3 END AS 'priority',
									CASE WHEN tab_cus.disable_customer_statements = 1 THEN 'No (Disabled for this customer)' WHEN ISNULL(tab_con.email_id) OR tab_con.email_id = '' THEN 'No (No email address on record)' ELSE 'Yes' END AS 'send_statement'
								FROM `tabCustomer` AS tab_cus
									LEFT JOIN `tabDynamic Link` as tab_dyn ON tab_dyn.link_name = tab_cus.name AND tab_dyn.link_doctype = 'Customer' AND tab_dyn.parenttype = 'Contact'
									LEFT JOIN `tabContact` as tab_con ON tab_dyn.parent = tab_con.name
								WHERE tab_cus.disabled = 0) AS t_contacts
							GROUP BY customer
							ORDER BY customer""",
        as_dict=True,
    )


@frappe.whitelist()
def statements_sender_scheduler(manual=None):
    if manual:
        send_statements(manual=manual)
    else:
        enqueue()


def send_statements(company=None, manual=None):
    """
    Send out customer statements
    """
    show_progress = manual
    progress_title = _("Sending customer statements...")

    if show_progress:
        publish_progress(percent=0, title=progress_title)

    if company is None:
        company = frappe.db.get_single_value("Customer Statements Sender", "company")
        if not company:
            frappe.throw(_("Company field is required on Customer Statements Sender"))
            exit()

    from_date_for_all_customers = frappe.db.get_single_value(
        "Customer Statements Sender", "from_date_for_all_customers"
    )
    to_date_for_all_customers = frappe.db.get_single_value(
        "Customer Statements Sender", "to_date_for_all_customers"
    )

    email_list = get_recipient_list()
    idx = 0
    total = len(email_list)
    for row in email_list:
        idx += 1
        if row.email_id is not None and row.email_id != "":
            if row.send_statement == "Yes":
                if show_progress:
                    publish_progress(
                        percent=(idx / total * 100),
                        title=progress_title,
                        description=" Creating PDF for {0}".format(row.customer),
                    )
                send_individual_statement(
                    row.customer,
                    row.email_id,
                    company,
                    from_date_for_all_customers,
                    to_date_for_all_customers,
                )

    if show_progress:
        publish_progress(percent=100, title=progress_title)
        frappe.msgprint("Emails queued for sending")


def enqueue():
    """Add method `send_statements` to the queue."""
    enqueue_frappe(
        method=send_statements,
        queue="long",
        timeout=600000,
        is_async=True,
        job_name="send_statments",
    )

# @frappe.whitelist()
# def get_summary_statement(company, customer, from_date, to_date, account=None):
#     report_doc = frappe.get_doc("Report", "Customer Statement Summary")

#     filters = {
#         "customer": customer,
#         "from_date": from_date,
#         "to_date": to_date,
#     }

#     # Get customer name
#     customer_name = frappe.get_value("Customer", customer, "customer_name")

#     # Get customer statement summary report data
#     columns, data = report_doc.get_data(
#         limit=1000, user="Administrator", filters=filters, as_dict=True
#     )

#     date_time = format_datetime(now_datetime())
#     currency = frappe.db.get_value("Company", company, "default_currency")

#     html = frappe.render_template("his/templates/report/customer_statement_summary_template.html", {
#         "title": "Customer Statement Summary",
#         "columns": columns,
#         "data": data,
#         "filters": filters,
#         "now": date_time,
#         "currency": currency,
#         "customer_name": customer_name,  # 👈 pass to HTML template
#     })

#     return html

@frappe.whitelist()
def get_summary_statement(company, customer, from_date, to_date):
    # Normalize customer into a list if needed
    if isinstance(customer, str):
        try:
            customer = frappe.parse_json(customer)
        except Exception:
            customer = [customer]  # Wrap in list if it's just a string

    filters = {
        "company": company,
        "party": customer,
        "from_date": from_date,
        "to_date": to_date
    }

    # customer_name = frappe.db.get_value("Customer", customer[0], "customer_name","patient")
    customer_name, patient_id = frappe.db.get_value("Customer", customer[0], ["customer_name", "patient"])
    currency = frappe.db.get_value("Company", company, "default_currency")
    date_time = frappe.utils.format_datetime(frappe.utils.now_datetime())

    report_doc = frappe.get_doc("Report", "Customer Statement Summary")
    columns, data = report_doc.get_data(
        limit=1000, user="Administrator", filters=filters, as_dict=True
    )

    html = frappe.render_template("his/templates/report/customer_statement_summary_template.html", {
        "title": "Customer Statement Summary",
        "columns": columns,
        "data": data,
        "filters": filters,
        "now": date_time,
        "currency": currency,
        "customer_name": customer_name,
        "patient": patient_id,
        "from": from_date,
        "to": to_date,
    })

    return html



@frappe.whitelist()
def get_report_content( company, customer_name,cost_center = None, account = None, from_date=None, to_date=None):
    """Returns html for the report in PDF format"""

    settings_doc = frappe.get_single("Customer Statements Sender")

    if not from_date:
        from_date = get_first_day(today()).strftime("%Y-%m-%d")
    if not to_date:
        to_date = today()

    # Get General Ledger report content
    report_gl = frappe.get_doc("Report", "General Ledger")
   
    
    report_gl_filters = {
        
        "company": company,
        "party_type": "Customer",
        "party": [customer_name],
        "from_date": from_date,
        "to_date": to_date,
        "group_by": "Group by Voucher (Consolidated)",
    }
    if  account:
       report_gl_filters['account'] = [account]
    if cost_center:
       frappe.errprint(cost_center)
       report_gl_filters['cost_center'] = [cost_center]
    frappe.errprint(report_gl_filters)
    columns_gl, data_gl = report_gl.get_data(
        limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
    )

    # Add serial numbers
    columns_gl.insert(0, frappe._dict(fieldname="idx", label="", width="30px"))
    for i in range(len(data_gl)):
        data_gl[i]["idx"] = i + 1

    # Get ageing summary report content
    data_ageing = []
    labels_ageing = []
    if settings_doc.no_ageing != 1:
        report_ageing = frappe.get_doc("Report", "Accounts Receivable Summary")
        report_ageing_filters = {
            "party_account" : account,
            "company": company,
            "ageing_based_on": "Posting Date",
            "report_date": datetime.datetime.today(),
            "range1": 30,
            "range2": 60,
            "range3": 90,
            "range4": 120,
            "customer": customer_name,
        }
        columns_ageing, data_ageing = report_ageing.get_data(
            limit=50, user="Administrator", filters=report_ageing_filters, as_dict=True
        )
        labels_ageing = {}
        for col in columns_ageing:
            if "range" in col["fieldname"]:
                labels_ageing[col["fieldname"]] = col["label"]

    # Get Letter Head
    no_letterhead = bool(
        frappe.db.get_single_value("Customer Statements Sender", "no_letter_head")
    )
    letter_head = frappe._dict(
        printview.get_letter_head(settings_doc, no_letterhead) or {}
    )
    if letter_head.content:
        letter_head.content = frappe.utils.jinja.render_template(
            letter_head.content, {"doc": settings_doc.as_dict()}
        )

    # Render Template
    date_time = global_date_format(now()) + " " + format_time(now())
    currency = frappe.db.get_value("Company", company, "default_currency")
    report_html_data = frappe.render_template(
        "his/templates/report/customer_statements_jinja2.html",
        {
            "title": "Customer Statement for {0}".format(customer_name),
            "description": "Customer Statement for {0}".format(customer_name),
            "date_time": date_time,
            "columns": columns_gl,
            "data": data_gl,
            "report_name": "Customer Statement for {0}".format(customer_name),
            "filters": report_gl_filters,
            "currency": currency,
            "letter_head": letter_head.content,
            "billing_address": get_billing_address(customer_name),
            "labels_ageing": labels_ageing,
            "data_ageing": data_ageing,
        },
    )

    return report_html_data

@frappe.whitelist()
def get_report_content_2( company, supplier_name, account  = None,from_date=None, to_date=None):
    """Returns html for the report in PDF format"""

    settings_doc = frappe.get_single("Supplier Statements")

    if not from_date:
        from_date = get_first_day(today()).strftime("%Y-%m-%d")
    if not to_date:
        to_date = today()

    # Get General Ledger report content
    report_gl = frappe.get_doc("Report", "General Ledger")
   

    report_gl_filters = {
        
        "company": company,
        "party_type": "Supplier",
        "party": [supplier_name],
        "from_date": from_date,
        "to_date": to_date,
        "group_by": "Group by Voucher (Consolidated)",
    }
    if  account:
       report_gl_filters['account'] = [account]
    columns_gl, data_gl = report_gl.get_data(
        limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
    )

    # Add serial numbers
    columns_gl.insert(0, frappe._dict(fieldname="idx", label="", width="30px"))
    for i in range(len(data_gl)):
        data_gl[i]["idx"] = i + 1

    # Get ageing summary report content
    data_ageing = []
    labels_ageing = []
    if settings_doc.no_ageing != 1:
        report_ageing = frappe.get_doc("Report", "Accounts Receivable Summary")
        report_ageing_filters = {
            "party_account" : account,
            "company": company,
            "ageing_based_on": "Posting Date",
            "report_date": datetime.datetime.today(),
            "range1": 30,
            "range2": 60,
            "range3": 90,
            "range4": 120,
            "customer": supplier_name,
        }
        columns_ageing, data_ageing = report_ageing.get_data(
            limit=50, user="Administrator", filters=report_ageing_filters, as_dict=True
        )
        labels_ageing = {}
        for col in columns_ageing:
            if "range" in col["fieldname"]:
                labels_ageing[col["fieldname"]] = col["label"]

    # Get Letter Head
    no_letterhead = bool(
        frappe.db.get_single_value("Supplier Statements", "no_letter_head")
    )
    letter_head = frappe._dict(
        printview.get_letter_head(settings_doc, no_letterhead) or {}
    )
    if letter_head.content:
        letter_head.content = frappe.utils.jinja.render_template(
            letter_head.content, {"doc": settings_doc.as_dict()}
        )

    # Render Template
    date_time = global_date_format(now()) + " " + format_time(now())
    currency = frappe.db.get_value("Company", company, "default_currency")
    report_html_data = frappe.render_template(
        "his/templates/report/supplier_statements.html",
        {
            "title": "Customer Statement for {0}".format(supplier_name),
            "description": "Customer Statement for {0}".format(supplier_name),
            "date_time": date_time,
            "columns": columns_gl,
            "data": data_gl,
            "report_name": "Customer Statement for {0}".format(supplier_name),
            "filters": report_gl_filters,
            "currency": currency,
            "letter_head": letter_head.content,
            "billing_address": get_billing_address(supplier_name),
            "labels_ageing": labels_ageing,
            "data_ageing": data_ageing,
        },
    )

    return report_html_data

@frappe.whitelist()
def get_report_content_3(company, employee_name,account  = None, from_date=None, to_date=None):
    """Returns html for the report in PDF format"""

    settings_doc = frappe.get_single("Employee Statements")

    if not from_date:
        from_date = get_first_day(today()).strftime("%Y-%m-%d")
    if not to_date:
        to_date = today()

    # Get General Ledger report content
    report_gl = frappe.get_doc("Report", "General Ledger")
   

    report_gl_filters = {
        
        "company": company,
        "party_type": "Employee",
        "party": [employee_name],
        "from_date": from_date,
        "to_date": to_date,
        "group_by": "Group by Voucher (Consolidated)",
    }
    if  account:
       report_gl_filters['account'] = [account]
    columns_gl, data_gl = report_gl.get_data(
        limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
    )

    # Add serial numbers
    columns_gl.insert(0, frappe._dict(fieldname="idx", label="", width="30px"))
    for i in range(len(data_gl)):
        data_gl[i]["idx"] = i + 1

    # Get ageing summary report content
    data_ageing = []
    labels_ageing = []
    if settings_doc.no_ageing != 1:
        report_ageing = frappe.get_doc("Report", "Accounts Receivable Summary")
        report_ageing_filters = {
            "party_account" : account,
            "company": company,
            "ageing_based_on": "Posting Date",
            "report_date": datetime.datetime.today(),
            "range1": 30,
            "range2": 60,
            "range3": 90,
            "range4": 120,
            "customer": employee_name,
        }
        columns_ageing, data_ageing = report_ageing.get_data(
            limit=50, user="Administrator", filters=report_ageing_filters, as_dict=True
        )
        labels_ageing = {}
        for col in columns_ageing:
            if "range" in col["fieldname"]:
                labels_ageing[col["fieldname"]] = col["label"]

    # Get Letter Head
    no_letterhead = bool(
        frappe.db.get_single_value("Employee Statements", "no_letter_head")
    )
    letter_head = frappe._dict(
        printview.get_letter_head(settings_doc, no_letterhead) or {}
    )
    if letter_head.content:
        letter_head.content = frappe.utils.jinja.render_template(
            letter_head.content, {"doc": settings_doc.as_dict()}
        )

    # Render Template
    date_time = global_date_format(now()) + " " + format_time(now())
    currency = frappe.db.get_value("Company", company, "default_currency")
    report_html_data = frappe.render_template(
        "his/templates/report/employee_statements.html",
        {
            "title": "Customer Statement for {0}".format(employee_name),
            "description": "Customer Statement for {0}".format(employee_name),
            "date_time": date_time,
            "columns": columns_gl,
            "data": data_gl,
            "report_name": "Customer Statement for {0}".format(employee_name),
            "filters": report_gl_filters,
            "currency": currency,
            "letter_head": letter_head.content,
            "billing_address": get_billing_address(employee_name),
            "labels_ageing": labels_ageing,
            "data_ageing": data_ageing,
        },
    )

    return report_html_data


def get_file_name():
    return "{0}.{1}".format(
        "Customer Statement".replace(" ", "-").replace("/", "-"), "pdf"
    )


def get_billing_address(customer):
	filters = {
		'customer_name': customer
	}
	addresses = frappe.db.sql("""SELECT
								customer,
								MAX(priority) AS preferred_address,
								address_line1,
								address_line2,
								city,
								county,
								state,
								country,
								postal_code
							FROM
								(SELECT
										tab_cus.name AS 'customer',
										tab_add.name AS 'address_title',
										IFNULL(tab_add.is_primary_address, 0) AS 'priority',
										tab_add.address_line1,
										tab_add.address_line2,
										city,
										county,
										state,
										country,
										pincode AS 'postal_code'
									FROM `tabCustomer` AS tab_cus
										INNER JOIN `tabDynamic Link` as tab_dyn ON tab_dyn.link_name = tab_cus.name AND tab_dyn.link_doctype = 'Customer'
										INNER JOIN `tabAddress` as tab_add ON tab_dyn.parent = tab_add.name AND tab_dyn.parenttype = 'Address'
									WHERE tab_cus.name = %(customer_name)s AND tab_add.address_type = 'Billing') AS t_billing_add
							GROUP BY customer""", filters, True)
	if addresses and len(addresses)>0:
		del(addresses[0]['preferred_address'])
		return addresses[0]
	else:
		return {}

@frappe.whitelist()
def frappe_format_value(value, df=None, doc=None, currency=None, translated=False):
    from frappe.utils.formatters import format_value

    return format_value(value, df, doc, currency, translated)


@frappe.whitelist()
def send_individual_statement(customer, email_id, company, from_date, to_date):
    data = get_report_content(
        company,
        customer,
        from_date=from_date,
        to_date=to_date,
    )
    # Get PDF Data
    pdf_data = get_pdf(data)
    if not pdf_data:
        return

    attachments = [{"fname": get_file_name(), "fcontent": pdf_data}]

    if email_id == "to_find":
        email_id = frappe.get_value("Customer", customer, "email_id")
    make(
        recipients=email_id,
        send_email=True,
        subject="Customer Statement from {0}".format(company),
        content="Good day. <br> Please find attached your latest statement from {0}".format(
            company
        ),
        attachments=attachments,
        doctype="Report",
        name="General Ledger",
    )



@frappe.whitelist()
# def patient_clearance(patient):
#     cost_centers = frappe.get_all("Cost Center", filters={"is_group": 0}, pluck="name")
#     receivables = []

#     for center in cost_centers:
#         report_gl_filters = {
#             "company": frappe.defaults.get_user_default("Company"),
#             "posting_date": "Today",
#             "cost_center": [center],
#             "party_type": "Customer",
#             "party": [frappe.db.get_value('Patient', patient, 'customer')],
#             "from_date"  : frappe.utils.getdate("2000-01-01"),
#             "to_date" : frappe.utils.getdate()
#         }

#         report_gl = frappe.get_doc("Report", "General Ledger")
#         # report_gl_filters = report_gl.get_filter_values(filters)

#         columns_gl, data_gl = report_gl.get_data(
#             limit=500, user="Administrator", filters=report_gl_filters, as_dict=True
#         )

#         if data_gl:
#             balance = data_gl[0].balance
#             receivables.append({"cost_center": center, "amount": balance})

#     return receivables


@frappe.whitelist()
def patient_clearance(**args):
    cost_center=frappe.db.sql(""" select name from `tabCost Center` where is_group not in (1)""",as_dict=True)
    bl=[]
    for center in cost_center:

        report_re = frappe.get_doc("Report", "Accounts Receivable Summary")
        customer= frappe.db.get_value('Patient', args.get("patient"),'customer')
        
        report_re_filters = {
            
            "company": frappe.defaults.get_user_default("company"),
            # "party_type": "Customer",
            "cost_center": center.name,
            "customer": customer,
            "range1": 30,
            "range2": 60,
            "range3": 90,
            "range4": 120,

        }

        columns_re, data_re = report_re.get_data(
            limit=500, user="Administrator", filters=report_re_filters, as_dict=True
        )
        if data_re:
            bl.append({
            "cost_center": center.name,
            "amount": data_re[0].outstanding
            })
    return bl


# ---------------------------------print consents-------------------------
@frappe.whitelist()
def get_print_html(patient,clinical_procedure):

    report_html_data = frappe.render_template(
        "his/templates/report/consent.html",
        {
            "patient": patient,
            "clinical_procedure": clinical_procedure,
   
        },
    )

    return report_html_data



@frappe.whitelist()
def item_wise(customer , from_date ,to_date ,customer_name , detail = 1):
    # customer_name = frappe.db.get_value("Customer",customer,"customer_name")
    frappe.errprint(customer_name)

     # Get Letter Head
   
    # no_letterhead = bool(
    #     frappe.db.get_single_value("Customer Statements", "no_letter_head")
    # )
    # letter_head = frappe._dict(
    #     printview.get_letter_head(settings_doc, no_letterhead) or {}
    # )
    # if letter_head.content:
    #     letter_head.content = frappe.utils.jinja.render_template(
    #         letter_head.content, {"doc": settings_doc.as_dict()}
    #     )
    report_gl = frappe.get_doc("Report", "Item-wise Sales Register")

    report_item_wise = {
             "company": frappe.db.get_single_value("Customer Statements Sender", "company"),
             "customer" : customer,
            "from_date": from_date,
             "to_date": to_date,
            "group_by":"Item Group"  }
    col ,data_gl = report_gl.get_data(
           limit=500, user="Administrator", filters=report_item_wise, as_dict=True
         )
    l = []
    payment= []
    l_in = 0
    for index , i in enumerate(data_gl):
         if i == {}:
             frappe.errprint(index)
             if len(l) == 0:
                 l.append(data_gl[:index])
                 l_in = index
             else:
                 l.append(data_gl[l_in:index])
                 l_in = index
            #  print("\n\n\n" , l ,"\n\n\n")
    total_invoice= 0
    for t in l:
        total_invoice = total_invoice + t[-1].amount
        # frappe.errprint(t[-1].amount )
        
        # frappe.errprint(t)
    pay= frappe.db.get_list("Payment Entry", filters={'docstatus': ['=', 1] ,"posting_date": ["between", [from_date, to_date]], "party": customer}, fields=["name", "unallocated_amount","posting_date", "party", "paid_amount" ,"unallocated_amount"])
    total_receipt = 0
    for row in pay:
        # frappe.errprint()
        # payment_doc = 
        total_receipt = total_receipt+ row.unallocated_amount

    # frappe.errprint(total_receipt)
    # print("\n\n" , l ,"\n\n\n")
    net_total = get_balance_on(company = frappe.defaults.get_user_default("Company"),
						party_type ="Customer",
						party = customer,
						date = getdate())
    # for paid_sales in l:        
    paid_list = frappe.get_list("Sales Invoice", filters={'docstatus': ['=', 1] ,"customer": customer , 'paid_amount': ['>', 0] , "posting_date": ["between", [from_date, to_date]] }, fields=["docstatus","name", "customer", "posting_date", "paid_amount"])
    # frappe.errprint(paid_list)
    for inv in paid_list:
        total_receipt = total_receipt+ inv.paid_amount
    group_runign= 0
    for  group in l:
        running = 0
        group_runign = group_runign + group[-1].amount
        group[-1]['grunning'] = group_runign
        for i in group:
            if i.amount:
                running = running + i.amount or running
            i['running'] = running

    # frappe.msgprint(detail)
    report_html_data = frappe.render_template(
        "his/templates/report/customer_statement.html",
        {
            "data" : l ,
            "customer": customer,
            "customer_name": customer_name,
            "from" : from_date,
            "to" : to_date,
            "payments" : pay,
            "paid_invoices" : paid_list,
            "total_invoice" : total_invoice, 
            "total_recipt" : total_receipt,
            "net_total" : net_total,
            "detail" : int(detail)
            # "letter_head" :letter_head.content,

        }
     )
    return report_html_data

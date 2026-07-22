import frappe

@frappe.whitelist()
def employee_due(doc, method = None):
    abbr = frappe.db.get_value("Company", frappe.defaults.get_user_default("company"), "abbr")
    his_settings = frappe.get_doc("HIS Settings", "HIS Settings")
    if his_settings.allow_bill_to_employee:
        if doc.bill_to_employee:
           
            account = [
                            {
                            "account":his_settings.employee_due,
                            "party_type" : "Employee",
                            "party":  doc.employee,
                            "debit_in_account_currency":doc.net_total,
                            "source_order" : doc.source_order,
                            },
                            {
                            "account": "4110 - Sales - "+ abbr,
                            "credit_in_account_currency":doc.net_total,
                            "source_order" : doc.source_order,
                            },
                            ]
            journal = frappe.get_doc({
                                        'doctype': 'Journal Entry',
                                        'voucher_type': 'Journal Entry',
                                        "posting_date" : doc.posting_date,
                                        # "user_remark":"Doctor Commission",
                                        "accounts": account,
                                        "sales_invoice": doc.name
                                        
                                        })
            journal.insert(ignore_permissions = True)
            journal.submit()
            doc.journal_entry = journal.name


@frappe.whitelist()
def transfer_balance(posting_date,amount,from_c, to):
    abbr = frappe.db.get_value("Company", frappe.defaults.get_user_default("company"), "abbr")
    his_settings = frappe.get_doc("HIS Settings", "HIS Settings")
    if not his_settings.allow_transfer_balance:
         frappe.throw("Trasfter Balance its not allowed in HIS Settings")
    if his_settings.allow_transfer_balance:
        
            account = [
                            {
                            "account":"1310 - Debtors - "+abbr,
                            "party_type" : "Customer",
                            "party": to,
                            "debit_in_account_currency":amount,
                            },
                            {
                            "account": "1310 - Debtors - "+ abbr,
                            "party_type" : "Customer",
                            "party": from_c,
                            "credit_in_account_currency":amount,
                            },
                            ]
            journal = frappe.get_doc({
                                        'doctype': 'Journal Entry',
                                        'voucher_type': 'Journal Entry',
                                        "posting_date" : posting_date,
                                        # "user_remark":"Doctor Commission",
                                        "accounts": account,
                                        
                                        })
            journal.insert(ignore_permissions = True)
            journal.submit()


@frappe.whitelist()
def insurance(doc, method=None):
    if doc.is_insurance:
        Journal = frappe.get_doc({
        "doctype" : "Journal Entry",
        "posting_date": doc.posting_date,
        "sales_invoice": doc.name,
    
        "source_order": "OPD",
        "accounts": [{
        "account": doc.debit_to,
        "party_type": "Customer",
        "party" : frappe.db.get_value("Patient", doc.patient,"ref_insturance"),
        "debit_in_account_currency": doc.net_total,
        "doctype": "Journal Entry Account"
    
    
            },
            {
        "account": doc.debit_to,
        "party_type": "Customer",
        "party" : doc.customer,
        "credit_in_account_currency": doc.net_total,
        "doctype": "Journal Entry Account"
        
    
            }]
    
        })
    
        
        Journal.insert(ignore_permissions = True)
        Journal.submit()
        doc.journal_entry = Journal.name
    
        doc.save()



@frappe.whitelist()
def free_que_expense(doc, method = None):
    abbr = frappe.db.get_value("Company", frappe.defaults.get_user_default("company"), "abbr")
    his_settings = frappe.get_doc("HIS Settings", "HIS Settings")
    if his_settings.free_que_expense:
        if doc.is_free:
            account = [
                            
                            
                            {
                            "account":his_settings.free_que_expense_account,
                            "debit_in_account_currency":doc.net_total,
                            "source_order" : doc.source_order,
                            },
                            {
                            "account": "1310 - Debtors - "+ abbr,
                            "credit_in_account_currency":doc.net_total,
                            "party_type" : "Customer",
                            "party":  doc.customer,
                            "source_order" : doc.source_order,
                            },
                            ]
            journal = frappe.get_doc({
                                        'doctype': 'Journal Entry',
                                        'voucher_type': 'Journal Entry',
                                        "posting_date" : doc.posting_date,
                                        # "user_remark":"Doctor Commission",
                                        "accounts": account,
                                        "sales_invoice": doc.name
                                        
                                        })
            journal.insert(ignore_permissions = True)
            journal.submit()
            doc.journal_entry = journal.name
            doc.save()

@frappe.whitelist()
def cancell_journal(doc , method = None):
    # frappe.msgprint(str(doc.journal_entry))
    if doc.journal_entry:
        if frappe.db.exists("Journal Entry" , {"sales_invoice" : doc.name , "docstatus" : 1}):
            journ_name = frappe.db.get_value("Journal Entry" , {"sales_invoice" : doc.name , "docstatus" : 1})
            jour = frappe.get_doc("Journal Entry" ,journ_name)
            if jour.docstatus ==1 :
                jour.cancelled_from = "Sales Invoice"
                jour.save("update")
                jour.reload()
                jour.cancel()

@frappe.whitelist()
def cancell_sales_invoice(doc , method = None):
    # frappe.msgprint(str(doc.journal_entry))
    # if doc.doctype == "Journal Entry":
    if doc.cancelled_from != "Sales Invoice":
        if doc.sales_invoice:
            if frappe.db.exists("Sales Invoice" , doc.sales_invoice):
                sales = frappe.get_doc("Sales Invoice" , doc.sales_invoice)
                frappe.throw(f"This Journal Entry Is Linked with Sales Invoice <strong><a href = '/app/sales-invoice/{sales.name}' >{sales.name}</a></strong> Please Cancel Sales Invoice Instead")


def validate_finance_approval(doc, method=None):
    if not requires_finance_approval(doc):
        return

    user_roles = set(frappe.get_roles(frappe.session.user))
    allowed_roles = {"CFO"}

    if user_roles.intersection(allowed_roles):
        return

    frappe.throw(
        _(
            "CFO approval is required before submitting this Journal Entry because it includes an Expense account against a Cash or Bank account."
        )
    )


def requires_finance_approval(doc):
    account_names = [row.account for row in doc.accounts if row.account]
    if not account_names:
        return False

    account_types = frappe.get_all(
        "Account",
        filters={"name": ["in", account_names]},
        fields=["name", "account_type", "root_type"],
        limit_page_length=0,
    )

    account_map = {row.name: row for row in account_types}

    has_expense = False
    has_cash_or_bank = False
    has_discount_account = False

    for row in doc.accounts:
        account = account_map.get(row.account)
        if not account:
            continue

        # Discount account always requires CFO approval
        if row.account == "Discount - HH":
            has_discount_account = True

        if account.root_type == "Expense":
            has_expense = True

        if account.account_type in ("Cash", "Bank"):
            has_cash_or_bank = True

    return has_discount_account or (has_expense and has_cash_or_bank)
import frappe

@frappe.whitelist()
def get_last_doc(doc):
    try:
        # frappe.get_last_doc("Task")
        docs = frappe.get_last_doc(doc)
        return docs.voucher_no
    except:
        return 1

@frappe.whitelist()
def get_last_leave(doc,docname):
    # leave = frappe.db.get_value(doc, filters={'employee': docname},
    #                             fieldname='to_date', order_by='creation DESC', as_dict=True)

    
    # return leave.get('to_date') if leave else 1
    # leave = frappe.db.get_value('Leaves Assignment',
    #                         filters={'employee': docname},
    #                         fieldname=['leave_type', 'to_date'],
    #                         order_by='creation DESC',
    #                         as_dict=True)

    # leave_info = {
    #     'leave_type': leave.get('leave_type') if leave else 0,
    #     'to_date': leave.get('to_date') if leave else 0
    # }

    # return leave_info.leave_type and leave_info.to_date if leave_info else 1 

    leave_assignment = frappe.get_all(doc,
                                filters={'employee': docname},
                                fields=['leave_type', 'to_date'],
                                order_by='creation DESC',
                                limit=1)

    if leave_assignment:
        last_leave = leave_assignment[0]
        leave_type = last_leave.get('leave_type')
        to_date = last_leave.get('to_date')
    else:
        leave_type = None
        to_date = None

    return {
        'leave_type': leave_type,
        'to_date': to_date
    }



    try:
        # frappe.get_last_doc("Task")
        docs = frappe.get_doc(doc, leave)
        return docs.to_date
    except:
        return 1
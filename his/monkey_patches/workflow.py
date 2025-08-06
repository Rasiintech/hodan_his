# import frappe
# from frappe.model import workflow
# from his.utils import get_allowed_discount

# old_get_workflow_safe_globals = workflow.get_workflow_safe_globals


# def get_workflow_safe_globals():
#     frappe.msgprint("called called")
#     safe_globals = old_get_workflow_safe_globals()
#     safe_globals["get_allowed_discount"] = get_allowed_discount
#     return safe_globals


# workflow.get_workflow_safe_globals = get_workflow_safe_globals





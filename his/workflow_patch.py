"""HIS extensions for Frappe workflow condition evaluation."""

from frappe.model import workflow

from his.utils import get_allowed_discount


_original_get_workflow_safe_globals = workflow.get_workflow_safe_globals


def get_workflow_safe_globals():
    safe_globals = _original_get_workflow_safe_globals()
    safe_globals["get_allowed_discount"] = get_allowed_discount
    return safe_globals


get_workflow_safe_globals._his_discount_patch = True

if not getattr(workflow.get_workflow_safe_globals, "_his_discount_patch", False):
    workflow.get_workflow_safe_globals = get_workflow_safe_globals

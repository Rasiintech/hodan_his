# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries


class FacilityIncidentManagement(Document):
    def autoname(self):
        self.name = "FIM-" + getseries("FIM-", 4)

    def validate(self):
        if self.status != "Close":
            self.closing_time = None

    def before_submit(self):
        if self.status != "Close" or not self.closing_time:
            frappe.throw(_("Status must be Close and Closing Time must be entered before submission."))

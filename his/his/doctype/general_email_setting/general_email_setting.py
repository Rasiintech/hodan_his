# Copyright (c) 2026, Rasiin Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_url_to_form


class GeneralEmailSetting(Document):
	def validate(self):
		existing = frappe.db.get_value(
			"General Email Setting",
			{
				"document": self.document,
				"doctype_event": self.doctype_event,
				"name": ["!=", self.name],
			},
			"name",
		)
		if existing:
			frappe.throw(
				_("General Email Setting {0} already exists for {1} on {2}.").format(
					existing, self.document, self.doctype_event
				)
			)


def send_configured_doctype_email(doc, doctype_event):
	settings = frappe.get_all(
		"General Email Setting",
		filters={
			"enabled": 1,
			"document": doc.doctype,
			"doctype_event": doctype_event,
		},
		fields=["name"],
	)
	if not settings:
		return

	recipients = []
	for setting in settings:
		setting_doc = frappe.get_doc("General Email Setting", setting.name)
		recipients.extend(
			[row.recipient.strip() for row in setting_doc.recipients if row.recipient and row.recipient.strip()]
		)

	recipients = sorted(set(recipients))
	if not recipients:
		return

	subject = _("{0} submitted: {1}").format(doc.doctype, doc.name)
	if doc.doctype == "Department Audit":
		subject = _("Department Audit submitted: {0}").format(doc.department or doc.name)

	message = build_doctype_event_message(doc, doctype_event)
	attachments = get_doctype_email_attachments(doc)
	frappe.sendmail(
		recipients=recipients,
		subject=subject,
		message=message,
		attachments=attachments,
	)


def build_doctype_event_message(doc, doctype_event):
	doc_link = get_url_to_form(doc.doctype, doc.name)
	lines = [
		_("<p>A <strong>{0}</strong> document triggered <strong>{1}</strong>.</p>").format(
			doc.doctype, doctype_event
		),
		_("<p><strong>Document:</strong> <a href=\"{0}\">{1}</a></p>").format(doc_link, doc.name),
	]

	if doc.doctype == "Department Audit":
		lines.extend(
			[
				_("<p><strong>Department:</strong> {0}</p>").format(doc.department or ""),
				_("<p><strong>Date:</strong> {0}</p>").format(doc.date or ""),
				_("<p><strong>Frequency:</strong> {0}</p>").format(doc.frequency or ""),
				_("<p><strong>Total Tasks:</strong> {0}</p>").format(len(doc.items or [])),
			]
		)

		pending = sum(1 for row in doc.items if row.status == "Pending")
		done = sum(1 for row in doc.items if row.status == "Done")
		na = sum(1 for row in doc.items if row.status == "N/A")
		lines.append(
			_("<p><strong>Status Summary:</strong> Pending {0}, Done {1}, N/A {2}</p>").format(
				pending, done, na
			)
		)

	return "".join(lines)


def get_doctype_email_attachments(doc):
	if doc.doctype != "Department Audit":
		return None

	return [
		frappe.attach_print(
			doc.doctype,
			doc.name,
			print_format="Department Audit Overview Print",
			file_name=_("Department Audit {0}").format(doc.name),
			doc=doc,
		)
	]

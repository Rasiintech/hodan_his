function set_reference_sales_type(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (frm.doc.docstatus !== 0 || row.reference_doctype !== 'Sales Invoice' || !row.reference_name) {
		if (frm.doc.docstatus === 0 && row.sales_type) {
			frappe.model.set_value(cdt, cdn, 'sales_type', null);
		}
		return;
	}

	frappe.db.get_value('Sales Invoice', row.reference_name, 'so_type').then((response) => {
		const currentRow = locals[cdt] && locals[cdt][cdn];
		if (!currentRow || currentRow.reference_name !== row.reference_name) return;
		frappe.model.set_value(cdt, cdn, 'sales_type', response.message?.so_type || null);
	});
}

function populate_reference_sales_types(frm) {
	const invoiceRows = (frm.doc.references || []).filter((row) =>
		row.reference_doctype === 'Sales Invoice' && row.reference_name
	);
	if (!invoiceRows.length) return Promise.resolve();

	const invoiceNames = [...new Set(invoiceRows.map((row) => row.reference_name))];
	return frappe.db.get_list('Sales Invoice', {
		filters: {name: ['in', invoiceNames]},
		fields: ['name', 'so_type'],
		limit: invoiceNames.length
	}).then((invoices) => {
		const salesTypes = Object.fromEntries(invoices.map((invoice) => [invoice.name, invoice.so_type]));
		return Promise.all(invoiceRows.map((row) =>
			frappe.model.set_value(row.doctype, row.name, 'sales_type', salesTypes[row.reference_name] || null)
		));
	});
}

function wrap_outstanding_invoice_fetch(frm) {
	if (frm.__sales_type_fetch_wrapped || !frm.events.get_outstanding_documents) return;

	const getOutstandingDocuments = frm.events.get_outstanding_documents;
	frm.events.get_outstanding_documents = function (...args) {
		const request = getOutstandingDocuments.apply(this, args);
		if (request && typeof request.then === 'function') {
			return request.then((result) => populate_reference_sales_types(frm).then(() => result));
		}
		return request;
	};
	frm.__sales_type_fetch_wrapped = true;
}

// frappe.ui.form.on('Payment Entry', {
// 	refresh(frm) {
// 		wrap_outstanding_invoice_fetch(frm);
// 		if (frm.doc.docstatus !== 0) return;
// 		populate_reference_sales_types(frm);
// 	}
// });

// frappe.ui.form.on('Payment Entry Reference', {
// 	reference_doctype: set_reference_sales_type,
// 	reference_name: set_reference_sales_type
// });

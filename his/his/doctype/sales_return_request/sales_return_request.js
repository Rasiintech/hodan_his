frappe.ui.form.on('Sales Return Request', {
    setup(frm) {
        lock_items_grid(frm);
    },

    onload(frm) {
        lock_items_grid(frm);

        if (frm.is_new() && frm.doc.sales_invoice) {
            fetch_invoice_summary(frm);
        }
    },

    refresh(frm) {
        lock_items_grid(frm);

        if (frm.doc.sales_invoice && frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Get Invoice Items'), () => {
                load_invoice_items(frm);
            });
        }

        if (
            frm.doc.workflow_state === 'Approved' &&
            !frm.doc.return_sales_invoice &&
            has_cashier_role()
        ) {
            frm.add_custom_button(__('Create Return Invoice'), () => {
                frappe.call({
                    method: 'his.his.doctype.sales_return_request.sales_return_request.create_return_invoice',
                    args: { docname: frm.doc.name },
                    freeze: true,
                    callback(r) {
                        if (r.message) {
                            frappe.msgprint(__('Return Sales Invoice created: {0}', [r.message]));
                            frm.reload_doc();
                        }
                    }
                });
            }).addClass('btn-primary');
        }
    },

    sales_invoice(frm) {
        if (!frm.doc.sales_invoice) {
            reset_invoice_data(frm);
            return;
        }

        fetch_invoice_summary(frm);
        load_invoice_items(frm);
    },

    requested_amount(frm) {
        validate_requested_amount(frm);
    }
});

frappe.ui.form.on('Sales Return Request Item', {
    returned_qty(frm, cdt, cdn) {
        update_row_return_amount(cdt, cdn);
        update_requested_amount(frm);
    },
    return_amount(frm) {
        update_requested_amount(frm);
    },
    items_remove(frm) {
        schedule_requested_amount_refresh(frm);
    },
    items_delete(frm) {
        schedule_requested_amount_refresh(frm);
    }
});

function update_requested_amount(frm) {
    let total = 0;
    (frm.doc.items || []).forEach(d => {
        total += flt(d.return_amount);
    });
    frm.set_value('requested_amount', total);
    validate_requested_amount(frm);
}

function schedule_requested_amount_refresh(frm) {
    setTimeout(() => {
        update_requested_amount(frm);
    }, 0);
}

function has_cashier_role() {
    return frappe.user.has_role('Cashier');
}

function lock_items_grid(frm) {
    const grid = frm.get_field('items') && frm.get_field('items').grid;
    if (!grid) {
        return;
    }

    grid.df.cannot_add_rows = true;
    grid.df.cannot_delete_rows = false;
    grid.cannot_add_rows = true;
    grid.cannot_delete_rows = false;
    frm.refresh_field('items');

    setTimeout(() => {
        const wrapper = grid.wrapper;
        wrapper.find('.grid-add-row, .grid-append-row, .grid-insert-row, [data-action="add_row"]').hide();
        wrapper.find('.grid-remove-rows, [data-action="delete_rows"]').show();
        wrapper.find('.grid-delete-row, .grid-remove-row, .row-actions .grid-delete-row, .row-actions .grid-remove-row').show();
        wrapper.find('.form-in-grid .btn-danger, .grid-row-open .btn-danger').show();
    }, 0);
}

function validate_requested_amount(frm) {
    if (flt(frm.doc.balance_refundable) && flt(frm.doc.requested_amount) > flt(frm.doc.balance_refundable)) {
        frappe.msgprint(__('Requested Amount cannot exceed Balance Refundable'));
        frm.set_value('requested_amount', frm.doc.balance_refundable);
    }
}

function reset_invoice_data(frm) {
    frm.clear_table('items');
    frm.refresh_field('items');

    [
        'company',
        'customer',
        'currency',
        'sales_invoice_date',
        'patient',
        'patient_name',
        'invoice_net_total',
        'invoice_additional_discount_percentage',
        'invoice_discount_amount',
        'invoice_grand_total',
        'invoice_paid_amount',
        'invoice_outstanding_amount',
        'already_refunded_amount',
        'eligible_refund_amount',
        'balance_refundable',
        'is_insurance',
        'insurance',
        'insurance_id',
        'insurance_policy',
        'insurance_company',
        'policy_number',
        'policyholder_name',
        'coverage_limits',
        'expiry_date',
        'insurance_coverage_amount',
        'insurance_paid',
        'is_claimed',
    ].forEach((fieldname) => frm.set_value(fieldname, null));

    frm.set_value('requested_amount', 0);
}

function fetch_invoice_summary(frm) {
    if (!frm.doc.sales_invoice) {
        return;
    }

    frappe.call({
        method: 'his.his.doctype.sales_return_request.sales_return_request.get_invoice_summary',
        args: { sales_invoice: frm.doc.sales_invoice },
        freeze: true,
        freeze_message: __('Loading invoice details...'),
        callback(r) {
            const data = r.message || {};
            Object.keys(data).forEach((fieldname) => {
                if (fieldname in frm.doc) {
                    frm.set_value(fieldname, data[fieldname]);
                }
            });
        }
    });
}

function load_invoice_items(frm) {
    if (!frm.doc.sales_invoice) {
        return;
    }

    frappe.call({
        method: 'his.his.doctype.sales_return_request.sales_return_request.get_invoice_items',
        args: {
            sales_invoice: frm.doc.sales_invoice,
            reference_doctype: frm.doc.reference_doctype,
            reference_name: frm.doc.reference_name
        },
        freeze: true,
        freeze_message: __('Loading Sales Invoice items...'),
        callback(r) {
            frm.clear_table('items');

            (r.message || []).forEach(row => {
                let d = frm.add_child('items');
                Object.assign(d, row);
            });

            frm.refresh_field('items');
            update_requested_amount(frm);
        }
    });
}

function update_row_return_amount(cdt, cdn) {
    const row = locals[cdt] && locals[cdt][cdn];
    if (!row || !flt(row.qty)) {
        return;
    }

    const unit_return_amount = flt(row.max_return_amount) / flt(row.qty);
    frappe.model.set_value(cdt, cdn, 'return_amount', unit_return_amount * flt(row.returned_qty));
}

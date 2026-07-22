// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Supplier Payment Plan', {
	setup(frm) {
		frm.set_query('supplier', 'payment_schedule', () => {
			return {
				filters: {
					disabled: 0
				}
			};
		});
	},

	refresh(frm) {
		if (frm.is_new() && !frm.doc.plan_date) {
			frm.set_value('plan_date', frappe.datetime.now_date());
		}

		if (frm.is_new() && !frm.doc.plan_month) {
			sync_plan_month_from_date(frm);
		}

		frm.set_intro(__('Create one monthly supplier plan and allocate plan amounts across all suppliers with outstanding balances.'), 'blue');
		update_totals(frm);

		if (frm.doc.company) {
			frm.add_custom_button(__('Load Suppliers'), () => load_suppliers(frm), __('Actions'));
		}
	},

	company(frm) {
		update_totals(frm);
	},

	plan_month(frm) {
		sync_date_range_from_month(frm);
		update_totals(frm);
	},

	plan_date(frm) {
		sync_plan_month_from_date(frm);
		update_totals(frm);
	},

	payment_schedule_remove(frm) {
		update_totals(frm);
	},

	validate(frm) {
		update_totals(frm);
	}
});

frappe.ui.form.on('Supplier Payment Plan Item', {
	supplier(frm, cdt, cdn) {
		refresh_row_balance(frm, cdt, cdn);
	},

	payment_amount(frm) {
		update_totals(frm);
	}
});

function load_suppliers(frm) {
	if (!frm.doc.company) {
		frappe.msgprint(__('Select Company first.'));
		return;
	}

	frappe.call({
		method: 'his.his.doctype.supplier_payment_plan.supplier_payment_plan.get_supplier_plan_rows',
		args: {
			company: frm.doc.company,
			date: frm.doc.plan_date || frappe.datetime.now_date()
		},
		callback: function(r) {
			if (!r.message) {
				return;
			}

			frm.clear_table('payment_schedule');

			(r.message || []).forEach((row) => {
				const child = frm.add_child('payment_schedule');
				child.supplier = row.supplier;
				child.balance_amount = row.balance_amount;
				child.last_month_credited = row.last_month_credited;
				child.payment_amount = row.payment_amount;
				child.balance_after_payment = row.balance_after_payment;
				child.payment_date = frm.doc.plan_date;
			});

			frm.refresh_field('payment_schedule');
			update_totals(frm);
			frappe.show_alert({
				message: __('Supplier balances loaded.'),
				indicator: 'green'
			});
		}
	});
}

function refresh_row_balance(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row.supplier || !frm.doc.company) {
		return;
	}

	frappe.call({
		method: 'his.his.doctype.supplier_payment_plan.supplier_payment_plan.get_supplier_outstanding_amount',
		args: {
			supplier: row.supplier,
			company: frm.doc.company,
			date: frm.doc.plan_date
		},
		callback: function(r) {
			if (r.message === undefined) {
				return;
			}

			frappe.model.set_value(cdt, cdn, 'balance_amount', r.message);

			frappe.call({
				method: 'his.his.doctype.supplier_payment_plan.supplier_payment_plan.get_last_month_credited',
				args: {
					supplier: row.supplier,
					company: frm.doc.company,
					plan_date: frm.doc.plan_date
				},
				callback: function(creditResponse) {
					if (creditResponse.message !== undefined) {
						frappe.model.set_value(cdt, cdn, 'last_month_credited', creditResponse.message);
					}

					update_totals(frm);
				}
			});
		}
	});
}

function update_totals(frm) {
	(frm.doc.payment_schedule || []).forEach((row) => {
		row.balance_after_payment = flt(row.balance_amount) - flt(row.payment_amount);
		if (!row.payment_date && frm.doc.plan_date) {
			row.payment_date = frm.doc.plan_date;
		}
	});

	frm.refresh_field('payment_schedule');

	const totalBalance = (frm.doc.payment_schedule || []).reduce((sum, row) => sum + flt(row.balance_amount), 0);
	const totalPlan = (frm.doc.payment_schedule || []).reduce((sum, row) => sum + flt(row.payment_amount), 0);

	frm.set_value('total_amount', totalBalance);
	frm.set_value('total_scheduled_amount', totalPlan);
	frm.set_value('balance_amount', totalBalance - totalPlan);
}

function sync_plan_month_from_date(frm) {
	if (!frm.doc.plan_date) {
		return;
	}

	const dateObject = frappe.datetime.str_to_obj(frm.doc.plan_date);
	const monthLabel = dateObject.toLocaleString('default', { month: 'long' });

	frm.set_value('plan_month', monthLabel);
}

function sync_date_range_from_month(frm) {
	if (!frm.doc.plan_month) {
		return;
	}

	const monthNames = [
		'January',
		'February',
		'March',
		'April',
		'May',
		'June',
		'July',
		'August',
		'September',
		'October',
		'November',
		'December'
	];

	const monthIndex = monthNames.indexOf(frm.doc.plan_month);
	if (monthIndex === -1) {
		return;
	}

	let year = new Date().getFullYear();
	if (frm.doc.plan_date) {
		const existingDate = frappe.datetime.str_to_obj(frm.doc.plan_date);
		if (existingDate instanceof Date && !Number.isNaN(existingDate.getTime())) {
			year = existingDate.getFullYear();
		}
	}

	const monthStart = new Date(year, monthIndex, 1);
	const monthEnd = new Date(year, monthIndex + 1, 0);

	frm.set_value('plan_date', frappe.datetime.obj_to_str(monthStart));
	frm.set_value('to_date', frappe.datetime.obj_to_str(monthEnd));
}

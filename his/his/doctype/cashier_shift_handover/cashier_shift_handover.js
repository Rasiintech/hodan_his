frappe.ui.form.on("Cashier Shift Handover", {
	setup(frm) {
		frm.set_query("cashier", () => ({
			filters: { disabled: 0, ...(frm.doc.company ? { company: frm.doc.company } : {}) },
		}));
	},
	refresh(frm) {
		if (frm.is_new() && !frm.doc.company) {
			frm.set_value("company", frappe.defaults.get_user_default("Company"));
		}
		if (frm.is_new() && !frm.doc.cashier) {
			frappe
				.xcall("his.his.doctype.cashier_shift_handover.cashier_shift_handover.get_user_pos_profile", {
					company: frm.doc.company,
				})
				.then((profile) => profile && frm.set_value("cashier", profile));
		}
	},
	cashier(frm) {
		frm.set_value("cashier_name", frm.doc.cashier || "");
		update_account_details(frm);
	},
	company: update_account_details,
	posting_date: update_account_details,
	cash_collections_remove: update_totals,
	cash_available_remove: update_totals,
	merchant_withdrawals_remove: update_totals,
});

function update_account_details(frm) {
	if (frm.doc.docstatus !== 0) return;
	frappe
		.xcall("his.his.doctype.cashier_shift_handover.cashier_shift_handover.get_cashier_account_details", {
			cashier: frm.doc.cashier,
			company: frm.doc.company,
			posting_date: frm.doc.posting_date,
		})
		.then((details) => frm.set_value(details));
}

function update_totals(frm) {
	const sum = (rows, field) => (rows || []).reduce((total, row) => total + flt(row[field]), 0);
	const opening = sum(frm.doc.cash_collections, "opening_balance");
	const collection = sum(frm.doc.cash_collections, "collection_today");
	frm.set_value({
		total_opening_balance: opening,
		total_collection_today: collection,
		grand_total: opening + collection,
		total_cash_receipt: sum(frm.doc.cash_available, "cash_receipt"),
		total_served: sum(frm.doc.cash_available, "served"),
		total_exchange: sum(frm.doc.cash_available, "exchange"),
		total_withdraw: sum(frm.doc.merchant_withdrawals, "withdraw"),
	});
}

function update_exchange(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	frappe.model.set_value(cdt, cdn, "exchange", flt(row.cash_receipt) - flt(row.served));
	update_totals(frm);
}

frappe.ui.form.on("Cashier Shift Collection", {
	opening_balance: update_totals,
	collection_today: update_totals,
});

frappe.ui.form.on("Cashier Shift Cash Available", {
	cash_receipt: update_exchange,
	served: update_exchange,
});

frappe.ui.form.on("Cashier Shift Merchant Withdraw", {
	withdraw: update_totals,
});

frappe.ui.form.on("Cashier Hand Over", {
	setup(frm) {
		frm.set_query("cashier", () => ({ filters: { enabled: 1 } }));
	},
	refresh(frm) {
		if (frm.is_new() && !frm.doc.cashier) {
			frm.set_value("cashier", frappe.session.user);
		}
		if (frm.is_new() && !frm.doc.company) {
			frm.set_value("company", frappe.defaults.get_user_default("Company"));
		}
	},
	cash_collections_remove: update_totals,
	cash_available_remove: update_totals,
	merchant_report_remove: update_totals,
});

function update_totals(frm) {
	const sum = (rows, field) => (rows || []).reduce((total, row) => total + flt(row[field]), 0);
	const cash_receipt = sum(frm.doc.cash_available, "cash_receipt");
	const served = sum(frm.doc.cash_available, "served");
	const exchange = sum(frm.doc.cash_available, "exchange");
	frm.set_value({
		total_opening_balance: sum(frm.doc.cash_collections, "opening_balance"),
		total_collection_today: sum(frm.doc.cash_collections, "collection_today"),
		total_cash_receipt: cash_receipt,
		total_served: served,
		total_exchange: exchange,
		total_withdraw: sum(frm.doc.merchant_report, "withdraw"),
		net_cash_available: cash_receipt - served - exchange,
	});
}

frappe.ui.form.on("Cashier Cash Collection", {
	opening_balance: update_totals,
	collection_today: update_totals,
});

frappe.ui.form.on("Cashier Cash Available", {
	cash_receipt: update_totals,
	served: update_totals,
	exchange: update_totals,
});

frappe.ui.form.on("Cashier Merchant Report", {
	withdraw: update_totals,
});

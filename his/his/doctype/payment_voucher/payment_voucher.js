frappe.ui.form.on("Payment Voucher", {
	refresh(frm) {
		frm.toggle_display("bank_name", frm.doc.payment_method !== "Cash");
		frm.toggle_display("cheque_no", frm.doc.payment_method === "Cheque");
		frm.toggle_display("cash_no", frm.doc.payment_method === "Cash");
	},
	payment_method(frm) {
		frm.trigger("refresh");
	},
	supplier(frm) {
		if (!frm.doc.supplier) {
			frm.set_value("vendor_balance", null);
			return;
		}

		frappe.call({
			method: "his.his.doctype.payment_voucher.payment_voucher.get_supplier_net_balance",
			args: {
				supplier: frm.doc.supplier,
				posting_date: frm.doc.posting_date,
			},
			callback: (response) => frm.set_value("vendor_balance", response.message),
		});
	},
	posting_date(frm) {
		if (frm.doc.supplier) {
			frm.trigger("supplier");
		}
	},
});

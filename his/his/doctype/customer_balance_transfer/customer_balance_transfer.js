frappe.ui.form.on('Customer Balance Transfer', {
	setup(frm) {
		frm.set_query('source_account', () => {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0
				}
			};
		});

		frm.set_query('target_account', () => {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0
				}
			};
		});
	},

	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.trigger('get_transfer_details');
		}
	},

	company(frm) {
		frm.trigger('clear_account_values');
		frm.trigger('get_transfer_details');
	},

	source_customer(frm) {
		frm.set_value('source_account', '');
		frm.trigger('get_transfer_details');
	},

	target_party_type(frm) {
		frm.set_value('target_party', '');
		frm.set_value('target_party_name', '');
		frm.set_value('target_account', '');
		frm.set_value('target_balance', 0);
	},

	target_party(frm) {
		frm.set_value('target_party_name', '');
		frm.set_value('target_account', '');
		frm.trigger('get_transfer_details');
	},

	source_account(frm) {
		frm.trigger('get_transfer_details');
	},

	target_account(frm) {
		frm.trigger('get_transfer_details');
	},

	clear_account_values(frm) {
		frm.set_value('source_account', '');
		frm.set_value('target_account', '');
		frm.set_value('source_balance', 0);
		frm.set_value('target_balance', 0);
		frm.set_value('target_party_name', '');
	},

	get_transfer_details(frm) {
		if (!frm.doc.company && !frm.doc.source_customer && !frm.doc.target_party) {
			return;
		}

		frappe.call({
			method: 'his.his.doctype.customer_balance_transfer.customer_balance_transfer.get_transfer_details',
			args: {
				company: frm.doc.company,
				source_customer: frm.doc.source_customer,
				source_account: frm.doc.source_account,
				target_party_type: frm.doc.target_party_type,
				target_party: frm.doc.target_party,
				target_account: frm.doc.target_account
			},
			callback(r) {
				if (!r.message) {
					return;
				}

				frm.set_value('company', r.message.company);
				if (!frm.doc.source_account) {
					frm.set_value('source_account', r.message.source_account);
				}
				if (!frm.doc.target_account) {
					frm.set_value('target_account', r.message.target_account);
				}
				frm.set_value('target_party_name', r.message.target_party_name);
				frm.set_value('source_balance', r.message.source_balance);
				frm.set_value('target_balance', r.message.target_balance);
			}
		});
	}
});

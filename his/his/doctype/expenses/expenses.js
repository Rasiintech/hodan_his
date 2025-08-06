// Copyright (c) 2021, Rasiin and contributors
// For license information, please see license.txt

frappe.ui.form.on('Expenses', {
	refresh: function(frm) {
		// frappe.call({
		// 	method: "his.api.get_mode_of_payments.mode_of_payments",
		// 	args: {
		// 	  company: frappe.defaults.get_default('Company'),
		// 	},
		// 	callback: function (r) {
		// 	  console.log(r.message);
		// 	  frm.set_value("paid_from" , r.message[0])
		// 	  frm.set_value("cost_center" , r.message[1])
		// 	}
		//   });
	}
});

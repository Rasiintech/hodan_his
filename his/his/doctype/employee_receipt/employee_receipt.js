frappe.ui.form.on('Employee Receipt', {
	refresh(frm) {
		// your code here
       if(frm.is_new()){
        frappe.call({
            method: 'his.his.doctype.employee_receipt.employee_receipt.get_account',
            callback: function(r) {
                frm.set_value("paid_to", r.message)
                
               
            }
        });
        }
        
		frm.set_query("paid_from", function() {
			return {
				"filters": {
					"company": frm.doc.company,
					"account_type": ["in", ["Payable"]]
				}
			};
		});

		frm.set_query("paid_to", function() {
			return {
				"filters": {
					"company": frm.doc.company,
					"account_type": ["in", ["Cash"]]
				}
			};
		});

		frm.set_query("cost_center", function() {
			return {
				"filters": {
					"company": frm.doc.company,
					"is_group": 0
				}
			};
		});

	},
	
	 employee: function(frm){
	    frappe.call({
		method: "erpnext.accounts.utils.get_balance_on",
// 		method: "his.get_balance.get_balance_on",
		args: {
		    date: get_today(), 
		    party_type: 'Employee', 
		    party: frm.doc.employee, 
		  //  cost_center: frm.doc.cost_center,
		    account: frm.doc.paid_from
		    
		},
		callback: function(r) {
// 			doc.outstanding_balance = format_currency(r.message, erpnext.get_currency(doc.company));
           frm.set_value("balance", r.message)
            frm.set_value("paid_amount", r.message)

            // frm.set_value("balance_with_vat", r.message * 1.05)
// 			refresh_field('outstanding_balance', 'accounts');
		}
		})
	},

	 paid_from: function(frm){
	    frappe.call({
		method: "erpnext.accounts.utils.get_balance_on",
// 		method: "his.get_balance.get_balance_on",
		args: {
		    date: get_today(), 
		    party_type: 'Employee', 
		    party: frm.doc.employee, 
		  //  cost_center: frm.doc.cost_center,
		    account: frm.doc.paid_from
		    
		},
		callback: function(r) {
// 			doc.outstanding_balance = format_currency(r.message, erpnext.get_currency(doc.company));
           frm.set_value("balance", r.message)
            frm.set_value("paid_amount", r.message)

            // frm.set_value("balance_with_vat", r.message * 1.05)
// 			refresh_field('outstanding_balance', 'accounts');
		}
		})
	},

	discount_amount: function(frm){
        frm.set_value("paid_amount", frm.doc.balance - frm.doc.discount_amount)

	}

	
})
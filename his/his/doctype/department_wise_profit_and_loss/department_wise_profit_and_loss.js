// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Department Wise Profit and Loss', {
	refresh: function(frm) {
		update_allocate_by_ui(frm);
	},
	account: function(frm){
		// alert()
			frappe.call({
               
            doc: frm.doc,
			method: 'get_account_balance',
            callback: function(r) {
                const data = r.message || {};
				frm.set_value("balance", flt(data.remaining_balance || 0));
				frm.set_value("previous_allocated_balance", flt(data.previously_allocated || 0));
				frm.set_value("unlocated_amount", flt(data.remaining_balance || 0));
                // frm.set_value("account",r.message[0].against);
              }
            });
	},
 allocate: function(frm) {
	if(frm.doc.type == "Direct Expense"){
		 frappe.call({
            doc: frm.doc,
            method: "get_direct_expense_by_practitioner",
            callback: function(r) {
                if (r.message) {
					console.log(r.message)
                    frm.set_value("allocation_table", r.message).then(() => {
                        calculate_allocation_totals(frm);
                    });
                }
            }
        });

	}else if(frm.doc.type == "Income"){
        frappe.call({
            doc: frm.doc,
            method: "get_sales_invoice_by_practitioner",
            callback: function(r) {
                if (r.message) {
                    frm.set_value("allocation_table", r.message).then(() => {
                        calculate_allocation_totals(frm);
                    });
                }
            }
        });
	}
	else if(frm.doc.type == "Indirect Expense"){
		if (frm.doc.allocate_by === "Revenue") {
			frappe.call({
				doc: frm.doc,
				method: "get_indirect_expense_by_revenue",
				callback: function(r) {
					if (r.message) {
						frm.set_value("allocation_table", r.message).then(() => {
							calculate_allocation_totals(frm);
						});
					}
				}
			});
		} else {
			frappe.call({
				doc: frm.doc,
				method: "get_all_consultants",
				callback: function(r) {
					if (r.message) {
						frm.set_value("allocation_table", r.message).then(() => {
							calculate_allocation_totals(frm);
						});
					}
				}
			});
		}
	}
    },
	
	type: function(frm) {
		if (frm.doc.type === "Direct Expense") {
			frm.set_query("account", function() {
				return {
					filters: {
						cost_allocaction: ["in", ["Direct", "Both"]]
					}
				};
			});
		} else if (frm.doc.type === "Indirect Expense") {
			frm.set_query("account", function() {
					return {
					filters: {
						cost_allocaction: ["in", ["Indirect", "Both"]]
					}
				};
			});
		}
		else {
			frm.set_query("account", function() {
					return {};
			});
		}

		frm.set_value("account", null);
		update_allocate_by_ui(frm);
	},

	allocate_by: function(frm) {
		if (frm.doc.type === "Indirect Expense") {
			frm.set_value("allocation_table", []);
			calculate_allocation_totals(frm);
		}
	}

});

function update_allocate_by_ui(frm) {
	const is_indirect = frm.doc.type === "Indirect Expense";
	frm.toggle_display("allocate_by", is_indirect);
	frm.toggle_reqd("allocate_by", is_indirect);

	if (is_indirect && !frm.doc.allocate_by) {
		frm.set_value("allocate_by", "Manual");
	}

	if (!is_indirect && frm.doc.allocate_by) {
		frm.set_value("allocate_by", null);
	}
}

function calculate_allocation_totals(frm) {
    let total_allocated = 0;

    (frm.doc.allocation_table || []).forEach(row => {
        total_allocated += flt(row.allocatated_amount);
    });

    frm.set_value("total_allocated", total_allocated);
    frm.set_value("unlocated_amount", flt(frm.doc.balance) - flt(total_allocated));
}



frappe.ui.form.on("Allocation Table", {
	allocatated_percentage: function(frm, cdt, cdn) {
		
		if (frm.doc.type !== "Indirect Expense") {
			
			return;
		}

		let row = locals[cdt][cdn];
		let balance = flt(frm.doc.balance);
		
		row.allocatated_amount = balance * flt(row.allocatated_percentage) / 100;
		// alert(row.allocatated_amount)
		frm.refresh_field("allocation_table");

		calculate_allocation_totals(frm);
	},

	allocation_table_add: function(frm, cdt, cdn) {
		if (frm.doc.type !== "Indirect Expense") {
			return;
		}
		calculate_allocation_totals(frm);
	},

	allocation_table_remove: function(frm, cdt, cdn) {
		if (frm.doc.type !== "Indirect Expense") {
			return;
		}
		calculate_allocation_totals(frm);
	}
});

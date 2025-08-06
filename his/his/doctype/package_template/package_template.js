// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Package Template', {
	// refresh: function(frm) {

	// }
	before_save: function(frm){
		let total_rate=0;
	   var tbl = cur_frm.doc.package_prescription || [];
	   for(var i = 0; i < tbl.length; i++) {
		   total_rate+=flt(tbl[i].rate);
		   
	   }
	   frm.set_value("rate",total_rate);
   }
});

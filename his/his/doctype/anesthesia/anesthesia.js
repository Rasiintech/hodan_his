// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Anesthesia', {
	// refresh: function(frm) {

	// }
	onload: function(frm) {


		
		var filters = [["Anesthesia", "date", "=", frappe.datetime.get_today()]];
		listview.filter_area.add(filters);

	
},
});

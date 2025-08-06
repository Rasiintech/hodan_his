// Copyright (c) 2022, Anfac Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

// frappe.db.get_value('Defaults', {user: frappe.session.user , document : "Account"}, 'value')
// 			.then(r => {		
frappe.query_reports["Sales Report"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default:frappe.datetime.now_date(),
			reqd: 1
		},
		{
			fieldname: "to",
			label: __("To Date"),
			fieldtype: "Date",
			default:frappe.datetime.now_date(),
			reqd: 1
		},
		

	]
};
// })
//default :r.message.value

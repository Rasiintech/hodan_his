

// Copyright (c) 2022, Anfac Tech and contributors
// For license information, please see license.txt
/* eslint-disable */
// account_filter ={
// 	"fieldname":"account",
// 	"label": __("Account"),
// 	"fieldtype": "Link",
// 	"options": "Account",
// 	"hidden" : 1
	
// }
// if(frappe.user_roles.includes("Main Cashier")){
// 	account_filter = 	{
// 		"fieldname":"account",
// 		"label": __("Account"),
// 		"fieldtype": "Link",
// 		"options": "Account",
		
// 	}
// }


frappe.query_reports["Daily Ledger Report"] = {
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
		// account_filter
			{
			"fieldname":"account",
			"label": __("Account"),
			"fieldtype": "Link",
			"options": "Account",
			
		}
		

	]
};


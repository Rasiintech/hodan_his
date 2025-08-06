// Copyright (c) 2024, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Cash Report By User"] = {
	 filters: [
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      default: frappe.datetime.now_date(),
      reqd: 1,
    },
    {
      fieldname: "to",
      label: __("To Date"),
      fieldtype:  "Date",
      default: frappe.datetime.now_date(),
      reqd: 1,
    },
    // {
    //  	fieldname: "user",
    //  	label: __("User"),
    //  	fieldtype: "Link",
    //  	"options": "User",
    //  	"default": frappe.session.user

    //  },
  ],
  onload: function(report) {
		report.page.add_inner_button(__("Detailed Cash Report"), function() {
			var filters = report.get_values();
			frappe.set_route('query-report', 'Detailed Cash Report By User', { from: filters.from_date, to: filters.to_date, user: frappe.session.user });
		});
	}
};

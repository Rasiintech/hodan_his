// Copyright (c) 2025, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Material Request  Report"] = {
	"filters": [
		{
		"fieldname": "from_date",
		"label": __("From Date"),
		"fieldtype": "Date",
		"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
		"fieldname": "to_date",
		"label": __("To Date"),
		"fieldtype": "Date",
		"default": frappe.datetime.get_today()
		},
		{
		"fieldname": "material_request_type",
		"label": __("Material Request Type"),
		"fieldtype": "Select",
		"options": "\nPurchase\nMaterial Transfer\nMaterial Issue\nManufacture\nCustomer Provided"
		},
		{
		"fieldname": "status",
		"label": __("MR Status"),
		"fieldtype": "Select",
		"options": "\nDraft\nPending\nStopped\nCancelled\nSubmitted\nPartially Ordered\nOrdered\nIssued\nTransferred\nCompleted"
		},
		{
		"fieldname": "department",
		"label": __("Department"),
		"fieldtype": "Link",
		"options": "Department"
		},
		{
		"fieldname": "requested_by",
		"label": __("Requested By"),
		"fieldtype": "Link", // change to Link User if your field is a Link
		"options": "User"
		},
		{
		"fieldname": "hod_approval",
		"label": __("HOD Approval"),
		"fieldtype": "Link", // adjust to Select or Link depending on your custom field
		"options": "HOD Approval Type"
		},
		{
		"fieldname": "fulfilled",
		"label": __("Fully Fulfilled"),
		"fieldtype": "Select",
		"options": "\nYes\nNo"
		}
	],

	onload(report) {
    // Ask server for the single permitted HOD (if any) and prefill the filter
    frappe.call({
      method: "his.his.report.material_request__report.material_request__report.get_default_hod",
      callback: function(r) {
        const val = r.message;
        if (val) {
          report.set_filter_value("hod_approval", val);
        }
      }
    });
  }
};

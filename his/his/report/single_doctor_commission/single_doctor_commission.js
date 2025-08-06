frappe.query_reports["Single Doctor Commission"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), -30)
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname": "ref_practitioner",
            "label": __("Doctor"),
            "fieldtype": "Link",
            "options": "Healthcare Practitioner",
            "reqd": 1,
            "get_query": function () {
                return {
                    filters: {
                        user_id: frappe.session.user
                    }
                };
            },
            "default": null  // We'll set it dynamically below
        },
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company")
        }
    ],
    "onload": function(report) {
        frappe.call({
            method: "frappe.client.get_value",
            args: {
                doctype: "Healthcare Practitioner",
                filters: { user_id: frappe.session.user },
                fieldname: "name"
            },
            callback: function(r) {
                if (r.message) {
                    frappe.query_report.set_filter_value("ref_practitioner", r.message.name);
                }
            }
        });
    }
};

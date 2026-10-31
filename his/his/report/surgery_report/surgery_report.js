// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Surgery Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
        },
        {
            fieldname: "patient",
            label: __("Patient"),
            fieldtype: "Link",
            options: "Patient",
            on_change(query_report) {
                query_report.set_filter_value("patient_value", query_report.get_filter_value("patient") || "%");
            },
        },
        {
            fieldname: "customer_group",
            label: __("Customer Group"),
            fieldtype: "Link",
            options: "Customer Group",
            on_change(query_report) {
                query_report.set_filter_value("customer_group_value", query_report.get_filter_value("customer_group") || "%");
            },
        },
        {
            fieldname: "practitioner",
            label: __("Practitioner"),
            fieldtype: "Link",
            options: "Healthcare Practitioner",
            on_change(query_report) {
                query_report.set_filter_value("practitioner_value", query_report.get_filter_value("practitioner") || "%");
            },
        },
        {
            fieldname: "medical_department",
            label: __("Medical Department"),
            fieldtype: "Link",
            options: "Medical Department",
            on_change(query_report) {
                query_report.set_filter_value("medical_department_value", query_report.get_filter_value("medical_department") || "%");
            },
        },
        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group",
            on_change(query_report) {
                query_report.set_filter_value("item_group_value", query_report.get_filter_value("item_group") || "%");
            },
        },
        {
            fieldname: "procedure_name",
            label: __("Procedure Template"),
            fieldtype: "Link",
            options: "Clinical Procedure Template",
            on_change(query_report) {
                query_report.set_filter_value("procedure_name_value", query_report.get_filter_value("procedure_name") || "%");
            },
        },
        ...["patient_value", "customer_group_value", "practitioner_value", "medical_department_value", "item_group_value", "procedure_name_value"].map((fieldname) => ({
            fieldname,
            fieldtype: "Data",
            default: "%",
            hidden: 1,
        })),
    ],
};

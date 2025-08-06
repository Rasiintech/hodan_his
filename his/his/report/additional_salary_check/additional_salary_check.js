// app/reports/additional_salary_check/additional_salary_check.js

frappe.query_reports["Additional Salary Check"] = {
  filters: [
    {
      fieldname: "from_date",
      label: "From Date",
      fieldtype: "Date",
      reqd: 1,
      default: frappe.datetime.month_start()
    },
    {
      fieldname: "to_date",
      label: "To Date",
      fieldtype: "Date",
      reqd: 1,
      default: frappe.datetime.month_end()
    }
  ]
};

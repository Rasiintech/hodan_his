frappe.dashboards.chart_sources["OPD Visits Trend"] = {
    method: "his.his.dashboard_chart_source.opd_visits_trend.opd_visits_trend.get_data",
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
        },
    ]
};

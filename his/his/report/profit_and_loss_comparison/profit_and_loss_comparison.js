// Copyright (c) 2025, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */
let suppress_on_change = true;
frappe.query_reports["Profit and Loss Comparison"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            // reqd: 1
        },
        {
            fieldname: "periodicity",
            label: __("Periodicity"),
            fieldtype: "Select",
            options: ["Monthly", "Quarterly", "Half-Yearly", "Yearly"],
            default: "Quarterly",
            // reqd: 1,
            on_change: () => {
                const periodicity = frappe.query_report.get_filter_value("periodicity");
                updatePeriodOptions(periodicity);
            }
        },
        {
            fieldname: "period_1",
            label: __("Period 1"),
            fieldtype: "Select",
            options: [],
            on_change: () => {
                if (!suppress_on_change) setDatesFromPeriod(1);
            }
        },
        {
            fieldname: "period_2",
            label: __("Period 2"),
            fieldtype: "Select",
            options: [],
            on_change: () => {
                if (!suppress_on_change) setDatesFromPeriod(2);
            }
        },
        {
            fieldname: "from_date_1",
            label: __("From Date (Period 1)"),
            fieldtype: "Date",
			"default": frappe.datetime.get_today().slice(0, 4) + "-01-01",
            // reqd: 1
        },
        {
            fieldname: "to_date_1",
            label: __("To Date (Period 1)"),
            fieldtype: "Date",
			"default": frappe.datetime.get_today(),
            // reqd: 1
        },
        {
            fieldname: "from_date_2",
            label: __("From Date (Period 2)"),
            fieldtype: "Date",
			"default": frappe.datetime.get_today().slice(0, 4) + "-01-01",
            // reqd: 1
        },
        {
            fieldname: "to_date_2",
            label: __("To Date (Period 2)"),
            fieldtype: "Date",
			"default": frappe.datetime.get_today(),
            // reqd: 1
        },
        {
            fieldname: "cost_center",
            label: __("Cost Center"),
            fieldtype: "Link",
            options: "Cost Center",
			hidden: 1
        },
        {
            fieldname: "department",
            label: __("Department"),
            fieldtype: "Link",
            options: "Department",
			hidden: 1
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "difference" || column.fieldname === "percentage_change") {
            if (data && data.difference > 0) {
                value = `<span style="color: green">${value}</span>`;
            } else if (data && data.difference < 0) {
                value = `<span style="color: red">${value}</span>`;
            }
        }

        return value;
    }
};

function updatePeriodOptions(periodicity) {
    const period1_filter = frappe.query_report.get_filter("period_1");
    const period2_filter = frappe.query_report.get_filter("period_2");

    if (periodicity === "Yearly") {
        // Fetch fiscal years dynamically from ERPNext
        frappe.db.get_list("Fiscal Year", {
            fields: ["name"],
            order_by: "name asc"
        }).then(res => {
            const fiscal_years = res.map(row => row.name);

            period1_filter.df.options = fiscal_years;
            period2_filter.df.options = fiscal_years;

            period1_filter.refresh();
            period2_filter.refresh();

            suppress_on_change = true;
            frappe.query_report.set_filter_value("period_1", fiscal_years[0]);
            frappe.query_report.set_filter_value("period_2", fiscal_years[1] || fiscal_years[0]);
            suppress_on_change = false;

            setDatesFromPeriod(1);
            setDatesFromPeriod(2);
        });

        return; // Exit here; rest of the logic is for non-Yearly
    }

    // Non-Yearly options
    let options = [];

    if (periodicity === "Monthly") {
        options = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ];
    } else if (periodicity === "Quarterly") {
        options = ["Jan - Mar", "Apr - Jun", "Jul - Sep", "Oct - Dec"];
    } else if (periodicity === "Half-Yearly") {
        options = ["Jan - Jun", "Jul - Dec"];
    }

    period1_filter.df.options = options;
    period2_filter.df.options = options;

    period1_filter.refresh();
    period2_filter.refresh();

    suppress_on_change = true;
    frappe.query_report.set_filter_value("period_1", options[0] || "");
    frappe.query_report.set_filter_value("period_2", options[1] || options[0] || "");
    suppress_on_change = false;

    setDatesFromPeriod(1);
    setDatesFromPeriod(2);
}

function setDatesFromPeriod(periodNumber) {
    const periodicity = frappe.query_report.get_filter_value("periodicity");
    const period = frappe.query_report.get_filter_value(`period_${periodNumber}`);
    const year = new Date().getFullYear();

    if (!periodicity || !period) return;

    let from_date, to_date;

    if (periodicity === "Monthly") {
        const monthIndex = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ].indexOf(period);
        const firstDay = new Date(year, monthIndex, 1);
        const lastDay = new Date(year, monthIndex + 1, 0);
        from_date = frappe.datetime.obj_to_str(firstDay);
        to_date = frappe.datetime.obj_to_str(lastDay);
    }

    if (periodicity === "Quarterly") {
        const map = {
            "Jan - Mar": ["01-01", "03-31"],
            "Apr - Jun": ["04-01", "06-30"],
            "Jul - Sep": ["07-01", "09-30"],
            "Oct - Dec": ["10-01", "12-31"]
        };
        [from_date, to_date] = map[period].map(d => `${year}-${d}`);
    }

    if (periodicity === "Half-Yearly") {
        const map = {
            "Jan - Jun": ["01-01", "06-30"],
            "Jul - Dec": ["07-01", "12-31"]
        };
        [from_date, to_date] = map[period].map(d => `${year}-${d}`);
    }

    if (periodicity === "Yearly") {
        from_date = `${period}-01-01`;
        to_date = `${period}-12-31`;
    }

    frappe.query_report.set_filter_value(`from_date_${periodNumber}`, from_date);
    frappe.query_report.set_filter_value(`to_date_${periodNumber}`, to_date);
}
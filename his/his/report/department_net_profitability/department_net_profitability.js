frappe.query_reports["Department Net Profitability"] = {
	filters: [
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date"
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date"
		},
		{
			fieldname: "department",
			label: "Department",
			fieldtype: "Link",
			options: "Medical Department"
		}
	],

	treeView: true,
	name_field: "row_name",
	parent_field: "parent_row",
	// This makes the report collapsed by default
	initial_depth: 0,

	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) return value;

		if (data.department === "Grand Total" || data.is_group) {
			value = `<b>${value || ""}</b>`;
		}

		if (
			["net_profit", "net_profit_percent"].includes(column.fieldname) &&
			parseFloat(data.net_profit || 0) < 0
		) {
			return `<span style="color:red;font-weight:600">${value || ""}</span>`;
		}

		if (
			["net_profit", "net_profit_percent"].includes(column.fieldname) &&
			parseFloat(data.net_profit || 0) > 0
		) {
			return `<span style="color:green;font-weight:600">${value || ""}</span>`;
		}

		if (
			column.fieldname === "net_profit_percent" &&
			parseFloat(data.net_profit_percent || 0) >= 0 &&
			parseFloat(data.net_profit_percent || 0) < 10
		) {
			return `<span style="color:#b58900;font-weight:600">${value || ""}</span>`;
		}

		return value;
	}
};
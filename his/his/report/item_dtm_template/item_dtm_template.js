// Copyright (c) 2025, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item DTM Template"] = {
	"filters": [
		{
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "default": frappe.sys_defaults.year_start_date || frappe.datetime.month_start()
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname": "warehouse",
            "label": "Warehouse",
            "fieldtype": "Link",
            "options": "Warehouse"
        },
        {
            "fieldname": "item_code",
            "label": "Item Code",
            "fieldtype": "Link",
            "options": "Item"
        },
        // MULTI-SELECT ITEM GROUPS
        {
            "fieldname": "item_groups",
            "label": "Item Groups",
            "fieldtype": "MultiSelectList",
            "get_data": function (txt) {
                return frappe.db.get_link_options("Item Group", txt);
            }
        },
        {
            "fieldname": "uom",
            "label": "UOM",
            "fieldtype": "Link",
            "options": "UOM"
        },
        {
            "fieldname": "is_stock_item",
            "label": "Maintain Stock",
            "fieldtype": "Select",
            "options": "\nYes\nNo",
			"default": "Yes"
        },
        {
            "fieldname": "is_fixed_asset",
            "label": "Is Fixed Asset",
            "fieldtype": "Select",
            "options": "\nYes\nNo"
        },
        {
            "fieldname": "price_list",
            "label": "Selling Price List",
            "fieldtype": "Link",
            "options": "Price List",
            "default": "Standard Selling",
			"read_only": 1
        }
	]
};

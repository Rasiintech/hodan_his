import frappe
from frappe.utils import today


def execute(filters=None):
    filters = filters or {}

    if not filters.get("to_date"):
        filters["to_date"] = today()

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {"label": "Sr No", "fieldname": "sr_no", "fieldtype": "Int", "width": 60},
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link",
         "options": "Item", "width": 120},
        {"label": "Item Name (Full Commercial/Chem)", "fieldname": "item_name",
         "fieldtype": "Data", "width": 250},
        {"label": "Category (Medicine / Consumable )", "fieldname": "category",
         "fieldtype": "Data", "width": 180},
        {"label": "Unit of Measure", "fieldname": "uom",
         "fieldtype": "Data", "width": 100},
        {"label": "Average Cost per Unit", "fieldname": "avg_cost",
         "fieldtype": "Currency", "width": 120},
        {"label": "Stock on Hand (Qty)", "fieldname": "stock_qty",
         "fieldtype": "Float", "width": 120},
        {"label": "Selling Price", "fieldname": "selling_price",
         "fieldtype": "Currency", "width": 120},
        {"label": "Comments (If Necessary)", "fieldname": "comments",
         "fieldtype": "Data", "width": 200},
    ]


def get_data(filters):
    values = {
        "warehouse": filters.get("warehouse"),
        "item_code": filters.get("item_code"),
        "uom": filters.get("uom"),
        "price_list": filters.get("price_list"),
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "is_stock_item": filters.get("is_stock_item"),
        "is_fixed_asset": filters.get("is_fixed_asset"),
    }

    # -------- MultiSelect Item Groups (works with list, dict, or string) --------
    raw_groups = filters.get("item_groups")
    item_groups = []

    if raw_groups:
        # Case 1: already a list/tuple from MultiSelectList
        if isinstance(raw_groups, (list, tuple)):
            for g in raw_groups:
                if isinstance(g, dict) and g.get("value"):
                    item_groups.append(g.get("value"))
                elif isinstance(g, str):
                    item_groups.append(g)
        # Case 2: string (JSON or comma-separated fallback)
        elif isinstance(raw_groups, str):
            # Try to parse JSON first (some versions send JSON string)
            try:
                parsed = frappe.parse_json(raw_groups)
            except Exception:
                parsed = None

            if isinstance(parsed, (list, tuple)):
                for g in parsed:
                    if isinstance(g, dict) and g.get("value"):
                        item_groups.append(g.get("value"))
                    elif isinstance(g, str):
                        item_groups.append(g)
            else:
                # Fallback: treat as comma-separated string
                item_groups = [g.strip() for g in raw_groups.split(",") if g.strip()]

    item_group_condition = ""
    if item_groups:
        item_group_condition = " AND i.item_group IN %(item_groups)s"
        values["item_groups"] = tuple(item_groups)

    # -------- Rest of your conditions unchanged --------
    stock_condition = """
        AND (
            %(is_stock_item)s IS NULL
            OR %(is_stock_item)s = ''
            OR (%(is_stock_item)s = 'Yes' AND i.is_stock_item = 1)
            OR (%(is_stock_item)s = 'No' AND i.is_stock_item = 0)
        )
    """

    fixed_asset_condition = """
        AND (
            %(is_fixed_asset)s IS NULL
            OR %(is_fixed_asset)s = ''
            OR (%(is_fixed_asset)s = 'Yes' AND i.is_fixed_asset = 1)
            OR (%(is_fixed_asset)s = 'No' AND i.is_fixed_asset = 0)
        )
    """

    query = f"""
        SELECT
            i.item_code,
            i.item_name,
            i.item_group AS category,
            i.stock_uom AS uom,
            CASE
                WHEN COALESCE(SUM(COALESCE(b.actual_qty, 0)), 0) != 0
                    THEN SUM(COALESCE(b.valuation_rate, 0) * COALESCE(b.actual_qty, 0))
                         / SUM(COALESCE(b.actual_qty, 0))
                ELSE AVG(COALESCE(b.valuation_rate, 0))
            END AS avg_cost,
            COALESCE(SUM(COALESCE(b.actual_qty, 0)), 0) AS stock_qty,
            (
                SELECT ip.price_list_rate
                FROM `tabItem Price` ip
                WHERE
                    ip.item_code = i.name
                    AND (%(price_list)s IS NULL OR ip.price_list = %(price_list)s)
                    AND (ip.valid_from IS NULL OR ip.valid_from <= %(to_date)s)
                    AND (ip.selling = 1 OR ip.selling IS NULL)
                ORDER BY
                    ip.valid_from DESC,
                    ip.creation DESC
                LIMIT 1
            ) AS selling_price
        FROM `tabItem` i
        LEFT JOIN `tabBin` b
            ON b.item_code = i.name
        WHERE
            i.disabled = 0
            AND (%(warehouse)s IS NULL OR b.warehouse = %(warehouse)s)
            AND (%(item_code)s IS NULL OR i.item_code = %(item_code)s)
            AND (%(uom)s IS NULL OR i.stock_uom = %(uom)s)
            AND (%(from_date)s IS NULL OR DATE(i.creation) >= %(from_date)s)
            AND (%(to_date)s IS NULL OR DATE(i.creation) <= %(to_date)s)
            {item_group_condition}
            {stock_condition}
            {fixed_asset_condition}
        GROUP BY
            i.item_code, i.item_name, i.item_group, i.stock_uom
        ORDER BY
            i.item_code
    """

    data = frappe.db.sql(query, values, as_dict=True)

    for idx, row in enumerate(data, start=1):
        row["sr_no"] = idx
        row["comments"] = ""

    return data


# import frappe
# from frappe.utils import today


# def execute(filters=None):
#     filters = filters or {}

#     if not filters.get("to_date"):
#         filters["to_date"] = today()

#     columns = get_columns()
#     data = get_data(filters)

#     return columns, data


# def get_columns():
#     return [
#         {"label": "Sr No", "fieldname": "sr_no", "fieldtype": "Int", "width": 60},
#         {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link",
#          "options": "Item", "width": 120},
#         {"label": "Item Name (Full Commercial/Chem)", "fieldname": "item_name",
#          "fieldtype": "Data", "width": 250},
#         {"label": "Category (Medicine / Consumable )", "fieldname": "category",
#          "fieldtype": "Data", "width": 180},
#         {"label": "Unit of Measure", "fieldname": "uom",
#          "fieldtype": "Data", "width": 100},
#         {"label": "Average Cost per Unit", "fieldname": "avg_cost",
#          "fieldtype": "Currency", "width": 120},
#         {"label": "Stock on Hand (Qty)", "fieldname": "stock_qty",
#          "fieldtype": "Float", "width": 120},
#         {"label": "Selling Price", "fieldname": "selling_price",
#          "fieldtype": "Currency", "width": 120},
#         {"label": "Comments (If Necessary)", "fieldname": "comments",
#          "fieldtype": "Data", "width": 200},
#     ]


# def get_data(filters):
#     values = {
#         "warehouse": filters.get("warehouse"),
#         "item_code": filters.get("item_code"),
#         "item_group": filters.get("item_group"),
#         "uom": filters.get("uom"),
#         "price_list": filters.get("price_list"),
#         "from_date": filters.get("from_date"),
#         "to_date": filters.get("to_date"),
#     }

#     # If warehouse is None → aggregate all warehouses.
#     # avg_cost is weighted average: SUM(rate * qty) / SUM(qty)
#     data = frappe.db.sql(
#         """
#         SELECT
#             i.item_code,
#             i.item_name,
#             i.item_group AS category,
#             i.stock_uom AS uom,
#             CASE
#                 WHEN COALESCE(SUM(COALESCE(b.actual_qty, 0)), 0) != 0
#                     THEN SUM(COALESCE(b.valuation_rate, 0) * COALESCE(b.actual_qty, 0))
#                          / SUM(COALESCE(b.actual_qty, 0))
#                 ELSE AVG(COALESCE(b.valuation_rate, 0))
#             END AS avg_cost,
#             COALESCE(SUM(COALESCE(b.actual_qty, 0)), 0) AS stock_qty,
#             (
#                 SELECT ip.price_list_rate
#                 FROM `tabItem Price` ip
#                 WHERE
#                     ip.item_code = i.name
#                     AND (%(price_list)s IS NULL OR ip.price_list = %(price_list)s)
#                     AND (ip.valid_from IS NULL OR ip.valid_from <= %(to_date)s)
#                     AND (ip.selling = 1 OR ip.selling IS NULL)
#                 ORDER BY
#                     ip.valid_from DESC,
#                     ip.creation DESC
#                 LIMIT 1
#             ) AS selling_price
#         FROM `tabItem` i
#         LEFT JOIN `tabBin` b
#             ON b.item_code = i.name
#         WHERE
#             i.disabled = 0
#             AND (%(warehouse)s IS NULL OR b.warehouse = %(warehouse)s)
#             AND (%(item_code)s IS NULL OR i.item_code = %(item_code)s)
#             AND (%(item_group)s IS NULL OR i.item_group = %(item_group)s)
#             AND (%(uom)s IS NULL OR i.stock_uom = %(uom)s)
#             AND (%(from_date)s IS NULL OR DATE(i.creation) >= %(from_date)s)
#             AND (%(to_date)s IS NULL OR DATE(i.creation) <= %(to_date)s)
#         GROUP BY
#             i.item_code, i.item_name, i.item_group, i.stock_uom
#         ORDER BY
#             i.item_code
#         """,
#         values,
#         as_dict=True,
#     )

#     for idx, row in enumerate(data, start=1):
#         row["sr_no"] = idx
#         row["comments"] = ""

#     return data

import frappe
from frappe import _
from frappe.utils import flt

def _pick_mr_field(candidates, default=None):
    meta = frappe.get_meta("Material Request")
    for f in candidates:
        if meta.get_field(f):
            return f
    return default

# NEW: pull current user's permitted values for a given Link doctype
def _get_permitted_values(allow_doctype: str, user: str | None = None) -> list[str]:
    user = user or frappe.session.user
    # We only fetch the current user's own permissions; safe to bypass read perms
    vals = frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": allow_doctype},
        pluck="for_value",
        ignore_permissions=True,
    )
    # De-dupe while preserving order
    return list(dict.fromkeys(vals))

@frappe.whitelist()
def get_default_hod():
    """For client-side defaulting (optional). Returns the single permitted HOD, else None."""
    vals = _get_permitted_values("HOD Approval Type")
    return vals[0] if len(vals) == 1 else None

def execute(filters=None):
    filters = frappe._dict(filters or {})

    requested_by_field = _pick_mr_field(["requested_by", "requested_by_user", "requester", "user"], default="owner")
    department_field   = _pick_mr_field(["medical_department", "cost_center", "branch"])
    hod_field          = _pick_mr_field(["hod_departament", "hod_approved_by", "hod_approver", "hod_approval_status"])

    where = ["mr.docstatus = 1"]
    params = {}

    # --- DEFAULT / ENFORCE HOD PER USER PERMISSIONS ---
    permitted_hods = []
    if hod_field:
        permitted_hods = _get_permitted_values("HOD Approval Type")
        if filters.get("hod_approval"):
            where.append(f"mr.`{hod_field}` = %(hod_approval)s")
            params["hod_approval"] = filters.hod_approval
        else:
            if len(permitted_hods) == 1:
                filters.hod_approval = permitted_hods[0]
                where.append(f"mr.`{hod_field}` = %(hod_approval)s")
                params["hod_approval"] = filters.hod_approval
            elif len(permitted_hods) > 1:
                where.append(f"mr.`{hod_field}` in %(hod_list)s")
                params["hod_list"] = tuple(permitted_hods)

    # Other filters
    if filters.get("from_date"):
        where.append("mr.transaction_date >= %(from_date)s")
        params["from_date"] = filters.from_date
    if filters.get("to_date"):
        where.append("mr.transaction_date <= %(to_date)s")
        params["to_date"] = filters.to_date
    if filters.get("material_request_type"):
        where.append("mr.material_request_type = %(material_request_type)s")
        params["material_request_type"] = filters.material_request_type
    if department_field and filters.get("department"):
        where.append(f"mr.`{department_field}` = %(department)s")
        params["department"] = filters.department
    if filters.get("requested_by"):
        where.append(f"mr.`{requested_by_field}` = %(requested_by)s")
        params["requested_by"] = filters.requested_by
    if filters.get("status"):
        where.append("mr.status = %(status)s")
        params["status"] = filters.status

    where_sql = " AND ".join(where)

    # --- Item-level pull (lightweight) we will aggregate in Python ---
    base_rows = frappe.db.sql(f"""
        SELECT
            mr.name                              AS mr_no,
            mr.transaction_date                  AS mr_date,
            mr.material_request_type             AS mr_type,
            mr.status                            AS mr_status,
            mr.`{requested_by_field}`           AS requested_by,
            {"mr.`{}` as department,".format(department_field) if department_field else "NULL as department,"}
            {"mr.`{}` as hod_approval,".format(hod_field) if hod_field else "NULL as hod_approval,"}
            mri.name                             AS mri_row,
            mri.stock_qty                        AS req_stock_qty,
            (mri.qty * IFNULL(mri.rate, 0))      AS amount
        FROM `tabMaterial Request` mr
        JOIN `tabMaterial Request Item` mri ON mri.parent = mr.name
        WHERE {where_sql}
        ORDER BY mr.transaction_date, mr.name, mri.idx
    """, params, as_dict=True)

    if not base_rows:
        return get_columns(), [], None, None, []

    # --- Delivered per Material Request Item (we'll roll up to MR) ---
    delivered_by_item = frappe.db.sql("""
        SELECT
            sed.material_request_item            AS mri_row,
            SUM(CASE WHEN se.docstatus = 1 THEN sed.transfer_qty ELSE 0 END) AS delivered_stock_qty
        FROM `tabStock Entry Detail` sed
        JOIN `tabStock Entry` se ON se.name = sed.parent
        WHERE sed.material_request_item IS NOT NULL
          AND se.docstatus = 1
        GROUP BY sed.material_request_item
    """, as_dict=True)
    delivered_map = {d.mri_row: flt(d.delivered_stock_qty) for d in delivered_by_item}

    # --- Aggregate to MR level ---
    mr_map = {}
    for r in base_rows:
        mr = mr_map.setdefault(r.mr_no, {
            "mr_no": r.mr_no,
            "mr_date": r.mr_date,
            "mr_type": r.mr_type,
            "mr_status": r.mr_status,
            "requested_by": r.requested_by,
            "department": r.get("department"),
            "hod_approval": r.get("hod_approval"),
            "item_count": 0,
            "req_stock_qty": 0.0,
            "amount": 0.0,
            "delivered_stock_qty": 0.0,
        })
        mr["item_count"] += 1
        mr["req_stock_qty"] += flt(r.req_stock_qty)
        mr["amount"] += flt(r.amount or 0)
        mr["delivered_stock_qty"] += flt(delivered_map.get(r.mri_row, 0.0))

    # --- Finalize rows: % and Fulfilled flag ---
    rows = []
    TOL = 1e-6
    for mr_no, v in sorted(mr_map.items(), key=lambda kv: (kv[1]["mr_date"], kv[0])):
        delivered_pct = (v["delivered_stock_qty"] / v["req_stock_qty"] * 100.0) if v["req_stock_qty"] else 0.0
        fulfilled_flag = 1 if v["delivered_stock_qty"] + TOL >= v["req_stock_qty"] else 0

        rows.append({
            "mr_no": v["mr_no"],
            "mr_date": v["mr_date"],
            "mr_type": v["mr_type"],
            "mr_status": v["mr_status"],
            "requested_by": v["requested_by"],
            "department": v["department"],
            "hod_approval": v["hod_approval"],
            "item_count": v["item_count"],
            "req_stock_qty": flt(v["req_stock_qty"], 3),
            "amount": flt(v["amount"], 2),
            "delivered_stock_qty": flt(v["delivered_stock_qty"], 3),
            "delivered_pct": flt(delivered_pct, 2),
            "fulfilled": _("Yes") if fulfilled_flag else _("No"),
            "_fulfilled_flag": fulfilled_flag,   # internal key for filtering
        })

    # --- Apply Fulfilled filter (Yes/No) from UI ---
    sel = (filters.get("fulfilled") or "").strip()
    if sel in ("Yes", "No"):
        want = 1 if sel == "Yes" else 0
        rows = [r for r in rows if r.get("_fulfilled_flag", 0) == want]

    # --- Recompute totals AFTER filtering ---
    totals = {"mrs": 0, "req_stock_qty": 0.0, "delivered_stock_qty": 0.0, "amount": 0.0, "fulfilled_count": 0}
    for r in rows:
        totals["mrs"] += 1
        totals["req_stock_qty"] += flt(r["req_stock_qty"])
        totals["delivered_stock_qty"] += flt(r["delivered_stock_qty"])
        totals["amount"] += flt(r["amount"])
        totals["fulfilled_count"] += 1 if r.get("_fulfilled_flag") else 0

    columns = get_columns()
    chart = {
        "data": {
            "labels": [_("Qty")],
            "datasets": [
                {"name": _("Requested (Stock UOM)"), "values": [flt(totals["req_stock_qty"], 3)]},
                {"name": _("Delivered (Stock UOM)"), "values": [flt(totals["delivered_stock_qty"], 3)]},
            ],
        },
        "type": "bar",
    }
    report_summary = [
        {"label": _("MRs"), "value": totals["mrs"], "indicator": "blue"},
        {"label": _("Requested (Stock UOM)"), "value": flt(totals["req_stock_qty"], 3), "indicator": "orange"},
        {"label": _("Delivered (Stock UOM)"), "value": flt(totals["delivered_stock_qty"], 3), "indicator": "green"},
        {"label": _("% Fully Fulfilled MRs"),
         "value": flt((totals["fulfilled_count"] / totals["mrs"]) * 100.0, 1) if totals["mrs"] else 0.0,
         "indicator": "green" if totals["fulfilled_count"] == totals["mrs"] else "yellow"},
        {"label": _("Total Amount"),
         "value": frappe.utils.fmt_money(totals["amount"]) if totals["amount"] else "-",
         "indicator": "blue"},
    ]

    return columns, rows, None, chart, report_summary

def get_columns():
    return [
        {"label": _("MR No"), "fieldname": "mr_no", "fieldtype": "Link", "options": "Material Request", "width": 160},
        {"label": _("Date"), "fieldname": "mr_date", "fieldtype": "Date", "width": 100},
        {"label": _("Type"), "fieldname": "mr_type", "fieldtype": "Data", "width": 110},
        {"label": _("MR Status"), "fieldname": "mr_status", "fieldtype": "Data", "width": 110},
        {"label": _("Requested By"), "fieldname": "requested_by", "fieldtype": "Data", "width": 150},
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Medical Department", "width": 160},
        {"label": _("HOD Approval"), "fieldname": "hod_approval", "fieldtype": "Link", "options": "HOD Approval Type", "width": 160},

        {"label": _("# Items"), "fieldname": "item_count", "fieldtype": "Int", "width": 90},
        {"label": _("Total Qty (Stock UOM)"), "fieldname": "req_stock_qty", "fieldtype": "Float", "precision": 3, "width": 170},
        {"label": _("Total Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 140},

        {"label": _("Delivered (Stock UOM)"), "fieldname": "delivered_stock_qty", "fieldtype": "Float", "precision": 3, "width": 190},
        {"label": _("Delivered %"), "fieldname": "delivered_pct", "fieldtype": "Percent", "width": 110},
        {"label": _("Fully Fulfilled?"), "fieldname": "fulfilled", "fieldtype": "Data", "width": 130},
    ]

def get_chart(totals):
    # Simple bar chart: Requested vs Delivered (Stock UOM)
    return {
        "data": {
            "labels": [_("Qty")],
            "datasets": [
                {"name": _("Requested"), "values": [flt(totals["req_stock_qty"], 3)]},
                {"name": _("Delivered"), "values": [flt(totals["delivered_stock_qty"], 3)]},
            ],
        },
        "type": "bar",
        "colors": ["#7c3aed", "#10b981"],  # optional; remove if you prefer defaults
    }




# import frappe
# from frappe import _
# from frappe.utils import flt

# def _pick_mr_field(candidates, default=None):
#     meta = frappe.get_meta("Material Request")
#     for f in candidates:
#         if meta.get_field(f):
#             return f
#     return default

# # NEW: pull current user's permitted values for a given Link doctype
# def _get_permitted_values(allow_doctype: str, user: str | None = None) -> list[str]:
#     user = user or frappe.session.user
#     # We only fetch the current user's own permissions; safe to bypass read perms
#     vals = frappe.get_all(
#         "User Permission",
#         filters={"user": user, "allow": allow_doctype},
#         pluck="for_value",
#         ignore_permissions=True,
#     )
#     # De-dupe while preserving order
#     return list(dict.fromkeys(vals))

# @frappe.whitelist()
# def get_default_hod():
#     """For client-side defaulting (optional). Returns the single permitted HOD, else None."""
#     vals = _get_permitted_values("HOD Approval Type")
#     return vals[0] if len(vals) == 1 else None

# def execute(filters=None):
#     filters = frappe._dict(filters or {})

#     requested_by_field = _pick_mr_field(["requested_by", "requested_by_user", "requester", "user"], default="owner")
#     department_field   = _pick_mr_field(["medical_department", "cost_center", "branch"])
#     hod_field          = _pick_mr_field(["hod_departament", "hod_approved_by", "hod_approver", "hod_approval_status"])

#     where = ["mr.docstatus = 1"]
#     params = {}

#     # --- DEFAULT / ENFORCE HOD PER USER PERMISSIONS ---
#     permitted_hods = []
#     if hod_field:
#         permitted_hods = _get_permitted_values("HOD Approval Type")
#         # If user supplied a specific filter, keep it (but still respect perms if you want)
#         if filters.get("hod_approval"):
#             where.append(f"mr.`{hod_field}` = %(hod_approval)s")
#             params["hod_approval"] = filters.hod_approval
#         else:
#             if len(permitted_hods) == 1:
#                 # Default to the single permitted HOD value
#                 filters.hod_approval = permitted_hods[0]
#                 where.append(f"mr.`{hod_field}` = %(hod_approval)s")
#                 params["hod_approval"] = filters.hod_approval
#             elif len(permitted_hods) > 1:
#                 # Show all permitted HODs without forcing the user to pick
#                 where.append(f"mr.`{hod_field}` in %(hod_list)s")
#                 params["hod_list"] = tuple(permitted_hods)

#     # The rest of your filters...
#     if filters.get("from_date"):
#         where.append("mr.transaction_date >= %(from_date)s")
#         params["from_date"] = filters.from_date
#     if filters.get("to_date"):
#         where.append("mr.transaction_date <= %(to_date)s")
#         params["to_date"] = filters.to_date
#     if filters.get("material_request_type"):
#         where.append("mr.material_request_type = %(material_request_type)s")
#         params["material_request_type"] = filters.material_request_type
#     if department_field and filters.get("department"):
#         where.append(f"mr.`{department_field}` = %(department)s")
#         params["department"] = filters.department
#     if filters.get("requested_by"):
#         where.append(f"mr.`{requested_by_field}` = %(requested_by)s")
#         params["requested_by"] = filters.requested_by
#     if filters.get("status"):
#         where.append("mr.status = %(status)s")
#         params["status"] = filters.status
#     if filters.get("item_code"):
#         where.append("mri.item_code = %(item_code)s")
#         params["item_code"] = filters.item_code

#     where_sql = " AND ".join(where)

#     # Base rows: all MR Items (posted)
#     base_rows = frappe.db.sql(f"""
#         SELECT
#             mr.name                              AS mr_no,
#             mr.transaction_date                  AS mr_date,
#             mr.material_request_type             AS mr_type,
#             mr.status                            AS mr_status,
#             mr.`{requested_by_field}`           AS requested_by,
#             {"mr.`{}` as department,".format(department_field) if department_field else "NULL as department,"}
#             {"mr.`{}` as hod_approval,".format(hod_field) if hod_field else "NULL as hod_approval,"}
#             mri.name                             AS mri_row,
#             mri.item_code,
#             mri.item_name,
#             mri.description,
#             mri.uom,
#             mri.qty                              AS req_qty,           -- in UOM
#             mri.stock_uom,
#             mri.stock_qty                        AS req_stock_qty,     -- in stock UOM
#             mri.rate                             AS rate,              -- may be NULL if you don't track rates on MR
#             (mri.qty * IFNULL(mri.rate, 0))      AS amount
#         FROM `tabMaterial Request` mr
#         JOIN `tabMaterial Request Item` mri ON mri.parent = mr.name
#         WHERE {where_sql}
#         ORDER BY mr.transaction_date, mr.name, mri.idx
#     """, params, as_dict=True)

#     if not base_rows:
#         return get_columns(), [], None, None, []

#     # Delivered map from Stock Entry (use transfer_qty in stock UOM)
#     delivered = frappe.db.sql("""
#         SELECT
#             sed.material_request_item    AS mri_row,
#             SUM(CASE WHEN se.docstatus = 1 THEN sed.transfer_qty ELSE 0 END) AS delivered_stock_qty
#         FROM `tabStock Entry Detail` sed
#         JOIN `tabStock Entry` se ON se.name = sed.parent
#         WHERE sed.material_request_item IS NOT NULL
#           AND se.docstatus = 1
#         GROUP BY sed.material_request_item
#     """, as_dict=True)

#     delivered_map = {d.mri_row: flt(d.delivered_stock_qty) for d in delivered}

#     # Build result rows
#     rows = []
#     totals = {
#         "req_qty": 0.0,
#         "req_stock_qty": 0.0,
#         "amount": 0.0,
#         "delivered_stock_qty": 0.0,
#         "fulfilled_count": 0,
#         "lines": 0,
#     }

#     TOL = 1e-6  # tiny tolerance
#     for r in base_rows:
#         delivered_stock_qty = flt(delivered_map.get(r.mri_row, 0.0))
#         delivered_pct = (delivered_stock_qty / r.req_stock_qty * 100.0) if r.req_stock_qty else 0.0
#         fulfilled = 1 if delivered_stock_qty + TOL >= flt(r.req_stock_qty) else 0

#         rows.append({
#             "mr_no": r.mr_no,
#             "mr_date": r.mr_date,
#             "mr_type": r.mr_type,
#             "mr_status": r.mr_status,
#             "requested_by": r.requested_by,
#             "department": r.get("department"),
#             "hod_approval": r.get("hod_approval"),
#             "item_code": r.item_code,
#             "item_name": r.item_name,
#             "uom": r.uom,
#             "req_qty": flt(r.req_qty, 3),
#             "rate": flt(r.rate) if r.rate is not None else None,
#             "amount": flt(r.amount, 2) if r.amount is not None else None,
#             "stock_uom": r.stock_uom,
#             "req_stock_qty": flt(r.req_stock_qty, 3),
#             "delivered_stock_qty": flt(delivered_stock_qty, 3),
#             "delivered_pct": flt(delivered_pct, 2),
#             "fulfilled": _("Yes") if fulfilled else _("No"),
#         })

#         totals["req_qty"] += flt(r.req_qty)
#         totals["req_stock_qty"] += flt(r.req_stock_qty)
#         totals["amount"] += flt(r.amount or 0)
#         totals["delivered_stock_qty"] += flt(delivered_stock_qty)
#         totals["fulfilled_count"] += fulfilled
#         totals["lines"] += 1

#     columns = get_columns()
#     chart = get_chart(totals)
#     report_summary = [
#         {"label": _("Lines"), "value": totals["lines"], "indicator": "blue"},
#         {"label": _("Requested (Stock UOM)"), "value": flt(totals["req_stock_qty"], 3), "indicator": "orange"},
#         {"label": _("Delivered (Stock UOM)"), "value": flt(totals["delivered_stock_qty"], 3), "indicator": "green"},
#         {"label": _("% Fulfilled Lines"),
#          "value": flt((totals["fulfilled_count"] / totals["lines"]) * 100.0, 1) if totals["lines"] else 0.0,
#          "indicator": "green" if totals["fulfilled_count"] == totals["lines"] else "yellow"},
#         {"label": _("Amount"),
#          "value": frappe.utils.fmt_money(totals["amount"]) if totals["amount"] else "-",
#          "indicator": "blue"},
#     ]

#     return columns, rows, None, chart, report_summary

# def get_columns():
#     return [
#         {"label": _("MR No"), "fieldname": "mr_no", "fieldtype": "Link", "options": "Material Request", "width": 140},
#         {"label": _("Date"), "fieldname": "mr_date", "fieldtype": "Date", "width": 100},
#         {"label": _("Type"), "fieldname": "mr_type", "fieldtype": "Data", "width": 100},
#         {"label": _("MR Status"), "fieldname": "mr_status", "fieldtype": "Data", "width": 110},
#         {"label": _("Requested By"), "fieldname": "requested_by", "fieldtype": "Data", "width": 140},
#         {"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Medical Department", "width": 140},
#         {"label": _("HOD Approval"), "fieldname": "hod_approval", "fieldtype": "Link", "options": "HOD Approval Type", "width": 140},

#         {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 140},
#         {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 180},
#         {"label": _("UOM"), "fieldname": "uom", "fieldtype": "Data", "width": 80},
#         {"label": _("Req Qty (UOM)"), "fieldname": "req_qty", "fieldtype": "Float", "precision": 3, "width": 120},
#         {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 110},
#         {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},

#         {"label": _("Stock UOM"), "fieldname": "stock_uom", "fieldtype": "Data", "width": 100},
#         {"label": _("Req Qty (Stock UOM)"), "fieldname": "req_stock_qty", "fieldtype": "Float", "precision": 3, "width": 160},
#         {"label": _("Issued/Transferred (Stock UOM)"), "fieldname": "delivered_stock_qty", "fieldtype": "Float", "precision": 3, "width": 200},
#         {"label": _("Delivered %"), "fieldname": "delivered_pct", "fieldtype": "Percent", "width": 110},
#         {"label": _("Fully Fulfilled?"), "fieldname": "fulfilled", "fieldtype": "Data", "width": 120},
#     ]

# def get_chart(totals):
#     # Simple bar chart: Requested vs Delivered (Stock UOM)
#     return {
#         "data": {
#             "labels": [_("Qty")],
#             "datasets": [
#                 {"name": _("Requested"), "values": [flt(totals["req_stock_qty"], 3)]},
#                 {"name": _("Delivered"), "values": [flt(totals["delivered_stock_qty"], 3)]},
#             ],
#         },
#         "type": "bar",
#         "colors": ["#7c3aed", "#10b981"],  # optional; remove if you prefer defaults
#     }

# # # Poor
# # # Fair
# # # Very good
# # # N/A
# import frappe

# @frappe.whitelist()
# def get_patient_survey_data():
#     """
#     Fetches and processes patient survey data from multiple doctypes,
#     categorizing responses into 'happy' and 'unhappy' sentiments.
#     Returns:
#         dict: {
#             "IPD": {"happy": 26, "unhappy": 8},
#             "OPD": {"happy": 32, "unhappy": 6},
#             ...
#         }
#     """
#     survey_config = {
#         "IPD Survey": {"field": "name_4", "name": "IPD"},
#         "OPD Survey": {"field": "name_06", "name": "OPD"},
#         "Pharmacy Survey": {"field": "name_001", "name": "Pharmacy"},
#         "Laboratory And Radiology  Survey": {"field": "overall_experience_rating", "name": "Lab & Radiology"},
#         "Radiology Survey": {"field": "r_s_07", "name": "Radiology"},
#         "Laboratory Survey": {"field": "lab_08", "name": "Laboratory"},
#         "OR Survey": {"field": "or_012", "name": "OR"},
#         "Maternity Survey": {"field": "l_s_014", "name": "Maternity"},
#     }

#     sentiment_map = {
#         "very good": "happy",
#         "good": "happy",
#         "very satisfied": "happy",
#         "satisfied": "happy",
#         "satisfy": "happy",      # typo variant
#         "statisfy": "happy",     # typo variant
#         "fair": "unhappy",
#         "poor": "unhappy",
#         "dissatisfied": "unhappy",
#         "very dissatisfied": "unhappy",
#         # anything else (including "n/a") is ignored
#     }

#     dashboard_data = {}

#     for doctype, conf in survey_config.items():
#         fieldname = conf["field"]
#         category = conf["name"]
#         happy_count = 0
#         unhappy_count = 0

#         try:
#             entries = frappe.get_all(doctype, fields=[fieldname], ignore_permissions=True)
#             for e in entries:
#                 resp = e.get(fieldname)
#                 if not resp or not isinstance(resp, str):
#                     continue
#                 key = resp.strip().lower()
#                 s = sentiment_map.get(key)
#                 if s == "happy":
#                     happy_count += 1
#                 elif s == "unhappy":
#                     unhappy_count += 1
#         except Exception:
#             frappe.log_error(frappe.get_traceback(), f"Error loading {doctype}")
#             # leave counts at zero

#         dashboard_data[category] = {
#             "happy": happy_count,
#             "unhappy": unhappy_count
#         }

#     return dashboard_data

import frappe

@frappe.whitelist()
def get_patient_survey_data():
    survey_config = {
        "IPD Survey": {"field": "name_4", "name": "IPD"},
        "OPD Survey": {"field": "name_06", "name": "OPD"},
        "Pharmacy Survey": {"field": "name_001", "name": "Pharmacy"},
        "Laboratory And Radiology  Survey": {"field": "overall_experience_rating", "name": "Lab & Radiology"},
        "Radiology Survey": {"field": "r_s_07", "name": "Radiology"},
        "Laboratory Survey": {"field": "lab_08", "name": "Laboratory"},
        "OR Survey": {"field": "or_012", "name": "OR"},
        "Maternity Survey": {"field": "l_s_014", "name": "Maternity"},
    }

    # 👇 Exclude this doctype completely (note the two spaces in the name)
    EXCLUDE_DOCTYPES = {"Laboratory And Radiology  Survey"}

    survey_comments_cfg = {
        "IPD Survey": {"fields": [f"why_{i}" for i in range(1, 13)], "name": "IPD"},
        "OPD Survey": {"fields": [f"why_{i}" for i in range(1, 11)], "name": "OPD"},
        "Pharmacy Survey": {"fields": [f"why_{i}" for i in range(1, 11)], "name": "Pharmacy"},
        "Radiology Survey": {"fields": [f"why_{i}" for i in range(1, 8)], "name": "Radiology"},
        "Laboratory Survey": {"fields": [f"lab_why_0{i}" for i in range(1, 9)], "name": "Laboratory"},
        "OR Survey": {"fields": [f"or_why_0{i}" for i in range(1, 13)], "name": "OR"},
        "Maternity Survey": {"fields": [f"l_s_why_0{i}" for i in range(1, 15)], "name": "Maternity"},
    }

    sentiment_map = {
        "very good": "happy", "good": "happy", "very satisfied": "happy",
        "satisfied": "happy", "satisfy": "happy", "statisfy": "happy",
        "fair": "unhappy", "poor": "unhappy", "dissatisfied": "unhappy", "very dissatisfied": "unhappy",
    }

    dashboard_data, comments_by_category = {}, {}

    for doctype, conf in survey_config.items():
        # ✅ Skip excluded doctypes entirely
        if doctype in EXCLUDE_DOCTYPES:
            continue

        fieldname = conf["field"]
        category = conf["name"]

        comment_fields = (survey_comments_cfg.get(doctype) or {}).get("fields", [])
        fields = [fieldname] + comment_fields if comment_fields else [fieldname]

        happy_count = unhappy_count = 0
        collected_comments = []

        try:
            entries = frappe.get_all(doctype, fields=fields, ignore_permissions=True)
            for e in entries:
                resp = e.get(fieldname)
                if isinstance(resp, str):
                    key = resp.strip().lower()
                    s = sentiment_map.get(key)
                    if s == "happy": happy_count += 1
                    elif s == "unhappy": unhappy_count += 1

                for cf in comment_fields:
                    val = e.get(cf)
                    if isinstance(val, str):
                        val = val.strip()
                        if val:
                            collected_comments.append(val)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Error loading {doctype}")

        # de-duplicate while preserving order
        if collected_comments:
            seen = set()
            collected_comments = [c for c in collected_comments if not (c in seen or seen.add(c))]

        dashboard_data[category] = {"happy": happy_count, "unhappy": unhappy_count}
        if collected_comments:
            comments_by_category[category] = collected_comments

    return dashboard_data, comments_by_category

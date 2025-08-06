# # Poor
# # Fair
# # Very good
# # N/A
import frappe

@frappe.whitelist()
def get_patient_survey_data():
    """
    Fetches and processes patient survey data from multiple doctypes,
    categorizing responses into 'happy' and 'unhappy' sentiments.
    Returns:
        dict: {
            "IPD": {"happy": 26, "unhappy": 8},
            "OPD": {"happy": 32, "unhappy": 6},
            ...
        }
    """
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

    sentiment_map = {
        "very good": "happy",
        "good": "happy",
        "very satisfied": "happy",
        "satisfied": "happy",
        "satisfy": "happy",      # typo variant
        "statisfy": "happy",     # typo variant
        "fair": "unhappy",
        "poor": "unhappy",
        "dissatisfied": "unhappy",
        "very dissatisfied": "unhappy",
        # anything else (including "n/a") is ignored
    }

    dashboard_data = {}

    for doctype, conf in survey_config.items():
        fieldname = conf["field"]
        category = conf["name"]
        happy_count = 0
        unhappy_count = 0

        try:
            entries = frappe.get_all(doctype, fields=[fieldname], ignore_permissions=True)
            for e in entries:
                resp = e.get(fieldname)
                if not resp or not isinstance(resp, str):
                    continue
                key = resp.strip().lower()
                s = sentiment_map.get(key)
                if s == "happy":
                    happy_count += 1
                elif s == "unhappy":
                    unhappy_count += 1
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Error loading {doctype}")
            # leave counts at zero

        dashboard_data[category] = {
            "happy": happy_count,
            "unhappy": unhappy_count
        }

    return dashboard_data

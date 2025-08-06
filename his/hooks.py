from . import __version__ as app_version

app_name = "his"
app_title = "HIS"
app_publisher = "Rasiin Tech"
app_description = "Rasiin HIS"
app_email = "rasiin"
app_license = "MIT"
required_apps = ["erpnext","healthcare"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = ["/assets/his/css/his.css"]
app_include_js = ["/assets/his/js/his.js"]


# include js, css files in header of web template
# web_include_css = "/assets/his/css/his.css"
# web_include_js = "/assets/his/js/his.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "his/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Sales Invoice" : "public/js/sales_invoice.js" , 
    "Patient" : "public/js/patient.js" ,  
    "Patient Appointment" : "public/js/patient_encounter.js" , 
    "Patient Encounter" : "public/js/encounter_steps.js",
    "Sample Collection": "public/js/sample.js",
    "Inpatient Record": "public/js/inpatient_record.js"


    
    
    }
doctype_list_js = {
    "Sales Order" : "public/js/opd_order_list.js", 
    "Inpatient Record": "public/js/inpatient_record_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#   "Role": "home_page"
# }

website_route_rules = [
    {"from_route": "/screen/screen/<roomname>", "to_route": "screen/screen"},
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#   "methods": "his.utils.jinja_methods",
#   "filters": "his.utils.jinja_filters"
# }

# Installation
# ------------


# before_install = "his.install.before_install"
after_install = "his.setup.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "his.uninstall.before_uninstall"
# after_uninstall = "his.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "his.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#   "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#   "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    # "Item": "his.api.retail_setup.CustomItem",
    "Clinical Procedure": "his.api.clinical_procedure.CustomClinicalProcedure",
     "Sales Order": "his.override.sales_order.CustomSalesOrder",
      "Sales Invoice": "his.override.sales_invoice.CustomSalesInvoice"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Patient Encounter": {
        "before_validate": "his.api.patient_encounter.set_so_values_from_db",
        "on_update": "his.api.patient_encounter.enqueue_sales_orders",
        "on_update_after_submit": "his.api.patient_encounter.enqueue_sales_orders",
        "after_insert" : [
            "his.api.patient_encounter.close_que_after_save_pe",
            "his.api.sales_invoice_refund_control.update_que_status",
        ]
    },
    #     "Doctor Plan": {
    #     "before_validate": "his.api.doctor_plan.set_so_values_from_db",
    #     "on_update": "his.api.doctor_plan.enqueue_sales_orders",
    #     "on_update_after_submit": "his.api.doctor_plan.enqueue_sales_orders",
    # },
    #     "Inpatient Order": {
    #     "before_validate": "his.api.inpatient_order.set_so_values_from_db",
    #     "on_update": "his.api.inpatient_order.enqueue_sales_orders",
    #     "on_update_after_submit": "his.api.inpatient_order.enqueue_sales_orders",
    # },
    # "Emergency": {
    #     "before_validate": "his.api.emergency.set_so_values_from_db",
    #     "on_update": "his.api.emergency.enqueue_sales_orders",
    #     "on_update_after_submit": "his.api.emergency.enqueue_sales_orders",
    # },
    # "Que": {
    #     "before_save": 
    #     ["his.api.Que_to_make_sales_invove.make_invoice",
    #     "his.api.Que_to_fee_validity.make_fee_validity",
    #     "his.api.que_token_number.token_numebr"]
        
        
    # },
    "Sample Collection": {
        "before_insert": ["his.api.make_sample_collection.token_numebr"],
        "on_submit": ["his.api.create_lab_test.create_lab_tests"]
      
        
    },
    "Patient": {
            "before_save": ["his.api.make_uppercase.make_uppercase", "his.api.patient.age_todate" ],
            "after_insert": ["his.api.patient.invoice_registration"]
            
    },
      "Inpatient Record": {
            "before_save": "his.api.admit.invoice_addition_beds",
            
    },
    "Journal Entry" : {
    #   "before_cancel" : "his.api.journal_entry.cancell_sales_invoice"
    },
   "Customer" : {
    "before_insert" : "his.api.credit_limit.credit_limit"
	},
    "Lab Result": {
        "on_submit": "his.api.sales_invoice_refund_control.update_lab_results_status",
        "on_cancel": "his.api.sales_invoice_refund_control.handle_lab_result_cancellation",
    },
    
    "Radiology": {
        "on_submit": "his.api.sales_invoice_refund_control.update_imaging_results_status",
        "on_cancel": "his.api.sales_invoice_refund_control.handle_imaging_result_cancellation"
    },
    "Clinical Procedure":{
        "on_submit": [
            "his.api.clinical_procedure.make_anethesia",
            "his.api.sales_invoice_refund_control.update_clinical_procedure"
        ],
        "on_cancel": "his.api.sales_invoice_refund_control.handle_clinical_procedure_cancellation"
    },
    "Sales Invoice": {
            "on_submit": [

                # "his.api.journal_entry.insurance",
                # "his.api.journal_entry.employee_due",
                # "his.api.journal_entry.free_que_expense",
                "his.api.make_sample_collection.make_sample_collection",
                # "his.api.sales_invoice.real",
                
                "his.api.clinical_procedure.clinical_pro_comm",
                
                "his.api.radiology.create_radiolgy",
                # "his.api.radiology.make_cytology",
                # "his.api.ot_prepation.make_ot_prepararion",
                # "his.api.egd.make_egd",
                # "his.api.clinical_procedure.make_procedures"
                
                ],
                # "before_cancel" : "his.api.journal_entry.cancell_journal"
            
    },
    "Stock Reconciliation" : {
        # "on_submit" : "his.api.retail_setup.stock_reconciliation_retail",
    },
    "Purchase Invoice" : {
        # "on_submit" : "his.api.retail_setup.purchase_invoice_retail",
    },
    # "Patient Encounter" : {
    # # "before_save" : "his.api.patient_encounter.close_que_after_save_pe",
    # #   
    # }
    
#"Patient": {"after_insert": "his.api.patient.invoice_registration"}
    
#   "*": {
#       "on_update": "method",
#       "on_cancel": "method",
#       "on_trash": "method"
#   }
}

# Scheduled Tasks
# ---------------
scheduler_events = {
       "cron": {
	"* 16 * * *": [
		 "his.api.send_sms_follow_up.sendsms",
       
        

		
	],
	   }
}

# scheduler_events = {
#   "all": [
#       "his.tasks.all"
#   ],
#   "daily": [
#       "his.tasks.daily"
#   ],
#   "hourly": [
#       "his.tasks.hourly"
#   ],
#   "weekly": [
#       "his.tasks.weekly"
#   ],
#   "monthly": [
#       "his.tasks.monthly"
#   ],
# }

# Testing
# -------

# before_tests = "his.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "healthcare.healthcare.doctype.lab_test.lab_test.create_multiple": "his.override.lab_test.create_multiple",
    "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_sales_return": "his.api.sales_invoice_refund_control.custom_make_sales_return"
}

# Client and Server Script Fixtures
fixtures = [
    {
        "doctype": doctype,
        "filters": [["module", "=", "HIS"]]
    }
    for doctype in [
        "Client Script",
        "Server Script",
        "Custom Field",
        "Print Format",
        # "Home Page"  # Uncomment if needed
    ]
] + [
    # {"doctype": "Role Profile"}

]

# fixtures = [
    # {
    #     "doctype": "Client Script",
    #     "filters": [
    #         ["module", "=", "HIS"]
    #     ]
    # },
    # {
    #     "doctype": "Server Script",
    #     "filters": [
    #         ["module", "=", "HIS"]
    #     ]
    # },
    # {
    #     "doctype": "Custom Field",
    #     "filters": [
    #         ["module", "=", "HIS"]
    #     ]
    # },
    # {
    #     "doctype": "Property Setter",
    #     "filters": [["module", "=", "his"]]
    # },
    # {
    #     "doctype": "Print Format",
    #     "filters": [
    #         ["module", "=", "HIS"]
    #     ]
    # },
    # {
    #     "doctype": "Role Profile"
    # }
    # {
    #     "doctype": "Home Page",
    #     "filters": [
    #         ["module", "=", "HIS"]
    #     ]
    # },
# ]


#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#   "Task": "his.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]


# User Data Protection
# --------------------

# user_data_fields = [
#   {
#       "doctype": "{doctype_1}",
#       "filter_by": "{filter_by}",
#       "redact_fields": ["{field_1}", "{field_2}"],
#       "partial": 1,
#   },
#   {
#       "doctype": "{doctype_2}",
#       "filter_by": "{filter_by}",
#       "partial": 1,
#   },
#   {
#       "doctype": "{doctype_3}",
#       "strict": False,
#   },
#   {
#       "doctype": "{doctype_4}"
#   }
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#   "his.auth.validate"
# ]

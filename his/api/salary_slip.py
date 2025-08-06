# import frappe
# import json

# @frappe.whitelist()
# def get_salary_slip():
#     try:
#         # Fetch salary slip data along with earnings and deductions
#         salary_slips = frappe.db.get_list(
#             "Salary Slip",
#             fields=["name", "employee_name", "posting_date", "start_date", "end_date"]
#         )
        
#         result = []
        
#         for slip in salary_slips:
#             # Fetch earnings rows
#             earnings = frappe.db.get_list(
#                 "Salary Detail",
#                 filters={"parent": slip["name"], "parentfield": "earnings"},
#                 fields=["salary_component", "amount"]
#             )
            
#             # Fetch deductions rows
#             deductions = frappe.db.get_list(
#                 "Salary Detail",
#                 filters={"parent": slip["name"], "parentfield": "deductions"},
#                 fields=["salary_component", "amount"]
#             )
            
#             # Add to the result
#             result.append({
#                 "salary_slip": slip,
#                 "earnings": earnings,
#                 "deductions": deductions
#             })
        
#         if result:
#             return {"status": "Success", "data": result}
#         else:
#             return {"status": "Error", "message": "No salary slips found"}
    
#     except Exception as e:
#         frappe.errprint(f"Error: {e}")
#         return {"status": "Error", "message": str(e)}


import frappe
import json

@frappe.whitelist()
def get_salary_slip(employee_id):
    try:
        # Verify if the employee exists
        employee = frappe.db.exists("Employee", {"name": employee_id})
        
        if not employee:
            return {"status": "Error", "message": "Employee not found for the given Employee ID"}
        
        # Fetch salary slips for the given Employee ID
        salary_slips = frappe.db.get_list(
            "Salary Slip",
            filters={"employee": employee_id},
            fields=["name", "employee_name", "posting_date", "start_date", "end_date"]
        )
        
        result = []
        
        for slip in salary_slips:
            # Fetch earnings rows
            earnings = frappe.db.get_list(
                "Salary Detail",
                filters={"parent": slip["name"], "parentfield": "earnings"},
                fields=["salary_component", "amount"]
            )
            
            # Fetch deductions rows
            deductions = frappe.db.get_list(
                "Salary Detail",
                filters={"parent": slip["name"], "parentfield": "deductions"},
                fields=["salary_component", "amount"]
            )
            
            # Add to the result
            result.append({
                "salary_slip": slip,
                "earnings": earnings,
                "deductions": deductions
            })
        
        if result:
            return {"status": "Success", "data": result}
        else:
            return {"status": "Error", "message": "No salary slips found for the given Employee ID"}
    
    except Exception as e:
        frappe.errprint(f"Error: {e}")
        return {"status": "Error", "message": str(e)}





@frappe.whitelist()
def get_employee_attendance(employee_id):
    # Fetch employee's attendance details, such as name, date, shift, in_time, and out_time
    attendance_data = frappe.db.get_all('Attendance', filters={'employee': employee_id},
                                        fields=['employee_name', 'attendance_date', 'shift', 'in_time', 'out_time'])

    if not attendance_data:
        frappe.throw(_("No attendance data found for employee: {0}").format(employee_id))

    return attendance_data

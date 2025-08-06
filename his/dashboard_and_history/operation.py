from collections import defaultdict
import frappe
from frappe.utils import getdate
from frappe.desk.query_report import run

from frappe.utils.pdf import get_pdf
from frappe.www.printview import get_print_style
from frappe.utils import getdate
from erpnext.accounts.utils import get_balance_on

company = frappe.defaults.get_user_default("company")
abbr    = frappe.db.get_value("Company" , company , "abbr")
curren =  frappe.db.get_value("Company" , company , "default_currency")
base_template_path = "frappe/www/printview.html"


@frappe.whitelist()
def get_opetations(from_date =getdate(), to_date=getdate() , view = True  ):
    profit = get_profit_and_los(getdate(from_date) , getdate(to_date))
    acc_balnces = get_accounts_balance(getdate(from_date) ,getdate(to_date))
    served_dep  = get_department_served(getdate(from_date) , getdate(to_date))
    total_ques  = get_que_list(getdate(from_date) , getdate(to_date))
    total_admitted_list  = get_admitted_list(getdate(from_date) , getdate(to_date))
    account_tran = get_accounts_history(getdate(from_date) , getdate(to_date))
    doctor_sales = get_doctor_sale(getdate(from_date ),getdate(to_date))
    doctor_sales_ipd = get_doctor_sale_ipd(getdate(from_date ),getdate(to_date))
    patient_by_doctor = get_patient_by_doctor(getdate(from_date ),getdate(to_date))
    
    cash_balance = get_cash_balance(getdate(from_date) , getdate(to_date))
    bank_balance = get_bank_balance(getdate(from_date) , getdate(to_date))
    total_balance = get_total_balance(getdate(from_date) , getdate(to_date))
    doctors = get_total_doctor(getdate(from_date) , getdate(to_date))

    report_html_data = frappe.render_template(
    "his/templates/report/operation.html",
    {
      "profit" : profit,
      "acc_balnces" : acc_balnces,
      "served_dep" : served_dep,
      "total_ques" : total_ques,
      "cash_in_hand" : cash_balance,
      "cash_in_bank" : bank_balance,
      "total_balance" : total_balance,
      "total_admitted_list" : total_admitted_list,
      "account_tran" : account_tran,
      "doctors" : doctors,
      "doctor_sales" : doctor_sales,
       "doctor_sales_ipd" : doctor_sales_ipd,
      "curreny" :  curren,
      "from_date" : from_date,
      "patient_by_doctor" : patient_by_doctor,
      "to_date": to_date
    }
)
    html = frappe.render_template(
        base_template_path,
        {"body": report_html_data ,"css" : get_print_style() , "title": "Statement For "},
    )
    if view:
        return report_html_data
    return get_pdf(html , {"orientation": "Landscape"})

download_from_date = ""
download_to_date = ""

@frappe.whitelist()
def assign_date_to_download(from_date ,to_date):
    
    # return True
    global download_from_date 
    global download_to_date 
    download_from_date = getdate(from_date)
    download_to_date = getdate(to_date)
    

    

@frappe.whitelist()
def download_report():
    # frappe.errprint(str(download_from_date))
    # pass
    # frappe.msgprint(str(download_from_date))
    report = get_opetations(from_date=download_from_date , to_date= download_to_date , view= False)
    if report:
        
        frappe.local.response.filename = "Operation report.pdf"
        frappe.local.response.filecontent = report
        frappe.local.response.type = "download"
    else:
        return False

@frappe.whitelist()
def send_emails():

    report = get_opetations(False)

    if report:
        
        context = get_context()
        filename = frappe.render_template("operation report", context)
        attachments = [{"fname": filename + ".pdf", "fcontent": report}]

        recipients = ['engxirsi38@gmail.com']
        if  recipients:
            

            subject = frappe.render_template("Daily Opeartion", context)
            message = frappe.render_template(f"This is Daily Report {company} on Date {frappe.format(getdate())}", context)

            frappe.enqueue(
                queue="short",
                method=frappe.sendmail,
                recipients=recipients,
                sender=frappe.session.user,
            
                subject=subject,
                message=message,
                now=True,
                reference_doctype="Process Statement Of Accounts",
                reference_name="daily Opeartion",
                attachments=attachments,
            )

            return True
def get_context():

    return {
        "doc": "Daily Operation",
        "customer": "",
        "frappe": frappe.utils,
    }

def get_patient_by_doctor(from_date , to_date):
    report_gl = frappe.get_doc("Report", "OPD Report")
   
    
    report_gl_filters = {
        "from_date": from_date,
        "to_date": to_date,

        # "group_by": "Group by Voucher (Consolidated)",
    }

    
   
    cols , data = report_gl.get_data(limit=500, user="Administrator", filters=report_gl_filters, as_dict=True)
    # frappe.errprint(data[-1])
   
    return data[:-1]

def get_profit_and_los(from_date , to_date):
    report_gl = frappe.get_doc("Report", "Profit and Loss Statement")
   
    
    report_gl_filters = {
        
        "company": company,
        
    
        "from_date": from_date,
        "to_date": to_date,
        "filter_based_on" : "Date Range",
        "period_start_date" : from_date,
        "period_end_date" : to_date,
        "periodicity" : "Yearly"
        # "group_by": "Group by Voucher (Consolidated)",
    }

    
   
    data = run("Profit and Loss Statement" , report_gl_filters)['report_summary']
   
    return data

def get_total_doctor(from_date , to_date):
    doctor = frappe.db.sql(f"""
   
    select COUNT(DISTINCT ref_practitioner)  as doctors from   `tabSales Invoice`
    
    where posting_date between '{from_date}' and '{to_date}'
    

    """ , as_dict = 1) 

    return doctor



def get_accounts_history(from_date , to_date):
    account_types = ['1100 - Cash In Hand - HH' , '1200 - Bank Accounts - HH' , '1300 - Accounts Receivable - HH' , '2100 - Accounts Payable - HH']
    # account = frappe.get_list(
    # "Account",
    # filters={"account_type": "Bank", "is_group": 0},
    # fields=["name"],
    # as_list=False  # Use False to get dictionaries instead of tuples
    # )
    # account_types = [acc["name"] for acc in account]
    report_gl = frappe.get_doc("Report", "General Ledger")
    balances = []
    
    for type in account_types:
        total = 0
    
        report_gl_filters = {
            
            "company": company,
            
        
            "from_date": from_date,
            "to_date": to_date,
            "account" : [type],
            "group_by": "Group by Voucher (Consolidated)",
            # "group_by": "Group by Voucher (Consolidated)",
            }
        cols , data = report_gl.get_data(limit=500, user="Administrator", filters=report_gl_filters, as_dict=True)
        d = data
        # for d in data:
          
                
                # continue
            # total = total + (d.balance)
                
      
        balances.append({"account":type,"opening" : d[0].balance ,"total_debit" : d[-2].debit , "total_credit" : d[-2].credit , "balance" : d[-1].balance})


    
    # frappe.errprint(balances)
    return balances


def get_accounts_balance(from_date , to_date):
    account_types = ['Cash' , 'Bank' , 'Receivable' , 'Payable']
    report_gl = frappe.get_doc("Report", "Account Balance")
    balances = []
    
    for type in account_types:
        total = 0
    
        report_gl_filters = {
            
            "company": company,
            
        
            "date": to_date,
            "account_type": type,
            
            # "group_by": "Group by Voucher (Consolidated)",
            }
        cols , data = report_gl.get_data(limit=500, user="Administrator", filters=report_gl_filters, as_dict=True)
        if type == "Cash":
            balances.append({"account" : type ,"balance" : data[0].balance})
        else:
            for d in data:
            
                if not frappe.db.get_value("Account" , d.account , 'is_group'):
                    balance_str = d.balance
                    if balance_str:
                        try:
                            balance = float(balance_str)
                            total += balance
                        except ValueError:
                            # Handle the case where balance is not a valid float
                            continue
                
      
        balances.append({"account" : type ,"balance" : total})


    # balances[0]['balance']+= balances[1]['balance']
   
    return balances

def get_department_served(from_date , to_date):
    data = frappe.db.sql(f""" 

    select  source_order , count(source_order) as number from `tabSales Invoice` where posting_date between '{from_date}' and '{to_date}' and docstatus = 1 GROUP BY patient, source_order ;
                         

    ;""", as_dict =1)
    # data[]
    # data[0]['OPD'] +=  data[0]['ER']
    # Initialize totals
    totals = {}

    # Iterate through the data and update totals
    for item in data:
        source_order = item['source_order']
        totals[source_order] = totals.get(source_order, 0) + 1

    # # for d in data:

    data = [totals]
    # frappe.errprint(totals)
    return data

def get_que_list(from_date , to_date):
    data = frappe.db.sql(f""" 

    select  count(*) as number from `tabQue` where date between '{from_date}' and '{to_date}' and status != "Canceled" ;
                         

    ;""", as_dict =1)
    return data


def get_cash_balance(from_date , to_date):
    data = frappe.db.sql(f""" 
               
    select 
        
            SUM(G.debit) - SUM(G.credit) as balance
            from `tabGL Entry` G, `tabAccount` A 
            where G.posting_date   between  '{from_date}' and '{to_date}'
            and A.name = G.account
            and A.Account_type in ("Cash")
        
            and G.is_cancelled=0

            group by  A.Account_type 
            ;
    ;""", as_dict =1)
    return data
    
    # return get_balance_on(
                        
	# 					date = getdate(),
    #                     account= "1100 - Cash In Hand - HH"
    #                     )
def get_bank_balance(from_date , to_date):
    data = frappe.db.sql(f""" 

      select 
        
            SUM(G.debit) - SUM(G.credit) as balance
            from `tabGL Entry` G, `tabAccount` A 
            where G.posting_date   between  '{from_date}' and '{to_date}'
            and A.name = G.account
            and A.Account_type in ("Bank")
        
            and G.is_cancelled=0

            group by  A.Account_type 
            ;               

    ;""", as_dict =1)
    return data
def get_total_balance(from_date , to_date):
    data = frappe.db.sql(f""" 

      select 
        
            SUM(G.debit) - SUM(G.credit) as balance
            from `tabGL Entry` G, `tabAccount` A 
            where G.posting_date   between  '{from_date}' and '{to_date}'
            and A.name = G.account
            and A.Account_type in ("Bank", "Cash")
        
            and G.is_cancelled=0

            group by  A.Account_type 
            ;               

    ;""", as_dict =1)
    return data
    
    # return get_balance_on(
                        
	# 					date = getdate(),
    #                     account= "1200 - Bank Accounts - HH"
    #                     )

def get_admitted_list(from_date , to_date):
    data = frappe.db.sql(f""" 

    select  count(*) as number from `tabInpatient Record` where scheduled_date between '{from_date}' and '{to_date}' and status = "Admitted" ;
                         

    ;""", as_dict =1)
    return data
    
def get_doctor_sale(from_date , to_date):
    report_gl = frappe.get_doc("Report", "Doctor Daily Sales")
    report_gl_filters = {
        
       
        
    
        "from_date": from_date,
        "to_date": to_date,
        "source" :"OPD"
        
        # "group_by": "Group by Voucher (Consolidated)",
    }

    
   
    cols , data = report_gl.get_data(limit=500, user="Administrator", filters=report_gl_filters, as_dict=True)
    cols = []
 
    # data = [{'Dr Abdulkadir Sheikh' : [{"BED CHARGES" : [1.0,4000.0],'Consultation' : [ 3.0, 5000.0], 'Services' : [ 2.0, 5000.0]}]},
            
            
    #         {'Dr. Abdirahman Salad' : [{"BED CHARGES" : [1.0,4000.0], 'Services' : [ 2.0, 5000.0]}]}
    #         ]
    result_dict = defaultdict(lambda: defaultdict(list))

    for item in data:
        practitioner = item['ref_practitioner']
        item_group = item['item_group']
        patient = item['patient']
        base_net_amount = item['base_net_amount']

        result_dict[practitioner][item_group].append([patient, base_net_amount])

    # Convert defaultdict to a regular dictionary
    result = [{practitioner: [{item_group: values} for item_group, values in groups.items()]} for practitioner, groups in result_dict.items()]
    g_total = 0
    g_count =0
    totals_per_group = {}
    for r in result:
        total = 0
        count = 0
        ref_pract = list(r.keys())[0]
        if ref_pract != "Total":
            for i in r[ref_pract]:
                for j in i:
                    total += i[j][0][1]
                    count += i[j][0][0]
                    g_total += i[j][0][1]
                    g_count += i[j][0][0]
                    if j  in totals_per_group:
                        totals_per_group[j] = totals_per_group[j] +  i[j][0][1]
                        
                    else:
                        totals_per_group[j] = i[j][0][1]
                        
                    # frappe.errprint(totals_per_group)
                
            r[ref_pract].append({"Total" : [[count,total]]})
    # result = sorted(result, key=lambda x: max(len(v) for v in x.values()), reverse=True)


    # frappe.errprint(totals_per_group)
    for col in result:
        
        for key , value in col.items():
            
            for va in value:
        
                i = list(va.keys())[0]
                if i  and i not in cols and i != "Total":
                    cols.append(i)
            
                # for i , j in va.items():
        
                #     if i  and i not in cols:
                #         cols.append(k)
    
    # cols.append("Others")
    # cols.append("Total Revenue")
    cols.append("Total")
    return [result ,cols , [g_count, g_total] , totals_per_group]
    

def get_doctor_sale_ipd(from_date , to_date):
    report_gl = frappe.get_doc("Report", "Doctor Daily Sales")
    report_gl_filters = {
        
       
        
    
        "from_date": from_date,
        "to_date": to_date,
        "source" :"IPD"
        
        # "group_by": "Group by Voucher (Consolidated)",
    }

    
   
    cols , data = report_gl.get_data(limit=500, user="Administrator", filters=report_gl_filters, as_dict=True)
    cols = []
 
    # data = [{'Dr Abdulkadir Sheikh' : [{"BED CHARGES" : [1.0,4000.0],'Consultation' : [ 3.0, 5000.0], 'Services' : [ 2.0, 5000.0]}]},
            
            
    #         {'Dr. Abdirahman Salad' : [{"BED CHARGES" : [1.0,4000.0], 'Services' : [ 2.0, 5000.0]}]}
    #         ]
    result_dict = defaultdict(lambda: defaultdict(list))

    for item in data:
        practitioner = item['ref_practitioner']
        item_group = item['item_group']
        patient = item['patient']
        base_net_amount = item['base_net_amount']

        result_dict[practitioner][item_group].append([patient, base_net_amount])

    # Convert defaultdict to a regular dictionary
    result = [{practitioner: [{item_group: values} for item_group, values in groups.items()]} for practitioner, groups in result_dict.items()]
    g_total = 0
    g_count =0
    totals_per_group ={}
    for r in result:
        total = 0
        count = 0
        ref_pract = list(r.keys())[0]
        if ref_pract != "Total":
            for i in r[ref_pract]:
                for j in i:
                    total += i[j][0][1]
                    count += i[j][0][0]
                    g_total += i[j][0][1]
                    g_count += i[j][0][0]
                    if j  in totals_per_group:
                        totals_per_group[j] = totals_per_group[j] +  i[j][0][1]
                        
                    else:
                        totals_per_group[j] = i[j][0][1]
                        
                
            r[ref_pract].append({"Total" : [[count,total]]})
    # result = sorted(result, key=lambda x: max(len(v) for v in x.values()), reverse=True)


    # frappe.errprint(result)
    for col in result:
        
        for key , value in col.items():
            
            for va in value:
        
                i = list(va.keys())[0]
                if i  and i not in cols and i != "Total":
                    cols.append(i)
            
                # for i , j in va.items():
        
                #     if i  and i not in cols:
                #         cols.append(k)
    
    # cols.append("Others")
    # cols.append("Total Revenue")
    cols.append("Total")
    return [result ,cols , [g_count, g_total] , totals_per_group]
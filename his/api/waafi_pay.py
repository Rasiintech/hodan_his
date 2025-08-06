import requests
import datetime
import json
import frappe

@frappe.whitelist()
def waafi_pay(mobile_no, patient="None" ,  doctor="None" , date="" , charge=0):
    patient = frappe.form_dict.patient
    doctor = frappe.form_dict.doctor
    date = frappe.form_dict.date
    charge = frappe.form_dict.charge
    # mobile_no = frappe.db.get_value("Patient", patient , "mobile_no")
    if mobile_no.startswith('0'):
        mobile_no = mobile_no[1:]
    mobile_no = "252" + mobile_no
    payload = {
        "schemaVersion": "1.0",
        "requestId": "77919264891",
        "timestamp": "2024-06-2 Africa",
        "channelName": "WEB",
        "serviceName": "API_PREAUTHORIZE",
        "serviceParams": {
            "merchantUid": "M0913615",
            "apiUserId": "1007359",
            "apiKey": "API-1221796037AHX",
            "paymentMethod": "MWALLET_ACCOUNT",
            "payerInfo": {
                "accountNo": mobile_no
            },
            "transactionInfo": {
                "referenceId": "11111244",
                "invoiceId": "22222554",
                "amount": charge,
                "currency": "USD",
                "description": "wan diray"
        }
        }
        }
    waafipayResp = requests.request("POST", ' https://api.waafipay.net/asm',data= json.dumps(payload))
    respObj = waafipayResp.json()
    description = "Error Occured"
    # if 'description' in respObj:
    #     description = respObj['description']
   
    # print(str(respObj['responseCode']))
    responseCode =  respObj['responseCode']
    responseMsg = respObj['responseMsg']
    if responseMsg == "RCS_SUCCESS": 
        make_app(patient , doctor , date)
        return {"msg" : "Success" , "status" : "200" }
    else:
        if  'description' in respObj['params']:
            description = respObj['params']['description']
        if description == "Your account balance is not sufficient, mobile No: undefined":
            description = "Waan ka xunahay kuguma filna haraagaaga"
        
        return {"msg" :description , "status" : responseCode }



@frappe.whitelist()
def make_app(patient , doctor , date):
    patient = patient
    doctor = doctor
    date = date

    # patient = "PID-00001"
    # doctor = "Dr Mohamed"
    visit_charge = frappe.db.get_value("Healthcare Practitioner" , doctor, 'op_consulting_charge')
    que_doc = frappe.new_doc("Que")
    que_doc.patient = patient
    que_doc.practitioner = doctor
    que_doc.paid_amount = visit_charge
    que_doc.mode_of_payment = "Hormud Merchant"
    que_doc.source =  "Mobile App"
    que_doc.date = frappe.utils.getdate(date)
    que_doc.insert()
    # frappe.response['message'] = "Success"
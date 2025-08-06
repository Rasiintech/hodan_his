import requests
import datetime
import json
import frappe


# print(resp_dict1)
@frappe.whitelist()
def send_sms(mobile , message):
    payload = "grant_type=password&username=Hodanhospital&password=fj8TVv9w9eLUyknMUhyQpQ=="
    response = requests.request("POST", 'https://smsapi.hormuud.com/token', data=payload,
    headers={'content-type': "application/x-www-form-urlencoded"})
    resp_dict1 = json.loads(response.text)
    payload = {
    "senderid":"Hodan Hospital",
    "mobile":mobile,
    "message":message
    }
    sendsmsResp = requests.request("POST", 'https://smsapi.hormuud.com/api/SendSMS',data= json.dumps(payload),
    headers={'Content-Type':'application/json', 'Authorization': 'Bearer ' + resp_dict1['access_token']})

    respObj = json.loads(sendsmsResp.text)
    frappe.msgprint("Sent SMS")
    frappe.errprint(respObj)
    return respObj
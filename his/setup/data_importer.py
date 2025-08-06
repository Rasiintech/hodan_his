import frappe
import pandas as pd
def create_rooms():
    df = pd.read_excel(r'/home/rasiin/frappe-bench/rooms.xlsx')
   

    df= pd.DataFrame(df)
    data = df.to_dict(orient='records')
    for d in data:
        
        if not frappe.db.exists("Healthcare Service Unit Type" ,d['Service Unit Type']):
            # service_type = frappe.get_doc("Healthcare Service Unit Type")
            room_dict = {"doctype" : "Healthcare Service Unit Type"}
            for key , val in d.items():
            # [{'Service Unit Type': 'Room 14', 'Type': 'IPD', 'Allow Overlap': 0, 'Inpatient Occupancy': 1, 'Is Billable': 1, 'Item Code': 'Room 14', 'Item Group': 'Room', 'UOM': 'Hour', 'UOM Conversion in Hours': 24, 'Rate / UOM': 20, 'Description': 'Room 14'}, {'Service Unit Type': 'Emergency', 'Type': 'IPD', 'Allow Overlap': 0, 'Inpatient Occupancy': 1, 'Is Billable': 1, 'Item Code': 'Emergency', 'Item Group': 'Room', 'UOM': 'Hour', 'UOM Conversion in Hours': 24, 'Rate / UOM': 20, 'Description': 'Emergency'}
                # print("Creating OPD Service Unit")
                doc_f = frappe.get_meta("Healthcare Service Unit Type")
                
                for f in doc_f.fields:
                    if f.label == key:
                        # print(val)
                        room_dict[f.fieldname] = val
            # print(room_dict)
            service_type = frappe.get_doc(room_dict)
            service_type.insert()
             
                    
            
        
        print("Done")


import frappe
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos
import frappe
from frappe import _
from frappe.utils import flt
from erpnext.controllers.sales_and_purchase_return import get_returned_qty_map_for_row
from  his.api.clinical_procedure import clinical_pro_comm

def update_served_status(sales_invoice_number, item_names, is_served_value):
    """
    This function updates the 'is_served' field for the given sales invoice items.
    :param sales_invoice_number: The sales invoice number.
    :param item_names: List of item names (lab tests or imaging).
    :param is_served_value: The value to set for the 'is_served' field (1 or 0).
    """
    if not item_names:
        return  # Skip if no items to update

    # Remove duplicates to avoid redundant updates
    item_names = list(set(item_names))

    # Check if the Sales Invoice exists
    if not frappe.db.exists("Sales Invoice", sales_invoice_number):
        frappe.log_error(f"Sales Invoice {sales_invoice_number} not found", "update_served_status Error")
        return

    # Use parameterized queries to avoid SQL injection
    placeholders = ', '.join(['%s'] * len(item_names))  # Create placeholders for each item name
    
    try:
        # Update the served status
        frappe.db.sql("""
            UPDATE `tabSales Invoice Item`
            SET is_served = %s
            WHERE parent = %s AND item_name IN ({})
        """.format(placeholders), [is_served_value, sales_invoice_number] + item_names)
    except Exception as e:
        frappe.log_error(str(e), "update_served_status Error")
        return

    sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_number)
    if sales_invoice.journal_entry:
        journal_entry = frappe.get_doc("Journal Entry", sales_invoice.journal_entry)
    
        try:
            # Update the served status in the Commission Reference
            frappe.db.sql("""
                UPDATE `tabCommisions Reference`
                SET is_served = %s
                WHERE parent = %s AND item IN ({})
            """.format(placeholders), [is_served_value, journal_entry.name] + item_names)
        except Exception as e:
            frappe.log_error(str(e), "update_served_status Error")
            return

def update_lab_results_status(doc, method):
    if doc.reff_collection:
        sample_collection = frappe.get_doc("Sample Collection", doc.reff_collection)
        sales_invoice_number = sample_collection.reff_invoice
        
        # Ensure the sales invoice exists
        if not frappe.db.exists("Sales Invoice", sales_invoice_number):
            frappe.log_error(f"Sales Invoice {sales_invoice_number} not found", "update_lab_results_status Error")
            return
        
        # Collect lab test names
        lab_test_names = [doc.template] + [item.lab_test_name for item in doc.normal_test_items]
        
        # Update served status to 1 (served)
        update_served_status(sales_invoice_number, lab_test_names, 1)

def update_imaging_results_status(doc, method):
    if doc.reff_invoice:
        sales_invoice_number = doc.reff_invoice
        
        # Ensure the sales invoice exists
        if not frappe.db.exists("Sales Invoice", sales_invoice_number):
            frappe.log_error(f"Sales Invoice {sales_invoice_number} not found", "update_imaging_results_status Error")
            return
        
        item_name = doc.eximination
        
        # Update served status to 1 (served) for imaging result
        update_served_status(sales_invoice_number, [item_name], 1)

def update_que_status(doc, method=None):
    if doc.que:
        # Get the "Que" document
        if not frappe.db.exists("Que", doc.que):
            frappe.log_error(f"Que {doc.que} not found", "update_que_status Error")
            return
        
        que = frappe.get_doc("Que", doc.que)
        
        if que.status == "Closed":
            sales_invoice_number = que.sales_invoice
            
            # Get the associated "Sales Invoice" document    
            if not frappe.db.exists("Sales Invoice", sales_invoice_number):
                frappe.log_error(f"Sales Invoice {sales_invoice_number} not found", "update_que_status Error")
                return
            
            sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_number)
            
            # Collect item names (or other fields) from the Sales Invoice Item child table
            item_names = [item.item_code for item in sales_invoice.items]
            
            # Update served status to 1 (served) for imaging result
            update_served_status(sales_invoice_number, item_names, 1)

def update_clinical_procedure(doc, method):
    patient = frappe.get_doc("Patient", doc.patient)
    inpatient_record = patient.inpatient_record  

    if inpatient_record == doc.inpatient_record:
        
        sales_invoices = frappe.get_list("Sales Invoice", filters={
            'patient': doc.patient
        })
        
        # Flag to check if no matching items were found
        no_match_found = True
        
        for invoice in sales_invoices:
            sales_invoice = frappe.get_doc("Sales Invoice", invoice.name)
            sales_invoice_number = sales_invoice.name
            
            # Find the matching item in the Sales Invoice
            matching_items = [item for item in sales_invoice.items if item.item_code == doc.procedure_template]
            
            if matching_items:
                for item in matching_items:
                    item_name = item.item_code  # Only the matched item_code
                    frappe.errprint(f"Found matching item in Sales Invoice: {sales_invoice_number}")
                    update_served_status(sales_invoice_number, [item_name], 1)
                
                # Set the flag to False as we've found a match
                no_match_found = False
        if no_match_found:
            frappe.log_error(f"No matching procedure template found for patient {doc.patient}", "update_clinical_procedure Error")
    
def handle_lab_result_cancellation(doc, method):
    if doc.reff_collection:
        sample_collection = frappe.get_doc("Sample Collection", doc.reff_collection)
        sales_invoice_number = sample_collection.reff_invoice
        
        # Ensure the sales invoice exists
        if not frappe.db.exists("Sales Invoice", sales_invoice_number):
            frappe.log_error(f"Sales Invoice {sales_invoice_number} not found", "handle_lab_result_cancellation Error")
            return
        
        # Collect lab test names
        lab_test_names = [doc.template] + [item.lab_test_name for item in doc.normal_test_items]
        
        # Update served status to 0 (not served) for cancelled lab results
        update_served_status(sales_invoice_number, lab_test_names, 0)

def handle_imaging_result_cancellation(doc, method):
    if doc.reff_invoice:
        sales_invoice_number = doc.reff_invoice
        
        # Ensure the sales invoice exists
        if not frappe.db.exists("Sales Invoice", sales_invoice_number):
            frappe.log_error(f"Sales Invoice {sales_invoice_number} not found", "handle_imaging_result_cancellation Error")
            return
        
        item_name = doc.eximination
        
        # Update served status to 0 (not served) for cancelled imaging results
        update_served_status(sales_invoice_number, [item_name], 0)

def handle_que_cancellation(doc, method):
    if doc.que:
        # Get the "Que" document
        if not frappe.db.exists("Que", doc.que):
            frappe.log_error(f"Que {doc.que} not found", "handle_que_cancellation Error")
            return
        
        que = frappe.get_doc("Que", doc.que)
        
        if que.status == "Canceled":
            sales_invoice_number = que.sales_invoice
            
            # Ensure the sales invoice exists
            if not frappe.db.exists("Sales Invoice", sales_invoice_number):
                frappe.log_error(f"Sales Invoice {sales_invoice_number} not found", "handle_que_cancellation Error")
                return
            
            # Get the associated "Sales Invoice" document    
            sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_number)
            
            # Collect item names (or other fields) from the Sales Invoice Item child table
            item_names = [item.item_code for item in sales_invoice.items]
            
            # Update served status to 0 (not served) for canceled items
            update_served_status(sales_invoice_number, item_names, 0)

def handle_clinical_procedure_cancellation(doc, method):
    patient = frappe.get_doc("Patient", doc.patient)
    inpatient_record = patient.inpatient_record  

    if inpatient_record == doc.inpatient_record:
        
        sales_invoices = frappe.get_list("Sales Invoice", filters={
            'patient': doc.patient
        })
        
        # Flag to check if no matching items were found
        no_match_found = True
        
        for invoice in sales_invoices:
            sales_invoice = frappe.get_doc("Sales Invoice", invoice.name)
            sales_invoice_number = sales_invoice.name
            
            # Find the matching item in the Sales Invoice
            matching_items = [item for item in sales_invoice.items if item.item_code == doc.procedure_template]
            
            if matching_items:
                for item in matching_items:
                    item_name = item.item_code  # Only the matched item_code
                    frappe.errprint(f"Found matching item in Sales Invoice: {sales_invoice_number}")
                    update_served_status(sales_invoice_number, [item_name], 0)
                
                # Set the flag to False as we've found a match
                no_match_found = False
        if no_match_found:
            frappe.log_error(f"No matching procedure template found for patient {doc.patient}", "handle_clinical_procedure_cancellation Error")
              
                
                
@frappe.whitelist()
def custom_make_sales_return(source_name, target_doc=None):
    return custom_make_return_doc("Sales Invoice", source_name, target_doc)
  

def custom_make_return_doc(doctype: str, source_name: str, target_doc=None):
    company = frappe.db.get_value("Delivery Note", source_name, "company")
    default_warehouse_for_sales_return = frappe.get_cached_value(
        "Company", company, "default_warehouse_for_sales_return"
    )

    def set_missing_values(source, target):
        doc = frappe.get_doc(target)
        doc.is_return = 1
        doc.return_against = source.name
        doc.set_warehouse = ""
        if doctype == "Sales Invoice" or doctype == "POS Invoice":
            doc.is_pos = source.is_pos

            # look for Print Heading "Credit Note"
            if not doc.select_print_heading:
                doc.select_print_heading = frappe.get_cached_value("Print Heading", _("Credit Note"))

        elif doctype == "Purchase Invoice":
            doc.select_print_heading = frappe.get_cached_value("Print Heading", _("Debit Note"))

        for tax in doc.get("taxes") or []:
            if tax.charge_type == "Actual":
                tax.tax_amount = -1 * tax.tax_amount

        if doc.get("is_return"):
            if doc.doctype == "Sales Invoice" or doc.doctype == "POS Invoice":
                doc.consolidated_invoice = ""
                doc.set("payments", [])
                for data in source.payments:
                    paid_amount = 0.00
                    base_paid_amount = 0.00
                    data.base_amount = flt(
                        data.amount * source.conversion_rate, source.precision("base_paid_amount")
                    )
                    paid_amount += data.amount
                    base_paid_amount += data.base_amount
                    doc.append(
                        "payments",
                        {
                            "mode_of_payment": data.mode_of_payment,
                            "type": data.type,
                            "amount": -1 * paid_amount,
                            "base_amount": -1 * base_paid_amount,
                            "account": data.account,
                            "default": data.default,
                        },
                    )
                if doc.is_pos:
                    doc.paid_amount = -1 * source.paid_amount
            elif doc.doctype == "Purchase Invoice":
                doc.paid_amount = -1 * source.paid_amount
                doc.base_paid_amount = -1 * source.base_paid_amount
                doc.payment_terms_template = ""
                doc.payment_schedule = []

        if doc.get("is_return") and hasattr(doc, "packed_items"):
            for d in doc.get("packed_items"):
                d.qty = d.qty * -1

        if doc.get("discount_amount"):
            doc.discount_amount = -1 * source.discount_amount

        if doctype != "Subcontracting Receipt":
            doc.run_method("calculate_taxes_and_totals")

    def update_item(source_doc, target_doc, source_parent):
        target_doc.qty = -1 * source_doc.qty

        if source_doc.serial_no:
            returned_serial_nos = get_returned_serial_nos(source_doc, source_parent)
            serial_nos = list(set(get_serial_nos(source_doc.serial_no)) - set(returned_serial_nos))
            if serial_nos:
                target_doc.serial_no = "\n".join(serial_nos)

        if source_doc.get("rejected_serial_no"):
            returned_serial_nos = get_returned_serial_nos(
                source_doc, source_parent, serial_no_field="rejected_serial_no"
            )
            rejected_serial_nos = list(
                set(get_serial_nos(source_doc.rejected_serial_no)) - set(returned_serial_nos)
            )
            if rejected_serial_nos:
                target_doc.rejected_serial_no = "\n".join(rejected_serial_nos)

        if doctype in ["Purchase Receipt", "Subcontracting Receipt"]:
            returned_qty_map = get_returned_qty_map_for_row(
                source_parent.name, source_parent.supplier, source_doc.name, doctype
            )

            if doctype == "Subcontracting Receipt":
                target_doc.received_qty = -1 * flt(source_doc.qty)
            else:
                target_doc.received_qty = -1 * flt(
                    source_doc.received_qty - (returned_qty_map.get("received_qty") or 0)
                )
                target_doc.rejected_qty = -1 * flt(
                    source_doc.rejected_qty - (returned_qty_map.get("rejected_qty") or 0)
                )

            target_doc.qty = -1 * flt(source_doc.qty - (returned_qty_map.get("qty") or 0))

            if hasattr(target_doc, "stock_qty"):
                target_doc.stock_qty = -1 * flt(
                    source_doc.stock_qty - (returned_qty_map.get("stock_qty") or 0)
                )
                target_doc.received_stock_qty = -1 * flt(
                    source_doc.received_stock_qty - (returned_qty_map.get("received_stock_qty") or 0)
                )

            if doctype == "Subcontracting Receipt":
                target_doc.subcontracting_order = source_doc.subcontracting_order
                target_doc.subcontracting_order_item = source_doc.subcontracting_order_item
                target_doc.rejected_warehouse = source_doc.rejected_warehouse
                target_doc.subcontracting_receipt_item = source_doc.name
            else:
                target_doc.purchase_order = source_doc.purchase_order
                target_doc.purchase_order_item = source_doc.purchase_order_item
                target_doc.rejected_warehouse = source_doc.rejected_warehouse
                target_doc.purchase_receipt_item = source_doc.name

        elif doctype == "Purchase Invoice":
            returned_qty_map = get_returned_qty_map_for_row(
                source_parent.name, source_parent.supplier, source_doc.name, doctype
            )
            target_doc.received_qty = -1 * flt(
                source_doc.received_qty - (returned_qty_map.get("received_qty") or 0)
            )
            target_doc.rejected_qty = -1 * flt(
                source_doc.rejected_qty - (returned_qty_map.get("rejected_qty") or 0)
            )
            target_doc.qty = -1 * flt(source_doc.qty - (returned_qty_map.get("qty") or 0))

            target_doc.stock_qty = -1 * flt(source_doc.stock_qty - (returned_qty_map.get("stock_qty") or 0))
            target_doc.purchase_order = source_doc.purchase_order
            target_doc.purchase_receipt = source_doc.purchase_receipt
            target_doc.rejected_warehouse = source_doc.rejected_warehouse
            target_doc.po_detail = source_doc.po_detail
            target_doc.pr_detail = source_doc.pr_detail
            target_doc.purchase_invoice_item = source_doc.name

        elif doctype == "Delivery Note":
            returned_qty_map = get_returned_qty_map_for_row(
                source_parent.name, source_parent.customer, source_doc.name, doctype
            )
            target_doc.qty = -1 * flt(source_doc.qty - (returned_qty_map.get("qty") or 0))
            target_doc.stock_qty = -1 * flt(source_doc.stock_qty - (returned_qty_map.get("stock_qty") or 0))

            target_doc.against_sales_order = source_doc.against_sales_order
            target_doc.against_sales_invoice = source_doc.against_sales_invoice
            target_doc.so_detail = source_doc.so_detail
            target_doc.si_detail = source_doc.si_detail
            target_doc.expense_account = source_doc.expense_account
            target_doc.dn_detail = source_doc.name
            if default_warehouse_for_sales_return:
                target_doc.warehouse = default_warehouse_for_sales_return
        elif doctype == "Sales Invoice" or doctype == "POS Invoice":
            returned_qty_map = get_returned_qty_map_for_row(
                source_parent.name, source_parent.customer, source_doc.name, doctype
            )
            target_doc.qty = -1 * flt(source_doc.qty - (returned_qty_map.get("qty") or 0))
            target_doc.stock_qty = -1 * flt(source_doc.stock_qty - (returned_qty_map.get("stock_qty") or 0))

            target_doc.sales_order = source_doc.sales_order
            target_doc.delivery_note = source_doc.delivery_note
            target_doc.so_detail = source_doc.so_detail
            target_doc.dn_detail = source_doc.dn_detail
            target_doc.expense_account = source_doc.expense_account

            if doctype == "Sales Invoice":
                target_doc.sales_invoice_item = source_doc.name
            else:
                target_doc.pos_invoice_item = source_doc.name

            if default_warehouse_for_sales_return:
                target_doc.warehouse = default_warehouse_for_sales_return

    def update_terms(source_doc, target_doc, source_parent):
        target_doc.payment_amount = -source_doc.payment_amount

    doclist = get_mapped_doc(
        doctype,
        source_name,
        {
            doctype: {
                "doctype": doctype,
                "validation": {
                    "docstatus": ["=", 1],
                },
            },
            doctype + " Item": {
                "doctype": doctype + " Item",
                "field_map": {"serial_no": "serial_no", "batch_no": "batch_no", "bom": "bom"},
                "postprocess": update_item,
                "condition": lambda doc: not doc.is_served
            },
            "Payment Schedule": {"doctype": "Payment Schedule", "postprocess": update_terms},
        },
        target_doc,
        set_missing_values,
    )

    doclist.set_onload("ignore_price_list", True)

    return doclist

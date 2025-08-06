// // Copyright (c) 2023, Rasiin Tech and contributors
// // For license information, please see license.txt

frappe.ui.form.on('Inpatient Order', {
    refresh(frm){
 
        frm.set_query('drug_code', 'drug_prescription', function() {
            return {
                // query: "his.api.dp_drug_pr_link_query.my_custom_query",
                filters: {
                    is_stock_item: 1
                }
                
            };
        })
    }
    
    })

// frappe.ui.form.on('Inpatient Order', {
//     refresh(frm){
 
//         // frm.set_query('drug_code', 'drug_prescription', function() {
//         //     return {
//         //         // query: "his.api.dp_drug_pr_link_query.my_custom_query",
//         //         filters: {
//         //             parent: "DP-000016"
//         //         }
                
//         //     };
//         // }),
//     },
// 	// bed: function(frm) {
//     //     setTimeout(() => {
//     //         var filed = frappe.meta.get_docfield("Nurse Drug Prescription", "drug_code", frm.docname);
    
       
//     //         filed.options = "Item";
//     //         console.log(filed)
//     //         // frm.refresh_field("drug_prescription")
//     //         frm.get_field("drug_prescription").grid.refresh();
//     //         frm.refresh_field("drug_prescription")
            
//     //     }, 1000);
   
//     //     var field = frappe.meta.get_docfield('Inpatient Order', 'bed', cur_frm.docname);
        
//     //     // Change the datatype to 'Select'
//     //     field.options = 'Item';
        
//     //     // Update the field in the form
//     //     cur_frm.fields_dict['bed'].refresh();
// 	// 	frm.refresh_field('drug_prescription');
        
       
     
// 	// }


// });
// frappe.ui.form.on('Nurse Drug Prescription', {
// 	refresh(frm) {
// 		// your code here
// 	},
//     from:function(frm ,cdt ,cdn){
//         var row= locals[cdt][cdn]
//         // alert(row.from)
//         if(row.from == "Extra")
//         {
//             row.doc = 'Item'

//         }
//         else{
//             row.doc = "Nurse Drug Prescription"
//             frm.set_query('drug_code', 'drug_prescription', function() {
//                 return {
//                     // query: "his.api.dp_drug_pr_link_query.my_custom_query",
//                     filters: {
//                         parent: "DP-000021"
//                     }
                    
//                 };
//             })
//         }
      
//         frm.refresh_field("drug_prescription")

//     },
// 	drug_code: function(frm, cdt, cdn){
//         var row= locals[cdt][cdn]
//         // alert(row.from)
	
//      if(row.from !== "Extra"){
//         // row.doc = 'Item'

//     // var childtable = frm.fields_dict['drug_prescription'];

//     // childtable.grid.grid_rows[row.idx-1].docfields[1].options = 'Item'
//     // frm.get_field("drug_prescription").grid.refresh();

  
//     frm.refresh_field("drug_prescription")
// 	 var drug_code= row.drug_code
	 
// 	 frappe.call({
//     method: 'his.api.inpatient_order.drug_code',
//     args: {
//         'drug_code': drug_code,
//         // doctor_plan: frm.doc.doctor_plan,

//     },
//     callback: function(r) {
//         // console.log(r.message[0].drug_code)
//      row.drug_name=r.message[0].drug_code
//     //  frm.set_value("qty",2)
//     // frm.set_value("item_name", r.message[0].drug_code)
//      frm.refresh_field("drug_prescription")
//     }
// });
// }else{
    
//     row.drug_name = row.drug_code
//     frm.refresh_field("drug_prescription")
// }
// 	}
    
// })

// // frappe.ui.form.on('Nurse Drug Prescription', {
    
// //     from(frm, cdt, cdn) { 
// //         // change_op(frm)
// //         var row = locals[cdt][cdn];
 
// //         if(row.from == "Extra"){
// //             row.doc = 'Item'

// //         // var childtable = frm.fields_dict['drug_prescription'];
   
// //         // childtable.grid.grid_rows[row.idx-1].docfields[1].options = 'Item'
// //         // frm.get_field("drug_prescription").grid.refresh();
   
// //         }else{
// //             row.doc = "IPD Drug Prescription"
// //         }
// //         frm.refresh_field("drug_prescription")
// //     },

// //     // drug_code(frm, cdt, cdn){
// //     //     var row = locals[cdt][cdn];
// //     //     frappe.db.get_value("IPD Drug Prescription" , row.name , "drug_name").then( r => {
// //     //         console.log(r.message)
// //     //     })

// //     // }
// //    })
   

// function change_op(frm){
//    setTimeout(() => {
//     var filed = frappe.meta.get_docfield("Nurse Drug Prescription", "drug_code", frm.docname);


//     filed.options = "eerrr";
//     console.log(filed)
//     // frm.refresh_field("drug_prescription")
//     frm.get_field("drug_prescription").grid.refresh();
//     frm.refresh_field("drug_prescription")
    
// }, 1000);
// }
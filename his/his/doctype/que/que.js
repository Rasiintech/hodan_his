// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt
frappe.provide('erpnext.queries');
frappe.ui.form.on('Que', {
    // after_save: function(frm) {
    //     alert()
	//      let url= `${frappe.urllib.get_base_url()}/printview?doctype=Que&name=${frm.doc.name}&trigger_print=1&settings=%7B%7D&_lang=en`;
    //      window.open(url, '_blank');
	// },
    is_free:function(frm){

        frm.set_value("paid_amount" , 0)
    },
    discount: function(frm){

        frm.set_value("paid_amount" , (frm.doc.doctor_amount-frm.doc.discount))
    
},
// bill_to: function(frm){

//     frm.set_value("customer" , frm.doc.bill_to)

// },


	refresh: function(frm) {

                frm.set_query('practitioner',  function() {
            return {
                query: "his.api.dp_drug_pr_link_query.my_custom_query_que",
               
                
            };
        })
        if(frm.is_new()){
            frm.set_value("status","Open")
            frm.set_value("sales_invoice","")
            frm.set_value("sales_order","")
        }
        if (frappe.user_roles.includes('Doctor') && !frappe.user_roles.includes('Doctor') ) {
            frm.set_df_property('paid_amount',  'hidden',  1);
             frm.set_df_property('doctor_amount',  'hidden',  1);
              frm.set_df_property('mode_of_payment',  'hidden',  1);
              frm.set_df_property('reference',  'hidden',  1);
              frm.set_df_property('debtor',  'hidden',  1);
              frm.set_df_property('bill_to',  'hidden',  1);
              if (frm.doc.status=="Open" || frm.doc.status=="Closed"){
                frm.add_custom_button(__("Open Encounter"), function(){
                    frappe.new_doc("Patient Encounter",{"que": frm.doc.name, "patient": frm.doc.patient,"practitioner" : frm.doc.practitioner,}) 

                    //perform desired action such as routing to new form or fetching etc.
                  })

              }
    }
    
        // if (!frappe.user_roles.includes('Main Cashier') || !frappe.user_roles.includes('Cashier')) {
        //     frm.set_df_property("is_free" , "hidden" , 1)
            
        // }
        // frm.set_value("company",frappe.defaults.get_default('Company'))
		if(!frm.is_new()){
		    // frm.set_value("company",frappe.defaults.get_default('Company'))

        
            
    	
       
            //   frm.set_value("messege","?");
            if (frm.doc.status=="Open") {
               
                if (frappe.user_roles.includes('Main Cashier') || frappe.user_roles.includes('Cashier')) {
                // -------------------------------------------------------------------------------
                var cancel_btn=  frm.add_custom_button(__("Cancel"), function(){

                    frappe.prompt({
                        label: 'Remark',
                        fieldname: 'remark',
                        fieldtype: 'Data',
                        reqd: 1
                    }, (values) => {
                        frappe.db.set_value('Que', frm.doc.name, 'remarks', values.remark)
                        frappe.db.set_value('Que', frm.doc.name, 'status', "Canceled")
                        // frm.db.set_value("remarks", values.remark)
                        frappe.call({
                            method: "his.api.make_cancel_ques.make_cancel", //dotted path to server method
                            args: {
                                "que" : frm.doc.name,
                                "sales_invoice" : frm.doc.sales_invoice,
                                "sakes_order" : frm.doc.sales_order,
                                "fee" : frm.doc.fee_validity,
                                
                                
                                
                             
                            },
                            callback: function(r) {
                                
                        //frappe.msgprint(r)
                        console.log(r)
                        frappe.utils.play_sound("submit")
        
                        frappe.show_alert({
                            message:__('Patient Que Canceled Succesfully'),
                            indicator:'red',
                            
                        }, 5);
                              
                        frm.reload_doc()
                            }
                            
        });
                    })


                      
            //            frappe.confirm('Are you sure you want to Cancel?',
            //     () => {
            //         // action to perform if Yes is selected
            //                     frappe.call({
            //                     method: "his.api.make_cancel_ques.make_cancel", //dotted path to server method
            //                     args: {
            //                         "que" : frm.doc.name,
            //                         "sales_invoice" : frm.doc.sales_invoice,
            //                         "sakes_order" : frm.doc.sales_order,
            //                         "fee" : frm.doc.fee_validity,
                                    
                                    
                                    
                                 
            //                     },
            //                     callback: function(r) {
                                    
            //                 //frappe.msgprint(r)
            //                 console.log(r)
            //                 frappe.utils.play_sound("submit")
            
            //                 frappe.show_alert({
            //                     message:__('Patient Que Canceled Succesfully'),
            //                     indicator:'red',
                                
            //                 }, 5);
                                  
            //                 frm.reload_doc()
            //                     }
                                
            // });
            //     }, () => {
            //         // action to perform if No is selected
            //     })
                        
            
                  
                    
                    
                });
                if(!frm.doc.is_free && !frm.doc.is_insurance && frm.doc.paid_amount ){
                var refurn_btn=  frm.add_custom_button(__("Refund"), function(){
                      
                    frappe.confirm('Are you sure you want to Refund?',
             () => {
                 // action to perform if Yes is selected
                             frappe.call({
                                method: "his.api.create_inv.create_inv_refund",
                                args: {
                                    doc_name: frm.doc.sales_invoice,
                                    dt:"Sales Invoice",
                                    is_sales_return: true,
                                    que : frm.doc.name,
                                },
                             callback: function(r) {
                                 
                         //frappe.msgprint(r)
                        //  console.log(r)
                         frappe.utils.play_sound("submit")
            
                         frappe.show_alert({
                             message:__('Patient Que Refund Succesfully'),
                             indicator:'green',
                             
                         }, 5);
                               
                         frm.reload_doc()
                             }
                             
            });
             }, () => {
                 // action to perform if No is selected
             })
                     
            
               
                 
                 
             });
            }
                // ---------------------------------------------------------------------------------
            
                // cancel_btn.addClass('btn-danger');
                // refurn_btn.addClass('btn-danger');
                // reviset_btn.addClass('btn-primary');
                }

            }
//             if (frm.doc.status !=="Closed"){
//                 var reviset_btn=  frm.add_custom_button(__("Revisit"), function(){

//                     // action to perform if Yes is selected
//                                 frappe.call({
//                                    method: "his.api.revisit.Check_revisit",
//                                    args: {
//                                        //is_free: true,
//                                        "que" : frm.doc.name,
//                                        "date" : frm.doc.date,
//                                        "doctor" : frm.doc.practitioner
//                                    },
//                                 callback: function(r) {
//                                    // alert(r)
                                     
                                    
//                            console.log(r)
                           
//                             // frappe.utils.play_sound("submit")
               
//                             // frappe.show_alert({
//                             //     message:__('Patient Que Revesit Succesfully'),
//                             //     indicator:'blue',
                                
//                             // }, 5);
//                        let htmldata = ''
//                        let d;
//            r.message.forEach(row => {
//                htmldata += ` <tr>
//            <td>${row.patient_name}</td>
//            <td>${row.practitioner}</td>
//            <td>${row.date}</td>
//            <td><button class= 'btn btn-success' onclick='
//            frappe.call({
//                        method: "his.api.revisit.que_revisit", //dotted path to server method
//                        args: {
                           
                           
//                            "que" : "${row.name}",
                           
//                        },
//                        callback: function(r) {
//                            // code snippet
//                            // frappe.msgprint(r)
//                        // frm.set_value("status" , "Refered")
//                         frappe.utils.play_sound("submit")
//                    frappe.show_alert({
//                     //    $(".modal-dialog").hide()
//                        message:__("Que Created Successfully!!"),
//                        indicator:"green",
                       
//                    }, 5);
                   
//                        }
//    });
//            ' width='40px'>Que</button></td>
//          </tr>`
         
//            })
   
//                var template=`<table class="table table-hover">
     
//        <tr>
//          <th scope="col">Patient</th>
//          <th scope="col">Doctor</th>
//          <th scope="col">Date</th>
//          <th scope="col">Action</th>
//        </tr>
//        <tbody>
//        ${htmldata}
//        </tbody>
    
//    </table>
//    `;
//                 d = new frappe.ui.Dialog({
//                title: 'Revist Lists',
//                fields: [
//                    {
//                        label: 'Revist List',
//                        fieldname: 'practitioner',
//                        fieldtype: 'HTML',
//                        options: template,
                       
//                    }
                  
                  
                
//                ]
   
               
//            });
   
//            d.show();
                                  
                                    
//                                 }
                                
   
//                 })
   
    
                    
//                 });
//             }

}
  },


 	
    practitioner: function(frm){
        setTimeout(() => {
            // alert()
            if(!frm.doc.is_insurance && !frm.doc.is_free){
            frm.set_value("paid_amount" , frm.doc.doctor_amount)
            }
            
        }, 100);
       
    },
    patient: function(frm) {
        
        let me = this
		if (frm.doc.patient) {
			frm.trigger('toggle_payment_fields');
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Patient',
					name: frm.doc.patient
				},
				callback: function(data) {
                    // alert(data.message.dob)
                    // console.log(data)
					let age = null;
					if (data.message.dob) {
						age = calculate_age(data.message.dob);
                       
					}
					frappe.model.set_value(frm.doctype, frm.docname, 'age', age);
                    // alert(data.message.is_insurance)
                    if (data.message.is_insurance){
                     
                      let d = new frappe.ui.Dialog({

                              title: `This patient in insurance <strong>${frm.doc.patient}</strong> is in insurance <strong>${data.message.ref_insturance} </strong> do you want to Charge Patient or insurance

                                <br>

                              `,
                              fields: [
                              {
                               label: 'Insurance',
                               fieldname: 'btn',
                               fieldtype: 'HTML',
                               options: `<button type="button" class="btn btn-success" style="background-color: green" onclick='$(".modal-dialog").hide()'>Patient</button>
                                        <button type="button" id = "insu" class="btn btn-danger" onclick='frappe.model.set_value("${frm.doctype}", "${frm.docname}", "is_insurance", 1 ); $(".modal-dialog").hide()' >insurance</button>`,
                               
                               }]

                                
                                
                          });

                          d.show();
                      
                        //   const button = document.getElementById('insu');
                        //   button.addEventListener('click', function);
                        
                        // frappe.warn('This patient in insurance ',
                        //         frm.doc.patient+ ', is in insurance '+ data.message.ref_insturance+' do you want to Charge Patient or insurance',
                        //         () => {
                        //             frappe.model.set_value(frm.doctype, frm.docname, 'is_insurance', 1);
                        //             // action to perform if Continue is selected
                        //         },
                        //         'insurance',
                        //         true // Sets dialog as minimizable
                        //     )
                        
                    }
                    if(data.message.is_employee){
                       frm.set_value("is_employee" , 1)
                       frm.set_value("employee" , data.message.linked_employee)
                    }
				}
			});
		}

	}
	
});
let hide_dialog = function(){
    alert()
    $(".modal-dialog").hide()
  }
let calculate_age = function(birth) {
	let ageMS = Date.parse(Date()) - Date.parse(birth);
	let age = new Date();
	age.setTime(ageMS);
	let years =  age.getFullYear() - 1970;
	return `${years} ${__('Years(s)')} ${age.getMonth()} ${__('Month(s)')} ${age.getDate()} ${__('Day(s)')}`;
};



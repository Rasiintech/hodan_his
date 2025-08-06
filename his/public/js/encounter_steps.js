frappe.ui.form.on('Patient Encounter', {
    after_save: function (frm) {
        // alert()
        window.location.reload();
    },
    select_lab_tests: function (frm) {
        select_lab_tests(frm)
    },

    select_imaging: function (frm) {
        // alert("ok")
        select_imaging(frm)
    },

    check_up: function (frm) {
        var d = new frappe.ui.Dialog({
            'fields': [

                { 'fieldname': 'ht', 'fieldtype': 'HTML' },

            ],

            primary_action: function () {

                var test = []
                var labs = []
                $("input[name='lab']:checked").each(function () {
                    if (!$(this).is(':checked')) {
                        console.log($(this))
                    }

                    var selectedlabs = []
                    cur_frm.get_field("lab_test_prescription").grid.grid_rows.forEach(r => selectedlabs.push(r.doc.lab_test_code))
                    if (selectedlabs) {
                        if (!selectedlabs.includes($(this).val())) {
                            labs.push($(this).val())
                            //   var row = frappe.model.add_child(cur_frm.doc, "Lab Prescription", "lab_test_prescription");
                            //     row.lab_test_code = $(this).val()

                            //     refresh_field("lab_test_prescription");

                            // test.push($(this).val());
                        }
                    }
                    else {
                        labs.push($(this).val())

                    }

                });
                labs.forEach(lab => {
                    var row = frappe.model.add_child(cur_frm.doc, "Lab Prescription", "lab_test_prescription");
                    row.lab_test_code = lab

                    refresh_field("lab_test_prescription");
                })
                //   console.log(test)
                //   test = []

                //   var va = $('input:checked').map(function(i, e) {return e.value}).toArray();
                //   console.log(va)
                // //  var va = [];
                //     $(':checkbox:checked').each(function(i){
                //         va = []
                //       va.push($(this).val());
                //       console.log(va)
                //     });

                d.hide();


            }
        });

        var td = ''

        // frappe.client.get_list('Lab Test Template', {
        //      page_length:2,
        //     fields: ['lab_test_name' , 'department'],
        //     filters: {
        //         is_billable: 1,

        //     },
        // frappe.db.get_list('Lab Test Template', {
        //     fields: ['lab_test_name' , 'department'],
        //     filters: {
        //         is_billable: 1
        //     },
        //     limit : 1000
        // }).then(records => {
        //      var pr_selectedlabs= []
        //      cur_frm.get_field("lab_test_prescription").grid.grid_rows.forEach(r => pr_selectedlabs.push(r.doc.lab_test_code))

        //     records.forEach(r =>  { 
        //          if (pr_selectedlabs.includes(r.lab_test_name)){
        //               td += `${r.lab_test_name}  <input type="checkbox" class="lab" name="lab" value="${r.lab_test_name}" checked>`
        //          }
        //          else{
        //                td += `${r.lab_test_name}  <input type="checkbox" class="lab" name="lab" value="${r.lab_test_name}">`
        //          }

        //         var htm = td
        //         d.fields_dict.ht.$wrapper.html(htm);
        //     })
        // })

        var td = "";
        frappe.db
            .get_list("Lab Test Template", {
                fields: ["lab_test_name", "department", "profile"],
                filters: {
                    is_billable: 1,
                    disabled: 0,
                    check_up: 1
                },
                limit: 500,
                order_by: "department"
            })
            .then((records) => {
                records.forEach((r) => {
                    // 	td += ` <span class ="text-primary h4" >${r.lab_test_name}  <input type="checkbox" class="lab" name="lab" value="${r.lab_test_name}"></span>`

                    // 		   var htm = td
                    // 		   var row= `<div class="container">
                    // 	 <div class="row">
                    // 	   <div class="col-sm-6">
                    // 		${td}
                    // 	   </div>

                    // 	 </div>
                    //    </div>`

                    const re_arr = [records];
                    let row = ``;
                    const groupByDept = records.reduce((group, dep) => {
                        // console.log(group)
                        const { profile } = dep;
                        if (profile) {
                            group[profile.toUpperCase().trim()] = group[profile.toUpperCase().trim()] || [];
                            group[profile.toUpperCase().trim()].push(dep);
                        }
                        else {
                            group[profile] = group[profile] || [];
                            group[profile].push(dep);

                        }

                        return group;
                    }, {});
                    //   console.log(groupByDept);
                    var pr_selectedlabs = []
                    frm.get_field("lab_test_prescription").grid.grid_rows.forEach(r => pr_selectedlabs.push(r.doc.lab_test_code))

                    Object.keys(groupByDept).forEach((key) => {
                        // console.log(key, groupByDept[key]);
                        let td = ``;
                        groupByDept[key].forEach((test) => {
                            if (pr_selectedlabs.includes(test.lab_test_name)) {
                                td += `
          
          <div class="form-group form-check">
          
              <input type="checkbox" checked="1"  class="form-check-input" name = "lab" id="${test.lab_test_name}"  value="${test.lab_test_name}" checked>
              <label class="form-check-label" >${test.lab_test_name}</label>
              
          </div>
          `;
                            }
                            else {
                                td += `
          
                <div class="form-group form-check">
                
                    <input type="checkbox" checked="1"  class="form-check-input" name = "lab" id="${test.lab_test_name}"  value="${test.lab_test_name}">
                    <label class="form-check-label" >${test.lab_test_name}</label>
                    
                </div>
                `;

                            }
                        });
                        row += `
          
          <div class = "col-md-3" id = "${key}">
              <h4>${key}</h4>
              ${td}
              
          </div>
          `;
                    });
                    var continaer = `<div class="container">
  <div class="row">
  
     ${row}
  
  

  </div>
</div>`;
                    d.fields_dict.ht.$wrapper.html(continaer);
                    d.$wrapper.find(".modal-dialog").css("max-width", "100%", "width", "100%");

                    d.show();
                    // d.$wrapper.find('.modal-content').css("width", "800px");
                })
            })
    },
    // patient: function(frm){
    //     frappe.call({
    //         method: "rasiin_design.api.p_history.get_history", //dotted path to server method
    //         args : {"patient" : frm.doc.patient , heading : 0},
    //         //  args : {"load_a" : currdate , to_date : to_date},
    //         callback: function(r) {
    //             $('#history').html(r.message)

    //             // console.log(window.open.document)
    //         // 	var x = window;
    //         // 	x.document.open().write(r.message);



    //         }})
    // },
    onload_post_render(frm) {
        setTimeout(() => {
            get_history(frm.doc.patient , "dental_plan")
            get_history(frm.doc.patient , "vitals")
            get_history(frm.doc.patient , "labs")
            if (frm.doc.patient) {
                get_history(frm.doc.patient , "dental_plan")
                frappe.call({
                    method: "rasiin_design.api.p_history.get_history", //dotted path to server method
                    args: { "patient": frm.doc.patient },
                    //  args : {"load_a" : currdate , to_date : to_date},
                    callback: function (r) {
                        $('#history').html(r.message)

                        // console.log(window.open.document)
                        // 	var x = window;
                        // 	x.document.open().write(r.message);



                    }
                })
            }

        }, 1000);


    },
    refresh(frm) {
        if (!frm.is_new()){
            get_history(frm.doc.patient , "dental_plan")
            get_history(frm.doc.patient , "vitals")
            get_history(frm.doc.patient , "labs")
        }

        // if (frm.fields_dict["services_prescription"]) {
        //     let hide_field = !frappe.user_roles.includes("HR XX");
            
        //     // Hide the "rate" column completely from the grid
        //     frm.fields_dict["services_prescription"].grid.update_docfield_property("rate", "hidden", hide_field);

        //     // Refresh the grid to apply the change
        //     frm.fields_dict["services_prescription"].grid.refresh();
        // }

        // frm.set_query('service', 'services_prescription', function() {
        //     return {
        //         filters: frm.doc.item_group ? { 'item_group': frm.doc.item_group } : {}
        //     };
        // });

        
        

        frm.set_query('service', 'services_prescription', function() {
            return {
                filters: frm.doc.medical_departments ? { 'department': frm.doc.medical_departments } : {}
            };
        });
        var Admission_request = frm.add_custom_button('Admission Request', () => {


            frappe.new_doc("Admission Ordering Request", {
                "patient": frm.doc.patient,
                "practitioner": frm.doc.practitioner,

            })

        })
        if (!frm.doc.__islocal) {

            var Admission_request = frm.add_custom_button('OR Booking', () => {


                frappe.new_doc("OR BOOKING FORM", {
                    "patient": frm.doc.patient,
                    "practitioner": frm.doc.practitioner,
                    "sex": frm.doc.patient_sex,

                })

            })

        }

        var dental_plan = frm.add_custom_button('Dental Plan', () => {


            frappe.new_doc("Dental Plan", {
                "patient": frm.doc.patient,
                "practitioner": frm.doc.practitioner,

            })

        })

        dental_plan.addClass('btn-primary');
        frm.remove_custom_button('Patient History')
        frm.remove_custom_button('Vital Signs')


        if (frm.doc.patient) {
            frappe.call({
                method: "rasiin_design.api.p_history.get_history", //dotted path to server method
                args: { "patient": frm.doc.patient },
                //  args : {"load_a" : currdate , to_date : to_date},
                callback: function (r) {
                    $('#history').html(r.message)

                    // console.log(window.open.document)
                    // 	var x = window;
                    // 	x.document.open().write(r.message);



                }
            })
        }

        // frm.clear_custom_buttons();
        frm.remove_custom_button('Patient History', 'View');
        frm.remove_custom_button('Vital Signs', 'Create');
        frm.remove_custom_button('Medical Record', 'Create');
        frm.remove_custom_button('Inpatient Medication Order', 'Create');
        frm.remove_custom_button('Clinical Procedure', 'Create');
        frm.remove_custom_button('Nursing Tasks', 'Create');


        if (!frm.doc.__islocal) {
            if (frm.doc.docstatus === 1) {
                if (!['Discharge Scheduled', 'Admission Scheduled', 'Admitted'].includes(frm.doc.inpatient_status)) {
                    frm.add_custom_button(__('Schedule Admission'), function () {
                        schedule_inpatient(frm);
                    });
                }
            }
        }



        // frm.add_custom_button('Today ', () => {
        //     consoleerp_hi(frm.doc.patient , frm.doc.patient_name , true)
        //   }, 'History');
        //   frm.add_custom_button('Open History', () => {
        //     if(frm.doc.patient){
        //     frappe.call({
        // 		method: "rasiin_design.api.p_history.get_history", //dotted path to server method
        // 		args : {"patient" : frm.doc.patient},
        // 		//  args : {"load_a" : currdate , to_date : to_date},
        // 		callback: function(r) {

        // 			var x = window.open();
        // 			x.document.open().write(r.message);



        // 		}})
        //     }
        //   });
        //   frm.add_custom_button('Open Vital Sign', () => {
        //     if(frm.doc.patient){

        //     frappe.new_doc("Vital Signs", { "patient": frm.doc.patient, "practitioner": frm.doc.ref_practitioner, })
        //     }
        //   });



        if (!frm.is_new()) {

            frm.add_custom_button(__('Print Medication'), function () {
                var url = `${frappe.urllib.get_base_url()}/printview?doctype=Patient%20Encounter&name=${frm.doc.name}&trigger_print=1&format=Medication%20Prescription&no_letterhead=0&letterhead=Logo&settings=%7B%7D&_lang=en-US`
                window.open(url, '_blank');
            }, __("Print"));
            frm.add_custom_button(__('Print Lab'), function () {
                var url = `${frappe.urllib.get_base_url()}/printview?doctype=Patient%20Encounter&name=${frm.doc.name}&trigger_print=1&format=Lab%20Prescription&no_letterhead=0&letterhead=Logo&settings=%7B%7D&_lang=en-US`
                window.open(url, '_blank');
            }, __("Print"));
            frm.add_custom_button(__('Print Procedure'), function () {
                var url = `${frappe.urllib.get_base_url()}/printview?doctype=Patient%20Encounter&name=${frm.doc.name}&trigger_print=1&format=Procedure%20Prescription&no_letterhead=0&letterhead=Logo&settings=%7B%7D&_lang=en-US`
                window.open(url, '_blank');
            }, __("Print"));

            frm.add_custom_button(__('Print Radiology'), function () {
                var url = `${frappe.urllib.get_base_url()}/printview?doctype=Patient%20Encounter&name=${frm.doc.name}&trigger_print=1&format=Radiology%20Prescription&no_letterhead=0&letterhead=Logo&settings=%7B%7D&_lang=en-US`
                window.open(url, '_blank');
            }, __("Print"));
            frm.add_custom_button(__('Print Services'), function(){
                var url=`${frappe.urllib.get_base_url()}/printview?doctype=Patient%20Encounter&name=${frm.doc.name}&trigger_print=1&format=Services%20Prescription&no_letterhead=0&letterhead=Logo&settings=%7B%7D&_lang=en-US`
                window.open(url, '_blank');
            }, __("Print"));
            frm.add_custom_button(__('Print Package'), function(){
                var url=`${frappe.urllib.get_base_url()}/printview?doctype=Patient%20Encounter&name=${frm.doc.name}&trigger_print=1&format=Package&no_letterhead=0&letterhead=Logo&settings=%7B%7D&_lang=en-US`
                window.open(url, '_blank');
            }, __("Print"));
            frm.add_custom_button('Refer', () => {
                let d = new frappe.ui.Dialog({
                    title: 'Enter details',
                    fields: [
                        {
                            label: 'Type',
                            fieldname: 'type',
                            fieldtype: 'Select',
                            options: "Internal\nExternal"
                        },
                        {
                            label: 'Practitioner',
                            fieldname: 'practitioner',
                            fieldtype: 'Link',
                            options: 'Healthcare Practitioner',
                            // reqd : 1,
                            depends_on: "eval:(doc.type != 'External' && doc.type == 'Internal')",
                            get_query: function() {
                                return {
                                    query: "his.api.dp_drug_pr_link_query.my_custom_query",  // Custom query method
                                };
                            },
                        },
                        {
                            fieldname: "to",
                            fieldtype: "Data",
                            label: "To",
                            depends_on: "eval: doc.type == 'External'",
                        },
                        {
                            fieldname: "rtype",
                            fieldtype: "Data",
                            label: "Type",
                            depends_on: "eval: doc.type == 'External'",
                        },
                        {
                            fieldname: "request",
                            fieldtype: "Small Text",
                            label: "Request",
                            depends_on: "eval:(doc.type == 'External' || doc.type == 'Internal' )",
                        },

                    ],
                    primary_action_label: 'Submit',
                    primary_action(values) {
                        let practitioner = d.get_value("practitioner")
                        let to = d.get_value("to")
                        let rtype = d.get_value("rtype")
                        let request = d.get_value("request")
                        let type = d.get_value("type")
                        
                        frappe.call({
                            method: "his.api.refer.refer_from_doctor", //dotted path to server method
                            args: {
                                "to": to,
                                "rtype": rtype,
                                "request": request,
                                "docname": frm.doc.name,
                                "practitioner": practitioner,
                                'patient': frm.doc.patient,
                                'type': type,
                                'ref_practitioner': frm.doc.practitioner
                            },
                            callback: function (r) {
                                // code snippet

                                // frm.set_value("status" , "Refered")
                                frappe.utils.play_sound("submit")

                                frappe.show_alert({
                                    message: __('You have Refered Patient Succesfully'),
                                    indicator: 'green',

                                }, 5);
                                let doc_ = r.message

                                frappe.utils.print(doc_.doctype, doc_.name, "referal form" ,"logo")
                            }
                        });
                        d.hide();


                    }
                });
                // Set the custom query for the 'practitioner' field
                frm.set_query('practitioner', function() {
                    return {
                        query: "his.api.dp_drug_pr_link_query.my_custom_query",  // Path to the custom query method
                    };
                });
                d.show();


            })
        }


        // frappe.call({
        // method: "his.api.steps.All_que_numbers", //dotted path to server method
        // callback: function(r) {
        //     console.log(r)
        // }
        // });

        //  let token_n=` <div class="header" style="margin:0 auto;
        //  padding: 5px 10px;
        //  width:10%;
        //  border:2px solid #333;">

        //   <h4 style="color:black;text-align:center;font-size: 20px;">${frm.doc.token_n}</h4>
        // </div>`


        //  frm.set_df_property("token","options",token_n);


        if (!frm.is_new()) {

            // 	   var pre=  frm.add_custom_button(__("Pre"), function(){
            //                    //frappe.msgprint(frm.doc.practitioner);
            //            frappe.call({
            //                     method: "his.api.steps.pre", //dotted path to server method
            //                     args: {
            //                         "doc":frm.doc.que,
            //                         "doctor":frm.doc.practitioner




            //                     },
            //                     callback: function(r) {
            //                         let count=r.message[0].min;

            //                         console.log(r)
            //                         if(count){       // frappe.msgprint(count);
            //                        if(r.message[0].patient_encounter){
            //                        frappe.set_route('Form', 'Patient Encounter', r.message[0].patient_encounter);
            //                    }else{
            //                        frappe.new_doc("Patient Encounter",{"que": r.message[0].name, "patient": r.message[0].patient_id,"practitioner" : r.message[0].doctor})
            //                        // count+1

            //                    }
            //                }
            //                else{
            //                    frappe.msgprint(__('There is no patient in your que '));
            //                }


            //                     }

            // });


            // 	   })
            // 	   var next=  frm.add_custom_button(__("Next"), function(){


            // 	       //frappe.msgprint(frm.doc.practitioner);
            // 	       frappe.call({
            //                     method: "his.api.steps.steps", //dotted path to server method
            //                     args: {
            //                         "doc":frm.doc.que,
            //                         "doctor":frm.doc.practitioner




            //                     },
            //                     callback: function(r) {
            //                         let count=r.message[0].min;
            //                         console.log(r)
            //                  if(count){  
            //                     frappe.db.set_value("Que" ,r.message[0].name , "que_steps" , "Called" )      // frappe.msgprint(count);
            //                 if(r.message[0].patient_encounter){
            //                 frappe.set_route('Form', 'Patient Encounter', r.message[0].patient_encounter);
            //             }else{
            //                 frappe.new_doc("Patient Encounter",{"que": r.message[0].name, "patient": r.message[0].patient,"practitioner" : r.message[0].practitioner})
            //                 // count+1

            //             }
            //         }
            //         else{
            //             frappe.msgprint(__('There is no patient in your que '));
            //         }


            //                     }

            // });

            // 	   })

            //    frappe.db.get_single_value('Patient Encounter', 'token')




            // console.log(records);


            // your code here
        }

        //         var missed=  frm.add_custom_button(__("Missed"), function(){


        //             //frappe.msgprint(frm.doc.practitioner);
        //             frappe.call({
        //                      method: "his.api.steps.missed", //dotted path to server method
        //                      args: {
        //                          "doc":frm.doc.que,
        //                          "doctor":frm.doc.practitioner





        //                      },
        //                      callback: function(r) {
        //                          let count=r.message[0].min;
        //                          console.log(r)
        //                   if(count){
        //                     frappe.db.set_value("Que" ,r.message[0].name , "que_steps" , "Called" )       // frappe.msgprint(count);
        //                  if(frm.doc.patient_encounter){
        //                  frappe.set_route('Form', 'Patient Encounter', frm.doc.patient_encounter);
        //              }else{
        //                  frappe.new_doc("Patient Encounter",{"que": r.message[0].name, "patient": r.message[0].patient,"practitioner" : r.message[0].practitioner})
        //                  // count+1


        //              }
        //          }
        //          else{
        //              frappe.msgprint(__('There is no patient in your que '));
        //          }


        //                      }

        //  });

        //         })

    },
    onload(frm) {

        // alert(doctor)
        frappe.call({
            method: "his.api.steps.All_que_numbers", //dotted path to server method
            args: {
                "doctor": frm.doc.practitioner




            },
            callback: function (r) {

                let token_n = ` <div  style="margin:0 auto;
        padding: 5px 10px;
        width:40%;
        border:2px solid #333; ">
        
         <h4 style="color:black;text-align:center;font-size: 20px;">${frm.doc.token_n || 0} Remain ${r.message[0].number}</h4>
       </div>`


                frm.set_df_property("token", "options", token_n);
            }
        });
    },
    practitioner: function(frm){
        if (frm.doc.practitioner) {
            frm.set_value("medical_departments" , frm.doc.medical_department)
        }
    },
    get_plan:function(frm){
        frappe.call({
            method: "his.api.get_dental_plan.get_plan",
            args: {
                patient: frm.doc.patient,
                practitioner: frm.doc.practitioner,
                medical_department: frm.doc.medical_department,
            },
            callback: function(r) {
            if (r.message) {
                console.log("Dental Plan Retrieved:", r.message);
                // Check if the child table exists
                if (!frm.doc.services_prescription) {
                    frm.doc.services_prescription = [];
                }

                // Add a new row to the child table
                let row = frm.add_child("services_prescription");
                console.log(r.message)
                
                // Set values in the new row
                row.service = "Dental Service";  // Change this to the actual field name
                row.rate = r.message.agreed_fee;  // Use correct object property
                row.agreed_amount = r.message.grand_total;

                // Refresh the field to show changes in UI
                frm.refresh_field("services_prescription");
            } else {
                frappe.msgprint("No Dental Plan found for this patient.");
            }
            }
        });
	},

})





frappe.ui.form.on('Drug Prescription', {

    drug_code(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        //   console.log(row)
        frappe.db.get_value('Item', row.drug_code, ['of_stripes_box', 'of_tabs__stripe', 'tab_ber_box'])
            .then(r => {

                if (r.message) {

                    let data = `1Box= ${r.message.of_stripes_box} S, 1Strip= ${r.message.of_tabs__stripe} P`;
                    // console.log(data)
                    row.info = data
                    frm.refresh_field("drug_prescription")
                }
            })
        // let row = frappe.get_doc(cdt, cdn);


    }
})



var schedule_inpatient = function (frm) {
    var dialog = new frappe.ui.Dialog({
        title: 'Patient Admission',
        fields: [
            { fieldtype: 'Data', label: 'Diagnosis', fieldname: 'diagnosis', reqd: 1 },
            { fieldtype: 'Link', label: 'Medical Department', hidden: 1, fieldname: 'medical_department', options: 'Medical Department', reqd: 1 },
            { fieldtype: 'Link', hidden: 1, label: 'Healthcare Practitioner (Primary)', fieldname: 'primary_practitioner', options: 'Healthcare Practitioner', reqd: 1 },
            { fieldtype: 'Link', hidden: 1, label: 'Healthcare Practitioner (Secondary)', fieldname: 'secondary_practitioner', options: 'Healthcare Practitioner' },
            { fieldtype: 'Link', hidden: 1, label: 'Nursing Checklist Template', fieldname: 'admission_nursing_checklist_template', options: 'Nursing Checklist Template' },
            { fieldtype: 'Column Break', hidden: 1, },
            { fieldtype: 'Date', hidden: 1, label: 'Admission Ordered For', fieldname: 'admission_ordered_for', default: 'Today' },
            { fieldtype: 'Link', hidden: 1, label: 'Service Unit Type', fieldname: 'service_unit_type', options: 'Healthcare Service Unit Type' },
            { fieldtype: 'Int', hidden: 1, label: 'Expected Length of Stay', fieldname: 'expected_length_of_stay' },
            { fieldtype: 'Section Break', hidden: 1, },
            { fieldtype: 'Long Text', hidden: 1, label: 'Admission Instructions', fieldname: 'admission_instruction' },
            // {fieldtype: 'Link',hidden:0, label: 'Consultant', fieldname: 'admission_practitioner', options: 'Healthcare Practitioner', reqd: 1},


        ],
        primary_action_label: __('Order Admission'),
        primary_action: function () {
            var args = {
                patient: frm.doc.patient,
                admission_encounter: frm.doc.name,
                referring_practitioner: frm.doc.practitioner,
                diagnosis: dialog.get_value('diagnosis'),
                company: frm.doc.company,
                medical_department: dialog.get_value('medical_department'),
                primary_practitioner: dialog.get_value('primary_practitioner'),
                secondary_practitioner: dialog.get_value('secondary_practitioner'),
                admission_ordered_for: dialog.get_value('admission_ordered_for'),
                admission_service_unit_type: dialog.get_value('service_unit_type'),
                expected_length_of_stay: dialog.get_value('expected_length_of_stay'),
                admission_instruction: dialog.get_value('admission_instruction'),

                admission_nursing_checklist_template: dialog.get_value('admission_nursing_checklist_template')
            }
            frappe.call({
                method: 'his.api.admission_schd.schedule_inpatient',
                args: {
                    args: args
                },
                callback: function (data) {
                    if (!data.exc) {
                        frm.reload_doc();
                    }
                },
                freeze: true,
                freeze_message: __('Scheduling Patient Admission')
            });
            frm.refresh_fields();
            dialog.hide();
        }
    });

    dialog.set_values({
        'medical_department': frm.doc.medical_department,
        'primary_practitioner': frm.doc.practitioner,
    });

    // dialog.fields_dict['service_unit_type'].get_query = function() {
    // 	return {
    // 		filters: {
    // 			'inpatient_occupancy': 1,
    // 			'allow_appointments': 0
    // 		}
    // 	};
    // };

    dialog.show();
    dialog.$wrapper.find('.modal-dialog').css('width', '800px');
};



function setup_datatable(columns, data, group, tabid) {
    // console.log(data)

    // alert(tabid)
    let groupBy = []
    if (group) {
        groupBy.push(group)
    }

    this.table = new Tabulator(`#${tabid}`, {
        // layout:"fitDataFill",
        layout: "fitDataFill",
        //  layout:"fitColumns",
        // responsiveLayout:"collapse",
        rowHeight: 30,
        placeholder: "No Data Available",
        //  selectable:true,
        //  dataTree:true,
        //  dataTreeStartExpanded:true,
        groupStartOpen: false,
        printAsHtml: true,
        //  printHeader:`<img src = '/private/files/WhatsApp Image 2022-10-20 at 6.19.02 PM.jpeg'>`,
        printFooter: "<h2>Example Table Footer<h2>",
        groupBy: groupBy,
        groupHeader: function (value, count, data, group) {
            //value - the value all members of this group share
            //count - the number of rows in this group
            //data - an array of all the row data objects in this group
            //group - the group component for the group

            return value + "<span style=' margin-left:0px;'>(" + count + "   )</span>";
        },
        groupToggleElement: "header",
        //  groupBy:groupbyD.length >0 ? groupbyD : "",
        //  textDirection: frappe.utils.is_rtl() ? "rtl" : "ltr",

        columns: columns,

        // [
        // 	{formatter:"rowSelection", titleFormatter:"rowSelection", hozAlign:"center", headerSort:false, cellClick:function(e, cell){
        // 		cell.getRow().toggleSelect();
        // 	  }},
        // 	{
        // 		title:"Name", field:"name", width:200,
        // 	},
        // 	{title:"Group", field:"item_group", width:200},
        // ],
        // [
        // {title:"Name", field:"name" , formatter:"link" , formatterParams:{
        // 	labelField:"name",
        // 	urlPrefix:`/app/${doct}/`,

        // }},
        // {title:"Customer", field:"customer" },
        // {title:"Total", field:"net_total" , bottomCalc:"sum",},

        // ],

        data: data
    });
}

frappe.ui.form.on('Services Prescription', { 
    service: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.service) {
            frappe.db.get_value('Other Service', {'template': row.service}, 'rate')
                .then(r => {
                    if (r.message.rate) {
                        frappe.model.set_value(cdt, cdn, 'rate', r.message.rate);
                    }
                });
        }
    }
});
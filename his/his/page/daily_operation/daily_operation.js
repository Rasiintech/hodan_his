frappe.pages['daily-operation'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'None',
		single_column: true
	});
}


frappe.pages['daily-operation'].on_page_load = function(wrapper) {
	new DailyOP(wrapper)
}

DailyOP = Class.extend(
	{
		init:function(wrapper){
			this.page = frappe.ui.make_app_page({
				parent : wrapper,
				title: "Daily Operations",
				single_column : true
			});
			this.make()
			this.from_date =  frappe.datetime.get_today()
			this.to_date =  frappe.datetime.get_today()
		},
		make:function(){
			$('.page-body').append("<div id ='report'></div>")
			
			let from_date = this.page.add_field({
				fieldtype: 'Date',
			
				fieldname: 'from_date',
				label : "Date",
				default: frappe.datetime.get_today(),
				
				
				change: () => {
					// alert()
					this.from_date = from_date.get_value()
					get_data(this.from_date , this.to_date)
					// me.setupdata_table()
					// me.curMonth = field.get_value()
					// me.setup_datatable()
				}
			});
			let to_date = this.page.add_field({
				fieldtype: 'Date',
			
				fieldname: 'to_date',
				label : "Date",
				default: frappe.datetime.get_today(),
				
				
				change: () => {
					// alert()
					this.to_date = to_date.get_value()
					get_data(this.from_date , this.to_date)
					// me.setupdata_table()
					// me.curMonth = field.get_value()
					// me.setup_datatable()
				}
			});
			let me = this
			// let $btn2 = this.page.set_secondary_action('Download', () => download_report (me.from_date , me.to_date), 'octicon octicon-print')
			let $btn3 = this.page.set_secondary_action('Print', () => print_report(me.from_date , me.to_date), 'octicon octicon-print')
			let $btn = this.page.set_primary_action('Send Email', () => send_email (from_date , to_date), 'octicon octicon-plus')

			get_data(this.from_date , this.to_date)
			
			
		}
	
	
	
	})

function get_data(from_date , to_date){
	frappe.call({
		method: "his.dashboard_and_history.operation.get_opetations", //dotted path to server method
		args : {"from_date" : from_date , "to_date" : to_date},
		//  args : {"from_date" : currdate , to_date : to_date},
		callback: function(r) {
			// console.log(window.open.document)
			// var x = window;
			// x.document.open().write(r.message);
			// code snippet
			// $(frappe.render_template(frappe.render_template('dashboard_page' ,{"data" : r.message }), me)).appendTo(me.page.main)
			// tbldata = r.message
			// let html = $('.page-body').html()
			$('#report').empty()
			$('#report').html(r.message)
		}})
}
function download_report (from_date , to_date){
	// console.log(from_date)
	
	frappe.call({
		method: "his.dashboard_and_history.operation.assign_date_to_download", //dotted path to server method
		// args : {"_from" : "2022-11-5" , "to" : "2022-11-10"},
		 args : {"from_date" : from_date , "to_date" : to_date},
		callback: function(r) {
			// alert()
			// code snippet
			// $(frappe.render_template(frappe.render_template('dashboard_page' ,{"data" : r.message }), me)).appendTo(me.page.main)
			// tbldata = r.message
		
			// $('.page-body').html(r.message)
		
		var url = frappe.urllib.get_full_url("/api/method/his.dashboard_and_history.operation.download_report")
		// var data = {
		// 	from_date,
		// 	to_date,
		// };
		$.ajax({
			url: url,
			type: 'GET',
			success: function(result) {
	
				if(jQuery.isEmptyObject(result)){
					frappe.msgprint(__('No Records for these settings.'));
				}
				else{
					window.location = url;
				}
			}
		});
	}})

	
}


function print_report(from_date , to_date){
	frappe.call({
		method: "his.dashboard_and_history.operation.get_opetations", //dotted path to server method
		// args : {"_from" : "2022-11-5" , "to" : "2022-11-10"},
		 args : {"from_date" : from_date , to_date : to_date},
		callback: function(r) {
			// console.log(r.message)
			var x = window.open();
			x.document.write(r.message);
			// code snippet
			// $(frappe.render_template(frappe.render_template('dashboard_page' ,{"data" : r.message }), me)).appendTo(me.page.main)
			// tbldata = r.message
			// $('.page-body').html(r.message)
		}})
}

function send_email(){
	frappe.call({
		method: "his.dashboard_and_history.operation.send_emails",
		
		callback: function(r) {
			if(r && r.message) {
				frappe.show_alert({message: __('Emails Queued'), indicator: 'blue'});
			}
			else{
				frappe.msgprint(__('No Records for these settings.'))
			}
		}
	});
}

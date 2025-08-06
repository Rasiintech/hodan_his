
frappe.pages['collected-test'].on_page_load = function(wrapper) {
	new CollectedTests(wrapper)
}

CollectedTests = Class.extend(
	{
		init:function(wrapper){
			this.page = frappe.ui.make_app_page({
				parent : wrapper,
				title: "Collected Samples",
				single_column : true
			});
			this.groupbyD = []
			this.currDate =  frappe.datetime.get_today()
			this.toDate =  frappe.datetime.get_today()
			this.make()
			this.setupdata_table()
			this.make_grouping_btn()
			let myf = this
			this.colms = []
			frappe.realtime.on('lab_resul_update', (data) => {
				// alert("in realtime")
				myf.setupdata_table()
					})
			this.grouping_cols()
		},
		make:function(){

		
			let me = this

			let date = this.page.add_field({
				fieldtype: 'Date',
			
				fieldname: 'date',
				label : "Date",
				default: frappe.datetime.get_today(),
				
				
				change: () => {
					// alert()
					this.currDate = date.get_value()
					me.setupdata_table()
					// me.curMonth = field.get_value()
					// me.setup_datatable()
				}
			});
			let to_date = this.page.add_field({
				fieldtype: 'Date',
			
				fieldname: 'date',
				label : "Date",
				default: frappe.datetime.get_today(),
				
				
				change: () => {
					// alert()
					this.toDate = to_date.get_value()
					me.setupdata_table()
					// me.curMonth = field.get_value()
					// me.setup_datatable()
				}
			});
		
   		
   		
			$(frappe.render_template(frappe.dashbard_page.body, me)).appendTo(me.page.main)




		
		},

		setupdata_table : function(gr_ref){
			let currdate = this.currDate
			let to_date = this.toDate
		let tbldata = []
		frappe.call({
        method: "his.api.labtsamples.get_collected", //dotted path to server method
        // args : {"_from" : "2022-11-5" , "to" : "2022-11-10"},
        //  args : {"currdate" : currdate},
		args : {"from_date" : currdate , to_date : to_date},
		callback: function(r) {
            // code snippet
            // $(frappe.render_template(frappe.render_template('dashboard_page' ,{"data" : r.message }), me)).appendTo(me.page.main)
			tbldata = r.message
        // console.log(r)
   

			
		
		 let me = this
		//  let fields = frappe.get_meta("Sales Order").fields
		 	columns = [
			// {title:"ID", field:"name"},
			// {title:"Patient", field:"customer"},
			{title:"No", field:"id", formatter:"rownum"},
			{title:"PID", field:"patient" ,  headerFilter:"input"},
			{title:"Patient Name", field:"patient_name" ,  headerFilter:"input"},
			{title:"Date", field:"date" ,  headerFilter:"input"},
			{title:"Time", field:"time" ,  headerFilter:"input"},
			{title:"Doctor Name", field:"practitioner" ,  headerFilter:"input",},
			{title:"Source Order", field:"source_order" ,  headerFilter:"input",},
			{title:"Status", field:"status" ,  headerFilter:"input", formatter:"html"},
		
			
			{title:"", field: "modified" ,  headerFilter:"input", formatter:formatter},

			// {title:"Action", field:"action", hozAlign:"center" , formatter:"html"},
			
		 ]
		 this.colms = columns
		//  console.log( this.colms)
	
		let new_data = []
		
		tbldata.forEach(row => {
		
			row['time'] = row.creation.split(' ')[1].split('.')[0]
			row['status'] = "<span style='color:blue'>Collected</span>"
			// row['action'] = btnhml
			
			new_data.push(row)
		})
		// console.log(columns)
this.table = new Tabulator("#collected", {
			// layout:"fitDataFill",
			layout:"fitDataStretch",
			//  layout:"fitColumns",
			// responsiveLayout:"collapse",
			 rowHeight:30, 
			//  selectable:true,
			//  dataTree:true,
			//  dataTreeStartExpanded:true,
			 groupStartOpen:false,
			 printAsHtml:true,
			//  printHeader:`<img src = '/private/files/WhatsApp Image 2022-10-20 at 6.19.02 PM.jpeg'>`,
			//  printFooter:"<h2>Example Table Footer<h2>",
			 rowFormatter:function(row){
				//row - row component
				
				var data = row.getData();
				if(data.custom_urgent){
					row.getElement().style.backgroundColor = "#f00";
					row.getElement().style.color = "#fff";
				}
				// console.log(row.getElement().firstChild)
				
				if(data.source_order == "E.R"){
					row.getElement().firstChild.style.backgroundColor = "#f00";
					row.getElement().firstChild.style.color = "#fff";
				}
				else if(data.source_order == "IPD"){
					row.getElement().firstChild.style.backgroundColor = "#FFA500";
					row.getElement().firstChild.style.color = "#fff";
				}
				else {
					row.getElement().firstChild.style.backgroundColor = "#00FF00";
					row.getElement().firstChild.style.color = "#fff";
				}
			},
			 // groupBy:"customer",
			 groupHeader:function(value, count, data, group){
				 //value - the value all members of this group share
				 //count - the number of rows in this group
				 //data - an array of all the row data objects in this group
				 //group - the group component for the group
			 // console.log(group)
				 return value + "<span style=' margin-left:0px;'>(" + count + "   )</span>";
			 },
			 groupToggleElement:"header",
			 groupBy:groupbyD.length >0 ? groupbyD : "",
			 textDirection: frappe.utils.is_rtl() ? "rtl" : "ltr",
	 
			 columns: columns,
	
			 
			 data: new_data
		 });
		 
		 //  table.getSelectedData(); 
		 let row = this
		 this.table.on("rowClick", function(e ,rows){
			 let selectedRows = row.table.getSelectedRows(); 
			//  alert()
			//  console.log(rows._row.data)
			//  console.log(row.table.getSelectedData())
			//  row.toggle_actions_menu_button(row.table.getSelectedData().length > 0);
			 frappe.set_route("Form" , "Sample Collection" , rows._row.data.name)
			 // document.getElementById("select-stats").innerHTML = data.length;
		   });
	
		}
	
});
		},


		make_grouping_btn:function(){
			gr_columns = [
				// {title:"ID", field:"name"},
				// {title:"Patient", field:"customer"},
				{title:"No", field:"id", formatter:"rownum"},
				{title:"PID", field:"patient" ,  headerFilter:"input"},
				{title:"Patient Name", field:"patient_name" ,  headerFilter:"input"},
				{title:"Date", field:"date" ,  headerFilter:"input"},
				{title:"Time", field:"time" ,  headerFilter:"input"},
				{title:"Doctor Name", field:"practitioner" ,  headerFilter:"input",},
				{title:"Source Order", field:"source_order" ,  headerFilter:"input",},
				{title:"Status", field:"status" ,  headerFilter:"input", formatter:"html"},
			
				
				{title:"", field: "modified" ,  headerFilter:"input", formatter:formatter},
	
				// {title:"Action", field:"action", hozAlign:"center" , formatter:"html"},
				
			 ]
			let listitmes = ''
		
				
	
			
			console.log(gr_columns)
			gr_columns.forEach(field => {
					// console.log(field)
					// if(field.docfield.fieldtype !== "Currency"){
						listitmes += `
 
						<li>
						<input type="checkbox" class="form-check-input groupcheck ml-2"  value = '${field.field}' >
						<label class="form-check-label" for="exampleCheck1">${field.title}</label>
						
					</li>	
						
						`
	
					// }
				
	  
				
			})
			$('.page-heade')
			// 	<button type="button" class="btn btn-default btn-sm" data-toggle="dropdown">
			// 	<span class="dropdown-text">Grouping by</span>
			// 	<ul class="dropdown-menu dropdown-menu-right">
				
					
			// 		${listitmes}
			// 	</ul>
			// </button>
				$(`<div class="mt-2 sort-selector">
				
	
	
	
				<button type="button" class="btn btn-default btn-sm"<a href="#" data-toggle="dropdown" class="dropdown-toggle">Group<b class="caret"></b></a>
				</button>
				<ul class="dropdown-menu">
				${listitmes}
			</ul>
				</div>`).appendTo('.page-head')
			
			// this.group_by_control = new frappe.ui.GroupBy(this);
	
		},

		grouping_cols:function(){

		
			let me = this
			$('.groupcheck').change(function() {
				// alert ("The element with id " + this.value + " changed.");
				// alert()
				let value = this.value
				if(this.checked) {
				groupbyD.push(this.value)
				}
				else{
					groupbyD = groupbyD.filter(function(e) { return e !== value })
				}
				me.setupdata_table(true);
				// setup_datatable()
				
			});
	
		   
		},





	})
let testorder = `

<div class="container">
<div class="row">

<div id="collected" style = "min-width : 100%"></div>

</div>


<!-- endrow 2--- >
</div>


`
frappe.dashbard_page = {
	body : testorder
}

formatter = function(cell, formatterParams, onRendered){
			return frappe.datetime.prettyDate(cell.getValue() , 1)
		}





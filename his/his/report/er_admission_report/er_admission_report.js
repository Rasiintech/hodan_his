
frappe.query_reports['ER Admission Report'] = {
	filters: [
		{fieldname: 'from_date', label: __('From Date'), fieldtype: 'Date'},
		{fieldname: 'to_date', label: __('To Date'), fieldtype: 'Date'},
		{fieldname: 'patient_id', label: __('Patient ID'), fieldtype: 'Link', options: 'Patient'},
		{fieldname: 'admission_type', label: __('Admission Type'), fieldtype: 'Select', options: '\nICU\nNICU\nIPD'},
		{fieldname: 'er_type', label: __('ER Type'), fieldtype: 'Select', options: '\nAdult\nPediatric\nOBS/GYN'},
	],
};

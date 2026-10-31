// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt

async function show_technician_name(frm) {
    const technician_field = frm.fields_dict.technician;

    if (!technician_field) {
        return;
    }

    // Store the Employee ID, but display Employee.employee_name in the Link field.
    technician_field.is_title_link = () => true;
    if (frm.doc.technician) {
        await technician_field.set_link_title(frm.doc.technician);
    }
}

frappe.ui.form.on("Facility Incident Management", {
    onload_post_render(frm) {
        show_technician_name(frm);
    },

    refresh(frm) {
        show_technician_name(frm);
    },

    technician(frm) {
        show_technician_name(frm);
    },

    status(frm) {
        if (frm.doc.status !== "Close" && frm.doc.closing_time) {
            frm.set_value("closing_time", null);
        }
    },

    after_save(frm) {
        if (
            frm.doc.docstatus === 0 &&
            frm.doc.status === "Close" &&
            frm.doc.closing_time
        ) {
            frm.savesubmit();
        }
    },
});

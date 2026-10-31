// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.listview_settings["Facility Incident Management"] = {
    has_indicator_for_draft: true,
    has_indicator_for_cancelled: true,

    get_indicator(doc) {
        if (doc.status === "Open") {
            return [__("Open"), "red", "status,=,Open"];
        }

        if (doc.status === "Close") {
            return [__("Close"), "green", "status,=,Close"];
        }
    },

    onload(listview) {
        const subject = listview.columns.find((column) => column.type === "Subject");
        const tag = listview.columns.find((column) => column.type === "Tag");
        const status = listview.columns.find((column) => column.type === "Status");
        const fields = Object.fromEntries(
            listview.columns
                .filter((column) => column.type === "Field")
                .map((column) => [column.df.fieldname, column])
        );

        listview.columns = [
            subject,
            tag,
            fields.incident_title,
            fields.incident_area,
            fields.technician_name,
            fields.date,
            fields.technician_calling_time,
            status,
        ].filter(Boolean);

        listview.render_header(true);
    },
};

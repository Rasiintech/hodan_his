// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Department Audit", {
	refresh(frm) {
		ensure_item_state_cache(frm);
		enforce_items_grid_controls(frm);
		expand_items_grid_text(frm);
		trigger_checklist_load(frm, {
			preserve_existing: true,
			force_reload: frm.is_new() || !(frm.doc.items || []).length,
		});
	},

	department(frm) {
		trigger_checklist_load(frm);
	},

	date(frm) {
		trigger_checklist_load(frm, { preserve_existing: true });
	},

	frequency(frm) {
		trigger_checklist_load(frm, { preserve_existing: true });
	},
});

frappe.ui.form.on("Department Audit Item", {
	form_render(frm) {
		ensure_item_state_cache(frm);
		enforce_items_grid_controls(frm);
		expand_items_grid_text(frm);
	},

	status(frm, cdt, cdn) {
		cache_item_row_state(frm, locals[cdt][cdn]);
	},

	remarks(frm, cdt, cdn) {
		cache_item_row_state(frm, locals[cdt][cdn]);
	},
});

function enforce_items_grid_controls(frm) {
	const grid = frm.get_field("items").grid;
	grid.df.cannot_add_rows = true;
	grid.df.cannot_delete_rows = true;
	grid.cannot_add_rows = true;
	grid.cannot_delete_rows = true;
	frm.refresh_field("items");

	setTimeout(() => {
		const wrapper = grid.wrapper;
		wrapper.find(".grid-add-row, .grid-remove-rows, .grid-append-row").hide();
		wrapper.find(".grid-delete-row, .grid-remove-row, [data-action='delete_rows']").hide();
		wrapper.find(".row-actions .grid-delete-row, .row-actions .grid-remove-row").hide();
		wrapper.find(".form-in-grid .btn-danger, .grid-row-open .btn-danger").hide();
	}, 0);
}

function expand_items_grid_text(frm) {
	setTimeout(() => {
		const wrapper = frm.get_field("items").grid.wrapper;
		wrapper.css("font-size", "14px");
		wrapper.find(".grid-heading-row, .grid-body, .data-row, .grid-static-col, .control-value").css(
			"font-size",
			"14px"
		);
		wrapper.find('[data-fieldname="task"], [data-fieldname="follow_up"]').css({
			"white-space": "normal",
			"word-break": "break-word",
			"line-height": "1.4",
			"height": "auto",
			"min-height": "56px"
		});
		wrapper.find(".grid-row, .data-row").css("height", "auto");
	}, 0);
}

function trigger_checklist_load(frm, options = {}) {
	if (!frm.doc.department) return;
	const { force_reload = false } = options;

	// Date is part of the user's audit entry flow, so once the key fields are set
	// we proactively try to populate the checklist even if the user selected them in a different order.
	if (frm.doc.date && (frm.doc.frequency || "Daily")) {
		if (!force_reload && !frm.is_new() && (frm.doc.items || []).length) {
			return;
		}

		load_checklist_items(frm, options);
	}
}

function load_checklist_items(frm, options = {}) {
	const { preserve_existing = false } = options;
	const selected_frequency = frm.doc.frequency || "Daily";

	if (!frm.doc.department) {
		frm.clear_table("items");
		frm.refresh_field("items");
		enforce_items_grid_controls(frm);
		expand_items_grid_text(frm);
		return;
	}

	ensure_item_state_cache(frm);
	const existing_items = preserve_existing ? capture_existing_item_values(frm) : {};

	frappe.call({
		method: "his.his.doctype.department_checklist.department_checklist.get_checklist_items",
		args: {
			department: frm.doc.department,
			frequency: selected_frequency,
		},
		freeze: true,
		freeze_message: __("Loading department checklist..."),
		callback(r) {
			const rows = r.message || [];
			frm.clear_table("items");

			rows.forEach((row) => {
				const item = frm.add_child("items");
				const preserved =
					existing_items[get_item_key(row)] ||
					existing_items[get_item_cache_key(row)] ||
					{};

				Object.assign(item, row, {
					status: preserved.status || row.status || "Pending",
					remarks: preserved.remarks || row.remarks || "",
				});

				cache_item_row_state(frm, item);
			});

			frm.refresh_field("items");
			enforce_items_grid_controls(frm);
			expand_items_grid_text(frm);

			if (!rows.length && frm.doc.department) {
				frappe.show_alert({
					message: __(
						"No checklist items found for department {0} with frequency {1}.",
						[frm.doc.department, selected_frequency]
					),
					indicator: "orange",
				});
			}
		},
	});
}

function capture_existing_item_values(frm) {
	const cached_items = { ...(frm._department_audit_item_state || {}) };

	return (frm.doc.items || []).reduce((accumulator, row) => {
		accumulator[get_item_key(row)] = {
			status: row.status,
			remarks: row.remarks,
		};
		accumulator[get_item_cache_key(row)] = {
			status: row.status,
			remarks: row.remarks,
		};
		return accumulator;
	}, cached_items);
}

function get_item_key(row) {
	return [row.area, row.task, row.follow_up].map((value) => (value || "").trim()).join("||");
}

function get_item_cache_key(row) {
	return [
		(row.frequency || "").trim(),
		(row.area || "").trim(),
		(row.task || "").trim(),
		(row.follow_up || "").trim(),
	].join("||");
}

function ensure_item_state_cache(frm) {
	if (!frm._department_audit_item_state) {
		frm._department_audit_item_state = {};
	}

	(frm.doc.items || []).forEach((row) => cache_item_row_state(frm, row, { skip_ensure: true }));
}

function cache_item_row_state(frm, row, options = {}) {
	if (!row) {
		return;
	}

	if (!options.skip_ensure) {
		ensure_item_state_cache(frm);
	}

	const state = {
		status: row.status || "Pending",
		remarks: row.remarks || "",
	};

	frm._department_audit_item_state[get_item_key(row)] = state;
	frm._department_audit_item_state[get_item_cache_key(row)] = state;
}

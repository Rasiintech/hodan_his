// frappe.pages['dept-audit'].on_page_load = function(wrapper) {
// 	var page = frappe.ui.make_app_page({
// 		parent: wrapper,
// 		title: 'None',
// 		single_column: true
// 	});
// }

frappe.pages["dept-audit"].on_page_load = function (wrapper) {
	new DepartmentAuditOverview(wrapper);
};


class DepartmentAuditOverview {
	constructor(wrapper) {
		this.wrapper = wrapper;
		$(this.wrapper).addClass("department-audit-overview-page");
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: "HOD Checklist Dashboard",
			single_column: true,
		});

		this.make();
	}

	make() {
		this.inject_style();

		this.page.main.html(`
			<div class="hod-dashboard-page">
				<section class="hod-topbar">
					<div>
						<div class="hod-eyebrow">Hodan Hospital
</div>
						<h1 class="hod-title">HOD's Checklist Dashboard</h1>
						
					</div>
					<div class="hod-topbar-actions">
						<button class="btn btn-default btn-sm hod-export-btn">Export Report</button>
					</div>
				</section>

				<section class="hod-hero-card">
					<div class="hod-hero-copy">
						<div class="hod-hero-chip">Exclusive for CEO Office</div>
						<h2>Review what needs attention first, without losing sight of completed progress.</h2>
						<p>
							Monitor daily, weekly and monthly completed and pending tasks across all departments.
						</p>
					</div>
					<div class="hod-hero-metrics">
						<div class="hod-hero-mini-card hod-hero-clickable js-remarks-card" role="button" tabindex="0">
							<div class="hod-hero-mini-label">Remarks</div>
							<div class="hod-hero-mini-value js-remarks-count">0</div>
						</div>
						<div class="hod-hero-mini-card hod-hero-clickable js-alert-card" role="button" tabindex="0">
							<div class="hod-hero-mini-label">Idle Departments</div>
							<div class="hod-hero-mini-value js-alert-count">0</div>
						</div>
					</div>
				</section>

				<section class="hod-filter-card">
					<div class="hod-filter-field hod-filter-date"></div>
					<div class="hod-filter-field hod-filter-frequency"></div>
					<div class="hod-filter-field hod-filter-department"></div>
					<div class="hod-filter-field hod-filter-action">
						<button class="btn btn-primary btn-block js-apply-filters">Apply Filters</button>
					</div>
				</section>

				<section class="hod-stat-grid js-summary-grid"></section>

				<section class="hod-main-grid">
					<aside class="hod-sidebar-card">
						<div class="hod-sidebar-head">
							<h3>Submitted Department</h3>
							<span class="hod-sidebar-total js-department-total">0 total</span>
						</div>
						<div class="hod-sidebar-list js-department-health"></div>
					</aside>

					<main class="hod-content-area">
						<div class="js-hero-panel" style="display:none;"></div>
						<div class="js-department-details"></div>
						<div class="hod-insight-grid js-insight-grid"></div>
					</main>
				</section>
			</div>
		`);

		this.date_field = frappe.ui.form.make_control({
			parent: this.page.main.find(".hod-filter-date"),
			df: {
				fieldtype: "Date",
				fieldname: "audit_date",
				label: "Date",
				default: frappe.datetime.get_today(),
				onchange: () => this.load_data(),
			},
			render_input: true,
		});

		this.frequency_field = frappe.ui.form.make_control({
			parent: this.page.main.find(".hod-filter-frequency"),
			df: {
				fieldtype: "Select",
				fieldname: "frequency",
				label: "Frequency",
				options: "Daily\nWeekly\nMonthly",
				default: "Daily",
				onchange: () => this.load_data(),
			},
			render_input: true,
		});

		this.department_field = frappe.ui.form.make_control({
			parent: this.page.main.find(".hod-filter-department"),
			df: {
				fieldtype: "Link",
				fieldname: "department",
				label: "Department",
				options: "Department",
				onchange: () => this.load_data(),
			},
			render_input: true,
		});

		this.checklist_departments = [];
		this.current_departments = [];
		this.current_draft_departments = [];
		this.current_summary = {};
		this.current_task_status_map = {};
		this.task_status_request_id = 0;

		this.department_field.get_query = () => ({
			filters: {
				name: ["in", this.checklist_departments.length ? this.checklist_departments : [""]],
			},
		});

		this.page.main.find(".js-apply-filters").on("click", () => this.load_data());
		this.page.main.find(".hod-export-btn").on("click", () => window.print());

		this.page.main.find(".js-alert-card").on("click keypress", (e) => {
			if (e.type === "click" || e.key === "Enter" || e.key === " ") {
				this.render_alerts_panel();
			}
		});

		this.page.main.find(".js-remarks-card").on("click keypress", (e) => {
			if (e.type === "click" || e.key === "Enter" || e.key === " ") {
				this.render_remarks_panel();
			}
		});

		this.page.main.on("click keypress", ".js-missing-submission-card", (e) => {
			if (e.type === "click" || e.key === "Enter" || e.key === " ") {
				this.render_missing_submissions_panel();
			}
		});

		this.page.main.on("click keypress", ".js-pending-tasks-card", (e) => {
			if (e.type === "click" || e.key === "Enter" || e.key === " ") {
				this.render_pending_tasks_panel();
			}
		});

		this.page.main.on("click", ".js-add-task-btn", (e) => {
			const $button = $(e.currentTarget);
			this.create_task_from_remark(
				cint($button.attr("data-department-index")),
				$button.attr("data-task-type"),
				cint($button.attr("data-task-index"))
			);
		});

		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Department Checklist",
				fields: ["department"],
				limit_page_length: 0,
			},
			callback: (r) => {
				this.checklist_departments = [...new Set((r.message || []).map((row) => row.department).filter(Boolean))];
				this.load_data();
			},
			error: () => this.load_data(),
		});

		this.page.set_primary_action("Refresh Data", () => this.load_data(), "refresh");
	}

	load_data() {
		frappe.call({
			method: "his.his.doctype.department_audit.department_audit.get_ceo_daily_view",
			args: {
				audit_date: this.date_field.get_value(),
				frequency: this.frequency_field.get_value(),
				department: this.department_field.get_value(),
			},
			freeze: true,
			freeze_message: __("Loading department audit overview..."),
			callback: (r) => {
				this.render(r.message || {});
			},
		});
	}

	render(data) {
		const summary = data.summary || {};
		const departments = data.departments || [];
		const draftDepartments = data.draft_departments || [];
		this.current_departments = departments;
		this.current_draft_departments = draftDepartments;
		this.current_summary = summary;
		this.refresh_task_status_map().then(() => this.render_view());
	}

	render_view() {
		const summary = this.current_summary || {};
		const departments = this.current_departments || [];
		this.render_summary(summary, departments);
		this.render_department_health(departments);
		this.render_departments(departments);
		this.render_insights(summary, departments);
		this.render_remarks_panel();
	}

	render_summary(summary, departments) {
		const done = cint(summary.done || 0);
		const pending = cint(summary.pending || 0);
		const total = done + pending;
		const completion_rate = total ? Math.round((done / total) * 100) : 0;
		const draftDepartments = this.get_draft_departments();
		const inactiveDepartments = this.get_not_active_departments();
		const remarks_count = this.get_all_remarks().length;
		const selectedDate = this.date_field?.get_value() || "";

		this.page.main.find(".js-remarks-count").text(remarks_count);
		this.page.main.find(".js-alert-count").text(inactiveDepartments.length);
		this.page.main.find(".js-department-total").text(`${cint(summary.departments || departments.length || 0)} total`);

		const cards = [
			{ label: "Submitted Departments", value: cint(summary.departments || departments.length || 0), note: "Submitted", tone: "neutral" },
			{
				label: "Departments Not Submitted",
				value: draftDepartments.length,
				note: draftDepartments.length ? "Needs COO Submission" : `No draft on ${selectedDate || "selected date"}`,
				tone: "warning",
				clickable: true,
				click_class: "js-missing-submission-card",
			},
			{
				label: "Pending Tasks",
				value: pending,
				note: "Needs attention",
				tone: "pending",
				clickable: true,
				click_class: "js-pending-tasks-card",
			},
			{ label: "Completed", value: done, note: `${completion_rate}% completion`, tone: "done" },
			
		];

		const html = cards.map((card) => `
			<div class="hod-stat-card hod-${card.tone} ${card.clickable ? `hod-stat-clickable ${card.click_class || ""}` : ""}" ${card.clickable ? 'role="button" tabindex="0"' : ""}>
				<div class="hod-stat-label">${frappe.utils.escape_html(card.label)}</div>
				<div class="hod-stat-row">
					<div class="hod-stat-value">${card.value}</div>
					<div class="hod-stat-note">${frappe.utils.escape_html(card.note)}</div>
				</div>
			</div>
		`).join("");

		this.page.main.find(".js-summary-grid").html(html);
	}

	render_default_panel() {
		this.close_hero_panel();
	}

	close_hero_panel() {
		this.page.main.find(".js-hero-panel").hide().empty();
	}

	open_hero_panel(html) {
		this.page.main.find(".js-hero-panel").html(html).show();
		this.page.main.find(".js-close-hero-panel").on("click", () => this.close_hero_panel());
	}

	get_draft_departments() {
		const selectedDepartment = (this.department_field?.get_value() || "").trim();
		return (this.current_draft_departments || []).filter((department) => {
			const departmentName = (department.department || "").trim();
			if (!departmentName) return false;
			return !selectedDepartment || departmentName === selectedDepartment;
		});
	}

	get_not_active_departments() {
		const selectedDepartment = (this.department_field?.get_value() || "").trim();
		const availableDepartments = selectedDepartment
			? [selectedDepartment]
			: (this.checklist_departments || []).filter(Boolean);
		const activeDepartments = new Set(
			(this.current_departments || []).map((department) => (department.department || "").trim()).filter(Boolean)
		);
		(this.current_draft_departments || []).forEach((department) => {
			const departmentName = (department.department || "").trim();
			if (departmentName) activeDepartments.add(departmentName);
		});

		return availableDepartments.filter((department) => !activeDepartments.has(department));
	}

	get_all_remarks() {
		const remarks = [];

		(this.current_departments || []).forEach((department, department_index) => {
			(department.pending_tasks || []).forEach((task, task_index) => {
				if (task.remarks) {
					remarks.push({
						department: department.department || "Department",
						area: task.area || "General",
						task: task.task || "",
						remarks: task.remarks || "",
						status: "Pending",
						department_index,
						task_type: "pending",
						task_index,
					});
				}
			});

			(department.done_tasks || []).forEach((task, task_index) => {
				if (task.remarks) {
					remarks.push({
						department: department.department || "Department",
						area: task.area || "General",
						task: task.task || "",
						remarks: task.remarks || "",
						status: "Done",
						department_index,
						task_type: "done",
						task_index,
					});
				}
			});
		});

		return remarks;
	}

	create_task_from_remark(departmentIndex, taskType, taskIndex) {
		const department = (this.current_departments || [])[departmentIndex];
		if (!department) return;

		const tasks = taskType === "done" ? (department.done_tasks || []) : (department.pending_tasks || []);
		const task = tasks[taskIndex];

		if (!task || !task.remarks) {
			frappe.msgprint(__("No remarks found for this entry."));
			return;
		}


		frappe.new_doc("Task", {}, function(doc) {
			doc.subject = task.area || __("General");
			doc.description = task.remarks || "";
		});

		
	}

	refresh_task_status_map() {
		const requestId = ++this.task_status_request_id;
		const entries = this.get_all_remarks();
		const subjects = [...new Set(entries.map((item) => (item.area || "General").trim()).filter(Boolean))];

		if (!subjects.length) {
			this.current_task_status_map = {};
			return Promise.resolve();
		}

		return frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Task",
				fields: ["name", "subject", "description", "status"],
				filters: {
					subject: ["in", subjects],
				},
				limit_page_length: 0,
			},
		}).then((r) => {
			if (requestId !== this.task_status_request_id) return;

			const taskStatusMap = {};
			(r.message || []).forEach((task) => {
				const key = this.get_task_match_key(task.subject, task.description);
				if (!key) return;
				taskStatusMap[key] = task.status;
			});

			this.current_task_status_map = taskStatusMap;
		});
	}

	get_task_match_key(area, remarks) {
		const normalizedArea = (area || "General").trim();
		const normalizedRemarks = (remarks || "").trim();
		if (!normalizedRemarks) return "";
		return `${normalizedArea}||${normalizedRemarks}`;
	}

	is_task_completed(task) {
		const key = this.get_task_match_key(task?.area, task?.remarks);
		return key && this.current_task_status_map[key] === "Completed";
	}

	get_task_status(task) {
		const key = this.get_task_match_key(task?.area, task?.remarks);
		return key ? this.current_task_status_map[key] || "" : "";
	}

	get_task_status_badge_class(status) {
		if (status === "Completed") return "is-completed";
		if (status === "Open") return "is-open";
		if (status === "Cancelled") return "is-cancelled";
		return "is-neutral";
	}

	get_panel_task_class(status) {
		if (status === "Done" || status === "Completed") return "hod-panel-subitem-done";
		return "hod-panel-subitem-pending";
	}

	render_task_action(task, departmentIndex, taskType, taskIndex) {
		if (!task?.remarks) return "";

		const taskStatus = this.get_task_status(task);
		if (taskStatus) {
			return `
				<span class="hod-task-status-badge ${this.get_task_status_badge_class(taskStatus)}">
					${frappe.utils.escape_html(String(taskStatus).toUpperCase())}
				</span>
			`;
		}

		return `
			<button
				class="btn btn-xs btn-default hod-add-task-btn js-add-task-btn"
				data-department-index="${departmentIndex}"
				data-task-type="${taskType}"
				data-task-index="${taskIndex}"
				type="button"
			>
				Add Task
			</button>
		`;
	}

	render_alerts_panel() {
	const inactiveDepartments = this.get_not_active_departments();
	const $panel = this.page.main.find(".js-hero-panel");

	if (!inactiveDepartments.length) {
		$panel.html(`
			<div class="hod-panel-card">
				<div class="hod-panel-head">
					<div class="hod-panel-title">Inactive Departments</div>
					<button class="hod-panel-close js-close-hero-panel" type="button">&times;</button>
				</div>
				<div class="hod-empty-card">All departments entered values for the selected date and frequency.</div>
			</div>
		`).show();

		$panel.find(".js-close-hero-panel").on("click", () => this.close_hero_panel());
		return;
	}

		const html = inactiveDepartments.map((department) => `
			<div class="hod-panel-item">
				<div class="hod-panel-item-head">
					<div>
						<div class="hod-panel-item-title hod-panel-item-title-missing">${frappe.utils.escape_html(department || "Department")}</div>
					<div class="hod-panel-item-meta">No value entered for the selected date and frequency.</div>
				</div>
			</div>
		</div>
	`).join("");

	$panel.html(`
		<div class="hod-panel-card">
			<div class="hod-panel-head">
				<div class="hod-panel-title">Inactive Departments</div>
				<button class="hod-panel-close js-close-hero-panel" type="button">&times;</button>
			</div>
			<div class="hod-panel-list">${html}</div>
		</div>
	`).show();

	$panel.find(".js-close-hero-panel").on("click", () => this.close_hero_panel());
}

	render_missing_submissions_panel() {
		const departments = this.get_draft_departments();
		const $panel = this.page.main.find(".js-hero-panel");
		const selectedDate = this.date_field?.get_value() || "";
		const selectedFrequency = this.frequency_field?.get_value() || "";

		if (!departments.length) {
			$panel.html(`
				<div class="hod-panel-card">
					<div class="hod-panel-head">
						<div class="hod-panel-title">Departments Not Submitted</div>
						<button class="hod-panel-close js-close-hero-panel" type="button">&times;</button>
					</div>
					<div class="hod-empty-card">No departments entered values in Draft status for ${frappe.utils.escape_html(selectedDate || "the selected date")} (${frappe.utils.escape_html(selectedFrequency || "selected frequency")}).</div>
				</div>
			`).show();

			$panel.find(".js-close-hero-panel").on("click", () => this.close_hero_panel());
			return;
		}

		const html = departments.map((department) => `
			<div class="hod-panel-item hod-panel-item-draft">
				<div class="hod-panel-item-head">
					<div>
						<div class="hod-panel-item-title hod-panel-item-title-draft">${frappe.utils.escape_html(department.department || "Department")}</div>
						<div class="hod-panel-item-meta">Entered values but the audit is still in Draft status for the selected date and frequency.</div>
					</div>
				</div>
			</div>
		`).join("");

		$panel.html(`
			<div class="hod-panel-card">
				<div class="hod-panel-head">
					<div class="hod-panel-title">Departments Not Submitted</div>
					<button class="hod-panel-close js-close-hero-panel" type="button">&times;</button>
				</div>
				<div class="hod-panel-list">${html}</div>
			</div>
		`).show();

		$panel.find(".js-close-hero-panel").on("click", () => this.close_hero_panel());
	}

	render_pending_tasks_panel() {
		const pendingTasks = [];
		(this.current_departments || []).forEach((department, department_index) => {
			(department.pending_tasks || []).forEach((task, task_index) => {
				pendingTasks.push({
					department: department.department || "Department",
					area: task.area || "General",
					task: task.task || "",
					follow_up: task.follow_up || "",
					remarks: task.remarks || "",
					department_index,
					task_type: "pending",
					task_index,
				});
			});
		});
		const $panel = this.page.main.find(".js-hero-panel");

		if (!pendingTasks.length) {
			$panel.html(`
				<div class="hod-panel-card">
					<div class="hod-panel-head">
						<div class="hod-panel-title">Pending Tasks</div>
						<button class="hod-panel-close js-close-hero-panel" type="button">&times;</button>
					</div>
					<div class="hod-empty-card">No pending tasks found for the selected filters.</div>
				</div>
			`).show();

			$panel.find(".js-close-hero-panel").on("click", () => this.close_hero_panel());
			return;
		}

		const grouped = pendingTasks.reduce((acc, item) => {
			const department = item.department || "Department";
			if (!acc[department]) acc[department] = [];
			acc[department].push(item);
			return acc;
		}, {});

		const html = Object.keys(grouped).sort((a, b) => a.localeCompare(b)).map((department) => {
			const items = grouped[department];

			return `
				<div class="hod-panel-item">
					<div class="hod-panel-item-head">
						<div>
							<div class="hod-panel-item-title">${frappe.utils.escape_html(department)}</div>
							<div class="hod-panel-item-meta">${items.length} pending task${items.length > 1 ? "s" : ""}</div>
						</div>
					</div>

					<div class="hod-panel-sublist">
						${items.map((item) => `
							<div class="hod-panel-subitem ${this.get_panel_task_class('Pending')}">
								<div class="hod-panel-subitem-area">${frappe.utils.escape_html(item.area || "General")}</div>
								<div class="hod-panel-subitem-text">${frappe.utils.escape_html(item.task || "")}</div>
								${item.follow_up ? `<div class="hod-panel-subitem-note">${frappe.utils.escape_html(item.follow_up)}</div>` : ""}
								${item.remarks ? `
									<div class="hod-task-remark-wrap">
										<div class="hod-task-remark">
											<strong>Remarks:</strong> ${frappe.utils.escape_html(item.remarks)}
										</div>
										${this.render_task_action(item, item.department_index, item.task_type, item.task_index)}
									</div>
								` : ""}
							</div>
						`).join("")}
					</div>
				</div>
			`;
		}).join("");

		$panel.html(`
			<div class="hod-panel-card">
				<div class="hod-panel-head">
					<div class="hod-panel-title">Pending Tasks</div>
					<button class="hod-panel-close js-close-hero-panel" type="button">&times;</button>
				</div>
				<div class="hod-panel-list">${html}</div>
			</div>
		`).show();

		$panel.find(".js-close-hero-panel").on("click", () => this.close_hero_panel());
	}

	render_remarks_panel() {
		const remarks = this.get_all_remarks();
		const $panel = this.page.main.find(".js-hero-panel");

		if (!remarks.length) {
			$panel.html(`
				<div class="hod-panel-card">
					<div class="hod-panel-head">
						<div class="hod-panel-title">Remarks</div>
						<button class="hod-panel-close js-close-hero-panel" type="button">&times;</button>
					</div>
					<div class="hod-empty-card">No remarks found for the selected filters.</div>
				</div>
			`).show();

			$panel.find(".js-close-hero-panel").on("click", () => this.close_hero_panel());
			return;
		}

		const grouped = remarks.reduce((acc, item) => {
			const department = item.department || "Department";
			if (!acc[department]) acc[department] = [];
			acc[department].push(item);
			return acc;
		}, {});

		const html = Object.keys(grouped).map((department) => {
			const items = grouped[department];

			return `
				<div class="hod-panel-item">
					<div class="hod-panel-item-head">
						<div>
							<div class="hod-panel-item-title">${frappe.utils.escape_html(department)}</div>
							<div class="hod-panel-item-meta">${items.length} remark${items.length > 1 ? "s" : ""}</div>
						</div>
					</div>

					<div class="hod-panel-sublist">
						${items.map((item) => `
							<div class="hod-panel-subitem ${this.get_panel_task_class(item.status)}">
								<div class="hod-panel-subitem-area">
									${frappe.utils.escape_html(item.area)} • ${frappe.utils.escape_html(item.status)}
								</div>
								<div class="hod-panel-subitem-text">${frappe.utils.escape_html(item.task)}</div>
								<div class="hod-task-remark-wrap">
									<div class="hod-task-remark">
										<strong>Remarks:</strong> ${frappe.utils.escape_html(item.remarks)}
									</div>
									${this.render_task_action(item, item.department_index, item.task_type, item.task_index)}
								</div>
							</div>
						`).join("")}
					</div>
				</div>
			`;
		}).join("");

		$panel.html(`
			<div class="hod-panel-card">
				<div class="hod-panel-head">
					<div class="hod-panel-title">Remarks</div>
					<button class="hod-panel-close js-close-hero-panel" type="button">&times;</button>
				</div>
				<div class="hod-panel-list">${html}</div>
			</div>
		`).show();

		$panel.find(".js-close-hero-panel").on("click", () => this.close_hero_panel());
	}

	render_department_health(departments) {
		if (!departments.length) {
			this.page.main.find(".js-department-health").html(`
				<div class="hod-empty-card">No departments found for the selected filters.</div>
			`);
			return;
		}

		const html = departments.map((department, index) => {
			const name = department.department || "Department";
			const pending = cint(department.counts?.pending || 0);
			const done = cint(department.counts?.done || 0);

			return `
				<button class="hod-sidebar-item ${index === 0 ? "is-active" : ""}" data-index="${index}">
					<div class="hod-sidebar-name">${frappe.utils.escape_html(name)}</div>
					<div class="hod-sidebar-meta-row">
						<span class="hod-badge hod-badge-pending">${pending} pending</span>
						<span class="hod-badge hod-badge-done">${done} done</span>
					</div>
				</button>
			`;
		}).join("");

		const $health = this.page.main.find(".js-department-health");
		$health.html(html);

		$health.find(".hod-sidebar-item").on("click", (e) => {
			const index = cint($(e.currentTarget).attr("data-index"));
			$health.find(".hod-sidebar-item").removeClass("is-active");
			$(e.currentTarget).addClass("is-active");
			this.render_department_panel(this.current_departments[index]);
		});
	}

	// render_departments(departments) {
	// 	if (!departments.length) {
	// 		this.page.main.find(".js-department-details").html(`
	// 			<div class="hod-empty-card">Welcome to Hodan Hospital Executive Dashboard on HOD Checklist Review. Please Select Date and Frequency</div>
	// 		`);
	// 		return;
	// 	}

	// 	this.page.main.find(".js-department-details").html("");
	// }


		render_departments(departments) {
		if (!departments.length) {
			this.page.main.find(".js-department-details").html(`
				<div class="hod-empty-card" style="font-weight: bold; font-size: 30px;">
					<div>
						No submitted department audits found for the selected filters.
					</div>
					<div style="
						font-size: 18px;
						background: #3b4449;
						color: #f5f5f5;
						margin-top: 10px;
						padding: 8px;
						display: inline-block;
						border-radius: 12px;
					">
						Draft audits appear in Departments Not Submitted. Departments with no record appear in Inactive Departments.
					</div>
				</div>
			`);
			return;
		}

		this.page.main.find(".js-department-details").html("");
	}


	render_department_panel(department) {
		if (!department) {
			this.close_hero_panel();
			return;
		}

		const departmentIndex = this.current_departments.indexOf(department);
		const pending = cint(department.counts?.pending || 0);
		const done = cint(department.counts?.done || 0);
		const html = `
			<div class="hod-panel-card hod-panel-card-department">
				<div class="hod-panel-head">
					<div>
						${department.audit_name
							? `<div class="hod-detail-link-wrap"><a class="hod-detail-link" href="/app/department-audit/${encodeURIComponent(department.audit_name)}" target="_blank">${frappe.utils.escape_html(department.audit_name)}</a></div>`
							: `<div class="hod-detail-chip">Audit not entered</div>`}
						<div class="hod-panel-title">${frappe.utils.escape_html(department.department || "Department")}</div>
						<div class="hod-panel-item-meta">Submitted department details</div>
					</div>
					<button class="hod-panel-close js-close-hero-panel" type="button">&times;</button>
				</div>
				<div class="hod-detail-badges">
					<span class="hod-badge hod-badge-pending">Pending ${pending}</span>
					<span class="hod-badge hod-badge-done">Done ${done}</span>
				</div>
				<div class="hod-task-grid">
					${this.render_task_block("Pending Tasks", department.pending_tasks || [], "pending", departmentIndex)}
					${this.render_task_block("Completed Tasks", department.done_tasks || [], "done", departmentIndex)}
				</div>
			</div>
		`;

		this.page.main.find(".js-department-details").html("");
		this.open_hero_panel(html);
	}

	render_single_department(department) {
		if (!department) {
			this.page.main.find(".js-department-details").html("");
			return;
		}

		const departmentIndex = this.current_departments.indexOf(department);
		const pending = cint(department.counts?.pending || 0);
		const done = cint(department.counts?.done || 0);
		const html = `
			<section class="hod-detail-card">
				<div class="hod-detail-head">
					<div>
						${department.audit_name
							? `<div class="hod-detail-link-wrap"><a class="hod-detail-link" href="/app/department-audit/${encodeURIComponent(department.audit_name)}" target="_blank">${frappe.utils.escape_html(department.audit_name)}</a></div>`
							: `<div class="hod-detail-chip">Audit not entered • Checklist shown as pending</div>`}
						<h3>${frappe.utils.escape_html(department.department || "Department")}</h3>
						<p>A clearer two-column task layout with stronger status visibility.</p>
					</div>
					<div class="hod-detail-badges">
						<span class="hod-badge hod-badge-pending">Pending ${pending}</span>
						<span class="hod-badge hod-badge-done">Done ${done}</span>
					</div>
				</div>

				<div class="hod-task-grid">
					${this.render_task_block("Pending Tasks", department.pending_tasks || [], "pending", departmentIndex)}
					${this.render_task_block("Completed Tasks", department.done_tasks || [], "done", departmentIndex)}
				</div>
			</section>
		`;

		this.page.main.find(".js-department-details").html(html);
	}

	render_task_block(title, tasks, tone, departmentIndex) {
		const body = tasks.length
			? tasks.map((task, taskIndex) => `
				<div class="hod-task-card">
					<div class="hod-task-area">${frappe.utils.escape_html(task.area || "General")}</div>
					<div class="hod-task-text">${frappe.utils.escape_html(task.task || "")}</div>
					${task.follow_up ? `<div class="hod-task-subline">${frappe.utils.escape_html(task.follow_up)}</div>` : ""}
					${task.remarks ? `
						<div class="hod-task-remark-wrap">
							<div class="hod-task-remark"><strong>Remarks:</strong> ${frappe.utils.escape_html(task.remarks)}</div>
							${this.render_task_action(task, departmentIndex, tone, taskIndex)}
						</div>
					` : ""}
				</div>
			`).join("")
			: `
				<div class="hod-task-empty-card">
					<div class="hod-task-empty-title">No ${frappe.utils.escape_html(title.toLowerCase())}</div>
					<div class="hod-task-empty-text">Once audits are submitted, tasks will appear here with clearer visual grouping.</div>
				</div>
			`;

		return `
			<div class="hod-task-column hod-task-column-${tone}">
				<div class="hod-task-column-head">
					<h4>${frappe.utils.escape_html(title)}</h4>
					<span class="hod-column-chip ${tone === "pending" ? "is-pending" : "is-done"}">
						${tone === "pending" ? "Needs review" : "On track"}
					</span>
				</div>
				<div class="hod-task-column-body">${body}</div>
			</div>
		`;
	}

	render_insights(summary, departments) {
		const most_delayed = [...departments].sort((a, b) => cint(b.counts?.pending || 0) - cint(a.counts?.pending || 0))[0];
		const best_done = [...departments].sort((a, b) => cint(b.counts?.done || 0) - cint(a.counts?.done || 0))[0];
		const total_done = cint(summary.done || 0);
		const total_pending = cint(summary.pending || 0);
		const recommendation = total_pending > total_done ? "Escalate pending bottlenecks" : "Maintain current follow-up pace";

		const cards = [
			{
				label: "Most delayed unit",
				value: most_delayed?.department || "-",
				description: `${cint(most_delayed?.counts?.pending || 0)} open items require action.`
			},
			{
				label: "Best completion rate",
				value: best_done?.department || "-",
				description: `${cint(best_done?.counts?.done || 0)} tasks completed.`
			},
			{
				label: "Recommended action",
				value: recommendation,
				description: total_pending > total_done
					? "Focus on unresolved department checkpoints first."
					: "Keep review cadence steady across departments."
			},
		];

		const html = cards.map((card) => `
			<div class="hod-insight-card">
				<div class="hod-insight-label">${frappe.utils.escape_html(card.label)}</div>
				<div class="hod-insight-value">${frappe.utils.escape_html(card.value)}</div>
				<div class="hod-insight-text">${frappe.utils.escape_html(card.description)}</div>
			</div>
		`).join("");

		this.page.main.find(".js-insight-grid").html(html);
	}

	make_short_label(name) {
		if (!name) return "-";
		const parts = name.split(/\s+/).filter(Boolean);
		return parts.slice(0, 3).map((p) => p[0]).join("").toUpperCase();
	}

	inject_style() {
		if ($("#hod-dashboard-redesign-style").length) return;

		$(
			`<style id="hod-dashboard-redesign-style">
				.department-audit-overview-page .layout-main-section {
					background: #f8fafc;
				}

				.department-audit-overview-page .page-head,
				.department-audit-overview-page .page-title {
					background: transparent !important;
					box-shadow: none !important;
					border: none !important;
				}

				.department-audit-overview-page .page-head .title-text,
				.department-audit-overview-page .page-title .title-text {
					display: none;
				}

				.hod-dashboard-page {
					padding: 24px 8px 36px;
					background: #f8fafc;
					min-height: calc(100vh - 120px);
				}

				.hod-topbar {
					display: flex;
					justify-content: space-between;
					align-items: flex-start;
					gap: 16px;
					margin-bottom: 24px;
				}

				.hod-eyebrow {
					font-size: 12px;
					font-weight: 700;
					text-transform: uppercase;
					letter-spacing: 0.18em;
					color: #64748b;
					margin-bottom: 10px;
				}

				.hod-title {
					margin: 0;
					font-size: 34px;
					line-height: 1.15;
					font-weight: 700;
					color: #0f172a;
				}

				.hod-subtitle {
					margin: 12px 0 0;
					max-width: 820px;
					font-size: 15px;
					color: #475569;
				}

				.hod-topbar-actions {
					display: flex;
					gap: 10px;
				}

				.hod-hero-card {
					display: grid;
					grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.8fr);
					gap: 24px;
					padding: 32px;
					border-radius: 28px;
					background: linear-gradient(135deg, #f59e0b 0%, #fb923c 42%, #111827 100%);
					color: #fff;
					box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
					margin-bottom: 22px;
				}

				.hod-hero-chip {
					display: inline-flex;
					padding: 6px 12px;
					border-radius: 999px;
					background: rgba(255, 255, 255, 0.14);
					font-size: 12px;
					font-weight: 600;
					margin-bottom: 14px;
					backdrop-filter: blur(8px);
				}

				.hod-hero-copy h2 {
					margin: 0 0 10px;
					font-size: 34px;
					line-height: 1.15;
					font-weight: 700;
				}

				.hod-hero-copy p {
					margin: 0;
					font-size: 15px;
					line-height: 1.7;
					color: rgba(255, 255, 255, 0.9);
				}

				.hod-hero-metrics {
					display: grid;
					grid-template-columns: 1fr 1fr;
					gap: 12px;
					align-self: end;
				}

				.hod-hero-mini-card {
					padding: 18px;
					border-radius: 20px;
					background: rgba(255, 255, 255, 0.12);
					backdrop-filter: blur(10px);
				}

				.hod-hero-clickable {
					cursor: pointer;
					transition: transform 0.18s ease, background 0.18s ease;
				}

				.hod-hero-clickable:hover,
				.hod-hero-clickable:focus {
					background: rgba(255, 255, 255, 0.18);
					transform: translateY(-1px);
					outline: none;
				}

				.hod-hero-mini-label {
					font-size: 13px;
					color: rgba(255, 255, 255, 0.75);
					margin-bottom: 8px;
				}

				.hod-hero-mini-value {
					font-size: 30px;
					font-weight: 700;
				}

				.hod-filter-card {
					display: grid;
					grid-template-columns: repeat(4, minmax(0, 1fr));
					gap: 16px;
					padding: 18px;
					border-radius: 28px;
					background: #fff;
					border: 1px solid #e2e8f0;
					box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
					margin-bottom: 20px;
				}

				.hod-filter-field .frappe-control,
				.hod-filter-field .form-group {
					margin-bottom: 0 !important;
				}

				.hod-filter-field .control-label {
					font-size: 13px;
					font-weight: 700;
					color: #475569;
					margin-bottom: 6px;
				}

				.hod-filter-field .control-input,
				.hod-filter-field input,
				.hod-filter-field select,
				.hod-filter-field .awesomplete input {
					border-radius: 16px !important;
					min-height: 42px;
					background: #f8fafc !important;
					border-color: #e2e8f0 !important;
				}

				.hod-filter-action {
					display: flex;
					align-items: flex-end;
				}

				.hod-filter-action .btn {
					width: 100%;
					min-height: 42px;
					border-radius: 16px;
					font-weight: 600;
				}

				.hod-stat-grid {
					display: grid;
					grid-template-columns: repeat(4, minmax(0, 1fr));
					gap: 16px;
					margin-bottom: 22px;
				}

				.hod-stat-card {
					padding: 20px;
					border-radius: 24px;
					background: #fff;
					border: 1px solid #e2e8f0;
					box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
				}

				.hod-stat-clickable {
					cursor: pointer;
					transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
				}

				.hod-stat-clickable:hover,
				.hod-stat-clickable:focus {
					transform: translateY(-1px);
					border-color: #cbd5e1;
					background: #f8fafc;
					outline: none;
				}

				.hod-stat-label {
					font-size: 13px;
					font-weight: 600;
					color: #64748b;
					margin-bottom: 10px;
				}

				.hod-stat-row {
					display: flex;
					justify-content: space-between;
					align-items: flex-end;
					gap: 10px;
				}

				.hod-stat-value {
					font-size: 38px;
					line-height: 1;
					font-weight: 700;
					color: #0f172a;
				}

				.hod-stat-note {
					font-size: 12px;
					font-weight: 600;
					padding: 6px 10px;
					border-radius: 999px;
					background: #f1f5f9;
					color: #475569;
					white-space: nowrap;
				}

				.hod-pending .hod-stat-value,
				.hod-warning .hod-stat-value {
					color: #b45309;
				}

				.hod-done .hod-stat-value {
					color: #047857;
				}

				.hod-main-grid {
					display: grid;
					grid-template-columns: 320px minmax(0, 1fr);
					gap: 22px;
				}

				.hod-sidebar-card,
				.hod-detail-card,
				.hod-insight-card,
				.hod-panel-card {
					background: #fff;
					border: 1px solid #e2e8f0;
					box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
				}

				.hod-sidebar-card {
					border-radius: 28px;
					padding: 20px;
					height: fit-content;
				}

				.hod-panel-card {
					border-radius: 28px;
					padding: 20px;
					margin-bottom: 4px;
				}

				.hod-panel-head {
					display: flex;
					align-items: center;
					justify-content: space-between;
					gap: 12px;
					margin-bottom: 16px;
				}

				.hod-panel-title {
					font-size: 20px;
					font-weight: 700;
					color: #0f172a;
				}

				.hod-panel-close {
					width: 34px;
					height: 34px;
					border: none;
					border-radius: 999px;
					background: #e2e8f0;
					color: #0f172a;
					font-size: 22px;
					line-height: 1;
					font-weight: 700;
					cursor: pointer;
					display: inline-flex;
					align-items: center;
					justify-content: center;
					transition: background 0.18s ease, transform 0.18s ease;
				}

				.hod-panel-close:hover {
					background: #cbd5e1;
					transform: scale(1.04);
				}

				.hod-panel-list {
					display: grid;
					gap: 14px;
				}

				.hod-panel-item {
					padding: 16px;
					border: 1px solid #e2e8f0;
					border-radius: 18px;
					background: #f8fafc;
				}

				.hod-panel-item-department-group {
					border-left: 4px solid #f59e0b;
					background: linear-gradient(180deg, #fffaf0 0%, #f8fafc 100%);
				}

				.hod-panel-item-head {
					display: flex;
					justify-content: space-between;
					align-items: flex-start;
					gap: 12px;
					margin-bottom: 10px;
				}

				.hod-panel-item-title {
					font-size: 15px;
					font-weight: 700;
					color: #0f172a;
				}

				.hod-panel-item-group-label {
					font-size: 11px;
					font-weight: 800;
					text-transform: uppercase;
					letter-spacing: 0.08em;
					color: #b45309;
					margin-bottom: 6px;
				}

				.hod-panel-item-title-missing {
					color: #dc2626;
				}

				.hod-panel-item-draft {
					border-color: #fed7aa;
					background: #fff7ed;
				}

				.hod-panel-item-title-draft {
					color: #c2410c;
				}

				.hod-panel-item-meta {
					font-size: 12px;
					color: #64748b;
					margin-top: 4px;
				}

				.hod-panel-sublist {
					display: grid;
					gap: 10px;
				}

				.hod-panel-subitem {
					padding: 12px 14px;
					border-radius: 14px;
					background: #fff;
					border: 1px solid #e2e8f0;
				}

				.hod-panel-subitem-pending {
					background: #fff8e7;
					border-color: #f6d7a8;
				}

				.hod-panel-subitem-done {
					background: #effcf4;
					border-color: #b7ebc6;
				}

				.hod-panel-subitem-area {
					font-size: 12px;
					font-weight: 800;
					text-transform: uppercase;
					letter-spacing: 0.08em;
					color: #64748b;
					margin-bottom: 6px;
				}

				.hod-panel-subitem-text {
					font-size: 14px;
					line-height: 1.6;
					color: #0f172a;
					white-space: pre-wrap;
				}

				.hod-panel-subitem-note {
					margin-top: 8px;
					font-size: 13px;
					line-height: 1.6;
					color: #475569;
				}

				.hod-sidebar-head {
					display: flex;
					justify-content: space-between;
					align-items: center;
					gap: 10px;
					margin-bottom: 16px;
				}

				.hod-sidebar-head h3 {
					margin: 0;
					font-size: 18px;
					font-weight: 700;
					color: #0f172a;
				}

				.hod-sidebar-total {
					padding: 6px 10px;
					border-radius: 999px;
					background: #f1f5f9;
					color: #475569;
					font-size: 12px;
					font-weight: 600;
				}

				.hod-sidebar-list {
					display: grid;
					gap: 12px;
				}

				.hod-sidebar-item {
					width: 100%;
					padding: 16px;
					border: 1px solid #e2e8f0;
					border-radius: 20px;
					background: #fff;
					text-align: left;
					transition: all 0.18s ease;
				}

				.hod-sidebar-item:hover,
				.hod-sidebar-item.is-active {
					background: #f8fafc;
					border-color: #cbd5e1;
				}

				.hod-sidebar-item-top {
					display: flex;
					justify-content: space-between;
					align-items: flex-start;
					gap: 12px;
				}

				.hod-sidebar-name {
					font-size: 15px;
					font-weight: 700;
					color: #0f172a;
					margin-bottom: 8px;
				}

				.hod-sidebar-short {
					font-size: 12px;
					color: #64748b;
					margin-top: 4px;
				}

				.hod-sidebar-meta-row {
					display: flex;
					gap: 8px;
					flex-wrap: wrap;
				}

				.hod-sidebar-badges,
				.hod-detail-badges {
					display: flex;
					gap: 8px;
					flex-wrap: wrap;
				}

				.hod-badge {
					padding: 7px 12px;
					border-radius: 999px;
					font-size: 12px;
					font-weight: 700;
				}

				.hod-badge-pending,
				.hod-column-chip.is-pending {
					background: #fef3c7;
					color: #92400e;
				}

				.hod-badge-done,
				.hod-column-chip.is-done {
					background: #d1fae5;
					color: #065f46;
				}

				.hod-content-area {
					display: grid;
					gap: 20px;
				}

				.hod-detail-card {
					border-radius: 28px;
					padding: 24px;
				}

				.hod-detail-head {
					display: flex;
					justify-content: space-between;
					align-items: flex-start;
					gap: 16px;
					margin-bottom: 20px;
				}

				.hod-detail-chip {
					display: inline-flex;
					padding: 7px 12px;
					border-radius: 999px;
					background: #fef3c7;
					color: #92400e;
					font-size: 12px;
					font-weight: 700;
					margin-bottom: 10px;
				}

				.hod-detail-link-wrap {
					margin-bottom: 10px;
				}

				.hod-detail-link {
					font-size: 13px;
					font-weight: 700;
					color: #2563eb;
					text-decoration: none;
				}

				.hod-detail-head h3 {
					margin: 0;
					font-size: 34px;
					line-height: 1.1;
					font-weight: 700;
					color: #0f172a;
				}

				.hod-detail-head p {
					margin: 8px 0 0;
					color: #475569;
					font-size: 15px;
				}

				.hod-task-grid {
					display: grid;
					grid-template-columns: repeat(2, minmax(0, 1fr));
					gap: 18px;
				}

				.hod-task-column {
					padding: 18px;
					border-radius: 24px;
				}

				.hod-task-column-pending {
					background: #fff8e7;
				}

				.hod-task-column-done {
					background: #effcf4;
				}

				.hod-task-column-head {
					display: flex;
					justify-content: space-between;
					align-items: center;
					gap: 10px;
					margin-bottom: 14px;
				}

				.hod-task-column-head h4 {
					margin: 0;
					font-size: 20px;
					font-weight: 700;
					color: #0f172a;
				}

				.hod-column-chip {
					padding: 6px 10px;
					border-radius: 999px;
					font-size: 12px;
					font-weight: 700;
				}

				.hod-task-column-body {
					display: grid;
					gap: 14px;
				}

				.hod-task-card {
					padding: 16px;
					border-radius: 20px;
					background: rgba(255, 255, 255, 0.92);
					border: 1px solid rgba(226, 232, 240, 0.9);
				}

				.hod-task-area {
					font-size: 12px;
					font-weight: 800;
					text-transform: uppercase;
					letter-spacing: 0.08em;
					color: #64748b;
					margin-bottom: 8px;
				}

				.hod-task-text {
					font-size: 15px;
					line-height: 1.6;
					color: #0f172a;
					white-space: pre-wrap;
				}

				.hod-task-subline {
					margin-top: 8px;
					font-size: 13px;
					line-height: 1.6;
					color: #475569;
					white-space: pre-wrap;
				}

				.hod-task-remark {
					margin-top: 10px;
					display: inline-block;
					padding: 8px 12px;
					border-radius: 12px;
					background: #334155;
					color: #fff;
					font-size: 13px;
					line-height: 1.6;
				}

				.hod-task-remark strong {
					color: #fff;
				}

				.hod-task-remark-wrap {
					margin-top: 10px;
					display: flex;
					align-items: center;
					gap: 10px;
					flex-wrap: wrap;
				}

				.hod-task-remark-wrap .hod-task-remark {
					margin-top: 0;
				}

				.hod-add-task-btn {
					border-radius: 999px;
					padding: 6px 12px;
					font-weight: 700;
					border-color: #cbd5e1;
					background: #fff;
					color: #0f172a;
				}

				.hod-add-task-btn:hover,
				.hod-add-task-btn:focus {
					background: #f8fafc;
					border-color: #94a3b8;
					color: #0f172a;
				}

				.hod-task-status-badge {
					display: inline-flex;
					align-items: center;
					padding: 6px 12px;
					border-radius: 999px;
					font-size: 12px;
					font-weight: 800;
					letter-spacing: 0.04em;
				}

				.hod-task-status-badge.is-open {
					background: #2563eb;
					color: #fff;
				}

				.hod-task-status-badge.is-completed {
					background: #16a34a;
					color: #fff;
				}

				.hod-task-status-badge.is-cancelled {
					background: #dc2626;
					color: #fff;
				}

				.hod-task-status-badge.is-neutral {
					background: #64748b;
					color: #fff;
				}

				.hod-task-empty-card,
				.hod-empty-card {
					padding: 24px;
					border-radius: 20px;
					background: rgba(255, 255, 255, 0.9);
					border: 1px dashed #cbd5e1;
					color: #64748b;
				}

				.hod-task-empty-title {
					font-size: 18px;
					font-weight: 700;
					color: #0f172a;
					margin-bottom: 8px;
				}

				.hod-task-empty-text {
					font-size: 14px;
					line-height: 1.6;
				}

				.hod-insight-grid {
					display: grid;
					grid-template-columns: repeat(3, minmax(0, 1fr));
					gap: 16px;
					align-items: start;
				}

				.hod-insight-card {
					padding: 20px;
					border-radius: 24px;
					min-height: 0;
					height: auto;
					display: flex;
					flex-direction: column;
					justify-content: flex-start;
					align-self: start;
				}

				.hod-insight-label {
					font-size: 13px;
					font-weight: 600;
					color: #64748b;
					margin-bottom: 10px;
				}

				.hod-insight-value {
					font-size: 24px;
					font-weight: 700;
					color: #0f172a;
					line-height: 1.25;
					display: -webkit-box;
					-webkit-line-clamp: 2;
					-webkit-box-orient: vertical;
					overflow: hidden;
				}

				.hod-insight-text {
					margin-top: 8px;
					font-size: 14px;
					line-height: 1.6;
					color: #475569;
					display: -webkit-box;
					-webkit-line-clamp: 3;
					-webkit-box-orient: vertical;
					overflow: hidden;
				}

				@media (max-width: 1200px) {
					.hod-main-grid,
					.hod-hero-card {
						grid-template-columns: 1fr;
					}

					.hod-stat-grid,
					.hod-insight-grid {
						grid-template-columns: repeat(2, minmax(0, 1fr));
					}
				}

				@media (max-width: 900px) {
					.hod-filter-card,
					.hod-task-grid,
					.hod-stat-grid,
					.hod-insight-grid,
					.hod-hero-metrics {
						grid-template-columns: 1fr;
					}

					.hod-topbar,
					.hod-detail-head,
					.hod-sidebar-item-top,
					.hod-task-column-head,
					.hod-panel-head {
						flex-direction: column;
						align-items: flex-start;
					}

					.hod-detail-head h3,
					.hod-hero-copy h2,
					.hod-title {
						font-size: 28px;
					}
				}
			</style>`
		).appendTo("head");
	}
}


frappe.pages["department-audit-ove"].on_page_load = function (wrapper) {
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
			<div class="ceo-audit-page">
				<div class="ceo-audit-hero">
					<div>
						<div class="ceo-audit">Executive Daily Checklist View</div>
						<h2>Department Performance at a Glance</h2>
						<p>Reveiw Daily, Weekly and Monthly Completed and Pending Tasks Across all Departments.</p>
					</div>
				</div>
				<div class="ceo-filter-bar">
					<div class="ceo-filter-field ceo-filter-date"></div>
					<div class="ceo-filter-field ceo-filter-frequency"></div>
					<div class="ceo-filter-field ceo-filter-department"></div>
				</div>
				<div class="ceo-audit-summary"></div>
				<div class="ceo-audit-departments"></div>
			</div>
		`);

		this.date_field = frappe.ui.form.make_control({
			parent: this.page.main.find(".ceo-filter-date"),
			df: {
				fieldtype: "Date",
				fieldname: "audit_date",
				label: "Date",
				default: frappe.datetime.get_today(),
				change: () => this.load_data(),
			},
			render_input: true,
		});

		this.frequency_field = frappe.ui.form.make_control({
			parent: this.page.main.find(".ceo-filter-frequency"),
			df: {
				fieldtype: "Select",
				fieldname: "frequency",
				label: "Frequency",
				options: "Daily\nWeakly\nMonthly",
				default: "Daily",
				change: () => this.load_data(),
			},
			render_input: true,
		});

		this.department_field = frappe.ui.form.make_control({
			parent: this.page.main.find(".ceo-filter-department"),
			df: {
				fieldtype: "Link",
				fieldname: "department",
				label: "Department",
				options: "Designation",
				change: () => this.load_data(),
			},
			render_input: true,
		});
		this.checklist_departments = [];
		this.department_field.get_query = () => ({
			filters: {
				name: ["in", this.checklist_departments.length ? this.checklist_departments : [""]],
			},
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
			},
		});

		this.page.set_primary_action("Refresh", () => this.load_data(), "refresh");
		this.load_data();
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
		this.render_summary(data.summary || {});
		this.render_departments(data.departments || []);
	}

	render_summary(summary) {
		const cards = [
			{ label: "Departments", value: summary.departments || 0, tone: "neutral" },
			{ label: "Pending Tasks", value: summary.pending || 0, tone: "pending" },
			{ label: "Done Tasks", value: summary.done || 0, tone: "done" },
		];

		const html = cards
			.map(
				(card) => `
				<div class="ceo-summary-card ceo-${card.tone}">
					<div class="ceo-summary-label">${frappe.utils.escape_html(card.label)}</div>
					<div class="ceo-summary-value">${card.value}</div>
				</div>
			`
			)
			.join("");

		this.page.main.find(".ceo-audit-summary").html(html);
	}

	render_departments(departments) {
		if (!departments.length) {
			this.page.main.find(".ceo-audit-departments").html(`
				<div class="ceo-empty-state">
					No department audits were found for the selected date and frequency.
				</div>
			`);
			return;
		}

		const html = departments
			.map((department) => {
				return `
					<div class="ceo-department-card">
						<div class="ceo-department-header">
							<div>
								<h3>${frappe.utils.escape_html(department.department || "Department")}</h3>
								<div class="ceo-department-meta">
									${department.audit_name
										? `<a href="/app/department-audit/${encodeURIComponent(department.audit_name)}" target="_blank">
											${frappe.utils.escape_html(department.audit_name || "")}
										</a>`
										: `<span class="ceo-missing-audit">Audit not entered. Checklist shown as pending.</span>`}
								</div>
							</div>
							<div class="ceo-count-pills">
								<span class="ceo-pill ceo-pill-pending">Pending ${department.counts.pending || 0}</span>
								<span class="ceo-pill ceo-pill-done">Done ${department.counts.done || 0}</span>
							</div>
						</div>
						<div class="ceo-columns">
							${this.render_task_block("Pending", department.pending_tasks, "pending")}
							${this.render_task_block("Done", department.done_tasks, "done")}
						</div>
					</div>
				`;
			})
			.join("");

		this.page.main.find(".ceo-audit-departments").html(html);
	}

	render_task_block(title, tasks, tone) {
		const body = tasks.length
			? tasks
					.map(
						(task) => `
						<div class="ceo-task-row">
							<div class="ceo-task-area">${frappe.utils.escape_html(task.area || "General")}</div>
							<div class="ceo-task-text">${frappe.utils.escape_html(task.task || "")}</div>
							${task.follow_up ? `<div class="ceo-task-followup">${frappe.utils.escape_html(task.follow_up)}</div>` : ""}
							${task.remarks ? `<div class="ceo-task-remark"><strong>Remarks:</strong> ${frappe.utils.escape_html(task.remarks)}</div>` : ""}
						</div>
					`
					)
					.join("")
			: `<div class="ceo-task-empty">No ${title.toLowerCase()} tasks.</div>`;

		return `
			<div class="ceo-column ceo-column-${tone}">
				<div class="ceo-column-title">${title}</div>
				<div class="ceo-column-body">${body}</div>
			</div>
		`;
	}

	inject_style() {
		if ($("#ceo-department-audit-style").length) {
			return;
		}

		$(`<style id="ceo-department-audit-style">
			
			.department-audit-overview-page .page-head .title-text,
			.department-audit-overview-page .page-title .title-text {
				font-size: 2.0rem;
				font-weight: 600;
				line-height: 1.4;
				background: #f0f0f0;
				padding: 12px 12px;
				border-radius: 10px;
				max-width: 100%;
				border-radius: 12px;
			}

			.ceo-audit-page {
				padding: 18px 6px 30px;
				background: linear-gradient(180deg, #f8fafc 0%, #eef4f7 100%);
				min-height: calc(100vh - 120px);
			}
			.ceo-audit-hero {
				background: linear-gradient(135deg, #f19f21 0%, #3b4449 100%);
				color: #fff;
				padding: 28px 30px;
				border-radius: 20px;
				box-shadow: 0 18px 40px rgba(16, 58, 77, 0.18);
				margin-bottom: 20px;
			}
			.ceo-audit-eyebrow {
				font-size: 12px;
				letter-spacing: 0.16em;
				text-transform: uppercase;
				opacity: 0.75;
				margin-bottom: 10px;
			}
			.ceo-audit-hero h2 {
				margin: 0 0 8px;
				font-size: 30px;
				font-weight: 700;
			}
			.ceo-audit-hero p {
				margin: 0;
				max-width: 760px;
				font-size: 15px;
				opacity: 0.9;
			}
			.ceo-audit-summary {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
				gap: 14px;
				margin-bottom: 18px;
			}
			.ceo-filter-bar {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
				gap: 14px;
				margin-bottom: 18px;
				padding: 16px;
				border-radius: 18px;
				background: rgba(255, 255, 255, 0.9);
				border: 1px solid rgba(148, 163, 184, 0.18);
				box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
			}
			.ceo-filter-field .frappe-control {
				margin-bottom: 0;
			}
			.ceo-filter-field .control-label {
				font-size: 13px;
				font-weight: 700;
				color: #334155;
				margin-bottom: 6px;
			}
			.ceo-summary-card {
				padding: 18px 20px;
				border-radius: 18px;
				background: #fff;
				box-shadow: 0 12px 28px rgba(15, 23, 42, 0.07);
				border: 1px solid rgba(148, 163, 184, 0.18);
			}
			.ceo-summary-label {
				font-size: 13px;
				color: #5b6472;
				margin-bottom: 8px;
			}
			.ceo-summary-value {
				font-size: 34px;
				font-weight: 700;
				line-height: 1;
				color: #12212c;
			}
			.ceo-pending .ceo-summary-value {
				color: #b45309;
			}
			.ceo-done .ceo-summary-value {
				color: #047857;
			}
			.ceo-audit-departments {
				display: grid;
				gap: 18px;
			}
			.ceo-department-card {
				background: rgba(255, 255, 255, 0.94);
				border: 1px solid rgba(148, 163, 184, 0.18);
				border-radius: 22px;
				padding: 20px;
				box-shadow: 0 14px 36px rgba(15, 23, 42, 0.07);
			}
			.ceo-department-header {
				display: flex;
				justify-content: space-between;
				align-items: flex-start;
				gap: 16px;
				margin-bottom: 16px;
			}
			.ceo-department-header h3 {
				margin: 0 0 6px;
				font-size: 24px;
				color: #0f172a;
			}
			.ceo-department-meta a {
				color: #1d4ed8;
				font-size: 13px;
				text-decoration: none;
			}
			.ceo-missing-audit {
				display: inline-block;
				font-size: 13px;
				font-weight: 600;
				color: #b45309;
				background: #fff3c4;
				padding: 6px 10px;
				border-radius: 999px;
			}
			.ceo-count-pills {
				display: flex;
				flex-wrap: wrap;
				gap: 8px;
			}
			.ceo-pill {
				padding: 7px 12px;
				border-radius: 999px;
				font-size: 12px;
				font-weight: 600;
			}
			.ceo-pill-pending {
				background: #fff3c4;
				color: #8a5a00;
			}
			.ceo-pill-done {
				background: #d8f7e6;
				color: #0b6b46;
			}
			.ceo-columns {
				display: grid;
				grid-template-columns: repeat(2, minmax(0, 1fr));
				gap: 14px;
			}
			.ceo-column {
				border-radius: 18px;
				padding: 14px;
				min-height: 100%;
			}
			.ceo-column-pending {
				background: #fff9e8;
			}
			.ceo-column-done {
				background: #eefcf5;
			}
			.ceo-column-title {
				font-size: 16px;
				font-weight: 700;
				margin-bottom: 12px;
				color: #17212b;
			}
			.ceo-column-body {
				display: grid;
				gap: 10px;
			}
			.ceo-task-row {
				background: rgba(255, 255, 255, 0.8);
				border-radius: 14px;
				padding: 12px;
				border: 1px solid rgba(255, 255, 255, 0.7);
			}
			.ceo-task-area {
				font-size: 12px;
				font-weight: 700;
				letter-spacing: 0.04em;
				text-transform: uppercase;
				color: #52606d;
				margin-bottom: 5px;
			}
			.ceo-task-text {
				font-size: 15px;
				line-height: 1.5;
				color: #18212b;
				white-space: pre-wrap;
			}
			.ceo-task-followup,
			.ceo-task-remark {
				margin-top: 8px;
				font-size: 13px;
				line-height: 1.5;
				color: #4a5565;
				white-space: pre-wrap;
			}
			

			.ceo-task-remark {
				display: inline-block;
				padding: 8px 12px;
				border-radius: 10px;
				background: #3b4449;
				color: #fff;
			}
			.ceo-task-remark strong {
				color: #fff;




			.ceo-task-empty,
			.ceo-empty-state {
				padding: 20px;
				border-radius: 16px;
				background: rgba(255, 255, 255, 0.9);
				color: #5b6472;
				font-size: 15px;
			}
			@media (max-width: 1100px) {
				.ceo-columns {
					grid-template-columns: 1fr;
				}
			}
		</style>`).appendTo("head");
	}
}

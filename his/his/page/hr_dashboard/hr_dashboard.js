frappe.pages["hr-dashboard"].on_page_load = function(wrapper) {
	wrapper.hr_dashboard = new FrappeDashHR(wrapper);
};

frappe.pages["hr-dashboard"].on_page_show = function(wrapper) {
	if (wrapper.hr_dashboard) {
		wrapper.hr_dashboard.enter_fullscreen();
	}
};

frappe.pages["hr-dashboard"].on_page_hide = function(wrapper) {
	if (wrapper.hr_dashboard) {
		wrapper.hr_dashboard.exit_fullscreen();
	}
};

class FrappeDashHR {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("HRM and Payroll"),
			single_column: true,
		});

		this.make();
		this.setup_filters();
		this.page.set_primary_action(__("Refresh"), () => this.refresh(), "refresh");
		this.refresh();
	}

	make() {
		$(frappe.render_template("hr_dashboard", {})).appendTo(this.page.main);
		this.$root = $(this.page.main).find(".fd-hr");
		this.$page_container = $(this.wrapper).closest(".page-container");
		this.enter_fullscreen();
	}

	enter_fullscreen() {
		$("body").addClass("fd-hr-fullscreen");
		this.$page_container.addClass("fd-hr-page");
		this.$page_container.find(".page-body").addClass("full-width");
		this.$page_container.find(".page-head").hide();
	}

	exit_fullscreen() {
		$("body").removeClass("fd-hr-fullscreen");
		this.$page_container.removeClass("fd-hr-page");
		this.$page_container.find(".page-body").removeClass("full-width");
		this.$page_container.find(".page-head").show();
	}

	setup_filters() {
		const today = frappe.datetime.get_today();
		const yearStart = `${today.slice(0, 4)}-01-01`;

		this.from_date = frappe.ui.form.make_control({
			parent: this.$root.find(".fd-from-date"),
			df: {
				fieldtype: "Date",
				fieldname: "from_date",
				default: yearStart,
				change: () => this.refresh(),
			},
			render_input: true,
		});

		this.to_date = frappe.ui.form.make_control({
			parent: this.$root.find(".fd-to-date"),
			df: {
				fieldtype: "Date",
				fieldname: "to_date",
				default: today,
				change: () => this.refresh(),
			},
			render_input: true,
		});

		this.department = frappe.ui.form.make_control({
			parent: this.$root.find(".fd-department-filter"),
			df: {
				fieldtype: "Link",
				fieldname: "department",
				options: "Department",
				placeholder: __("Department"),
				change: () => this.refresh(),
			},
			render_input: true,
		});

		this.from_date.set_value(yearStart);
		this.to_date.set_value(today);
	}

	refresh() {
		this.set_loading();

		frappe.call({
			method: "his.api.hr_dashboard.get_dashboard_data",
			args: {
				from_date: this.from_date.get_value(),
				to_date: this.to_date.get_value(),
				department: this.department.get_value(),
			},
			callback: (response) => {
				this.data = response.message || {};
				this.render();
			},
			error: () => this.render_error(),
		});
	}

	set_loading() {
		const loading = this.empty(__("Loading HR dashboard"));
		this.$root.find(".fd-hr-kpis").html(loading);
		this.$root.find(".fd-department-bars, .fd-hr-chart, .fd-table-wrap").html(loading);
	}

	render() {
		this.render_cards();
		this.render_department_bars();
		this.render_salary_trend();
		this.render_employee_exit_trend();
		this.render_expense_table();
		this.render_advances();
		this.render_leaves();
	}

	render_cards() {
		const cards = this.data.cards || [];
		const html = cards.map((card) => `
			<div class="fd-hr-kpi">
				<div class="fd-hr-kpi-value">${this.format(card.value, card.format)}</div>
				<div class="fd-hr-kpi-label">${this.escape(__(card.label))}</div>
			</div>
		`).join("");

		this.$root.find(".fd-hr-kpis").html(html || this.empty(__("No employee data found")));
	}

	render_department_bars() {
		const rows = this.data.employees_by_department || [];
		const max = Math.max(...rows.map((row) => row.employees), 1);
		const html = rows.map((row) => {
			const width = Math.max((row.employees / max) * 100, 2);
			return `
				<div class="fd-dept-row" title="${this.escape(row.department)}">
					<div class="fd-dept-name">${this.escape(row.department)}</div>
					<div class="fd-dept-bar-track">
						<div class="fd-dept-bar" style="width: ${width}%"></div>
						<div class="fd-dept-value">${row.employees} (${this.money(row.salary, 0)})</div>
					</div>
				</div>
			`;
		}).join("");

		this.$root.find(".fd-department-bars").html(html || this.empty(__("No department data found")));
	}

	render_salary_trend() {
		this.render_step_trend(this.data.salary_trend || [], "#fd-hr-salary-chart", __("Salary Trend"));
		this.render_step_trend(
			this.data.commission_trend || [],
			"#fd-hr-commission-chart",
			__("Commission Trend")
		);
	}

	render_employee_exit_trend() {
		this.render_step_trend(
			this.data.employee_exit_trend || [],
			"#fd-employee-exit-chart",
			__("Employee Exit Trend"),
			{
				value_key: "value",
				previous_key: "previous_value",
				format_value: (value) => frappe.format(value || 0, { fieldtype: "Int" }),
				show_change: false,
			}
		);
	}

	render_step_trend(rows, selector, title, options = {}) {
		const target = this.$root.find(selector).empty()[0];

		if (!rows.length) {
			$(target).html(this.empty(__("No trend found")));
			return;
		}

		const width = 684;
		const height = 201;
		const left = 62;
		const right = 34;
		const top = 38;
		const bottom = 24;
		const plot_width = width - left - right;
		const baseline = height - bottom;
		const value_key = options.value_key || "salary";
		const previous_key = options.previous_key || "previous_salary";
		const format_value = options.format_value || ((value) => this.money(value, 0));
		const values = rows.map((row) => Number(row[value_key] || 0));
		const max = Math.max(...values, 1);
		const min = Math.min(...values, 0);
		const range = Math.max(max - min, 1);
		const x_step = rows.length > 1 ? plot_width / (rows.length - 1) : 0;
		const points = rows.map((row, index) => {
			const value = Number(row[value_key] || 0);
			const previous = row[previous_key] != null
				? Number(row[previous_key] || 0)
				: Number((rows[index - 1] || {})[value_key] || 0);
			return {
				label: row.label,
				value,
				previous,
				x: left + x_step * index,
				y: top + ((max - value) / range) * (baseline - top),
			};
		});
		const line_path = this.step_path(points);
		const area_path = `${line_path} L ${points[points.length - 1].x} ${baseline} L ${points[0].x} ${baseline} Z`;
		const labels = points.map((point) => this.salary_trend_label(
			point,
			width,
			format_value,
			options.show_change !== false
		)).join("");
		const months = points.map((point) => `
			<div class="fd-step-month" style="left: ${(point.x / width) * 100}%">${this.escape(point.label)}</div>
		`).join("");

		$(target).html(`
			<div class="fd-step-chart">
				<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-label="${this.escape(title)}">
					<path class="fd-step-fill" d="${area_path}"></path>
					<path class="fd-step-line" d="${line_path}"></path>
					${points.map((point) => `<circle class="fd-step-dot" cx="${point.x}" cy="${point.y}" r="3"></circle>`).join("")}
				</svg>
				<div class="fd-step-labels">${labels}</div>
				<div class="fd-step-months">${months}</div>
			</div>
		`);
	}

	step_path(points) {
		if (!points.length) {
			return "";
		}

		let path = `M ${points[0].x} ${points[0].y}`;
		for (let index = 1; index < points.length; index++) {
			const previous = points[index - 1];
			const current = points[index];
			const midpoint = previous.x + (current.x - previous.x) / 2;
			path += ` H ${midpoint} V ${current.y} H ${current.x}`;
		}
		return path;
	}

	salary_trend_label(point, chart_width, format_value, show_change = true) {
		const change = show_change && point.previous ? ((point.value - point.previous) / point.previous) * 100 : null;
		const change_html = change == null ? "" : `
			<div class="fd-step-change ${change >= 0 ? "positive" : "negative"}">
				<span class="fd-step-caret"></span>${change >= 0 ? "+" : ""}${this.number(change, 1)}%
			</div>
		`;

		return `
			<div class="fd-step-value-label" style="left: ${(point.x / chart_width) * 100}%; top: ${Math.max(point.y - 31, 6)}px">
				<div class="fd-step-total">${format_value(point.value)}</div>
				${change_html}
			</div>
		`;
	}

	render_expense_table() {
		const rows = this.data.department_expense || [];
		const components = this.data.component_columns || [];
		const headers = [
			__("Department"),
			__("Employee"),
			__("Salary"),
			...components.map((component) => __(component)),
			__("Total"),
		];

		const body = rows.map((row) => `
			<tr>
				<td>${this.escape(row.department)}</td>
				<td class="fd-num">${row.employees || 0}</td>
				<td class="fd-num">${this.money(row.salary)}</td>
				${components.map((component) => `<td class="fd-num">${this.money(row.components[component] || 0)}</td>`).join("")}
				<td class="fd-num">${this.money(row.total)}</td>
			</tr>
		`).join("");

		const totals = {
			employees: rows.reduce((sum, row) => sum + (row.employees || 0), 0),
			salary: rows.reduce((sum, row) => sum + (row.salary || 0), 0),
			total: rows.reduce((sum, row) => sum + (row.total || 0), 0),
		};

		const footer = rows.length ? `
			<tfoot>
				<tr>
					<td>${__("Total")}</td>
					<td class="fd-num">${totals.employees}</td>
					<td class="fd-num">${this.money(totals.salary)}</td>
					${components.map((component) => {
						const value = rows.reduce((sum, row) => sum + (row.components[component] || 0), 0);
						return `<td class="fd-num">${this.money(value)}</td>`;
					}).join("")}
					<td class="fd-num">${this.money(totals.total)}</td>
				</tr>
			</tfoot>
		` : "";

		this.$root.find(".fd-expense-table").html(
			rows.length ? this.table(headers, body, footer) : this.empty(__("No salary expense found"))
		);
	}

	render_advances() {
		const advances = this.data.advances || {};
		const rows = advances.rows || [];
		const body = rows.map((row) => `
			<tr>
				<td>${this.escape(row.employee_name)}</td>
				<td class="fd-num">${this.money(row.advance)}</td>
				<td class="fd-num">${this.money(row.receivable)}</td>
			</tr>
		`).join("");
		const footer = rows.length ? `
			<tfoot>
				<tr>
					<td>${__("Total")}</td>
					<td class="fd-num">${this.money(advances.total_advance || 0)}</td>
					<td class="fd-num">${this.money(advances.total_receivable || 0)}</td>
				</tr>
			</tfoot>
		` : "";

		this.$root.find(".fd-advance-table").html(
			rows.length
				? this.table([__("Employee Name"), __("Advance"), __("Receivable")], body, footer)
				: this.empty(__("No employee advances found"))
		);
	}

	render_leaves() {
		const leaves = this.data.leaves || {};
		const rows = leaves.rows || [];
		const totals = leaves.totals || {};
		const body = rows.map((row) => `
			<tr>
				<td>${this.escape(row.leave_type)}</td>
				<td class="fd-num">${row.active || 0}</td>
				<td class="fd-num">${row.pending || 0}</td>
				<td class="fd-num">${row.ending_today || 0}</td>
			</tr>
		`).join("");
		const footer = rows.length ? `
			<tfoot>
				<tr>
					<td>${__("Total")}</td>
					<td class="fd-num">${totals.active || 0}</td>
					<td class="fd-num">${totals.pending || 0}</td>
					<td class="fd-num">${totals.ending_today || 0}</td>
				</tr>
			</tfoot>
		` : "";

		this.$root.find(".fd-leave-table").html(
			rows.length
				? this.table([__("Leave Type"), __("Active Leaves"), __("Pending Leaves"), __("Ending Today")], body, footer)
				: this.empty(__("No leave data found"))
		);
	}

	render_error() {
		const message = this.empty(__("Unable to load HR dashboard"));
		this.$root.find(".fd-hr-kpis, .fd-department-bars, .fd-hr-chart, .fd-table-wrap").html(message);
	}

	table(headers, body, footer) {
		return `
			<table class="fd-hr-table">
				<thead>
					<tr>${headers.map((header) => `<th>${this.escape(header)}</th>`).join("")}</tr>
				</thead>
				<tbody>${body}</tbody>
				${footer || ""}
			</table>
		`;
	}

	format(value, format) {
		if (format === "percent") {
			return `${this.number(value || 0, 2)}%`;
		}
		if (format === "currency_compact") {
			return this.compact_money(value || 0);
		}
		if (format === "currency") {
			return this.money(value || 0, 0);
		}
		return frappe.format(value || 0, { fieldtype: "Int" });
	}

	money(value, decimals = 2) {
		const currency = frappe.defaults.get_default("currency") || "$";
		const number = this.number(value || 0, decimals);

		if (currency.length <= 3 && !currency.includes(" ")) {
			return `${currency === "USD" ? "$" : currency} ${number}`.replace("$ ", "$");
		}

		return `$${number}`;
	}

	compact_money(value) {
		const amount = Number(value || 0);
		if (Math.abs(amount) >= 1000000) {
			return `${this.money(amount / 1000000, 1)}M`;
		}
		if (Math.abs(amount) >= 1000) {
			return `${this.money(amount / 1000, 0)}K`;
		}
		return this.money(amount, 0);
	}

	number(value, decimals = 2) {
		return Number(value || 0).toLocaleString(undefined, {
			minimumFractionDigits: decimals,
			maximumFractionDigits: decimals,
		});
	}

	escape(value) {
		return frappe.utils.escape_html(value == null ? "" : value);
	}

	empty(message) {
		return `<div class="fd-empty-state">${this.escape(message)}</div>`;
	}
}

frappe.pages['monthly_budget_plan'].on_page_load = function(wrapper) {
	new MonthlyBudgetPlanPage(wrapper);
};

class MonthlyBudgetPlanPage {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Monthly Budget Plan',
			single_column: true
		});
		this.report_month = this.get_initial_report_month();
		this.setup();
	}

	get_initial_report_month() {
		const route_options = frappe.route_options || {};
		const selected_date = route_options.report_month || route_options.from_date;
		frappe.route_options = null;
		if (!selected_date) {
			return frappe.datetime.month_start();
		}

		const normalized_date = selected_date.length === 7 ? `${selected_date}-01` : selected_date;
		const date = frappe.datetime.str_to_obj(normalized_date);
		if (!date || Number.isNaN(date.getTime())) {
			return frappe.datetime.month_start();
		}

		return frappe.datetime.obj_to_str(new Date(date.getFullYear(), date.getMonth(), 1));
	}

	setup() {
		$(this.wrapper).addClass('monthly-budget-plan-page');
		this.page.wrapper.find('.page-head').hide();
		this.page.main.addClass('monthly-budget-plan-main');
		this.render_loading();
		this.load();
	}

	make_actions() {
		this.page.set_primary_action(__('Refresh'), () => this.load(), 'refresh');
		this.page.set_secondary_action(__('Print'), () => window.print(), 'printer');
	}

	render_loading() {
		this.page.main.html(`
			<div class="mbp-shell">
				<div class="mbp-loading">
					<div class="mbp-loading__spinner"></div>
					<div class="mbp-loading__text">${__('Loading monthly budget plan...')}</div>
				</div>
			</div>
		`);
	}

	load() {
		this.make_actions();
		this.render_loading();
		frappe.call({
			method: 'his.his.page.monthly_budget_plan.monthly_budget_plan.get_budget_plan_data',
			args: {
				report_month: this.report_month
			},
			callback: (r) => {
				const data = r.message || {};
				data.has_data = Boolean((data.sections || []).length);
				data.report_month = this.report_month;
				data.month_input_value = data.month_input_value || (this.report_month || '').slice(0, 7);
				this.page.main.html(frappe.render_template('monthly_budget_plan', data));
				this.bind_actions();
			}
		});
	}

	bind_actions() {
		const $main = this.page.main;
		$main.find('[data-budget-action="prev-month"]').on('click', () => {
			this.report_month = this.shift_month(this.report_month, -1);
			this.load();
		});
		$main.find('[data-budget-action="next-month"]').on('click', () => {
			this.report_month = this.shift_month(this.report_month, 1);
			this.load();
		});
		$main.find('[data-budget-action="pick-month"]').on('click', () => {
			const input = $main.find('.mbp-month-input').get(0);
			if (!input) {
				return;
			}
			if (typeof input.showPicker === 'function') {
				input.showPicker();
			} else {
				input.focus();
				input.click();
			}
		});
		$main.find('.mbp-month-input').on('change', (event) => {
			const value = event.currentTarget.value;
			if (!value) {
				return;
			}
			this.report_month = `${value}-01`;
			this.load();
		});
	}

	shift_month(date_string, delta) {
		const date = frappe.datetime.str_to_obj(date_string || frappe.datetime.month_start());
		return frappe.datetime.obj_to_str(new Date(date.getFullYear(), date.getMonth() + delta, 1));
	}
}

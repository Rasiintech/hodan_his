frappe.pages['sales-dashboard'].on_page_load = function(wrapper) {
	new sales_dashboard(wrapper);
};

sales_dashboard = Class.extend({
	init: function(wrapper) {
		this.wrapper = wrapper;
		this.from_date = null;
		this.to_date = null;
		this.aiInsightRequestId = 0;
		this.themeStorageKey = 'sales_dashboard_theme';
		this.currentTheme = this.get_saved_theme();
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Sales Dashboard',
			single_column: true
		});
		this.$page_container = $(wrapper).closest('.page-container');
		this.$page_container.addClass('accounts-dashboard-page');
		$(wrapper).addClass('accounts-dashboard-wrapper');
		this.apply_theme_to_shell();
		this.make();
	},

	make: function() {
		this.load_dashboard();
	},

	load_dashboard: function() {
		this.page.main.addClass('accounts-dashboard-main');
		this.page.main.closest('.layout-main-section').addClass('accounts-dashboard-layout');
		this.$page_container.find('.page-body').addClass('full-width');
		this.page.wrapper.find('.page-head').hide();

		const has_dashboard = this.page.main.find('.accounts-dashboard').length > 0;
		if (!has_dashboard) {
			this.render_dashboard(this.get_loading_context(), false);
			this.show_dashboard_loading();
		} else {
			this.show_dashboard_loading();
		}

		frappe.call({
			method: 'his.his.page.sales_dashboard.sales_dashboard.get_dashboard_data',
			args: {
				from_date: this.from_date,
				to_date: this.to_date
			},
			callback: (r) => {
				const data = this.prepare_dashboard_data(r.message || {});
				this.from_date = data.from_date || this.from_date;
				this.to_date = data.to_date || this.to_date;
				this.render_dashboard(data, true);
				this.bind_actions();
				this.load_ai_insights(data);
			}
		});
	},

	render_dashboard: function(data, preserve_sidebar) {
		const $dashboard = $(frappe.render_template('sales_dashboard', data));
		if (preserve_sidebar) {
			this.page.main.find('.accounts-content').replaceWith($dashboard.find('.accounts-content'));
			return;
		}
		this.page.main.empty().append($dashboard);
	},

	show_dashboard_loading: function() {
		const $content = this.page.main.find('.accounts-content');
		$content.find('.accounts-date-popover').remove();
		$content.find('.accounts-theme-popover').remove();
		$(document).off('click.finance-date-filter');
		$(document).off('click.finance-theme-picker');
		$content.addClass('is-loading');
		$content.find('.theme-button, .date-button, .filter-button, .refresh-button, .export-button').prop('disabled', true);
	},

	get_loading_context: function() {
		const range = this.get_month_range(0);
		return {
			from_date: this.from_date || range.from_date,
			to_date: this.to_date || range.to_date,
			date_range: 'Loading...',
			comparison_range: 'previous period',
			metrics: [],
			income_expenses: [],
			expense_categories: [],
			expense_donut_style: 'background: conic-gradient(#e5e7eb 0 100%);',
			income_sources: [],
			source_donut_style: 'background: conic-gradient(#e5e7eb 0 100%);',
			account_balances: [],
			account_balances_total: '$ 0',
			unpaid_invoices: [],
			unpaid_invoices_total: {
				customer_count: 0,
				outstanding: '$ 0',
				opd_sales: '$ 0',
				ipd_type_values: []
			},
			ipd_type_columns: [],
			performance_views: {
				doctor: { entity_label: 'Doctor', rows: [], total: { outstanding: '$ 0', opd_sales: '$ 0', ipd_type_values: [] }, ipd_type_columns: [], has_more: false },
				department: { entity_label: 'Department', rows: [], total: { outstanding: '$ 0', opd_sales: '$ 0', ipd_type_values: [] }, ipd_type_columns: [], has_more: false }
			},
			item_group_views: {
				summary: { rows: [], total: {}, has_more: false },
				doctor_matrix: { entity_label: 'Doctor', columns: [], rows: [], total: { item_group_values: [], total_amount: '$ 0' }, has_more: false }
			},
			top_supplier_balances: [],
			top_supplier_balances_has_more: false,
			top_supplier_balances_total: '$ 0',
			budget_variance: [],
			budget_variance_total: {
				budget: '$ 0',
				actual: '$ 0',
				variance: '$ 0',
				variance_class: 'neutral',
				indicator_label: 'No Activity',
				indicator_class: 'neutral',
				utilization: '0.0%'
			},
			budget_variance_message: 'Loading item group performance...',
			cash_flow: [],
			insights: [],
			current_theme: this.currentTheme,
			current_theme_label: this.get_theme_label(this.currentTheme)
		};
	},

	prepare_dashboard_data: function(data) {
		const prepared = Object.assign({}, data || {});
		prepared.account_balances = prepared.account_balances || [];
		prepared.unpaid_invoices = prepared.unpaid_invoices || [];
		prepared.ipd_type_columns = prepared.ipd_type_columns || [];
		prepared.performance_views = Object.assign(
			{
				doctor: { entity_label: 'Doctor', rows: [], total: { outstanding: '$ 0', opd_sales: '$ 0', ipd_type_values: [] }, ipd_type_columns: [], has_more: false },
				department: { entity_label: 'Department', rows: [], total: { outstanding: '$ 0', opd_sales: '$ 0', ipd_type_values: [] }, ipd_type_columns: [], has_more: false }
			},
			prepared.performance_views || {}
		);
		prepared.item_group_views = Object.assign(
			{
				summary: { rows: [], total: {}, has_more: false },
				doctor_matrix: { entity_label: 'Doctor', columns: [], rows: [], total: { item_group_values: [], total_amount: '$ 0' }, has_more: false }
			},
			prepared.item_group_views || {}
		);
		prepared.top_supplier_balances = prepared.top_supplier_balances || [];
		prepared.top_supplier_balances_has_more = Boolean(prepared.top_supplier_balances_has_more);
		prepared.account_balances_total = this.format_currency_total(
			prepared.account_balances.reduce((sum, row) => sum + this.to_number(row.raw_balance), 0)
		);
		prepared.unpaid_invoices_total = Object.assign(
			{
				customer_count: 0,
				outstanding: '$ 0',
				opd_sales: '$ 0',
				ipd_type_values: []
			},
			prepared.unpaid_invoices_total || {}
		);
		if (!prepared.unpaid_invoices_total.outstanding || prepared.unpaid_invoices_total.outstanding === '$ 0') {
			prepared.unpaid_invoices_total.outstanding = this.format_currency_total(
				prepared.unpaid_invoices.reduce((sum, row) => sum + this.to_number(row.raw_outstanding || row.raw_net_sales), 0)
			);
		}
		prepared.top_supplier_balances_total = this.format_currency_total(
			prepared.top_supplier_balances.reduce((sum, row) => sum + this.to_number(row.raw_balance), 0)
		);
		prepared.current_theme = this.currentTheme;
		prepared.current_theme_label = this.get_theme_label(this.currentTheme);
		return prepared;
	},

	load_ai_insights: function(data) {
		const requestId = ++this.aiInsightRequestId;
		const $target = this.page.main.find('[data-ai-insight-content="1"]');
		if (!$target.length) {
			return;
		}

		$target.html('<p class="ai-insight-placeholder"><i class="fa fa-spinner fa-spin slate-text"></i>Generating AI sales insight...</p>');

		frappe.call({
			method: 'his.his.page.sales_dashboard.sales_dashboard.get_ai_insights',
			type: 'POST',
			args: {
				from_date: this.from_date,
				to_date: this.to_date,
				dashboard_context: JSON.stringify(this.build_ai_dashboard_context(data))
			},
			callback: (r) => {
				if (requestId !== this.aiInsightRequestId) {
					return;
				}
				const payload = r.message || {};
				this.render_ai_insights(payload.insights || []);
			},
			error: () => {
				if (requestId !== this.aiInsightRequestId) {
					return;
				}
				this.render_ai_insights([
					{
						icon_class: 'fa-info-circle',
						text_class: 'slate-text',
						text: 'Insights are not available right now. Please review the dashboard figures below.'
					}
				]);
			}
		});
	},

	build_ai_dashboard_context: function(data) {
		return {
			metrics: data.metrics || [],
			expense_categories: data.expense_categories || [],
			income_sources: data.income_sources || [],
			account_balances_total: this.format_currency_total(
				(data.account_balances || []).reduce((sum, row) => sum + this.to_number(row.raw_balance), 0)
			),
			unpaid_invoices: data.unpaid_invoices || [],
			unpaid_invoices_total: {
				customer_count: (data.unpaid_invoices || []).reduce((sum, row) => sum + this.to_number(row.raw_customer_count || row.customer_count), 0),
				outstanding: this.format_currency_total(
					(data.unpaid_invoices || []).reduce((sum, row) => sum + this.to_number(row.raw_outstanding), 0)
				)
			},
			top_supplier_balances: data.top_supplier_balances || [],
			top_supplier_balances_total: this.format_currency_total(
				(data.top_supplier_balances || []).reduce((sum, row) => sum + this.to_number(row.raw_balance), 0)
			),
			budget_variance_total: data.budget_variance_total || {}
		};
	},

	render_ai_insights: function(insights) {
		const $target = this.page.main.find('[data-ai-insight-content="1"]');
		if (!$target.length) {
			return;
		}

		try {
			if (!insights.length) {
				$target.html('<p><i class="fa fa-info-circle slate-text"></i>Insights are not available right now. Please review the dashboard figures below.</p>');
				return;
			}

			$target.html(insights.map((insight) => {
				return `<p><i class="fa ${this.escape_attribute(insight.icon_class || 'fa-info-circle')} ${this.escape_attribute(insight.text_class || 'slate-text')}"></i>${this.escape_html(insight.text || '')}</p>`;
			}).join(''));
		} catch (error) {
			$target.html('<p><i class="fa fa-info-circle slate-text"></i>Insights are not available right now. Please review the dashboard figures below.</p>');
		}
	},

	bind_actions: function() {
		this.page.main.find('.theme-button').on('click', (event) => {
			event.stopPropagation();
			this.show_theme_picker();
		});
		this.page.main.find('.date-button').on('click', (event) => {
			event.stopPropagation();
			this.show_date_filter();
		});
		this.page.main.find('.refresh-button').on('click', () => {
			this.load_dashboard();
		});
		this.bind_performance_toggle();
		this.bind_item_group_toggle();
		this.bind_table_expand();
		this.page.main.find('[data-budget-plan-link="1"]').on('click', (event) => {
			event.preventDefault();
			const report_month = this.get_budget_report_month();
			frappe.route_options = {
				report_month: report_month,
				from_date: this.from_date,
				to_date: this.to_date
			};
			frappe.set_route('List', 'Sales Invoice');
		});
	},

	bind_performance_toggle: function() {
		const $main = this.page.main;
		$main.find('[data-performance-toggle]').off('click').on('click', (event) => {
			const view = $(event.currentTarget).data('performance-toggle');
			$main.find('[data-performance-toggle]').removeClass('is-active');
			$main.find(`[data-performance-toggle="${view}"]`).addClass('is-active');
			$main.find('[data-performance-panel]').removeClass('is-active').hide();
			$main.find(`[data-performance-panel="${view}"]`).addClass('is-active').show();
		});
	},

	bind_item_group_toggle: function() {
		const $main = this.page.main;
		$main.find('[data-item-group-toggle]').off('click').on('click', (event) => {
			const view = $(event.currentTarget).data('item-group-toggle');
			$main.find('[data-item-group-toggle]').removeClass('is-active');
			$main.find(`[data-item-group-toggle="${view}"]`).addClass('is-active');
			$main.find('[data-item-group-panel]').removeClass('is-active').hide();
			$main.find(`[data-item-group-panel="${view}"]`).addClass('is-active').show();
		});
	},

	bind_table_expand: function() {
		const $main = this.page.main;
		$main.find('[data-table-expand]').off('click').on('click', (event) => {
			const $button = $(event.currentTarget);
			const $panel = $button.closest('[data-row-limit-panel]');
			const isExpanded = $panel.toggleClass('is-expanded').hasClass('is-expanded');
			$button.text(isExpanded ? ($button.attr('data-collapse-label') || 'Show Less') : ($button.attr('data-expand-label') || 'View All'));
		});
	},

	show_theme_picker: function() {
		const $actions = this.page.main.find('.accounts-actions');
		const $existing = $actions.find('.accounts-theme-popover');
		if ($existing.length) {
			$existing.remove();
			$(document).off('click.finance-theme-picker');
			return;
		}

		const themes = [
			{ key: 'standard', label: 'Standard', description: 'Original hospital sales dashboard palette' },
			{ key: 'hodan-brand', label: 'Hodan Brand', description: 'Carrot Orange and Limed Spruce palette' }
		];
		const $popover = $(`
			<div class="accounts-theme-popover">
				<div class="accounts-theme-popover-head">
					<strong>Choose Theme</strong>
					<button type="button" class="accounts-theme-close" aria-label="Close"><i class="fa fa-times"></i></button>
				</div>
				<div class="accounts-theme-options">
					${themes.map((theme) => `
						<button
							type="button"
							class="accounts-theme-option ${theme.key === this.currentTheme ? 'is-active' : ''}"
							data-theme-key="${this.escape_attribute(theme.key)}"
						>
							<span class="accounts-theme-swatch accounts-theme-swatch--${this.escape_attribute(theme.key)}"></span>
							<span class="accounts-theme-copy">
								<strong>${this.escape_html(theme.label)}</strong>
								<small>${this.escape_html(theme.description)}</small>
							</span>
						</button>
					`).join('')}
				</div>
			</div>
		`);

		$actions.append($popover);
		$popover.on('click', (event) => event.stopPropagation());
		$popover.find('.accounts-theme-close').on('click', () => {
			$popover.remove();
			$(document).off('click.finance-theme-picker');
		});
		$popover.find('[data-theme-key]').on('click', (event) => {
			const nextTheme = $(event.currentTarget).data('theme-key');
			this.set_theme(nextTheme);
			$popover.remove();
			$(document).off('click.finance-theme-picker');
		});

		setTimeout(() => {
			$(document).on('click.finance-theme-picker', () => {
				$popover.remove();
				$(document).off('click.finance-theme-picker');
			});
		}, 0);
	},

	set_theme: function(theme) {
		const normalizedTheme = this.normalize_theme(theme);
		this.currentTheme = normalizedTheme;
		this.save_theme(normalizedTheme);
		this.apply_theme_to_shell();
		const $dashboard = this.page.main.find('.accounts-dashboard');
		$dashboard.removeClass('theme-standard theme-hodan-brand').addClass(`theme-${normalizedTheme}`);
		this.page.main.find('.theme-button span').text(this.get_theme_label(normalizedTheme));
	},

	apply_theme_to_shell: function() {
		const themeClass = `theme-${this.currentTheme}`;
		this.$page_container.removeClass('theme-standard theme-hodan-brand').addClass(themeClass);
		$(this.wrapper).removeClass('theme-standard theme-hodan-brand').addClass(themeClass);
	},

	normalize_theme: function(theme) {
		return theme === 'hodan-brand' ? 'hodan-brand' : 'standard';
	},

	get_theme_label: function(theme) {
		return this.normalize_theme(theme) === 'hodan-brand' ? 'Hodan Brand' : 'Standard';
	},

	get_saved_theme: function() {
		try {
			return this.normalize_theme(window.localStorage.getItem(this.themeStorageKey));
		} catch (error) {
			return 'standard';
		}
	},

	save_theme: function(theme) {
		try {
			window.localStorage.setItem(this.themeStorageKey, this.normalize_theme(theme));
		} catch (error) {
			// Ignore storage errors and keep the in-memory theme.
		}
	},

	show_date_filter: function() {
		const $actions = this.page.main.find('.accounts-actions');
		const $existing = $actions.find('.accounts-date-popover');
		if ($existing.length) {
			$existing.remove();
			$(document).off('click.finance-date-filter');
			return;
		}

		const ranges = {
			today: this.get_today_range(),
			this_month: this.get_month_range(0),
			last_month: this.get_month_range(-1),
			year_to_date: this.get_year_to_date_range()
		};
		const $popover = $(`
			<div class="accounts-date-popover">
				<div class="accounts-date-popover-head">
					<strong>Date Range</strong>
					<button type="button" class="accounts-date-close" aria-label="Close"><i class="fa fa-times"></i></button>
				</div>
				<div class="accounts-date-presets">
					<button type="button" data-range="today">Today</button>
					<button type="button" data-range="this_month">This Month</button>
					<button type="button" data-range="last_month">Last Month</button>
					<button type="button" data-range="year_to_date">Year to Date</button>
				</div>
				<div class="accounts-date-fields">
					<label>
						<span>From</span>
						<input type="date" data-date-field="from_date" value="${this.escape_attribute(this.from_date || ranges.this_month.from_date)}">
					</label>
					<label>
						<span>To</span>
						<input type="date" data-date-field="to_date" value="${this.escape_attribute(this.to_date || ranges.this_month.to_date)}">
					</label>
				</div>
				<div class="accounts-date-error"></div>
				<div class="accounts-date-actions">
					<button type="button" class="accounts-date-cancel">Cancel</button>
					<button type="button" class="accounts-date-apply">Apply</button>
				</div>
			</div>
		`);

		$actions.append($popover);

		$popover.on('click', (event) => event.stopPropagation());
		$popover.find('[data-range]').on('click', (event) => {
			const range = ranges[$(event.currentTarget).data('range')];
			$popover.find('[data-date-field="from_date"]').val(range.from_date);
			$popover.find('[data-date-field="to_date"]').val(range.to_date);
			$popover.find('.accounts-date-error').text('');
		});
		$popover.find('.accounts-date-close, .accounts-date-cancel').on('click', () => {
			$popover.remove();
			$(document).off('click.finance-date-filter');
		});
		$popover.find('.accounts-date-apply').on('click', () => {
			const from_date = $popover.find('[data-date-field="from_date"]').val();
			const to_date = $popover.find('[data-date-field="to_date"]').val();
			if (!from_date || !to_date) {
				$popover.find('.accounts-date-error').text('Choose both dates.');
				return;
			}
			if (from_date > to_date) {
				$popover.find('.accounts-date-error').text('From date cannot be after to date.');
				return;
			}
			this.from_date = from_date;
			this.to_date = to_date;
			$popover.remove();
			$(document).off('click.finance-date-filter');
			this.load_dashboard();
		});

		setTimeout(() => {
			$(document).on('click.finance-date-filter', () => {
				$popover.remove();
				$(document).off('click.finance-date-filter');
			});
		}, 0);
	},

	get_today_range: function() {
		const today = new Date();
		return {
			from_date: this.format_date_value(today),
			to_date: this.format_date_value(today)
		};
	},

	get_month_range: function(month_offset) {
		const today = new Date();
		const first_day = new Date(today.getFullYear(), today.getMonth() + month_offset, 1);
		const last_day = new Date(today.getFullYear(), today.getMonth() + month_offset + 1, 0);
		return {
			from_date: this.format_date_value(first_day),
			to_date: this.format_date_value(last_day)
		};
	},

	get_budget_report_month: function() {
		const range = this.get_month_range(0);
		const base_date = this.from_date || range.from_date;
		return `${base_date.slice(0, 7)}-01`;
	},

	get_year_to_date_range: function() {
		const today = new Date();
		return {
			from_date: this.format_date_value(new Date(today.getFullYear(), 0, 1)),
			to_date: this.format_date_value(today)
		};
	},

	format_date_value: function(date) {
		const year = date.getFullYear();
		const month = String(date.getMonth() + 1).padStart(2, '0');
		const day = String(date.getDate()).padStart(2, '0');
		return `${year}-${month}-${day}`;
	},

	escape_attribute: function(value) {
		return String(value || '')
			.replace(/&/g, '&amp;')
			.replace(/"/g, '&quot;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;');
	},

	escape_html: function(value) {
		return String(value || '')
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;')
			.replace(/'/g, '&#39;');
	},

	to_number: function(value) {
		const number = Number(value);
		return Number.isFinite(number) ? number : 0;
	},

	format_currency_total: function(value) {
		return `$ ${this.to_number(value).toLocaleString(undefined, {
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		})}`;
	}
});

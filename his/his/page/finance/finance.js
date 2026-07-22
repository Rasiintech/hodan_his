frappe.pages['finance'].on_page_load = function(wrapper) {
	new finance(wrapper);
};

finance = Class.extend({
	init: function(wrapper) {
		this.wrapper = wrapper;
		this.from_date = null;
		this.to_date = null;
		this.currentData = null;
		this.aiInsightRequestId = 0;
		this.themeStorageKey = 'finance_dashboard_theme';
		this.currentTheme = this.get_saved_theme();
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Accounts Dashboard',
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
			method: 'his.his.page.finance.finance.get_dashboard_data',
			args: {
				from_date: this.from_date,
				to_date: this.to_date
			},
			callback: (r) => {
				const data = this.prepare_dashboard_data(r.message || {});
				this.currentData = data;
				this.from_date = data.from_date || this.from_date;
				this.to_date = data.to_date || this.to_date;
				this.render_dashboard(data, true);
				this.bind_actions();
				this.load_ai_insights(data);
			}
		});
	},

	render_dashboard: function(data, preserve_sidebar) {
		const $dashboard = $(frappe.render_template('finance', data));
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
		$content.find('.accounts-export-popover').remove();
		$(document).off('click.finance-date-filter');
		$(document).off('click.finance-theme-picker');
		$(document).off('click.finance-export-menu');
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
			unpaid_invoices_total: { customer_count: 0, outstanding: '$ 0' },
			top_supplier_balances: [],
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
			budget_variance_message: 'Loading budget variance...',
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
		prepared.top_supplier_balances = (prepared.top_supplier_balances || [])
			.slice()
			.sort((a, b) => this.to_number(b.raw_balance) - this.to_number(a.raw_balance));
		prepared.account_balances_total = this.format_currency_total(
			prepared.account_balances.reduce((sum, row) => sum + this.to_number(row.raw_balance), 0)
		);
		prepared.unpaid_invoices_total = {
			customer_count: prepared.unpaid_invoices.reduce((sum, row) => sum + this.to_number(row.raw_customer_count || row.customer_count), 0),
			outstanding: this.format_currency_total(
				prepared.unpaid_invoices.reduce((sum, row) => sum + this.to_number(row.raw_outstanding), 0)
			)
		};
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

		$target.html('<p class="ai-insight-placeholder"><i class="fa fa-spinner fa-spin slate-text"></i>Generating AI financial insight...</p>');

		frappe.call({
			method: 'his.his.page.finance.finance.get_ai_insights',
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
				if (this.currentData) {
					this.currentData.insights = payload.insights || [];
				}
				this.render_ai_insights(payload.insights || []);
			},
			error: () => {
				if (requestId !== this.aiInsightRequestId) {
					return;
				}
				const fallbackInsights = [
					{
						icon_class: 'fa-info-circle',
						text_class: 'slate-text',
						text: 'Insights are not available right now. Please review the dashboard figures below.'
					}
				];
				if (this.currentData) {
					this.currentData.insights = fallbackInsights;
				}
				this.render_ai_insights(fallbackInsights);
			}
		});
	},

	build_ai_dashboard_context: function(data) {
		return {
			comparison_range: data.comparison_range || '',
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
		this.page.main.find('.accounts-nav [data-route]').on('click', (event) => {
			event.preventDefault();
			const route = $(event.currentTarget).data('route');
			if (route && route !== 'finance') {
				frappe.set_route(route);
			}
		});
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
		this.page.main.find('.export-button').on('click', (event) => {
			event.stopPropagation();
			this.show_export_menu();
		});
		this.page.main.find('[data-budget-plan-link="1"]').on('click', (event) => {
			event.preventDefault();
			const report_month = this.get_budget_report_month();
			frappe.route_options = {
				report_month: report_month,
				from_date: this.from_date,
				to_date: this.to_date
			};
			frappe.set_route('monthly_budget_plan');
		});
		this.bind_supplier_balances_toggle();
	},

	bind_supplier_balances_toggle: function() {
		const visibleLimit = 15;
		const $table = this.page.main.find('[data-supplier-balances-table="1"]');
		const $toggle = this.page.main.find('[data-supplier-balances-toggle="1"]');
		if (!$table.length || !$toggle.length) {
			return;
		}

		const $rows = $table.find('tbody tr');
		if ($rows.length <= visibleLimit) {
			$toggle.hide();
			return;
		}

		const setExpandedState = (expanded) => {
			$rows.each((index, row) => {
				$(row).toggle(index < visibleLimit || expanded);
			});
			$toggle.text(expanded ? `Show Top ${visibleLimit} Payables` : 'View All Payables');
			$toggle.data('expanded', expanded);
		};

		setExpandedState(false);
		$toggle.off('click').on('click', (event) => {
			event.preventDefault();
			setExpandedState(!$toggle.data('expanded'));
		});
	},

	show_export_menu: function() {
		const $actions = this.page.main.find('.accounts-actions');
		const $existing = $actions.find('.accounts-export-popover');
		if ($existing.length) {
			$existing.remove();
			$(document).off('click.finance-export-menu');
			return;
		}

		const options = [
			{ key: 'csv', label: 'CSV', description: 'Download dashboard data as spreadsheet-ready CSV', icon: 'fa-file-text-o' },
			{ key: 'print', label: 'Print', description: 'Open a clean print view of the dashboard', icon: 'fa-print' },
			{ key: 'pdf', label: 'PDF', description: 'Open print dialog for Save as PDF export', icon: 'fa-file-pdf-o' }
		];
		const $popover = $(`
			<div class="accounts-export-popover">
				<div class="accounts-export-popover-head">
					<strong>Export Dashboard</strong>
					<button type="button" class="accounts-export-close" aria-label="Close"><i class="fa fa-times"></i></button>
				</div>
				<div class="accounts-export-options">
					${options.map((option) => `
						<button type="button" class="accounts-export-option" data-export-action="${this.escape_attribute(option.key)}">
							<span class="accounts-export-icon"><i class="fa ${this.escape_attribute(option.icon)}"></i></span>
							<span class="accounts-export-copy">
								<strong>${this.escape_html(option.label)}</strong>
								<small>${this.escape_html(option.description)}</small>
							</span>
						</button>
					`).join('')}
				</div>
			</div>
		`);

		$actions.append($popover);
		$popover.on('click', (event) => event.stopPropagation());
		$popover.find('.accounts-export-close').on('click', () => {
			$popover.remove();
			$(document).off('click.finance-export-menu');
		});
		$popover.find('[data-export-action]').on('click', (event) => {
			const action = $(event.currentTarget).data('export-action');
			$popover.remove();
			$(document).off('click.finance-export-menu');
			this.handle_export_action(action);
		});

		setTimeout(() => {
			$(document).on('click.finance-export-menu', () => {
				$popover.remove();
				$(document).off('click.finance-export-menu');
			});
		}, 0);
	},

	handle_export_action: function(action) {
		if (!this.currentData) {
			frappe.show_alert({
				message: __('Dashboard data is still loading. Please try export again in a moment.'),
				indicator: 'orange'
			});
			return;
		}

		if (action === 'print') {
			this.open_print_window('print');
			return;
		}

		if (action === 'pdf') {
			this.open_print_window('pdf');
			return;
		}

		this.export_dashboard_csv();
	},

	export_dashboard_csv: function() {
		const csvContent = this.build_export_csv(this.currentData);
		const blob = new Blob([`\ufeff${csvContent}`], { type: 'text/csv;charset=utf-8;' });
		const fromDate = (this.currentData.from_date || 'from').replace(/[^0-9-]/g, '');
		const toDate = (this.currentData.to_date || 'to').replace(/[^0-9-]/g, '');
		const fileName = `finance-dashboard-${fromDate}-to-${toDate}.csv`;
		const downloadUrl = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = downloadUrl;
		link.download = fileName;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(downloadUrl);

		frappe.show_alert({
			message: __('Finance dashboard export downloaded'),
			indicator: 'green'
		});
	},

	open_print_window: function(mode) {
		const printWindow = window.open('', '_blank', 'width=1200,height=900');
		if (!printWindow) {
			frappe.msgprint(__('Unable to open export window. Please allow pop-ups and try again.'));
			return;
		}

		const title = mode === 'pdf' ? 'Finance Dashboard PDF Export' : 'Finance Dashboard Print View';
		printWindow.document.open();
		printWindow.document.write(this.build_print_document(this.currentData, mode, title));
		printWindow.document.close();

		frappe.show_alert({
			message: mode === 'pdf'
				? __('Print dialog opened. Choose "Save as PDF" in your browser destination options.')
				: __('Print view opened'),
			indicator: 'green'
		});
	},

	build_export_csv: function(data) {
		const rows = [];
		const addRow = (...values) => rows.push(values.map((value) => this.escape_csv_value(value)).join(','));
		const addBlankRow = () => rows.push('');
		const addSectionTitle = (title) => {
			addRow(title);
		};

		addRow('Accounts Dashboard Export');
		addRow('Date Range', data.date_range || '');
		addRow('From Date', data.from_date || '');
		addRow('To Date', data.to_date || '');
		addRow('Theme', this.get_theme_label(this.currentTheme));
		addBlankRow();

		addSectionTitle('Metrics');
		addRow('Metric', 'Value', 'Trend', 'Comparison');
		(data.metrics || []).forEach((metric) => {
			addRow(metric.label, metric.value, this.strip_html_text(metric.trend), data.comparison_range || '');
		});
		addBlankRow();

		addSectionTitle('Income vs Expenses');
		addRow('Period', 'Income', 'Expenses');
		(data.income_expenses || []).forEach((item) => {
			addRow(item.label, item.income_value, item.expense_value);
		});
		addBlankRow();

		addSectionTitle('Expense by Category');
		addRow('Category', 'Value');
		(data.expense_categories || []).forEach((item) => {
			addRow(item.label, item.value);
		});
		addBlankRow();

		addSectionTitle('Income by Source');
		addRow('Source', 'Value');
		(data.income_sources || []).forEach((item) => {
			addRow(item.label, item.value);
		});
		addBlankRow();

		addSectionTitle('Account Balances');
		addRow('Account', 'Account Type', 'Balance');
		(data.account_balances || []).forEach((row) => {
			addRow(row.account, row.type, row.balance);
		});
		addRow('Total', 'Bank', data.account_balances_total || '');
		addBlankRow();

		addSectionTitle('Receivables');
		addRow('Customer Group', 'Customers', 'Outstanding');
		(data.unpaid_invoices || []).forEach((row) => {
			addRow(row.customer_group, row.customer_count, row.outstanding);
		});
		addRow('Total', data.unpaid_invoices_total.customer_count, data.unpaid_invoices_total.outstanding);
		addBlankRow();

		addSectionTitle('Top Supplier Balances');
		addRow('Supplier', 'Supplier Group', 'Balance');
		(data.top_supplier_balances || []).forEach((row) => {
			addRow(row.supplier, row.supplier_group, row.balance);
		});
		addRow('Total', 'Top 10', data.top_supplier_balances_total || '');
		addBlankRow();

		addSectionTitle('Budget Variance');
		if ((data.budget_variance || []).length) {
			addRow('Category', 'Budget', 'Actual Debit', 'Variance', 'Indicator', 'Utilization');
			(data.budget_variance || []).forEach((row) => {
				addRow(row.category, row.budget, row.actual, row.variance, row.indicator_label, row.utilization);
			});
			addRow(
				'Total',
				data.budget_variance_total.budget,
				data.budget_variance_total.actual,
				data.budget_variance_total.variance,
				data.budget_variance_total.indicator_label,
				data.budget_variance_total.utilization
			);
		} else {
			addRow(data.budget_variance_message || 'No budget variance data available');
		}
		addBlankRow();

		addSectionTitle('AI Insight');
		addRow('Insight');
		(data.insights || []).forEach((item) => {
			addRow(item.text);
		});

		return rows.join('\r\n');
	},

	build_print_document: function(data, mode, title) {
		const note = mode === 'pdf'
			? '<div class="print-note">Use your browser destination options to save this view as PDF.</div>'
			: '';
		const renderRows = (items, columns) => {
			return (items || []).map((item) => `
				<tr>${columns.map((column) => `<td>${this.escape_html(item[column] == null ? '' : item[column])}</td>`).join('')}</tr>
			`).join('');
		};

		return `<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
	<title>${this.escape_html(title)}</title>
	<style>
		body { font-family: Arial, sans-serif; margin: 24px; color: #1f2937; }
		h1 { margin: 0 0 6px; font-size: 28px; }
		h2 { margin: 28px 0 12px; font-size: 18px; color: #111827; }
		p { margin: 4px 0; }
		.meta { display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 18px; }
		.meta-card { padding: 12px 14px; border: 1px solid #d1d5db; border-radius: 8px; min-width: 180px; }
		.meta-card strong { display: block; margin-bottom: 4px; font-size: 12px; text-transform: uppercase; color: #6b7280; }
		.print-note { margin: 14px 0 18px; padding: 12px 14px; border-radius: 8px; background: #fff7e6; border: 1px solid #f19f21; color: #7c4a00; }
		.metric-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
		.metric-card { border: 1px solid #d1d5db; border-radius: 10px; padding: 14px; }
		.metric-card strong { display: block; margin: 8px 0 6px; font-size: 20px; }
		.metric-card small, .muted { color: #6b7280; }
		table { width: 100%; border-collapse: collapse; margin-top: 10px; }
		th, td { border: 1px solid #d1d5db; padding: 8px 10px; text-align: left; font-size: 13px; vertical-align: top; }
		th { background: #f9fafb; }
		.section-block { margin-top: 22px; }
		.list-table td:last-child, .list-table th:last-child { text-align: right; }
		.ai-list { padding-left: 18px; }
		.ai-list li { margin-bottom: 8px; }
		@media print {
			body { margin: 12mm; }
			.print-note { display: ${mode === 'pdf' ? 'block' : 'none'}; }
		}
	</style>
</head>
<body>
	<h1>Accounts Dashboard</h1>
	<p>${this.escape_html(data.date_range || '')}</p>
	${note}
	<div class="meta">
		<div class="meta-card"><strong>From Date</strong><span>${this.escape_html(data.from_date || '')}</span></div>
		<div class="meta-card"><strong>To Date</strong><span>${this.escape_html(data.to_date || '')}</span></div>
		<div class="meta-card"><strong>Theme</strong><span>${this.escape_html(this.get_theme_label(this.currentTheme))}</span></div>
	</div>

	<h2>Metrics</h2>
	<div class="metric-grid">
		${(data.metrics || []).map((metric) => `
			<div class="metric-card">
				<div>${this.escape_html(metric.label || '')}</div>
				<strong>${this.escape_html(metric.value || '')}</strong>
				<small>${this.escape_html(this.strip_html_text(metric.trend || ''))}</small>
				<div class="muted">vs ${this.escape_html(data.comparison_range || '')}</div>
			</div>
		`).join('')}
	</div>

	<div class="section-block">
		<h2>Income vs Expenses</h2>
		<table class="list-table">
			<thead><tr><th>Period</th><th>Income</th><th>Expenses</th></tr></thead>
			<tbody>${renderRows(data.income_expenses, ['label', 'income_value', 'expense_value'])}</tbody>
		</table>
	</div>

	<div class="section-block">
		<h2>Expense by Category</h2>
		<table class="list-table">
			<thead><tr><th>Category</th><th>Value</th></tr></thead>
			<tbody>${renderRows(data.expense_categories, ['label', 'value'])}</tbody>
		</table>
	</div>

	<div class="section-block">
		<h2>Income by Source</h2>
		<table class="list-table">
			<thead><tr><th>Source</th><th>Value</th></tr></thead>
			<tbody>${renderRows(data.income_sources, ['label', 'value'])}</tbody>
		</table>
	</div>

	<div class="section-block">
		<h2>Account Balances</h2>
		<table>
			<thead><tr><th>Account</th><th>Account Type</th><th>Balance</th></tr></thead>
			<tbody>${renderRows(data.account_balances, ['account', 'type', 'balance'])}</tbody>
		</table>
		<p><strong>Total:</strong> ${this.escape_html(data.account_balances_total || '')}</p>
	</div>

	<div class="section-block">
		<h2>Receivables</h2>
		<table>
			<thead><tr><th>Customer Group</th><th>Customers</th><th>Outstanding</th></tr></thead>
			<tbody>${renderRows(data.unpaid_invoices, ['customer_group', 'customer_count', 'outstanding'])}</tbody>
		</table>
		<p><strong>Total:</strong> ${this.escape_html(String((data.unpaid_invoices_total || {}).customer_count || 0))} customers, ${this.escape_html((data.unpaid_invoices_total || {}).outstanding || '')}</p>
	</div>

	<div class="section-block">
		<h2>Top Supplier Balances</h2>
		<table>
			<thead><tr><th>Supplier</th><th>Supplier Group</th><th>Balance</th></tr></thead>
			<tbody>${renderRows(data.top_supplier_balances, ['supplier', 'supplier_group', 'balance'])}</tbody>
		</table>
		<p><strong>Total:</strong> ${this.escape_html(data.top_supplier_balances_total || '')}</p>
	</div>

	<div class="section-block">
		<h2>Budget Variance</h2>
		${(data.budget_variance || []).length ? `
			<table>
				<thead><tr><th>Category</th><th>Budget</th><th>Actual Debit</th><th>Variance</th><th>Indicator</th><th>Utilization</th></tr></thead>
				<tbody>${renderRows(data.budget_variance, ['category', 'budget', 'actual', 'variance', 'indicator_label', 'utilization'])}</tbody>
			</table>
			<p><strong>Total:</strong> ${this.escape_html((data.budget_variance_total || {}).variance || '')}</p>
		` : `<p>${this.escape_html(data.budget_variance_message || 'No budget variance data available')}</p>`}
	</div>

	<div class="section-block">
		<h2>AI Insight</h2>
		<ul class="ai-list">
			${(data.insights || []).map((item) => `<li>${this.escape_html(item.text || '')}</li>`).join('')}
		</ul>
	</div>

	<script>
		window.addEventListener('load', function () {
			setTimeout(function () {
				window.print();
			}, 250);
		});
	</script>
</body>
</html>`;
	},

	strip_html_text: function(value) {
		return String(value || '')
			.replace(/<[^>]*>/g, ' ')
			.replace(/\s+/g, ' ')
			.trim();
	},

	escape_csv_value: function(value) {
		const text = String(value == null ? '' : value).replace(/"/g, '""');
		return `"${text}"`;
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
			{ key: 'standard', label: 'Standard', description: 'Original finance dashboard palette' },
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

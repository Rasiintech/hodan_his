frappe.pages['stock-dashboard'].on_page_load = function(wrapper) {
	new stock_dashboard(wrapper);
};

stock_dashboard = Class.extend({
	init: function(wrapper) {
		this.wrapper = wrapper;
		this.from_date = null;
		this.to_date = null;
		this.currentData = null;
		this.aiInsightRequestId = 0;
		this.themeStorageKey = 'stock_dashboard_theme';
		this.currentTheme = this.get_saved_theme();
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Stock Dashboard',
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
			method: 'his.his.page.stock_dashboard.stock_dashboard.get_dashboard_data',
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
		const $dashboard = $(frappe.render_template('stock_dashboard', data));
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
			low_moving_items: [],
			low_moving_items_total: '0',
			low_moving_items_has_more: false,
			top_supplier_balances: [],
			top_supplier_balances_total: '0',
			top_supplier_balances_has_more: false,
			store_balance_columns: [],
			budget_variance: [],
			budget_variance_has_more: false,
			budget_variance_total: {
				count: '0'
			},
			budget_variance_message: 'Loading stock anomalies...',
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
		prepared.low_moving_items = prepared.low_moving_items || [];
		prepared.low_moving_items_has_more = !!prepared.low_moving_items_has_more;
		prepared.low_moving_items_total = prepared.low_moving_items_total || this.format_number_total(prepared.low_moving_items.length);
		prepared.top_supplier_balances = prepared.top_supplier_balances || [];
		prepared.store_balance_columns = prepared.store_balance_columns || [];
		prepared.top_supplier_balances.forEach((row) => {
			row.store_balance_values = row.store_balance_values || prepared.store_balance_columns.map(() => '—');
		});
		prepared.account_balances_total = this.format_currency_total(
			prepared.account_balances.reduce((sum, row) => sum + this.to_number(row.raw_balance), 0)
		);
		prepared.unpaid_invoices_total = {
			customer_count: prepared.unpaid_invoices.reduce((sum, row) => sum + this.to_number(row.raw_customer_count || row.customer_count), 0),
			outstanding: this.format_currency_total(
				prepared.unpaid_invoices.reduce((sum, row) => sum + this.to_number(row.raw_outstanding), 0)
			)
		};
		prepared.top_supplier_balances_has_more = !!prepared.top_supplier_balances_has_more;
		prepared.top_supplier_balances_total = prepared.top_supplier_balances_total || this.format_number_total(prepared.top_supplier_balances.length);
		prepared.budget_variance = prepared.budget_variance || [];
		prepared.budget_variance_has_more = !!prepared.budget_variance_has_more;
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

		$target.html('<p class="ai-insight-placeholder"><i class="fa fa-spinner fa-spin slate-text"></i>Generating AI stock insight...</p>');

		frappe.call({
			method: 'his.his.page.stock_dashboard.stock_dashboard.get_ai_insights',
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
			top_supplier_balances_total: data.top_supplier_balances_total || this.format_number_total((data.top_supplier_balances || []).length),
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
			if (route && route !== 'stock-dashboard') {
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
			frappe.set_route('query-report', 'Stock Balance');
		});
		this.bind_table_expand();
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
		const fileName = `stock-dashboard-${fromDate}-to-${toDate}.csv`;
		const downloadUrl = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = downloadUrl;
		link.download = fileName;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(downloadUrl);

		frappe.show_alert({
			message: __('Stock dashboard export downloaded'),
			indicator: 'green'
		});
	},

	open_print_window: function(mode) {
		const printWindow = window.open('', '_blank', 'width=1200,height=900');
		if (!printWindow) {
			frappe.msgprint(__('Unable to open export window. Please allow pop-ups and try again.'));
			return;
		}

		const title = mode === 'pdf' ? 'Stock Dashboard PDF Export' : 'Stock Dashboard Print View';
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

		addRow('Stock Dashboard Export');
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

		addSectionTitle('Stock In vs Stock Out');
		addRow('Period', 'Stock In', 'Stock Out');
		(data.income_expenses || []).forEach((item) => {
			addRow(item.label, item.income_value, item.expense_value);
		});
		addBlankRow();

		addSectionTitle('Stock Value by Item Group');
		addRow('Item Group', 'Value');
		(data.expense_categories || []).forEach((item) => {
			addRow(item.label, item.value);
		});
		addBlankRow();

		addSectionTitle('Stock Value by Warehouse');
		addRow('Warehouse', 'Value');
		(data.income_sources || []).forEach((item) => {
			addRow(item.label, item.value);
		});
		addBlankRow();

		addSectionTitle('Warehouse Stock Value');
		addRow('Warehouse', 'Warehouse Type', 'Stock Value');
		(data.account_balances || []).forEach((row) => {
			addRow(row.account, row.type, row.balance);
		});
		addRow('Total', 'Top Warehouses', data.account_balances_total || '');
		addBlankRow();

		addSectionTitle('Item Group Inventory');
		addRow('Item Group', 'SKUs', 'Stock Value');
		(data.unpaid_invoices || []).forEach((row) => {
			addRow(row.customer_group, row.customer_count, row.outstanding);
		});
		addRow('Total', data.unpaid_invoices_total.customer_count, data.unpaid_invoices_total.outstanding);
		addBlankRow();

		addSectionTitle('Low Moving Items with High Balance');
		addRow('Item', 'Total Qty', 'Total Sold', 'Item Value', 'Sell-through');
		(data.low_moving_items || []).forEach((row) => {
			addRow(row.item, row.total_qty, row.total_sold, row.item_value, row.sell_through);
		});
		addRow('Total', 'High-balance low movers', '', '', data.low_moving_items_total || '0');
		addBlankRow();

		addSectionTitle('Fast Moving Drug Items Below Weekly Average Sold');
		addRow('Item', 'Total Qty', ...(data.store_balance_columns || []), 'Total Sold');
		(data.top_supplier_balances || []).forEach((row) => {
			addRow(row.supplier, row.total_qty, ...(row.store_balance_values || []), row.total_sold);
		});
		addRow('Total', 'Flagged Items', ...(data.store_balance_columns || []).map(() => ''), data.top_supplier_balances_total || '');
		addBlankRow();

		addSectionTitle('Stock Anomalies');
		if ((data.budget_variance || []).length) {
			addRow('Item', 'Anomaly', 'Total Qty', 'Detail');
			(data.budget_variance || []).forEach((row) => {
				addRow(row.category, row.anomaly, row.actual, row.variance);
			});
			addRow('Total', `${data.budget_variance_total.count || '0'} anomalies`, '', '');
		} else {
			addRow(data.budget_variance_message || 'No stock anomalies detected');
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
		const renderFastMovingRows = (items) => (items || []).map((row) => `
			<tr><td>${this.escape_html(row.supplier || '')}</td><td>${this.escape_html(row.total_qty || '')}</td>${(row.store_balance_values || []).map((balance) => `<td>${this.escape_html(balance)}</td>`).join('')}<td>${this.escape_html(row.total_sold || '')}</td></tr>
		`).join('');

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
	<h1>Hospital Stock Dashboard</h1>
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
		<h2>Stock In vs Stock Out</h2>
		<table class="list-table">
			<thead><tr><th>Period</th><th>Stock In</th><th>Stock Out</th></tr></thead>
			<tbody>${renderRows(data.income_expenses, ['label', 'income_value', 'expense_value'])}</tbody>
		</table>
	</div>

	<div class="section-block">
		<h2>Stock Value by Item Group</h2>
		<table class="list-table">
			<thead><tr><th>Item Group</th><th>Value</th></tr></thead>
			<tbody>${renderRows(data.expense_categories, ['label', 'value'])}</tbody>
		</table>
	</div>

	<div class="section-block">
		<h2>Stock Value by Warehouse</h2>
		<table class="list-table">
			<thead><tr><th>Warehouse</th><th>Value</th></tr></thead>
			<tbody>${renderRows(data.income_sources, ['label', 'value'])}</tbody>
		</table>
	</div>

	<div class="section-block">
		<h2>Warehouse Stock Value</h2>
		<table>
			<thead><tr><th>Warehouse</th><th>Warehouse Type</th><th>Stock Value</th></tr></thead>
			<tbody>${renderRows(data.account_balances, ['account', 'type', 'balance'])}</tbody>
		</table>
		<p><strong>Total:</strong> ${this.escape_html(data.account_balances_total || '')}</p>
	</div>

	<div class="section-block">
		<h2>Item Group Inventory</h2>
		<table>
			<thead><tr><th>Item Group</th><th>SKUs</th><th>Stock Value</th></tr></thead>
			<tbody>${renderRows(data.unpaid_invoices, ['customer_group', 'customer_count', 'outstanding'])}</tbody>
		</table>
		<p><strong>Total:</strong> ${this.escape_html(String((data.unpaid_invoices_total || {}).customer_count || 0))} skus, ${this.escape_html((data.unpaid_invoices_total || {}).outstanding || '')}</p>
	</div>

	<div class="section-block">
		<h2>Low Moving Items with High Balance</h2>
		<table>
			<thead><tr><th>Item</th><th>Total Qty</th><th>Total Sold</th><th>Item Value</th><th>Sell-through</th></tr></thead>
			<tbody>${renderRows(data.low_moving_items, ['item', 'total_qty', 'total_sold', 'item_value', 'sell_through'])}</tbody>
		</table>
	</div>

	<div class="section-block">
		<h2>Fast Moving Drug Items Below Weekly Average Sold</h2>
		<table>
			<thead><tr><th>Item</th><th>Total Qty</th>${(data.store_balance_columns || []).map((warehouse) => `<th>${this.escape_html(warehouse)}</th>`).join('')}<th>Total Sold</th></tr></thead>
			<tbody>${renderFastMovingRows(data.top_supplier_balances)}</tbody>
		</table>
		<p><strong>Flagged Items:</strong> ${this.escape_html(data.top_supplier_balances_total || '')}</p>
	</div>

	<div class="section-block">
		<h2>Stock Anomalies</h2>
		${(data.budget_variance || []).length ? `
			<table>
				<thead><tr><th>Item</th><th>Anomaly</th><th>Total Qty</th><th>Detail</th></tr></thead>
				<tbody>${renderRows(data.budget_variance, ['category', 'anomaly', 'actual', 'variance'])}</tbody>
			</table>
			<p><strong>Total:</strong> ${this.escape_html((data.budget_variance_total || {}).count || '0')} anomalies</p>
		` : `<p>${this.escape_html(data.budget_variance_message || 'No stock anomalies detected')}</p>`}
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
			{ key: 'standard', label: 'Standard', description: 'Original stock dashboard palette' },
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

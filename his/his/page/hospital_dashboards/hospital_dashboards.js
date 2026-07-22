frappe.pages['hospital-dashboards'].on_page_load = function(wrapper) {
	new HospitalDashboardsPage(wrapper);
};

const HOSPITAL_DASHBOARD_VIEWS = {
	finance: {
		label: 'Finance',
		icon: 'fa-home',
		template: 'finance',
		method: 'his.his.page.finance.finance.get_dashboard_data',
		ai_method: 'his.his.page.finance.finance.get_ai_insights',
		ai_loading_message: 'Generating AI financial insight...',
		empty_message: 'Loading budget variance...',
		on_budget_link(page) {
			const report_month = page.get_budget_report_month('finance');
			frappe.route_options = {
				report_month,
				from_date: page.get_view_state('finance').from_date,
				to_date: page.get_view_state('finance').to_date
			};
			frappe.set_route('monthly_budget_plan');
		}
	},
	'profit-and-loss': {
		label: 'Profit and Loss',
		icon: 'fa-landmark',
		template: 'profit_and_loss',
		method: 'his.his.page.profit_and_loss.profit_and_loss.get_dashboard_data',
		ai_method: 'his.his.page.profit_and_loss.profit_and_loss.get_ai_insights',
		ai_loading_message: 'Generating AI profit and loss insight...',
		empty_message: 'Loading the dashboard...',
		on_budget_link(page) {
			const state = page.get_view_state('profit-and-loss');
			frappe.route_options = {
				company: frappe.defaults.get_user_default('Company') || frappe.defaults.get_global_default('company'),
				filter_based_on: 'Date Range',
				period_start_date: state.from_date,
				period_end_date: state.to_date,
				periodicity: 'Yearly',
				accumulated_values: 0
			};
			frappe.set_route('query-report', 'Profit and Loss Statement');
		}
	},
	sales: {
		label: 'Sales',
		icon: 'fa-file-invoice',
		template: 'sales_dashboard',
		method: 'his.his.page.sales_dashboard.sales_dashboard.get_dashboard_data',
		ai_method: 'his.his.page.sales_dashboard.sales_dashboard.get_ai_insights',
		ai_loading_message: 'Generating AI sales insight...',
		empty_message: 'Loading item group performance...',
		on_budget_link() {
			frappe.set_route('List', 'Sales Invoice');
		}
	},
	'purchase-dashboard': {
		label: 'Purchase',
		icon: 'fa-shopping-cart',
		template: 'purchase_dashboard',
		method: 'his.his.page.purchase_dashboard.purchase_dashboard.get_dashboard_data',
		ai_method: 'his.his.page.purchase_dashboard.purchase_dashboard.get_ai_insights',
		ai_loading_message: 'Generating AI purchase insight...',
		empty_message: 'Loading item group performance...',
		on_budget_link() {
			frappe.set_route('List', 'Purchase Invoice');
		}
	},
	'stock-dashboard': {
		label: 'Stock',
		icon: 'fa-cubes',
		template: 'stock_dashboard',
		method: 'his.his.page.stock_dashboard.stock_dashboard.get_dashboard_data',
		ai_method: 'his.his.page.stock_dashboard.stock_dashboard.get_ai_insights',
		ai_loading_message: 'Generating AI stock insight...',
		empty_message: 'Loading fast moving items...',
		on_budget_link() {
			frappe.set_route('query-report', 'Stock Balance');
		}
	},
	'hr-dashboard': {
		label: 'HR',
		icon: 'fa-university',
		template: 'hr_dashboard',
		method: 'his.his.page.hr_dashboard.hr_dashboard.get_dashboard_data',
		ai_method: 'his.his.page.hr_dashboard.hr_dashboard.get_ai_insights',
		ai_loading_message: 'Generating AI HR insight...',
		empty_message: 'Loading employee joiner mix...',
		on_budget_link() {
			frappe.set_route('List', 'Employee');
		}
	},
	'payroll-dashboard': {
		label: 'Payroll',
		icon: 'fa-money',
		template: 'payroll_dashboard',
		method: 'his.his.page.payroll_dashboard.payroll_dashboard.get_dashboard_data',
		ai_method: 'his.his.page.payroll_dashboard.payroll_dashboard.get_ai_insights',
		ai_loading_message: 'Generating AI payroll insight...',
		empty_message: 'Loading top employee payouts...',
		on_budget_link() {
			frappe.set_route('List', 'Salary Slip');
		}
	},
	'commissions-dashboard': {
		label: 'Commissions',
		icon: 'fa-chart-bar',
		template: 'commissions_dashboard',
		method: 'his.his.page.commissions_dashboard.commissions_dashboard.get_dashboard_data',
		ai_method: 'his.his.page.commissions_dashboard.commissions_dashboard.get_ai_insights',
		ai_loading_message: 'Generating AI commission insight...',
		empty_message: 'Loading top doctor commission share...',
		on_budget_link() {
			frappe.set_route('query-report', 'Doctors Net Commission');
		}
	},
	'budget-dashboard': {
		label: 'Budget',
		icon: 'fa-clipboard',
		template: 'budget_dashboard',
		method: 'his.his.page.budget_dashboard.budget_dashboard.get_dashboard_data',
		ai_method: 'his.his.page.budget_dashboard.budget_dashboard.get_ai_insights',
		ai_loading_message: 'Generating AI budget insight...',
		empty_message: 'Loading budget variance...',
		on_budget_link(page) {
			frappe.route_options = {
				report_month: page.get_view_state('budget-dashboard').from_date,
				from_date: page.get_view_state('budget-dashboard').from_date,
				to_date: page.get_view_state('budget-dashboard').to_date
			};
			frappe.set_route('monthly_budget_plan');
		}
	},
	'tasks-dashboard': {
		label: 'Tasks',
		icon: 'fa-sitemap',
		template: 'tasks_dashboard',
		method: 'his.his.page.tasks_dashboard.tasks_dashboard.get_dashboard_data',
		ai_method: 'his.his.page.tasks_dashboard.tasks_dashboard.get_ai_insights',
		ai_loading_message: 'Generating AI task insight...',
		empty_message: 'Loading department workload variance...',
		on_budget_link() {
			frappe.set_route('List', 'Task');
		}
	}
};

const HOSPITAL_DASHBOARD_INLINE_TEMPLATES = {
	finance: `<div class="accounts-dashboard theme-{%= current_theme || "standard" %}">
	<aside class="accounts-sidebar">
		<nav class="accounts-nav">
			<a class="active" href="#" data-route="finance"><i class="fa fa-home"></i><span>Finance</span></a>
			<a href="#" data-route="profit-and-loss"><i class="fa fa-landmark"></i><span>Profit and Loss</span></a>
			<a href="#" data-route="sales-dashboard"><i class="fa fa-file-invoice"></i><span>Sales</span></a>
			<a href="#" data-route="purchase-dashboard"><i class="fa fa-shopping-cart"></i><span>Purchase</span></a>
			<a href="#" data-route="stock-dashboard"><i class="fa fa-shopping-cart"></i><span>Stock</span></a>
			<a href="#" data-route="hr-dashboard"><i class="fa fa-university"></i><span>HR</span></a>
			<a href="#" data-route="payroll-dashboard"><i class="fa fa-university"></i><span>Payroll</span></a>
			<a href="#" data-route="commissions-dashboard"><i class="fa fa-chart-bar"></i><span>Commissions</span></a>
			<a href="#" data-route="budget-dashboard"><i class="fa fa-clipboard"></i><span>Budget</span></a>
			<a href="#" data-route="tasks-dashboard"><i class="fa fa-sitemap"></i><span>Tasks</span></a>
		</nav>
	</aside>
	<main class="accounts-content">
		<header class="accounts-header">
			<div>
				<h1>Accounts Dashboard</h1>
				<p>Financial overview and key accounting metrics</p>
			</div>
			<div class="accounts-actions">
				<button class="theme-button" type="button"><i class="fa fa-paint-brush"></i><span>{%= current_theme_label || "Standard" %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="date-button"><i class="fa fa-calendar"></i><span>{%= date_range %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="filter-button"><i class="fa fa-filter"></i><span>Filters</span></button>
				<button class="refresh-button"><i class="fa fa-sync-alt"></i><span>Refresh</span></button>
				<button class="export-button"><i class="fa fa-download"></i><span>Export</span></button>
			</div>
		</header>
		<section class="metric-grid">
			{% for metric in metrics %}
			<div class="metric-card {%= metric.class %}">
				<div class="metric-icon">{%= metric.icon %}</div>
				<div>
					<span>{%= metric.label %}</span>
					<strong>{%= metric.value %}</strong>
					<small class="{%= metric.trend_class %}">{%= metric.trend %}</small>
					<em>vs {%= comparison_range %}</em>
				</div>
			</div>
			{% endfor %}
		</section>
		<section class="chart-row">
			<div class="panel income-expenses">
				<div class="panel-head">
					<h2>Income vs Expenses</h2>
					<div class="legend"><span class="green"></span>Income <span class="red"></span>Expenses</div>
				</div>
				<div class="bar-chart">
					<div class="plot">
						<div class="grid-lines"></div>
						{% for item in income_expenses %}
						<div class="bar-group">
							<div class="bar-stack">
								<span class="bar-column">
									<span class="bar-value income-value">{%= item.income_value %}</span>
									<span class="income-b" style="height: {%= item.income_height %}px;"></span>
								</span>
								<span class="bar-column">
									<span class="bar-value expense-value">{%= item.expense_value %}</span>
									<span class="expense-b" style="height: {%= item.expense_height %}px;"></span>
								</span>
							</div>
							<label>{%= item.label %}</label>
						</div>
						{% endfor %}
					</div>
				</div>
			</div>
			<div class="panel donut-panel">
				<h2>Expense by Category</h2>
				<div class="donut-wrap">
					<div class="donut expense-donut" style="{%= expense_donut_style %}"></div>
					<ul class="chart-list">
						{% for category in expense_categories %}
						<li><span class="{%= category.class %}"></span>{%= category.label %} <b>{%= category.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
			<div class="panel donut-panel source-panel">
				<h2>Income by Source</h2>
				<div class="donut-wrap">
					<div class="donut source-donut" style="{%= source_donut_style %}"></div>
					<ul class="chart-list">
						{% for source in income_sources %}
						<li><span class="{%= source.class %}"></span>{%= source.label %} <b>{%= source.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
		</section>
		<section class="table-row">
			<div class="panel table-panel accounts-table">
				<h2>Account Balances</h2>
				<table>
					<thead><tr><th>Account</th><th>Account Type</th><th>Balance ($)</th></tr></thead>
					<tbody>
						{% for row in account_balances %}
						<tr><td>{%= row.account %}</td><td>{%= row.type %}</td><td>{%= row.balance %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>Bank</th><th>{%= account_balances_total %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View All Accounts</a>
			</div>
			<div class="panel table-panel">
				<h2>Receivables</h2>
				<table>
					<thead><tr><th>Customer Group</th><th>Customers</th><th>Outstanding ($)</th></tr></thead>
					<tbody>
						{% for row in unpaid_invoices %}
						<tr><td>{%= row.customer_group %}</td><td>{%= row.customer_count %}</td><td>{%= row.outstanding %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>{%= unpaid_invoices_total.customer_count %}</th><th>{%= unpaid_invoices_total.outstanding %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View All Receivables</a>
			</div>
			<div class="panel table-panel">
				<h2>Top Supplier Balances</h2>
				<table>
					<thead><tr><th>Supplier</th><th>Supplier Group</th><th>Balance ($)</th></tr></thead>
					<tbody>
						{% for row in top_supplier_balances %}
						<tr><td>{%= row.supplier %}</td><td>{%= row.supplier_group %}</td><td>{%= row.balance %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>Top 10</th><th>{%= top_supplier_balances_total %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View All Payables</a>
			</div>
		</section>
		<section class="bottom-row">
			<div class="panel table-panel budget-variance-panel">
				<h2>Budget Variance</h2>
				{% if budget_variance.length %}
				<table>
					<thead><tr><th>Category</th><th>Budget</th><th>Actual</th><th>Variance</th><th>Indicator</th></tr></thead>
					<tbody>
						{% for row in budget_variance %}
						<tr>
							<td>{%= row.category %}</td>
							<td>{%= row.budget %}</td>
							<td>{%= row.actual %}</td>
							<td class="variance-cell {%= row.variance_class %}">{%= row.variance %}</td>
							<td><div class="budget-indicator"><span class="indicator-pill {%= row.indicator_class %}">{%= row.indicator_label %}</span><small>{%= row.utilization %}</small></div></td>
						</tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr>
							<th>Total</th>
							<th>{%= budget_variance_total.budget %}</th>
							<th>{%= budget_variance_total.actual %}</th>
							<th class="variance-cell {%= budget_variance_total.variance_class %}">{%= budget_variance_total.variance %}</th>
							<th><div class="budget-indicator"><span class="indicator-pill {%= budget_variance_total.indicator_class %}">{%= budget_variance_total.indicator_label %}</span><small>{%= budget_variance_total.utilization %}</small></div></th>
						</tr>
					</tfoot>
				</table>
				{% else %}
				<div class="budget-empty-state">
					<i class="fa fa-chart-pie"></i>
					<p>{%= budget_variance_message %}</p>
				</div>
				{% endif %}
				<a href="#" data-budget-plan-link="1">View Budget Variance Report</a>
			</div>
			<div class="panel insight-panel">
				<h2><span class="spark"><i class="fa fa-sun"></i></span>AI Insight</h2>
				<div data-ai-insight-content="1">
					{% for insight in insights %}
					<p><i class="fa {%= insight.icon_class %} {%= insight.text_class %}"></i>{%= insight.text %}</p>
					{% endfor %}
				</div>
			</div>
		</section>
	</main>
</div>`,
	profit_and_loss: `<div class="accounts-dashboard theme-{%= current_theme || "standard" %}">
	<aside class="accounts-sidebar">
		<nav class="accounts-nav">
			<a href="#" data-route="finance"><i class="fa fa-home"></i><span>Finance</span></a>
			<a class="active" href="#" data-route="profit-and-loss"><i class="fa fa-landmark"></i><span>Profit and Loss</span></a>
			<a href="#" data-route="sales-dashboard"><i class="fa fa-file-invoice"></i><span>Sales</span></a>
			<a href="#" data-route="purchase-dashboard"><i class="fa fa-shopping-cart"></i><span>Purchase</span></a>
			<a href="#" data-route="stock-dashboard"><i class="fa fa-cubes"></i><span>Stock</span></a>
			<a href="#" data-route="hr-dashboard"><i class="fa fa-university"></i><span>HR</span></a>
			<a href="#" data-route="payroll-dashboard"><i class="fa fa-money"></i><span>Payroll</span></a>
			<a href="#" data-route="commissions-dashboard"><i class="fa fa-chart-bar"></i><span>Commissions</span></a>
			<a href="#" data-route="budget-dashboard"><i class="fa fa-clipboard"></i><span>Budget</span></a>
			<a href="#" data-route="tasks-dashboard"><i class="fa fa-sitemap"></i><span>Tasks</span></a>
		</nav>
	</aside>

	<main class="accounts-content">
		<header class="accounts-header">
			<div>
				<h1>Hospital Profit and Loss Dashboard</h1>
			</div>
			<div class="accounts-actions">
				<button class="theme-button" type="button"><i class="fa fa-paint-brush"></i><span>{%= current_theme_label || "Standard" %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="date-button"><i class="fa fa-calendar"></i><span>{%= date_range %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="filter-button"><i class="fa fa-filter"></i><span>Filters</span></button>
				<button class="refresh-button"><i class="fa fa-sync-alt"></i><span>Refresh</span></button>
				<button class="export-button"><i class="fa fa-download"></i><span>Export</span></button>
			</div>
		</header>

		<section class="table-row statement-only-row">
			<div class="panel statement-panel">
				<div class="statement-table-wrap">
					<table class="statement-table">
						<thead>
							<tr class="statement-head-top">
								<th rowspan="2">Particulars</th>
								<th colspan="2">Actual Period<br><small>{%= statement_table.actual_period_label %}</small></th>
								<th colspan="2">Compare With Period<br><small>{%= statement_table.previous_period_label %}</small></th>
							</tr>
							<tr class="statement-head-sub">
								<th>Amount ({%= statement_table.currency %})</th>
								<th>% of Revenue</th>
								<th>Amount ({%= statement_table.currency %})</th>
								<th>% of Revenue</th>
							</tr>
						</thead>
						<tbody>
							{% for row in statement_table.rows %}
							{% if row.row_type == "section" %}
							<tr class="statement-section-row">
								<td colspan="5">{%= row.label %}</td>
							</tr>
							{% else %}
							<tr class="statement-data-row statement-{%= row.row_type %} {%= row.is_collapsible_group ? "statement-group-row is-collapsed" : "" %}" data-indent="{%= row.indent || 0 %}" data-collapsible-group="{%= row.is_collapsible_group ? 1 : 0 %}">
								<td class="statement-label indent-{%= row.indent || 0 %} {%= row.is_group ? "is-group" : "" %}">
									{% if row.is_collapsible_group %}
									<button type="button" class="statement-toggle" aria-label="Toggle account group"><span class="statement-toggle-arrow">▸</span></button>
									{% endif %}
									<span>{%= row.label %}</span>
								</td>
								<td>
									<div class="statement-amount-row">
										<span>{%= row.current_amount %}</span>
									{% if row.current_trend %}
										<small class="statement-trend trend-{%= row.current_trend_class || "flat" %}">{%= row.current_trend %}</small>
									{% endif %}
									</div>
								</td>
								<td>{%= row.current_percent %}</td>
								<td>{%= row.previous_amount %}</td>
								<td>{%= row.previous_percent %}</td>
							</tr>
							{% endif %}
							{% endfor %}
						</tbody>
					</table>
				</div>
			</div>
		</section>

		<section class="bottom-row bottom-row--single">
			<div class="panel insight-panel">
				<h2><span class="spark"><i class="fa fa-sun"></i></span>AI Insight</h2>
				<div data-ai-insight-content="1">
					{% for insight in insights %}
					<p><i class="fa {%= insight.icon_class %} {%= insight.text_class %}"></i>{%= insight.text %}</p>
					{% endfor %}
				</div>
			</div>
		</section>
	</main>
</div>`,
	tasks_dashboard: `<div class="accounts-dashboard theme-{%= current_theme || "standard" %}">
	<aside class="accounts-sidebar">
		<nav class="accounts-nav">
			<a href="#" data-route="finance"><i class="fa fa-home"></i><span>Finance</span></a>
			<a href="#" data-route="profit-and-loss"><i class="fa fa-landmark"></i><span>Profit and Loss</span></a>
			<a href="#" data-route="sales-dashboard"><i class="fa fa-file-invoice"></i><span>Sales</span></a>
			<a href="#" data-route="purchase-dashboard"><i class="fa fa-shopping-cart"></i><span>Purchase</span></a>
			<a href="#" data-route="stock-dashboard"><i class="fa fa-cubes"></i><span>Stock</span></a>
			<a href="#" data-route="hr-dashboard"><i class="fa fa-university"></i><span>HR</span></a>
			<a href="#" data-route="payroll-dashboard"><i class="fa fa-money"></i><span>Payroll</span></a>
			<a href="#" data-route="commissions-dashboard"><i class="fa fa-chart-bar"></i><span>Commissions</span></a>
			<a href="#" data-route="budget-dashboard"><i class="fa fa-clipboard"></i><span>Budget</span></a>
			<a class="active" href="#" data-route="tasks-dashboard"><i class="fa fa-sitemap"></i><span>Tasks</span></a>
		</nav>
	</aside>

	<main class="accounts-content">
		<header class="accounts-header">
			<div>
				<h1>Hospital Tasks Dashboard</h1>
				<p>Cross-functional execution workload from Task, ToDo, and Department Audit records</p>
			</div>
			<div class="accounts-actions">
				<button class="theme-button" type="button"><i class="fa fa-paint-brush"></i><span>{%= current_theme_label || "Standard" %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="date-button"><i class="fa fa-calendar"></i><span>{%= date_range %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="filter-button"><i class="fa fa-filter"></i><span>Filters</span></button>
				<button class="refresh-button"><i class="fa fa-sync-alt"></i><span>Refresh</span></button>
				<button class="export-button"><i class="fa fa-download"></i><span>Export</span></button>
			</div>
		</header>

		<section class="metric-grid">
			{% for metric in metrics %}
			<div class="metric-card {%= metric.class %}">
				<div class="metric-icon">{%= metric.icon %}</div>
				<div>
					<span>{%= metric.label %}</span>
					<strong>{%= metric.value %}</strong>
					<small class="{%= metric.trend_class %}">{%= metric.trend %}</small>
					<em>vs {%= comparison_range %}</em>
				</div>
			</div>
			{% endfor %}
		</section>

		<section class="chart-row">
			<div class="panel income-expenses">
				<div class="panel-head">
					<h2>Work Opened vs Closed</h2>
					<div class="legend"><span class="green"></span>Opened <span class="red"></span>Closed</div>
				</div>
				<div class="bar-chart">
					<div class="plot">
						<div class="grid-lines"></div>
						{% for item in income_expenses %}
						<div class="bar-group">
							<div class="bar-stack">
								<span class="bar-column">
									<span class="bar-value income-value">{%= item.income_value %}</span>
									<span class="income-b" style="height: {%= item.income_height %}px;"></span>
								</span>
								<span class="bar-column">
									<span class="bar-value expense-value">{%= item.expense_value %}</span>
									<span class="expense-b" style="height: {%= item.expense_height %}px;"></span>
								</span>
							</div>
							<label>{%= item.label %}</label>
						</div>
						{% endfor %}
					</div>
				</div>
			</div>

			<div class="panel donut-panel">
				<h2>Task Status Mix</h2>
				<div class="donut-wrap">
					<div class="donut expense-donut" style="{%= expense_donut_style %}"></div>
					<ul class="chart-list">
						{% for category in expense_categories %}
						<li><span class="{%= category.class %}"></span>{%= category.label %} <b>{%= category.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>

			<div class="panel donut-panel source-panel">
				<h2>Work by Department</h2>
				<div class="donut-wrap">
					<div class="donut source-donut" style="{%= source_donut_style %}"></div>
					<ul class="chart-list">
						{% for source in income_sources %}
						<li><span class="{%= source.class %}"></span>{%= source.label %} <b>{%= source.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
		</section>

		<section class="table-row">
			<div class="panel table-panel accounts-table">
				<h2>Department Workload</h2>
				<table>
					<thead><tr><th>Department</th><th>Split</th><th>Open Work</th></tr></thead>
					<tbody>
						{% for row in account_balances %}
						<tr><td>{%= row.account %}</td><td>{%= row.type %}</td><td>{%= row.balance %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>Open Work</th><th>{%= account_balances_total %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View Departments</a>
			</div>

			<div class="panel table-panel">
				<h2>Assignee Queue</h2>
				<table>
					<thead><tr><th>Assignee</th><th>Open ToDos</th><th>Overdue</th></tr></thead>
					<tbody>
						{% for row in unpaid_invoices %}
						<tr><td>{%= row.customer_group %}</td><td>{%= row.customer_count %}</td><td>{%= row.outstanding %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>{%= unpaid_invoices_total.customer_count %}</th><th>{%= unpaid_invoices_total.outstanding %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View ToDos</a>
			</div>

			<div class="panel table-panel">
				<h2>Department Audit Summary</h2>
				<table>
					<thead><tr><th>Department</th><th>Status Mix</th><th>Checks</th></tr></thead>
					<tbody>
						{% for row in top_supplier_balances %}
						<tr><td>{%= row.supplier %}</td><td>{%= row.supplier_group %}</td><td>{%= row.balance %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>Audit Checks</th><th>{%= top_supplier_balances_total %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View Department Audits</a>
			</div>
		</section>

		<section class="bottom-row">
			<div class="panel table-panel budget-variance-panel">
				<h2>Department Workload Variance</h2>
				{% if budget_variance.length %}
				<table>
					<thead><tr><th>Department</th><th>Current</th><th>Previous</th><th>Variance</th><th>Direction</th></tr></thead>
					<tbody>
						{% for row in budget_variance %}
						<tr>
							<td>{%= row.category %}</td>
							<td>{%= row.budget %}</td>
							<td>{%= row.actual %}</td>
							<td class="variance-cell {%= row.variance_class %}">{%= row.variance %}</td>
							<td><div class="budget-indicator"><span class="indicator-pill {%= row.indicator_class %}">{%= row.indicator_label %}</span><small>{%= row.utilization %}</small></div></td>
						</tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr>
							<th>Total</th>
							<th>{%= budget_variance_total.budget %}</th>
							<th>{%= budget_variance_total.actual %}</th>
							<th class="variance-cell {%= budget_variance_total.variance_class %}">{%= budget_variance_total.variance %}</th>
							<th><div class="budget-indicator"><span class="indicator-pill {%= budget_variance_total.indicator_class %}">{%= budget_variance_total.indicator_label %}</span><small>{%= budget_variance_total.utilization %}</small></div></th>
						</tr>
					</tfoot>
				</table>
				{% else %}
				<div class="budget-empty-state">
					<i class="fa fa-chart-pie"></i>
					<p>{%= budget_variance_message %}</p>
				</div>
				{% endif %}
				<a href="#" data-budget-plan-link="1">Open Task List</a>
			</div>

			<div class="panel insight-panel">
				<h2><span class="spark"><i class="fa fa-sun"></i></span>AI Insight</h2>
				<div data-ai-insight-content="1">
					{% for insight in insights %}
					<p><i class="fa {%= insight.icon_class %} {%= insight.text_class %}"></i>{%= insight.text %}</p>
					{% endfor %}
				</div>
			</div>
		</section>
	</main>
</div>`,
	sales_dashboard: `<div class="accounts-dashboard theme-{%= current_theme || "standard" %}">
	<aside class="accounts-sidebar">
		<nav class="accounts-nav">
			<a class="active" href="#"><i class="fa fa-home"></i><span>Sales Overview</span></a>
			<a href="#"><i class="fa fa-user-md"></i><span>Doctors</span></a>
			<a href="#"><i class="fa fa-hospital-o"></i><span>Departments</span></a>
			<a href="#"><i class="fa fa-bed"></i><span>Admissions</span></a>
			<a href="#"><i class="fa fa-cubes"></i><span>Item Groups</span></a>
			<a href="#"><i class="fa fa-users"></i><span>Patients</span></a>
			<a href="#"><i class="fa fa-credit-card"></i><span>Payers</span></a>
			<a href="#"><i class="fa fa-line-chart"></i><span>Collections</span></a>
			<a href="#"><i class="fa fa-list"></i><span>Invoices</span></a>
			<a href="#"><i class="fa fa-sitemap"></i><span>Operational Mix</span></a>
		</nav>
	</aside>
	<main class="accounts-content">
		<header class="accounts-header">
			<div>
				<h1>Hospital Sales Dashboard</h1>
				<p>Doctor, pharmacy vs hospital, admission, and item-group sales performance</p>
			</div>
			<div class="accounts-actions">
				<button class="theme-button" type="button"><i class="fa fa-paint-brush"></i><span>{%= current_theme_label || "Standard" %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="date-button"><i class="fa fa-calendar"></i><span>{%= date_range %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="filter-button"><i class="fa fa-filter"></i><span>Filters</span></button>
				<button class="refresh-button"><i class="fa fa-sync-alt"></i><span>Refresh</span></button>
				<button class="export-button"><i class="fa fa-download"></i><span>Export</span></button>
			</div>
		</header>
		<section class="metric-grid">
			{% for metric in metrics %}
			<div class="metric-card {%= metric.class %}">
				<div class="metric-icon">{%= metric.icon %}</div>
				<div>
					<span>{%= metric.label %}</span>
					<strong>{%= metric.value %}</strong>
					<small class="{%= metric.trend_class %}">{%= metric.trend %}</small>
					<em>vs {%= comparison_range %}</em>
				</div>
			</div>
			{% endfor %}
		</section>
		<section class="chart-row">
			<div class="panel income-expenses">
				<div class="panel-head">
					<h2>Sales vs Collections</h2>
					<div class="legend"><span class="green"></span>Sales <span class="red"></span>Collections</div>
				</div>
				<div class="bar-chart">
					<div class="plot">
						<div class="grid-lines"></div>
						{% for item in income_expenses %}
						<div class="bar-group">
							<div class="bar-stack">
								<span class="bar-column">
									<span class="bar-value income-value">{%= item.income_value %}</span>
									<span class="income-b" style="height: {%= item.income_height %}px;"></span>
								</span>
								<span class="bar-column">
									<span class="bar-value expense-value">{%= item.expense_value %}</span>
									<span class="expense-b" style="height: {%= item.expense_height %}px;"></span>
								</span>
							</div>
							<label>{%= item.label %}</label>
						</div>
						{% endfor %}
					</div>
				</div>
			</div>
			<div class="panel donut-panel">
				<h2>Sales by Pharmacy and Hospital</h2>
				<div class="donut-wrap">
					<div class="donut expense-donut" style="{%= expense_donut_style %}"></div>
					<ul class="chart-list">
						{% for category in expense_categories %}
						<li><span class="{%= category.class %}"></span>{%= category.label %} <b>{%= category.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
			<div class="panel donut-panel source-panel">
				<h2>Sales by Inpatient Type</h2>
				<div class="donut-wrap">
					<div class="donut source-donut" style="{%= source_donut_style %}"></div>
					<ul class="chart-list">
						{% for source in income_sources %}
						<li><span class="{%= source.class %}"></span>{%= source.label %} <b>{%= source.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
		</section>
		<section class="table-row">
			<div class="panel table-panel department-performance-panel">
				<div class="table-panel-head">
					<h2>Performance</h2>
					<div class="performance-toggle" role="tablist" aria-label="Performance View">
						<button type="button" class="is-active" data-performance-toggle="doctor">Doctor</button>
						<button type="button" data-performance-toggle="department">Department</button>
					</div>
				</div>
				<div class="performance-table-view is-active" data-performance-panel="doctor">
					<div class="table-row-limit-panel" data-row-limit-panel="10">
					<table>
						<thead>
							<tr>
								<th>{%= performance_views.doctor.entity_label %}</th>
								<th>Net Sales ($)</th>
								<th>% of Total Sales</th>
								<th>OPD</th>
								{% for column in performance_views.doctor.ipd_type_columns %}
								<th>{%= column.label %}</th>
								{% endfor %}
							</tr>
						</thead>
						<tbody>
							{% for row in performance_views.doctor.rows %}
							{% if row.is_over_limit %}
							<tr class="is-over-limit">
							{% else %}
							<tr>
							{% endif %}
								<td>{%= row.doctor %}</td>
								<td>{%= row.net_sales %}</td>
								<td>{%= row.sales_share %}</td>
								<td>{%= row.opd_sales %}</td>
								{% for value in row.ipd_type_values %}
								<td>{%= value %}</td>
								{% endfor %}
							</tr>
							{% endfor %}
						</tbody>
						<tfoot>
							<tr>
								<th>Total</th>
								<th>{%= performance_views.doctor.total.outstanding %}</th>
								<th>100.0%</th>
								<th>{%= performance_views.doctor.total.opd_sales %}</th>
								{% for value in performance_views.doctor.total.ipd_type_values %}
								<th>{%= value %}</th>
								{% endfor %}
							</tr>
						</tfoot>
					</table>
					{% if performance_views.doctor.has_more %}
					<button type="button" class="table-expand-link" data-table-expand="1" data-expand-label="View All Doctors" data-collapse-label="Show Less">View All Doctors</button>
					{% endif %}
					</div>
				</div>
				<div class="performance-table-view" data-performance-panel="department">
					<div class="table-row-limit-panel" data-row-limit-panel="10">
					<table>
						<thead>
							<tr>
								<th>{%= performance_views.department.entity_label %}</th>
								<th>Net Sales ($)</th>
								<th>% of Total Sales</th>
								<th>OPD</th>
								{% for column in performance_views.department.ipd_type_columns %}
								<th>{%= column.label %}</th>
								{% endfor %}
							</tr>
						</thead>
						<tbody>
							{% for row in performance_views.department.rows %}
							{% if row.is_over_limit %}
							<tr class="is-over-limit">
							{% else %}
							<tr>
							{% endif %}
								<td>{%= row.department %}</td>
								<td>{%= row.net_sales %}</td>
								<td>{%= row.sales_share %}</td>
								<td>{%= row.opd_sales %}</td>
								{% for value in row.ipd_type_values %}
								<td>{%= value %}</td>
								{% endfor %}
							</tr>
							{% endfor %}
						</tbody>
						<tfoot>
							<tr>
								<th>Total</th>
								<th>{%= performance_views.department.total.outstanding %}</th>
								<th>100.0%</th>
								<th>{%= performance_views.department.total.opd_sales %}</th>
								{% for value in performance_views.department.total.ipd_type_values %}
								<th>{%= value %}</th>
								{% endfor %}
							</tr>
						</tfoot>
					</table>
					{% if performance_views.department.has_more %}
					<button type="button" class="table-expand-link" data-table-expand="1" data-expand-label="View All Departments" data-collapse-label="Show Less">View All Departments</button>
					{% endif %}
					</div>
				</div>
			</div>
			<div class="panel table-panel">
				<h2>Admission Contribution</h2>
				<div class="table-row-limit-panel" data-row-limit-panel="10">
				<table>
					<thead><tr><th>Admission</th><th>Patients</th><th>Net Sales ($)</th></tr></thead>
					<tbody>
						{% for row in top_supplier_balances %}
						{% if row.is_over_limit %}
						<tr class="is-over-limit">
						{% else %}
						<tr>
						{% endif %}
							<td>{%= row.supplier %}</td><td>{%= row.supplier_group %}</td><td>{%= row.balance %}</td>
						</tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>All Patients</th><th>{%= top_supplier_balances_total %}</th></tr>
					</tfoot>
				</table>
				{% if top_supplier_balances_has_more %}
				<button type="button" class="table-expand-link" data-table-expand="1" data-expand-label="View All Admissions" data-collapse-label="Show Less">View All Admissions</button>
				{% endif %}
				</div>
			</div>
		</section>
		<section class="bottom-row">
			<div class="panel table-panel budget-variance-panel">
				<div class="table-panel-head">
					<h2>Item Group Performance</h2>
					<div class="performance-toggle" role="tablist" aria-label="Item Group View">
						<button type="button" class="is-active" data-item-group-toggle="summary">Summary</button>
						<button type="button" data-item-group-toggle="doctor_matrix">Doctor View</button>
					</div>
				</div>
				{% if budget_variance.length %}
				<div class="item-group-table-view is-active" data-item-group-panel="summary">
					<div class="table-row-limit-panel" data-row-limit-panel="10">
					<table>
						<thead><tr><th>Item Group</th><th>Invoices</th><th>Qty</th><th>Revenue</th><th>Mix</th></tr></thead>
						<tbody>
							{% for row in budget_variance %}
							{% if row.is_over_limit %}
							<tr class="is-over-limit">
							{% else %}
							<tr>
							{% endif %}
								<td>{%= row.category %}</td>
								<td>{%= row.budget %}</td>
								<td>{%= row.actual %}</td>
								<td class="variance-cell {%= row.variance_class %}">{%= row.variance %}</td>
								<td><div class="budget-indicator"><span class="indicator-pill {%= row.indicator_class %}">{%= row.indicator_label %}</span><small>{%= row.utilization %}</small></div></td>
							</tr>
							{% endfor %}
						</tbody>
						<tfoot>
							<tr>
								<th>Total</th>
								<th>{%= budget_variance_total.budget %}</th>
								<th>{%= budget_variance_total.actual %}</th>
								<th class="variance-cell {%= budget_variance_total.variance_class %}">{%= budget_variance_total.variance %}</th>
								<th><div class="budget-indicator"><span class="indicator-pill {%= budget_variance_total.indicator_class %}">{%= budget_variance_total.indicator_label %}</span><small>{%= budget_variance_total.utilization %}</small></div></th>
							</tr>
						</tfoot>
					</table>
					{% if item_group_views.summary.has_more %}
					<button type="button" class="table-expand-link" data-table-expand="1" data-expand-label="View All Item Groups" data-collapse-label="Show Less">View All Item Groups</button>
					{% endif %}
					</div>
				</div>
				<div class="item-group-table-view" data-item-group-panel="doctor_matrix">
					<div class="table-row-limit-panel" data-row-limit-panel="10">
					<table class="doctor-item-group-table">
						<thead>
							<tr>
								<th>{%= item_group_views.doctor_matrix.entity_label %}</th>
								{% for column in item_group_views.doctor_matrix.columns %}
								<th>{%= column.label %}</th>
								{% endfor %}
								<th>Total</th>
							</tr>
						</thead>
						<tbody>
							{% for row in item_group_views.doctor_matrix.rows %}
							{% if row.is_over_limit %}
							<tr class="is-over-limit">
							{% else %}
							<tr>
							{% endif %}
								<td>{%= row.doctor %}</td>
								{% for value in row.item_group_values %}
								<td>{%= value %}</td>
								{% endfor %}
								<td>{%= row.total_amount %}</td>
							</tr>
							{% endfor %}
						</tbody>
						<tfoot>
							<tr>
								<th>Total</th>
								{% for value in item_group_views.doctor_matrix.total.item_group_values %}
								<th>{%= value %}</th>
								{% endfor %}
								<th>{%= item_group_views.doctor_matrix.total.total_amount %}</th>
							</tr>
						</tfoot>
					</table>
					{% if item_group_views.doctor_matrix.has_more %}
					<button type="button" class="table-expand-link" data-table-expand="1" data-expand-label="View All Doctors" data-collapse-label="Show Less">View All Doctors</button>
					{% endif %}
					</div>
				</div>
				{% else %}
				<div class="budget-empty-state">
					<i class="fa fa-chart-pie"></i>
					<p>{%= budget_variance_message %}</p>
				</div>
				{% endif %}
			</div>
			<div class="panel insight-panel">
				<h2><span class="spark"><i class="fa fa-sun"></i></span>AI Insight</h2>
				<div data-ai-insight-content="1">
					{% for insight in insights %}
					<p><i class="fa {%= insight.icon_class %} {%= insight.text_class %}"></i>{%= insight.text %}</p>
					{% endfor %}
				</div>
			</div>
		</section>
	</main>
</div>`,
	payroll_dashboard: `<div class="accounts-dashboard theme-{%= current_theme || "standard" %}">
	<aside class="accounts-sidebar">
		<nav class="accounts-nav">
			<a class="active" href="#"><i class="fa fa-money"></i><span>Payroll Overview</span></a>
			<a href="#"><i class="fa fa-sitemap"></i><span>Departments</span></a>
			<a href="#"><i class="fa fa-file-text-o"></i><span>Salary Slips</span></a>
			<a href="#"><i class="fa fa-credit-card"></i><span>Net Pay</span></a>
			<a href="#"><i class="fa fa-minus-circle"></i><span>Deductions</span></a>
			<a href="#"><i class="fa fa-users"></i><span>Employees Paid</span></a>
			<a href="#"><i class="fa fa-list-alt"></i><span>Payroll Entries</span></a>
			<a href="#"><i class="fa fa-clock-o"></i><span>Payment Days</span></a>
			<a href="#"><i class="fa fa-list"></i><span>Statuses</span></a>
			<a href="#"><i class="fa fa-pie-chart"></i><span>Payout Mix</span></a>
		</nav>
	</aside>
	<main class="accounts-content">
		<header class="accounts-header">
			<div>
				<h1>Hospital Payroll Dashboard</h1>
				<p>Gross pay, deductions, net pay, payroll status, and employee payout performance</p>
			</div>
			<div class="accounts-actions">
				<button class="theme-button" type="button"><i class="fa fa-paint-brush"></i><span>{%= current_theme_label || "Standard" %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="date-button"><i class="fa fa-calendar"></i><span>{%= date_range %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="filter-button"><i class="fa fa-filter"></i><span>Filters</span></button>
				<button class="refresh-button"><i class="fa fa-sync-alt"></i><span>Refresh</span></button>
				<button class="export-button"><i class="fa fa-download"></i><span>Export</span></button>
			</div>
		</header>
		<section class="metric-grid">
			{% for metric in metrics %}
			<div class="metric-card {%= metric.class %}">
				<div class="metric-icon">{%= metric.icon %}</div>
				<div>
					<span>{%= metric.label %}</span>
					<strong>{%= metric.value %}</strong>
					<small class="{%= metric.trend_class %}">{%= metric.trend %}</small>
					<em>vs {%= comparison_range %}</em>
				</div>
			</div>
			{% endfor %}
		</section>
		<section class="chart-row">
			<div class="panel income-expenses">
				<div class="panel-head">
					<h2>Gross vs Net Payroll</h2>
					<div class="legend"><span class="green"></span>Gross <span class="red"></span>Net</div>
				</div>
				<div class="bar-chart">
					<div class="plot">
						<div class="grid-lines"></div>
						{% for item in income_expenses %}
						<div class="bar-group">
							<div class="bar-stack">
								<span class="bar-column">
									<span class="bar-value income-value">{%= item.income_value %}</span>
									<span class="income-b" style="height: {%= item.income_height %}px;"></span>
								</span>
								<span class="bar-column">
									<span class="bar-value expense-value">{%= item.expense_value %}</span>
									<span class="expense-b" style="height: {%= item.expense_height %}px;"></span>
								</span>
							</div>
							<label>{%= item.label %}</label>
						</div>
						{% endfor %}
					</div>
				</div>
			</div>
			<div class="panel donut-panel">
				<h2>Payroll by Department</h2>
				<div class="donut-wrap">
					<div class="donut expense-donut" style="{%= expense_donut_style %}"></div>
					<ul class="chart-list">
						{% for category in expense_categories %}
						<li><span class="{%= category.class %}"></span>{%= category.label %} <b>{%= category.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
			<div class="panel donut-panel source-panel">
				<h2>Payroll by Slip Status</h2>
				<div class="donut-wrap">
					<div class="donut source-donut" style="{%= source_donut_style %}"></div>
					<ul class="chart-list">
						{% for source in income_sources %}
						<li><span class="{%= source.class %}"></span>{%= source.label %} <b>{%= source.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
		</section>
		<section class="table-row">
			<div class="panel table-panel accounts-table">
				<h2>Department Payroll</h2>
				<table>
					<thead><tr><th>Department</th><th>Designation Mix</th><th>Net Payroll</th></tr></thead>
					<tbody>
						{% for row in account_balances %}
						<tr><td>{%= row.account %}</td><td>{%= row.type %}</td><td>{%= row.balance %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>Top Departments</th><th>{%= account_balances_total %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View Department Payroll</a>
			</div>
			<div class="panel table-panel">
				<h2>Salary Slip Status</h2>
				<table>
					<thead><tr><th>Status</th><th>Slips</th><th>Net Payroll</th></tr></thead>
					<tbody>
						{% for row in unpaid_invoices %}
						<tr><td>{%= row.customer_group %}</td><td>{%= row.customer_count %}</td><td>{%= row.outstanding %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>{%= unpaid_invoices_total.customer_count %}</th><th>{%= unpaid_invoices_total.outstanding %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View Salary Slip Status</a>
			</div>
			<div class="panel table-panel">
				<h2>Payroll Entry Status</h2>
				<table>
					<thead><tr><th>Status</th><th>Entries</th><th>Employees</th></tr></thead>
					<tbody>
						{% for row in top_supplier_balances %}
						<tr><td>{%= row.supplier %}</td><td>{%= row.supplier_group %}</td><td>{%= row.balance %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>All Statuses</th><th>{%= top_supplier_balances_total %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View Payroll Entries</a>
			</div>
		</section>
		<section class="bottom-row">
			<div class="panel table-panel budget-variance-panel">
				<h2>Top Employee Payouts</h2>
				{% if budget_variance.length %}
				<table>
					<thead><tr><th>Employee</th><th>Slips</th><th>Payment Days</th><th>Net Payroll</th><th>Share</th></tr></thead>
					<tbody>
						{% for row in budget_variance %}
						<tr>
							<td>{%= row.category %}</td>
							<td>{%= row.budget %}</td>
							<td>{%= row.actual %}</td>
							<td class="variance-cell {%= row.variance_class %}">{%= row.variance %}</td>
							<td><div class="budget-indicator"><span class="indicator-pill {%= row.indicator_class %}">{%= row.indicator_label %}</span><small>{%= row.utilization %}</small></div></td>
						</tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr>
							<th>Total</th>
							<th>{%= budget_variance_total.budget %}</th>
							<th>{%= budget_variance_total.actual %}</th>
							<th class="variance-cell {%= budget_variance_total.variance_class %}">{%= budget_variance_total.variance %}</th>
							<th><div class="budget-indicator"><span class="indicator-pill {%= budget_variance_total.indicator_class %}">{%= budget_variance_total.indicator_label %}</span><small>{%= budget_variance_total.utilization %}</small></div></th>
						</tr>
					</tfoot>
				</table>
				{% else %}
				<div class="budget-empty-state">
					<i class="fa fa-chart-pie"></i>
					<p>{%= budget_variance_message %}</p>
				</div>
				{% endif %}
				<a href="#" data-budget-plan-link="1">View Payroll Detail Report</a>
			</div>
			<div class="panel insight-panel">
				<h2><span class="spark"><i class="fa fa-sun"></i></span>AI Insight</h2>
				<div data-ai-insight-content="1">
					{% for insight in insights %}
					<p><i class="fa {%= insight.icon_class %} {%= insight.text_class %}"></i>{%= insight.text %}</p>
					{% endfor %}
				</div>
			</div>
		</section>
	</main>
</div>`,
	commissions_dashboard: `<div class="accounts-dashboard theme-{%= current_theme || "standard" %}">
	<aside class="accounts-sidebar">
		<nav class="accounts-nav">
			<a href="#" data-route="finance"><i class="fa fa-home"></i><span>Finance</span></a>
			<a href="#" data-route="profit-and-loss"><i class="fa fa-landmark"></i><span>Profit and Loss</span></a>
			<a href="#" data-route="sales-dashboard"><i class="fa fa-file-invoice"></i><span>Sales</span></a>
			<a href="#" data-route="purchase-dashboard"><i class="fa fa-shopping-cart"></i><span>Purchase</span></a>
			<a href="#" data-route="stock-dashboard"><i class="fa fa-cubes"></i><span>Stock</span></a>
			<a href="#" data-route="hr-dashboard"><i class="fa fa-university"></i><span>HR</span></a>
			<a href="#" data-route="payroll-dashboard"><i class="fa fa-money"></i><span>Payroll</span></a>
			<a class="active" href="#" data-route="commissions-dashboard"><i class="fa fa-chart-bar"></i><span>Commissions</span></a>
			<a href="#" data-route="budget-dashboard"><i class="fa fa-clipboard"></i><span>Budget</span></a>
			<a href="#" data-route="tasks-dashboard"><i class="fa fa-sitemap"></i><span>Tasks</span></a>
		</nav>
	</aside>
	<main class="accounts-content">
		<header class="accounts-header">
			<div>
				<h1>Hospital Commissions Dashboard</h1>
				<p>Doctor commission sales, salary slip commission lines, commission accounts, and payout concentration</p>
			</div>
			<div class="accounts-actions">
				<button class="theme-button" type="button"><i class="fa fa-paint-brush"></i><span>{%= current_theme_label || "Standard" %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="date-button"><i class="fa fa-calendar"></i><span>{%= date_range %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="filter-button"><i class="fa fa-filter"></i><span>Filters</span></button>
				<button class="refresh-button"><i class="fa fa-sync-alt"></i><span>Refresh</span></button>
				<button class="export-button"><i class="fa fa-download"></i><span>Export</span></button>
			</div>
		</header>
		<section class="metric-grid">
			{% for metric in metrics %}
			<div class="metric-card {%= metric.class %}">
				<div class="metric-icon">{%= metric.icon %}</div>
				<div>
					<span>{%= metric.label %}</span>
					<strong>{%= metric.value %}</strong>
					<small class="{%= metric.trend_class %}">{%= metric.trend %}</small>
					<em>vs {%= comparison_range %}</em>
				</div>
			</div>
			{% endfor %}
		</section>
		<section class="chart-row">
			<div class="panel income-expenses">
				<div class="panel-head">
					<h2>Gross Sales vs Net Commission</h2>
					<div class="legend"><span class="green"></span>Gross Sales <span class="red"></span>Net Commission</div>
				</div>
				<div class="bar-chart">
					<div class="plot">
						<div class="grid-lines"></div>
						{% for item in income_expenses %}
						<div class="bar-group">
							<div class="bar-stack">
								<span class="bar-column">
									<span class="bar-value income-value">{%= item.income_value %}</span>
									<span class="income-b" style="height: {%= item.income_height %}px;"></span>
								</span>
								<span class="bar-column">
									<span class="bar-value expense-value">{%= item.expense_value %}</span>
									<span class="expense-b" style="height: {%= item.expense_height %}px;"></span>
								</span>
							</div>
							<label>{%= item.label %}</label>
						</div>
						{% endfor %}
					</div>
				</div>
			</div>
			<div class="panel donut-panel">
				<h2>Commission by Department</h2>
				<div class="donut-wrap">
					<div class="donut expense-donut" style="{%= expense_donut_style %}"></div>
					<ul class="chart-list">
						{% for category in expense_categories %}
						<li><span class="{%= category.class %}"></span>{%= category.label %} <b>{%= category.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
			<div class="panel donut-panel source-panel">
				<h2>Commission by Item Group</h2>
				<div class="donut-wrap">
					<div class="donut source-donut" style="{%= source_donut_style %}"></div>
					<ul class="chart-list">
						{% for source in income_sources %}
						<li><span class="{%= source.class %}"></span>{%= source.label %} <b>{%= source.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
		</section>
		<section class="table-row">
			<div class="panel table-panel accounts-table">
				<h2>Commission Accounts</h2>
				<table>
					<thead><tr><th>Account</th><th>Type</th><th>Debit</th></tr></thead>
					<tbody>
						{% for row in account_balances %}
						<tr><td>{%= row.account %}</td><td>{%= row.type %}</td><td>{%= row.balance %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>Commission Debit</th><th>{%= account_balances_total %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View Commission Accounts</a>
			</div>
			<div class="panel table-panel">
				<h2>Salary Slip Commission Status</h2>
				<table>
					<thead><tr><th>Status</th><th>Slips</th><th>Commission</th></tr></thead>
					<tbody>
						{% for row in unpaid_invoices %}
						<tr><td>{%= row.customer_group %}</td><td>{%= row.customer_count %}</td><td>{%= row.outstanding %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>{%= unpaid_invoices_total.customer_count %}</th><th>{%= unpaid_invoices_total.outstanding %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View Salary Slip Commissions</a>
			</div>
			<div class="panel table-panel">
				<h2>Doctor Commission Summary</h2>
				<table>
					<thead><tr><th>Doctor</th><th>Department</th><th>Net Commission</th></tr></thead>
					<tbody>
						{% for row in top_supplier_balances %}
						<tr><td>{%= row.supplier %}</td><td>{%= row.supplier_group %}</td><td>{%= row.balance %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>Top Doctors</th><th>{%= top_supplier_balances_total %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View Doctor Commissions</a>
			</div>
		</section>
		<section class="bottom-row">
			<div class="panel table-panel budget-variance-panel">
				<h2>Top Doctor Commission Share</h2>
				{% if budget_variance.length %}
				<table>
					<thead><tr><th>Doctor</th><th>Invoices</th><th>Item Groups</th><th>Net Commission</th><th>Share</th></tr></thead>
					<tbody>
						{% for row in budget_variance %}
						<tr>
							<td>{%= row.category %}</td>
							<td>{%= row.budget %}</td>
							<td>{%= row.actual %}</td>
							<td class="variance-cell {%= row.variance_class %}">{%= row.variance %}</td>
							<td><div class="budget-indicator"><span class="indicator-pill {%= row.indicator_class %}">{%= row.indicator_label %}</span><small>{%= row.utilization %}</small></div></td>
						</tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr>
							<th>Total</th>
							<th>{%= budget_variance_total.budget %}</th>
							<th>{%= budget_variance_total.actual %}</th>
							<th class="variance-cell {%= budget_variance_total.variance_class %}">{%= budget_variance_total.variance %}</th>
							<th><div class="budget-indicator"><span class="indicator-pill {%= budget_variance_total.indicator_class %}">{%= budget_variance_total.indicator_label %}</span><small>{%= budget_variance_total.utilization %}</small></div></th>
						</tr>
					</tfoot>
				</table>
				{% else %}
				<div class="budget-empty-state">
					<i class="fa fa-chart-pie"></i>
					<p>{%= budget_variance_message %}</p>
				</div>
				{% endif %}
				<a href="#" data-budget-plan-link="1">View Doctors Net Commission Report</a>
			</div>
			<div class="panel insight-panel">
				<h2><span class="spark"><i class="fa fa-sun"></i></span>AI Insight</h2>
				<div data-ai-insight-content="1">
					{% for insight in insights %}
					<p><i class="fa {%= insight.icon_class %} {%= insight.text_class %}"></i>{%= insight.text %}</p>
					{% endfor %}
				</div>
			</div>
		</section>
	</main>
</div>`,
	budget_dashboard: `<div class="accounts-dashboard theme-{%= current_theme || "standard" %}">
	<aside class="accounts-sidebar">
		<nav class="accounts-nav">
			<a href="#" data-route="finance"><i class="fa fa-home"></i><span>Finance</span></a>
			<a href="#" data-route="profit-and-loss"><i class="fa fa-landmark"></i><span>Profit and Loss</span></a>
			<a href="#" data-route="sales-dashboard"><i class="fa fa-file-invoice"></i><span>Sales</span></a>
			<a href="#" data-route="purchase-dashboard"><i class="fa fa-shopping-cart"></i><span>Purchase</span></a>
			<a href="#" data-route="stock-dashboard"><i class="fa fa-cubes"></i><span>Stock</span></a>
			<a href="#" data-route="hr-dashboard"><i class="fa fa-university"></i><span>HR</span></a>
			<a href="#" data-route="payroll-dashboard"><i class="fa fa-money"></i><span>Payroll</span></a>
			<a href="#" data-route="commissions-dashboard"><i class="fa fa-chart-bar"></i><span>Commissions</span></a>
			<a class="active" href="#" data-route="budget-dashboard"><i class="fa fa-clipboard"></i><span>Budget</span></a>
			<a href="#" data-route="tasks-dashboard"><i class="fa fa-sitemap"></i><span>Tasks</span></a>
		</nav>
	</aside>
	<main class="accounts-content">
		<header class="accounts-header">
			<div>
				<h1>Hospital Budget Dashboard</h1>
				<p>Budget plans, actual transactions, utilization, and variance performance across budget accounts</p>
			</div>
			<div class="accounts-actions">
				<button class="theme-button" type="button"><i class="fa fa-paint-brush"></i><span>{%= current_theme_label || "Standard" %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="date-button"><i class="fa fa-calendar"></i><span>{%= date_range %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="filter-button"><i class="fa fa-filter"></i><span>Filters</span></button>
				<button class="refresh-button"><i class="fa fa-sync-alt"></i><span>Refresh</span></button>
				<button class="export-button"><i class="fa fa-download"></i><span>Export</span></button>
			</div>
		</header>
		<section class="metric-grid">
			{% for metric in metrics %}
			<div class="metric-card {%= metric.class %}">
				<div class="metric-icon">{%= metric.icon %}</div>
				<div>
					<span>{%= metric.label %}</span>
					<strong>{%= metric.value %}</strong>
					<small class="{%= metric.trend_class %}">{%= metric.trend %}</small>
					<em>vs {%= comparison_range %}</em>
				</div>
			</div>
			{% endfor %}
		</section>
		<section class="chart-row">
			<div class="panel income-expenses">
				<div class="panel-head">
					<h2>Budget vs Actual</h2>
					<div class="legend"><span class="green"></span>Budget <span class="red"></span>Actual</div>
				</div>
				<div class="bar-chart">
					<div class="plot">
						<div class="grid-lines"></div>
						{% for item in income_expenses %}
						<div class="bar-group">
							<div class="bar-stack">
								<span class="bar-column">
									<span class="bar-value income-value">{%= item.income_value %}</span>
									<span class="income-b" style="height: {%= item.income_height %}px;"></span>
								</span>
								<span class="bar-column">
									<span class="bar-value expense-value">{%= item.expense_value %}</span>
									<span class="expense-b" style="height: {%= item.expense_height %}px;"></span>
								</span>
							</div>
							<label>{%= item.label %}</label>
						</div>
						{% endfor %}
					</div>
				</div>
			</div>
			<div class="panel donut-panel">
				<h2>Budget by Category</h2>
				<div class="donut-wrap">
					<div class="donut expense-donut" style="{%= expense_donut_style %}"></div>
					<ul class="chart-list">
						{% for category in expense_categories %}
						<li><span class="{%= category.class %}"></span>{%= category.label %} <b>{%= category.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
			<div class="panel donut-panel source-panel">
				<h2>Actual by Budget Type</h2>
				<div class="donut-wrap">
					<div class="donut source-donut" style="{%= source_donut_style %}"></div>
					<ul class="chart-list">
						{% for source in income_sources %}
						<li><span class="{%= source.class %}"></span>{%= source.label %} <b>{%= source.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
		</section>
		<section class="table-row">
			<div class="panel table-panel accounts-table">
				<h2>Budget Account Allocation</h2>
				<table>
					<thead><tr><th>Account</th><th>Type</th><th>Budget</th></tr></thead>
					<tbody>
						{% for row in account_balances %}
						<tr><td>{%= row.account %}</td><td>{%= row.type %}</td><td>{%= row.balance %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>Top Accounts</th><th>{%= account_balances_total %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View Budget Accounts</a>
			</div>
			<div class="panel table-panel">
				<h2>Category Actuals</h2>
				<table>
					<thead><tr><th>Category</th><th>Accounts</th><th>Actual</th></tr></thead>
					<tbody>
						{% for row in unpaid_invoices %}
						<tr><td>{%= row.customer_group %}</td><td>{%= row.customer_count %}</td><td>{%= row.outstanding %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>{%= unpaid_invoices_total.customer_count %}</th><th>{%= unpaid_invoices_total.outstanding %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View Category Actuals</a>
			</div>
			<div class="panel table-panel">
				<h2>Budget Plan Summary</h2>
				<table>
					<thead><tr><th>Plan</th><th>Type</th><th>Budget</th></tr></thead>
					<tbody>
						{% for row in top_supplier_balances %}
						<tr><td>{%= row.supplier %}</td><td>{%= row.supplier_group %}</td><td>{%= row.balance %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>Active Plans</th><th>{%= top_supplier_balances_total %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View Budget Plans</a>
			</div>
		</section>
		<section class="bottom-row">
			<div class="panel table-panel budget-variance-panel">
				<h2>Budget Variance</h2>
				{% if budget_variance.length %}
				<table>
					<thead><tr><th>Account</th><th>Budget</th><th>Actual</th><th>Variance</th><th>Utilization</th></tr></thead>
					<tbody>
						{% for row in budget_variance %}
						<tr>
							<td>{%= row.category %}</td>
							<td>{%= row.budget %}</td>
							<td>{%= row.actual %}</td>
							<td class="variance-cell {%= row.variance_class %}">{%= row.variance %}</td>
							<td><div class="budget-indicator"><span class="indicator-pill {%= row.indicator_class %}">{%= row.indicator_label %}</span><small>{%= row.utilization %}</small></div></td>
						</tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr>
							<th>Total</th>
							<th>{%= budget_variance_total.budget %}</th>
							<th>{%= budget_variance_total.actual %}</th>
							<th class="variance-cell {%= budget_variance_total.variance_class %}">{%= budget_variance_total.variance %}</th>
							<th><div class="budget-indicator"><span class="indicator-pill {%= budget_variance_total.indicator_class %}">{%= budget_variance_total.indicator_label %}</span><small>{%= budget_variance_total.utilization %}</small></div></th>
						</tr>
					</tfoot>
				</table>
				{% else %}
				<div class="budget-empty-state">
					<i class="fa fa-chart-pie"></i>
					<p>{%= budget_variance_message %}</p>
				</div>
				{% endif %}
				<a href="#" data-budget-plan-link="1">View Monthly Budget Plan</a>
			</div>
			<div class="panel insight-panel">
				<h2><span class="spark"><i class="fa fa-sun"></i></span>AI Insight</h2>
				<div data-ai-insight-content="1">
					{% for insight in insights %}
					<p><i class="fa {%= insight.icon_class %} {%= insight.text_class %}"></i>{%= insight.text %}</p>
					{% endfor %}
				</div>
			</div>
		</section>
	</main>
</div>`,
	hr_dashboard: `<div class="accounts-dashboard theme-{%= current_theme || "standard" %}">
	<aside class="accounts-sidebar">
		<nav class="accounts-nav">
			<a class="active" href="#"><i class="fa fa-users"></i><span>HR Overview</span></a>
			<a href="#"><i class="fa fa-sitemap"></i><span>Departments</span></a>
			<a href="#"><i class="fa fa-id-badge"></i><span>Headcount</span></a>
			<a href="#"><i class="fa fa-calendar-check-o"></i><span>Attendance</span></a>
			<a href="#"><i class="fa fa-plane"></i><span>Leave</span></a>
			<a href="#"><i class="fa fa-user-plus"></i><span>Joiners</span></a>
			<a href="#"><i class="fa fa-clock-o"></i><span>Working Hours</span></a>
			<a href="#"><i class="fa fa-exclamation-circle"></i><span>Absence</span></a>
			<a href="#"><i class="fa fa-list"></i><span>Records</span></a>
			<a href="#"><i class="fa fa-pie-chart"></i><span>Workforce Mix</span></a>
		</nav>
	</aside>
	<main class="accounts-content">
		<header class="accounts-header">
			<div>
				<h1>Hospital HR Dashboard</h1>
				<p>Headcount, attendance, leave, department, and workforce activity performance</p>
			</div>
			<div class="accounts-actions">
				<button class="theme-button" type="button"><i class="fa fa-paint-brush"></i><span>{%= current_theme_label || "Standard" %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="date-button"><i class="fa fa-calendar"></i><span>{%= date_range %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="filter-button"><i class="fa fa-filter"></i><span>Filters</span></button>
				<button class="refresh-button"><i class="fa fa-sync-alt"></i><span>Refresh</span></button>
				<button class="export-button"><i class="fa fa-download"></i><span>Export</span></button>
			</div>
		</header>
		<section class="metric-grid">
			{% for metric in metrics %}
			<div class="metric-card {%= metric.class %}">
				<div class="metric-icon">{%= metric.icon %}</div>
				<div>
					<span>{%= metric.label %}</span>
					<strong>{%= metric.value %}</strong>
					<small class="{%= metric.trend_class %}">{%= metric.trend %}</small>
					<em>vs {%= comparison_range %}</em>
				</div>
			</div>
			{% endfor %}
		</section>
		<section class="chart-row">
			<div class="panel income-expenses">
				<div class="panel-head">
					<h2>Joining vs Left</h2>
					<div class="legend"><span class="green"></span>Joining <span class="red"></span>Left</div>
				</div>
				<div class="bar-chart">
					<div class="plot">
						<div class="grid-lines"></div>
						{% for item in income_expenses %}
						<div class="bar-group">
							<div class="bar-stack">
								<span class="bar-column">
									<span class="bar-value income-value">{%= item.income_value %}</span>
									<span class="income-b" style="height: {%= item.income_height %}px;"></span>
								</span>
								<span class="bar-column">
									<span class="bar-value expense-value">{%= item.expense_value %}</span>
									<span class="expense-b" style="height: {%= item.expense_height %}px;"></span>
								</span>
							</div>
							<label>{%= item.label %}</label>
						</div>
						{% endfor %}
					</div>
				</div>
			</div>
			<div class="panel donut-panel">
				<h2>Employee by Employment Type</h2>
				<div class="donut-wrap">
					<div class="donut expense-donut" style="{%= expense_donut_style %}"></div>
					<ul class="chart-list">
						{% for category in expense_categories %}
						<li><span class="{%= category.class %}"></span>{%= category.label %} <b>{%= category.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
			<div class="panel donut-panel source-panel">
				<h2>Employees by Status</h2>
				<div class="donut-wrap">
					<div class="donut source-donut" style="{%= source_donut_style %}"></div>
					<ul class="chart-list">
						{% for source in income_sources %}
						<li><span class="{%= source.class %}"></span>{%= source.label %} <b>{%= source.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
		</section>
		<section class="table-row">
			<div class="panel table-panel accounts-table">
				<h2>Department Headcount</h2>
				<div class="table-row-limit-panel" data-row-limit-panel="10">
				<table>
					<thead><tr><th>Department</th><th>Employees</th><th>Male</th><th>Female</th></tr></thead>
					<tbody>
						{% for row in account_balances %}
						{% if row.is_over_limit %}
						<tr class="is-over-limit"><td>{%= row.account %}</td><td>{%= row.balance %}</td><td>{%= row.male %}</td><td>{%= row.female %}</td></tr>
						{% else %}
						<tr><td>{%= row.account %}</td><td>{%= row.balance %}</td><td>{%= row.male %}</td><td>{%= row.female %}</td></tr>
						{% endif %}
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>{%= account_balances_total %}</th><th></th><th></th></tr>
					</tfoot>
				</table>
				{% if account_balances_has_more %}
				<button type="button" class="table-expand-link" data-table-expand="1" data-expand-label="View All Departments" data-collapse-label="Show Less">View All Departments</button>
				{% endif %}
				</div>
			</div>
			<div class="panel table-panel">
				<h2>Attendance Status</h2>
				<table>
					<thead><tr><th>Status</th><th>Records</th><th>Working Hours</th></tr></thead>
					<tbody>
						{% for row in unpaid_invoices %}
						<tr><td>{%= row.customer_group %}</td><td>{%= row.customer_count %}</td><td>{%= row.outstanding %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>{%= unpaid_invoices_total.customer_count %}</th><th>{%= unpaid_invoices_total.outstanding %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View Attendance Breakdown</a>
			</div>
			<div class="panel table-panel">
				<h2>Approved Leave Types</h2>
				<table>
					<thead><tr><th>Leave Type</th><th>Employees</th><th>Leave Days</th></tr></thead>
					<tbody>
						{% for row in top_supplier_balances %}
						<tr><td>{%= row.supplier %}</td><td>{%= row.supplier_group %}</td><td>{%= row.balance %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>Top Leave Types</th><th>{%= top_supplier_balances_total %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View Leave Summary</a>
			</div>
		</section>
		<section class="bottom-row">
			<div class="panel table-panel budget-variance-panel">
				<h2>Employee Joiner Mix</h2>
				{% if budget_variance.length %}
				<table>
					<thead><tr><th>Department</th><th>Joiners</th><th>Avg Tenure Days</th><th>Joiners</th><th>Share</th></tr></thead>
					<tbody>
						{% for row in budget_variance %}
						<tr>
							<td>{%= row.category %}</td>
							<td>{%= row.budget %}</td>
							<td>{%= row.actual %}</td>
							<td class="variance-cell {%= row.variance_class %}">{%= row.variance %}</td>
							<td><div class="budget-indicator"><span class="indicator-pill {%= row.indicator_class %}">{%= row.indicator_label %}</span><small>{%= row.utilization %}</small></div></td>
						</tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr>
							<th>Total</th>
							<th>{%= budget_variance_total.budget %}</th>
							<th>{%= budget_variance_total.actual %}</th>
							<th class="variance-cell {%= budget_variance_total.variance_class %}">{%= budget_variance_total.variance %}</th>
							<th><div class="budget-indicator"><span class="indicator-pill {%= budget_variance_total.indicator_class %}">{%= budget_variance_total.indicator_label %}</span><small>{%= budget_variance_total.utilization %}</small></div></th>
						</tr>
					</tfoot>
				</table>
				{% else %}
				<div class="budget-empty-state">
					<i class="fa fa-chart-pie"></i>
					<p>{%= budget_variance_message %}</p>
				</div>
				{% endif %}
				<a href="#" data-budget-plan-link="1">View HR Detail Report</a>
			</div>
			<div class="panel insight-panel">
				<h2><span class="spark"><i class="fa fa-sun"></i></span>AI Insight</h2>
				<div data-ai-insight-content="1">
					{% for insight in insights %}
					<p><i class="fa {%= insight.icon_class %} {%= insight.text_class %}"></i>{%= insight.text %}</p>
					{% endfor %}
				</div>
			</div>
		</section>
	</main>
</div>`,
	stock_dashboard: `<div class="accounts-dashboard theme-{%= current_theme || "standard" %}">
	<aside class="accounts-sidebar">
		<nav class="accounts-nav">
			<a class="active" href="#"><i class="fa fa-cubes"></i><span>Stock Overview</span></a>
			<a href="#"><i class="fa fa-building"></i><span>Warehouses</span></a>
			<a href="#"><i class="fa fa-tags"></i><span>Item Groups</span></a>
			<a href="#"><i class="fa fa-exchange"></i><span>Movements</span></a>
			<a href="#"><i class="fa fa-line-chart"></i><span>Fast Movers</span></a>
			<a href="#"><i class="fa fa-warning"></i><span>Low Stock</span></a>
			<a href="#"><i class="fa fa-calendar-times-o"></i><span>Expiry Risk</span></a>
			<a href="#"><i class="fa fa-truck"></i><span>Replenishment</span></a>
			<a href="#"><i class="fa fa-list"></i><span>Transactions</span></a>
			<a href="#"><i class="fa fa-sitemap"></i><span>Inventory Mix</span></a>
		</nav>
	</aside>
	<main class="accounts-content">
		<header class="accounts-header">
			<div>
				<h1>Hospital Stock Dashboard</h1>
				<p>Warehouse, item-group, movement, and inventory risk performance</p>
			</div>
			<div class="accounts-actions">
				<button class="theme-button" type="button"><i class="fa fa-paint-brush"></i><span>{%= current_theme_label || "Standard" %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="date-button"><i class="fa fa-calendar"></i><span>{%= date_range %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="filter-button"><i class="fa fa-filter"></i><span>Filters</span></button>
				<button class="refresh-button"><i class="fa fa-sync-alt"></i><span>Refresh</span></button>
				<button class="export-button"><i class="fa fa-download"></i><span>Export</span></button>
			</div>
		</header>
		<section class="metric-grid">
			{% for metric in metrics %}
			<div class="metric-card {%= metric.class %}">
				<div class="metric-icon">{%= metric.icon %}</div>
				<div>
					<span>{%= metric.label %}</span>
					<strong>{%= metric.value %}</strong>
					<small class="{%= metric.trend_class %}">{%= metric.trend %}</small>
					<em>vs {%= comparison_range %}</em>
				</div>
			</div>
			{% endfor %}
		</section>
		<section class="table-row">
			<div class="panel table-panel accounts-table">
				<h2>Warehouse Stock Value</h2>
				<table>
					<thead><tr><th>Warehouse</th><th>Warehouse Type</th><th>Stock Value ($)</th></tr></thead>
					<tbody>
						{% for row in account_balances %}
						<tr><td>{%= row.account %}</td><td>{%= row.type %}</td><td>{%= row.balance %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>Top Warehouses</th><th>{%= account_balances_total %}</th></tr>
					</tfoot>
				</table>
			</div>
			<div class="panel table-panel">
				<h2>Item Group Inventory</h2>
				<table>
					<thead><tr><th>Item Group</th><th>SKUs</th><th>Stock Value ($)</th></tr></thead>
					<tbody>
						{% for row in unpaid_invoices %}
						<tr><td>{%= row.customer_group %}</td><td>{%= row.customer_count %}</td><td>{%= row.outstanding %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>{%= unpaid_invoices_total.customer_count %}</th><th>{%= unpaid_invoices_total.outstanding %}</th></tr>
					</tfoot>
				</table>
			</div>
			<div class="panel table-panel">
				<h2>Fast Moving Drug Items Below Weekly Average Sold</h2>
				<table>
					<thead><tr><th>Item</th><th>Current Qty</th><th>Weekly Avg Sold</th></tr></thead>
					<tbody>
						{% for row in top_supplier_balances %}
						<tr><td>{%= row.supplier %}</td><td>{%= row.current_qty %}</td><td>{%= row.weekly_avg_sold %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>Flagged Items</th><th>{%= top_supplier_balances_total %}</th></tr>
					</tfoot>
				</table>
			</div>
		</section>
		<section class="bottom-row">
			<div class="panel table-panel budget-variance-panel">
				<h2>Stock Anomalies</h2>
				{% if budget_variance.length %}
				<div class="table-row-limit-panel" data-row-limit-panel="10">
				<table>
					<thead><tr><th>Item</th><th>Anomaly</th><th>Current Qty</th><th>Detail</th></tr></thead>
					<tbody>
						{% for row in budget_variance %}
						{% if row.is_over_limit %}
						<tr class="is-over-limit">
						{% else %}
						<tr>
						{% endif %}
							<td>{%= row.category %}</td>
							<td>{%= row.anomaly %}</td>
							<td>{%= row.actual %}</td>
							<td>{%= row.variance %}</td>
						</tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr>
							<th>Total</th>
							<th colspan="3">{%= budget_variance_total.count %} anomalies</th>
						</tr>
					</tfoot>
				</table>
				{% if budget_variance_has_more %}
				<button type="button" class="table-expand-link" data-table-expand="1" data-expand-label="View All" data-collapse-label="Show Less">View All</button>
				{% endif %}
				</div>
				{% else %}
				<div class="budget-empty-state">
					<i class="fa fa-chart-pie"></i>
					<p>{%= budget_variance_message %}</p>
				</div>
				{% endif %}
			</div>
			<div class="panel insight-panel">
				<h2><span class="spark"><i class="fa fa-sun"></i></span>AI Insight</h2>
				<div data-ai-insight-content="1">
					{% for insight in insights %}
					<p><i class="fa {%= insight.icon_class %} {%= insight.text_class %}"></i>{%= insight.text %}</p>
					{% endfor %}
				</div>
			</div>
		</section>
	</main>
</div>`,
	purchase_dashboard: `<div class="accounts-dashboard theme-{%= current_theme || "standard" %}">
	<aside class="accounts-sidebar">
		<nav class="accounts-nav">
			<a class="active" href="#"><i class="fa fa-shopping-cart"></i><span>Purchase Overview</span></a>
			<a href="#"><i class="fa fa-truck"></i><span>Suppliers</span></a>
			<a href="#"><i class="fa fa-tags"></i><span>Supplier Groups</span></a>
			<a href="#"><i class="fa fa-hospital-o"></i><span>Departments</span></a>
			<a href="#"><i class="fa fa-building"></i><span>Warehouses</span></a>
			<a href="#"><i class="fa fa-cubes"></i><span>Item Groups</span></a>
			<a href="#"><i class="fa fa-file-text-o"></i><span>Invoices</span></a>
			<a href="#"><i class="fa fa-undo"></i><span>Returns</span></a>
			<a href="#"><i class="fa fa-credit-card"></i><span>Payments</span></a>
			<a href="#"><i class="fa fa-sitemap"></i><span>Procurement Mix</span></a>
		</nav>
	</aside>
	<main class="accounts-content">
		<header class="accounts-header">
			<div>
				<h1>Hospital Purchase Dashboard</h1>
				<p>Supplier, department, warehouse, and item-group purchase performance</p>
			</div>
			<div class="accounts-actions">
				<button class="theme-button" type="button"><i class="fa fa-paint-brush"></i><span>{%= current_theme_label || "Standard" %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="date-button"><i class="fa fa-calendar"></i><span>{%= date_range %}</span><i class="fa fa-chevron-down"></i></button>
				<button class="filter-button"><i class="fa fa-filter"></i><span>Filters</span></button>
				<button class="refresh-button"><i class="fa fa-sync-alt"></i><span>Refresh</span></button>
				<button class="export-button"><i class="fa fa-download"></i><span>Export</span></button>
			</div>
		</header>
		<section class="metric-grid">
			{% for metric in metrics %}
			<div class="metric-card {%= metric.class %}">
				<div class="metric-icon">{%= metric.icon %}</div>
				<div>
					<span>{%= metric.label %}</span>
					<strong>{%= metric.value %}</strong>
					<small class="{%= metric.trend_class %}">{%= metric.trend %}</small>
					<em>vs {%= comparison_range %}</em>
				</div>
			</div>
			{% endfor %}
		</section>
		<section class="chart-row">
			<div class="panel income-expenses">
				<div class="panel-head">
					<h2>Purchases vs Payments</h2>
					<div class="legend"><span class="green"></span>Purchases <span class="red"></span>Payments</div>
				</div>
				<div class="bar-chart">
					<div class="plot">
						<div class="grid-lines"></div>
						{% for item in income_expenses %}
						<div class="bar-group">
							<div class="bar-stack">
								<span class="bar-column">
									<span class="bar-value income-value">{%= item.income_value %}</span>
									<span class="income-b" style="height: {%= item.income_height %}px;"></span>
								</span>
								<span class="bar-column">
									<span class="bar-value expense-value">{%= item.expense_value %}</span>
									<span class="expense-b" style="height: {%= item.expense_height %}px;"></span>
								</span>
							</div>
							<label>{%= item.label %}</label>
						</div>
						{% endfor %}
					</div>
				</div>
			</div>
			<div class="panel donut-panel">
				<h2>Purchase by Cost Center</h2>
				<div class="donut-wrap">
					<div class="donut expense-donut" style="{%= expense_donut_style %}"></div>
					<ul class="chart-list">
						{% for category in expense_categories %}
						<li><span class="{%= category.class %}"></span>{%= category.label %} <b>{%= category.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
			<div class="panel donut-panel source-panel">
				<h2>Purchase by Warehouse</h2>
				<div class="donut-wrap">
					<div class="donut source-donut" style="{%= source_donut_style %}"></div>
					<ul class="chart-list">
						{% for source in income_sources %}
						<li><span class="{%= source.class %}"></span>{%= source.label %} <b>{%= source.value %}</b></li>
						{% endfor %}
					</ul>
				</div>
			</div>
		</section>
		<section class="table-row">
			<div class="panel table-panel accounts-table">
				<h2>Supplier Spend</h2>
				<div class="table-row-limit-panel" data-row-limit-panel="10">
				<table>
					<thead><tr><th>Supplier</th><th>Supplier Group</th><th>Net Purchase ($)</th><th>Payment ($)</th><th>Balance as of {%= to_date %}</th></tr></thead>
					<tbody>
						{% for row in account_balances %}
						{% if row.is_over_limit %}
						<tr class="is-over-limit"><td>{%= row.account %}</td><td>{%= row.type %}</td><td>{%= row.balance %}</td><td>{%= row.payment %}</td><td>{%= row.supplier_balance %}</td></tr>
						{% else %}
						<tr><td>{%= row.account %}</td><td>{%= row.type %}</td><td>{%= row.balance %}</td><td>{%= row.payment %}</td><td>{%= row.supplier_balance %}</td></tr>
						{% endif %}
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>Top Suppliers</th><th>{%= account_balances_total %}</th><th>{%= account_balances_payment_total %}</th><th>{%= account_balances_supplier_balance_total %}</th></tr>
					</tfoot>
				</table>
				{% if account_balances_has_more %}
				<button type="button" class="table-expand-link" data-table-expand="1" data-expand-label="View All Suppliers" data-collapse-label="Show Less">View All Suppliers</button>
				{% endif %}
				</div>
			</div>
			<div class="panel table-panel">
				<h2>Purchase by Item Group</h2>
				<table>
					<thead><tr><th>Item Group</th><th>Qty</th><th>Amount ($)</th></tr></thead>
					<tbody>
						{% for row in unpaid_invoices %}
						<tr><td>{%= row.item_group %}</td><td>{%= row.qty %}</td><td>{%= row.amount %}</td></tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr><th>Total</th><th>{%= unpaid_invoices_total.qty %}</th><th>{%= unpaid_invoices_total.amount %}</th></tr>
					</tfoot>
				</table>
				<a href="#">View Item Group Breakdown</a>
			</div>
		</section>
		<section class="bottom-row">
			<div class="panel table-panel budget-variance-panel">
				<h2>Anomalies in Purchase</h2>
				{% if budget_variance.length %}
				<div class="table-row-limit-panel" data-row-limit-panel="10">
				<table>
					<thead><tr><th>Supplier / Item</th><th>Current Value</th><th>Expected Value</th><th>Variance</th></tr></thead>
					<tbody>
						{% for row in budget_variance %}
						{% if row.is_over_limit %}
						<tr class="is-over-limit">
						{% else %}
						<tr>
						{% endif %}
							<td>{%= row.subject %}</td>
							<td>{%= row.current_value %}</td>
							<td>{%= row.expected_value %}</td>
							<td class="variance-cell {%= row.variance_class %}">{%= row.variance %}</td>
						</tr>
						{% endfor %}
					</tbody>
					<tfoot>
						<tr>
							<th>Total</th>
							<th colspan="3">{%= budget_variance_total.count %} anomalies</th>
						</tr>
					</tfoot>
				</table>
				{% if budget_variance_has_more %}
				<button type="button" class="table-expand-link" data-table-expand="1" data-expand-label="Display All" data-collapse-label="Show Less">Display All</button>
				{% endif %}
				</div>
				{% else %}
				<div class="budget-empty-state">
					<i class="fa fa-chart-pie"></i>
					<p>{%= budget_variance_message %}</p>
				</div>
				{% endif %}
				<a href="#" data-budget-plan-link="1">View Detailed Purchase Breakdown</a>
			</div>
			<div class="panel insight-panel">
				<h2><span class="spark"><i class="fa fa-sun"></i></span>AI Insight</h2>
				<div data-ai-insight-content="1">
					{% for insight in insights %}
					<p><i class="fa {%= insight.icon_class %} {%= insight.text_class %}"></i>{%= insight.text %}</p>
					{% endfor %}
				</div>
			</div>
		</section>
	</main>
</div>`
};

HospitalDashboardsPage = Class.extend({
	init: function(wrapper) {
		this.wrapper = wrapper;
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Hospital Dashboards',
			single_column: true
		});
		this.$page_container = $(wrapper).closest('.page-container');
		this.$page_container.addClass('accounts-dashboard-page');
		$(wrapper).addClass('accounts-dashboard-wrapper');
		this.themeStorageKey = 'hospital_dashboards_theme';
		this.currentTheme = this.get_saved_theme();
		this.currentView = 'finance';
		this.viewState = {
			finance: { from_date: null, to_date: null, previous_from_date: null, previous_to_date: null },
			sales: { from_date: null, to_date: null, previous_from_date: null, previous_to_date: null }
		};
		this.aiInsightRequestId = 0;
		this.render_shell();
		this.apply_theme_to_shell();
		this.load_view(this.currentView);
	},

	render_shell: function() {
		this.page.main.addClass('accounts-dashboard-main');
		this.page.main.closest('.layout-main-section').addClass('accounts-dashboard-layout');
		this.$page_container.find('.page-body').addClass('full-width');
		this.page.wrapper.find('.page-head').hide();
		this.page.main.html(this.get_shell_markup());
		this.bind_sidebar();
	},

	get_shell_markup: function() {
		return `
			<div class="accounts-dashboard theme-${this.escape_attribute(this.currentTheme)}" data-hospital-dashboards-shell="1">
				<aside class="accounts-sidebar">
					<nav class="accounts-nav">
						${Object.entries(HOSPITAL_DASHBOARD_VIEWS).map(([key, config]) => `
							<a href="#" data-dashboard-view="${this.escape_attribute(key)}" class="${key === this.currentView ? 'active' : ''}">
								<i class="fa ${this.escape_attribute(config.icon)}"></i><span>${this.escape_html(config.label)}</span>
							</a>
						`).join('')}
					</nav>
				</aside>
				<main class="accounts-content hospital-dashboard-stage">
					<div class="hospital-dashboard-loader">
						<i class="fa fa-spinner fa-spin"></i>
						<span>Loading dashboard...</span>
					</div>
				</main>
			</div>
		`;
	},

	bind_sidebar: function() {
		this.page.main.find('[data-dashboard-view]').on('click', (event) => {
			event.preventDefault();
			const view = $(event.currentTarget).data('dashboard-view');
			if (view && view !== this.currentView) {
				this.load_view(view);
			}
		});
	},

	set_active_sidebar: function() {
		this.page.main.find('[data-dashboard-view]').removeClass('active');
		this.page.main.find(`[data-dashboard-view="${this.currentView}"]`).addClass('active');
	},

	get_view_state: function(view) {
		if (!this.viewState[view]) {
			this.viewState[view] = { from_date: null, to_date: null, previous_from_date: null, previous_to_date: null };
		}
		return this.viewState[view];
	},

	load_view: function(view) {
		this.currentView = view;
		this.set_active_sidebar();
		const config = HOSPITAL_DASHBOARD_VIEWS[view];
		if (!config) return;

		if (config.template) {
			this.load_template_view(view, config);
			return;
		}
		this.render_placeholder_view(config.placeholder || {});
	},

	load_template_view: function(view, config) {
		const state = this.get_view_state(view);
		this.show_loading_state(config.empty_message || 'Loading dashboard...');
		const loadingContext = this.get_loading_context(view);
		this.render_template_content(view, config.template, loadingContext);
		this.show_dashboard_loading();

		frappe.call({
			method: config.method,
			args: Object.assign({
				from_date: state.from_date,
				to_date: state.to_date
			}, view === 'profit-and-loss' ? {
				previous_from_date: state.previous_from_date,
				previous_to_date: state.previous_to_date
			} : {}),
			callback: (r) => {
				if (view !== this.currentView) return;
				const data = this.prepare_dashboard_data(r.message || {});
				state.from_date = data.from_date || state.from_date;
				state.to_date = data.to_date || state.to_date;
				state.previous_from_date = data.previous_from_date || state.previous_from_date;
				state.previous_to_date = data.previous_to_date || state.previous_to_date;
				this.render_template_content(view, config.template, data);
				this.bind_template_actions(view, config, data);
				this.load_ai_insights(view, config, data);
			}
		});
	},

	render_template_content: function(view, template, data) {
		const context = Object.assign({}, data, {
			current_theme: this.currentTheme,
			current_theme_label: this.get_theme_label(this.currentTheme)
		});
		const inlineTemplate = HOSPITAL_DASHBOARD_INLINE_TEMPLATES[template];
		const rendered = inlineTemplate
			? frappe.render(inlineTemplate, context, `hospital_dashboards_${template}`)
			: frappe.render_template(template, context);
		const $dashboard = $(rendered);
		const $content = $dashboard.find('.accounts-content');
		this.page.main.find('.hospital-dashboard-stage, .accounts-content').last().replaceWith($content);
		this.page.main.find('[data-hospital-dashboards-shell="1"]').removeClass('theme-standard theme-hodan-brand').addClass(`theme-${this.currentTheme}`);
		this.page.main.find('.accounts-content').addClass('hospital-dashboard-stage').attr('data-current-view', view);
	},

	render_placeholder_view: function(placeholder) {
		const cards = placeholder.cards || [];
		const markup = `
			<main class="accounts-content hospital-dashboard-stage hospital-dashboard-placeholder" data-current-view="${this.escape_attribute(this.currentView)}">
				<header class="accounts-header">
					<div>
						<h1>${this.escape_html(placeholder.title || 'Dashboard')}</h1>
						<p>${this.escape_html(placeholder.subtitle || 'This dashboard will live inside the hospital dashboard container.')}</p>
					</div>
				</header>
				<section class="metric-grid">
					${cards.map((card) => `
						<div class="metric-card profit">
							<div class="metric-icon"><i class="fa fa-columns"></i></div>
							<div>
								<span>${this.escape_html(card[0] || '')}</span>
								<strong>Scaffolded</strong>
								<small class="trend-flat">Ready for data binding</small>
								<em>${this.escape_html(card[1] || '')}</em>
							</div>
						</div>
					`).join('')}
				</section>
				<section class="bottom-row">
					<div class="panel table-panel budget-variance-panel">
						<h2>Container Mode</h2>
						<div class="budget-empty-state">
							<i class="fa fa-layer-group"></i>
							<p>This dashboard is loaded inside <strong>hospital-dashboards</strong> with one fixed sidebar and a swappable content panel.</p>
						</div>
					</div>
					<div class="panel insight-panel">
						<h2><span class="spark"><i class="fa fa-sun"></i></span>Next Step</h2>
						<div>
							<p><i class="fa fa-lightbulb gold-text"></i>We can now turn this placeholder into a real data dashboard without changing the container shell.</p>
						</div>
					</div>
				</section>
			</main>
		`;
		this.page.main.find('.hospital-dashboard-stage, .accounts-content').last().replaceWith($(markup));
		this.page.main.find('[data-hospital-dashboards-shell="1"]').removeClass('theme-standard theme-hodan-brand').addClass(`theme-${this.currentTheme}`);
	},

	show_loading_state: function(message) {
		this.page.main.find('.hospital-dashboard-stage, .accounts-content').last().replaceWith($(`
			<main class="accounts-content hospital-dashboard-stage">
				<div class="hospital-dashboard-loader">
					<i class="fa fa-spinner fa-spin"></i>
					<span>${this.escape_html(message || 'Loading dashboard...')}</span>
				</div>
			</main>
		`));
	},

	show_dashboard_loading: function() {
		const $content = this.page.main.find('.accounts-content');
		$content.find('.accounts-date-popover, .accounts-theme-popover, .accounts-export-popover').remove();
		$(document).off('click.finance-date-filter click.finance-theme-picker click.finance-export-menu');
		$content.addClass('is-loading');
		$content.find('.theme-button, .date-button, .filter-button, .refresh-button, .export-button').prop('disabled', true);
	},

	get_loading_context: function(view) {
		const state = this.get_view_state(view);
		const range = this.get_month_range(0);
		const empty_message = (HOSPITAL_DASHBOARD_VIEWS[view] || {}).empty_message || 'Loading dashboard...';
		const purchaseBudgetTotal = view === 'purchase-dashboard'
			? { count: '0' }
			: {
				budget: '$ 0',
				actual: '$ 0',
				variance: '$ 0',
				variance_class: 'neutral',
				indicator_label: 'No Activity',
				indicator_class: 'neutral',
				utilization: '0.0%'
			};
		const purchaseUnpaidTotal = view === 'purchase-dashboard'
			? { qty: '0', amount: '$ 0' }
			: { customer_count: 0, outstanding: '$ 0' };
		return {
			from_date: state.from_date || range.from_date,
			to_date: state.to_date || range.to_date,
			previous_from_date: state.previous_from_date || '',
			previous_to_date: state.previous_to_date || '',
			date_range: 'Loading...',
			comparison_range: 'previous period',
			metrics: [],
			statement_table: {
				title: 'PROFIT AND LOSS STATEMENT',
				subtitle: 'Loading statement...',
				currency: 'USD',
				company: '',
				actual_period_label: '',
				previous_period_label: '',
				rows: []
			},
			income_expenses: [],
			expense_categories: [],
			expense_donut_style: 'background: conic-gradient(#e5e7eb 0 100%);',
			income_sources: [],
			source_donut_style: 'background: conic-gradient(#e5e7eb 0 100%);',
			account_balances: [],
			account_balances_has_more: false,
			account_balances_total: '$ 0',
			account_balances_payment_total: '$ 0',
			account_balances_supplier_balance_total: '$ 0',
			unpaid_invoices: [],
			unpaid_invoices_total: purchaseUnpaidTotal,
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
			budget_variance_has_more: false,
			budget_variance_total: purchaseBudgetTotal,
			budget_variance_message: empty_message,
			cash_flow: [],
			insights: []
		};
	},

	prepare_dashboard_data: function(data) {
		const prepared = Object.assign({}, data || {});
		prepared.statement_table = prepared.statement_table || {
			title: 'PROFIT AND LOSS STATEMENT',
			subtitle: '',
			currency: 'USD',
			company: '',
			actual_period_label: '',
			previous_period_label: '',
			rows: []
		};
		prepared.statement_table.rows = prepared.statement_table.rows || [];
		prepared.previous_from_date = prepared.previous_from_date || '';
		prepared.previous_to_date = prepared.previous_to_date || '';
		prepared.account_balances = prepared.account_balances || [];
		prepared.account_balances_has_more = Boolean(prepared.account_balances_has_more);
		prepared.unpaid_invoices = prepared.unpaid_invoices || [];
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
		prepared.budget_variance = prepared.budget_variance || [];
		prepared.budget_variance_has_more = Boolean(prepared.budget_variance_has_more);
		prepared.account_balances_total = prepared.account_balances_total || this.format_currency_total(
			prepared.account_balances.reduce((sum, row) => sum + this.to_number(row.raw_balance), 0)
		);
		if (this.currentView === 'purchase-dashboard') {
			prepared.account_balances_payment_total = prepared.account_balances_payment_total || this.format_currency_total(
				prepared.account_balances.reduce((sum, row) => sum + this.to_number(row.raw_payment), 0)
			);
			prepared.account_balances_supplier_balance_total = prepared.account_balances_supplier_balance_total || this.format_currency_total(
				prepared.account_balances.reduce((sum, row) => sum + this.to_number(row.raw_supplier_balance), 0)
			);
			prepared.unpaid_invoices_total = prepared.unpaid_invoices_total || {
				qty: this.format_quantity_total(
					prepared.unpaid_invoices.reduce((sum, row) => sum + this.to_number(row.raw_qty), 0)
				),
				amount: this.format_currency_total(
					prepared.unpaid_invoices.reduce((sum, row) => sum + this.to_number(row.raw_amount), 0)
				)
			};
			prepared.budget_variance_total = prepared.budget_variance_total || { count: this.format_number_total(prepared.budget_variance.length) };
		} else {
			prepared.unpaid_invoices_total = prepared.unpaid_invoices_total || {
				customer_count: prepared.unpaid_invoices.reduce((sum, row) => sum + this.to_number(row.raw_customer_count || row.customer_count), 0),
				outstanding: this.format_currency_total(
					prepared.unpaid_invoices.reduce((sum, row) => sum + this.to_number(row.raw_outstanding), 0)
				)
			};
		}
		prepared.top_supplier_balances_total = prepared.top_supplier_balances_total || this.format_currency_total(
			prepared.top_supplier_balances.reduce((sum, row) => sum + this.to_number(row.raw_balance), 0)
		);
		return prepared;
	},

	bind_template_actions: function(view, config, data) {
		const $main = this.page.main;
		$main.find('.theme-button').off('click').on('click', (event) => {
			event.stopPropagation();
			this.show_theme_picker();
		});
		$main.find('.date-button').off('click').on('click', (event) => {
			event.stopPropagation();
			this.show_date_filter();
		});
		$main.find('.refresh-button').off('click').on('click', () => {
			this.load_view(view);
		});
		this.bind_performance_toggle();
		this.bind_item_group_toggle();
		this.bind_table_expand();
		$main.find('.filter-button').off('click').on('click', () => {
			frappe.show_alert({ message: __('Filters can be added per dashboard inside hospital-dashboards.'), indicator: 'blue' });
		});
		$main.find('.export-button').off('click').on('click', () => {
			frappe.show_alert({ message: __('Export can be enabled per dashboard without leaving this container.'), indicator: 'blue' });
		});
		$main.find('[data-budget-plan-link="1"]').off('click').on('click', (event) => {
			event.preventDefault();
			if (typeof config.on_budget_link === 'function') {
				config.on_budget_link(this, data);
			}
		});
		this.bind_statement_toggles();
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

	bind_statement_toggles: function() {
		const $rows = this.page.main.find('.statement-table tbody .statement-data-row');
		if (!$rows.length) return;

		const applyVisibility = () => {
			const collapsedStack = [];
			$rows.each((_, row) => {
				const $row = $(row);
				const indent = this.to_number($row.attr('data-indent'));
				while (collapsedStack.length && indent <= collapsedStack[collapsedStack.length - 1]) {
					collapsedStack.pop();
				}
				const hiddenByAncestor = collapsedStack.length > 0;
				$row.toggle(!hiddenByAncestor);
				if (!hiddenByAncestor && $row.attr('data-collapsible-group') === '1' && $row.hasClass('is-collapsed')) {
					collapsedStack.push(indent);
				}
			});
		};

		this.page.main.find('.statement-toggle').off('click').on('click', (event) => {
			event.preventDefault();
			event.stopPropagation();
			$(event.currentTarget).closest('.statement-group-row').toggleClass('is-collapsed');
			applyVisibility();
		});

		applyVisibility();
	},

	load_ai_insights: function(view, config, data) {
		const requestId = ++this.aiInsightRequestId;
		const $target = this.page.main.find('[data-ai-insight-content="1"]');
		if (!$target.length || !config.ai_method) return;

		$target.html(`<p class="ai-insight-placeholder"><i class="fa fa-spinner fa-spin slate-text"></i>${this.escape_html(config.ai_loading_message || 'Generating insight...')}</p>`);
		frappe.call({
			method: config.ai_method,
			type: 'POST',
			args: {
				from_date: this.get_view_state(view).from_date,
				to_date: this.get_view_state(view).to_date,
				dashboard_context: JSON.stringify(this.build_ai_dashboard_context(data))
			},
			callback: (r) => {
				if (requestId !== this.aiInsightRequestId || view !== this.currentView) return;
				this.render_ai_insights(r.message?.insights || []);
			},
			error: () => {
				if (requestId !== this.aiInsightRequestId || view !== this.currentView) return;
				this.render_ai_insights([]);
			}
		});
	},

	build_ai_dashboard_context: function(data) {
		return {
			metrics: data.metrics || [],
			expense_categories: data.expense_categories || [],
			income_sources: data.income_sources || [],
			account_balances_total: data.account_balances_total || '$ 0',
			account_balances_payment_total: data.account_balances_payment_total || '$ 0',
			account_balances_supplier_balance_total: data.account_balances_supplier_balance_total || '$ 0',
			unpaid_invoices: data.unpaid_invoices || [],
			unpaid_invoices_total: data.unpaid_invoices_total || { customer_count: 0, outstanding: '$ 0' },
			top_supplier_balances: data.top_supplier_balances || [],
			top_supplier_balances_total: data.top_supplier_balances_total || '$ 0',
			budget_variance: data.budget_variance || [],
			budget_variance_total: data.budget_variance_total || {}
		};
	},

	render_ai_insights: function(insights) {
		const $target = this.page.main.find('[data-ai-insight-content="1"]');
		if (!$target.length) return;
		if (!insights.length) {
			$target.html('<p><i class="fa fa-info-circle slate-text"></i>Insights are not available right now. Please review the dashboard figures below.</p>');
			return;
		}
		$target.html(insights.map((insight) => {
			return `<p><i class="fa ${this.escape_attribute(insight.icon_class || 'fa-info-circle')} ${this.escape_attribute(insight.text_class || 'slate-text')}"></i>${this.escape_html(insight.text || '')}</p>`;
		}).join(''));
	},

	show_theme_picker: function() {
		const $actions = this.page.main.find('.accounts-actions');
		if (!$actions.length) return;
		const $existing = $actions.find('.accounts-theme-popover');
		if ($existing.length) {
			$existing.remove();
			$(document).off('click.finance-theme-picker');
			return;
		}

		const themes = [
			{ key: 'standard', label: 'Standard', description: 'Original dashboard palette' },
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
						<button type="button" class="accounts-theme-option ${theme.key === this.currentTheme ? 'is-active' : ''}" data-theme-key="${this.escape_attribute(theme.key)}">
							<span class="accounts-theme-swatch accounts-theme-swatch--${this.escape_attribute(theme.key)}"></span>
							<span class="accounts-theme-copy"><strong>${this.escape_html(theme.label)}</strong><small>${this.escape_html(theme.description)}</small></span>
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
			this.set_theme($(event.currentTarget).data('theme-key'));
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
		this.currentTheme = this.normalize_theme(theme);
		this.save_theme(this.currentTheme);
		this.apply_theme_to_shell();
		const $shell = this.page.main.find('[data-hospital-dashboards-shell="1"]');
		$shell.removeClass('theme-standard theme-hodan-brand').addClass(`theme-${this.currentTheme}`);
		this.page.main.find('.theme-button span').text(this.get_theme_label(this.currentTheme));
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
			// Ignore storage errors.
		}
	},

	show_date_filter: function() {
		const $actions = this.page.main.find('.accounts-actions');
		if (!$actions.length) return;
		const $existing = $actions.find('.accounts-date-popover');
		if ($existing.length) {
			$existing.remove();
			$(document).off('click.finance-date-filter');
			return;
		}

		const state = this.get_view_state(this.currentView);
		const ranges = {
			today: this.get_today_range(),
			this_month: this.get_month_range(0),
			last_month: this.get_month_range(-1),
			year_to_date: this.get_year_to_date_range()
		};
		const isComparisonView = this.currentView === 'profit-and-loss';
		const defaultPreviousRange = this.get_previous_period_for_range(
			state.from_date || ranges.this_month.from_date,
			state.to_date || ranges.this_month.to_date
		);
		const fieldsMarkup = isComparisonView ? `
				<div class="accounts-date-section">
					<div class="accounts-date-section-title">Actual Period</div>
					<div class="accounts-date-fields">
						<label>
							<span>From</span>
							<input type="date" data-date-field="from_date" value="${this.escape_attribute(state.from_date || ranges.this_month.from_date)}">
						</label>
						<label>
							<span>To</span>
							<input type="date" data-date-field="to_date" value="${this.escape_attribute(state.to_date || ranges.this_month.to_date)}">
						</label>
					</div>
				</div>
				<div class="accounts-date-section">
					<div class="accounts-date-section-title">Compare With Period</div>
					<div class="accounts-date-fields">
						<label>
							<span>From</span>
							<input type="date" data-date-field="previous_from_date" value="${this.escape_attribute(state.previous_from_date || defaultPreviousRange.from_date)}">
						</label>
						<label>
							<span>To</span>
							<input type="date" data-date-field="previous_to_date" value="${this.escape_attribute(state.previous_to_date || defaultPreviousRange.to_date)}">
						</label>
					</div>
				</div>
		` : `
				<div class="accounts-date-fields">
					<label>
						<span>From</span>
						<input type="date" data-date-field="from_date" value="${this.escape_attribute(state.from_date || ranges.this_month.from_date)}">
					</label>
					<label>
						<span>To</span>
						<input type="date" data-date-field="to_date" value="${this.escape_attribute(state.to_date || ranges.this_month.to_date)}">
					</label>
				</div>
		`;
		const $popover = $(`
			<div class="accounts-date-popover">
				<div class="accounts-date-popover-head">
					<strong>${isComparisonView ? 'Comparison Dates' : 'Date Range'}</strong>
					<button type="button" class="accounts-date-close" aria-label="Close"><i class="fa fa-times"></i></button>
				</div>
				<div class="accounts-date-presets">
					<button type="button" data-range="today">Today</button>
					<button type="button" data-range="this_month">This Month</button>
					<button type="button" data-range="last_month">Last Month</button>
					<button type="button" data-range="year_to_date">Year to Date</button>
				</div>
				${fieldsMarkup}
				<div class="accounts-date-error"></div>
				<div class="accounts-date-actions">
					<button type="button" class="accounts-date-cancel">Cancel</button>
					<button type="button" class="accounts-date-apply">Apply</button>
				</div>
			</div>
		`);

		$actions.append($popover);
		$popover.on('click', (event) => event.stopPropagation());
		if (isComparisonView) {
			$popover.find('[data-date-field="from_date"]').on('change', (event) => {
				const actualFromDate = $(event.currentTarget).val();
				if (!actualFromDate) return;
				const actualToDate = this.get_month_end_for_date(actualFromDate);
				const previousRange = this.get_previous_month_range_for_date(actualFromDate);
				$popover.find('[data-date-field="to_date"]').val(actualToDate);
				$popover.find('[data-date-field="previous_from_date"]').val(previousRange.from_date);
				$popover.find('[data-date-field="previous_to_date"]').val(previousRange.to_date);
				$popover.find('.accounts-date-error').text('');
			});
		}
		$popover.find('[data-range]').on('click', (event) => {
			const range = ranges[$(event.currentTarget).data('range')];
			$popover.find('[data-date-field="from_date"]').val(range.from_date);
			$popover.find('[data-date-field="to_date"]').val(range.to_date);
			if (isComparisonView) {
				const previousRange = this.get_previous_period_for_range(range.from_date, range.to_date);
				$popover.find('[data-date-field="previous_from_date"]').val(previousRange.from_date);
				$popover.find('[data-date-field="previous_to_date"]').val(previousRange.to_date);
			}
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
			const viewState = this.get_view_state(this.currentView);
			if (isComparisonView) {
				const previous_from_date = $popover.find('[data-date-field="previous_from_date"]').val();
				const previous_to_date = $popover.find('[data-date-field="previous_to_date"]').val();
				if (!previous_from_date || !previous_to_date) {
					$popover.find('.accounts-date-error').text('Choose all actual and previous period dates.');
					return;
				}
				if (previous_from_date > previous_to_date) {
					$popover.find('.accounts-date-error').text('Previous period from date cannot be after to date.');
					return;
				}
				viewState.previous_from_date = previous_from_date;
				viewState.previous_to_date = previous_to_date;
			}
			viewState.from_date = from_date;
			viewState.to_date = to_date;
			$popover.remove();
			$(document).off('click.finance-date-filter');
			this.load_view(this.currentView);
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
		return { from_date: this.format_date_value(today), to_date: this.format_date_value(today) };
	},

	get_month_range: function(month_offset) {
		const today = new Date();
		const first_day = new Date(today.getFullYear(), today.getMonth() + month_offset, 1);
		const last_day = new Date(today.getFullYear(), today.getMonth() + month_offset + 1, 0);
		return { from_date: this.format_date_value(first_day), to_date: this.format_date_value(last_day) };
	},

	get_budget_report_month: function(view) {
		const state = this.get_view_state(view);
		const range = this.get_month_range(0);
		const base_date = state.from_date || range.from_date;
		return `${base_date.slice(0, 7)}-01`;
	},

	get_year_to_date_range: function() {
		const today = new Date();
		return {
			from_date: this.format_date_value(new Date(today.getFullYear(), 0, 1)),
			to_date: this.format_date_value(today)
		};
	},

	get_previous_period_for_range: function(from_date, to_date) {
		const fromDate = this.parse_date_value(from_date);
		const toDate = this.parse_date_value(to_date);
		if (!fromDate || !toDate) {
			const fallback = this.get_month_range(-1);
			return { from_date: fallback.from_date, to_date: fallback.to_date };
		}
		if (this.is_full_month_range(fromDate, toDate)) {
			const previousMonthDate = new Date(fromDate);
			previousMonthDate.setDate(previousMonthDate.getDate() - 1);
			return {
				from_date: this.format_date_value(new Date(previousMonthDate.getFullYear(), previousMonthDate.getMonth(), 1)),
				to_date: this.format_date_value(new Date(previousMonthDate.getFullYear(), previousMonthDate.getMonth() + 1, 0))
			};
		}
		const dayCount = Math.max(Math.round((toDate - fromDate) / 86400000) + 1, 1);
		const previousToDate = new Date(fromDate);
		previousToDate.setDate(previousToDate.getDate() - 1);
		const previousFromDate = new Date(previousToDate);
		previousFromDate.setDate(previousFromDate.getDate() - (dayCount - 1));
		return {
			from_date: this.format_date_value(previousFromDate),
			to_date: this.format_date_value(previousToDate)
		};
	},

	get_month_end_for_date: function(value) {
		const date = this.parse_date_value(value);
		if (!date) return value || '';
		return this.format_date_value(new Date(date.getFullYear(), date.getMonth() + 1, 0));
	},

	get_previous_month_range_for_date: function(value) {
		const date = this.parse_date_value(value);
		if (!date) {
			return this.get_month_range(-1);
		}
		const previousMonthDate = new Date(date.getFullYear(), date.getMonth(), 0);
		return {
			from_date: this.format_date_value(new Date(previousMonthDate.getFullYear(), previousMonthDate.getMonth(), 1)),
			to_date: this.format_date_value(new Date(previousMonthDate.getFullYear(), previousMonthDate.getMonth() + 1, 0))
		};
	},

	parse_date_value: function(value) {
		if (!value) return null;
		const parts = String(value).split('-').map((part) => parseInt(part, 10));
		if (parts.length !== 3 || parts.some((part) => !Number.isFinite(part))) {
			return null;
		}
		return new Date(parts[0], parts[1] - 1, parts[2]);
	},

	is_full_month_range: function(fromDate, toDate) {
		return (
			fromDate instanceof Date &&
			toDate instanceof Date &&
			fromDate.getDate() === 1 &&
			toDate.getFullYear() === fromDate.getFullYear() &&
			toDate.getMonth() === fromDate.getMonth() &&
			toDate.getDate() === new Date(toDate.getFullYear(), toDate.getMonth() + 1, 0).getDate()
		);
	},

	format_date_value: function(date) {
		const year = date.getFullYear();
		const month = String(date.getMonth() + 1).padStart(2, '0');
		const day = String(date.getDate()).padStart(2, '0');
		return `${year}-${month}-${day}`;
	},

	format_currency_total: function(value) {
		return `$ ${this.to_number(value).toLocaleString(undefined, {
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		})}`;
	},

	format_quantity_total: function(value) {
		const quantity = this.to_number(value);
		if (Math.abs(quantity - Math.round(quantity)) <= 0.005) {
			return Math.round(quantity).toLocaleString();
		}
		return quantity.toLocaleString(undefined, {
			minimumFractionDigits: 1,
			maximumFractionDigits: 1
		});
	},

	format_number_total: function(value) {
		return this.to_number(value).toLocaleString(undefined, {
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		});
	},

	to_number: function(value) {
		const number = Number(value);
		return Number.isFinite(number) ? number : 0;
	},

	escape_attribute: function(value) {
		return String(value || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
	},

	escape_html: function(value) {
		return String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
	}
});

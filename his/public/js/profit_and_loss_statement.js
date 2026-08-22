(function () {
	const report_name = "Profit and Loss Statement";
	const formatter_flag = "__his_hide_root_account_values";
	const max_attempts = 100;

	function is_profit_and_loss_route() {
		const route = frappe.get_route();
		return route[0] === "query-report" && route[1] === report_name;
	}

	function apply_formatter(attempt = 0) {
		if (!is_profit_and_loss_route()) {
			return;
		}

		// ERPNext loads the report definition asynchronously and can replace the
		// settings object after the route first changes. Keep checking briefly so
		// the final report definition is always customized.
		if (attempt < max_attempts) {
			setTimeout(() => apply_formatter(attempt + 1), 50);
		}

		const report_settings = frappe.query_reports?.[report_name];
		if (!report_settings?.formatter) {
			return;
		}

		if (report_settings.formatter[formatter_flag]) {
			return;
		}

		const standard_formatter = report_settings.formatter;
		const custom_formatter = function (value, row, column, data, default_formatter) {
			const is_root_account =
				data &&
				!data.parent_account &&
				Number(data.indent) === 0 &&
				Object.prototype.hasOwnProperty.call(data, "is_group");

			if (is_root_account && column.fieldname !== "account") {
				return "";
			}

			return standard_formatter.call(
				this,
				value,
				row,
				column,
				data,
				default_formatter
			);
		};

		custom_formatter[formatter_flag] = true;
		report_settings.formatter = custom_formatter;

		// If the report rendered before the asynchronous customization landed,
		// redraw its existing data with the new formatter (no server call).
		const query_report = frappe.query_report;
		if (
			query_report?.report_name === report_name &&
			query_report.report_settings === report_settings &&
			query_report.datatable &&
			query_report.data
		) {
			query_report.render_datatable();
		}
	}

	frappe.router.on("change", () => apply_formatter());
	apply_formatter();
})();

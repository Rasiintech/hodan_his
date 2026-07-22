frappe.pages["power-bi"].on_page_load = function (wrapper) {
	new HISPowerBIPage(wrapper);
};

frappe.pages["power-bi"].refresh = function (wrapper) {
	if (wrapper.power_bi_page) {
		wrapper.power_bi_page.refresh();
	}
};

class HISPowerBIPage {
	constructor(wrapper) {
		this.wrapper = $(wrapper);
		wrapper.power_bi_page = this;
		this.reports = [];
		this.selected_report = null;
		this.route_name = this.get_route_name();
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Power BI"),
			single_column: true,
		});

		this.render();
		this.load_embed();
	}

	refresh() {
		const next_route_name = this.get_route_name();
		if (next_route_name === this.route_name && this.selected_report) {
			return;
		}

		this.route_name = next_route_name;
		this.selected_report = this.get_selected_report();

		if (!this.selected_report) {
			this.set_state(__("No Power BI report matches the current route."), true);
			return;
		}

		this.fetch_embed_config(this.selected_report)
			.then((config) => this.embed_report(config))
			.catch((error) => {
				const message =
					error && error.message ? error.message : __("Unable to load the Power BI report.");
				this.set_state(message, true);
			});
	}

	render() {
		this.page.container.addClass("full-width");
		this.page.main.addClass("power-bi-page");
		this.page.main.html(`
			<div class="power-bi-shell">
				<div class="power-bi-container js-power-bi-container">
					<div class="power-bi-state js-power-bi-state">
						${__("Loading Power BI report...")}
					</div>
				</div>
			</div>
		`);
	}

	load_embed() {
		this.set_state(__("Loading Power BI client..."));
		this.load_power_bi_client()
			.then(() => this.fetch_reports())
			.then((reports) => {
				this.reports = reports || [];
				this.selected_report = this.get_selected_report();

				if (!this.selected_report) {
					if (this.route_name) {
						throw new Error(
							__("No Power BI report matches route {0}.", [this.route_name])
						);
					}

					throw new Error(__("No Power BI reports are configured in Power BI Settings."));
				}

				return this.fetch_embed_config(this.selected_report);
			})
			.then((config) => this.embed_report(config))
			.catch((error) => {
				const message =
					error && error.message ? error.message : __("Unable to load the Power BI report.");
				this.set_state(message, true);
			});
	}

	get_route_name() {
		const route = frappe.get_route();
		if (route.length <= 1 || !route[1]) {
			return null;
		}

		return route[1].toString().trim().toLowerCase().replace(/\s+/g, "-");
	}

	get_selected_report() {
		if (this.route_name) {
			return this.reports.find((row) => row.route_name === this.route_name) || null;
		}

		return this.reports[0] || null;
	}

	load_power_bi_client() {
		if (window.powerbi && window["powerbi-client"]) {
			return Promise.resolve();
		}

		return new Promise((resolve, reject) => {
			const existing = document.getElementById("his-power-bi-client");
			if (existing) {
				existing.addEventListener("load", resolve, { once: true });
				existing.addEventListener(
					"error",
					() => reject(new Error(__("Failed to load the Power BI client library."))),
					{ once: true }
				);
				return;
			}

			const script = document.createElement("script");
			script.id = "his-power-bi-client";
			script.src =
				"https://cdn.jsdelivr.net/npm/powerbi-client@2.23.1/dist/powerbi.min.js";
			script.onload = resolve;
			script.onerror = () =>
				reject(new Error(__("Failed to load the Power BI client library.")));
			document.head.appendChild(script);
		});
	}

	fetch_reports() {
		return new Promise((resolve, reject) => {
			frappe.call({
				method: "his.api.power_bi.get_available_reports",
				callback: (response) => {
					if (!response.exc) {
						resolve(response.message || []);
						return;
					}

					reject(new Error(__("The backend did not return Power BI reports.")));
				},
				error: (error) => {
					reject(new Error(this.get_server_error_message(error)));
				},
			});
		});
	}

	fetch_embed_config(report) {
		this.set_state(__("Requesting Power BI embed token..."));

		return new Promise((resolve, reject) => {
			frappe.call({
				method: "his.api.power_bi.get_embed_config",
				args: {
					route_name: report?.route_name,
					report_name: report?.report_name,
					report_url: report?.report_url,
					report_id: report?.report_id,
					workspace_id: report?.workspace_id,
				},
				callback: (response) => {
					if (!response.exc && response.message) {
						resolve(response.message);
						return;
					}

					reject(new Error(__("The backend did not return a Power BI embed configuration.")));
				},
				error: (error) => {
					const server_message = this.get_server_error_message(error);
					reject(new Error(server_message));
				},
			});
		});
	}

	embed_report(config) {
		if (!config.embed_url || !config.access_token || !config.report_id) {
			throw new Error(
				__("The backend response is missing report_id, embed_url, or access_token.")
			);
		}

		const models = window["powerbi-client"].models;
		const container = this.page.main.find(".js-power-bi-container").get(0);

		if (!container) {
			throw new Error(__("Missing Power BI container."));
		}

		window.powerbi.reset(container);

		const embed_config = {
			type: "report",
			id: config.report_id,
			embedUrl: config.embed_url,
			accessToken: config.access_token,
			tokenType: models.TokenType.Embed,
			settings: {
				filterPaneEnabled: false,
				navContentPaneEnabled: false,
				panes: {
					filters: {
						visible: false,
					},
					pageNavigation: {
						visible: false,
					},
				},
			},
		};

		container.innerHTML = "";
		const report = window.powerbi.embed(container, embed_config);

		report.off("loaded");
		report.off("error");

		report.on("loaded", () => {
			this.page.clear_indicator();
		});

		report.on("error", (event) => {
			const message = event?.detail?.message || __("Power BI returned an embedding error.");
			this.set_state(message, true);
		});
	}

	set_state(message, is_error) {
		const container = this.page.main.find(".js-power-bi-container").get(0);
		if (!container) {
			return;
		}

		container.innerHTML = `
			<div class="power-bi-state ${is_error ? "is-error" : ""}">
				<div>${frappe.utils.escape_html(message || "")}</div>
			</div>
		`;

		this.page.set_indicator(is_error ? __("Error") : __("External Service"), is_error ? "red" : "blue");
	}

	get_server_error_message(error) {
		const fallback = __("Unable to fetch the Power BI embed configuration.");
		const raw = error?._server_messages;

		if (raw) {
			try {
				const messages = JSON.parse(raw);
				if (Array.isArray(messages) && messages.length) {
					const first = JSON.parse(messages[0]);
					return first.message || fallback;
				}
			} catch (e) {
				return raw;
			}
		}

		return error?.message || fallback;
	}
}

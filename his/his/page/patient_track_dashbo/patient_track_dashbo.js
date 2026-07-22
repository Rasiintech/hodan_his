
frappe.pages["patient-track-dashbo"].on_page_load = function(wrapper) {
	new PatientTrackDashboardV2(wrapper);
};

class PatientTrackDashboardV2 {
	constructor(wrapper) {
		this.wrapper = $(wrapper);
		this.active_tab = "encounter";
		this.data = {};

		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Patient Track"),
			single_column: true,
		});

		this.page.wrapper.find(".page-head").hide();
		this.make_body();
		this.make_patient_selector();
		this.bind_events();
		this.load_from_route();
	}

	make_body() {
		this.$body = $(`
			<div class="pt-dashboard">
				<header class="pt-topbar">
					<div>
						<h1>${__("Patient Track")}</h1>
						<p>${__("Track patient journey from registration to lab result completion")}</p>
					</div>
					<div class="pt-actions">
						<button class="pt-action-btn js-print" type="button">${this.icon("printer")} <span>${__("Print")}</span></button>
						<button class="pt-action-btn js-refresh" type="button">${this.icon("refresh")} <span>${__("Refresh")}</span></button>
						<button class="pt-icon-btn" type="button" title="${__("More")}">${this.icon("dot-horizontal")}</button>
					</div>
				</header>

				<section class="pt-selector-card">
					<div class="pt-selector-label">${__("Select Patient")}</div>
					<div class="pt-select-control"></div>
					<div class="pt-doctor-control"></div>
					<div class="pt-from-date-control"></div>
					<div class="pt-to-date-control"></div>
				</section>

				<div class="pt-empty">
					<div class="pt-empty-title">${__("Choose a patient")}</div>
					<div class="pt-empty-subtitle">${__("Patient journey details will appear here.")}</div>
				</div>

				<div class="pt-content hide">
					<div class="pt-layout">
						<main class="pt-main">
							<section class="pt-card pt-patient-card"></section>
							<section class="pt-card pt-journey-card">
								<div class="pt-card-title">${__("Patient Journey")}</div>
								<div class="pt-journey"></div>
							</section>
							<section class="pt-metrics"></section>
							<section class="pt-card pt-tabs-card">
								<div class="pt-tabs">
									<button class="active" data-tab="encounter" type="button">${__("Encounter Details")}</button>
									<button data-tab="orders" type="button">${__("Orders")}</button>
									<button data-tab="lab" type="button">${__("Sample & Lab Result")}</button>
									<button data-tab="history" type="button">${__("History")}</button>
								</div>
								<div class="pt-tab-body"></div>
							</section>
						</main>

						<aside class="pt-side">
							<section class="pt-card pt-quick-links">
								<div class="pt-card-title">${__("Quick Links")}</div>
								<div class="pt-quick-list"></div>
							</section>
							<section class="pt-card pt-timeline-card">
								<div class="pt-card-title">${__("Timeline")}</div>
								<div class="pt-timeline"></div>
							</section>
						</aside>
					</div>
				</div>
			</div>
		`).appendTo(this.page.main);
	}

	make_patient_selector() {
		this.patient_field = frappe.ui.form.make_control({
			parent: this.$body.find(".pt-select-control"),
			df: {
				fieldtype: "Link",
				fieldname: "patient",
				label: "Patient",
				options: "Patient",
				placeholder: __("Search patient"),
				onchange: () => this.load(),
			},
			render_input: true,
		});

		this.from_date_field = frappe.ui.form.make_control({
			parent: this.$body.find(".pt-from-date-control"),
			df: {
				fieldtype: "Date",
				fieldname: "from_date",
				label: "From Date",
				onchange: () => this.load_if_patient_selected(),
			},
			render_input: true,
		});

		this.doctor_field = frappe.ui.form.make_control({
			parent: this.$body.find(".pt-doctor-control"),
			df: {
				fieldtype: "Link",
				fieldname: "practitioner",
				label: "Doctor",
				options: "Healthcare Practitioner",
				placeholder: __("Select doctor"),
				onchange: () => this.load_if_patient_selected(),
			},
			render_input: true,
		});

		this.to_date_field = frappe.ui.form.make_control({
			parent: this.$body.find(".pt-to-date-control"),
			df: {
				fieldtype: "Date",
				fieldname: "to_date",
				label: "To Date",
				onchange: () => this.load_if_patient_selected(),
			},
			render_input: true,
		});
	}

	bind_events() {
		this.$body.on("click", ".js-refresh", () => this.load());
		this.$body.on("click", ".js-print", () => window.print());
		this.$body.on("click", "[data-route-doctype]", (event) => {
			const $target = $(event.currentTarget);
			if ($target.hasClass("disabled")) return;
			frappe.set_route("Form", $target.data("route-doctype"), $target.data("route-name"));
		});
		this.$body.on("click", ".pt-tabs button", (event) => {
			this.active_tab = $(event.currentTarget).data("tab");
			this.render_tabs();
		});
	}

	load_from_route() {
		if (frappe.route_options) {
			if (frappe.route_options.practitioner || frappe.route_options.doctor) {
				this.doctor_field.set_value(frappe.route_options.practitioner || frappe.route_options.doctor);
			}
			if (frappe.route_options.patient) {
				this.patient_field.set_value(frappe.route_options.patient);
			}
			frappe.route_options = null;
		}
	}

	load_if_patient_selected() {
		if (this.patient_field.get_value()) {
			this.load();
		}
	}

	load() {
		const patient = this.patient_field.get_value();
		if (!patient) {
			this.show_empty();
			return;
		}

		frappe.call({
			method: "his.api.patient_track_dashboard.get_patient_track",
			args: {
				patient,
				practitioner: this.doctor_field.get_value(),
				from_date: this.from_date_field.get_value(),
				to_date: this.to_date_field.get_value(),
			},
			freeze: true,
			freeze_message: __("Loading patient track..."),
			callback: (response) => {
				this.data = response.message || {};
				this.ensure_patient_registration_time().then(() => this.render());
			},
		});
	}

	ensure_patient_registration_time() {
		if (this.patient_registration_time()) {
			return Promise.resolve();
		}

		const patient = this.data.patient || {};
		if (!patient.name) {
			return Promise.resolve();
		}

		return frappe.db.get_value("Patient", patient.name, "creation")
			.then((response) => {
				const creation = response?.message?.creation;
				if (!creation) return;

				this.data.patient.creation = creation;
				this.upsert_patient_registration_summary(creation);
			})
			.catch(() => null);
	}

	upsert_patient_registration_summary(creation) {
		this.data.summary = this.data.summary || [];
		let registration = this.summary_for("patient_registration");
		if (!registration.key) {
			registration = {
				key: "patient_registration",
				label: "Patient Registration Time",
				count: 1,
				doctype: "Patient",
				document: this.data.patient?.name || "",
			};
			this.data.summary.unshift(registration);
		}

		registration.first_time = registration.first_time || creation;
		registration.latest_time = registration.latest_time || creation;
	}

	show_empty() {
		this.$body.find(".pt-empty").removeClass("hide");
		this.$body.find(".pt-content").addClass("hide");
	}

	render() {
		this.$body.find(".pt-empty").addClass("hide");
		this.$body.find(".pt-content").removeClass("hide");
		this.render_patient_card();
		this.render_journey();
		this.render_metrics();
		this.render_quick_links();
		this.render_timeline();
		this.render_tabs();
	}

	render_patient_card() {
		const patient = this.data.patient || {};
		const encounter = this.event_for("encounter_creation", "latest") || {};
		const registration_time = this.patient_registration_time();
		const total_visit_time = this.total_visit_time();
		const status = this.current_status();
		const doctor = encounter.data?.practitioner_name || encounter.data?.practitioner || this.detail_value(encounter, "Practitioner") || this.selected_practitioner_display();
		const visit_type = encounter.data?.que_tye || this.detail_value(encounter, "Visit Type") || "OPD";

		this.$body.find(".pt-patient-card").html(`
			<div class="pt-avatar">${this.avatar(patient)}</div>
			<div class="pt-patient-info">
				<h2>${this.escape(patient.display_name || patient.patient_name || patient.name || "")}</h2>
				<div class="pt-info-grid">
					${this.info_item("users", "PID", patient.name)}
					${this.info_item("calendar", "Age / Gender", [patient.p_age, patient.sex].filter(Boolean).join(" / "))}
					${this.info_item("call", "Mobile", patient.mobile_no || patient.mobile)}
					${this.info_item("file", "Encounter", encounter.name)}
					${this.info_item("healthcare", "Visit Type", visit_type)}
					${this.info_item("customer", "Doctor", doctor)}
					${this.info_item("calendar", "Registration Time", this.format_datetime(registration_time))}
					${this.info_item("check", "Current Status", `<span class="pt-green-pill">${this.escape(status)}</span>`, true)}
					${this.info_item("today", "Total Visit Time", total_visit_time)}
				</div>
			</div>
		`);
	}

	render_journey() {
		const stages = this.journey_stages();
		const html = stages.map((stage, index) => `
			<div class="pt-journey-step ${stage.time ? "complete" : "pending"}">
				<div class="pt-node ${stage.color}">
					${this.icon(stage.icon, "lg")}
					<span>${this.icon("check", "xs")}</span>
				</div>
				<div class="pt-step-title">${index + 1}. ${this.escape(stage.label)}</div>
				<div class="pt-step-date">${this.format_date(stage.time) || "-"}</div>
				<div class="pt-step-time">${this.format_time(stage.time) || ""}</div>
				<div class="pt-step-status">${stage.time ? __("Completed") : __("Pending")}</div>
			</div>
			${index < stages.length - 1 ? `<div class="pt-step-arrow">${this.icon("arrow-right")}</div>` : ""}
		`).join("");

		this.$body.find(".pt-journey").html(html);
	}

	render_metrics() {
		const stats = [
			{ label: "Total Waiting Time", value: this.duration_between(this.summary_for("que_creation").first_time, this.summary_for("encounter_creation").first_time), icon: "today", color: "amber" },
			{ label: "Total Process Time", value: this.duration_between(this.summary_for("que_creation").first_time, this.summary_for("lab_result_creation").latest_time || this.latest_event_time()), icon: "refresh", color: "blue" },
			{ label: "Total Visit Time", value: this.total_visit_time(), icon: "calendar", color: "blue" },
		];

		this.$body.find(".pt-metrics").html(stats.map((stat) => `
			<div class="pt-metric">
				<div class="pt-metric-icon ${stat.color}">${this.icon(stat.icon)}</div>
				<div>
					<div class="pt-metric-label">${this.escape(__(stat.label))}</div>
					<div class="pt-metric-value ${stat.paid ? "paid" : ""}">${this.escape(stat.value || "-")}</div>
				</div>
			</div>
		`).join(""));
	}

	render_quick_links() {
		const links = [
			{ label: "View Patient", doctype: "Patient", name: this.data.patient?.name, icon: "users", color: "blue" },
			{ label: "View Encounter", event_key: "encounter_creation", icon: "file", color: "blue" },
			{ label: "View Sales Order", event_key: "sales_order_creation", icon: "file", color: "amber" },
			{ label: "View Sample Collection", event_key: "sample_collection_creation", icon: "healthcare", color: "purple" },
			{ label: "View Lab Result", event_key: "lab_result_creation", icon: "clipboard", color: "purple" },
		].map((link) => {
			if (link.event_key) {
				const event = this.event_for(link.event_key, "latest") || {};
				link.doctype = event.doctype;
				link.name = event.name;
			}
			return link;
		});

		this.$body.find(".pt-quick-list").html(links.map((link) => `
			<button
				class="pt-quick-link ${link.name ? "" : "disabled"}"
				type="button"
				data-route-doctype="${this.escape_attr(link.doctype || "")}"
				data-route-name="${this.escape_attr(link.name || "")}"
			>
				<span class="pt-quick-icon ${link.color}">${this.icon(link.icon)}</span>
				<span>${this.escape(__(link.label))}</span>
				${this.icon("right")}
			</button>
		`).join(""));
	}

	render_timeline() {
		const items = this.timeline_items();
		this.$body.find(".pt-timeline").html(items.map((item) => `
			<div class="pt-timeline-item">
				<div class="pt-dot"></div>
				<div>
					<div class="pt-timeline-date">${this.escape(this.format_datetime(item.time))}</div>
					<div class="pt-timeline-label">${this.escape(item.label)}</div>
				</div>
			</div>
		`).join("") || `<div class="pt-muted">${__("No timeline available")}</div>`);
	}

	render_tabs() {
		this.$body.find(".pt-tabs button").removeClass("active");
		this.$body.find(`.pt-tabs button[data-tab="${this.active_tab}"]`).addClass("active");

		const renderers = {
			encounter: () => this.encounter_tab(),
			orders: () => this.orders_tab(),
			lab: () => this.lab_tab(),
			history: () => this.history_tab(),
		};
		this.$body.find(".pt-tab-body").html((renderers[this.active_tab] || renderers.encounter)());
	}

	encounter_tab() {
		const encounter = this.event_for("encounter_creation", "latest") || {};
		const data = encounter.data || {};
		const visit_type = data.que_tye || this.detail_value(encounter, "Visit Type") || "OPD";
		const doctor = data.practitioner_name || data.practitioner || this.detail_value(encounter, "Practitioner");
		const department = data.medical_department || this.detail_value(encounter, "Department");
		const chief_complaint = data.chief_complaint_f || data.cheif_complaint || this.detail_value(encounter, "Chief Complaint");
		const differential_diagnosis = data.differential_diagnosis || data.differential__diagnosis || this.detail_value(encounter, "Differential Diagnosis");
		const notes = this.strip_html(data.management_plan) || __("Not recorded");

		return `
			<div class="pt-detail-grid">
				${this.detail_card("Encounter Information", [
					["Encounter ID", encounter.name],
					["Visit Type", visit_type],
					["Doctor", doctor],
					["Department", department],
					["Notes", notes],
				])}
				${this.detail_card("Vitals", [
					["Temperature", __("Not recorded")],
					["Blood Pressure", __("Not recorded")],
					["Pulse", __("Not recorded")],
					["Respiratory Rate", __("Not recorded")],
					["Weight", __("Not recorded")],
					["Height", __("Not recorded")],
				])}
				${this.detail_card("Diagnosis & Prescription", [
					["Chief Complaint", chief_complaint],
					["Differential Diagnosis", differential_diagnosis],
					["Prescription", __("Not recorded")],
					["Follow Up", data.custom_follow_up_date || data.fallow_up_days],
					["Remarks", notes],
				])}
			</div>
		`;
	}

	orders_tab() {
		const rows = [
			...this.events_for("sales_order_creation"),
		];
		return this.document_table(rows, ["Document", "Type", "Time", "Status", "Amount"]);
	}

	lab_tab() {
		const rows = [
			...this.events_for("sample_collection_creation"),
			...this.events_for("lab_result_creation"),
			...this.events_for("lab_result_submitted"),
		];
		return this.document_table(rows, ["Document", "Type", "Time", "Status", "Reference"]);
	}

	history_tab() {
		return this.document_table(this.visible_events(), ["Stage", "Document", "Time", "Status", "Details"]);
	}

	document_table(rows, columns) {
		if (!rows.length) {
			return `<div class="pt-muted">${__("No records found")}</div>`;
		}

		return `
			<div class="pt-mini-table-wrap">
				<table class="pt-mini-table">
					<thead><tr>${columns.map((column) => `<th>${this.escape(__(column))}</th>`).join("")}</tr></thead>
					<tbody>
						${rows.map((row) => `
							<tr>
								${columns.map((column) => `<td>${this.table_cell(row, column)}</td>`).join("")}
							</tr>
						`).join("")}
					</tbody>
				</table>
			</div>
		`;
	}

	table_cell(row, column) {
		if (column === "Stage") return this.escape(row.stage || "");
		if (column === "Document") return row.name ? `<button class="pt-inline-link" data-route-doctype="${this.escape_attr(row.doctype)}" data-route-name="${this.escape_attr(row.name)}">${this.escape(row.name)}</button>` : "-";
		if (column === "Type") return this.escape(row.doctype || "");
		if (column === "Time") return this.escape(this.format_datetime(row.time));
		if (column === "Status") return this.escape(row.status || "-");
		if (column === "Amount") return this.escape(this.format_currency(row.data?.grand_total));
		if (column === "Reference") return this.escape(row.data?.reff_collection || row.data?.reff_invoice || row.data?.lab_ref || "-");
		if (column === "Details") return this.escape((row.details || []).join(", ") || "-");
		return "";
	}

	detail_card(title, rows) {
		return `
			<div class="pt-detail-card">
				<h3>${this.escape(__(title))}</h3>
				${rows.map(([label, value]) => `
					<div class="pt-detail-row">
						<span>${this.escape(__(label))}</span>
						<strong>${this.escape(value || "-")}</strong>
					</div>
				`).join("")}
			</div>
		`;
	}

	info_item(icon, label, value, value_is_html) {
		return `
			<div class="pt-info-item">
				${this.icon(icon)}
				<span>${this.escape(__(label))}</span>
				<strong>${value_is_html ? value : this.escape(value || "-")}</strong>
			</div>
		`;
	}

	journey_stages() {
		const que = this.summary_for("que_creation");
		const lab_submitted = this.summary_for("lab_result_submitted");
		return [
			{ label: "Registration", time: this.patient_registration_time(), icon: "users", color: "blue" },
			{ label: "Queue", time: que.latest_time || que.first_time, icon: "users", color: "blue" },
			{ label: "Patient Encounter", time: this.summary_for("encounter_creation").latest_time, icon: "healthcare", color: "green" },
			{ label: "Sales Order", time: this.summary_for("sales_order_creation").latest_time, icon: "file", color: "amber" },
			{ label: "Sales Invoice", time: this.summary_for("sales_invoice_creation").latest_time, icon: "money-coins-1", color: "pink" },
			{ label: "Sample Collection", time: this.summary_for("sample_collection_creation").latest_time, icon: "healthcare", color: "purple" },
			{ label: "Lab Result Created", time: this.summary_for("lab_result_creation").latest_time, icon: "clipboard", color: "teal" },
			{ label: "Lab Result Submitted", time: lab_submitted.latest_time, icon: "check", color: "green" },
		];
	}

	timeline_items() {
		const encounter = this.event_for("encounter_creation", "latest") || {};
		const doctor = encounter.data?.practitioner_name || this.detail_value(encounter, "Practitioner");
		const labels = {
			"Registration": "Registered",
			"Queue": "In Queue",
			"Patient Encounter": doctor ? `Encounter with ${doctor}` : "Encounter Created",
			"Sales Order": "Sales Order Created",
			"Sample Collection": "Sample Collected",
			"Lab Result Created": "Lab Result Created",
			"Lab Result Submitted": "Lab Result Submitted",
		};
		return this.journey_stages()
			.filter((stage) => stage.label !== "Sales Invoice")
			.map((stage) => ({ time: stage.time, label: labels[stage.label] }))
			.filter((item) => item.time);
	}

	summary_for(key) {
		return (this.data.summary || []).find((item) => item.key === key) || {};
	}

	patient_registration_time() {
		const registration = this.summary_for("patient_registration");
		const patient = this.data.patient || {};
		return registration.first_time || registration.latest_time || patient.creation || "";
	}

	selected_practitioner_display() {
		const practitioner = this.data.practitioner || {};
		return practitioner.display_name || practitioner.practitioner_name || practitioner.name || this.doctor_field?.get_value() || "";
	}

	events_for(key) {
		return (this.data.events || []).filter((event) => event.stage_key === key);
	}

	event_for(key, direction) {
		const events = this.events_for(key);
		if (!events.length) return null;
		return direction === "first" ? events[0] : events[events.length - 1];
	}

	latest_event_time() {
		const events = this.visible_events();
		return events.length ? events[events.length - 1].time : "";
	}

	current_status() {
		if (this.summary_for("lab_result_submitted").latest_time) return "Lab Result Submitted";
		const events = this.visible_events();
		const latest = events[events.length - 1] || {};
		return latest.stage ? latest.stage.replace(" Time", "") : "In Progress";
	}

	total_visit_time() {
		const events = this.visible_events();
		if (!events.length) return "-";
		return this.duration_between(events[0].time, events[events.length - 1].time);
	}

	visible_events() {
		return (this.data.events || []).filter((event) => !["patient_registration", "sales_invoice_creation"].includes(event.stage_key));
	}

	duration_between(start, end) {
		const start_date = this.to_date(start);
		const end_date = this.to_date(end);
		if (!start_date || !end_date || end_date < start_date) return "-";
		const minutes = Math.round((end_date - start_date) / 60000);
		const hours = Math.floor(minutes / 60);
		const remaining = minutes % 60;
		if (hours && remaining) return `${hours}h ${remaining}m`;
		if (hours) return `${hours}h`;
		return `${remaining}m`;
	}

	format_datetime(value) {
		if (!value) return "";
		return frappe.datetime.str_to_user(value);
	}

	format_date(value) {
		if (!value) return "";
		return frappe.datetime.str_to_user(String(value).slice(0, 10));
	}

	format_time(value) {
		if (!value || !String(value).includes(" ")) return "";
		return String(value).split(" ")[1].slice(0, 5);
	}

	format_currency(value) {
		const amount = this.number(value);
		if (!amount) return "-";
		return frappe.format(amount, { fieldtype: "Currency" });
	}

	to_date(value) {
		if (!value) return null;
		return new Date(String(value).replace(" ", "T"));
	}

	number(value) {
		const number = Number(value);
		return Number.isFinite(number) ? number : 0;
	}

	detail_value(event, label) {
		const detail = (event.details || []).find((item) => item.startsWith(`${label}:`));
		return detail ? detail.split(":").slice(1).join(":").trim() : "";
	}

	avatar(patient) {
		if (patient.image) {
			return `<img src="${this.escape_attr(patient.image)}" alt="${this.escape_attr(patient.display_name || patient.name)}">`;
		}
		const name = patient.display_name || patient.patient_name || patient.name || "";
		const initials = name.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
		return `<div class="pt-avatar-fallback">${this.escape(initials || "P")}</div>`;
	}

	icon(name, size) {
		return frappe.utils.icon(name, size || "sm");
	}

	strip_html(value) {
		return $("<div>").html(value || "").text().trim();
	}

	escape(value) {
		return frappe.utils.escape_html(String(value || ""));
	}

	escape_attr(value) {
		return this.escape(value).replace(/"/g, "&quot;");
	}
}

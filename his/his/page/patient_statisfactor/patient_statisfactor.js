// frappe.pages['patient-statisfactor'].on_page_load = function(wrapper) {
//     const page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: 'Patient Satisfaction Dashboard',
//         single_column: true
//     });

//     // 1. Ensure Chart.js is available
//     function init() {
//         if (typeof Chart === 'undefined') {
//             let s = document.createElement('script');
//             s.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js';
//             s.onload = build;
//             s.onerror = () => $(page.body).append(
//                 `<div class="alert alert-danger">Failed to load Chart.js.</div>`
//             );
//             document.head.appendChild(s);
//         } else {
//             build();
//         }
//     }

//     // 2. Build the dashboard
//     function build() {
//         // clear and setup containers
//         $(page.body).empty()
//             .append(`<div id="cards" style="display:flex;flex-wrap:wrap;gap:20px;padding:20px;"></div>`)
//             .append(`<h2 style="padding:0 20px;">Survey Sentiment Charts</h2>`)
//             .append(`<div id="charts" style="display:flex;flex-wrap:wrap;gap:20px;padding:20px;"></div>`);

//         frappe.call({
//             method: 'his.api.patient_statisfactory_dashboard.get_patient_survey_data',
//             callback: render,
//             error: () => $('#cards').append(
//                 `<div class="alert alert-danger">Unable to fetch data.</div>`
//             )
//         });
//     }

//     // 3. Render cards + charts
//     function render(r) {
//         const data = r.message[0] || {};
//         const surveyComments = r.message[1] || {};
//         const $cards = $('#cards');
//         const $charts = $('#charts');

//         Object.entries(data).forEach(([category, counts]) => {
//             // ensure numeric
//             const happy = parseInt(counts.happy, 10) || 0;
//             const unhappy = parseInt(counts.unhappy, 10) || 0;

//             // summary cards
//             $cards.append(`
//                 <div style="
//                     flex:1 1 220px;
//                     padding:20px;
//                     border-radius:12px;
//                     box-shadow:0 4px 12px rgba(0,0,0,0.08);
//                     background-color:#e6ffed;
//                     border-left:5px solid #4caf50;
//                     text-align:center;
//                     font-family:sans-serif;
//                 ">
//                     <h3 style="margin-bottom:10px;color:#333;font-size:1.1em;">
//                         ${category} Happy
//                     </h3>
//                     <p style="font-size:2.5em;font-weight:bold;color:#2e7d32;">
//                         ${happy}
//                     </p>
//                 </div>
//             `);
//             $cards.append(`
//                 <div style="
//                     flex:1 1 220px;
//                     padding:20px;
//                     border-radius:12px;
//                     box-shadow:0 4px 12px rgba(0,0,0,0.08);
//                     background-color:#ffebee;
//                     border-left:5px solid #f44336;
//                     text-align:center;
//                     font-family:sans-serif;
//                 ">
//                     <h3 style="margin-bottom:10px;color:#333;font-size:1.1em;">
//                         ${category} Unhappy
//                     </h3>
//                     <p style="font-size:2.5em;font-weight:bold;color:#c62828;">
//                         ${unhappy}
//                     </p>
//                 </div>
//             `);

//             // sanitize id
//             const safeId = category.replace(/[^\w]/g, '-').toLowerCase();
//             const doughnutId = `doughnut-${safeId}`;
//             const barId = `bar-${safeId}`;

//             $charts.append(`
//                 <div style="
//                     flex:1 1 45%;
//                     min-width:350px;
//                     padding:20px;
//                     background:#fff;
//                     border-radius:12px;
//                     box-shadow:0 2px 8px rgba(0,0,0,0.05);
//                 ">
//                     <h4 style="text-align:center;font-family:sans-serif;margin-bottom:20px;">
//                         ${category} Sentiment Breakdown
//                     </h4>
//                     <div style="display:flex;gap:20px;justify-content:center;">
//                         <div style="position:relative;width:250px;height:250px;">
//                             <canvas id="${doughnutId}"></canvas>
//                         </div>
//                         <div style="position:relative;width:300px;height:300px;">
//                             <canvas id="${barId}"></canvas>
//                         </div>
//                     </div>
//                 </div>
//             `);

//             // draw charts
//             drawDoughnut(doughnutId, happy, unhappy);
//             // drawBar(barId, happy, unhappy);
//         });
//     }

//     // 4a. Doughnut
//     function drawDoughnut(id, h, u) {
//         const ctx = document.getElementById(id).getContext('2d');
//         new Chart(ctx, {
//             type: 'doughnut',
//             data: {
//                 labels: ['Happy', 'Unhappy'],
//                 datasets: [{
//                     data: [h, u],
//                     backgroundColor: ['#4caf50', '#f44336'],
//                     borderColor: ['#fff', '#fff'],
//                     borderWidth: 2
//                 }]
//             },
//             options: {
//                 responsive: true,
//                 maintainAspectRatio: false,
//                 plugins: {
//                     legend: { position: 'top' },
//                     title: { display: true, text: 'Proportion' }
//                 }
//             }
//         });
//     }

//     // kick things off
//     init();
// };


frappe.pages['patient-statisfactor'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Patient Satisfaction Dashboard',
        single_column: true
    });

    function init() {
        if (typeof Chart === 'undefined') {
            let s = document.createElement('script');
            s.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js';
            s.onload = build;
            s.onerror = () => $(page.body).append(
                `<div class="alert alert-danger">Failed to load Chart.js.</div>`
            );
            document.head.appendChild(s);
        } else {
            build();
        }
    }

    function build() {
        $(page.body).empty()
            .append(`<div id="cards" style="display:flex;flex-wrap:wrap;gap:20px;padding:20px;"></div>`)
            .append(`<h2 style="padding:0 20px;">Survey Sentiment Charts</h2>`)
            .append(`<div id="charts" style="display:flex;flex-wrap:wrap;gap:20px;padding:20px;"></div>`)
            .append(`<h2 style="padding:0 20px;">Survey Comments</h2>`)
            .append(`<div id="comments" style="display:flex;flex-wrap:wrap;gap:20px;padding:20px;"></div>`);

        frappe.call({
            method: 'his.api.patient_statisfactory_dashboard.get_patient_survey_data',
            callback: render,
            error: () => $('#cards').append(
                `<div class="alert alert-danger">Unable to fetch data.</div>`
            )
        });
    }

    function esc(str) {
        return String(str).replace(/[&<>"']/g, s => ({
            '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
        }[s]));
    }

    function render(r) {
        const data = r.message?.[0] || {};
        const surveyComments = r.message?.[1] || {}; // now actual comments keyed by category
        const $cards = $('#cards');
        const $charts = $('#charts');
        const $comments = $('#comments');

        Object.entries(data).forEach(([category, counts]) => {
            const happy = parseInt(counts.happy, 10) || 0;
            const unhappy = parseInt(counts.unhappy, 10) || 0;
            const comments = Array.isArray(surveyComments[category]) ? surveyComments[category] : [];

            // summary cards
            $cards.append(`
                <div style="flex:1 1 220px;padding:20px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.08);background-color:#e6ffed;border-left:5px solid #4caf50;text-align:center;font-family:sans-serif;">
                    <h3 style="margin-bottom:10px;color:#333;font-size:1.1em;">${category} Happy</h3>
                    <p style="font-size:2.5em;font-weight:bold;color:#2e7d32;">${happy}</p>
                </div>
            `);
            $cards.append(`
                <div style="flex:1 1 220px;padding:20px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.08);background-color:#ffebee;border-left:5px solid #f44336;text-align:center;font-family:sans-serif;">
                    <h3 style="margin-bottom:10px;color:#333;font-size:1.1em;">${category} Unhappy</h3>
                    <p style="font-size:2.5em;font-weight:bold;color:#c62828;">${unhappy}</p>
                </div>
            `);

            // charts
            const safeId = category.replace(/[^\w]/g, '-').toLowerCase();
            const doughnutId = `doughnut-${safeId}`;

            $charts.append(`
                <div style="flex:1 1 45%;min-width:350px;padding:20px;background:#fff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                    <h4 style="text-align:center;font-family:sans-serif;margin-bottom:20px;">${category} Sentiment Breakdown</h4>
                    <div style="display:flex;gap:20px;justify-content:center;">
                        <div style="position:relative;width:250px;height:250px;">
                            <canvas id="${doughnutId}"></canvas>
                        </div>
                    </div>
                </div>
            `);

            drawDoughnut(doughnutId, happy, unhappy);

            // comments panel (shows up to 10, scrollable if many)
            $comments.append(`
                <div style="flex:1 1 45%;min-width:350px;padding:20px;background:#fff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                    <h4 style="margin-bottom:12px;font-family:sans-serif;">
                        ${category} Comments <span style="font-weight:normal;color:#666;">(${comments.length})</span>
                    </h4>
                    <div style="max-height:220px;overflow:auto;border:1px solid #eee;border-radius:8px;padding:10px;">
                        ${
                            comments.length
                              ? `<ul style="padding-left:18px;margin:0;">${
                                    comments.slice(0, 10).map(c => `<li style="margin:6px 0;line-height:1.4;">${esc(c)}</li>`).join('')
                                }</ul>`
                              : `<em style="color:#888;">No comments found.</em>`
                        }
                    </div>
                </div>
            `);
        });
    }

    function drawDoughnut(id, h, u) {
        const ctx = document.getElementById(id).getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Happy', 'Unhappy'],
                datasets: [{
                    data: [h, u],
                    backgroundColor: ['#4caf50', '#f44336'],
                    borderColor: ['#fff', '#fff'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    title: { display: true, text: 'Proportion' }
                }
            }
        });
    }

    init();
};

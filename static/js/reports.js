/**
 * ====================================================================
 * E-Learning Course Analytics System - Reports JavaScript
 * File: static/js/reports.js
 * ====================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initial reports load
    loadReportCompletion();
    loadReportComparison();
    loadReportLearnerPerf();
    loadReportActivityPart();
    loadReportWeekly();
    loadReportInactive();
    loadLearnerDepartmentOptions();

    // Matplotlib chart generation button
    const btnGenerateCharts = document.getElementById('btnGenerateMatplotlib');
    if (btnGenerateCharts) {
        btnGenerateCharts.addEventListener('click', handleGenerateCharts);
    }

    // Learner report filter button & input
    const btnFilterLearner = document.getElementById('btnFilterLearnerReport');
    if (btnFilterLearner) {
        btnFilterLearner.addEventListener('click', () => {
            const search = document.getElementById('reportLearnerSearch')?.value.trim() || '';
            const dept = document.getElementById('reportLearnerDept')?.value || '';
            loadReportLearnerPerf(search, dept);
        });
    }

    const inputLearnerSearch = document.getElementById('reportLearnerSearch');
    if (inputLearnerSearch) {
        inputLearnerSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const search = inputLearnerSearch.value.trim();
                const dept = document.getElementById('reportLearnerDept')?.value || '';
                loadReportLearnerPerf(search, dept);
            }
        });
    }

    const selectLearnerDept = document.getElementById('reportLearnerDept');
    if (selectLearnerDept) {
        selectLearnerDept.addEventListener('change', () => {
            const search = document.getElementById('reportLearnerSearch')?.value.trim() || '';
            const dept = selectLearnerDept.value;
            loadReportLearnerPerf(search, dept);
        });
    }

    // Weekly date filter
    const btnFilterWeekly = document.getElementById('btnFilterWeeklyReport');
    if (btnFilterWeekly) {
        btnFilterWeekly.addEventListener('click', () => {
            const start = document.getElementById('reportWeeklyStart').value;
            const end = document.getElementById('reportWeeklyEnd').value;
            loadReportWeekly(start, end);
        });
    }

    // Inactive threshold filter
    const btnFilterInactive = document.getElementById('btnFilterInactiveReport');
    if (btnFilterInactive) {
        btnFilterInactive.addEventListener('click', () => {
            const threshold = document.getElementById('reportInactiveThreshold').value || 14;
            loadReportInactive(threshold);
        });
    }
});

async function loadLearnerDepartmentOptions() {
    const deptSelect = document.getElementById('reportLearnerDept');
    if (!deptSelect) return;
    try {
        const res = await fetch('/api/learners/departments');
        const json = await res.json();
        const depts = json.data || [];
        deptSelect.innerHTML = '<option value="">All Departments</option>' +
            depts.map(d => `<option value="${escapeHtml(d)}">${escapeHtml(d)}</option>`).join('');
    } catch (err) {
        console.error('Failed to load department options:', err);
    }
}

async function handleGenerateCharts() {
    const btn = document.getElementById('btnGenerateMatplotlib');
    const container = document.getElementById('chartGenerationContainer');
    const imgCompletion = document.getElementById('imgCompletionChart');
    const imgWeekly = document.getElementById('imgWeeklyChart');
    const imgActivityType = document.getElementById('imgActivityTypeChart');
    const imgEngagement = document.getElementById('imgEngagementChart');
    const timestampEl = document.getElementById('chartTimestamp');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Generating Matplotlib Figures...';

    try {
        const res = await fetch('/api/reports/generate-charts', { method: 'POST' });
        const json = await res.json();

        if (res.ok && json.success) {
            showToast(json.message || 'Charts generated successfully!', 'success');
            const cacheBuster = `?t=${new Date().getTime()}`;
            if (imgCompletion) imgCompletion.src = `/static/charts/course_completion_bar.png${cacheBuster}`;
            if (imgWeekly) imgWeekly.src = `/static/charts/weekly_activity_trend.png${cacheBuster}`;
            if (imgActivityType) imgActivityType.src = `/static/charts/activity_type_distribution.png${cacheBuster}`;
            if (imgEngagement) imgEngagement.src = `/static/charts/course_engagement_comparison.png${cacheBuster}`;
            if (timestampEl) timestampEl.textContent = `Generated: ${json.timestamp}`;
            container.classList.remove('d-none');
            container.scrollIntoView({ behavior: 'smooth' });
        } else {
            showToast(json.message || json.error || 'Failed to generate charts.', 'danger');
        }
    } catch (err) {
        showToast('Network error while generating backend charts.', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-file-image me-1"></i> Generate Backend Matplotlib Charts';
    }
}

async function loadReportCompletion() {
    const tbody = document.getElementById('tbodyReportCompletion');
    try {
        const res = await fetch('/api/analytics/course-completion');
        const json = await res.json();
        const data = json.data || [];

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">No course data available.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(c => `
            <tr>
                <td class="fw-semibold">${escapeHtml(c.course_name)}</td>
                <td><span class="badge bg-light text-secondary border">${escapeHtml(c.category)}</span></td>
                <td class="text-center fw-bold">${c.total_enrollments}</td>
                <td class="text-center text-success fw-bold">${c.completed_enrollments}</td>
                <td class="text-center text-warning fw-bold">${c.in_progress_enrollments}</td>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <span class="small fw-bold">${c.completion_rate.toFixed(1)}%</span>
                        <div class="progress flex-grow-1" style="height: 6px;">
                            <div class="progress-bar ${c.completion_rate >= 50 ? 'bg-success' : 'bg-warning'}" style="width: ${c.completion_rate}%;"></div>
                        </div>
                    </div>
                </td>
                <td class="text-center">
                    <span class="badge ${c.badge_color === 'success' ? 'badge-soft-success' : c.badge_color === 'primary' ? 'badge-soft-primary' : 'badge-soft-warning'}">${c.performance_status}</span>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-danger">Failed to load report.</td></tr>';
    }
}

async function loadReportComparison() {
    const tbody = document.getElementById('tbodyReportComparison');
    try {
        const res = await fetch('/api/analytics/course-comparison');
        const json = await res.json();
        const data = json.data || [];

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">No comparison data available.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(c => `
            <tr>
                <td class="fw-semibold">${escapeHtml(c.course_name)}</td>
                <td><span class="badge bg-light text-secondary border">${escapeHtml(c.category)}</span></td>
                <td class="text-center fw-bold">${c.total_enrollments}</td>
                <td class="text-center text-success">${c.completed_enrollments}</td>
                <td class="text-center fw-bold text-primary">${c.total_activities}</td>
                <td class="text-center">${c.avg_activities_per_learner.toFixed(1)}</td>
                <td class="text-center fw-bold">${c.completion_rate.toFixed(1)}%</td>
                <td class="text-center"><span class="badge ${c.badge_color === 'success' ? 'badge-soft-success' : 'badge-soft-primary'}">${c.performance_status}</span></td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-danger">Failed to load report.</td></tr>';
    }
}

async function loadReportWeekly(startDate = '', endDate = '') {
    const tbody = document.getElementById('tbodyReportWeekly');
    const exportCsv = document.getElementById('btnExportWeeklyCsv');
    const exportJson = document.getElementById('btnExportWeeklyJson');
    const exportPdf = document.getElementById('btnExportWeeklyPdf');
    const exportPrint = document.getElementById('btnExportWeeklyPrint');

    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const q = params.toString() ? '?' + params.toString() : '';

    if (exportCsv) exportCsv.href = `/api/reports/weekly-activity.csv${q}`;
    if (exportJson) exportJson.href = `/api/reports/weekly-activity.json${q}`;
    if (exportPdf) exportPdf.href = `/api/reports/weekly-activity.pdf${q}`;
    if (exportPrint) exportPrint.href = `/reports/printable/weekly-activity${q}`;

    try {
        const res = await fetch(`/api/analytics/weekly-activity${q}`);
        const json = await res.json();
        const data = json.data || [];

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">No weekly activity found for this period.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(w => `
            <tr>
                <td class="fw-semibold">${w.week_label}</td>
                <td><code>${w.iso_week}</code></td>
                <td>${w.week_start}</td>
                <td class="text-center fw-bold text-primary">${w.total}</td>
                <td class="text-center text-success fw-semibold">${w.completed}</td>
                <td class="text-center text-danger fw-semibold">${w.incomplete}</td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-danger">Failed to load report.</td></tr>';
    }
}

async function loadReportInactive(threshold = 14) {
    const tbody = document.getElementById('tbodyReportInactive');
    const exportCsv = document.getElementById('btnExportInactiveCsv');
    const exportJson = document.getElementById('btnExportInactiveJson');
    const exportPdf = document.getElementById('btnExportInactivePdf');
    const exportPrint = document.getElementById('btnExportInactivePrint');

    const q = `?threshold=${threshold}`;
    if (exportCsv) exportCsv.href = `/api/reports/inactive-enrollments.csv${q}`;
    if (exportJson) exportJson.href = `/api/reports/inactive-enrollments.json${q}`;
    if (exportPdf) exportPdf.href = `/api/reports/inactive-enrollments.pdf${q}`;
    if (exportPrint) exportPrint.href = `/reports/printable/inactive-enrollments${q}`;

    try {
        const res = await fetch(`/api/analytics/inactive-enrollments${q}`);
        const json = await res.json();
        const data = json.data || [];

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-success fw-medium"><i class="bi bi-check-circle-fill me-1"></i> No inactive enrollments found for threshold of ${threshold} days!</td></tr>`;
            return;
        }

        tbody.innerHTML = data.map(i => `
            <tr>
                <td><span class="roll-no-badge font-monospace">${escapeHtml(i.roll_no)}</span></td>
                <td class="fw-bold text-navy">${escapeHtml(i.course_name)}</td>
                <td><span class="badge bg-light text-secondary border">${escapeHtml(i.category)}</span></td>
                <td>${escapeHtml(i.enrolled_at)}</td>
                <td>${escapeHtml(i.last_activity_date)}</td>
                <td class="text-center"><span class="badge bg-danger-subtle text-danger fw-bold">${i.days_since_last_activity} d</span></td>
                <td><span class="badge badge-soft-warning">${escapeHtml(i.status)}</span></td>
                <td><small class="text-muted">${escapeHtml(i.inactivity_reason)}</small></td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-danger">Failed to load report.</td></tr>';
    }
}

async function loadReportLearnerPerf(search = '', department = '') {
    const tbody = document.getElementById('tbodyReportLearnerPerf');
    const exportCsv = document.getElementById('btnExportLearnerCsv');
    const exportJson = document.getElementById('btnExportLearnerJson');
    const exportPdf = document.getElementById('btnExportLearnerPdf');
    const exportPrint = document.getElementById('btnExportLearnerPrint');
    if (!tbody) return;

    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (department) params.append('department', department);
    const q = params.toString() ? '?' + params.toString() : '';

    if (exportCsv) exportCsv.href = `/api/reports/learner-performance.csv${q}`;
    if (exportJson) exportJson.href = `/api/reports/learner-performance.json${q}`;
    if (exportPdf) exportPdf.href = `/api/reports/learner-performance.pdf${q}`;
    if (exportPrint) exportPrint.href = `/reports/printable/learner-performance${q}`;

    try {
        const res = await fetch(`/api/analytics/learner-performance${q}`);
        const json = await res.json();
        const data = json.data || [];

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center py-4 text-muted">No learners match the specified filters.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(l => {
            const initials = l.name ? l.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : (l.roll_no ? l.roll_no.substring(0, 2) : 'ST');
            const scoreDisplay = l.average_score !== null && l.average_score !== undefined
                ? `<span class="badge bg-light text-primary border">${l.average_score.toFixed(1)}%</span>`
                : '<span class="text-muted small">—</span>';
            const timeDisplay = l.total_time_spent_minutes !== null && l.total_time_spent_minutes !== undefined
                ? `<span class="badge bg-light text-secondary border">${l.total_time_spent_minutes}m</span>`
                : '<span class="text-muted small">—</span>';
            const statusClass = l.badge_class || 'badge-soft-secondary';

            return `
                <tr>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <div class="avatar-initials" style="width: 28px; height: 28px; font-size: 0.7rem;">${escapeHtml(initials)}</div>
                            <div>
                                <span class="roll-no-badge font-monospace">${escapeHtml(l.roll_no)}</span>
                                <div class="fw-semibold text-navy small">${escapeHtml(l.name || 'Student')}</div>
                            </div>
                        </div>
                    </td>
                    <td><span class="badge bg-light text-secondary border">${escapeHtml(l.department || 'General')}</span></td>
                    <td class="text-center fw-bold">${l.enrolled_courses_count}</td>
                    <td class="text-center text-success fw-bold">${l.completed_courses_count}</td>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <span class="small fw-bold">${l.completion_rate.toFixed(1)}%</span>
                            <div class="progress flex-grow-1" style="height: 6px; width: 60px;">
                                <div class="progress-bar ${l.completion_rate >= 50 ? 'bg-success' : 'bg-warning'}" style="width: ${l.completion_rate}%;"></div>
                            </div>
                        </div>
                    </td>
                    <td class="text-center"><span class="badge bg-light text-secondary border">${l.completed_activities_count}/${l.total_activities_logged}</span></td>
                    <td class="text-center">${scoreDisplay}</td>
                    <td class="text-center">${timeDisplay}</td>
                    <td><small class="text-muted">${escapeHtml(l.last_active_date || 'Never')}</small></td>
                    <td class="text-center"><span class="badge ${statusClass}">${escapeHtml(l.engagement_status)}</span></td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center py-4 text-danger">Failed to load learner performance report.</td></tr>';
    }
}

async function loadReportActivityPart() {
    const tbody = document.getElementById('tbodyReportActivityPart');
    if (!tbody) return;

    try {
        const res = await fetch('/api/analytics/activity-participation');
        const json = await res.json();
        const data = json.data || [];

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">No activity records logged.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(a => {
            const scoreDisplay = a.average_score !== null && a.average_score !== undefined
                ? `<span class="badge bg-light text-primary border">${a.average_score.toFixed(1)}%</span>`
                : '<span class="text-muted small">—</span>';
            const timeDisplay = a.total_time_spent_minutes !== null && a.total_time_spent_minutes !== undefined
                ? `<span class="badge bg-light text-secondary border">${a.total_time_spent_minutes}m</span>`
                : '<span class="text-muted small">—</span>';

            return `
                <tr>
                    <td class="fw-bold text-navy"><i class="bi bi-tag me-1 text-primary"></i>${escapeHtml(a.activity_type)}</td>
                    <td class="text-center fw-bold">${a.total_count}</td>
                    <td class="text-center text-success fw-bold">${a.completed_count}</td>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <span class="small fw-bold">${a.completion_rate.toFixed(1)}%</span>
                            <div class="progress flex-grow-1" style="height: 6px; width: 60px;">
                                <div class="progress-bar ${a.completion_rate >= 50 ? 'bg-success' : 'bg-warning'}" style="width: ${a.completion_rate}%;"></div>
                            </div>
                        </div>
                    </td>
                    <td class="text-center">${scoreDisplay}</td>
                    <td class="text-center">${timeDisplay}</td>
                    <td class="text-center"><span class="badge bg-light text-secondary border">${a.percentage_of_all_activities.toFixed(1)}%</span></td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-danger">Failed to load activity participation report.</td></tr>';
    }
}

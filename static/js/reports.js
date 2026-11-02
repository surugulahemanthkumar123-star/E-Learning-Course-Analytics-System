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
    loadReportWeekly();
    loadReportInactive();

    // Matplotlib chart generation button
    const btnGenerateCharts = document.getElementById('btnGenerateMatplotlib');
    if (btnGenerateCharts) {
        btnGenerateCharts.addEventListener('click', handleGenerateCharts);
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

async function handleGenerateCharts() {
    const btn = document.getElementById('btnGenerateMatplotlib');
    const container = document.getElementById('chartGenerationContainer');
    const imgCompletion = document.getElementById('imgCompletionChart');
    const imgWeekly = document.getElementById('imgWeeklyChart');
    const timestampEl = document.getElementById('chartTimestamp');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Generating Matplotlib Figures...';

    try {
        const res = await fetch('/api/reports/generate-charts', { method: 'POST' });
        const json = await res.json();

        if (res.ok && json.success) {
            showToast(json.message || 'Charts generated successfully!', 'success');
            const cacheBuster = `?t=${new Date().getTime()}`;
            imgCompletion.src = `/static/charts/course_completion_bar.png${cacheBuster}`;
            imgWeekly.src = `/static/charts/weekly_activity_trend.png${cacheBuster}`;
            timestampEl.textContent = `Generated: ${json.timestamp}`;
            container.classList.remove('d-none');
            container.scrollIntoView({ behavior: 'smooth' });
        } else {
            showToast(json.message || 'Failed to generate charts.', 'danger');
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
                <td class="fw-semibold">${c.course_name}</td>
                <td><span class="badge bg-light text-secondary border">${c.category}</span></td>
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
                <td class="fw-semibold">${c.course_name}</td>
                <td><span class="badge bg-light text-secondary border">${c.category}</span></td>
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
    const exportBtn = document.getElementById('btnExportWeeklyCsv');

    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    if (exportBtn) {
        exportBtn.href = `/api/reports/weekly-activity.csv${params.toString() ? '?' + params.toString() : ''}`;
    }

    try {
        const res = await fetch(`/api/analytics/weekly-activity?${params.toString()}`);
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
    const exportBtn = document.getElementById('btnExportInactiveCsv');

    if (exportBtn) {
        exportBtn.href = `/api/reports/inactive-enrollments.csv?threshold=${threshold}`;
    }

    try {
        const res = await fetch(`/api/analytics/inactive-enrollments?threshold=${threshold}`);
        const json = await res.json();
        const data = json.data || [];

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-success fw-medium"><i class="bi bi-check-circle-fill me-1"></i> No inactive enrollments found for threshold of ${threshold} days!</td></tr>`;
            return;
        }

        tbody.innerHTML = data.map(i => `
            <tr>
                <td><span class="roll-no-badge font-monospace">${i.roll_no}</span></td>
                <td class="fw-bold text-navy">${i.course_name}</td>
                <td><span class="badge bg-light text-secondary border">${i.category}</span></td>
                <td>${i.enrolled_at}</td>
                <td>${i.last_activity_date}</td>
                <td class="text-center"><span class="badge bg-danger-subtle text-danger fw-bold">${i.days_since_last_activity} d</span></td>
                <td><span class="badge badge-soft-warning">${i.status}</span></td>
                <td><small class="text-muted">${i.inactivity_reason}</small></td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-danger">Failed to load report.</td></tr>';
    }
}

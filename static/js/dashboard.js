/**
 * ====================================================================
 * E-Learning Course Analytics System - Dashboard JavaScript
 * File: static/js/dashboard.js
 * Controls live metrics, animated counters, Chart.js visualizations,
 * PNG chart export, inactivity tables, and dynamic theme synchronization.
 * ====================================================================
 */

let completionChart = null;
let weeklyChart = null;

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();

    // Refresh button event listener
    const refreshBtn = document.getElementById('btnRefreshDashboard');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Refreshing...';
            loadDashboardData().finally(() => {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i> Refresh Data';
            });
        });
    }

    // Inactive filter button
    const btnFilterInactive = document.getElementById('btnFilterInactive');
    if (btnFilterInactive) {
        btnFilterInactive.addEventListener('click', () => {
            const threshold = document.getElementById('inputInactiveThreshold').value || 14;
            loadInactiveEnrollments(threshold);
        });
    }

    // Chart Export (PNG) Buttons
    const btnDownloadCourseChart = document.getElementById('btnDownloadCourseChart');
    if (btnDownloadCourseChart) {
        btnDownloadCourseChart.addEventListener('click', () => {
            exportChartAsPNG(completionChart, 'Course_Completion_Analytics.png');
        });
    }

    const btnDownloadWeeklyChart = document.getElementById('btnDownloadWeeklyChart');
    if (btnDownloadWeeklyChart) {
        btnDownloadWeeklyChart.addEventListener('click', () => {
            exportChartAsPNG(weeklyChart, 'Weekly_Activity_Trends.png');
        });
    }

    // Dynamic Chart Theme Adaptation
    window.addEventListener('themeChanged', () => {
        loadCourseCompletionChart();
        loadWeeklyActivityChart();
    });
});

/**
 * Utility: Export any Chart.js canvas to downloadable PNG
 */
function exportChartAsPNG(chartInstance, filename) {
    if (!chartInstance) {
        alert('Chart is still loading. Please wait a moment.');
        return;
    }
    const imageURI = chartInstance.toBase64Image();
    const downloadLink = document.createElement('a');
    downloadLink.download = filename;
    downloadLink.href = imageURI;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

/**
 * Utility: Animated number counter for UX delight
 */
function animateValue(elementId, start, end, duration = 800, isPercentage = false) {
    const obj = document.getElementById(elementId);
    if (!obj) return;
    if (isNaN(end)) {
        obj.textContent = end;
        return;
    }

    const range = end - start;
    let current = start;
    const increment = end > start ? 1 : -1;
    const startTime = new Date().getTime();
    const endTime = startTime + duration;

    function run() {
        const now = new Date().getTime();
        const remaining = Math.max((endTime - now) / duration, 0);
        const value = Math.round(end - (remaining * range));
        obj.textContent = isPercentage ? `${(value).toFixed(1)}%` : value;
        if (now < endTime) {
            requestAnimationFrame(run);
        } else {
            obj.textContent = isPercentage ? `${end.toFixed(1)}%` : end;
        }
    }
    requestAnimationFrame(run);
}

async function loadDashboardData() {
    await Promise.all([
        loadSummaryCards(),
        loadCourseCompletionChart(),
        loadWeeklyActivityChart(),
        loadCourseComparisonTable(),
        loadInactiveEnrollments(document.getElementById('inputInactiveThreshold')?.value || 14)
    ]);
}

/**
 * 1. Fetch & display top summary cards with animated counters
 */
async function loadSummaryCards() {
    try {
        const res = await fetch('/api/dashboard/summary');
        const json = await res.json();
        const data = json.data || {};

        const alertContainer = document.getElementById('dbAlertContainer');
        if (alertContainer) {
            if (data.database_connected === false) {
                alertContainer.innerHTML = `
                    <div class="alert alert-danger shadow-sm d-flex align-items-center gap-3 mb-4 rounded-4" role="alert">
                        <i class="bi bi-exclamation-octagon-fill fs-3 text-danger"></i>
                        <div>
                            <h6 class="alert-heading mb-1 fw-bold">Database Connection Required</h6>
                            <p class="mb-0 small">Cannot connect to MySQL server. Ensure MySQL is running locally, configure your <code>.env</code> file, and run <code>database.sql</code>. <a href="/settings" class="alert-link fw-semibold">Check Database Settings &rarr;</a></p>
                        </div>
                    </div>
                `;
            } else {
                alertContainer.innerHTML = '';
            }
        }

        animateValue('cardTotalCourses', 0, data.total_courses ?? 0, 600);
        animateValue('cardTotalLearners', 0, data.total_learners ?? 0, 600);
        animateValue('cardTotalEnrollments', 0, data.total_enrollments ?? 0, 700);
        animateValue('cardCompletedEnrollments', 0, data.completed_enrollments ?? 0, 700);
        
        const subCard = document.getElementById('cardCompletedSub');
        if (subCard) {
            subCard.innerHTML = `<i class="bi bi-hourglass-split"></i> ${data.in_progress_enrollments ?? 0} In Progress`;
        }

        animateValue('cardOverallRate', 0, data.overall_completion_rate ?? 0, 800, true);
        animateValue('cardInactiveCount', 0, data.inactive_enrollments ?? 0, 600);

    } catch (err) {
        console.error('Error fetching dashboard summary:', err);
    }
}

/**
 * 2. Fetch & render Course Completion Bar Chart
 */
async function loadCourseCompletionChart() {
    const canvas = document.getElementById('courseCompletionChart');
    const emptyState = document.getElementById('courseCompletionEmpty');
    if (!canvas) return;

    try {
        const res = await fetch('/api/analytics/course-completion');
        const json = await res.json();
        const courses = json.data || [];

        if (courses.length === 0) {
            canvas.classList.add('d-none');
            if (emptyState) emptyState.classList.remove('d-none');
            return;
        }

        canvas.classList.remove('d-none');
        if (emptyState) emptyState.classList.add('d-none');

        const labels = courses.map(c => c.course_name.length > 22 ? c.course_name.substring(0, 20) + '...' : c.course_name);
        const completionRates = courses.map(c => c.completion_rate);
        const completedCounts = courses.map(c => c.completed_enrollments);
        const inProgressCounts = courses.map(c => c.in_progress_enrollments);

        if (completionChart) {
            completionChart.destroy();
        }

        const ctx = canvas.getContext('2d');
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(226, 232, 240, 0.7)';
        const tickColor = isDark ? '#94a3b8' : '#475569';

        // Create sleek gradients
        const gradientBlue = ctx.createLinearGradient(0, 0, 0, 300);
        gradientBlue.addColorStop(0, '#38bdf8');
        gradientBlue.addColorStop(1, '#6366f1');

        const gradientGreen = ctx.createLinearGradient(0, 0, 0, 300);
        gradientGreen.addColorStop(0, '#34d399');
        gradientGreen.addColorStop(1, '#059669');

        const gradientAmber = ctx.createLinearGradient(0, 0, 0, 300);
        gradientAmber.addColorStop(0, '#fbbf24');
        gradientAmber.addColorStop(1, '#d97706');

        completionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Completion Rate (%)',
                        data: completionRates,
                        backgroundColor: gradientBlue,
                        borderColor: '#38bdf8',
                        borderWidth: 1,
                        borderRadius: 8,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Completed Learners',
                        data: completedCounts,
                        backgroundColor: gradientGreen,
                        borderColor: '#34d399',
                        borderWidth: 1,
                        borderRadius: 8,
                        yAxisID: 'y1'
                    },
                    {
                        label: 'In Progress Learners',
                        data: inProgressCounts,
                        backgroundColor: gradientAmber,
                        borderColor: '#fbbf24',
                        borderWidth: 1,
                        borderRadius: 8,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            font: { family: 'Plus Jakarta Sans', size: 11, weight: '500' },
                            color: tickColor
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { 
                            display: true, 
                            text: 'Completion Rate (%)', 
                            color: isDark ? '#38bdf8' : '#2563eb',
                            font: { family: 'Plus Jakarta Sans', weight: '600', size: 11 }
                        },
                        min: 0,
                        max: 100,
                        grid: { color: gridColor },
                        ticks: { font: { family: 'Plus Jakarta Sans', size: 11 }, color: tickColor }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { 
                            display: true, 
                            text: 'Learners (Count)', 
                            color: tickColor,
                            font: { family: 'Plus Jakarta Sans', weight: '600', size: 11 }
                        },
                        grid: { drawOnChartArea: false },
                        min: 0,
                        ticks: { stepSize: 1, font: { family: 'Plus Jakarta Sans', size: 11 }, color: tickColor }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { 
                            boxWidth: 12, 
                            font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' },
                            usePointStyle: true,
                            pointStyle: 'circle',
                            color: tickColor
                        }
                    },
                    tooltip: {
                        backgroundColor: '#070a10',
                        titleFont: { family: 'Plus Jakarta Sans', size: 12, weight: '700' },
                        bodyFont: { family: 'Plus Jakarta Sans', size: 11 },
                        padding: 12,
                        cornerRadius: 8,
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                if (context.dataset.label.includes('%')) {
                                    return ` ${context.dataset.label}: ${context.parsed.y}%`;
                                }
                                return ` ${context.dataset.label}: ${context.parsed.y} learners`;
                            }
                        }
                    }
                }
            }
        });

    } catch (err) {
        console.error('Error rendering completion chart:', err);
    }
}

/**
 * 3. Fetch & render Weekly Activity Line Chart
 */
async function loadWeeklyActivityChart() {
    const canvas = document.getElementById('weeklyActivityChart');
    const emptyState = document.getElementById('weeklyActivityEmpty');
    if (!canvas) return;

    try {
        const res = await fetch('/api/analytics/weekly-activity');
        const json = await res.json();
        const weekly = json.data || [];

        if (weekly.length === 0) {
            canvas.classList.add('d-none');
            if (emptyState) emptyState.classList.remove('d-none');
            return;
        }

        canvas.classList.remove('d-none');
        if (emptyState) emptyState.classList.add('d-none');

        const labels = weekly.map(w => w.week_label.replace('Week of ', ''));
        const totalActivities = weekly.map(w => w.total);
        const completedActivities = weekly.map(w => w.completed);

        if (weeklyChart) {
            weeklyChart.destroy();
        }

        const ctx = canvas.getContext('2d');
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(226, 232, 240, 0.7)';
        const tickColor = isDark ? '#94a3b8' : '#475569';

        const gradientFill = ctx.createLinearGradient(0, 0, 0, 280);
        gradientFill.addColorStop(0, isDark ? 'rgba(56, 189, 248, 0.25)' : 'rgba(37, 99, 235, 0.2)');
        gradientFill.addColorStop(1, 'rgba(56, 189, 248, 0.01)');

        weeklyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Total Activities',
                        data: totalActivities,
                        borderColor: '#38bdf8',
                        backgroundColor: gradientFill,
                        fill: true,
                        tension: 0.38,
                        borderWidth: 2.5,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#38bdf8'
                    },
                    {
                        label: 'Completed Submissions',
                        data: completedActivities,
                        borderColor: '#34d399',
                        backgroundColor: 'transparent',
                        borderDash: [5, 5],
                        borderWidth: 2,
                        tension: 0.38,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#34d399'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: 'Plus Jakarta Sans', size: 10 }, color: tickColor }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, precision: 0, font: { family: 'Plus Jakarta Sans', size: 10 }, color: tickColor },
                        grid: { color: gridColor }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { 
                            boxWidth: 12, 
                            font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' },
                            usePointStyle: true,
                            pointStyle: 'circle',
                            color: tickColor
                        }
                    },
                    tooltip: {
                        backgroundColor: '#070a10',
                        titleFont: { family: 'Plus Jakarta Sans', size: 12, weight: '700' },
                        bodyFont: { family: 'Plus Jakarta Sans', size: 11 },
                        padding: 12,
                        cornerRadius: 8,
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1
                    }
                }
            }
        });

    } catch (err) {
        console.error('Error rendering weekly activity chart:', err);
    }
}

/**
 * 4. Fetch & populate Course Comparison Benchmark Table
 */
async function loadCourseComparisonTable() {
    const tbody = document.getElementById('tbodyCourseComparison');
    if (!tbody) return;

    try {
        const res = await fetch('/api/analytics/course-comparison');
        const json = await res.json();
        const comparison = json.data || [];

        if (comparison.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-4 text-muted">
                        No courses recorded yet. Add courses in the course manager.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = comparison.map(c => {
            const badgeClass = c.badge_color === 'success' ? 'badge-soft-success' :
                               c.badge_color === 'primary' ? 'badge-soft-primary' :
                               c.badge_color === 'warning' ? 'badge-soft-warning' :
                               c.badge_color === 'danger' ? 'badge-soft-danger' : 'badge-soft-secondary';

            const progressGrad = c.completion_rate >= 75 ? 'background: linear-gradient(90deg, #10b981, #34d399);' :
                                 c.completion_rate >= 50 ? 'background: linear-gradient(90deg, #6366f1, #38bdf8);' :
                                 c.completion_rate >= 25 ? 'background: linear-gradient(90deg, #f59e0b, #fbbf24);' : 
                                 'background: linear-gradient(90deg, #ef4444, #f87171);';

            return `
                <tr>
                    <td>
                        <div class="fw-bold text-navy">${c.course_name}</div>
                    </td>
                    <td>
                        <span class="badge bg-light text-secondary border font-monospace">${c.category}</span>
                    </td>
                    <td class="text-center fw-bold">${c.total_enrollments}</td>
                    <td class="text-center text-success fw-bold">${c.completed_enrollments}</td>
                    <td class="text-center text-warning fw-bold">${c.in_progress_enrollments}</td>
                    <td style="min-width: 180px;">
                        <div class="d-flex align-items-center gap-2">
                            <span class="small fw-bold text-nowrap" style="width: 44px;">${c.completion_rate.toFixed(1)}%</span>
                            <div class="progress-modern flex-grow-1">
                                <div class="progress-bar" role="progressbar" style="width: ${c.completion_rate}%; ${progressGrad}"></div>
                            </div>
                        </div>
                    </td>
                    <td class="text-center">
                        <span class="${badgeClass}">${c.performance_status}</span>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (err) {
        console.error('Error loading course comparison:', err);
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4 text-danger">
                    Failed to load course comparison table.
                </td>
            </tr>
        `;
    }
}

/**
 * 5. Fetch & populate Inactive Enrollments Detection Table
 */
async function loadInactiveEnrollments(threshold = 14) {
    const tbody = document.getElementById('tbodyInactiveEnrollments');
    if (!tbody) return;

    try {
        const res = await fetch(`/api/analytics/inactive-enrollments?threshold=${threshold}`);
        const json = await res.json();
        const inactives = json.data || [];

        if (inactives.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4 text-success fw-bold">
                        <i class="bi bi-shield-check fs-5 me-1"></i> No inactive enrollments detected! All active learners have logged activity within the last ${threshold} days.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = inactives.map(item => {
            const isNoActivity = item.last_activity_date === 'No activity recorded';
            const statusBadge = item.status === 'In Progress' ? 'badge-soft-warning' : 'badge-soft-secondary';
            const initials = item.roll_no ? item.roll_no.substring(item.roll_no.length - 2).toUpperCase() : 'LR';

            return `
                <tr>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <div class="avatar-initials">${initials}</div>
                            <span class="roll-no-badge font-monospace">${item.roll_no}</span>
                        </div>
                    </td>
                    <td>
                        <span class="fw-bold text-navy">${item.course_name}</span>
                        <div class="small text-muted">${item.category}</div>
                    </td>
                    <td><small class="text-secondary">${item.enrolled_at}</small></td>
                    <td>
                        ${isNoActivity ? '<span class="badge badge-soft-danger"><i class="bi bi-x-circle"></i> No activity recorded</span>' : `<small class="fw-medium">${item.last_activity_date}</small>`}
                    </td>
                    <td class="text-center">
                        <span class="badge bg-danger text-white fw-bold px-2 py-1">${item.days_since_last_activity} days</span>
                    </td>
                    <td class="text-center">
                        <span class="${statusBadge}">${item.status}</span>
                    </td>
                    <td>
                        <small class="text-muted">${item.inactivity_reason}</small>
                    </td>
                    <td class="text-end">
                        <a href="/activities" class="btn btn-sm btn-outline-primary" title="Record learner activity">
                            <i class="bi bi-plus-circle me-1"></i> Log Activity
                        </a>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (err) {
        console.error('Error loading inactive enrollments:', err);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4 text-danger">
                    Failed to scan inactive enrollments.
                </td>
            </tr>
        `;
    }
}

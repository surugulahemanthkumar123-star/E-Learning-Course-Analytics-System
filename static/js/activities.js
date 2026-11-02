/**
 * ====================================================================
 * E-Learning Course Analytics System - Activities JavaScript
 * File: static/js/activities.js
 * Enhanced for Phase 5: Filter by learner, course & dates, display
 * nullable score & duration telemetry, safe DOM rendering.
 * ====================================================================
 */

let activityModal = null;

document.addEventListener('DOMContentLoaded', () => {
    const modalEl = document.getElementById('modalActivity');
    if (modalEl) {
        activityModal = new bootstrap.Modal(modalEl);
    }

    loadFilterDropdowns();
    loadActivities();

    // Filters event listeners
    document.getElementById('btnApplyActivityFilter')?.addEventListener('click', () => loadActivities());
    document.getElementById('filterActivityCourse')?.addEventListener('change', () => loadActivities());
    document.getElementById('filterActivityLearner')?.addEventListener('change', () => loadActivities());
    document.getElementById('filterActivityType')?.addEventListener('change', () => loadActivities());

    document.getElementById('btnResetActivityFilter')?.addEventListener('click', () => {
        const c = document.getElementById('filterActivityCourse');
        const l = document.getElementById('filterActivityLearner');
        const t = document.getElementById('filterActivityType');
        const s = document.getElementById('filterStartDate');
        const e = document.getElementById('filterEndDate');
        if (c) c.value = '';
        if (l) l.value = '';
        if (t) t.value = '';
        if (s) s.value = '';
        if (e) e.value = '';
        loadActivities();
    });

    // Populate enrollments when opening modal
    document.getElementById('btnOpenAddActivity')?.addEventListener('click', async () => {
        const form = document.getElementById('formActivity');
        if (form) form.reset();
        const chk = document.getElementById('checkCompleted');
        if (chk) chk.checked = true;
        await loadEnrollmentDropdown();
    });

    // Handle submit
    document.getElementById('formActivity')?.addEventListener('submit', handleSaveActivity);
});

async function loadFilterDropdowns() {
    try {
        const [resCourses, resLearners] = await Promise.all([
            fetch('/api/courses'),
            fetch('/api/learners')
        ]);
        const jsonCourses = await resCourses.json();
        const jsonLearners = await resLearners.json();

        const selectCourse = document.getElementById('filterActivityCourse');
        if (selectCourse && jsonCourses.data) {
            selectCourse.innerHTML = '<option value="">All Courses</option>';
            jsonCourses.data.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.course_id;
                opt.textContent = c.course_name.length > 25 ? c.course_name.substring(0, 22) + '...' : c.course_name;
                selectCourse.appendChild(opt);
            });
        }

        const selectLearner = document.getElementById('filterActivityLearner');
        if (selectLearner && jsonLearners.data) {
            selectLearner.innerHTML = '<option value="">All Learners</option>';
            jsonLearners.data.forEach(l => {
                const opt = document.createElement('option');
                opt.value = l.learner_id;
                opt.textContent = l.name ? `${l.roll_no} (${l.name})` : l.roll_no;
                selectLearner.appendChild(opt);
            });
        }
    } catch (err) {
        console.warn('Could not populate activity filter dropdowns:', err);
    }
}

async function loadEnrollmentDropdown() {
    try {
        const res = await fetch('/api/enrollments');
        const json = await res.json();
        const enrollments = json.data || [];

        const select = document.getElementById('selectEnrollment');
        if (!select) return;
        select.innerHTML = '<option value="">-- Choose Enrollment --</option>';

        enrollments.forEach(e => {
            const opt = document.createElement('option');
            opt.value = e.enrollment_id;
            opt.textContent = `${e.roll_no} - ${e.course_name} (${e.status})`;
            select.appendChild(opt);
        });
    } catch (err) {
        showToast('Failed to load enrollments for activity logging.', 'danger');
    }
}

async function loadActivities() {
    const tbody = document.getElementById('tbodyActivities');
    const badge = document.getElementById('activityTotalBadge');
    if (!tbody) return;

    const courseId = document.getElementById('filterActivityCourse')?.value || '';
    const learnerId = document.getElementById('filterActivityLearner')?.value || '';
    const type = document.getElementById('filterActivityType')?.value || '';
    const startDate = document.getElementById('filterStartDate')?.value || '';
    const endDate = document.getElementById('filterEndDate')?.value || '';

    try {
        const params = new URLSearchParams();
        if (courseId) params.append('course_id', courseId);
        if (learnerId) params.append('learner_id', learnerId);
        if (type) params.append('activity_type', type);
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);

        const res = await fetch(`/api/activities?${params.toString()}`);
        const json = await res.json();
        const activities = json.data || [];

        if (badge) badge.textContent = `${activities.length} activities`;

        if (activities.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="text-center py-4 text-muted">
                        <i class="bi bi-inbox fs-4 d-block mb-1 text-secondary"></i>
                        No learning activities found matching the selected criteria.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = activities.map(a => {
            const scoreDisplay = (a.score !== null && a.score !== undefined)
                ? `<span class="badge ${a.score >= 75 ? 'bg-success-subtle text-success border border-success-subtle' : a.score >= 50 ? 'bg-primary-subtle text-primary border border-primary-subtle' : 'bg-warning-subtle text-warning border border-warning-subtle'} fw-bold">${parseFloat(a.score).toFixed(1)}%</span>`
                : '<span class="text-muted small">&mdash;</span>';

            const timeDisplay = (a.time_spent_minutes !== null && a.time_spent_minutes !== undefined)
                ? `<span class="small fw-semibold text-navy"><i class="bi bi-clock me-1 text-muted"></i>${a.time_spent_minutes}m</span>`
                : '<span class="text-muted small">&mdash;</span>';

            return `
                <tr>
                    <td><span class="badge bg-primary-subtle text-primary border border-primary-subtle fw-bold">#${a.activity_id}</span></td>
                    <td>
                        <span class="roll-no-badge font-monospace">${escapeHtml(a.roll_no)}</span>
                    </td>
                    <td>
                        <div class="fw-bold text-navy">${escapeHtml(a.course_name)}</div>
                    </td>
                    <td>
                        <span class="badge bg-light text-primary border">${escapeHtml(a.activity_type)}</span>
                    </td>
                    <td>${scoreDisplay}</td>
                    <td>${timeDisplay}</td>
                    <td>
                        <small class="text-muted">${escapeHtml(a.activity_date)}</small>
                    </td>
                    <td class="text-center">
                        <span class="badge ${a.completed ? 'badge-soft-success' : 'badge-soft-warning'}">
                            ${a.completed ? '<i class="bi bi-check-lg me-1"></i> Completed' : '<i class="bi bi-hourglass-split me-1"></i> Pending'}
                        </span>
                    </td>
                    <td class="text-end">
                        <button class="btn btn-sm ${a.completed ? 'btn-outline-warning' : 'btn-outline-success'}" 
                                title="${a.completed ? 'Mark as Incomplete' : 'Mark as Completed'}"
                                onclick="toggleActivityCompletion(${a.activity_id}, ${!a.completed})">
                            <i class="bi ${a.completed ? 'bi-x-circle' : 'bi-check-circle'} me-1"></i>
                            ${a.completed ? 'Incomplete' : 'Complete'}
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (err) {
        console.error('Error fetching activities:', err);
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-4 text-danger">
                    Failed to load activities from server.
                </td>
            </tr>
        `;
    }
}

async function handleSaveActivity(e) {
    e.preventDefault();
    const enrollment_id = parseInt(document.getElementById('selectEnrollment').value, 10);
    const activity_type = document.getElementById('selectActivityType').value;
    const completed = document.getElementById('checkCompleted').checked;
    const customDate = document.getElementById('customActivityDate').value;
    const rawScore = document.getElementById('inputActivityScore')?.value?.trim();
    const rawTime = document.getElementById('inputActivityTimeSpent')?.value?.trim();
    const btn = document.getElementById('btnSaveActivity');

    if (!enrollment_id || !activity_type) {
        showToast('Please select an enrollment and activity type.', 'warning');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';

    const payload = { enrollment_id, activity_type, completed };
    if (customDate) {
        payload.activity_date = customDate.replace('T', ' ') + ':00';
    }
    if (rawScore !== '' && rawScore !== undefined) {
        const numScore = parseFloat(rawScore);
        if (!isNaN(numScore) && numScore >= 0 && numScore <= 100) {
            payload.score = numScore;
        }
    }
    if (rawTime !== '' && rawTime !== undefined) {
        const numTime = parseInt(rawTime, 10);
        if (!isNaN(numTime) && numTime >= 0) {
            payload.time_spent_minutes = numTime;
        }
    }

    try {
        const res = await fetch('/api/activities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const json = await res.json();

        if (res.ok && json.success) {
            showToast(json.message || 'Activity recorded successfully!', 'success');
            if (activityModal) activityModal.hide();
            loadActivities();
        } else {
            showToast(json.message || json.error || 'Failed to record activity.', 'danger');
        }
    } catch (err) {
        showToast('Network error while recording activity.', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Save Activity';
    }
}

async function toggleActivityCompletion(id, newStatus) {
    try {
        const res = await fetch(`/api/activities/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ completed: newStatus })
        });
        const json = await res.json();
        if (res.ok && json.success) {
            showToast(json.message || 'Activity status updated.', 'success');
            loadActivities();
        } else {
            showToast(json.message || json.error || 'Failed to update activity.', 'danger');
        }
    } catch (err) {
        showToast('Network error updating activity.', 'danger');
    }
}

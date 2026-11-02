/**
 * ====================================================================
 * E-Learning Course Analytics System - Activities JavaScript
 * File: static/js/activities.js
 * ====================================================================
 */

let activityModal = null;

document.addEventListener('DOMContentLoaded', () => {
    activityModal = new bootstrap.Modal(document.getElementById('modalActivity'));

    loadActivities();

    // Filters event listeners
    document.getElementById('btnApplyActivityFilter')?.addEventListener('click', () => loadActivities());
    document.getElementById('filterActivityType')?.addEventListener('change', () => loadActivities());

    document.getElementById('btnResetActivityFilter')?.addEventListener('click', () => {
        document.getElementById('filterActivityType').value = '';
        document.getElementById('filterStartDate').value = '';
        document.getElementById('filterEndDate').value = '';
        loadActivities();
    });

    // Populate enrollments when opening modal
    document.getElementById('btnOpenAddActivity')?.addEventListener('click', async () => {
        document.getElementById('formActivity').reset();
        document.getElementById('checkCompleted').checked = true;
        await loadEnrollmentDropdown();
    });

    // Handle submit
    document.getElementById('formActivity')?.addEventListener('submit', handleSaveActivity);
});

async function loadEnrollmentDropdown() {
    try {
        const res = await fetch('/api/enrollments');
        const json = await res.json();
        const enrollments = json.data || [];

        const select = document.getElementById('selectEnrollment');
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
    const type = document.getElementById('filterActivityType')?.value || '';
    const startDate = document.getElementById('filterStartDate')?.value || '';
    const endDate = document.getElementById('filterEndDate')?.value || '';

    try {
        const params = new URLSearchParams();
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
                    <td colspan="7" class="text-center py-4 text-muted">
                        No learning activities found matching the criteria.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = activities.map(a => `
            <tr>
                <td><span class="badge bg-primary-subtle text-primary border border-primary-subtle fw-bold">#${a.activity_id}</span></td>
                <td>
                    <span class="roll-no-badge font-monospace">${a.roll_no}</span>
                </td>
                <td>
                    <div class="fw-bold text-navy">${a.course_name}</div>
                </td>
                <td>
                    <span class="badge bg-light text-primary border">${a.activity_type}</span>
                </td>
                <td>
                    <small class="text-muted">${a.activity_date}</small>
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
                        ${a.completed ? 'Mark Incomplete' : 'Mark Complete'}
                    </button>
                </td>
            </tr>
        `).join('');

    } catch (err) {
        console.error('Error fetching activities:', err);
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4 text-danger">
                    Failed to load activities from server.
                </td>
            </tr>
        `;
    }
}

async function handleSaveActivity(e) {
    e.preventDefault();
    const enrollment_id = parseInt(document.getElementById('selectEnrollment').value);
    const activity_type = document.getElementById('selectActivityType').value;
    const completed = document.getElementById('checkCompleted').checked;
    const customDate = document.getElementById('customActivityDate').value;
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

    try {
        const res = await fetch('/api/activities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const json = await res.json();

        if (res.ok && json.success) {
            showToast(json.message || 'Activity recorded successfully!', 'success');
            activityModal.hide();
            loadActivities();
        } else {
            showToast(json.message || 'Failed to record activity.', 'danger');
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
            showToast(json.message || 'Failed to update activity.', 'danger');
        }
    } catch (err) {
        showToast('Network error updating activity.', 'danger');
    }
}

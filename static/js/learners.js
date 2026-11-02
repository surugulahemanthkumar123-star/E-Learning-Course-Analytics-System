/**
 * ====================================================================
 * E-Learning Course Analytics System - Learners Management JavaScript
 * File: static/js/learners.js
 * ====================================================================
 */

let learnerModal = null;
let deleteLearnerModal = null;
let viewLearnerModal = null;
let learnerToDeleteId = null;

document.addEventListener('DOMContentLoaded', () => {
    learnerModal = new bootstrap.Modal(document.getElementById('modalLearner'));
    deleteLearnerModal = new bootstrap.Modal(document.getElementById('modalDeleteLearner'));
    viewLearnerModal = new bootstrap.Modal(document.getElementById('modalViewLearner'));

    loadDepartmentFilters();
    loadLearners();

    // Search input with debouncing
    const searchInput = document.getElementById('learnerSearchInput');
    let debounceTimer = null;
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                loadLearners();
            }, 300);
        });
    }

    // Department filter dropdown
    const deptFilter = document.getElementById('learnerDepartmentFilter');
    if (deptFilter) {
        deptFilter.addEventListener('change', () => loadLearners());
    }

    // Reset filters button
    const btnReset = document.getElementById('btnResetLearnerFilters');
    if (btnReset) {
        btnReset.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            if (deptFilter) deptFilter.value = '';
            loadLearners();
        });
    }

    // Reset form on open add
    const btnOpenAdd = document.getElementById('btnOpenAddLearner');
    if (btnOpenAdd) {
        btnOpenAdd.addEventListener('click', () => {
            document.getElementById('formLearner').reset();
            document.getElementById('learnerId').value = '';
            document.getElementById('learnerRollNo').disabled = false;
            document.getElementById('modalLearnerTitle').textContent = 'Register New Learner';
        });
    }

    // Submit form (Create / Update)
    const formLearner = document.getElementById('formLearner');
    if (formLearner) {
        formLearner.addEventListener('submit', handleSaveLearner);
    }

    // Confirm Delete
    const btnConfirmDelete = document.getElementById('btnConfirmDeleteLearner');
    if (btnConfirmDelete) {
        btnConfirmDelete.addEventListener('click', handleConfirmDelete);
    }
});

async function loadDepartmentFilters() {
    const select = document.getElementById('learnerDepartmentFilter');
    if (!select) return;

    try {
        const res = await fetch('/api/learners/departments');
        const json = await res.json();
        const depts = json.data || [];

        select.innerHTML = '<option value="">All Departments</option>';
        depts.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d;
            opt.textContent = d;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error('Error fetching departments for filter:', err);
    }
}

async function loadLearners() {
    const tbody = document.getElementById('tbodyLearners');
    const badge = document.getElementById('learnerTotalBadge');
    const search = document.getElementById('learnerSearchInput')?.value.trim() || '';
    const department = document.getElementById('learnerDepartmentFilter')?.value || '';

    try {
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (department) params.append('department', department);

        const url = `/api/learners${params.toString() ? '?' + params.toString() : ''}`;
        const res = await fetch(url);
        const json = await res.json();
        const learners = json.data || [];

        if (badge) badge.textContent = `${learners.length} learners`;

        if (learners.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-4 text-muted">
                        ${search || department ? 'No learners found matching the selected filters.' : 'No learners registered yet. Click "Register Learner" above.'}
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = learners.map(l => {
            const initials = l.name ? l.name.substring(0, 2).toUpperCase() :
                             l.roll_no ? l.roll_no.substring(l.roll_no.length - 2).toUpperCase() : 'LR';
            const nameDisplay = l.name ? `<div class="fw-bold text-navy">${escapeHtml(l.name)}</div>` : '';
            const deptBadge = l.department ? `<span class="badge bg-light text-secondary border">${escapeHtml(l.department)}</span>` : '<span class="text-muted small">-</span>';
            const emailDisplay = l.email ? `<small class="text-muted"><i class="bi bi-envelope me-1"></i>${escapeHtml(l.email)}</small>` : '<span class="text-muted small">-</span>';

            const rate = typeof l.completion_rate === 'number' ? l.completion_rate : 0;
            const progressColor = rate >= 75 ? 'bg-success' : rate >= 40 ? 'bg-primary' : rate > 0 ? 'bg-warning' : 'bg-secondary';

            return `
            <tr>
                <td><span class="badge bg-primary-subtle text-primary border border-primary-subtle fw-bold">#${l.learner_id}</span></td>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <div class="avatar-initials" style="width: 32px; height: 32px; font-size: 0.75rem;">${escapeHtml(initials)}</div>
                        <div>
                            ${nameDisplay}
                            <span class="roll-no-badge font-monospace">${escapeHtml(l.roll_no)}</span>
                        </div>
                    </div>
                </td>
                <td>${deptBadge}</td>
                <td>${emailDisplay}</td>
                <td class="text-center">
                    <span class="badge ${l.enrollment_count > 0 ? 'badge-soft-primary' : 'badge-soft-secondary'} px-2 py-1">
                        <i class="bi bi-mortarboard me-1"></i>${l.enrollment_count} course(s)
                    </span>
                </td>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <span class="small fw-bold text-navy" style="min-width: 40px;">${rate.toFixed(1)}%</span>
                        <div class="progress flex-grow-1" style="height: 6px;">
                            <div class="progress-bar ${progressColor}" style="width: ${rate}%;"></div>
                        </div>
                    </div>
                </td>
                <td class="text-end">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-info" title="View Profile & Progress" onclick="openViewLearnerProgress(${l.learner_id})">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-outline-secondary" title="Edit Learner" onclick="openEditLearner(${l.learner_id})">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger" title="Delete Learner" onclick="openDeleteLearner(${l.learner_id}, '${encodeURIComponent(l.roll_no)}')">
                            <i class="bi bi-trash3"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        }).join('');

    } catch (err) {
        console.error('Error fetching learners:', err);
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4 text-danger">
                    Failed to load learners from server.
                </td>
            </tr>
        `;
    }
}

async function openEditLearner(id) {
    try {
        const res = await fetch(`/api/learners/${id}`);
        const json = await res.json();
        if (!res.ok || !json.success) {
            showToast(json.message || 'Failed to load learner details.', 'danger');
            return;
        }
        const l = json.data;
        document.getElementById('learnerId').value = l.learner_id;
        document.getElementById('learnerRollNo').value = l.roll_no || '';
        document.getElementById('learnerName').value = l.name || '';
        document.getElementById('learnerEmail').value = l.email || '';
        document.getElementById('learnerDepartment').value = l.department || '';
        document.getElementById('modalLearnerTitle').textContent = `Edit Learner #${l.learner_id} (${l.roll_no})`;
        learnerModal.show();
    } catch (err) {
        showToast('Network error while retrieving learner details.', 'danger');
    }
}

function openDeleteLearner(id, encodedRoll) {
    learnerToDeleteId = id;
    document.getElementById('deleteLearnerRoll').textContent = decodeURIComponent(encodedRoll);
    deleteLearnerModal.show();
}

async function openViewLearnerProgress(id) {
    const tbody = document.getElementById('tbodyLearnerCoursesProgress');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Loading academic telemetry...</td></tr>';
    viewLearnerModal.show();

    try {
        const res = await fetch(`/api/learners/${id}/progress`);
        const json = await res.json();
        if (!res.ok || !json.success) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-danger">${json.message || 'Failed to load progress.'}</td></tr>`;
            return;
        }

        const learner = json.learner;
        const courses = json.data || [];

        // Fill header & KPI badges
        const initials = learner.name ? learner.name.substring(0, 2).toUpperCase() :
                         learner.roll_no ? learner.roll_no.substring(learner.roll_no.length - 2).toUpperCase() : 'LR';
        document.getElementById('viewDetailAvatar').textContent = initials;
        document.getElementById('viewDetailRoll').textContent = learner.roll_no;
        document.getElementById('viewDetailName').textContent = learner.name ? learner.name : 'Learner Profile';
        document.getElementById('viewDetailEmail').textContent = learner.email ? learner.email : '';
        document.getElementById('viewDetailDept').textContent = learner.department ? learner.department : 'Not assigned';

        const totalEnrolled = courses.length;
        const totalCompleted = courses.filter(c => c.status === 'Completed').length;
        const rate = totalEnrolled > 0 ? (totalCompleted / totalEnrolled * 100).toFixed(1) : '0.0';

        document.getElementById('viewDetailEnrolledCount').textContent = totalEnrolled;
        document.getElementById('viewDetailCompletedCount').textContent = totalCompleted;
        document.getElementById('viewDetailRate').textContent = `${rate}%`;

        if (courses.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">This learner is not currently enrolled in any courses.</td></tr>';
            return;
        }

        tbody.innerHTML = courses.map(c => {
            const badgeClass = c.status === 'Completed' ? 'badge-soft-success' :
                               c.status === 'In Progress' ? 'badge-soft-warning' : 'badge-soft-secondary';
            const creditsBadge = c.credits !== null && c.credits !== undefined ? `(${c.credits} cr)` : '';
            const lastActive = c.last_activity_date || 'No activity logged';

            return `
                <tr>
                    <td>
                        <div class="fw-bold text-navy">${escapeHtml(c.course_name)}</div>
                        <small class="text-muted">Enrolled: ${escapeHtml(c.enrolled_at || 'N/A')}</small>
                    </td>
                    <td>
                        <span class="badge bg-light text-secondary border">${escapeHtml(c.category)} ${escapeHtml(creditsBadge)}</span>
                    </td>
                    <td class="text-center">
                        <span class="badge ${badgeClass} px-2 py-1">${escapeHtml(c.status)}</span>
                    </td>
                    <td class="text-center">
                        <span class="badge bg-primary-subtle text-primary border border-primary-subtle fw-bold px-2 py-1">
                            ${c.total_activities} activities
                        </span>
                        ${c.completed_activities ? `<small class="text-muted d-block" style="font-size: 0.72rem;">${c.completed_activities} completed</small>` : ''}
                    </td>
                    <td>
                        <small class="text-muted">${escapeHtml(lastActive)}</small>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-danger">Network error loading progress.</td></tr>';
    }
}

async function handleSaveLearner(e) {
    e.preventDefault();
    const btn = document.getElementById('btnSaveLearner');
    const id = document.getElementById('learnerId').value;
    const rollNo = document.getElementById('learnerRollNo').value.trim().toUpperCase();
    const name = document.getElementById('learnerName').value.trim();
    const email = document.getElementById('learnerEmail').value.trim();
    const department = document.getElementById('learnerDepartment').value.trim();

    if (!rollNo) {
        showToast('Roll number is required.', 'warning');
        return;
    }

    const payload = {
        roll_no: rollNo,
        name: name || null,
        email: email || null,
        department: department || null
    };

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';

    try {
        const url = id ? `/api/learners/${id}` : '/api/learners';
        const method = id ? 'PUT' : 'POST';

        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const json = await res.json();

        if (res.ok && json.success) {
            showToast(json.message || 'Learner saved successfully.', 'success');
            learnerModal.hide();
            await loadDepartmentFilters();
            loadLearners();
        } else {
            showToast(json.message || json.error || 'Failed to save learner.', 'danger');
        }
    } catch (err) {
        showToast('Network error while saving learner.', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-check2 me-1"></i> Save Learner';
    }
}

async function handleConfirmDelete() {
    if (!learnerToDeleteId) return;

    const btn = document.getElementById('btnConfirmDeleteLearner');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Deleting...';

    try {
        const res = await fetch(`/api/learners/${learnerToDeleteId}`, { method: 'DELETE' });
        const json = await res.json();

        if (res.ok && json.success) {
            showToast(json.message || 'Learner deleted successfully.', 'success');
            deleteLearnerModal.hide();
            await loadDepartmentFilters();
            loadLearners();
        } else {
            showToast(json.message || json.error || 'Failed to delete learner.', 'danger');
        }
    } catch (err) {
        showToast('Network error while deleting learner.', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-trash3 me-1"></i> Confirm Delete';
        learnerToDeleteId = null;
    }
}

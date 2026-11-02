/**
 * ====================================================================
 * E-Learning Course Analytics System - Learners Management JavaScript
 * File: static/js/learners.js
 * ====================================================================
 */

let learnerModal = null;
let deleteLearnerModal = null;
let viewEnrollmentsModal = null;
let learnerToDeleteId = null;

document.addEventListener('DOMContentLoaded', () => {
    learnerModal = new bootstrap.Modal(document.getElementById('modalLearner'));
    deleteLearnerModal = new bootstrap.Modal(document.getElementById('modalDeleteLearner'));
    viewEnrollmentsModal = new bootstrap.Modal(document.getElementById('modalViewEnrollments'));

    loadLearners();

    // Search input with debouncing
    const searchInput = document.getElementById('learnerSearchInput');
    let debounceTimer = null;
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                loadLearners(searchInput.value.trim());
            }, 300);
        });
    }

    // Reset form on open add
    const btnOpenAdd = document.getElementById('btnOpenAddLearner');
    if (btnOpenAdd) {
        btnOpenAdd.addEventListener('click', () => {
            document.getElementById('formLearner').reset();
            document.getElementById('learnerId').value = '';
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

async function loadLearners(search = '') {
    const tbody = document.getElementById('tbodyLearners');
    const badge = document.getElementById('learnerTotalBadge');

    try {
        const url = search ? `/api/learners?search=${encodeURIComponent(search)}` : '/api/learners';
        const res = await fetch(url);
        const json = await res.json();
        const learners = json.data || [];

        if (badge) badge.textContent = `${learners.length} learners`;

        if (learners.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-4 text-muted">
                        ${search ? `No learners found matching roll number "${search}".` : 'No learners registered yet. Click "Register Learner" above.'}
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = learners.map(l => {
            const initials = l.roll_no ? l.roll_no.substring(l.roll_no.length - 2).toUpperCase() : 'LR';
            return `
            <tr>
                <td><span class="badge bg-primary-subtle text-primary border border-primary-subtle fw-bold">#${l.learner_id}</span></td>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <div class="avatar-initials" style="width: 32px; height: 32px; font-size: 0.75rem;">${initials}</div>
                        <span class="roll-no-badge font-monospace">${l.roll_no}</span>
                    </div>
                </td>
                <td class="text-center">
                    <span class="badge ${l.enrollment_count > 0 ? 'badge-soft-primary' : 'badge-soft-secondary'} px-2 py-1">
                        ${l.enrollment_count} course(s)
                    </span>
                </td>
                <td class="text-end">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-info" title="View Enrolled Courses" onclick="openViewEnrollments(${l.learner_id}, '${encodeURIComponent(l.roll_no)}')">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-outline-secondary" title="Edit Roll Number" onclick="openEditLearner(${l.learner_id}, '${encodeURIComponent(l.roll_no)}')">
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
                <td colspan="4" class="text-center py-4 text-danger">
                    Failed to load learners from server.
                </td>
            </tr>
        `;
    }
}

function openEditLearner(id, encodedRoll) {
    document.getElementById('learnerId').value = id;
    document.getElementById('learnerRollNo').value = decodeURIComponent(encodedRoll);
    document.getElementById('modalLearnerTitle').textContent = `Edit Learner #${id}`;
    learnerModal.show();
}

function openDeleteLearner(id, encodedRoll) {
    learnerToDeleteId = id;
    document.getElementById('deleteLearnerRoll').textContent = decodeURIComponent(encodedRoll);
    deleteLearnerModal.show();
}

async function openViewEnrollments(id, encodedRoll) {
    const rollNo = decodeURIComponent(encodedRoll);
    document.getElementById('viewLearnerRoll').textContent = rollNo;
    const tbody = document.getElementById('tbodyLearnerEnrollments');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Loading course enrollments...</td></tr>';
    viewEnrollmentsModal.show();

    try {
        const res = await fetch(`/api/learners/${id}/enrollments`);
        const json = await res.json();
        const enrollments = json.data || [];

        if (enrollments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">This learner is not currently enrolled in any courses.</td></tr>';
            return;
        }

        tbody.innerHTML = enrollments.map(e => {
            const badgeClass = e.status === 'Completed' ? 'badge-soft-success' :
                               e.status === 'In Progress' ? 'badge-soft-warning' : 'badge-soft-secondary';
            return `
                <tr>
                    <td class="fw-semibold">${e.course_name}</td>
                    <td><span class="badge bg-light text-secondary border">${e.category}</span></td>
                    <td>${e.enrolled_at ? e.enrolled_at.substring(0, 10) : 'N/A'}</td>
                    <td class="text-center"><span class="badge ${badgeClass}">${e.status}</span></td>
                    <td class="text-center fw-bold">${e.total_activities}</td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-danger">Failed to fetch enrollments.</td></tr>';
    }
}

async function handleSaveLearner(e) {
    e.preventDefault();
    const id = document.getElementById('learnerId').value;
    const roll_no = document.getElementById('learnerRollNo').value.trim().toUpperCase();
    const btn = document.getElementById('btnSaveLearner');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';

    const isEdit = Boolean(id);
    const url = isEdit ? `/api/learners/${id}` : '/api/learners';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ roll_no })
        });
        const json = await res.json();

        if (res.ok && json.success) {
            showToast(json.message || 'Learner saved successfully!', 'success');
            learnerModal.hide();
            loadLearners();
        } else {
            showToast(json.message || 'Failed to save learner.', 'danger');
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
            loadLearners();
        } else {
            showToast(json.message || 'Failed to delete learner.', 'danger');
            deleteLearnerModal.hide();
        }
    } catch (err) {
        showToast('Network error while deleting learner.', 'danger');
        deleteLearnerModal.hide();
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-trash3 me-1"></i> Confirm Delete';
        learnerToDeleteId = null;
    }
}

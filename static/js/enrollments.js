/**
 * ====================================================================
 * E-Learning Course Analytics System - Enrollments JavaScript
 * File: static/js/enrollments.js
 * ====================================================================
 */

let enrollmentModal = null;
let updateStatusModal = null;
let activitiesModal = null;

document.addEventListener('DOMContentLoaded', () => {
    enrollmentModal = new bootstrap.Modal(document.getElementById('modalEnrollment'));
    updateStatusModal = new bootstrap.Modal(document.getElementById('modalUpdateStatus'));
    activitiesModal = new bootstrap.Modal(document.getElementById('modalEnrollmentActivities'));

    // Initial load
    loadFilterOptions();
    loadEnrollments();

    // Filters event listeners
    document.getElementById('filterCourseSelect')?.addEventListener('change', () => loadEnrollments());
    document.getElementById('filterStatusSelect')?.addEventListener('change', () => loadEnrollments());
    document.getElementById('btnEnrollmentSearch')?.addEventListener('click', () => loadEnrollments());
    document.getElementById('enrollmentSearchInput')?.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') loadEnrollments();
    });

    document.getElementById('btnResetFilters')?.addEventListener('click', () => {
        document.getElementById('filterCourseSelect').value = '';
        document.getElementById('filterStatusSelect').value = '';
        document.getElementById('enrollmentSearchInput').value = '';
        loadEnrollments();
    });

    // Populate dropdowns before opening new enrollment modal
    document.getElementById('btnOpenAddEnrollment')?.addEventListener('click', async () => {
        document.getElementById('formEnrollment').reset();
        await loadDropdownsForModal();
    });

    // Handle create enrollment submit
    document.getElementById('formEnrollment')?.addEventListener('submit', handleSaveEnrollment);

    // Handle update status submit
    document.getElementById('formUpdateStatus')?.addEventListener('submit', handleSaveStatus);
});

async function loadFilterOptions() {
    try {
        const res = await fetch('/api/courses');
        const json = await res.json();
        const courses = json.data || [];
        const select = document.getElementById('filterCourseSelect');
        if (select) {
            courses.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.course_id;
                opt.textContent = c.course_name;
                select.appendChild(opt);
            });
        }
    } catch (err) {
        console.error('Error loading courses for filter:', err);
    }
}

async function loadDropdownsForModal() {
    try {
        const [resLearners, resCourses] = await Promise.all([
            fetch('/api/learners'),
            fetch('/api/courses')
        ]);
        const jsonLearners = await resLearners.json();
        const jsonCourses = await resCourses.json();

        const selectLearner = document.getElementById('selectLearner');
        const selectCourse = document.getElementById('selectCourse');

        selectLearner.innerHTML = '<option value="">-- Choose Learner by Roll No --</option>';
        (jsonLearners.data || []).forEach(l => {
            const opt = document.createElement('option');
            opt.value = l.learner_id;
            opt.textContent = `${l.roll_no} (ID: ${l.learner_id})`;
            selectLearner.appendChild(opt);
        });

        selectCourse.innerHTML = '<option value="">-- Choose Course --</option>';
        (jsonCourses.data || []).forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.course_id;
            opt.textContent = `${c.course_name} (${c.category})`;
            selectCourse.appendChild(opt);
        });
    } catch (err) {
        showToast('Failed to load learners and courses for enrollment selection.', 'danger');
    }
}

async function loadEnrollments() {
    const tbody = document.getElementById('tbodyEnrollments');
    const badge = document.getElementById('enrollmentTotalBadge');
    const courseId = document.getElementById('filterCourseSelect')?.value || '';
    const status = document.getElementById('filterStatusSelect')?.value || '';
    const search = document.getElementById('enrollmentSearchInput')?.value.trim() || '';

    try {
        const params = new URLSearchParams();
        if (courseId) params.append('course_id', courseId);
        if (status) params.append('status', status);
        if (search) params.append('search', search);

        const res = await fetch(`/api/enrollments?${params.toString()}`);
        const json = await res.json();
        const enrollments = json.data || [];

        if (badge) badge.textContent = `${enrollments.length} records`;

        if (enrollments.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4 text-muted">
                        No enrollments match the selected filters.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = enrollments.map(e => {
            const badgeClass = e.status === 'Completed' ? 'badge-soft-success' :
                               e.status === 'In Progress' ? 'badge-soft-warning' : 'badge-soft-secondary';

            return `
                <tr>
                    <td><span class="badge bg-primary-subtle text-primary border border-primary-subtle fw-bold">#${e.enrollment_id}</span></td>
                    <td>
                        <span class="roll-no-badge font-monospace">${escapeHtml(e.roll_no)}</span>
                    </td>
                    <td>
                        <div class="fw-bold text-navy">${escapeHtml(e.course_name)}</div>
                        <small class="text-muted">${escapeHtml(e.category)}</small>
                    </td>
                    <td>${escapeHtml(e.enrolled_at || 'N/A')}</td>
                    <td class="text-center">
                        <span class="badge ${badgeClass} px-2 py-1">${escapeHtml(e.status)}</span>
                    </td>
                    <td class="text-center">
                        <span class="badge bg-primary-subtle text-primary fw-bold px-2 py-1">${e.activity_count}</span>
                    </td>
                    <td>
                        <small class="text-muted">${escapeHtml(e.last_activity_date || 'No activity')}</small>
                    </td>
                    <td class="text-end">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-info" title="View Activity History" onclick="openEnrollmentActivities(${e.enrollment_id}, '${encodeURIComponent(e.roll_no)}', '${encodeURIComponent(e.course_name)}')">
                                <i class="bi bi-clock-history"></i>
                            </button>
                            <button class="btn btn-outline-secondary" title="Change Status" onclick="openUpdateStatusModal(${e.enrollment_id}, '${encodeURIComponent(e.roll_no)}', '${encodeURIComponent(e.course_name)}', '${e.status}')">
                                <i class="bi bi-pencil-square"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (err) {
        console.error('Error fetching enrollments:', err);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4 text-danger">
                    Failed to load enrollments from server.
                </td>
            </tr>
        `;
    }
}

async function handleSaveEnrollment(e) {
    e.preventDefault();
    const learner_id = parseInt(document.getElementById('selectLearner').value);
    const course_id = parseInt(document.getElementById('selectCourse').value);
    const status = document.getElementById('selectStatus').value;
    const btn = document.getElementById('btnSaveEnrollment');

    if (!learner_id || !course_id) {
        showToast('Please select both a learner and a course.', 'warning');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Enrolling...';

    try {
        const res = await fetch('/api/enrollments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ learner_id, course_id, status })
        });
        const json = await res.json();

        if (res.ok && json.success) {
            showToast(json.message || 'Learner enrolled successfully!', 'success');
            enrollmentModal.hide();
            loadEnrollments();
        } else {
            showToast(json.message || json.error || 'Failed to enroll learner.', 'danger');
        }
    } catch (err) {
        showToast('Network error while enrolling learner.', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-mortarboard me-1"></i> Enroll Student';
    }
}

function openUpdateStatusModal(id, encodedRoll, encodedCourse, currentStatus) {
    document.getElementById('updateEnrollmentId').value = id;
    document.getElementById('updateStatusRoll').textContent = decodeURIComponent(encodedRoll);
    document.getElementById('updateStatusCourse').textContent = decodeURIComponent(encodedCourse);
    document.getElementById('newEnrollmentStatus').value = currentStatus;
    updateStatusModal.show();
}

async function handleSaveStatus(e) {
    e.preventDefault();
    const id = document.getElementById('updateEnrollmentId').value;
    const status = document.getElementById('newEnrollmentStatus').value;
    const btn = document.getElementById('btnSaveStatus');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Updating...';

    try {
        const res = await fetch(`/api/enrollments/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        const json = await res.json();

        if (res.ok && json.success) {
            showToast(json.message || 'Status updated!', 'success');
            updateStatusModal.hide();
            loadEnrollments();
        } else {
            showToast(json.message || json.error || 'Failed to update status.', 'danger');
        }
    } catch (err) {
        showToast('Network error while updating status.', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-check2 me-1"></i> Update Status';
    }
}

async function openEnrollmentActivities(enrollmentId, encodedRoll, encodedCourse) {
    const rollNo = decodeURIComponent(encodedRoll);
    const course = decodeURIComponent(encodedCourse);
    document.getElementById('viewActivitySubtitle').textContent = `${rollNo} in "${course}"`;
    const tbody = document.getElementById('tbodyEnrollmentActivities');
    tbody.innerHTML = '<tr><td colspan="3" class="text-center py-4 text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Loading activities...</td></tr>';
    activitiesModal.show();

    try {
        const res = await fetch(`/api/enrollments/${enrollmentId}/activities`);
        const json = await res.json();
        const activities = json.data || [];

        if (activities.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center py-4 text-muted">No activities have been logged for this enrollment yet.</td></tr>';
            return;
        }

        tbody.innerHTML = activities.map(a => `
            <tr>
                <td class="fw-semibold">
                    <span class="badge bg-light text-dark border me-1">${a.activity_type}</span>
                </td>
                <td>${a.activity_date}</td>
                <td class="text-center">
                    <span class="badge ${a.completed ? 'badge-soft-success' : 'badge-soft-warning'}">
                        ${a.completed ? '<i class="bi bi-check-lg me-1"></i> Completed' : '<i class="bi bi-hourglass-split me-1"></i> Pending'}
                    </span>
                </td>
            </tr>
        `).join('');

    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center py-4 text-danger">Failed to fetch activities.</td></tr>';
    }
}

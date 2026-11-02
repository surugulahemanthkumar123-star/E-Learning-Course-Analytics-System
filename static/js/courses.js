/**
 * ====================================================================
 * E-Learning Course Analytics System - Courses Management JavaScript
 * File: static/js/courses.js
 * ====================================================================
 */

let courseModal = null;
let deleteCourseModal = null;
let courseToDeleteId = null;

document.addEventListener('DOMContentLoaded', () => {
    courseModal = new bootstrap.Modal(document.getElementById('modalCourse'));
    deleteCourseModal = new bootstrap.Modal(document.getElementById('modalDeleteCourse'));

    loadCategoryFilters();
    loadCourses();

    // Search input with debouncing
    const searchInput = document.getElementById('courseSearchInput');
    let debounceTimer = null;
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                loadCourses();
            }, 300);
        });
    }

    // Category filter dropdown
    const categoryFilter = document.getElementById('courseCategoryFilter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', () => loadCourses());
    }

    // Reset filters button
    const btnReset = document.getElementById('btnResetCourseFilters');
    if (btnReset) {
        btnReset.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            if (categoryFilter) categoryFilter.value = '';
            loadCourses();
        });
    }

    // Reset form on open add
    const btnOpenAdd = document.getElementById('btnOpenAddCourse');
    if (btnOpenAdd) {
        btnOpenAdd.addEventListener('click', () => {
            document.getElementById('formCourse').reset();
            document.getElementById('courseId').value = '';
            document.getElementById('courseCredits').value = '';
            document.getElementById('courseDescription').value = '';
            document.getElementById('modalCourseTitle').textContent = 'Add New Course';
        });
    }

    // Submit form (Create / Update)
    const formCourse = document.getElementById('formCourse');
    if (formCourse) {
        formCourse.addEventListener('submit', handleSaveCourse);
    }

    // Confirm Delete
    const btnConfirmDelete = document.getElementById('btnConfirmDeleteCourse');
    if (btnConfirmDelete) {
        btnConfirmDelete.addEventListener('click', handleConfirmDelete);
    }
});

async function loadCategoryFilters() {
    const select = document.getElementById('courseCategoryFilter');
    if (!select) return;

    try {
        const res = await fetch('/api/courses/categories');
        const json = await res.json();
        const categories = json.data || [];

        // Preserve "All Categories" option
        select.innerHTML = '<option value="">All Categories</option>';
        categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error('Error fetching course categories for filter:', err);
    }
}

async function loadCourses() {
    const tbody = document.getElementById('tbodyCourses');
    const badge = document.getElementById('courseTotalBadge');
    const search = document.getElementById('courseSearchInput')?.value.trim() || '';
    const category = document.getElementById('courseCategoryFilter')?.value || '';

    try {
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (category) params.append('category', category);

        const url = `/api/courses${params.toString() ? '?' + params.toString() : ''}`;
        const res = await fetch(url);
        const json = await res.json();
        const courses = json.data || [];

        if (badge) badge.textContent = `${courses.length} courses`;

        if (courses.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-4 text-muted">
                        ${search || category ? 'No courses found matching the selected filters.' : 'No courses registered yet. Click "Add Course" above.'}
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = courses.map(c => {
            const creditsBadge = c.credits !== null && c.credits !== undefined ?
                `<span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle fw-semibold">${escapeHtml(c.credits)} cr</span>` :
                '<span class="text-muted small">-</span>';

            const rate = typeof c.completion_rate === 'number' ? c.completion_rate : 0;
            const progressColor = rate >= 75 ? 'bg-success' : rate >= 40 ? 'bg-primary' : rate > 0 ? 'bg-warning' : 'bg-secondary';
            const descPreview = c.description ? `<p class="small text-muted mb-0 mt-1 text-truncate" style="max-width: 320px;" title="${escapeHtml(c.description)}">${escapeHtml(c.description)}</p>` : '';

            return `
            <tr>
                <td><span class="badge bg-primary-subtle text-primary border border-primary-subtle fw-bold">#${c.course_id}</span></td>
                <td>
                    <div class="fw-bold text-navy">${escapeHtml(c.course_name)}</div>
                    ${descPreview}
                </td>
                <td>
                    <span class="badge bg-light text-secondary border">${escapeHtml(c.category)}</span>
                </td>
                <td class="text-center">
                    ${creditsBadge}
                </td>
                <td class="text-center">
                    <span class="badge ${c.enrollment_count > 0 ? 'bg-primary-subtle text-primary border border-primary-subtle' : 'bg-light text-muted border'} px-2 py-1">
                        <i class="bi bi-people me-1"></i>${c.enrollment_count} enrolled
                    </span>
                </td>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <span class="small fw-bold text-navy" style="min-width: 42px;">${rate.toFixed(1)}%</span>
                        <div class="progress flex-grow-1" style="height: 6px;">
                            <div class="progress-bar ${progressColor}" style="width: ${rate}%;"></div>
                        </div>
                        <small class="text-muted" style="font-size: 0.75rem;">(${c.completed_count || 0}/${c.enrollment_count || 0})</small>
                    </div>
                </td>
                <td class="text-end">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-secondary" title="Edit Course" onclick="openEditCourse(${c.course_id})">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger" title="Delete Course" onclick="openDeleteCourse(${c.course_id}, '${encodeURIComponent(c.course_name)}')">
                            <i class="bi bi-trash3"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        }).join('');

    } catch (err) {
        console.error('Error fetching courses:', err);
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4 text-danger">
                    Failed to load courses from server.
                </td>
            </tr>
        `;
    }
}

async function openEditCourse(id) {
    try {
        const res = await fetch(`/api/courses/${id}`);
        const json = await res.json();
        if (!res.ok || !json.success) {
            showToast(json.message || 'Failed to load course details.', 'danger');
            return;
        }
        const c = json.data;
        document.getElementById('courseId').value = c.course_id;
        document.getElementById('courseName').value = c.course_name || '';
        document.getElementById('courseCategory').value = c.category || '';
        document.getElementById('courseDescription').value = c.description || '';
        document.getElementById('courseCredits').value = c.credits !== null && c.credits !== undefined ? c.credits : '';
        document.getElementById('modalCourseTitle').textContent = `Edit Course #${c.course_id}`;
        courseModal.show();
    } catch (err) {
        showToast('Network error while retrieving course details.', 'danger');
    }
}

function openDeleteCourse(id, encodedName) {
    courseToDeleteId = id;
    document.getElementById('deleteCourseName').textContent = decodeURIComponent(encodedName);
    deleteCourseModal.show();
}

async function handleSaveCourse(e) {
    e.preventDefault();
    const btn = document.getElementById('btnSaveCourse');
    const id = document.getElementById('courseId').value;
    const name = document.getElementById('courseName').value.trim();
    const category = document.getElementById('courseCategory').value.trim();
    const description = document.getElementById('courseDescription').value.trim();
    const creditsVal = document.getElementById('courseCredits').value;

    if (!name || !category) {
        showToast('Course name and category are required.', 'warning');
        return;
    }

    const payload = {
        course_name: name,
        category: category,
        description: description || null,
        credits: creditsVal !== '' ? parseInt(creditsVal, 10) : null
    };

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';

    try {
        const url = id ? `/api/courses/${id}` : '/api/courses';
        const method = id ? 'PUT' : 'POST';

        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const json = await res.json();

        if (res.ok && json.success) {
            showToast(json.message || 'Course saved successfully.', 'success');
            courseModal.hide();
            await loadCategoryFilters();
            loadCourses();
        } else {
            showToast(json.message || json.error || 'Failed to save course.', 'danger');
        }
    } catch (err) {
        showToast('Network error while saving course.', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-check2 me-1"></i> Save Course';
    }
}

async function handleConfirmDelete() {
    if (!courseToDeleteId) return;

    const btn = document.getElementById('btnConfirmDeleteCourse');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Deleting...';

    try {
        const res = await fetch(`/api/courses/${courseToDeleteId}`, { method: 'DELETE' });
        const json = await res.json();

        if (res.ok && json.success) {
            showToast(json.message || 'Course deleted successfully.', 'success');
            deleteCourseModal.hide();
            await loadCategoryFilters();
            loadCourses();
        } else {
            showToast(json.message || json.error || 'Failed to delete course.', 'danger');
        }
    } catch (err) {
        showToast('Network error while deleting course.', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-trash3 me-1"></i> Confirm Delete';
        courseToDeleteId = null;
    }
}

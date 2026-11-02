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

    loadCourses();

    // Search input with debouncing
    const searchInput = document.getElementById('courseSearchInput');
    let debounceTimer = null;
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                loadCourses(searchInput.value.trim());
            }, 300);
        });
    }

    // Reset form on open add
    const btnOpenAdd = document.getElementById('btnOpenAddCourse');
    if (btnOpenAdd) {
        btnOpenAdd.addEventListener('click', () => {
            document.getElementById('formCourse').reset();
            document.getElementById('courseId').value = '';
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

async function loadCourses(search = '') {
    const tbody = document.getElementById('tbodyCourses');
    const badge = document.getElementById('courseTotalBadge');

    try {
        const url = search ? `/api/courses?search=${encodeURIComponent(search)}` : '/api/courses';
        const res = await fetch(url);
        const json = await res.json();
        const courses = json.data || [];

        if (badge) badge.textContent = `${courses.length} courses`;

        if (courses.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-4 text-muted">
                        ${search ? `No courses found matching "${search}".` : 'No courses registered yet. Click "Add Course" above.'}
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = courses.map(c => `
            <tr>
                <td><span class="badge bg-primary-subtle text-primary border border-primary-subtle fw-bold">#${c.course_id}</span></td>
                <td>
                    <div class="fw-bold text-navy">${c.course_name}</div>
                </td>
                <td>
                    <span class="badge bg-light text-secondary border">${c.category}</span>
                </td>
                <td class="text-center">
                    <span class="badge ${c.enrollment_count > 0 ? 'bg-primary-subtle text-primary' : 'bg-light text-muted border'} px-2 py-1">
                        ${c.enrollment_count} enrolled
                    </span>
                </td>
                <td class="text-end">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-secondary" onclick="openEditCourse(${c.course_id}, '${encodeURIComponent(c.course_name)}', '${encodeURIComponent(c.category)}')">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="openDeleteCourse(${c.course_id}, '${encodeURIComponent(c.course_name)}')">
                            <i class="bi bi-trash3"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

    } catch (err) {
        console.error('Error fetching courses:', err);
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4 text-danger">
                    Failed to load courses from server.
                </td>
            </tr>
        `;
    }
}

function openEditCourse(id, encodedName, encodedCategory) {
    document.getElementById('courseId').value = id;
    document.getElementById('courseName').value = decodeURIComponent(encodedName);
    document.getElementById('courseCategory').value = decodeURIComponent(encodedCategory);
    document.getElementById('modalCourseTitle').textContent = `Edit Course #${id}`;
    courseModal.show();
}

function openDeleteCourse(id, encodedName) {
    courseToDeleteId = id;
    document.getElementById('deleteCourseName').textContent = decodeURIComponent(encodedName);
    deleteCourseModal.show();
}

async function handleSaveCourse(e) {
    e.preventDefault();
    const id = document.getElementById('courseId').value;
    const course_name = document.getElementById('courseName').value.trim();
    const category = document.getElementById('courseCategory').value.trim();
    const btn = document.getElementById('btnSaveCourse');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';

    const isEdit = Boolean(id);
    const url = isEdit ? `/api/courses/${id}` : '/api/courses';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ course_name, category })
        });
        const json = await res.json();

        if (res.ok && json.success) {
            showToast(json.message || 'Course saved successfully!', 'success');
            courseModal.hide();
            loadCourses();
        } else {
            showToast(json.message || 'Failed to save course.', 'danger');
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
            showToast(json.message || 'Course deleted.', 'success');
            deleteCourseModal.hide();
            loadCourses();
        } else {
            showToast(json.message || 'Failed to delete course.', 'danger');
            deleteCourseModal.hide();
        }
    } catch (err) {
        showToast('Network error while deleting course.', 'danger');
        deleteCourseModal.hide();
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-trash3 me-1"></i> Confirm Delete';
        courseToDeleteId = null;
    }
}

/*
 * Kanban board interactions:
 * - CSRF handling for AJAX requests
 * - Drag-and-drop workflow state changes using SortableJS
 * - Transition modal for states that require date input
 * - Quick-view modal for application cards
 * - Reminder hover highlighting for related Kanban cards
 */


/* --------------------------------------------------------------------------
 * CSRF handling
 * -------------------------------------------------------------------------- */

function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(';') : [];

    for (let cookie of cookies) {
        cookie = cookie.trim();

        if (cookie.startsWith(name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }

    return null;
}

const csrfToken = getCookie('csrftoken');


/* --------------------------------------------------------------------------
 * Shared state for pending Kanban transitions
 * -------------------------------------------------------------------------- */

let pendingTransition = null;


/* --------------------------------------------------------------------------
 * Utility functions
 * -------------------------------------------------------------------------- */

function getTodayDateString() {
    const today = new Date();

    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');

    return `${year}-${month}-${day}`;
}

function redirectToLogin() {
    const nextUrl = encodeURIComponent(window.location.pathname);
    window.location.href = `/accounts/login/?next=${nextUrl}`;
}


/* --------------------------------------------------------------------------
 * Status update request handling
 * -------------------------------------------------------------------------- */

function postStatusUpdate(updateUrl, status, extraData = {}) {
    return fetch(updateUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({
            status: status,
            ...extraData,
        }),
    });
}

function handleStatusUpdateResponse(response) {
    if (response.status === 401 || response.status === 403) {
        redirectToLogin();
        throw new Error('AUTH_REDIRECT');
    }

    if (!response.ok) {
        return response.json().then(function (data) {
            throw new Error(data.error || 'Status update failed.');
        });
    }

    return response.json();
}

function finishStatusUpdate(data) {
    if (data.success) {
        window.location.reload();
        return;
    }

    alert(data.error || 'Status update failed.');
    window.location.reload();
}

function handleStatusUpdateError(error) {
    if (error.message === 'AUTH_REDIRECT') {
        return;
    }

    alert(error.message);
    window.location.reload();
}


/* --------------------------------------------------------------------------
 * Transition modal
 *
 * Some workflow states require additional data:
 * - Applied -> applied_at
 * - Interview Scheduled -> interview_at
 * - Interview Completed -> interview_completed_at
 * - Offer Received -> offer_deadline
 *
 * The required field is configured on the target Kanban column using data-*.
 * -------------------------------------------------------------------------- */

function openTransitionModal(column, card) {
    const field = column.dataset.transitionField;
    const label = column.dataset.transitionLabel;
    const inputType = column.dataset.transitionInputType;
    const defaultToday = column.dataset.transitionDefaultToday === 'true';

    pendingTransition = {
        updateUrl: card.dataset.updateUrl,
        newStatus: column.dataset.status,
        field: field,
        inputType: inputType,
    };

    const modalElement = document.getElementById('stateTransitionModal');
    const labelElement = document.getElementById('stateTransitionFieldLabel');
    const dateInput = document.getElementById('stateTransitionDateInput');
    const dateTimeInput = document.getElementById('stateTransitionDateTimeInput');
    const errorElement = document.getElementById('stateTransitionError');

    if (!modalElement || !labelElement || !dateInput || !dateTimeInput || !errorElement) {
        return;
    }

    labelElement.textContent = label;

    dateInput.classList.add('d-none');
    dateTimeInput.classList.add('d-none');
    errorElement.classList.add('d-none');

    dateInput.value = '';
    dateTimeInput.value = '';

    if (inputType === 'datetime-local') {
        dateTimeInput.classList.remove('d-none');
    } else {
        dateInput.classList.remove('d-none');

        if (defaultToday) {
            dateInput.value = getTodayDateString();
        }
    }

    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

function getTransitionInputValue(inputType) {
    if (inputType === 'datetime-local') {
        return document.getElementById('stateTransitionDateTimeInput').value;
    }

    return document.getElementById('stateTransitionDateInput').value;
}

function submitPendingTransition() {
    if (!pendingTransition) {
        return;
    }

    const value = getTransitionInputValue(pendingTransition.inputType);
    const errorElement = document.getElementById('stateTransitionError');

    if (!value) {
        errorElement.classList.remove('d-none');
        return;
    }

    const extraData = {};
    extraData[pendingTransition.field] = value;

    postStatusUpdate(
        pendingTransition.updateUrl,
        pendingTransition.newStatus,
        extraData
    )
        .then(handleStatusUpdateResponse)
        .then(finishStatusUpdate)
        .catch(handleStatusUpdateError);
}

function setupTransitionModal() {
    const saveTransitionButton = document.getElementById('stateTransitionSaveButton');
    const transitionModal = document.getElementById('stateTransitionModal');

    if (saveTransitionButton) {
        saveTransitionButton.addEventListener('click', submitPendingTransition);
    }

    if (transitionModal) {
        transitionModal.addEventListener('hidden.bs.modal', function () {
            if (pendingTransition) {
                pendingTransition = null;

                /*
                 * SortableJS already moved the card visually.
                 * If the modal is cancelled, reload the board so the card returns
                 * to the persisted database state.
                 */
                window.location.reload();
            }
        });
    }
}


/* --------------------------------------------------------------------------
 * SortableJS Kanban board
 * -------------------------------------------------------------------------- */

function setupKanbanDragAndDrop() {
    const columns = document.querySelectorAll('.kanban-column');

    if (!columns.length || typeof Sortable === 'undefined') {
        return;
    }

    columns.forEach(function (column) {
        new Sortable(column, {
            group: 'applications',
            animation: 150,
            ghostClass: 'opacity-50',
            draggable: '.kanban-card',

            onEnd: function (evt) {
                const card = evt.item;
                const newStatus = evt.to.dataset.status;
                const oldStatus = evt.from.dataset.status;

                if (!card.classList.contains('kanban-card')) {
                    return;
                }

                if (newStatus === oldStatus) {
                    return;
                }

                /*
                 * If the target column requires additional transition data,
                 * open the modal instead of sending the update immediately.
                 */
                const transitionField = evt.to.dataset.transitionField;

                if (transitionField) {
                    openTransitionModal(evt.to, card);
                    return;
                }

                const updateUrl = card.dataset.updateUrl;

                postStatusUpdate(updateUrl, newStatus)
                    .then(handleStatusUpdateResponse)
                    .then(finishStatusUpdate)
                    .catch(handleStatusUpdateError);
            },
        });
    });
}


/* --------------------------------------------------------------------------
 * Quick-view modal
 *
 * Opens a lightweight modal with application details and next reminder data.
 * Full editing/history remains on the detail page.
 * -------------------------------------------------------------------------- */

function setupQuickViewModal() {
    const quickViewModal = document.getElementById('applicationQuickViewModal');

    if (!quickViewModal) {
        return;
    }

    quickViewModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;

        if (!button) {
            return;
        }

        const jobTitle = button.getAttribute('data-job-title');
        const companyName = button.getAttribute('data-company-name');

        const status = button.getAttribute('data-status');
        const statusClass = button.getAttribute('data-status-class') || 'bg-secondary';

        const reminderTitle = button.getAttribute('data-reminder-title');
        const reminderDue = button.getAttribute('data-reminder-due');
        const reminderState = button.getAttribute('data-reminder-state');

        const deadline = button.getAttribute('data-deadline');
        const contactEmail = button.getAttribute('data-contact-email');
        const notes = button.getAttribute('data-notes');

        const detailUrl = button.getAttribute('data-detail-url');
        const editUrl = button.getAttribute('data-edit-url');

        document.getElementById('applicationQuickViewModalLabel').textContent = jobTitle;
        document.getElementById('modalCompanyName').textContent = companyName;

        renderStatusBadge(status, statusClass);
        renderNextReminder(reminderTitle, reminderDue, reminderState);

        document.getElementById('modalDeadline').textContent = deadline;
        document.getElementById('modalContactEmail').textContent = contactEmail;
        document.getElementById('modalNotes').textContent = notes;

        document.getElementById('modalDetailLink').setAttribute('href', detailUrl);
        document.getElementById('modalEditLink').setAttribute('href', editUrl);
    });
}

function renderStatusBadge(status, statusClass) {
    const statusElement = document.getElementById('modalStatus');

    if (!statusElement) {
        return;
    }

    statusElement.innerHTML = '';

    const statusBadge = document.createElement('span');
    statusBadge.className = `badge ${statusClass}`;
    statusBadge.textContent = status;

    statusElement.appendChild(statusBadge);
}

function renderNextReminder(reminderTitle, reminderDue, reminderState) {
    const reminderElement = document.getElementById('modalNextReminder');

    if (!reminderElement) {
        return;
    }

    reminderElement.innerHTML = '';

    if (!reminderTitle || !reminderDue) {
        reminderElement.innerHTML = '<span class="text-muted">No open reminder</span>';
        return;
    }

    const wrapper = document.createElement('div');

    const titleElement = document.createElement('div');
    titleElement.textContent = reminderTitle;

    const dueElement = document.createElement('div');
    dueElement.classList.add('small', 'mt-1');

    if (reminderState === 'overdue') {
        dueElement.classList.add('text-danger', 'fw-semibold');
        dueElement.textContent = `Due: ${reminderDue} overdue`;
    } else if (reminderState === 'today') {
        dueElement.classList.add('text-warning', 'fw-semibold');
        dueElement.textContent = `Due: ${reminderDue} today`;
    } else {
        dueElement.classList.add('text-muted');
        dueElement.textContent = `Due: ${reminderDue}`;
    }

    wrapper.appendChild(titleElement);
    wrapper.appendChild(dueElement);

    reminderElement.appendChild(wrapper);
}


/* --------------------------------------------------------------------------
 * Reminder hover highlighting
 *
 * Hovering over a reminder in the top list highlights the corresponding
 * application card on the Kanban board.
 * -------------------------------------------------------------------------- */

function setupReminderHoverHighlight() {
    const reminderItems = document.querySelectorAll('.reminder-list-item');

    reminderItems.forEach(function (reminderItem) {
        const applicationId = reminderItem.dataset.applicationId;
        const card = document.getElementById(`application-card-${applicationId}`);

        if (!card) {
            return;
        }

        reminderItem.addEventListener('mouseenter', function () {
            card.classList.add('kanban-card-highlight');

            card.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'center',
            });
        });

        reminderItem.addEventListener('mouseleave', function () {
            card.classList.remove('kanban-card-highlight');
        });
    });
}


/* --------------------------------------------------------------------------
 * Page initialisation
 * -------------------------------------------------------------------------- */

function initKanbanPage() {
    setupKanbanDragAndDrop();
    setupTransitionModal();
    setupQuickViewModal();
    setupReminderHoverHighlight();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initKanbanPage);
} else {
    initKanbanPage();
}
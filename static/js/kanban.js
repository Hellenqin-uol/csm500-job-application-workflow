function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(';') : []

    for (let cookie of cookies) {
        cookie = cookie.trim()

        if (cookie.startsWith(name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1))
        }
    }
    return null
}

const csrfToken = getCookie('csrftoken')
let pendingTransition = null

function getTodayDateString() {
    const today = new Date()
    const year = today.getFullYear()
    const month = String(today.getMonth() + 1).padStart(2, '0')
    const day = String(today.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
}

function postStatusUpdate(updateUrl, status, extraData = {}) {
    return fetch(updateUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({status: status, ...extraData})
    })
}

function handleStatusUpdateResponse(response) {
    if (response.status === 401 || response.status === 403) {
        window.location.href = `/accounts/login/?next=${encodeURIComponent(window.location.pathname)}`
        throw new Error('AUTH_REDIRECT')
    }
    if (!response.ok) {
        return response.json().then((data) => {
            throw new Error(data.error || 'Status update failed.')
        })
    }
    return response.json()
}

function finishStatusUpdate(data) {
    if (data.success) {
        window.location.reload()
        return
    }
    alert(data.error || 'Status update failed.')
    window.location.reload()
}

function openTransitionModal(column, card) {
    const field = column.dataset.transitionField
    const label = column.dataset.transitionLabel
    const inputType = column.dataset.transitionInputType
    const defaultToday = column.dataset.transitionDefaultToday === 'true'

    pendingTransition = {
        updateUrl: card.dataset.updateUrl,
        newStatus: column.dataset.status,
        field: field,
        inputType: inputType
    }

    const modalElement = document.getElementById('stateTransitionModal')
    const labelElement = document.getElementById('stateTransitionFieldLabel')
    const dateInput = document.getElementById('stateTransitionDateInput')
    const dateTimeInput = document.getElementById('stateTransitionDateTimeInput')
    const errorElement = document.getElementById('stateTransitionError')

    labelElement.textContent = label

    dateInput.classList.add('d-none')
    dateTimeInput.classList.add('d-none')
    errorElement.classList.add('d-none')

    dateInput.value = ''
    dateTimeInput.value = ''

    if (inputType === 'datetime-local') {
        dateTimeInput.classList.remove('d-none')
    } else {
        dateInput.classList.remove('d-none')

        if (defaultToday) {
            dateInput.value = getTodayDateString()
        }
    }

    const modal = new bootstrap.Modal(modalElement)
    modal.show()
}

function getTransitionInputValue(inputType) {
    if (inputType === 'datetime-local') {
        return document.getElementById('stateTransitionDateTimeInput').value
    }
    return document.getElementById('stateTransitionDateInput').value
}

function submitPendingTransition() {
    if (!pendingTransition) {
        return
    }
    const value = getTransitionInputValue(pendingTransition.inputType)
    const errorElement = document.getElementById('stateTransitionError')

    if (!value) {
        errorElement.classList.remove('d-none')
        return
    }

    const extraData = {}
    extraData[pendingTransition.field] = value

    postStatusUpdate(
        pendingTransition.updateUrl,
        pendingTransition.newStatus,
        extraData
    )
        .then(handleStatusUpdateResponse)
        .then(finishStatusUpdate)
        .catch((error) => {
            if (error.message === 'AUTH_REDIRECT') {
                return
            }

            alert(error.message)
            window.location.reload()
        })
}

document.querySelectorAll('.kanban-column').forEach(function (column) {
    new Sortable(column, {
    group: 'applications',
    animation: 150,
    ghostClass: 'opacity-50',
    draggable: ".kanban-card",

    onEnd: function (evt) {
        const card = evt.item
        const newStatus = evt.to.dataset.status
        const oldStatus = evt.from.dataset.status

        if (newStatus === oldStatus) {
            return
        }
        const transitionField = evt.to.dataset.transitionField

        if (transitionField) {
            openTransitionModal(evt.to, card)
            return
        }
        const updateUrl = card.dataset.updateUrl


        postStatusUpdate(updateUrl, newStatus)
            .then(handleStatusUpdateResponse)
            .then(finishStatusUpdate)
            .catch((error) => {
                if (error.message === 'AUTH_REDIRECT') {
                    return
                }

                alert(error.message)
                window.location.reload()
            })
    }
    })
})

const saveTransitionButton = document.getElementById('stateTransitionSaveButton')

if (saveTransitionButton) {
    saveTransitionButton.addEventListener('click', submitPendingTransition)
}

const transitionModal = document.getElementById('stateTransitionModal')

if (transitionModal) {
    transitionModal.addEventListener('hidden.bs.modal', function () {
        if (pendingTransition) {
            pendingTransition = null
            // The card was already moved visually by SortableJS.
            // Reload to restore the board if the transition was cancelled.
            window.location.reload()
        }
    })
}

const quickViewModal = document.getElementById('applicationQuickViewModal')

if (quickViewModal) {
    quickViewModal.addEventListener('show.bs.modal', function (event) {
    const button = event.relatedTarget

    const jobTitle = button.getAttribute('data-job-title')
    const companyName = button.getAttribute('data-company-name')
    const status = button.getAttribute('data-status')
    const statusClass = button.getAttribute("data-status-class") || "bg-secondary"
    const reminderTitle = button.getAttribute("data-reminder-title")
    const reminderDue = button.getAttribute("data-reminder-due")
    const reminderState = button.getAttribute("data-reminder-state")

    const deadline = button.getAttribute('data-deadline')
    const contactEmail = button.getAttribute('data-contact-email')
    const notes = button.getAttribute('data-notes')
    const detailUrl = button.getAttribute('data-detail-url')
    const editUrl = button.getAttribute('data-edit-url')

    document.getElementById('applicationQuickViewModalLabel').textContent = jobTitle
    document.getElementById('modalCompanyName').textContent = companyName

    const statusElement = document.getElementById("modalStatus")
    statusElement.innerHTML = ""

    const statusBadge = document.createElement("span")
    statusBadge.className = `badge ${statusClass}`
    statusBadge.textContent = status

    statusElement.appendChild(statusBadge)

    const reminderElement = document.getElementById("modalNextReminder")
    reminderElement.innerHTML = ""


    if (reminderTitle && reminderDue) {
        const wrapper = document.createElement("div")

        const titleElement = document.createElement("div")
        titleElement.textContent = reminderTitle

        const dueElement = document.createElement("div")
        dueElement.classList.add("small", "mt-1")

        if (reminderState === "overdue") {
            dueElement.classList.add("text-danger", "fw-semibold")
            dueElement.textContent = `Due: ${reminderDue} overdue`
        } else if (reminderState === "today") {
            dueElement.classList.add("text-warning", "fw-semibold")
            dueElement.textContent = `Due: ${reminderDue} today`
        } else {
            dueElement.classList.add("text-muted");
            dueElement.textContent = `Due: ${reminderDue}`
        }

        wrapper.appendChild(titleElement)
        wrapper.appendChild(dueElement)
        reminderElement.appendChild(wrapper)
    } else {
        reminderElement.innerHTML = '<span class="text-muted">No open reminder</span>'
    }

    document.getElementById('modalDeadline').textContent = deadline
    document.getElementById('modalContactEmail').textContent = contactEmail
    document.getElementById('modalNotes').textContent = notes

    document.getElementById('modalDetailLink').setAttribute('href', detailUrl)
    document.getElementById('modalEditLink').setAttribute('href', editUrl)
    })
}

function setupReminderHoverHighlight() {
  const reminderItems = document.querySelectorAll(".reminder-list-item");

  reminderItems.forEach(function(reminderItem) {
    const applicationId = reminderItem.dataset.applicationId;
    const card = document.getElementById(`application-card-${applicationId}`);

    if (!card) {
      return;
    }

    reminderItem.addEventListener("mouseenter", function() {
      card.classList.add("kanban-card-highlight");
      card.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
        inline: "center",
      });
    });

    reminderItem.addEventListener("mouseleave", function() {
      card.classList.remove("kanban-card-highlight");
    });
  });
}

document.addEventListener("DOMContentLoaded", function() {
  setupReminderHoverHighlight();
});

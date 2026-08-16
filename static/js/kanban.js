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

        const updateUrl = card.dataset.updateUrl

        fetch(updateUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest' 
        },
        body: JSON.stringify({
            status: newStatus
        })
        })
        .then((response) => {
            if (response.status === 401) {
                window.location.href = `/account/login/?next=${encodeURIComponent(window.location.pathname)}`;
                throw new Error('AUTH_REDIRECT'); 
            }

            if (!response.ok) {
                throw new Error('Status update failed.')
            }
            return response.json()
        })
        .then((data) => {
            if (data.success) {
            window.location.reload()
            } else {
            alert(data.error || 'Status update failed.')
            window.location.reload()
            }
        })
        .catch((error) => {
            if (error.message === 'AUTH_REDIRECT') {
                return;
            }
            alert(error.message)
            window.location.reload()
        })
    }
    })
})

const quickViewModal = document.getElementById('applicationQuickViewModal')

if (quickViewModal) {
    quickViewModal.addEventListener('show.bs.modal', function (event) {
    const button = event.relatedTarget

    const jobTitle = button.getAttribute('data-job-title')
    const companyName = button.getAttribute('data-company-name')
    const status = button.getAttribute('data-status')
    const deadline = button.getAttribute('data-deadline')
    const contactEmail = button.getAttribute('data-contact-email')
    const notes = button.getAttribute('data-notes')
    const detailUrl = button.getAttribute('data-detail-url')
    const editUrl = button.getAttribute('data-edit-url')

    document.getElementById('applicationQuickViewModalLabel').textContent = jobTitle
    document.getElementById('modalCompanyName').textContent = companyName
    document.getElementById('modalStatus').textContent = status
    document.getElementById('modalDeadline').textContent = deadline
    document.getElementById('modalContactEmail').textContent = contactEmail
    document.getElementById('modalNotes').textContent = notes

    document.getElementById('modalDetailLink').setAttribute('href', detailUrl)
    document.getElementById('modalEditLink').setAttribute('href', editUrl)
    })
}

from django import template
from applications.models import JobApplication
register = template.Library()

# mapping of job states to bootstrap classes for the header of the columns
STATUS_HEADER_CLASSES = {
    "interested": "bg-secondary-subtle text-dark",
    "preparing": "bg-info-subtle text-dark",
    "applied": "bg-primary-subtle text-dark",
    "waiting_for_reply": "bg-warning-subtle text-dark",
    "interview_scheduled": "bg-success-subtle text-dark",
    "interview_completed": "bg-success-subtle text-dark",
    "waiting_for_decision": "bg-warning-subtle text-dark",
    "offer_received": "bg-success-subtle text-dark",
    "rejected": "bg-danger-subtle text-dark",
    "withdrawn": "bg-secondary-subtle text-dark",
}

# mapping of job states to bootstrap badge classes
STATUS_BADGE_CLASSES = {
    "interested": "bg-secondary-subtle text-dark border border-secondary-subtle",
    "preparing": "bg-info-subtle text-dark border border-info-subtle",
    "applied": "bg-primary-subtle text-dark border border-primary-subtle",
    "waiting_for_reply": "bg-warning-subtle text-dark border border-warning-subtle",
    "interview_scheduled": "bg-success-subtle text-dark border border-success-subtle",
    "interview_completed": "bg-success-subtle text-dark border border-success-subtle",
    "waiting_for_decision": "bg-warning-subtle text-dark border border-warning-subtle",
    "offer_received": "bg-success-subtle text-dark border border-success-subtle",
    "rejected": "bg-danger-subtle text-dark border border-danger-subtle",
    "withdrawn": "bg-secondary-subtle text-dark border border-secondary-subtle",
    "archived": "bg-dark-subtle text-dark border border-secondary-subtle",
}

@register.filter
def status_header_class(status):
    """
    filter for rendering the status header to the classes as defined above
    """
    return STATUS_HEADER_CLASSES.get(status, "bg-light text-dark")

@register.filter
def status_badge_class(status):
    """
    filter for rendering the status badge as defined above
    """
    return STATUS_BADGE_CLASSES.get(status, "bg-secondary")

@register.filter
def status_label(value):
    """
    render the status as text
    """
    return dict(JobApplication.Status.choices).get(value, value)
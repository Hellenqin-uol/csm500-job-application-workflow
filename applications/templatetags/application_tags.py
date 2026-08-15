from django import template

register = template.Library()


STATUS_HEADER_CLASSES = {
    "interested": "bg-secondary text-white",
    "preparing": "bg-info text-dark",
    "applied": "bg-primary text-white",
    "waiting_for_reply": "bg-warning text-dark",
    "interview_scheduled": "bg-success text-white",
    "interview_completed": "bg-success text-white",
    "waiting_for_decision": "bg-warning text-dark",
    "offer_received": "bg-dark text-white",
    "rejected": "bg-danger text-white",
    "withdrawn": "bg-secondary text-white",
    "archived": "bg-dark text-white",
}

STATUS_BADGE_CLASSES = {
    "interested": "bg-secondary",
    "preparing": "bg-info text-dark",
    "applied": "bg-primary",
    "waiting_for_reply": "bg-warning text-dark",
    "interview_scheduled": "bg-success",
    "interview_completed": "bg-success",
    "waiting_for_decision": "bg-warning text-dark",
    "offer_received": "bg-dark",
    "rejected": "bg-danger",
    "withdrawn": "bg-secondary",
    "archived": "bg-dark",
}

@register.filter
def status_header_class(status):
    return STATUS_HEADER_CLASSES.get(status, "bg-light text-dark")

@register.filter
def status_badge_class(status):
    return STATUS_BADGE_CLASSES.get(status, "bg-secondary")
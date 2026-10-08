"""
Default reminder rules used by the application.

The values are plain strings so they can be reused by management commands
and data migrations without importing current Django model classes.
"""

DEFAULT_REMINDER_RULES = [
    {
        "name": "Review job before deadline",
        "trigger_status": "interested",
        "anchor_type": "application_deadline",
        "offset_direction": "before",
        "offset_days": 3,
        "title_template": "Review {job_title} at {company_name} before the application deadline",
    },
    {
        "name": "Submit application",
        "trigger_status": "preparing",
        "anchor_type": "application_deadline",
        "offset_direction": "before",
        "offset_days": 1,
        "title_template": "Submit application for {job_title} at {company_name}",
    },
    {
        "name": "Send follow-up",
        "trigger_status": "applied",
        "anchor_type": "applied_at",
        "offset_direction": "after",
        "offset_days": 14,
        "title_template": "Send follow-up for {job_title} at {company_name}",
    },
    {
        "name": "Check for reply",
        "trigger_status": "waiting_for_reply",
        "anchor_type": "status_changed_at",
        "offset_direction": "after",
        "offset_days": 10,
        "title_template": "Check for reply from {company_name} regarding {job_title}",
    },
    {
        "name": "Prepare interview",
        "trigger_status": "interview_scheduled",
        "anchor_type": "interview_at",
        "offset_direction": "before",
        "offset_days": 1,
        "title_template": "Prepare interview for {job_title} at {company_name}",
    },
    {
        "name": "Send thank-you/follow-up",
        "trigger_status": "interview_completed",
        "anchor_type": "interview_completed_at",
        "offset_direction": "after",
        "offset_days": 2,
        "title_template": "Send post-interview follow-up for {job_title} at {company_name}",
    },
    {
        "name": "Ask for decision update",
        "trigger_status": "waiting_for_decision",
        "anchor_type": "status_changed_at",
        "offset_direction": "after",
        "offset_days": 7,
        "title_template": "Ask for decision update from {company_name} regarding {job_title}",
    },
    {
        "name": "Review offer",
        "trigger_status": "offer_received",
        "anchor_type": "offer_deadline",
        "offset_direction": "before",
        "offset_days": 2,
        "title_template": "Review offer from {company_name} before the deadline",
    },
]
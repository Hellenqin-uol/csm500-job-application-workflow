from django.db import models
from django.conf import settings

# -------------------------------------------------------------------
# JobApplication holds the applications per User
# -------------------------------------------------------------------
class JobApplication(models.Model):
    class Status(models.TextChoices):
        INTERESTED = "interested", "Interested"
        PREPARING = "preparing", "Preparing"
        APPLIED = "applied", "Applied"
        WAITING_FOR_REPLY = "waiting_for_reply", "Waiting for Reply"
        INTERVIEW_SCHEDULED = "interview_scheduled", "Interview Scheduled"
        INTERVIEW_COMPLETED = "interview_completed", "Interview Completed"
        WAITING_FOR_DECISION = "waiting_for_decision", "Waiting for Decision"
        OFFER_RECEIVED = "offer_received", "Offer Received"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"
        ARCHIVED = "archived", "Archived"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    company_name = models.CharField(max_length=255, verbose_name="Company")
    job_title = models.CharField(max_length=255, verbose_name="Job title")
    job_url = models.URLField(blank=True, verbose_name="Job URL")
    contact_email = models.EmailField(blank=True, verbose_name="Contact email")

    status = models.CharField(max_length=40, choices=Status.choices, default=Status.INTERESTED, verbose_name="Status")

    application_deadline = models.DateField(null=True, blank=True, verbose_name="Application deadline")
    applied_at = models.DateField(null=True, blank=True, verbose_name="Applied at")
    interview_at = models.DateTimeField(null=True, blank=True, verbose_name="Interview at")
    interview_completed_at = models.DateField(null=True, blank=True, verbose_name="Interview completed at")
    offer_deadline = models.DateField(null=True, blank=True, verbose_name="Offer deadline")

    notes = models.TextField(blank=True, verbose_name="Notes")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"

# -------------------------------------------------------------------
# This is the Event log of the job application
# whenever it is moved along the kanban board or
# reminder are generaed, en entry will appear here
# -------------------------------------------------------------------
class ApplicationEvent(models.Model):
    class EventType(models.TextChoices):
        CREATED = "created", "Created"
        STATUS_CHANGED = "status_changed", "Status changed"
        UPDATED = "updated", "Updated"
        ARCHIVED = "archived", "Archived"
        DELETED = "deleted", "Deleted"
        REMINDER_CREATED = "reminder_created", "Reminder created"
        REMINDER_COMPLETED = "reminder_completed", "Reminder completed"

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="events"
    )

    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices
    )

    old_status = models.CharField(max_length=40, blank=True)
    new_status = models.CharField(max_length=40, blank=True)

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_event_type_display()} for {self.application}"

# -------------------------------------------------------------------
# for the reminder logic and UI some columns mark the final
# state of an application, collect them for filtering
# active means reminders on
# -------------------------------------------------------------------    
VISIBLE_BOARD_STATES = (
    JobApplication.Status.INTERESTED,
    JobApplication.Status.PREPARING,
    JobApplication.Status.APPLIED,
    JobApplication.Status.WAITING_FOR_REPLY,
    JobApplication.Status.INTERVIEW_SCHEDULED,
    JobApplication.Status.INTERVIEW_COMPLETED,
    JobApplication.Status.WAITING_FOR_DECISION,
    JobApplication.Status.OFFER_RECEIVED,
    JobApplication.Status.REJECTED,
    JobApplication.Status.WITHDRAWN,
)

NO_REMINDER_STATES = (
    JobApplication.Status.REJECTED,
    JobApplication.Status.WITHDRAWN,
    JobApplication.Status.ARCHIVED,
)
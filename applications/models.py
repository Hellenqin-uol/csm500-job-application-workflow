from django.db import models
from django.conf import settings
from django.utils import timezone
import secrets

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
    job_description = models.TextField(blank=True, verbose_name="Job description")    
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
# Generic Reminder Rules for this Applications
# -------------------------------------------------------------------
class ReminderRule(models.Model):
    class AnchorType(models.TextChoices):
        APPLICATION_DEADLINE = "application_deadline", "Application deadline"
        APPLIED_AT = "applied_at", "Applied at"
        INTERVIEW_AT = "interview_at", "Interview at"
        INTERVIEW_COMPLETED_AT = "interview_completed_at", "Interview completed at"
        OFFER_DEADLINE = "offer_deadline", "Offer deadline"
        STATUS_CHANGED_AT = "status_changed_at", "Status changed at"

    class OffsetDirection(models.TextChoices):
        BEFORE = "before", "Before"
        AFTER = "after", "After"

    name = models.CharField(max_length=255)

    trigger_status = models.CharField(
        max_length=40,
        choices=JobApplication.Status.choices
    )

    anchor_type = models.CharField(
        max_length=50,
        choices=AnchorType.choices
    )

    offset_days = models.PositiveIntegerField(default=0)

    offset_direction = models.CharField(
        max_length=10,
        choices=OffsetDirection.choices,
        default=OffsetDirection.AFTER
    )

    title_template = models.CharField(
        max_length=255,
        help_text="Example: Follow up for {job_title} at {company_name}"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["trigger_status", "anchor_type", "offset_days"]

    def __str__(self):
        return self.name

# -------------------------------------------------------------------
# Generated reminders for applications are stored here.
# They reference to the reminder rules.
# It stores also the status, e.g. open
# -------------------------------------------------------------------
class Reminder(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        DONE = "done", "Done"
        CANCELLED = "cancelled", "Cancelled"

    class Source(models.TextChoices):
        RULE = "rule", "Generated by rule"
        MANUAL = "manual", "Manual"

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="reminders"
    )

    rule = models.ForeignKey(
        ReminderRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_reminders"
    )

    title = models.CharField(max_length=255)
    due_at = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.RULE
    )

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["due_at"]
        indexes = [
            models.Index(fields=["application", "status"]),
            models.Index(fields=["due_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.due_at})"

    @property
    def is_overdue(self):
        return self.status == self.Status.OPEN and self.due_at < timezone.now()

    @property
    def is_due_today(self):
        return (
            self.status == self.Status.OPEN
            and self.due_at.date() == timezone.localdate()
        )

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

# -------------------------------------------------------------------
# Model for Calender Feed enable and disable
# stores the Calender feed token
# ------------------------------------------------------------------- 
def default_calendar_feed_token():
    return secrets.token_urlsafe(32)


class CalendarFeed(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calendar_feed"
    )

    token = models.CharField(
        max_length=128,
        unique=True,
        default=default_calendar_feed_token
    )

    is_enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def reset_token(self):
        self.token = default_calendar_feed_token()
        self.save(update_fields=["token", "updated_at"])

    def disable(self):
        self.is_enabled = False
        self.save(update_fields=["is_enabled", "updated_at"])

    def enable(self):
        if not self.token:
            self.token = default_calendar_feed_token()

        self.is_enabled = True
        self.save(update_fields=["token", "is_enabled", "updated_at"])

    def __str__(self):
        return f"Calendar feed for {self.user}"
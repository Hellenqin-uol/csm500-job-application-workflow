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

    company_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255)
    job_url = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)

    status = models.CharField(max_length=40, choices=Status.choices, default=Status.INTERESTED)

    application_deadline = models.DateField(null=True, blank=True)
    applied_at = models.DateField(null=True, blank=True)
    interview_at = models.DateTimeField(null=True, blank=True)
    interview_completed_at = models.DateField(null=True, blank=True)
    offer_deadline = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"

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
from django.shortcuts import render, redirect, get_object_or_404
from .forms import BootstrapUserCreationForm, JobApplicationForm
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, TemplateView, ListView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db.models import Q
import json
from .models import JobApplication, VISIBLE_BOARD_STATES, ApplicationEvent, Reminder, CalendarFeed
from .services.workflow import change_application_status
from .services.reminders import generate_reminders_for_application
from django.views.generic import DetailView, UpdateView, DeleteView
from datetime import timedelta, timezone as datetime_timezone
from django.utils import timezone
from django.http import Http404, HttpResponse

# User Registration view
class RegisterView(CreateView):
    form_class = BootstrapUserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("applications:kanban")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("applications:kanban")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)

        login(self.request, self.object)

        return response
    
class KanbanBoardView(LoginRequiredMixin, TemplateView):
    template_name = "applications/kanban.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        search_query = self.request.GET.get("q", "").strip()

        applications = self.get_applications_for_board(search_query)
        open_reminders = self.get_open_reminders()

        columns = self.build_kanban_columns(applications=applications, open_reminders=open_reminders)

        context["columns"] = columns
        context["query"] = search_query
        context["result_count"] = len(applications)
        context["has_search"] = bool(search_query)
        context["open_reminders"] = open_reminders
        context["overdue_reminders"] = self.get_overdue_reminders(open_reminders)
        context["archived_count"] = self.get_archived_count()

        return context
    
    def get_applications_for_board(self, search_query):
        applications = JobApplication.objects.filter(
            user=self.request.user,
            status__in=VISIBLE_BOARD_STATES,
        ).order_by("-updated_at")

        if search_query:
            applications = applications.filter(
                Q(company_name__icontains=search_query)
                | Q(job_title__icontains=search_query)
            )

        return list(applications)

    def get_open_reminders(self):
        reminders = Reminder.objects.filter(
            application__user=self.request.user,
            status=Reminder.Status.OPEN,
        ).select_related("application").order_by("due_at")

        return list(reminders)

    def get_overdue_reminders(self, open_reminders):
        now = timezone.now()
        overdue_reminders = []

        for reminder in open_reminders:
            if reminder.due_at < now:
                overdue_reminders.append(reminder)

        return overdue_reminders

    def get_archived_count(self):
        return JobApplication.objects.filter(
            user=self.request.user,
            status=JobApplication.Status.ARCHIVED,
        ).count()

    def build_kanban_columns(self, applications, open_reminders):
        reminders_by_application_id = {}

        for reminder in open_reminders:
            application_id = reminder.application_id

            if application_id not in reminders_by_application_id:
                reminders_by_application_id[application_id] = []

            reminders_by_application_id[application_id].append(reminder)

        columns = []

        for status in VISIBLE_BOARD_STATES:
            cards = []

            for application in applications:
                if application.status != status:
                    continue

                application_reminders = reminders_by_application_id.get(application.id, []                )

                card = self.build_application_card(
                    application=application,
                    reminders=application_reminders,
                )

                cards.append(card)

            column = {
                "status": status,
                "label": JobApplication.Status(status).label,
                "cards": cards,
            }

            columns.append(column)

        return columns

    def build_application_card(self, application, reminders):
        today = timezone.localdate()
        now = timezone.now()

        next_reminder = None
        has_overdue_reminder = False
        has_due_today_reminder = False

        if reminders:
            next_reminder = reminders[0]

        for reminder in reminders:
            if reminder.due_at < now:
                has_overdue_reminder = True

            if reminder.due_at.date() == today:
                has_due_today_reminder = True

        return {
            "application": application,
            "reminders": reminders,
            "next_reminder": next_reminder,
            "has_overdue_reminder": has_overdue_reminder,
            "has_due_today_reminder": has_due_today_reminder,
        }

# create a new job application which is then added to the kanban board
class JobApplicationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = JobApplication
    form_class = JobApplicationForm
    template_name = "applications/job_application_form.html"
    success_url = reverse_lazy("applications:kanban")
    success_message = "Application '%(job_title)s' was created successfully."

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = JobApplication.Status.INTERESTED

        # save application
        response = super().form_valid(form)

        # add to event log
        ApplicationEvent.objects.create(
            application=self.object,
            event_type=ApplicationEvent.EventType.CREATED,
            new_status=self.object.status,
            description=(
                f"Application created with status "
                f"{self.object.get_status_display()}."
            )
        )
        # cretae reminders for application deadline
        generate_reminders_for_application(self.object)

        return response
    
class JobApplicationDetailView(LoginRequiredMixin, DetailView):
    model = JobApplication
    template_name = "applications/job_application_detail.html"
    context_object_name = "application"

    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["open_reminders"] = self.object.reminders.filter(
            status=Reminder.Status.OPEN
        ).order_by("due_at")

        context["closed_reminders"] = self.object.reminders.exclude(
            status=Reminder.Status.OPEN
        ).order_by("-created_at")

        return context
    
class JobApplicationUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = JobApplication
    form_class = JobApplicationForm
    template_name = "applications/job_application_form.html"
    context_object_name = "application"
    success_url = reverse_lazy("applications:kanban")
    success_message = "Application '%(job_title)s' was updated successfully."

    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)
    
    def form_valid(self, form):

        # never do status change here in this view, this is handled by kanban board
        changed_fields = form.changed_data
        other_changed_fields = [
            self.object._meta.get_field(field).verbose_name
            for field in changed_fields if field != "status"
        ]  
        # save form wihtout state change
        response = super().form_valid(form)    

        # log all other field changes
        if other_changed_fields:
            ApplicationEvent.objects.create(
                application=self.object,
                event_type=ApplicationEvent.EventType.UPDATED,
                description=f"Application entry updated: {', '.join(other_changed_fields)}.",
            )        
        return response


class JobApplicationDeleteView(LoginRequiredMixin, DeleteView):
    model = JobApplication
    template_name = "applications/job_application_confirm_delete.html"
    context_object_name = "application"
    success_url = reverse_lazy("applications:kanban")

    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)
    

    def form_valid(self, form):
        application_title = self.object.job_title
        response = super().form_valid(form)

        messages.success(self.request, f"Application '{application_title}' was deleted successfully.")

        return response
    
 # this AJAX method handles the drag and drop actions on the kanban board
class JobApplicationStatusUpdateView(LoginRequiredMixin, View):

    def handle_no_permission(self):
        # return 401 on ajax requests
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(
                {'error': 'permission denied'}, 
                status=401
            )
        # other request return the default redirect logic from django
        return super().handle_no_permission()
    
    def post(self, request, pk):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({
                "success": False,
                "error": "Invalid JSON."
            }, status=400)
        

        new_status = payload.get("status")

        valid_statuses = [
            choice[0] for choice in JobApplication.Status.choices
        ]

        if new_status not in valid_statuses:
            return JsonResponse({
                "success": False,
                "error": "Invalid status."
            }, status=400)

        try:
            application = JobApplication.objects.get(
                pk=pk,
                user=request.user
            )
        except JobApplication.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Application not found."
            }, status=404)

        old_status = application.status

        if old_status != new_status:
            transition_data = {
                    "applied_at": payload.get("applied_at"),
                    "interview_at": payload.get("interview_at"),
                    "interview_completed_at": payload.get("interview_completed_at"),
                    "offer_deadline": payload.get("offer_deadline"),
            }

            try:
                application = change_application_status(
                    application=application,
                    new_status=new_status,
                    transition_data=transition_data,
                )
            except ValidationError as error:
                return JsonResponse(
                    {
                        "success": False,
                        "error": error.messages[0] if error.messages else str(error),
                    },
                    status=400
                )

            messages.success(
                request,
                f"Application '{application.job_title}' moved to {application.get_status_display()}."
            )

        return JsonResponse({
            "success": True,
            "new_status": new_status,
        })

# list of archived applications    
class ArchivedApplicationsView(LoginRequiredMixin, ListView):
    model = JobApplication
    template_name = "applications/archived_applications.html"
    context_object_name = "applications"
    paginate_by = 30

    def get_queryset(self):
        queryset= JobApplication.objects.filter(
            user=self.request.user,
            status=JobApplication.Status.ARCHIVED,
        ).order_by("-updated_at")
    
        query = self.request.GET.get("q", "").strip()

        if query:
            queryset = queryset.filter(
                Q(company_name__icontains=query) |
                Q(job_title__icontains=query)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context

# move application to archive    
class ArchiveJobApplicationView(LoginRequiredMixin, View):
    def post(self, request, pk):
        application = get_object_or_404(
            JobApplication,
            pk=pk,
            user=request.user
        )

        application.status = JobApplication.Status.ARCHIVED
        application.save()

        # stop all reminders
        Reminder.objects.filter(
            application=application,
            status=Reminder.Status.OPEN,
        ).update(
            status=Reminder.Status.CANCELLED
        )

        # log entry in history as archived
        ApplicationEvent.objects.create(
            application=application,
            event_type=ApplicationEvent.EventType.ARCHIVED,
            description=(
                f"Application entry archived."
            )
        )

        messages.success(
            request,
            f"Application '{application.job_title}' was archived."
        )

        return redirect("applications:kanban")

# Unarchive application
class UnarchiveJobApplicationView(LoginRequiredMixin, View):
    def post(self, request, pk):
        application = get_object_or_404(
            JobApplication,
            pk=pk,
            user=request.user,
            status=JobApplication.Status.ARCHIVED,
        )

        old_status = application.status
        application.status = JobApplication.Status.INTERESTED
        application.save()

        ApplicationEvent.objects.create(
            application=application,
            event_type=ApplicationEvent.EventType.STATUS_CHANGED,
            old_status=old_status,
            new_status=JobApplication.Status.INTERESTED,
            description="Application restored from archive."
        )

        messages.success(
            request,
            f"Application '{application.job_title}' was restored to the board. No reminders were generated. Please move the job application along the columns to reactivate reminders."
        )

        return redirect("applications:kanban")

# mark reminder as done
class ReminderCompleteView(LoginRequiredMixin, View):
    # reminders can be marked as complete from detail view and kanban board, redirect to the calling view
    # this is why there are two URLs defined that goes to this same view
    redirect_to = "reminder_list"

    def post(self, request, pk):
        reminder = get_object_or_404(
            Reminder,
            pk=pk,
            application__user=request.user,
            status=Reminder.Status.OPEN,
        )

        reminder.status = Reminder.Status.DONE
        reminder.completed_at = timezone.now()
        reminder.save()

        ApplicationEvent.objects.create(
            application=reminder.application,
            event_type=ApplicationEvent.EventType.REMINDER_COMPLETED,
            description=f"Reminder completed: {reminder.title}",
        )

        messages.success(request, "Reminder marked as done.")


        if self.redirect_to == "application_detail":
            return redirect("applications:application_detail", pk=reminder.application.pk)

        return redirect("applications:kanban")

    
# Views for calender feed
class CalendarFeedSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "applications/calendar_feed_settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        feed = CalendarFeed.objects.filter(user=self.request.user).first()

        feed_url = None

        if feed and feed.is_enabled:
            feed_path = reverse(
                "applications:reminder_calendar_feed",
                kwargs={"token": feed.token}
            )
            feed_url = self.request.build_absolute_uri(feed_path)

        context["feed"] = feed
        context["feed_url"] = feed_url

        return context


class CalendarFeedEnableView(LoginRequiredMixin, View):
    def post(self, request):
        feed, created = CalendarFeed.objects.get_or_create(user=request.user)

        feed.enable()

        if created:
            messages.success(request, "Calendar feed was created.")
        else:
            messages.success(request, "Calendar feed was enabled.")

        return redirect("applications:calendar_feed_settings")


class CalendarFeedResetView(LoginRequiredMixin, View):
    def post(self, request):
        feed, _ = CalendarFeed.objects.get_or_create(user=request.user)

        feed.reset_token()
        feed.is_enabled = True
        feed.save(update_fields=["token", "is_enabled", "updated_at"])

        messages.success(
            request,
            "Calendar feed URL was reset. The previous URL no longer works."
        )

        return redirect("applications:calendar_feed_settings")


class CalendarFeedDisableView(LoginRequiredMixin, View):
    def post(self, request):
        feed = CalendarFeed.objects.filter(user=request.user).first()

        if feed:
            feed.disable()
            messages.success(request, "Calendar feed was disabled.")

        return redirect("applications:calendar_feed_settings")
    
class ReminderCalendarFeedView(View):
    def get(self, request, token):
        try:
            feed = CalendarFeed.objects.select_related("user").get(token=token, is_enabled=True)
        except CalendarFeed.DoesNotExist:
            raise Http404("Calendar feed not found")

        reminders = Reminder.objects.filter(application__user=feed.user, status=Reminder.Status.OPEN).select_related("application").order_by("due_at")

        ics_content = self.build_ics(reminders)

        response = HttpResponse(ics_content, content_type="text/calendar; charset=utf-8")
        response["Content-Disposition"] = 'inline; filename="jobtracker-reminders.ics"'

        return response

    def build_ics(self, reminders):
        now = timezone.now()

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//JobTracker//Reminder Feed//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Job Tracker Reminders",
            "X-WR-CALDESC:Open reminders from Job Tracker",
        ]

        for reminder in reminders:
            lines.extend(self.build_event(reminder, now))

        lines.append("END:VCALENDAR")

        return "\r\n".join(lines) + "\r\n"

    def build_event(self, reminder, now):
        due_at = reminder.due_at

        if timezone.is_naive(due_at):
            due_at = timezone.make_aware(due_at)

        start = due_at
        end = due_at + timedelta(minutes=30)

        uid = f"reminder-{reminder.id}@jobtracker.local"

        summary = self.escape_ics_text(reminder.title)

        description = self.escape_ics_text(
            f"{reminder.application.job_title} at {reminder.application.company_name}"
        )

        return [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{self.format_ics_datetime(now)}",
            f"DTSTART:{self.format_ics_datetime(start)}",
            f"DTEND:{self.format_ics_datetime(end)}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}",
            "END:VEVENT",
        ]

    def format_ics_datetime(self, value):
        value = value.astimezone(datetime_timezone.utc)
        return value.strftime("%Y%m%dT%H%M%SZ")

    def escape_ics_text(self, value):
        if value is None:
            return ""

        return (
            str(value)
            .replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", "\\n")
        )
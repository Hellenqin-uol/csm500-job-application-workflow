from django.urls import path
from . import views

app_name = "applications"

urlpatterns = [
    path("", views.KanbanBoardView.as_view(), name="kanban"),
    path("applications/new/", views.JobApplicationCreateView.as_view(), name="application_create"),
    path("applications/<int:pk>/", views.JobApplicationDetailView.as_view(), name="application_detail"),
    path("applications/<int:pk>/edit/", views.JobApplicationUpdateView.as_view(), name="application_update"),
    path("applications/<int:pk>/delete/", views.JobApplicationDeleteView.as_view(), name="application_delete"),
    path("applications/<int:pk>/update-status/", views.JobApplicationStatusUpdateView.as_view(), name="application_update_status"),
    path("applications/<int:pk>/archive/", views.ArchiveJobApplicationView.as_view(), name="application_archive"),
    path("applications/<int:pk>/unarchive/", views.UnarchiveJobApplicationView.as_view(), name="application_unarchive"),
    path("applications/archived/", views.ArchivedApplicationsView.as_view(), name="archived_applications"),
    path("reminders/<int:pk>/complete/", views.ReminderCompleteView.as_view(), name="reminder_complete"),
    path("calendar/<str:token>/reminders.ics", views.ReminderCalendarFeedView.as_view(), name="reminder_calendar_feed"),
    path("settings/calendar-feed/", views.CalendarFeedSettingsView.as_view(), name="calendar_feed_settings"),
    path("settings/calendar-feed/enable/", views.CalendarFeedEnableView.as_view(), name="calendar_feed_enable"),
    path("settings/calendar-feed/reset/", views.CalendarFeedResetView.as_view(), name="calendar_feed_reset"),
    path("settings/calendar-feed/disable/", views.CalendarFeedDisableView.as_view(), name="calendar_feed_disable"),    
]
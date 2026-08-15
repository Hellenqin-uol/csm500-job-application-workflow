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
    path("applications/archived/", views.ArchivedApplicationsView.as_view(), name="archived_applications"),
]
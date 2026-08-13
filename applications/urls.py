from django.urls import path
from . import views

app_name = "applications"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("applications/new/", views.JobApplicationCreateView.as_view(), name="application_create"),
    path("applications/<int:pk>/", views.JobApplicationDetailView.as_view(), name="application_detail"),
    path("applications/<int:pk>/edit/", views.JobApplicationUpdateView.as_view(), name="application_update"),
    path("applications/<int:pk>/delete/", views.JobApplicationDeleteView.as_view(), name="application_delete"),
]
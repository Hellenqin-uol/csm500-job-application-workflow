from django.urls import path
from . import views

app_name = "applications"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("applications/new/", views.JobApplicationCreateView.as_view(), name="application_create"),
]
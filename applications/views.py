from django.shortcuts import render, redirect
from .forms import BootstrapUserCreationForm, JobApplicationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from .models import JobApplication

# User Registration view
class RegisterView(CreateView):
    form_class = BootstrapUserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("applications:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("applications:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)

        login(self.request, self.object)

        return response

# test view, will be replaced later by kanban board
class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "applications/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["applications"] = JobApplication.objects.filter(
            user=self.request.user
        )

        return context    

# create a new job application which is then added to the kanban board
class JobApplicationCreateView(LoginRequiredMixin, CreateView):
    model = JobApplication
    form_class = JobApplicationForm
    template_name = "applications/job_application_form.html"
    success_url = reverse_lazy("applications:home")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
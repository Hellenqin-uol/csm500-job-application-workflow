from django.shortcuts import render, redirect
from .forms import BootstrapUserCreationForm, JobApplicationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import login
from django.contrib import messages
from .models import JobApplication
from django.views.generic import DetailView, UpdateView, DeleteView

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
class JobApplicationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = JobApplication
    form_class = JobApplicationForm
    template_name = "applications/job_application_form.html"
    success_url = reverse_lazy("applications:home")
    success_message = "Application '%(job_title)s' was created successfully."

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
class JobApplicationDetailView(LoginRequiredMixin, DetailView):
    model = JobApplication
    template_name = "applications/job_application_detail.html"
    context_object_name = "application"

    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)
    
class JobApplicationUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = JobApplication
    form_class = JobApplicationForm
    template_name = "applications/job_application_form.html"
    context_object_name = "application"
    success_url = reverse_lazy("applications:home")
    success_message = "Application '%(job_title)s' was updated successfully."

    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)


class JobApplicationDeleteView(LoginRequiredMixin, DeleteView):
    model = JobApplication
    template_name = "applications/job_application_confirm_delete.html"
    context_object_name = "application"
    success_url = reverse_lazy("applications:home")

    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)
    

    def form_valid(self, form):
        application_title = self.object.job_title
        response = super().form_valid(form)

        messages.success(self.request, f"Application '{application_title}' was deleted successfully.")

        return response
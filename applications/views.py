from django.shortcuts import render, redirect, get_object_or_404
from .forms import BootstrapUserCreationForm, JobApplicationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, ListView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
import json
from .models import JobApplication, VISIBLE_BOARD_STATES
from django.views.generic import DetailView, UpdateView, DeleteView

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

        query = self.request.GET.get("q", "").strip()

        states = list(VISIBLE_BOARD_STATES)

        applications = JobApplication.objects.filter(user=self.request.user, status__in=states)

        if query:
            applications = applications.filter(
                Q(company_name__icontains=query) |
                Q(job_title__icontains=query)
            )
        result_count = applications.count()     

        columns = []

        for status_value in states:
            status_label = JobApplication.Status(status_value).label
            columns.append({
                "status": status_value,
                "label": status_label,
                "applications": applications.filter(status=status_value),
            })

        context["columns"] = columns
        context["query"] = query
        context["has_search"] = bool(query)
        context["result_count"] = result_count

        return context

# create a new job application which is then added to the kanban board
class JobApplicationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = JobApplication
    form_class = JobApplicationForm
    template_name = "applications/job_application_form.html"
    success_url = reverse_lazy("applications:kanban")
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
    success_url = reverse_lazy("applications:kanban")
    success_message = "Application '%(job_title)s' was updated successfully."

    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)


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
            application.status = new_status
            application.save()
            #FIXME later call reminder logic here

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
        #FIMXE stop all reminders later here

        messages.success(
            request,
            f"Application '{application.job_title}' was archived."
        )

        return redirect("applications:kanban")
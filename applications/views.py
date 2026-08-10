from django.shortcuts import render, redirect
from .forms import BootstrapUserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login

# Registration view
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

# dummy test view
class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "applications/home.html"
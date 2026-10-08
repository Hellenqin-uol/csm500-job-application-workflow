from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from applications.models import JobApplication

"""
Django forms for creating and updating job applications and user accounts.
"""

class BootstrapAuthenticationForm(AuthenticationForm):
    """
    Overwrite default Django login form to set the Bootstrap classes on the widgets
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Username",
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Password",
        })
    )

class BootstrapUserCreationForm(UserCreationForm):
    """
    Overwrite default Django registration form to set the Bootstrap classes on the widgets
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Username",
        })
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Password",
        })
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Confirm password",
        })
    )

    class Meta:
        model = User
        fields = ("username", "password1", "password2")

class JobApplicationForm(forms.ModelForm):
    """
    The form for entering new job applications
    """
    class Meta:
        model = JobApplication
        fields = [
            "company_name",
            "job_title",
            "job_url",
            "contact_email",
            "application_deadline",
            "job_description",
            "notes",
        ]

        widgets = {
            "company_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Example Ltd.",
            }),
            "job_title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Frontend Developer",
            }),
            "job_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://example.com/job",
            }),
            "contact_email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "jobs@example.com",
            }),
            "application_deadline": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),      
            "job_description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "Optional: paste the job description here for later reference.",
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Optional notes about this job description",
            }),
        }

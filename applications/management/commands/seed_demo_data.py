from datetime import datetime, time, timedelta
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from applications.models import ApplicationEvent, JobApplication, Reminder, ReminderRule
from applications.services.reminders import generate_reminders_for_application


DEMO_COMPANIES = [
    "DemoTech GmbH",
    "BluePeak Software",
    "Example Analytics Ltd",
    "Northstar Digital",
    "GreenTech Solutions",
    "DataWorks AG",
    "CloudNine Systems",
    "Urban Mobility GmbH",
    "Fintech Labs",
    "HealthSoft SE",
    "Archive Demo AG",
]


DEMO_COMPANIES = [
    "DemoTech GmbH",
    "BluePeak Software",
    "Example Analytics Ltd",
    "Northstar Digital",
    "GreenTech Solutions",
    "DataWorks AG",
    "CloudNine Systems",
    "Urban Mobility GmbH",
    "Fintech Labs",
    "HealthSoft SE",
    "Archive Demo AG",
]


class Command(BaseCommand):
    help = "Create synthetic demo job applications for screenshots and screencasts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            help="Username for which demo data should be created.",
        )

        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing demo applications for the selected user before seeding.",
        )

        parser.add_argument(
            "--no-clear",
            action="store_true",
            help="Do not delete existing demo applications.",
        )

    def handle(self, *args, **options):
        if options["clear"] and options["no_clear"]:
            raise CommandError("Use either --clear or --no-clear, not both.")

        user = self.get_target_user(options["username"])
        clear_existing = self.should_clear_existing(options)

        self.ensure_reminder_rules_exist()

        if clear_existing:
            deleted_count, _ = JobApplication.objects.filter(
                user=user,
                company_name__in=DEMO_COMPANIES,
            ).delete()

            self.stdout.write(
                self.style.WARNING(
                    f"Deleted {deleted_count} existing demo objects."
                )
            )

        self.create_demo_applications(user)

        application_count = JobApplication.objects.filter(
            user=user,
            company_name__in=DEMO_COMPANIES,
        ).count()

        reminder_count = Reminder.objects.filter(
            application__user=user,
            application__company_name__in=DEMO_COMPANIES,
        ).count()

        open_reminder_count = Reminder.objects.filter(
            application__user=user,
            application__company_name__in=DEMO_COMPANIES,
            status=Reminder.Status.OPEN,
        ).count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data created for user '{user.username}'. "
                f"Applications: {application_count}, reminders: {reminder_count}, "
                f"open reminders: {open_reminder_count}."
            )
        )

    def get_target_user(self, username):
        User = get_user_model()

        if username:
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f"User '{username}' does not exist.")

        users = list(User.objects.all().order_by("username"))

        if not users:
            raise CommandError(
                "No users exist. Create a user first using the application or createsuperuser."
            )

        self.stdout.write("")
        self.stdout.write("Select a user for demo data:")
        self.stdout.write("")

        for index, user in enumerate(users, start=1):
            self.stdout.write(f"{index}. {user.username}")

        self.stdout.write("")

        while True:
            selected = input("Enter number: ").strip()

            try:
                selected_index = int(selected)
                if 1 <= selected_index <= len(users):
                    return users[selected_index - 1]
            except ValueError:
                pass

            self.stdout.write(
                self.style.ERROR("Invalid selection. Please enter a valid number.")
            )

    def should_clear_existing(self, options):
        if options["clear"]:
            return True

        if options["no_clear"]:
            return False

        answer = input(
            "Delete existing demo applications for this user before seeding? [y/N]: "
        ).strip().lower()

        return answer in ["y", "yes"]

    def ensure_reminder_rules_exist(self):
        if ReminderRule.objects.exists():
            return

        self.stdout.write(
            self.style.WARNING(
                "No reminder rules found. Running seed_reminder_rules..."
            )
        )

        call_command("seed_reminder_rules")

    def create_demo_applications(self, user):
        today = timezone.localdate()
        now = timezone.now()

        def aware_datetime(days_from_today, hour=10, minute=0):
            target_date = today + timedelta(days=days_from_today)
            naive_dt = datetime.combine(
                target_date,
                time(hour=hour, minute=minute),
            )
            return timezone.make_aware(naive_dt)

        def event_datetime(days_ago, hour=10, minute=0):
            target_date = today - timedelta(days=days_ago)
            naive_dt = datetime.combine(
                target_date,
                time(hour=hour, minute=minute),
            )
            return timezone.make_aware(naive_dt)

        def set_event_timestamp(event, days_ago=None, hour=10, minute=0):
            if days_ago is None:
                return

            ApplicationEvent.objects.filter(pk=event.pk).update(
                created_at=event_datetime(days_ago, hour, minute)
            )

        def create_event(
            application,
            event_type,
            description,
            old_status="",
            new_status="",
            days_ago=None,
            hour=10,
            minute=0,
        ):
            event = ApplicationEvent.objects.create(
                application=application,
                event_type=event_type,
                old_status=old_status,
                new_status=new_status,
                description=description,
            )

            set_event_timestamp(event, days_ago, hour, minute)

            return event

        def create_application(
            company_name,
            job_title,
            status,
            job_url,
            contact_email,
            application_deadline=None,
            applied_at=None,
            interview_at=None,
            interview_completed_at=None,
            offer_deadline=None,
            job_description="",
            notes="",
            created_days_ago=30,
            history=None,
        ):
            application = JobApplication.objects.create(
                user=user,
                company_name=company_name,
                job_title=job_title,
                job_url=job_url,
                contact_email=contact_email,
                status=status,
                application_deadline=application_deadline,
                applied_at=applied_at,
                interview_at=interview_at,
                interview_completed_at=interview_completed_at,
                offer_deadline=offer_deadline,
                job_description=job_description,
                notes=notes,
            )

            create_event(
                application=application,
                event_type=ApplicationEvent.EventType.CREATED,
                description="Demo application created.",
                new_status=JobApplication.Status.INTERESTED,
                days_ago=created_days_ago,
                hour=9,
                minute=15,
            )

            if history:
                for index, item in enumerate(history):
                    default_hour = 9 + (index * 2) % 8
                    default_minute = 15 if index % 2 == 0 else 45

                    create_event(
                        application=application,
                        event_type=ApplicationEvent.EventType.STATUS_CHANGED,
                        old_status=item["old_status"],
                        new_status=item["new_status"],
                        description=(
                            f"Demo status changed from "
                            f"{item['old_status']} to {item['new_status']}."
                        ),
                        days_ago=item["days_ago"],
                        hour=item.get("hour", default_hour),
                        minute=item.get("minute", default_minute),
                    )

            generate_reminders_for_application(application)

            return application

        create_application(
            company_name="DemoTech GmbH",
            job_title="Backend Developer",
            status=JobApplication.Status.APPLIED,
            job_url="https://example.com/jobs/backend-developer",
            contact_email="careers@demotech.example",
            application_deadline=today - timedelta(days=5),
            applied_at=today - timedelta(days=16),
            job_description=(
                "DemoTech GmbH is looking for a Backend Developer to support "
                "the development of internal web applications and APIs. "
                "Responsibilities include designing REST endpoints, working with "
                "relational databases, writing automated tests and collaborating "
                "with frontend developers."
            ),
            notes="Good match for backend and Django experience.",
            created_days_ago=26,
            history=[
                {
                    "old_status": JobApplication.Status.INTERESTED,
                    "new_status": JobApplication.Status.PREPARING,
                    "days_ago": 22,
                    "hour": 10,
                    "minute": 20,
                },
                {
                    "old_status": JobApplication.Status.PREPARING,
                    "new_status": JobApplication.Status.APPLIED,
                    "days_ago": 16,
                    "hour": 14,
                    "minute": 35,
                },
            ],
        )
        # Applied +14 days -> overdue by 2 days.

        create_application(
            company_name="BluePeak Software",
            job_title="Python Developer",
            status=JobApplication.Status.APPLIED,
            job_url="https://example.com/jobs/python-developer",
            contact_email="jobs@bluepeak.example",
            application_deadline=today - timedelta(days=1),
            applied_at=today - timedelta(days=10),
            job_description=(
                "BluePeak Software is looking for a Python Developer to build "
                "backend services and internal tools. The role involves API "
                "development, database work and automated testing."
            ),
            notes="Second applied application for demo board variety.",
            created_days_ago=18,
            history=[
                {
                    "old_status": JobApplication.Status.INTERESTED,
                    "new_status": JobApplication.Status.PREPARING,
                    "days_ago": 14,
                    "hour": 11,
                    "minute": 10,
                },
                {
                    "old_status": JobApplication.Status.PREPARING,
                    "new_status": JobApplication.Status.APPLIED,
                    "days_ago": 10,
                    "hour": 16,
                    "minute": 5,
                },
            ],
        )
        # Applied +14 days -> upcoming in 4 days.

        create_application(
            company_name="Example Analytics Ltd",
            job_title="Data Analyst",
            status=JobApplication.Status.INTERVIEW_SCHEDULED,
            job_url="https://example.com/jobs/data-analyst",
            contact_email="jobs@example-analytics.example",
            application_deadline=today - timedelta(days=3),
            applied_at=today - timedelta(days=10),
            interview_at=aware_datetime(days_from_today=3, hour=11, minute=0),
            job_description=(
                "Example Analytics Ltd is hiring a Data Analyst to transform "
                "business data into actionable insights. The role includes dashboards, "
                "reports, data cleaning and stakeholder communication."
            ),
            notes="Prepare examples of SQL and dashboard projects.",
            created_days_ago=20,
            history=[
                {
                    "old_status": JobApplication.Status.INTERESTED,
                    "new_status": JobApplication.Status.PREPARING,
                    "days_ago": 15,
                    "hour": 9,
                    "minute": 40,
                },
                {
                    "old_status": JobApplication.Status.PREPARING,
                    "new_status": JobApplication.Status.APPLIED,
                    "days_ago": 10,
                    "hour": 13,
                    "minute": 30,
                },
                {
                    "old_status": JobApplication.Status.APPLIED,
                    "new_status": JobApplication.Status.WAITING_FOR_REPLY,
                    "days_ago": 9,
                    "hour": 15,
                    "minute": 20,
                },
                {
                    "old_status": JobApplication.Status.WAITING_FOR_REPLY,
                    "new_status": JobApplication.Status.INTERVIEW_SCHEDULED,
                    "days_ago": 2,
                    "hour": 10,
                    "minute": 5,
                },
            ],
        )
        # Interview -1 day -> upcoming in 2 days.

        create_application(
            company_name="Northstar Digital",
            job_title="Junior Product Manager",
            status=JobApplication.Status.WAITING_FOR_REPLY,
            job_url="https://example.com/jobs/junior-product-manager",
            contact_email="hiring@northstar.example",
            application_deadline=today - timedelta(days=2),
            applied_at=today - timedelta(days=10),
            job_description=(
                "Northstar Digital is seeking a Junior Product Manager to support "
                "requirements gathering, roadmap planning and agile delivery."
            ),
            notes="Waiting for first response.",
            created_days_ago=17,
            history=[
                {
                    "old_status": JobApplication.Status.INTERESTED,
                    "new_status": JobApplication.Status.PREPARING,
                    "days_ago": 14,
                    "hour": 9,
                    "minute": 55,
                },
                {
                    "old_status": JobApplication.Status.PREPARING,
                    "new_status": JobApplication.Status.APPLIED,
                    "days_ago": 10,
                    "hour": 12,
                    "minute": 25,
                },
                {
                    "old_status": JobApplication.Status.APPLIED,
                    "new_status": JobApplication.Status.WAITING_FOR_REPLY,
                    "days_ago": 10,
                    "hour": 15,
                    "minute": 10,
                },
            ],
        )
        # Waiting for Reply +10 days -> due today.

        create_application(
            company_name="GreenTech Solutions",
            job_title="Software Engineer",
            status=JobApplication.Status.PREPARING,
            job_url="https://example.com/jobs/software-engineer",
            contact_email="talent@greentech.example",
            application_deadline=today + timedelta(days=1),
            job_description=(
                "GreenTech Solutions develops software for energy monitoring "
                "and sustainability reporting. The role includes backend services, "
                "APIs and data processing."
            ),
            notes="Need to adapt cover letter.",
            created_days_ago=5,
            history=[
                {
                    "old_status": JobApplication.Status.INTERESTED,
                    "new_status": JobApplication.Status.PREPARING,
                    "days_ago": 2,
                    "hour": 11,
                    "minute": 30,
                },
            ],
        )
        # Preparing deadline -1 day -> due today.

        create_application(
            company_name="DataWorks AG",
            job_title="Business Intelligence Analyst",
            status=JobApplication.Status.INTERESTED,
            job_url="https://example.com/jobs/bi-analyst",
            contact_email="recruiting@dataworks.example",
            application_deadline=today + timedelta(days=6),
            job_description=(
                "DataWorks AG is looking for a BI Analyst to support reporting "
                "and analytics projects using SQL and dashboarding tools."
            ),
            notes="Potentially interesting, check requirements later.",
            created_days_ago=3,
            history=[],
        )
        # Interested deadline -3 days -> upcoming in 3 days.

        create_application(
            company_name="CloudNine Systems",
            job_title="DevOps Engineer",
            status=JobApplication.Status.WAITING_FOR_DECISION,
            job_url="https://example.com/jobs/devops-engineer",
            contact_email="recruitment@cloudnine.example",
            application_deadline=today - timedelta(days=10),
            applied_at=today - timedelta(days=20),
            interview_at=aware_datetime(days_from_today=-5, hour=14, minute=0),
            interview_completed_at=today - timedelta(days=5),
            job_description=(
                "CloudNine Systems is hiring a DevOps Engineer to improve "
                "deployment pipelines, cloud infrastructure and monitoring."
            ),
            notes="Final interview completed. Waiting for decision.",
            created_days_ago=28,
            history=[
                {
                    "old_status": JobApplication.Status.INTERESTED,
                    "new_status": JobApplication.Status.PREPARING,
                    "days_ago": 25,
                    "hour": 10,
                    "minute": 10,
                },
                {
                    "old_status": JobApplication.Status.PREPARING,
                    "new_status": JobApplication.Status.APPLIED,
                    "days_ago": 20,
                    "hour": 13,
                    "minute": 40,
                },
                {
                    "old_status": JobApplication.Status.APPLIED,
                    "new_status": JobApplication.Status.WAITING_FOR_REPLY,
                    "days_ago": 19,
                    "hour": 16,
                    "minute": 20,
                },
                {
                    "old_status": JobApplication.Status.WAITING_FOR_REPLY,
                    "new_status": JobApplication.Status.INTERVIEW_SCHEDULED,
                    "days_ago": 9,
                    "hour": 9,
                    "minute": 25,
                },
                {
                    "old_status": JobApplication.Status.INTERVIEW_SCHEDULED,
                    "new_status": JobApplication.Status.INTERVIEW_COMPLETED,
                    "days_ago": 5,
                    "hour": 15,
                    "minute": 50,
                },
                {
                    "old_status": JobApplication.Status.INTERVIEW_COMPLETED,
                    "new_status": JobApplication.Status.WAITING_FOR_DECISION,
                    "days_ago": 4,
                    "hour": 11,
                    "minute": 5,
                },
            ],
        )
        # Waiting for Decision +7 days -> upcoming in 3 days.

        create_application(
            company_name="Urban Mobility GmbH",
            job_title="UX Designer",
            status=JobApplication.Status.OFFER_RECEIVED,
            job_url="https://example.com/jobs/ux-designer",
            contact_email="people@urbanmobility.example",
            application_deadline=today - timedelta(days=14),
            applied_at=today - timedelta(days=25),
            interview_at=aware_datetime(days_from_today=-8, hour=9, minute=30),
            interview_completed_at=today - timedelta(days=8),
            offer_deadline=today + timedelta(days=5),
            job_description=(
                "Urban Mobility GmbH is seeking a UX Designer to improve user "
                "experiences for mobility applications through research, "
                "prototyping and usability testing."
            ),
            notes="Offer received. Need to review conditions.",
            created_days_ago=35,
            history=[
                {
                    "old_status": JobApplication.Status.INTERESTED,
                    "new_status": JobApplication.Status.PREPARING,
                    "days_ago": 30,
                    "hour": 9,
                    "minute": 20,
                },
                {
                    "old_status": JobApplication.Status.PREPARING,
                    "new_status": JobApplication.Status.APPLIED,
                    "days_ago": 25,
                    "hour": 14,
                    "minute": 10,
                },
                {
                    "old_status": JobApplication.Status.APPLIED,
                    "new_status": JobApplication.Status.WAITING_FOR_REPLY,
                    "days_ago": 24,
                    "hour": 16,
                    "minute": 35,
                },
                {
                    "old_status": JobApplication.Status.WAITING_FOR_REPLY,
                    "new_status": JobApplication.Status.INTERVIEW_SCHEDULED,
                    "days_ago": 12,
                    "hour": 10,
                    "minute": 45,
                },
                {
                    "old_status": JobApplication.Status.INTERVIEW_SCHEDULED,
                    "new_status": JobApplication.Status.INTERVIEW_COMPLETED,
                    "days_ago": 8,
                    "hour": 13,
                    "minute": 15,
                },
                {
                    "old_status": JobApplication.Status.INTERVIEW_COMPLETED,
                    "new_status": JobApplication.Status.WAITING_FOR_DECISION,
                    "days_ago": 7,
                    "hour": 15,
                    "minute": 55,
                },
                {
                    "old_status": JobApplication.Status.WAITING_FOR_DECISION,
                    "new_status": JobApplication.Status.OFFER_RECEIVED,
                    "days_ago": 1,
                    "hour": 11,
                    "minute": 35,
                },
            ],
        )
        # Offer deadline -2 days -> upcoming in 3 days.

        create_application(
            company_name="Fintech Labs",
            job_title="Working Student Software Engineering",
            status=JobApplication.Status.REJECTED,
            job_url="https://example.com/jobs/working-student-software",
            contact_email="students@fintechlabs.example",
            application_deadline=today - timedelta(days=20),
            applied_at=today - timedelta(days=30),
            job_description=(
                "Fintech Labs is looking for a working student to support "
                "software development, testing and documentation in a financial "
                "technology context."
            ),
            notes="Rejected after application review.",
            created_days_ago=38,
            history=[
                {
                    "old_status": JobApplication.Status.INTERESTED,
                    "new_status": JobApplication.Status.PREPARING,
                    "days_ago": 35,
                    "hour": 10,
                    "minute": 0,
                },
                {
                    "old_status": JobApplication.Status.PREPARING,
                    "new_status": JobApplication.Status.APPLIED,
                    "days_ago": 30,
                    "hour": 13,
                    "minute": 20,
                },
                {
                    "old_status": JobApplication.Status.APPLIED,
                    "new_status": JobApplication.Status.REJECTED,
                    "days_ago": 3,
                    "hour": 16,
                    "minute": 10,
                },
            ],
        )

        create_application(
            company_name="HealthSoft SE",
            job_title="Frontend Developer",
            status=JobApplication.Status.WITHDRAWN,
            job_url="https://example.com/jobs/frontend-developer",
            contact_email="careers@healthsoft.example",
            application_deadline=today - timedelta(days=8),
            applied_at=today - timedelta(days=18),
            job_description=(
                "HealthSoft SE develops digital tools for healthcare providers. "
                "The Frontend Developer role includes building accessible and "
                "responsive UI components."
            ),
            notes="Withdrawn because location was not suitable.",
            created_days_ago=25,
            history=[
                {
                    "old_status": JobApplication.Status.INTERESTED,
                    "new_status": JobApplication.Status.PREPARING,
                    "days_ago": 22,
                    "hour": 9,
                    "minute": 45,
                },
                {
                    "old_status": JobApplication.Status.PREPARING,
                    "new_status": JobApplication.Status.APPLIED,
                    "days_ago": 18,
                    "hour": 12,
                    "minute": 15,
                },
                {
                    "old_status": JobApplication.Status.APPLIED,
                    "new_status": JobApplication.Status.WITHDRAWN,
                    "days_ago": 2,
                    "hour": 15,
                    "minute": 5,
                },
            ],
        )

        create_application(
            company_name="Archive Demo AG",
            job_title="QA Engineer",
            status=JobApplication.Status.ARCHIVED,
            job_url="https://example.com/jobs/qa-engineer",
            contact_email="qa-jobs@archivedemo.example",
            application_deadline=today - timedelta(days=45),
            applied_at=today - timedelta(days=60),
            job_description=(
                "Archive Demo AG is hiring a QA Engineer to support manual and "
                "automated testing of web applications."
            ),
            notes="Archived demo application.",
            created_days_ago=70,
            history=[
                {
                    "old_status": JobApplication.Status.INTERESTED,
                    "new_status": JobApplication.Status.PREPARING,
                    "days_ago": 65,
                    "hour": 9,
                    "minute": 30,
                },
                {
                    "old_status": JobApplication.Status.PREPARING,
                    "new_status": JobApplication.Status.APPLIED,
                    "days_ago": 60,
                    "hour": 13,
                    "minute": 15,
                },
                {
                    "old_status": JobApplication.Status.APPLIED,
                    "new_status": JobApplication.Status.REJECTED,
                    "days_ago": 40,
                    "hour": 16,
                    "minute": 40,
                },
                {
                    "old_status": JobApplication.Status.REJECTED,
                    "new_status": JobApplication.Status.ARCHIVED,
                    "days_ago": 20,
                    "hour": 11,
                    "minute": 25,
                },
            ],
        )
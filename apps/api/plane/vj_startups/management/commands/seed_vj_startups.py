import datetime
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from plane.db.models import WorkspaceMember
from plane.vj_startups.models.organization import Wing, OrganizationMemberProfile
from plane.vj_startups.models.reputation import Badge
from plane.vj_startups.models.startup import Startup, StartupMember
from plane.vj_startups.models.event import Event
from plane.vj_startups.services.onboarding_service import OnboardingService

User = get_user_model()

DEFAULT_WINGS = [
    {"name": "Vision", "slug": "vision", "description": "Strategy and direction", "color": "#FF5733"},
    {"name": "Ignition", "slug": "ignition", "description": "Ideation and MVP", "color": "#33FF57"},
    {"name": "Talent", "slug": "talent", "description": "Recruitment and culture", "color": "#3357FF"},
    {"name": "Echo", "slug": "echo", "description": "Marketing and comms", "color": "#F333FF"},
    {"name": "Fuel", "slug": "fuel", "description": "Finance and fundraising", "color": "#FFB833"},
    {"name": "Infra", "slug": "infra", "description": "Engineering and devops", "color": "#33FFF6"},
]

DEFAULT_BADGES = [
    {"name": "First PR", "slug": "first_pr", "description": "Merged your first PR"},
    {"name": "First Customer", "slug": "first_customer", "description": "Acquired the first paying customer"},
    {"name": "First Revenue", "slug": "first_revenue", "description": "Generated first revenue"},
    {"name": "100 Tasks", "slug": "100_tasks", "description": "Completed 100 tasks"},
    {"name": "Top Operator", "slug": "top_operator", "description": "Recognized for operational excellence"},
    {
        "name": "Top Founder",
        "slug": "top_founder",
        "description": "Recognized for founding a successful startup",
    },
    {"name": "Mentor", "slug": "mentor", "description": "Mentored other members"},
    {"name": "Grant Winner", "slug": "grant_winner", "description": "Secured a grant"},
    {
        "name": "Security Champion",
        "slug": "security_champion",
        "description": "Found or fixed major vulnerabilities",
    },
]

# Fixture accounts created ONLY by --with-demo-data. The first one is a
# superuser and workspace admin, so this list is also what lock_demo_accounts
# uses to find and neutralise them on an instance where they already exist.
DEMO_ACCOUNTS = [
    {
        "email": "admin@vnrvjiet.in",
        "username": "admin",
        "first_name": "Admin",
        "last_name": "User",
        "is_staff": True,
        "is_superuser": True,
        "role_in_workspace": 20,  # Admin role
        "profile": {
            "bio": "Instance administrator.",
            "headline": "System Admin",
            "member_stage": "builder",
            "is_club_member": True,
            "role": "Administrator",
            "wing_slug": "infra",
        },
    },
    {
        "email": "member1@vnrvjiet.in",
        "username": "member1",
        "first_name": "Manoj",
        "last_name": "Kumar",
        "is_staff": False,
        "is_superuser": False,
        "role_in_workspace": 15,  # Member role
        "profile": {
            "bio": "Passionate software engineer and tech lead.",
            "headline": "Lead Engineer",
            "member_stage": "builder",
            "is_club_member": True,
            "role": "Infra Lead",
            "wing_slug": "infra",
        },
    },
    {
        "email": "member2@vnrvjiet.in",
        "username": "member2",
        "first_name": "Shita",
        "last_name": "Gupta",
        "is_staff": False,
        "is_superuser": False,
        "role_in_workspace": 15,  # Member role
        "profile": {
            "bio": "Talent acquisition lead and community manager.",
            "headline": "Community Head",
            "member_stage": "builder",
            "is_club_member": True,
            "role": "Ecosystem Manager",
            "wing_slug": "talent",
        },
    },
    {
        "email": "founder1@vnrvjiet.in",
        "username": "founder1",
        "first_name": "Rohan",
        "last_name": "Sharma",
        "is_staff": False,
        "is_superuser": False,
        "role_in_workspace": 15,  # Member role
        "profile": {
            "bio": "Serial entrepreneur and innovator.",
            "headline": "CEO @ Bandiwala",
            "member_stage": "founder",
            "is_club_member": True,
            "role": "Founder",
            "wing_slug": "ignition",
        },
    },
    {
        "email": "student1@vnrvjiet.in",
        "username": "student1",
        "first_name": "Ananya",
        "last_name": "Reddy",
        "is_staff": False,
        "is_superuser": False,
        "role_in_workspace": 10,  # Guest role
        "profile": {
            "bio": "Student explorer finding new validation ideas.",
            "headline": "Student Explorer",
            "member_stage": "explorer",
            "is_club_member": False,
            "role": "Explorer",
            "wing_slug": "vision",
        },
    },
]
DEMO_ACCOUNT_EMAILS = [account["email"] for account in DEMO_ACCOUNTS]

DEMO_STARTUPS = [
    {
        "name": "BandiWala",
        "slug": "bandiwala",
        "description": (
            "BandiWala is a micro-commerce platform for street vendors, "
            "allowing them to broadcast local inventory in real-time."
        ),
        "tagline": "Empowering street vendors",
        "trl_stage": 4,  # MVP
        "industry": "Ecommerce",
        "status": "active",
        "team_size": 3,
        "funding_raised": 5000.00,
        "website": "https://bandiwala.vjstartup.com",
        "founders": ["founder1@vnrvjiet.in"],
    },
    {
        "name": "VJStartups Hub",
        "slug": "vjstartups-hub",
        "description": "The central collaboration portal for VJ Startups OS community members.",
        "tagline": "Ecosystem coordination software",
        "trl_stage": 6,  # Launch
        "industry": "Software",
        "status": "active",
        "team_size": 5,
        "funding_raised": 15000.00,
        "website": "https://hub.vjstartup.com",
        "founders": ["member1@vnrvjiet.in", "founder1@vnrvjiet.in"],
    },
]

DEMO_EVENTS = [
    {"title": "Ecosystem Pitching Day", "wing_slug": "vision", "status": "upcoming", "days_offset": 7},
    {
        "title": "Ideation Brainstorm & MVP Workshop",
        "wing_slug": "ignition",
        "status": "in_progress",
        "days_offset": 0,
    },
    {"title": "Infra Deployment Sprint", "wing_slug": "infra", "status": "completed", "days_offset": -14},
]


class Command(BaseCommand):
    help = (
        "Seed the reference data VJ Startups OS needs to run: the six wings and the badge catalogue "
        "(idempotent - existing rows are left exactly as they are). Runs on every deploy. "
        "Fake demo users, startups and events are created only with --with-demo-data, which is meant "
        "for local development."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-demo-data",
            action="store_true",
            help=(
                "Also create fixture users (including a superuser), startups and events. "
                "For local development only - refused unless DEBUG is on."
            ),
        )
        parser.add_argument(
            "--demo-password",
            help="Password for the demo accounts. If omitted a random one is generated and printed once.",
        )
        parser.add_argument(
            "--allow-in-production",
            action="store_true",
            help="Let --with-demo-data run with DEBUG off. Do not use on a real instance.",
        )

    def handle(self, *args, **options):
        with_demo = options["with_demo_data"]
        if with_demo and not settings.DEBUG and not options["allow_in_production"]:
            raise CommandError(
                "Refusing to create demo accounts (one is a superuser) while DEBUG is off. "
                "Pass --allow-in-production only if you really mean it."
            )

        self.stdout.write("Starting VJ Startups seeding...")
        self._seed_reference_data()
        if with_demo:
            self._seed_demo_data(options.get("demo_password"))
        self._backfill_wing_projects()
        self.stdout.write(self.style.SUCCESS("VJ Startups seeding finished."))

    def _seed_reference_data(self):
        # get_or_create, not update_or_create: an admin may have edited a wing's
        # description or colour, and a deploy must never overwrite that.
        with transaction.atomic():
            for wing_data in DEFAULT_WINGS:
                Wing.objects.get_or_create(slug=wing_data["slug"], defaults=wing_data)
            for badge_data in DEFAULT_BADGES:
                Badge.objects.get_or_create(slug=badge_data["slug"], defaults=badge_data)
        self.stdout.write(self.style.SUCCESS("Wings and badges are in place."))

    def _seed_demo_data(self, password):
        generated = password is None
        password = password or secrets.token_urlsafe(16)

        # Create the owner user first to resolve foreign key constraints.
        admin_data = DEMO_ACCOUNTS[0]
        admin_user, _ = User.objects.get_or_create(email=admin_data["email"])
        self._apply_demo_user(admin_user, admin_data, password)

        workspace = OnboardingService.get_or_create_global_workspace()
        OnboardingService.get_or_create_common_project(workspace)
        self.stdout.write(self.style.SUCCESS("Global Workspace and Projects initialized."))

        for user_data in DEMO_ACCOUNTS:
            user, _ = User.objects.get_or_create(email=user_data["email"])
            self._apply_demo_user(user, user_data, password)

            WorkspaceMember.objects.get_or_create(
                workspace=workspace, member=user, defaults={"role": user_data["role_in_workspace"]}
            )

            prof = user_data["profile"]
            OrganizationMemberProfile.objects.update_or_create(
                user=user,
                defaults={
                    "bio": prof["bio"],
                    "headline": prof["headline"],
                    "member_stage": prof["member_stage"],
                    "is_club_member": prof["is_club_member"],
                    "role": prof["role"],
                    "wing": Wing.objects.filter(slug=prof["wing_slug"]).first(),
                },
            )
        self.stdout.write(self.style.SUCCESS("Demo users and profiles seeded."))
        if generated:
            self.stdout.write(f"Demo account password (shown once, not stored anywhere): {password}")

        for startup_data in DEMO_STARTUPS:
            data = dict(startup_data)
            founders = data.pop("founders")
            startup, _ = Startup.objects.update_or_create(slug=data["slug"], defaults=data)
            OnboardingService.auto_provision_startup(startup)

            for email in founders:
                founder_user = User.objects.filter(email=email).first()
                profile = OrganizationMemberProfile.objects.filter(user=founder_user).first() if founder_user else None
                if profile:
                    StartupMember.objects.update_or_create(
                        startup=startup,
                        member=profile,
                        defaults={"role": "Co-Founder", "equity_notes": "Standard vesting agreement"},
                    )
        self.stdout.write(self.style.SUCCESS("Demo startups and founders mapped."))

        for ev in DEMO_EVENTS:
            wing = Wing.objects.filter(slug=ev["wing_slug"]).first()
            if wing:
                Event.objects.update_or_create(
                    title=ev["title"],
                    wing=wing,
                    defaults={
                        "status": ev["status"],
                        "scheduled_at": timezone.now() + datetime.timedelta(days=ev["days_offset"]),
                    },
                )
        self.stdout.write(self.style.SUCCESS("Demo events seeded."))

    @staticmethod
    def _apply_demo_user(user, data, password):
        user.username = data["username"]
        user.first_name = data["first_name"]
        user.last_name = data["last_name"]
        user.is_staff = data["is_staff"]
        user.is_superuser = data["is_superuser"]
        user.is_active = True
        user.is_password_autoset = False
        user.set_password(password)
        user.save()

    def _backfill_wing_projects(self):
        # auto_provision_wing/auto_provision_startup only run on first creation
        # (post_save, created=True), so a Wing/Startup created before the global
        # workspace existed never got a project and cannot self-heal on a later
        # save(). Catch those up - but only once the workspace exists; creating
        # it here would pick an arbitrary owner on a fresh instance.
        from plane.vj_startups.models.extension import VJProjectExtension

        if OnboardingService.get_global_workspace() is None:
            self.stdout.write("No global workspace yet - wing projects are created when the first member joins.")
            return

        for wing in Wing.objects.all():
            if not VJProjectExtension.objects.filter(wing=wing).exists():
                OnboardingService.auto_provision_wing(wing)
        for startup in Startup.objects.all():
            if not VJProjectExtension.objects.filter(startup=startup).exists():
                OnboardingService.auto_provision_startup(startup)
        self.stdout.write(self.style.SUCCESS("Backfilled missing wing/startup projects."))

        # Members whose profile was saved before their wing's project existed never
        # got added to it (the profile save signal ran too early to find a project).
        # Re-sync now that every wing definitely has one.
        for profile in OrganizationMemberProfile.objects.filter(wing__isnull=False).select_related("wing", "user"):
            OnboardingService.onboard_user_to_wing(profile.user, profile.wing)
        self.stdout.write(self.style.SUCCESS("Backfilled wing project memberships."))

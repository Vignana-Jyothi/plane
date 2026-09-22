from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
import datetime

from plane.db.models import WorkspaceMember
from plane.vj_startups.models.organization import Wing, OrganizationMemberProfile
from plane.vj_startups.models.reputation import Badge
from plane.vj_startups.models.startup import Startup, StartupMember
from plane.vj_startups.models.event import Event
from plane.vj_startups.services.onboarding_service import OnboardingService

User = get_user_model()

class Command(BaseCommand):
    help = "Seed database with default VJ Startups OS data (users, wings, badges, startups, members, and events)"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting VJ Startups database seeding...")

        # 1. Seed Wings
        default_wings = [
            {"name": "Vision", "slug": "vision", "description": "Strategy and direction", "color": "#FF5733"},
            {"name": "Ignition", "slug": "ignition", "description": "Ideation and MVP", "color": "#33FF57"},
            {"name": "Talent", "slug": "talent", "description": "Recruitment and culture", "color": "#3357FF"},
            {"name": "Echo", "slug": "echo", "description": "Marketing and comms", "color": "#F333FF"},
            {"name": "Fuel", "slug": "fuel", "description": "Finance and fundraising", "color": "#FFB833"},
            {"name": "Infra", "slug": "infra", "description": "Engineering and devops", "color": "#33FFF6"},
        ]

        with transaction.atomic():
            for wing_data in default_wings:
                Wing.objects.update_or_create(
                    slug=wing_data["slug"],
                    defaults=wing_data
                )
        self.stdout.write(self.style.SUCCESS("Wings seeded successfully."))

        # 2. Seed Badges
        default_badges = [
            {"name": "First PR", "slug": "first_pr", "description": "Merged your first PR"},
            {"name": "First Customer", "slug": "first_customer", "description": "Acquired the first paying customer"},
            {"name": "First Revenue", "slug": "first_revenue", "description": "Generated first revenue"},
            {"name": "100 Tasks", "slug": "100_tasks", "description": "Completed 100 tasks"},
            {"name": "Top Operator", "slug": "top_operator", "description": "Recognized for operational excellence"},
            {"name": "Top Founder", "slug": "top_founder", "description": "Recognized for founding a successful startup"},
            {"name": "Mentor", "slug": "mentor", "description": "Mentored other members"},
            {"name": "Grant Winner", "slug": "grant_winner", "description": "Secured a grant"},
            {"name": "Security Champion", "slug": "security_champion", "description": "Found or fixed major vulnerabilities"},
        ]

        with transaction.atomic():
            for badge_data in default_badges:
                Badge.objects.update_or_create(
                    slug=badge_data["slug"],
                    defaults=badge_data
                )
        self.stdout.write(self.style.SUCCESS("Badges seeded successfully."))

        # 3. Provision Global Workspace & General Project
        # 3. Seed Users definition
        users_to_seed = [
            {
                "email": "admin@vnrvjiet.in",
                "username": "admin",
                "first_name": "Admin",
                "last_name": "User",
                "is_staff": True,
                "is_superuser": True,
                "role_in_workspace": 20, # Admin role
                "profile": {
                    "bio": "Instance administrator.",
                    "headline": "System Admin",
                    "member_stage": "builder",
                    "is_club_member": True,
                    "role": "Administrator",
                    "wing_slug": "infra"
                }
            },
            {
                "email": "member1@vnrvjiet.in",
                "username": "member1",
                "first_name": "Manoj",
                "last_name": "Kumar",
                "is_staff": False,
                "is_superuser": False,
                "role_in_workspace": 15, # Member role
                "profile": {
                    "bio": "Passionate software engineer and tech lead.",
                    "headline": "Lead Engineer",
                    "member_stage": "builder",
                    "is_club_member": True,
                    "role": "Infra Lead",
                    "wing_slug": "infra"
                }
            },
            {
                "email": "member2@vnrvjiet.in",
                "username": "member2",
                "first_name": "Shita",
                "last_name": "Gupta",
                "is_staff": False,
                "is_superuser": False,
                "role_in_workspace": 15, # Member role
                "profile": {
                    "bio": "Talent acquisition lead and community manager.",
                    "headline": "Community Head",
                    "member_stage": "builder",
                    "is_club_member": True,
                    "role": "Ecosystem Manager",
                    "wing_slug": "talent"
                }
            },
            {
                "email": "founder1@vnrvjiet.in",
                "username": "founder1",
                "first_name": "Rohan",
                "last_name": "Sharma",
                "is_staff": False,
                "is_superuser": False,
                "role_in_workspace": 15, # Member role
                "profile": {
                    "bio": "Serial entrepreneur and innovator.",
                    "headline": "CEO @ Bandiwala",
                    "member_stage": "founder",
                    "is_club_member": True,
                    "role": "Founder",
                    "wing_slug": "ignition"
                }
            },
            {
                "email": "student1@vnrvjiet.in",
                "username": "student1",
                "first_name": "Ananya",
                "last_name": "Reddy",
                "is_staff": False,
                "is_superuser": False,
                "role_in_workspace": 10, # Guest role
                "profile": {
                    "bio": "Student explorer finding new validation ideas.",
                    "headline": "Student Explorer",
                    "member_stage": "explorer",
                    "is_club_member": False,
                    "role": "Explorer",
                    "wing_slug": "vision"
                }
            }
        ]

        # 4. Create Owner User first to resolve foreign key constraints
        admin_data = users_to_seed[0]
        admin_user, _ = User.objects.get_or_create(email=admin_data["email"])
        admin_user.username = admin_data["username"]
        admin_user.first_name = admin_data["first_name"]
        admin_user.last_name = admin_data["last_name"]
        admin_user.is_staff = admin_data["is_staff"]
        admin_user.is_superuser = admin_data["is_superuser"]
        admin_user.is_active = True
        admin_user.is_password_autoset = False
        admin_user.set_password("vjstartups123")
        admin_user.save()

        # 5. Provision Global Workspace & General Project
        workspace = OnboardingService.get_or_create_global_workspace()
        OnboardingService.get_or_create_common_project(workspace)
        self.stdout.write(self.style.SUCCESS("Global Workspace and Projects initialized."))

        # 6. Seed All Users and Workspace Memberships
        for user_data in users_to_seed:
            user, created = User.objects.get_or_create(email=user_data["email"])
            user.username = user_data["username"]
            user.first_name = user_data["first_name"]
            user.last_name = user_data["last_name"]
            user.is_staff = user_data["is_staff"]
            user.is_superuser = user_data["is_superuser"]
            user.is_active = True
            user.is_password_autoset = False
            user.set_password("vjstartups123")
            user.save()

            # Add to Workspace
            WorkspaceMember.objects.get_or_create(
                workspace=workspace,
                member=user,
                defaults={"role": user_data["role_in_workspace"]}
            )

            # Create Profile
            prof = user_data["profile"]
            wing = Wing.objects.filter(slug=prof["wing_slug"]).first()
            OrganizationMemberProfile.objects.update_or_create(
                user=user,
                defaults={
                    "bio": prof["bio"],
                    "headline": prof["headline"],
                    "member_stage": prof["member_stage"],
                    "is_club_member": prof["is_club_member"],
                    "role": prof["role"],
                    "wing": wing
                }
            )
        self.stdout.write(self.style.SUCCESS("Users and Profiles seeded successfully."))

        # 5. Seed Startups
        startups_to_seed = [
            {
                "name": "BandiWala",
                "slug": "bandiwala",
                "description": "BandiWala is a micro-commerce platform for street vendors, allowing them to broadcast local inventory in real-time.",
                "tagline": "Empowering street vendors",
                "trl_stage": 4, # MVP
                "industry": "Ecommerce",
                "status": "active",
                "team_size": 3,
                "funding_raised": 5000.00,
                "website": "https://bandiwala.vjstartup.com",
                "founders": ["founder1@vnrvjiet.in"]
            },
            {
                "name": "VJStartups Hub",
                "slug": "vjstartups-hub",
                "description": "The central collaboration portal for VJ Startups OS community members.",
                "tagline": "Ecosystem coordination software",
                "trl_stage": 6, # Launch
                "industry": "Software",
                "status": "active",
                "team_size": 5,
                "funding_raised": 15000.00,
                "website": "https://hub.vjstartup.com",
                "founders": ["member1@vnrvjiet.in", "founder1@vnrvjiet.in"]
            }
        ]

        for startup_data in startups_to_seed:
            founders = startup_data.pop("founders")
            startup, created = Startup.objects.update_or_create(
                slug=startup_data["slug"],
                defaults=startup_data
            )
            
            # Auto-provision Plane Project
            OnboardingService.auto_provision_startup(startup)

            # Map Founders in StartupMember
            for email in founders:
                founder_user = User.objects.filter(email=email).first()
                if founder_user:
                    profile = OrganizationMemberProfile.objects.filter(user=founder_user).first()
                    if profile:
                        StartupMember.objects.update_or_create(
                            startup=startup,
                            member=profile,
                            defaults={
                                "role": "Co-Founder",
                                "equity_notes": "Standard vesting agreement"
                            }
                        )
        self.stdout.write(self.style.SUCCESS("Startups and founders mapped successfully."))

        # 6. Seed Wing Activities/Events
        events_to_seed = [
            {
                "title": "Ecosystem Pitching Day",
                "wing_slug": "vision",
                "status": "upcoming",
                "days_offset": 7
            },
            {
                "title": "Ideation Brainstorm & MVP Workshop",
                "wing_slug": "ignition",
                "status": "in_progress",
                "days_offset": 0
            },
            {
                "title": "Infra Deployment Sprint",
                "wing_slug": "infra",
                "status": "completed",
                "days_offset": -14
            }
        ]

        for ev in events_to_seed:
            wing = Wing.objects.filter(slug=ev["wing_slug"]).first()
            if wing:
                Event.objects.update_or_create(
                    title=ev["title"],
                    wing=wing,
                    defaults={
                        "status": ev["status"],
                        "scheduled_at": timezone.now() + datetime.timedelta(days=ev["days_offset"])
                    }
                )
        self.stdout.write(self.style.SUCCESS("Wing events seeded successfully."))

        # Backfill: auto_provision_wing/auto_provision_startup only run on first
        # creation (via post_save signal, created=True). Any Wing/Startup that was
        # created before the global workspace existed - which used to always be the
        # case here, since this command seeded Wings before the workspace - never
        # got a project and can't self-heal on a later save(). Catch those up.
        from plane.vj_startups.models.extension import VJProjectExtension

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

        self.stdout.write(self.style.SUCCESS("All VJ Startups OS data seeded successfully!"))

from django.core.management.base import BaseCommand
from plane.vj_startups.models.organization import Wing
from plane.vj_startups.models.reputation import Badge
from django.db import transaction

class Command(BaseCommand):
    help = "Seed database with default VJ Startups OS data (wings, badges)"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding VJ Startups data...")

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

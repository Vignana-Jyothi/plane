from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from plane.db.models import Project
from plane.vj_startups.services.onboarding_service import OnboardingService


class Command(BaseCommand):
    help = (
        "Backfill module_view/cycle_view/issue_views_view=True on VJ Startups projects "
        "(the COMMON project, plus every startup/wing project) that were auto-provisioned "
        "before OnboardingService started setting those flags. New projects already get "
        "them at creation time via OnboardingService - this only fixes existing rows."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show which projects would be updated without writing anything.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        workspace = OnboardingService.get_global_workspace()
        if not workspace:
            self.stdout.write(self.style.WARNING(
                f"No workspace with slug '{OnboardingService.WORKSPACE_SLUG}' found - nothing to backfill."
            ))
            return

        projects = Project.objects.filter(
            Q(vj_extension__isnull=False) | Q(workspace=workspace, identifier="COMMON")
        ).filter(
            Q(module_view=False) | Q(cycle_view=False) | Q(issue_views_view=False)
        ).distinct()

        count = projects.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS(
                "Nothing to backfill - all VJ Startups projects already have the flags set."
            ))
            return

        self.stdout.write(f"{count} project(s) missing Cycles/Modules/Views:")
        for project in projects:
            self.stdout.write(f"  - {project.name} ({project.identifier}, id={project.id})")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run - no changes written."))
            return

        with transaction.atomic():
            updated = projects.update(module_view=True, cycle_view=True, issue_views_view=True)

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} project(s)."))

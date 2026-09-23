from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from plane.db.models import Project, ProjectIdentifier
from plane.vj_startups.services.onboarding_service import OnboardingService


class Command(BaseCommand):
    help = (
        "Backfill ProjectIdentifier rows for VJ Startups projects (the COMMON project, plus "
        "every startup/wing project) created before OnboardingService started reserving them. "
        "Project.identifier itself has no database-level uniqueness constraint - real "
        "uniqueness is enforced only via ProjectIdentifier's UniqueConstraint on (name, "
        "workspace), which Plane's own project-creation serializer creates for every project "
        "but OnboardingService's direct Project.objects.create() calls never did. Without this "
        "row, a project created through the normal UI could reuse an identifier already used "
        "by a VJ Startups project (e.g. 'COMMON') and silently succeed. New projects already "
        "get this at creation time - this only fixes existing rows."
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
        ).exclude(
            id__in=ProjectIdentifier.objects.filter(workspace=workspace).values_list("project_id", flat=True)
        ).distinct()

        count = projects.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("Nothing to backfill - every VJ Startups project already has a ProjectIdentifier."))
            return

        self.stdout.write(f"{count} project(s) with no ProjectIdentifier:")
        for project in projects:
            self.stdout.write(f"  - {project.name} ({project.identifier}, id={project.id})")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run - no changes written."))
            return

        with transaction.atomic():
            for project in projects:
                OnboardingService._reserve_project_identifier(project)

        self.stdout.write(self.style.SUCCESS(f"Reserved ProjectIdentifier rows for {count} project(s)."))

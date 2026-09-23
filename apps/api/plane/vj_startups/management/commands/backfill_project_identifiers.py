from django.core.management.base import BaseCommand
from django.db import transaction

from plane.db.models import Project, ProjectIdentifier


class Command(BaseCommand):
    help = (
        "Backfill ProjectIdentifier rows for ANY project in the instance missing one. "
        "Project.identifier itself has no database-level uniqueness constraint - real "
        "uniqueness is enforced only via ProjectIdentifier's UniqueConstraint on (name, "
        "workspace). Plane's own internal-app project-creation serializer "
        "(app/serializers/project.py's ProjectSerializer) creates this row correctly, but "
        "two other paths didn't: VJ Startups' OnboardingService (direct "
        "Project.objects.create() calls, now fixed) and Plane's own public API v1 "
        "(api/serializers/project.py's ProjectCreateSerializer, now fixed too - it already "
        "checked ProjectIdentifier for uniqueness on create but never actually wrote the row "
        "afterward). Without this row, a project created through either of those bypassed "
        "paths could reuse an identifier already in use by another project in the same "
        "workspace and silently succeed. New projects already get this at creation time - "
        "this only fixes existing rows."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show which projects would be updated without writing anything.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        projects = Project.objects.filter(deleted_at__isnull=True).exclude(
            id__in=ProjectIdentifier.objects.values_list("project_id", flat=True)
        ).select_related("workspace")

        count = projects.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("Nothing to backfill - every project already has a ProjectIdentifier."))
            return

        self.stdout.write(f"{count} project(s) with no ProjectIdentifier:")
        for project in projects:
            self.stdout.write(f"  - {project.workspace.slug}/{project.name} ({project.identifier}, id={project.id})")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run - no changes written."))
            return

        with transaction.atomic():
            for project in projects:
                ProjectIdentifier.objects.get_or_create(
                    name=project.identifier,
                    workspace=project.workspace,
                    defaults={"project": project},
                )

        self.stdout.write(self.style.SUCCESS(f"Reserved ProjectIdentifier rows for {count} project(s)."))

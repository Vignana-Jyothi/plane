from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from plane.db.models import Project, State, DEFAULT_STATES
from plane.vj_startups.services.onboarding_service import OnboardingService


class Command(BaseCommand):
    help = (
        "Backfill DEFAULT_STATES on VJ Startups projects (the COMMON project, plus every "
        "startup/wing project) created before OnboardingService started seeding them - "
        "every project created via Project.objects.create() (not Plane's own project-creation "
        "API) ended up with zero states in every group (Backlog/Unstarted/Started/Completed/"
        "Cancelled), since that seeding lives in the API view layer, not a model signal. "
        "New projects already get this at creation time - this only fixes existing rows."
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
            id__in=State.objects.filter(project__workspace=workspace).values_list("project_id", flat=True)
        ).distinct()

        count = projects.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("Nothing to backfill - every VJ Startups project already has states."))
            return

        self.stdout.write(f"{count} project(s) with zero states:")
        for project in projects:
            self.stdout.write(f"  - {project.name} ({project.identifier}, id={project.id})")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run - no changes written."))
            return

        with transaction.atomic():
            for project in projects:
                State.objects.bulk_create(
                    [
                        State(
                            name=state["name"],
                            color=state["color"],
                            project=project,
                            sequence=state["sequence"],
                            workspace=project.workspace,
                            group=state["group"],
                            default=state.get("default", False),
                        )
                        for state in DEFAULT_STATES
                    ]
                )

        self.stdout.write(self.style.SUCCESS(f"Seeded default states for {count} project(s)."))

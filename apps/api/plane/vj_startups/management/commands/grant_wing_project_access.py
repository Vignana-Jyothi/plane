from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from plane.db.models import Project, ProjectMember, Workspace, WorkspaceMember
from plane.vj_startups.models.organization import OrganizationMemberProfile, Wing


class Command(BaseCommand):
    help = (
        "Add every member of a Wing as a Member (role=15) on every project in a "
        "workspace. Idempotent - only creates the ProjectMember rows that are "
        "missing, never touches or removes an existing membership (so it's safe "
        "to re-run, e.g. after new Wing members join or new projects are "
        "created). Wing membership itself lives in "
        "OrganizationMemberProfile.wing, a VJ Startups model - it has no "
        "relation to Plane's own ProjectMember/WorkspaceMember rows until this "
        "command (or equivalent) links them."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--wing",
            required=True,
            help="Wing slug or exact name (e.g. 'vision-wing' or 'Vision Wing').",
        )
        parser.add_argument(
            "--workspace",
            required=True,
            help="Workspace slug whose projects should be granted (e.g. 'vj-startups').",
        )
        parser.add_argument(
            "--role",
            type=int,
            default=15,
            choices=[5, 15, 20],
            help="Project role to grant: 5=Guest, 15=Member (default), 20=Admin.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without writing anything.",
        )

    def handle(self, *args, **options):
        wing_key = options["wing"]
        workspace_slug = options["workspace"]
        role = options["role"]
        dry_run = options["dry_run"]

        wing = Wing.objects.filter(Q(slug=wing_key) | Q(name__iexact=wing_key)).first()
        if wing is None:
            raise CommandError(
                f"No Wing found matching slug or name '{wing_key}'. "
                f"Available: {', '.join(Wing.objects.values_list('slug', flat=True)) or '(none)'}"
            )

        workspace = Workspace.objects.filter(slug=workspace_slug).first()
        if workspace is None:
            raise CommandError(
                f"No workspace found with slug '{workspace_slug}'. "
                f"Available: {', '.join(Workspace.objects.values_list('slug', flat=True)) or '(none)'}"
            )

        members = list(
            OrganizationMemberProfile.objects.filter(wing=wing, deleted_at__isnull=True)
            .select_related("user")
        )
        if not members:
            self.stdout.write(self.style.WARNING(f"Wing '{wing.name}' has no members - nothing to do."))
            return

        projects = list(Project.objects.filter(workspace=workspace, deleted_at__isnull=True))
        if not projects:
            self.stdout.write(self.style.WARNING(f"Workspace '{workspace.slug}' has no projects - nothing to do."))
            return

        existing_pairs = set(
            ProjectMember.objects.filter(
                project__in=projects, member__in=[m.user_id for m in members], is_active=True
            ).values_list("project_id", "member_id")
        )

        to_create = [
            (project, member)
            for project in projects
            for member in members
            if (project.id, member.user_id) not in existing_pairs
        ]

        self.stdout.write(
            f"Wing '{wing.name}': {len(members)} member(s), workspace '{workspace.slug}': "
            f"{len(projects)} project(s), {len(existing_pairs)} membership(s) already exist, "
            f"{len(to_create)} to create."
        )
        for project, member in to_create:
            self.stdout.write(f"  + {member.user.email} -> {project.name}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run - no changes written."))
            return

        if not to_create:
            self.stdout.write(
                self.style.SUCCESS("Nothing to do - every wing member already has access to every project.")
            )
            return

        # Plane's own project-invite-acceptance flow (app/views/project/invite.py)
        # always ensures WorkspaceMember exists before adding a ProjectMember -
        # a project member is expected to already belong to the parent
        # workspace. Match that here rather than assuming every wing member is
        # already a workspace member.
        member_ids_needing_workspace = {m.user_id for m in members} - set(
            WorkspaceMember.objects.filter(
                workspace=workspace, member_id__in=[m.user_id for m in members], is_active=True
            ).values_list("member_id", flat=True)
        )

        # Individual .save() calls, not bulk_create() - ProjectMember.save() has
        # a side effect (creates a matching ProjectUserProperty row for sort
        # order/view prefs) that bulk_create() would silently skip, leaving
        # these members without proper project view preferences.
        with transaction.atomic():
            for member in members:
                if member.user_id in member_ids_needing_workspace:
                    WorkspaceMember.objects.get_or_create(
                        workspace=workspace, member=member.user, defaults={"role": role}
                    )
                    self.stdout.write(f"  (added {member.user.email} to workspace '{workspace.slug}' first)")

            for project, member in to_create:
                ProjectMember(project=project, member=member.user, role=role).save()

        self.stdout.write(self.style.SUCCESS(f"Granted {len(to_create)} project membership(s)."))

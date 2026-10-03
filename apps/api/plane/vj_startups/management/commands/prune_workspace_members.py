from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from plane.db.models import ProjectMember, Workspace, WorkspaceMember, WorkspaceMemberInvite
from plane.vj_startups.config import ROLE_ADMIN
from plane.vj_startups.services.onboarding_service import OnboardingService


class Command(BaseCommand):
    help = (
        "Remove every workspace member who is not an Admin from a workspace (default: the VJ Startups "
        "workspace). This is exactly what Plane's own Remove button does, for many people at once: the "
        "workspace membership and that person's project memberships in the workspace are deactivated. "
        "Nobody's account is deleted, pending workspace invitations are not touched, the workspace "
        "owner is kept, and a removed person can be added back (their data is intact). Note that Plane "
        "adds new accounts to the workspace automatically, and import_team_members adds the people in "
        "the team sheet as members, so this is a one-time cleanup, not a standing rule. Use --dry-run first."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--workspace",
            default=OnboardingService.WORKSPACE_SLUG,
            help=f"Workspace slug (default: {OnboardingService.WORKSPACE_SLUG}).",
        )
        parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing.")

    def handle(self, *args, **options):
        slug = options["workspace"]
        dry_run = options["dry_run"]
        workspace = Workspace.objects.filter(slug=slug).first()
        if workspace is None:
            raise CommandError(f"No workspace found with slug '{slug}'.")

        active = WorkspaceMember.objects.filter(workspace=workspace, is_active=True, member__is_bot=False)
        admins = active.filter(role__gte=ROLE_ADMIN).count()
        to_remove = active.filter(role__lt=ROLE_ADMIN).exclude(member_id=workspace.owner_id)
        ids = list(to_remove.values_list("member_id", flat=True))
        invites = WorkspaceMemberInvite.objects.filter(workspace=workspace, accepted=False).count()

        verb = "Would remove" if dry_run else "Removed"
        self.stdout.write(f"Admins kept: {admins} (plus the workspace owner).")
        self.stdout.write(f"Pending invitations left untouched: {invites}.")
        if not ids:
            self.stdout.write(self.style.SUCCESS("Nothing to remove: every active member is an Admin."))
            return
        if dry_run:
            self.stdout.write(f"{verb} {len(ids)} non-admin member(s) from workspace {slug}.")
            self.stdout.write(self.style.WARNING("Dry run - no changes written."))
            return

        now = timezone.now()
        with transaction.atomic():
            projects = ProjectMember.objects.filter(workspace=workspace, member_id__in=ids, is_active=True).update(
                is_active=False, updated_at=now
            )
            WorkspaceMember.objects.filter(workspace=workspace, member_id__in=ids, is_active=True).update(
                is_active=False, updated_at=now
            )
        self.stdout.write(self.style.SUCCESS(f"{verb} {len(ids)} non-admin member(s) from workspace {slug}."))
        self.stdout.write(f"Deactivated {projects} project membership(s) in the workspace.")
        self.clear_cached_member_lists(slug)

    def clear_cached_member_lists(self, slug):
        """Plane caches the member lists; without this the old list can show for up to an hour."""
        try:
            patterns = (f"*/api/workspaces/{slug}/members/*", "*api/users/me/workspaces/*", "*/api/users/me/settings/*")
            for pattern in patterns:
                keys = cache.keys(pattern)
                if keys:
                    cache.delete_many(keys=keys)
        except Exception as exc:  # the cleanup already succeeded; a cache problem must not fail it
            self.stdout.write(
                self.style.WARNING(
                    f"Could not clear Plane's cached lists ({type(exc).__name__}); they refresh within an hour."
                )
            )

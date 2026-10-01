from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from plane.db.models import Workspace, WorkspaceMember
from plane.vj_startups.config import plan_workspace_membership
from plane.vj_startups.services.onboarding_service import OnboardingService

User = get_user_model()

ROLE_NAMES = {5: "Guest", 15: "Member", 20: "Admin"}

# How each planned action reads in the output ("account <phrase> in workspace <slug>").
ACTION_PHRASE = {
    "add": "added as {role}",
    "reactivate": "re-activated as {role}",
    "raise": "raised to {role}",
    "keep": "unchanged (already {role} or higher)",
}


class Command(BaseCommand):
    help = (
        "Give an existing Plane account a role in a workspace (default: the VJ Startups workspace): "
        "adds it as a member, re-activates a deactivated membership, or raises a lower role. It never "
        "lowers a role. The account must already exist - the person signs in once first. Use --dry-run first."
    )

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Email of an existing Plane account.")
        parser.add_argument(
            "--role",
            type=int,
            required=True,
            choices=sorted(ROLE_NAMES),
            help="Workspace role: 5 = Guest, 15 = Member, 20 = Admin.",
        )
        parser.add_argument(
            "--workspace",
            default=OnboardingService.WORKSPACE_SLUG,
            help=f"Workspace slug (default: {OnboardingService.WORKSPACE_SLUG}).",
        )
        parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing.")

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        requested = options["role"]

        workspace = Workspace.objects.filter(slug=options["workspace"]).first()
        if workspace is None:
            raise CommandError(
                f"No workspace found with slug '{options['workspace']}'. "
                f"Available: {', '.join(Workspace.objects.values_list('slug', flat=True)) or '(none)'}"
            )

        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            raise CommandError("No Plane account with that email. The person must sign in to Plane once first.")
        if not user.is_active:
            raise CommandError("That account is deactivated.")

        membership = WorkspaceMember.objects.filter(workspace=workspace, member=user).first()
        action, new_role = plan_workspace_membership(
            membership.role if membership else None,
            membership.is_active if membership else False,
            requested,
        )
        shown_role = ROLE_NAMES[requested] if action == "keep" else ROLE_NAMES.get(new_role, str(new_role))
        outcome = f"account {ACTION_PHRASE[action].format(role=shown_role)} in workspace {workspace.slug}"

        if options["dry_run"]:
            self.stdout.write(f"Would apply: {outcome}.")
            self.stdout.write(self.style.WARNING("Dry run - no changes written."))
            return
        if action == "keep":
            self.stdout.write(self.style.SUCCESS(f"Nothing to do: {outcome}."))
            return

        with transaction.atomic():
            if membership is None:
                WorkspaceMember.objects.create(workspace=workspace, member=user, role=new_role)
            else:
                membership.role = new_role
                membership.is_active = True
                membership.save(update_fields=["role", "is_active"])
        self.stdout.write(self.style.SUCCESS(f"Applied: {outcome}."))

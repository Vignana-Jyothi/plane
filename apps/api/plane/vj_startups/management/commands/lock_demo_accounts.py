from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from plane.db.models import Workspace
from plane.license.models import InstanceAdmin
from plane.vj_startups.management.commands.seed_vj_startups import DEMO_ACCOUNT_EMAILS
from plane.vj_startups.models.organization import OrganizationMemberProfile

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Neutralise the fixture accounts that the old seed_vj_startups created on every deploy "
        "(admin@/member1@/member2@/founder1@/student1@vnrvjiet.in). They all shared one password that "
        "was written in a public repository, and admin@ was a superuser and workspace admin. This "
        "removes their password (an unusable one is set), strips superuser/staff, and with --deactivate "
        "also disables the accounts. It never deletes anything and never touches instance-admin rows or "
        "workspace ownership - it only reports them. It also unlists the accounts' profiles from the public "
        "team page (the seed flagged them as club members, so they would show as real people). "
        "Idempotent; use --dry-run first."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing.")
        parser.add_argument(
            "--deactivate",
            action="store_true",
            help="Also set is_active=False. Off by default so wing/workspace membership stays intact.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        users = list(User.objects.filter(email__in=DEMO_ACCOUNT_EMAILS).order_by("email"))
        if not users:
            self.stdout.write(self.style.SUCCESS("None of the demo accounts exist - nothing to do."))
            return

        changed = 0
        for user in users:
            changes = []
            if user.has_usable_password():
                changes.append("remove password")
            if user.is_superuser:
                changes.append("drop superuser")
            if user.is_staff:
                changes.append("drop staff")
            if options["deactivate"] and user.is_active:
                changes.append("deactivate")

            notes = []
            if InstanceAdmin.objects.filter(user=user).exists():
                notes.append("is an INSTANCE ADMIN (left as is - revoke it yourself if unintended)")
            owned = list(Workspace.objects.filter(owner=user).values_list("slug", flat=True))
            if owned:
                notes.append(f"OWNS workspace(s) {', '.join(owned)} (left as is)")

            label = ", ".join(changes) if changes else "already locked"
            self.stdout.write(f"  {user.email}: {label}")
            for note in notes:
                self.stdout.write(self.style.WARNING(f"    ! {note}"))
            if not changes:
                continue
            if dry_run:
                changed += 1
                continue

            with transaction.atomic():
                if user.has_usable_password():
                    user.set_unusable_password()
                user.is_superuser = False
                user.is_staff = False
                if options["deactivate"]:
                    user.is_active = False
                user.save()
            changed += 1

        # The seed flagged these profiles as club members, which publishes them on the public team page
        # (GET /api/vj-startups/public/team/). Unlist them even if the accounts were locked earlier.
        listed = OrganizationMemberProfile.objects.filter(user__in=users, is_club_member=True)
        listed_count = listed.count()
        if listed_count:
            tense = "would be " if dry_run else ""
            self.stdout.write(f"  {listed_count} demo profile(s) {tense}unlisted from the public team page")
            if not dry_run:
                listed.update(is_club_member=False)

        verb = "Would lock" if dry_run else "Locked"
        self.stdout.write(self.style.SUCCESS(f"{verb} {changed} of {len(users)} demo account(s)."))

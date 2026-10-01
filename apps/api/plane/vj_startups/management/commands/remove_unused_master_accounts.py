from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.utils.text import slugify

from plane.db.models import WorkspaceMemberInvite
from plane.vj_startups.management.commands.import_team_members import parse_rows

User = get_user_model()


def signed_up(user):
    """Why this account is really in use (empty string if it is just an unused placeholder).

    import_team_members gives the accounts it creates a random password that nobody knows and
    flags it is_password_autoset, so a usable password only counts when the person set it.
    """
    if user.has_usable_password() and not user.is_password_autoset:
        return "has set a password"
    if user.last_login is not None or user.last_login_time is not None:
        return "has signed in"
    return ""


class Command(BaseCommand):
    help = (
        "Delete the Plane account of the wing master of each named wing so they can sign up again with "
        "a password of their own. The people come from the team sheet. An account that already has a "
        "password or has signed in is kept. Pending workspace invitations are kept: they are tied to the "
        "email address, so the person sees them as soon as they sign up. Use --dry-run first."
    )

    def add_arguments(self, parser):
        parser.add_argument("--csv-file", required=True, help="Path to the team sheet exported as CSV.")
        parser.add_argument(
            "--wing",
            action="append",
            required=True,
            help="Wing name or slug whose master's account is removed. Repeat for several wings.",
        )
        parser.add_argument("--dry-run", action="store_true", help="Show what would happen without writing.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        wanted = {slugify(w) for w in options["wing"]}
        try:
            with open(options["csv_file"], newline="", encoding="utf-8-sig") as handle:
                rows = list(parse_rows(handle))
        except OSError as e:
            raise CommandError(f"Cannot read CSV: {e}")

        masters = {}
        for row in rows:
            slug = slugify(row["wing"])
            if row["is_master"] and slug in wanted and row["email"]:
                masters.setdefault(slug, set()).add(row["email"])

        removed = kept = 0
        for slug in sorted(wanted):
            emails = sorted(masters.get(slug, ()))
            if not emails:
                self.stdout.write(f"  {slug}: no wing master with an email in the sheet - skipped")
                continue
            for email in emails:
                user = User.objects.filter(email__iexact=email).first()
                if user is None:
                    self.stdout.write(f"  {slug}: no account exists - nothing to remove")
                    continue
                used = signed_up(user)
                if used:
                    kept += 1
                    self.stdout.write(f"  {slug}: kept - the person {used}")
                    continue

                invites = WorkspaceMemberInvite.objects.filter(email__iexact=email, accepted=False).count()
                if not dry_run:
                    try:
                        with transaction.atomic():
                            user.delete()
                    except IntegrityError:
                        # The database refuses if something (e.g. a problem or idea) still points at it.
                        kept += 1
                        self.stdout.write(f"  {slug}: kept - other data is attached to the account")
                        continue
                removed += 1
                self.stdout.write(
                    f"  {slug}: account {'would be ' if dry_run else ''}removed; "
                    f"pending workspace invitations kept: {invites}"
                )

        verb = "Would remove" if dry_run else "Removed"
        self.stdout.write(self.style.SUCCESS(f"{verb} {removed} account(s); kept {kept}."))
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run - no changes written."))

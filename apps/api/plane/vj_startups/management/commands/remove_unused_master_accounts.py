from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils.text import slugify

from plane.db.models import Workspace, WorkspaceMemberInvite
from plane.license.models import InstanceAdmin
from plane.vj_startups.management.commands.import_team_members import parse_rows

User = get_user_model()

# Tables that may hold rows belonging to the account itself (its memberships, profile and
# preferences). They go with the account. Any row in any other table that points at the account
# makes the command keep it, so it can never remove somebody's work along with the account.
OWN_TABLES = {
    "accounts",
    "profiles",
    "workspace_members",
    "project_members",
    "workspace_user_properties",
    "workspace_user_links",
    "workspace_home_preferences",
    "workspace_user_preferences",
    "vj_organization_member_profiles",
    "vj_member_badges",
    "vj_contribution_snapshots",
}
# Rows that only lose their link to the account (the foreign key is SET NULL): the wing keeps
# existing and gets its master back the next time import_team_members runs.
CLEARED_TABLES = {"vj_wings"}
# Every table has these two, set to NULL (not deleted) when the account goes.
AUDIT_COLUMNS = {"created_by_id", "updated_by_id"}


def rows_pointing_at(user):
    """{table: row count} for every database foreign key that points at this account.

    Read from the database catalogue, so tables that are not Django models (the public site's
    tables share this database) are covered too.
    """
    found = {}
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.conrelid::regclass::text, a.attname
            FROM pg_constraint c
            JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
            WHERE c.contype = 'f'
              AND c.confrelid = %s::regclass
              AND array_length(c.conkey, 1) = 1
            """,
            [User._meta.db_table],
        )
        for table, column in cursor.fetchall():
            if column in AUDIT_COLUMNS:
                continue
            cursor.execute(f'SELECT count(*) FROM {table} WHERE "{column}" = %s', [user.pk])
            count = cursor.fetchone()[0]
            if count:
                table = table.strip('"')
                found[table] = found.get(table, 0) + count
    return found


def reasons_to_keep(user):
    """Why this account must not be deleted (empty list = it is an unused placeholder)."""
    reasons = []
    if user.has_usable_password():
        reasons.append("it has a password")
    if user.last_login is not None or user.last_login_time is not None:
        reasons.append("it has signed in before")
    if user.is_superuser or user.is_staff:
        reasons.append("it is staff/superuser")
    if InstanceAdmin.objects.filter(user=user).exists():
        reasons.append("it is an Instance Admin")
    if Workspace.objects.filter(owner=user).exists():
        reasons.append("it owns a workspace")
    foreign = {
        table: count
        for table, count in rows_pointing_at(user).items()
        if table not in OWN_TABLES and table not in CLEARED_TABLES
    }
    if foreign:
        reasons.append("other data points at it: " + ", ".join(f"{t} ({n})" for t, n in sorted(foreign.items())))
    return reasons


class Command(BaseCommand):
    help = (
        "Delete the Plane account of the wing master of each named wing, but only if the account was "
        "created for them (by import_team_members) and they never signed in to it and it has no "
        "password. The point is to let them sign up themselves with a password of their own. The "
        "people are looked up in the team sheet, so nobody outside the named wings' master rows can "
        "be affected. An account that has signed in, has a password, is staff/an Instance Admin/a "
        "workspace owner, or has anything but its own memberships pointing at it is kept. Pending "
        "workspace invitations are kept: they are tied to the email address. Use --dry-run first."
    )

    def add_arguments(self, parser):
        parser.add_argument("--csv-file", required=True, help="Path to the team sheet exported as CSV.")
        parser.add_argument(
            "--wing",
            action="append",
            required=True,
            help="Wing name or slug whose master's unused account is removed. Repeat for several wings.",
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
                reasons = reasons_to_keep(user)
                if reasons:
                    kept += 1
                    self.stdout.write(f"  {slug}: kept - " + "; ".join(reasons))
                    continue

                invites = WorkspaceMemberInvite.objects.filter(email__iexact=email, accepted=False).count()
                self.stdout.write(
                    f"  {slug}: unused account ({'would be ' if dry_run else ''}removed); "
                    f"pending workspace invitations kept: {invites}"
                )
                if not dry_run:
                    with transaction.atomic():
                        user.delete()
                removed += 1

        verb = "Would remove" if dry_run else "Removed"
        self.stdout.write(self.style.SUCCESS(f"{verb} {removed} unused account(s); kept {kept}."))
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run - no changes written."))

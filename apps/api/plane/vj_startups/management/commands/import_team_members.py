import csv
import re
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from plane.db.models import User
from plane.vj_startups.config import ROLE_ADMIN, workspace_admin_wing_slugs
from plane.vj_startups.models.organization import OrganizationMemberProfile, Wing
from plane.vj_startups.services.onboarding_service import OnboardingService

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TITLE_RE = re.compile(r"^(mr|mrs|ms|miss|dr)\b\.?\s*", re.IGNORECASE)

# Sheet header (lowercased, whitespace collapsed) prefix -> our field name.
# Matching by prefix survives the sheet's multi-line "Phone Number ..." header.
COLUMN_PREFIXES = {
    "display name": "name",
    "wing name": "wing",
    "role": "role",
    "department": "department",
    "year": "year",
    "email": "email",
    "linkedin": "linkedin",
    "insta": "instagram",
    "photo": "photo",
}
DRIVE_ID_RE = re.compile(r"(?:/d/|[?&]id=)([A-Za-z0-9_-]{10,})")


def normalise_headers(fieldnames):
    mapping = {}
    for raw in fieldnames or []:
        cleaned = " ".join((raw or "").lower().split())
        for prefix, field in COLUMN_PREFIXES.items():
            if cleaned.startswith(prefix) and field not in mapping.values():
                mapping[raw] = field
                break
    return mapping


def clean_name(value):
    name = " ".join((value or "").split())
    name = TITLE_RE.sub("", name).strip()
    # The sheet has a few all-lowercase entries ("sahithi varma") - fix those, leave mixed case alone.
    return name.title() if name.islower() else name


def build_headline(department, year):
    department = " ".join((department or "").split())
    return " - ".join(part for part in (department, (year or "").strip()) if part)


def split_name(name):
    parts = name.split(" ", 1)
    return parts[0], (parts[1] if len(parts) > 1 else "")


def clean_email(value):
    email = (value or "").strip().lower()
    return email if EMAIL_RE.match(email) else ""


def clean_url(value):
    # Sheet URLs carry share-tracking params (?utm_source=..., ?igsh=...) - drop them.
    url = (value or "").strip().split("?")[0]
    return url if url.startswith("http") and len(url) <= 200 else ""


def clean_photo_url(value):
    """A Google Drive share link becomes a directly loadable image URL; another http(s) URL is
    kept as is; anything else (a name typed into the cell, blank) is dropped. The Drive file
    must be shared as 'anyone with the link' for the image to load."""
    text = (value or "").strip()
    if "drive.google.com" in text:
        match = DRIVE_ID_RE.search(text)
        return f"https://drive.google.com/thumbnail?id={match.group(1)}&sz=w600" if match else ""
    return text if text.startswith("http") and len(text) <= 500 else ""


def parse_role(value):
    """'wing member - ProblemHunt ' -> (False, 'Wing Member - ProblemHunt')."""
    text = " ".join((value or "").split())
    head, _, focus = text.partition(" - ")
    is_master = head.lower().startswith("wing master")
    label = "Wing Master" if is_master else "Wing Member"
    return is_master, (f"{label} - {focus.strip()}" if focus.strip() else label)


def parse_rows(handle):
    """Yield one dict per usable sheet row; blank spacer rows are dropped."""
    reader = csv.DictReader(handle)
    mapping = normalise_headers(reader.fieldnames)
    missing = {"name", "wing", "role", "email"} - set(mapping.values())
    if missing:
        raise CommandError(f"CSV is missing expected column(s): {', '.join(sorted(missing))}")

    for row in reader:
        fields = {field: (row.get(raw) or "").strip() for raw, field in mapping.items()}
        if not fields["name"] or not fields["wing"]:
            continue
        is_master, role = parse_role(fields["role"])
        yield {
            "name": clean_name(fields["name"]),
            "wing": fields["wing"],
            "is_master": is_master,
            "role": role,
            "email": clean_email(fields["email"]),
            "raw_email": fields["email"],
            "headline": build_headline(fields.get("department"), fields.get("year")),
            "linkedin": clean_url(fields.get("linkedin", "")),
            "instagram": clean_url(fields.get("instagram", "")),
            "photo": clean_photo_url(fields.get("photo", "")),
        }


class Command(BaseCommand):
    help = (
        "Fill in VJ Startups team member details (wing, role, headline, LinkedIn) from the team sheet "
        "exported as CSV. Matches people by email. Never touches phone numbers or roll numbers. "
        "Idempotent - safe to re-run. Use --dry-run first."
    )

    def add_arguments(self, parser):
        parser.add_argument("--csv-file", required=True, help="Path to the team sheet exported as CSV.")
        parser.add_argument(
            "--create-missing",
            action="store_true",
            help="Create a Plane account for sheet emails that do not exist yet (they can then sign in with Google).",
        )
        parser.add_argument(
            "--set-public-roles",
            action="store_true",
            help=(
                "Also set the public-site role (WING_MASTER / WING_MEMBER), which lets them verify problems "
                "and ideas. Never changes an existing ADMIN. Off by default."
            ),
        )
        parser.add_argument(
            "--publish-team",
            action="store_true",
            help="Also list the people in the sheet on the public site's team page (is_club_member). Off by default.",
        )
        parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        try:
            with open(options["csv_file"], newline="", encoding="utf-8-sig") as handle:
                rows = list(parse_rows(handle))
        except OSError as e:
            raise CommandError(f"Cannot read CSV: {e}")

        wings = {w.slug: w for w in Wing.objects.all()}
        stats = {
            "updated": 0,
            "created": 0,
            "masters": 0,
            "no_email": [],
            "no_account": [],
            "bad_wing": [],
            "dupes": 0,
        }
        seen = set()

        for row in rows:
            wing = wings.get(slugify(row["wing"]))
            if wing is None:
                stats["bad_wing"].append(row["name"])
                continue
            if not row["email"]:
                stats["no_email"].append(f"{row['name']} ({wing.name})")
                continue
            if row["email"] in seen:
                stats["dupes"] += 1
                continue
            seen.add(row["email"])

            user = User.objects.filter(email=row["email"]).first()
            if user is None and not options["create_missing"]:
                stats["no_account"].append(f"{row['name']} <{row['email']}>")
                continue

            action = "create" if user is None else "update"
            self.stdout.write(f"  {action}: {row['email']} -> {wing.name}, {row['role']}")
            if dry_run:
                stats["created" if user is None else "updated"] += 1
                if row["is_master"]:
                    stats["masters"] += 1
                continue

            with transaction.atomic():
                if user is None:
                    first, last = split_name(row["name"])
                    user = User(email=row["email"], username=uuid.uuid4().hex, first_name=first, last_name=last)
                    user.set_password(uuid.uuid4().hex)
                    user.is_password_autoset = True
                    user.is_email_verified = True
                    user.save()  # post_save onboards them into the workspace, like Google sign-in does
                    stats["created"] += 1
                else:
                    stats["updated"] += 1

                profile, _ = OrganizationMemberProfile.objects.get_or_create(user=user)
                profile.wing = wing
                profile.role = row["role"]
                if not profile.headline and row["headline"]:
                    profile.headline = row["headline"]
                if not profile.linkedin_url and row["linkedin"]:
                    profile.linkedin_url = row["linkedin"]
                if not profile.instagram_url and row["instagram"]:
                    profile.instagram_url = row["instagram"]
                if not profile.photo_url and row["photo"]:
                    profile.photo_url = row["photo"]
                if options["publish_team"]:
                    profile.is_club_member = True
                if options["set_public_roles"] and profile.public_role != OrganizationMemberProfile.PublicRole.ADMIN:
                    profile.public_role = (
                        OrganizationMemberProfile.PublicRole.WING_MASTER
                        if row["is_master"]
                        else OrganizationMemberProfile.PublicRole.WING_MEMBER
                    )
                profile.save()

                if row["is_master"]:
                    if wing.wing_master_id is None:
                        wing.wing_master = user
                        wing.save(update_fields=["wing_master"])
                    elif wing.wing_master_id != user.id:
                        self.stdout.write(
                            self.style.WARNING(f"  note: {wing.name} already has a wing master; left as is")
                        )
                    # Every wing master administers their wing's project; the master of a wing
                    # listed in VJ_WORKSPACE_ADMIN_WINGS (default: vision) is also a workspace
                    # Admin. The profile save above only adds plain members, so raise it here.
                    OnboardingService.onboard_user_to_wing(user, wing, role=ROLE_ADMIN)
                    stats["masters"] += 1

        self.stdout.write("")
        verb = "Would apply" if dry_run else "Applied"
        self.stdout.write(self.style.SUCCESS(f"{verb}: {stats['updated']} updated, {stats['created']} created."))
        if stats["masters"]:
            wing_slugs = workspace_admin_wing_slugs()
            admin_wings = "all wings" if "*" in wing_slugs else (", ".join(wing_slugs) or "no wing")
            # Starts with "Would apply" / "Applied" so the data-operations workflow log shows it.
            self.stdout.write(
                f"{'Would apply' if dry_run else 'Applied'} wing masters: {stats['masters']} Admin of their wing's "
                f"project (workspace Admin for: {admin_wings})."
            )
        if stats["dupes"]:
            self.stdout.write(f"Skipped {stats['dupes']} duplicate email row(s).")
        for label, key in (
            ("no email in the sheet (add one to include them)", "no_email"),
            ("no Plane account yet (re-run with --create-missing to create them)", "no_account"),
            ("wing not found in the database", "bad_wing"),
        ):
            if stats[key]:
                self.stdout.write(self.style.WARNING(f"{len(stats[key])} skipped - {label}:"))
                for item in stats[key]:
                    self.stdout.write(f"    {item}")

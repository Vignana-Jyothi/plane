"""
Set a new password for an Instance Admin without shell access or outgoing email.

Meant for the "Data operations (manual)" workflow (part: reset-admin-password), for the case where an
admin has forgotten their password and the instance has no SMTP, so the "forgot password" email cannot
be sent. Plane's own `reset_password` command does the same job but is interactive.

Safeguards:
  * The new password is read from the environment (VJ_NEW_PASSWORD), never from the command line,
    so it does not appear in process listings or in the workflow's command echo.
  * Neither the password nor the email address is ever printed (the workflow's logs are public).
  * It only acts on an existing, active account that is an Instance Admin or a superuser, so it
    cannot be used to take over an ordinary member's account.
  * The password must pass the same strength check Plane applies (zxcvbn score >= 3), plus a
    minimum length.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from zxcvbn import zxcvbn

from plane.license.models import InstanceAdmin

User = get_user_model()

PASSWORD_ENV = "VJ_NEW_PASSWORD"
MIN_LENGTH = 12


def check_new_password(password):
    """Return the password if it is acceptable, else raise ValueError with a reason safe to print."""
    if not password or not password.strip():
        raise ValueError(f"The new password is empty. Set the {PASSWORD_ENV} environment variable.")
    if len(password) < MIN_LENGTH:
        raise ValueError(f"The new password is too short (at least {MIN_LENGTH} characters).")
    if zxcvbn(password)["score"] < 3:
        raise ValueError("The new password is too easy to guess; choose a stronger one.")
    return password


def refusal_reason(exists, is_active, is_instance_admin, is_superuser):
    """Why the password of this account must not be reset here, or None if it may be."""
    if not exists:
        return "No Plane account with that email."
    if not is_active:
        return "That account is deactivated."
    if not (is_instance_admin or is_superuser):
        return "That account is not an Instance Admin, so its password is not reset here."
    return None


class Command(BaseCommand):
    help = (
        "Set a new password for an Instance Admin account, read from the VJ_NEW_PASSWORD environment "
        "variable. Refuses accounts that are not Instance Admins or superusers. Use --dry-run first."
    )

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Email of the Instance Admin account.")
        parser.add_argument("--dry-run", action="store_true", help="Check the account and password; write nothing.")

    def handle(self, *args, **options):
        email = options["email"].strip().lower()

        user = User.objects.filter(email__iexact=email).first()
        reason = refusal_reason(
            exists=user is not None,
            is_active=bool(user and user.is_active),
            is_instance_admin=bool(user and InstanceAdmin.objects.filter(user=user).exists()),
            is_superuser=bool(user and user.is_superuser),
        )
        if reason:
            raise CommandError(reason)

        try:
            password = check_new_password(os.environ.get(PASSWORD_ENV, ""))
        except ValueError as exc:
            raise CommandError(str(exc))

        if options["dry_run"]:
            self.stdout.write("Dry run: the account is an eligible Instance Admin and the new password is acceptable.")
            self.stdout.write("Dry run: nothing was changed.")
            return

        user.set_password(password)
        user.is_password_autoset = False
        user.save(update_fields=["password", "is_password_autoset"])
        self.stdout.write(self.style.SUCCESS("Password updated for the Instance Admin account."))

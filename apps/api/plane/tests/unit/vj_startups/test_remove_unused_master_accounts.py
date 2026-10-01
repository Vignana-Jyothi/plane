# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from plane.vj_startups.management.commands import remove_unused_master_accounts as cmd

ROWS = [
    {"wing": "Ignition", "is_master": True, "email": "ignition.master@example.com"},
    {"wing": "Fuel", "is_master": True, "email": "fuel.master@example.com"},
    {"wing": "Echo", "is_master": True, "email": "echo.master@example.com"},
    {"wing": "Ignition", "is_master": False, "email": "ignition.member@example.com"},
]


def account(password=False, last_login=None):
    user = MagicMock()
    user.has_usable_password.return_value = password
    user.last_login = last_login
    user.last_login_time = None
    return user


def run(users, *wings, dry_run=False, delete_error=None):
    """Run the command for `wings`; `users` maps email -> account."""
    if delete_error:
        for user in users.values():
            user.delete.side_effect = delete_error
    out = StringIO()
    with (
        patch.object(cmd, "parse_rows", return_value=ROWS),
        patch.object(cmd, "open", create=True),
        patch.object(cmd, "transaction"),
        patch.object(cmd, "User") as user_model,
        patch.object(cmd, "WorkspaceMemberInvite") as invites,
    ):
        user_model.objects.filter.side_effect = lambda email__iexact: MagicMock(
            first=lambda: users.get(email__iexact)
        )
        invites.objects.filter.return_value.count.return_value = 1
        args = ["--csv-file", "team.csv"]
        for wing in wings:
            args += ["--wing", wing]
        if dry_run:
            args.append("--dry-run")
        call_command("remove_unused_master_accounts", *args, stdout=out)
    return out.getvalue()


@pytest.mark.unit
class TestRemoveUnusedMasterAccounts:
    def test_deletes_the_unused_account_of_each_named_wings_master(self):
        users = {
            "ignition.master@example.com": account(),
            "fuel.master@example.com": account(),
            "echo.master@example.com": account(),
        }

        out = run(users, "ignition", "fuel")

        users["ignition.master@example.com"].delete.assert_called_once()
        users["fuel.master@example.com"].delete.assert_called_once()
        users["echo.master@example.com"].delete.assert_not_called()
        assert "Removed 2 account(s); kept 0." in out
        assert "@" not in out

    def test_a_dry_run_deletes_nothing(self):
        users = {"ignition.master@example.com": account()}

        out = run(users, "ignition", dry_run=True)

        users["ignition.master@example.com"].delete.assert_not_called()
        assert "Would remove 1 account(s)" in out

    def test_other_members_of_the_wing_are_never_touched(self):
        users = {"ignition.member@example.com": account(), "ignition.master@example.com": account()}

        run(users, "ignition")

        users["ignition.member@example.com"].delete.assert_not_called()

    def test_an_account_that_has_signed_up_is_kept(self):
        users = {
            "ignition.master@example.com": account(password=True),
            "fuel.master@example.com": account(last_login="x"),
        }

        out = run(users, "ignition", "fuel")

        users["ignition.master@example.com"].delete.assert_not_called()
        users["fuel.master@example.com"].delete.assert_not_called()
        assert "Removed 0 account(s); kept 2." in out

    def test_an_account_the_database_refuses_to_delete_is_kept(self):
        users = {"ignition.master@example.com": account()}

        out = run(users, "ignition", delete_error=cmd.IntegrityError())

        assert "kept 1" in out

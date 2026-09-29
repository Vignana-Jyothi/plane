# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import io
import pathlib
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from plane.db.models import User
from plane.vj_startups.management.commands import seed_vj_startups
from plane.vj_startups.management.commands.seed_vj_startups import (
    DEMO_ACCOUNT_EMAILS,
    DEMO_ACCOUNTS,
    Command as SeedCommand,
)

# The password the old seed wrote onto every demo account on every deploy, in a
# public repository. It must never come back.
LEAKED_PASSWORD = "vjstartups123"


@pytest.mark.unit
class TestSeedCommandSafety:
    def test_no_password_is_hardcoded_in_the_seed_module(self):
        source = pathlib.Path(seed_vj_startups.__file__).read_text(encoding="utf-8")
        assert LEAKED_PASSWORD not in source

    def test_demo_accounts_are_refused_when_debug_is_off(self):
        with override_settings(DEBUG=False):
            with pytest.raises(CommandError):
                call_command("seed_vj_startups", "--with-demo-data")

    def test_demo_email_list_matches_the_accounts(self):
        assert DEMO_ACCOUNT_EMAILS == [account["email"] for account in DEMO_ACCOUNTS]
        assert len(set(DEMO_ACCOUNT_EMAILS)) == len(DEMO_ACCOUNTS)

    def test_a_plain_seed_never_creates_demo_data(self):
        with (
            patch.object(SeedCommand, "_seed_reference_data") as reference,
            patch.object(SeedCommand, "_seed_demo_data") as demo,
            patch.object(SeedCommand, "_backfill_wing_projects") as backfill,
        ):
            call_command("seed_vj_startups", stdout=io.StringIO())
        reference.assert_called_once()
        backfill.assert_called_once()
        demo.assert_not_called()

    def test_demo_data_needs_the_flag_and_debug(self):
        with (
            override_settings(DEBUG=True),
            patch.object(SeedCommand, "_seed_reference_data"),
            patch.object(SeedCommand, "_seed_demo_data") as demo,
            patch.object(SeedCommand, "_backfill_wing_projects"),
        ):
            call_command("seed_vj_startups", "--with-demo-data", "--demo-password", "x", stdout=io.StringIO())
        demo.assert_called_once_with("x")


def make_user(email, *, superuser=False, staff=False, active=True):
    # bulk_create skips the post_save onboarding signal, which is irrelevant here.
    user = User(
        email=email,
        username=email.split("@")[0],
        password=make_password(LEAKED_PASSWORD),
        is_superuser=superuser,
        is_staff=staff,
        is_active=active,
    )
    User.objects.bulk_create([user])
    return User.objects.get(email=email)


def run_lock(*args):
    out = io.StringIO()
    call_command("lock_demo_accounts", *args, stdout=out)
    return out.getvalue()


@pytest.mark.unit
@pytest.mark.django_db
class TestLockDemoAccounts:
    def test_removes_the_password_and_privileges(self):
        make_user("admin@vnrvjiet.in", superuser=True, staff=True)

        run_lock()

        user = User.objects.get(email="admin@vnrvjiet.in")
        assert not user.has_usable_password()
        assert not user.check_password(LEAKED_PASSWORD)
        assert not user.is_superuser
        assert not user.is_staff
        assert user.is_active  # membership stays intact unless --deactivate

    def test_dry_run_changes_nothing(self):
        make_user("admin@vnrvjiet.in", superuser=True, staff=True)

        output = run_lock("--dry-run")

        user = User.objects.get(email="admin@vnrvjiet.in")
        assert user.check_password(LEAKED_PASSWORD)
        assert user.is_superuser
        assert "Would lock 1 of 1" in output

    def test_deactivate_flag_disables_the_account(self):
        make_user("member1@vnrvjiet.in")

        run_lock("--deactivate")

        assert not User.objects.get(email="member1@vnrvjiet.in").is_active

    def test_is_idempotent(self):
        make_user("admin@vnrvjiet.in", superuser=True, staff=True)
        run_lock()

        output = run_lock()

        assert "already locked" in output
        assert "Locked 0 of 1" in output

    def test_leaves_real_accounts_alone(self):
        make_user("admin@vnrvjiet.in", superuser=True)
        real = make_user("someone.real@vnrvjiet.in", superuser=True)

        run_lock()

        real.refresh_from_db()
        assert real.has_usable_password()
        assert real.is_superuser

    def test_reports_cleanly_when_no_demo_accounts_exist(self):
        assert "nothing to do" in run_lock()

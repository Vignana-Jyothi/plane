# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from unittest.mock import MagicMock, patch

import pytest

from plane.vj_startups.management.commands import remove_unused_master_accounts as cmd


def account(**overrides):
    user = MagicMock()
    user.has_usable_password.return_value = False
    user.last_login = None
    user.last_login_time = None
    user.is_superuser = False
    user.is_staff = False
    for key, value in overrides.items():
        setattr(user, key, value)
    return user


def reasons(user, pointing=None, instance_admin=False, owns_workspace=False):
    with (
        patch.object(cmd.InstanceAdmin, "objects") as admins,
        patch.object(cmd.Workspace, "objects") as workspaces,
        patch.object(cmd, "rows_pointing_at", return_value=pointing or {}),
    ):
        admins.filter.return_value.exists.return_value = instance_admin
        workspaces.filter.return_value.exists.return_value = owns_workspace
        return cmd.reasons_to_keep(user)


@pytest.mark.unit
class TestReferencedValue:
    def test_a_foreign_key_to_email_is_compared_with_the_email(self):
        user = account(email="someone@example.com", id="the-id")

        assert cmd.referenced_value(user, "email") == "someone@example.com"
        assert cmd.referenced_value(user, "id") == "the-id"

    def test_a_column_that_is_not_an_attribute_is_unknown(self):
        class Plain:
            pass

        assert cmd.referenced_value(Plain(), "no_such_column") is cmd.UNKNOWN


@pytest.mark.unit
class TestReasonsToKeep:
    def test_an_unused_placeholder_account_may_be_removed(self):
        assert reasons(account()) == []

    def test_its_own_memberships_and_profile_do_not_block_removal(self):
        pointing = {"workspace_members": 1, "project_members": 1, "profiles": 1, "vj_organization_member_profiles": 1}

        assert reasons(account(), pointing) == []

    def test_a_wing_that_names_it_as_master_does_not_block_removal(self):
        assert reasons(account(), {"vj_wings": 1}) == []

    def test_an_account_with_a_password_is_kept(self):
        user = account()
        user.has_usable_password.return_value = True

        assert "it has a password" in reasons(user)

    def test_an_account_that_has_signed_in_is_kept(self):
        assert "it has signed in before" in reasons(account(last_login_time="2026-10-01"))

    def test_staff_instance_admins_and_workspace_owners_are_kept(self):
        assert "it is staff/superuser" in reasons(account(is_staff=True))
        assert "it is an Instance Admin" in reasons(account(), instance_admin=True)
        assert "it owns a workspace" in reasons(account(), owns_workspace=True)

    def test_an_account_with_someone_elses_data_attached_is_kept(self):
        found = reasons(account(), {"problems": 3, "workspace_members": 1})

        assert len(found) == 1
        assert "problems (3)" in found[0]
        assert "workspace_members" not in found[0]

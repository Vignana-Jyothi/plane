# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from plane.vj_startups.management.commands import prune_workspace_members as cmd


def run(removable_ids, *, dry_run=False, workspace_exists=True):
    """Run the command with `removable_ids` as the non-admin members it would remove."""
    out = StringIO()
    with (
        patch.object(cmd, "Workspace") as workspace_model,
        patch.object(cmd, "WorkspaceMember") as member_model,
        patch.object(cmd, "ProjectMember") as project_model,
        patch.object(cmd, "WorkspaceMemberInvite") as invites,
        patch.object(cmd, "transaction"),
        patch.object(cmd, "cache") as cache,
    ):
        workspace_model.objects.filter.return_value.first.return_value = MagicMock() if workspace_exists else None
        active = member_model.objects.filter.return_value
        active.filter.return_value.count.return_value = 8
        active.filter.return_value.exclude.return_value.values_list.return_value = removable_ids
        invites.objects.filter.return_value.count.return_value = 2
        project_model.objects.filter.return_value.update.return_value = 5
        cache.keys.return_value = ["k"]
        args = ["--dry-run"] if dry_run else []
        call_command("prune_workspace_members", *args, stdout=out)
        return out.getvalue(), member_model, project_model, cache


@pytest.mark.unit
class TestPruneWorkspaceMembers:
    def test_a_dry_run_reports_counts_and_writes_nothing(self):
        out, members, projects, cache = run(["a", "b", "c"], dry_run=True)

        assert "Would remove 3 non-admin member(s)" in out
        assert "Admins kept: 8" in out
        assert "Pending invitations left untouched: 2" in out
        members.objects.filter.return_value.update.assert_not_called()
        projects.objects.filter.return_value.update.assert_not_called()

    def test_apply_deactivates_memberships_and_never_deletes_anything(self):
        out, members, projects, cache = run(["a", "b"])

        assert "Removed 2 non-admin member(s)" in out
        assert "Deactivated 5 project membership(s)" in out
        projects.objects.filter.return_value.update.assert_called_once()
        assert members.objects.filter.return_value.update.call_args.kwargs["is_active"] is False
        members.objects.filter.return_value.delete.assert_not_called()
        cache.delete_many.assert_called()

    def test_nothing_to_remove_when_everyone_is_an_admin(self):
        out, members, projects, cache = run([])

        assert "Nothing to remove" in out
        projects.objects.filter.return_value.update.assert_not_called()

    def test_an_unknown_workspace_is_an_error(self):
        with pytest.raises(CommandError):
            run([], workspace_exists=False)

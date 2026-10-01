# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from unittest.mock import MagicMock, patch

import pytest

from plane.vj_startups.models.extension import VJProjectExtension
from plane.vj_startups.views.admin import AdminStartupDetailEndpoint


def link(project):
    ext = MagicMock()
    ext.project = project
    return ext


def destroy(links):
    """Run perform_destroy for a startup whose project links are `links`; return the call order."""
    calls = []
    instance = MagicMock()
    instance.delete.side_effect = lambda: calls.append("startup")
    for ext in links:
        if ext.project is not None:
            ext.project.delete.side_effect = lambda ext=ext: calls.append(ext.project)

    with patch.object(VJProjectExtension, "objects") as manager:
        manager.filter.return_value.select_related.return_value = links
        AdminStartupDetailEndpoint().perform_destroy(instance)
    return calls, manager, instance


@pytest.mark.unit
class TestStartupDelete:
    def test_every_linked_project_is_deleted_before_the_startup(self):
        projects = [MagicMock(name=f"project{i}") for i in range(3)]

        calls, _, _ = destroy([link(p) for p in projects])

        assert calls == [*projects, "startup"]

    def test_a_startup_with_many_duplicate_projects_can_be_deleted(self):
        # The old .get() raised MultipleObjectsReturned here (a 500) once provisioning had
        # created a project per run.
        projects = [MagicMock() for _ in range(34)]

        calls, _, _ = destroy([link(p) for p in projects])

        assert len(calls) == 35
        assert calls[-1] == "startup"

    def test_a_startup_with_no_project_is_still_deleted(self):
        calls, _, _ = destroy([])

        assert calls == ["startup"]

    def test_a_link_without_a_project_is_skipped(self):
        project = MagicMock()

        calls, _, _ = destroy([link(None), link(project)])

        assert calls == [project, "startup"]

    def test_the_projects_are_looked_up_by_startup(self):
        _, manager, instance = destroy([])

        manager.filter.assert_called_once_with(startup=instance)

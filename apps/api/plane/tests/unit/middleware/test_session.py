# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from django.conf import settings

from plane.authentication.middleware.session import SessionMiddleware, uses_admin_session


def request_for(path):
    return SimpleNamespace(
        path=path,
        COOKIES={settings.ADMIN_SESSION_COOKIE_NAME: "admin-key", settings.SESSION_COOKIE_NAME: "web-key"},
    )


def session_key_used_for(path):
    middleware = SessionMiddleware.__new__(SessionMiddleware)
    middleware.SessionStore = MagicMock()
    middleware.process_request(request_for(path))
    return middleware.SessionStore.call_args.args[0]


@pytest.mark.unit
class TestAdminSessionPaths:
    def test_plane_admin_api_and_the_vj_startups_admin_pages_use_the_admin_session(self):
        assert uses_admin_session("/api/instances/admins/")
        assert uses_admin_session("/api/vj-startups/admin/microservice/users/")
        assert uses_admin_session("/api/vj-startups/admin/wings/")

    def test_everything_else_uses_the_normal_session(self):
        assert not uses_admin_session("/api/users/me/")
        assert not uses_admin_session("/api/workspaces/vj-startups/members/")
        assert not uses_admin_session("/api/vj-startups/leaderboards/members/")
        assert not uses_admin_session("/api/vj-startups/public/team/")

    def test_the_session_is_read_from_the_matching_cookie(self):
        assert session_key_used_for("/api/vj-startups/admin/microservice/users/") == "admin-key"
        assert session_key_used_for("/api/instances/") == "admin-key"
        assert session_key_used_for("/api/users/me/") == "web-key"

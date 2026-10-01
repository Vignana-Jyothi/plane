# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from types import SimpleNamespace

import pytest

from plane.vj_startups.views.public_team import is_master, member_name, serialize_member, team_sort_key


def member(name="Asha Rao", wing="Vision", role="Wing Member", **overrides):
    first, _, last = name.partition(" ")
    profile = SimpleNamespace(
        user=SimpleNamespace(first_name=first, last_name=last, display_name="", avatar="", email="private@example.com"),
        wing=SimpleNamespace(name=wing, slug=wing.lower()),
        role=role,
        headline="Information Technology - 3rd Year",
        linkedin_url="https://www.linkedin.com/in/asha",
        instagram_url=None,
        photo_url=None,
    )
    for key, value in overrides.items():
        setattr(profile, key, value)
    return profile


@pytest.mark.unit
class TestPublicTeam:
    def test_only_public_fields_are_returned(self):
        data = serialize_member(member(), 1)

        assert set(data) == {
            "name",
            "wing",
            "wing_slug",
            "role",
            "is_wing_master",
            "department_year",
            "linkedin_url",
            "instagram_url",
            "photo_url",
            "order",
        }
        assert "private@example.com" not in str(data)

    def test_missing_optional_links_are_empty_strings_not_null(self):
        data = serialize_member(member(), 1)

        assert data["instagram_url"] == ""
        assert data["photo_url"] == ""

    def test_the_sheet_photo_wins_over_the_account_avatar(self):
        both = member(photo_url="https://example.com/sheet.jpg")
        both.user.avatar = "https://example.com/avatar.jpg"
        avatar_only = member()
        avatar_only.user.avatar = "https://example.com/avatar.jpg"
        internal_path = member()
        internal_path.user.avatar = "/uploads/a.png"

        assert serialize_member(both, 1)["photo_url"] == "https://example.com/sheet.jpg"
        assert serialize_member(avatar_only, 1)["photo_url"] == "https://example.com/avatar.jpg"
        assert serialize_member(internal_path, 1)["photo_url"] == ""

    def test_wing_masters_are_listed_first_then_by_wing_and_name(self):
        people = [
            member("Zed Z", "Echo", "Wing Member - Posters"),
            member("Amy A", "Vision", "Wing Member"),
            member("Mia M", "Vision", "Wing Master - Vision and Strategy"),
            member("Bob B", "Echo", "Wing Master - Media"),
            member("Cal C", "Echo", "Wing Member"),
        ]

        ordered = [member_name(p) for p in sorted(people, key=team_sort_key)]

        assert ordered == ["Bob B", "Mia M", "Cal C", "Zed Z", "Amy A"]

    def test_is_master_reads_the_role_text_case_insensitively(self):
        assert is_master(member(role="wing master - X"))
        assert not is_master(member(role="Wing Member"))

    def test_the_name_falls_back_to_the_display_name(self):
        nameless = member(name="")
        nameless.user.display_name = "asha"

        assert member_name(nameless) == "asha"

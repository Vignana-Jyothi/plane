# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import pytest

from plane.vj_startups.services.badges import RULES, earned_badge_slugs


def stats(completed_total=0, longest_streak=0, active_days=0):
    return {"completed_total": completed_total, "longest_streak": longest_streak, "active_days": active_days}


@pytest.mark.unit
class TestAutomaticBadges:
    def test_nothing_done_earns_nothing(self):
        assert earned_badge_slugs(stats()) == []

    def test_first_task(self):
        assert earned_badge_slugs(stats(completed_total=1)) == ["first_task"]

    def test_task_milestones_stack(self):
        assert earned_badge_slugs(stats(completed_total=10)) == ["first_task", "10_tasks"]
        assert earned_badge_slugs(stats(completed_total=100)) == ["first_task", "10_tasks", "100_tasks"]

    def test_streak_badges_use_the_longest_streak(self):
        assert earned_badge_slugs(stats(longest_streak=6)) == []
        assert earned_badge_slugs(stats(longest_streak=7)) == ["streak_7"]
        assert earned_badge_slugs(stats(longest_streak=30)) == ["streak_7", "streak_30"]

    def test_active_days_badge(self):
        assert earned_badge_slugs(stats(active_days=99)) == []
        assert earned_badge_slugs(stats(active_days=100)) == ["active_100"]

    def test_slugs_are_unique(self):
        slugs = [rule.slug for rule in RULES]
        assert len(slugs) == len(set(slugs))

    def test_the_seeded_100_tasks_badge_is_reused_not_renamed(self):
        # seed_vj_startups already creates this slug; the rule must target the same one.
        assert "100_tasks" in [rule.slug for rule in RULES]

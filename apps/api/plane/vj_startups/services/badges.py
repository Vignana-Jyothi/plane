"""
Automatic badges earned from real work in Plane.

Only badges that can be decided from Plane's own data live here. Badges that
need a human judgement (Top Founder, Mentor, Grant Winner...) stay manual: an
admin awards them and this module never touches or removes them.

`earned_badge_slugs` is pure so the rules are unit-testable; `award_badges`
writes. Badges are only ever added, never revoked, so a quiet month does not
take away something earned.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BadgeRule:
    slug: str
    name: str
    description: str
    # Receives the stats dict from `member_stats` and says whether the badge is earned.
    earned: callable


# `100_tasks` already exists in the seeded catalogue; its name and description are kept as they are.
RULES = (
    BadgeRule("first_task", "First Task", "Completed your first task", lambda s: s["completed_total"] >= 1),
    BadgeRule("10_tasks", "10 Tasks", "Completed 10 tasks", lambda s: s["completed_total"] >= 10),
    BadgeRule("100_tasks", "100 Tasks", "Completed 100 tasks", lambda s: s["completed_total"] >= 100),
    BadgeRule("streak_7", "Week Streak", "Contributed 7 days in a row", lambda s: s["longest_streak"] >= 7),
    BadgeRule("streak_30", "Month Streak", "Contributed 30 days in a row", lambda s: s["longest_streak"] >= 30),
    BadgeRule("active_100", "Always Active", "Contributed on 100 different days", lambda s: s["active_days"] >= 100),
)


def earned_badge_slugs(stats):
    """Slugs of every automatic badge these stats qualify for."""
    return [rule.slug for rule in RULES if rule.earned(stats)]


def member_stats(user, workspace, calendar):
    """The numbers the rules read: all-time completed tasks, plus streaks/active days from the calendar."""
    from plane.db.models import Issue

    completed_total = Issue.issue_objects.filter(
        assignees=user, state__group="completed", workspace=workspace
    ).count()
    return {
        "completed_total": completed_total,
        "longest_streak": calendar["longest_streak"],
        "active_days": calendar["active_days"],
    }


def award_badges(profile, stats):
    """Give the member every automatic badge they qualify for and do not have yet. Returns the new slugs."""
    from plane.vj_startups.models.reputation import Badge, MemberBadge

    slugs = earned_badge_slugs(stats)
    if not slugs:
        return []

    have = set(MemberBadge.objects.filter(member=profile, badge__slug__in=slugs).values_list("badge__slug", flat=True))
    new = [slug for slug in slugs if slug not in have]
    rules = {rule.slug: rule for rule in RULES}
    for slug in new:
        rule = rules[slug]
        badge, _ = Badge.objects.get_or_create(slug=slug, defaults={"name": rule.name, "description": rule.description})
        MemberBadge.objects.get_or_create(member=profile, badge=badge)
    return new

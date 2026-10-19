"""
Contribution calendar ("heatmap") for a member's public profile.

Reads straight from Plane's own tables instead of a stored snapshot, so the
calendar can never drift from the real work and needs no sync job. The pure
helpers (levels, streaks, assembling days) take plain dicts and dates so they
are unit-testable without a database.

What counts as one contribution:
  completed - an issue assigned to the member that reached a "completed" state
  created   - an issue the member opened
  comments  - a comment the member wrote on an issue
  pages     - a page the member created

Only counts are ever produced here, never titles, so nothing from a private
project can leak through the calendar.
"""

import datetime
import math
from collections import defaultdict
from zoneinfo import ZoneInfo

KINDS = ("completed", "created", "comments", "pages")
DEFAULT_DAYS = 365
MAX_DAYS = 366
# Days are cut in the club's local time, not UTC: evening work in India would
# otherwise land on the next day.
DEFAULT_TIMEZONE = "Asia/Kolkata"


def level_for(count, max_count):
    """GitHub-style intensity: 0 for none, then 1-4 relative to the busiest day."""
    if count <= 0 or max_count <= 0:
        return 0
    return min(4, max(1, math.ceil(4 * count / max_count)))


def streaks(active_days, today):
    """
    (current, longest) streaks of consecutive active days.

    The current streak survives an empty today if yesterday was active, so a
    member is not shown as "0" every morning before they have done anything.
    """
    active = set(active_days)
    if not active:
        return 0, 0

    longest = 0
    for day in active:
        if day - datetime.timedelta(days=1) in active:
            continue  # not the start of a run
        length = 1
        while day + datetime.timedelta(days=length) in active:
            length += 1
        longest = max(longest, length)

    cursor = today if today in active else today - datetime.timedelta(days=1)
    current = 0
    while cursor in active:
        current += 1
        cursor -= datetime.timedelta(days=1)
    return current, longest


def build_calendar(per_kind, start, end):
    """
    per_kind: {kind: {date: count}}. Returns the activity block of the public profile.

    `days` is sparse (only days with activity) to keep the payload small; the
    client fills the gaps with zeros using `range`.
    """
    totals_by_day = defaultdict(int)
    detail = defaultdict(dict)
    breakdown = {kind: 0 for kind in KINDS}

    for kind in KINDS:
        for day, count in (per_kind.get(kind) or {}).items():
            if not count or day < start or day > end:
                continue
            totals_by_day[day] += count
            detail[day][kind] = count
            breakdown[kind] += count

    max_daily = max(totals_by_day.values(), default=0)
    current, longest = streaks(totals_by_day.keys(), end)

    days = [
        {
            "date": day.isoformat(),
            "count": totals_by_day[day],
            "level": level_for(totals_by_day[day], max_daily),
            **{kind: detail[day].get(kind, 0) for kind in KINDS},
        }
        for day in sorted(totals_by_day)
    ]
    return {
        "range": {"from": start.isoformat(), "to": end.isoformat()},
        "total": sum(totals_by_day.values()),
        "active_days": len(totals_by_day),
        "max_daily": max_daily,
        "current_streak": current,
        "longest_streak": longest,
        "breakdown": breakdown,
        "days": days,
    }


def window(days=DEFAULT_DAYS, tz_name=DEFAULT_TIMEZONE, now=None):
    """(start_date, end_date, tzinfo) for the last `days` days, ending today in the club's timezone."""
    days = max(1, min(int(days), MAX_DAYS))
    tz = ZoneInfo(tz_name)
    today = (now or datetime.datetime.now(tz=datetime.timezone.utc)).astimezone(tz).date()
    return today - datetime.timedelta(days=days - 1), today, tz


def _by_day(queryset, field, start, tz):
    from django.db.models import Count
    from django.db.models.functions import TruncDate

    start_dt = datetime.datetime.combine(start, datetime.time.min, tzinfo=tz)
    rows = (
        queryset.filter(**{f"{field}__gte": start_dt})
        .annotate(day=TruncDate(field, tzinfo=tz))
        .values("day")
        .annotate(n=Count("id"))
    )
    return {row["day"]: row["n"] for row in rows if row["day"]}


def member_calendar(user, workspace, days=DEFAULT_DAYS, tz_name=DEFAULT_TIMEZONE, now=None):
    """Query the four sources for one member in one workspace and build the calendar."""
    from plane.db.models import Issue, IssueComment, Page

    start, end, tz = window(days, tz_name, now)
    in_workspace = {"workspace": workspace}

    completed = Issue.issue_objects.filter(
        assignees=user, state__group="completed", completed_at__isnull=False, **in_workspace
    )
    created = Issue.issue_objects.filter(created_by=user, **in_workspace)
    comments = IssueComment.objects.filter(actor=user, **in_workspace)
    pages = Page.objects.filter(owned_by=user, archived_at__isnull=True, **in_workspace)

    per_kind = {
        "completed": _by_day(completed, "completed_at", start, tz),
        "created": _by_day(created, "created_at", start, tz),
        "comments": _by_day(comments, "created_at", start, tz),
        "pages": _by_day(pages, "created_at", start, tz),
    }
    calendar = build_calendar(per_kind, start, end)
    calendar["timezone"] = tz_name
    return calendar

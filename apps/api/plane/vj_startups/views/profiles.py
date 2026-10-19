"""
Public member profiles (the GitHub-style page on the main site) and the
settings a member uses to control their own.

Privacy rules, enforced here and nowhere else:
  * A profile is only readable by the public when its owner set
    profile_visibility to "public". Anything else (including never having
    chosen) answers 404, indistinguishable from "no such handle".
  * Only fields listed in `public_profile_payload` are ever returned: never an
    email, account id, token, or the title of work in a private project.
"""

from urllib.parse import urlparse

from django.core.cache import cache
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from plane.vj_startups.models.extension import VJProjectExtension
from plane.vj_startups.models.organization import OrganizationMemberProfile
from plane.vj_startups.models.startup import StartupMember
from plane.vj_startups.services import profile_activity, profile_handle
from plane.vj_startups.services.onboarding_service import OnboardingService

VISIBILITY_PUBLIC = "public"
VISIBILITY_PRIVATE = "private"
VISIBILITY_CHOICES = (VISIBILITY_PUBLIC, VISIBILITY_PRIVATE)

# Browsers and the proxy may keep a public profile this long; the calendar is cached server-side too.
CACHE_SECONDS = 300
ACTIVITY_CACHE_SECONDS = 600

MAX_BIO = 1000
MAX_HEADLINE = 255
MAX_SKILLS = 20
MAX_SKILL_LENGTH = 40
RECENT_WORK_LIMIT = 10

LINK_FIELDS = {
    "github_url": ("github.com",),
    "linkedin_url": ("linkedin.com",),
    # Any web address is fine for a portfolio.
    "portfolio_url": None,
}


def is_public(profile):
    return profile.profile_visibility == VISIBILITY_PUBLIC


def display_name(user):
    return (
        f"{user.first_name} {user.last_name}".strip() or user.display_name or user.username
    )


def public_photo(profile):
    """The team-sheet photo wins over the account avatar; only real web addresses, never internal paths."""
    avatar = profile.user.avatar or ""
    return profile.photo_url or (avatar if avatar.startswith("http") else "")


def clean_profile_update(data):
    """
    Validate a member's edit of their own profile.

    Returns (cleaned, errors). Only known fields are accepted; anything else is
    ignored, so a client cannot write role, scores, tokens or wing through here.
    """
    cleaned, errors = {}, {}

    if "handle" in data:
        try:
            cleaned["handle"] = profile_handle.validate_handle(data["handle"])
        except profile_handle.HandleError as exc:
            errors["handle"] = str(exc)

    if "profile_visibility" in data:
        value = (data["profile_visibility"] or "").strip().lower()
        if value in VISIBILITY_CHOICES:
            cleaned["profile_visibility"] = value
        else:
            errors["profile_visibility"] = "Must be 'public' or 'private'."

    for field, limit in (("bio", MAX_BIO), ("headline", MAX_HEADLINE)):
        if field in data:
            text = data[field]
            if not isinstance(text, str):
                errors[field] = "Must be text."
            elif len(text.strip()) > limit:
                errors[field] = f"Must be at most {limit} characters."
            else:
                cleaned[field] = text.strip()

    if "skills" in data:
        skills = data["skills"]
        if not isinstance(skills, list) or not all(isinstance(s, str) for s in skills):
            errors["skills"] = "Must be a list of text values."
        else:
            seen, unique = set(), []
            for skill in (s.strip() for s in skills):
                if skill and skill.lower() not in seen:
                    seen.add(skill.lower())
                    unique.append(skill)
            if len(unique) > MAX_SKILLS or any(len(s) > MAX_SKILL_LENGTH for s in unique):
                errors["skills"] = f"At most {MAX_SKILLS} skills of {MAX_SKILL_LENGTH} characters each."
            else:
                cleaned["skills"] = unique

    for field, hosts in LINK_FIELDS.items():
        if field not in data:
            continue
        value = (data[field] or "").strip() if isinstance(data[field], str) else None
        if value is None:
            errors[field] = "Must be a web address."
        elif value == "":
            cleaned[field] = ""
        else:
            try:
                URLValidator(schemes=["http", "https"])(value)
            except DjangoValidationError:
                errors[field] = "Must be a valid http(s) address."
                continue
            host = (urlparse(value).hostname or "").lower()
            if hosts and not any(host == h or host.endswith("." + h) for h in hosts):
                errors[field] = f"Must be a {hosts[0]} address."
            else:
                cleaned[field] = value

    return cleaned, errors


def _taken(handle, exclude_profile_id=None):
    qs = OrganizationMemberProfile.objects.filter(handle=handle)
    if exclude_profile_id:
        qs = qs.exclude(id=exclude_profile_id)
    return qs.exists()


def own_profile_payload(profile):
    return {
        "handle": profile.handle,
        "profile_visibility": profile.profile_visibility or VISIBILITY_PRIVATE,
        "headline": profile.headline,
        "bio": profile.bio,
        "skills": profile.skills or [],
        "github_url": profile.github_url,
        "linkedin_url": profile.linkedin_url,
        "portfolio_url": profile.portfolio_url,
        "is_public": is_public(profile),
        "public_path": f"/u/{profile.handle}" if profile.handle else None,
    }


def _calendar(profile):
    """Cached: the calendar is the only expensive part and need not be real-time."""
    key = f"vj:profile-activity:{profile.user_id}"
    try:
        cached = cache.get(key)
    except Exception:  # a cache outage must never take the profile page down
        cached = None
    if cached is not None:
        return cached

    workspace = OnboardingService.get_global_workspace()
    if workspace is None:
        calendar = profile_activity.build_calendar({}, *profile_activity.window()[:2])
        calendar["timezone"] = profile_activity.DEFAULT_TIMEZONE
    else:
        calendar = profile_activity.member_calendar(profile.user, workspace)
    try:
        cache.set(key, calendar, ACTIVITY_CACHE_SECONDS)
    except Exception:
        pass
    return calendar


def _recent_work(profile):
    """
    Titles are shown only for work in projects that belong to a startup the
    club has chosen to show publicly. Everything else is counted in the
    calendar but never named.
    """
    from plane.db.models import Issue

    public_projects = VJProjectExtension.objects.filter(startup__public_visibility=True).values("project_id")
    issues = (
        Issue.issue_objects.filter(
            assignees=profile.user,
            state__group="completed",
            completed_at__isnull=False,
            project_id__in=public_projects,
        )
        .select_related("project")
        .order_by("-completed_at")[:RECENT_WORK_LIMIT]
    )
    return [
        {"title": issue.name, "project": issue.project.name, "completed_at": issue.completed_at.isoformat()}
        for issue in issues
    ]


def public_profile_payload(profile):
    user = profile.user
    rank = OrganizationMemberProfile.objects.filter(reputation_score__gt=profile.reputation_score).count() + 1
    startups = [
        {"name": m.startup.name, "slug": m.startup.slug, "role": m.role}
        for m in StartupMember.objects.filter(
            member=profile, left_at__isnull=True, startup__public_visibility=True
        ).select_related("startup")
    ]
    badges = [
        {
            "name": mb.badge.name,
            "slug": mb.badge.slug,
            "description": mb.badge.description,
            "icon_url": mb.badge.icon_url,
            "awarded_at": mb.awarded_at.isoformat(),
        }
        for mb in profile.badges.select_related("badge").order_by("-awarded_at")
    ]
    return {
        "handle": profile.handle,
        "name": display_name(user),
        "headline": profile.headline,
        "bio": profile.bio,
        "photo_url": public_photo(profile),
        "role": profile.role,
        "member_stage": profile.member_stage,
        "is_club_member": profile.is_club_member,
        "wing": {"name": profile.wing.name, "slug": profile.wing.slug} if profile.wing else None,
        "joined_at": profile.joined_at.isoformat(),
        "skills": profile.skills or [],
        "links": {
            "github": profile.github_url,
            "linkedin": profile.linkedin_url,
            "portfolio": profile.portfolio_url,
        },
        "reputation": {
            "score": round(profile.reputation_score, 1),
            "rank": rank,
            "execution": round(profile.execution_score, 1),
            "impact": round(profile.impact_score, 1),
            "leadership": round(profile.leadership_score, 1),
            "learning": round(profile.learning_score, 1),
            "reliability": round(profile.reliability_score, 1),
        },
        "badges": badges,
        "startups": startups,
        "recent_work": _recent_work(profile),
        "activity": _calendar(profile),
    }


class PublicProfileEndpoint(APIView):
    """GET /public/profiles/<handle>/ - the public profile, or 404 unless its owner published it."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, handle, *args, **kwargs):
        profile = (
            OrganizationMemberProfile.objects.select_related("user", "wing")
            .filter(handle=profile_handle.normalize_handle(handle), profile_visibility=VISIBILITY_PUBLIC)
            .first()
        )
        if profile is None:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        response = Response(public_profile_payload(profile))
        response["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
        return response


class MyProfileEndpoint(APIView):
    """GET/PATCH /profile/me/ - a signed-in member reads and edits their own public profile settings."""

    permission_classes = [IsAuthenticated]

    def _profile(self, request):
        profile, _ = OrganizationMemberProfile.objects.get_or_create(user=request.user)
        return profile

    def get(self, request, *args, **kwargs):
        return Response(own_profile_payload(self._profile(request)))

    def patch(self, request, *args, **kwargs):
        profile = self._profile(request)
        cleaned, errors = clean_profile_update(request.data)
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        handle = cleaned.get("handle")
        if handle and _taken(handle, profile.id):
            return Response({"errors": {"handle": "That handle is already taken."}}, status=status.HTTP_409_CONFLICT)

        # Publishing needs an address: pick one from the member's name if they have not chosen yet.
        if cleaned.get("profile_visibility") == VISIBILITY_PUBLIC and not (handle or profile.handle):
            user = request.user
            try:
                cleaned["handle"] = profile_handle.suggest_handle(user.first_name, user.last_name, user.email, _taken)
            except profile_handle.HandleError as exc:
                return Response({"errors": {"handle": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        for field, value in cleaned.items():
            setattr(profile, field, value)
        try:
            profile.save(update_fields=[*cleaned.keys(), "updated_at"] if cleaned else None)
        except IntegrityError:
            # Lost a race for the same handle between the check and the save.
            return Response({"errors": {"handle": "That handle is already taken."}}, status=status.HTTP_409_CONFLICT)

        try:
            cache.delete(f"vj:profile-activity:{profile.user_id}")
        except Exception:
            pass
        return Response(own_profile_payload(profile))


class HandleAvailabilityEndpoint(APIView):
    """GET /profile/handle-available/?handle=x - lets the settings form check as the member types."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        raw = request.query_params.get("handle", "")
        try:
            handle = profile_handle.validate_handle(raw)
        except profile_handle.HandleError as exc:
            return Response({"handle": profile_handle.normalize_handle(raw), "available": False, "reason": str(exc)})
        own = OrganizationMemberProfile.objects.filter(user=request.user).values_list("id", flat=True).first()
        available = profile_handle.is_available(handle, _taken, exclude_profile_id=own)
        return Response(
            {"handle": handle, "available": available, "reason": None if available else "That handle is already taken."}
        )

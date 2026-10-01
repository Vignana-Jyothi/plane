from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from plane.vj_startups.models.organization import OrganizationMemberProfile

# The public site's team page may be cached briefly by browsers and the proxy.
CACHE_SECONDS = 300


def is_master(profile):
    return (profile.role or "").lower().startswith("wing master")


def team_sort_key(profile):
    """Wing masters first, then everyone else; within each group by wing, then by name."""
    return (not is_master(profile), profile.wing.name.lower(), member_name(profile).lower())


def member_name(profile):
    user = profile.user
    return (f"{user.first_name} {user.last_name}".strip() or user.display_name or "").strip()


def serialize_member(profile, order):
    """Public fields only: never the email, phone number, roll number or any account id/token."""
    avatar = profile.user.avatar or ""
    return {
        "name": member_name(profile),
        "wing": profile.wing.name,
        "wing_slug": profile.wing.slug,
        "role": profile.role,
        "is_wing_master": is_master(profile),
        "department_year": profile.headline,
        "linkedin_url": profile.linkedin_url,
        "instagram_url": profile.instagram_url or "",
        "photo_url": profile.photo_url or (avatar if avatar.startswith("http") else ""),
        "order": order,
    }


class PublicTeamEndpoint(APIView):
    """The club team for the public site's team page: everyone listed by the team-sheet import
    (``import_team_members --publish-team``), already in display order. Public, read-only."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        profiles = list(
            OrganizationMemberProfile.objects.filter(is_club_member=True, wing__isnull=False).select_related(
                "user", "wing"
            )
        )
        profiles.sort(key=team_sort_key)
        response = Response([serialize_member(p, order) for order, p in enumerate(profiles, start=1)])
        response["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
        return response

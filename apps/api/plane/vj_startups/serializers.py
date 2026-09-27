from rest_framework import serializers
from plane.vj_startups.models.organization import OrganizationMemberProfile, Wing
from plane.vj_startups.models.startup import Startup, StartupMember
from plane.vj_startups.models.contribution import Contribution, Milestone
from plane.vj_startups.models.reputation import Badge, MemberBadge
from plane.vj_startups.models.event import Event
from plane.vj_startups.models.contribution_snapshot import ContributionSnapshot
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email", "avatar", "username")

class WingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wing
        fields = "__all__"

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = ("id", "title", "description", "type", "achieved_at", "metadata")

class StartupSerializer(serializers.ModelSerializer):
    milestones = MilestoneSerializer(many=True, read_only=True)
    class Meta:
        model = Startup
        fields = "__all__"

class StartupMemberSerializer(serializers.ModelSerializer):
    startup = StartupSerializer(read_only=True)
    class Meta:
        model = StartupMember
        fields = ("id", "role", "joined_at", "left_at", "startup")

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ("id", "name", "slug", "description", "icon_url")

class MemberBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)
    class Meta:
        model = MemberBadge
        fields = ("id", "awarded_at", "badge")

class ContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contribution
        fields = (
            "id", "title", "description", "type", "impact_score", "hours",
            "evidence_url", "created_at", "updated_at",
        )

class OrganizationMemberProfileSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    wing = WingSerializer(read_only=True)
    startup_memberships = StartupMemberSerializer(many=True, read_only=True)
    badges = MemberBadgeSerializer(many=True, read_only=True)
    contributions = ContributionSerializer(many=True, read_only=True)
    
    class Meta:
        model = OrganizationMemberProfile
        fields = "__all__"

class EventSerializer(serializers.ModelSerializer):
    wing_name = serializers.CharField(source="wing.name", read_only=True)
    wing_color = serializers.CharField(source="wing.color", read_only=True)

    class Meta:
        model = Event
        fields = ("id", "title", "status", "scheduled_at", "wing", "wing_name", "wing_color")

class ContributionSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionSnapshot
        fields = "__all__"



# ---------------------------------------------------------------------------
# Public serializers
#
# Every AllowAny endpoint (leaderboards, showcase, public profiles) must use
# these explicit field lists. The model serializers above use "__all__", which
# served the main site's auth tokens (public_admin_token, public_session_token),
# every member's email and the invited_emails lists to anyone who asked.
# Add a field here only if it is fine for the whole internet to read.
# ---------------------------------------------------------------------------


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # username is the public profile slug (/public/members/<username>/).
        fields = ("id", "username", "first_name", "last_name", "display_name", "avatar")


class PublicWingSerializer(serializers.ModelSerializer):
    wing_master = PublicUserSerializer(read_only=True)

    class Meta:
        model = Wing
        fields = ("id", "name", "slug", "description", "color", "icon", "wing_master")


class PublicStartupSerializer(serializers.ModelSerializer):
    milestones = MilestoneSerializer(many=True, read_only=True)

    class Meta:
        model = Startup
        fields = (
            "id", "name", "slug", "tagline", "description", "logo", "cover_image", "website",
            "problem_statement", "solution_statement", "trl_stage", "industry", "founded_date",
            "status", "users", "team_size", "github_url", "pitch_deck_url", "one_pager_url",
            "founders_text", "funding_status", "incorporation_status", "milestones",
        )


class PublicStartupMemberSerializer(serializers.ModelSerializer):
    startup = PublicStartupSerializer(read_only=True)

    class Meta:
        model = StartupMember
        fields = ("id", "role", "joined_at", "left_at", "startup")


class PublicMemberSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)
    wing = PublicWingSerializer(read_only=True)
    startup_memberships = PublicStartupMemberSerializer(many=True, read_only=True)
    badges = MemberBadgeSerializer(many=True, read_only=True)

    class Meta:
        model = OrganizationMemberProfile
        fields = (
            "id", "user", "wing", "role", "headline", "bio", "skills",
            "linkedin_url", "github_url", "portfolio_url", "member_stage", "is_club_member",
            "joined_at", "updated_at",
            "reputation_score", "execution_score", "impact_score", "leadership_score",
            "learning_score", "reliability_score",
            "badges", "startup_memberships",
        )

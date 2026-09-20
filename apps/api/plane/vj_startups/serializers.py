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
        fields = ("id", "title", "description", "type", "impact_score", "hours", "evidence_url", "created_at", "updated_at")

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


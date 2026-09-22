from rest_framework import generics
from rest_framework.permissions import AllowAny
from plane.vj_startups.models.organization import OrganizationMemberProfile, Wing
from plane.vj_startups.models.startup import Startup
from plane.vj_startups.serializers import OrganizationMemberProfileSerializer, StartupSerializer, WingSerializer

class MemberLeaderboardEndpoint(generics.ListAPIView):
    serializer_class = OrganizationMemberProfileSerializer
    permission_classes = [AllowAny] # Publicly accessible for now, could be feature flagged

    def get_queryset(self):
        return OrganizationMemberProfile.objects.order_by('-reputation_score')[:100]

class StartupLeaderboardEndpoint(generics.ListAPIView):
    serializer_class = StartupSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Rank by users acquired or funding
        return Startup.objects.filter(public_visibility=True).order_by('-users')[:100]

class WingLeaderboardEndpoint(generics.ListAPIView):
    serializer_class = WingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Order by whatever metric, for now just name
        return Wing.objects.all()

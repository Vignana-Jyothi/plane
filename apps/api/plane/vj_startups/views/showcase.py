from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from plane.vj_startups.models.startup import Startup
from plane.vj_startups.models.organization import OrganizationMemberProfile
from plane.vj_startups.serializers import StartupSerializer, OrganizationMemberProfileSerializer
from plane.vj_startups.services.metrics import MetricsService

class ShowcaseStartupsEndpoint(generics.ListAPIView):
    serializer_class = StartupSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return Startup.objects.filter(public_visibility=True)

class ShowcaseMetricsEndpoint(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        metrics = MetricsService.get_dashboard_metrics()
        return Response(metrics)

class ShowcaseMembersEndpoint(generics.ListAPIView):
    serializer_class = OrganizationMemberProfileSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return (
            OrganizationMemberProfile.objects.filter(is_club_member=True)
            .select_related('user', 'wing')
            .order_by('-created_at')
        )

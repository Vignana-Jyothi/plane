from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from plane.vj_startups.models.organization import OrganizationMemberProfile
from plane.vj_startups.models.startup import Startup
from plane.vj_startups.serializers import OrganizationMemberProfileSerializer, StartupSerializer

class PublicMemberProfileEndpoint(generics.RetrieveAPIView):
    serializer_class = OrganizationMemberProfileSerializer
    permission_classes = [AllowAny]
    lookup_field = "user__username"

    def get_object(self):
        # We need a slug or username. We'll use user__username or user__id depending on Plane's user model
        # Let's assume slug is provided in URL
        slug = self.kwargs.get("slug")
        return get_object_or_404(OrganizationMemberProfile, user__username=slug)

class PublicStartupProfileEndpoint(generics.RetrieveAPIView):
    serializer_class = StartupSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return Startup.objects.filter(public_visibility=True)

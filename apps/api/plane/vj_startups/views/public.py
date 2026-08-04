from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from plane.vj_startups.models.organization import OrganizationMemberProfile
from plane.vj_startups.models.startup import Startup
from plane.vj_startups.serializers import OrganizationMemberProfileSerializer, StartupSerializer

from rest_framework.response import Response
from rest_framework import status

class PublicMemberProfileEndpoint(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, slug, *args, **kwargs):
        from plane.vj_startups.models.organization import OrganizationMemberProfile
        from plane.vj_startups.models.contribution_snapshot import ContributionSnapshot
        from plane.vj_startups.models.startup import StartupMember
        from django.db.models import Sum

        profile = get_object_or_404(OrganizationMemberProfile.objects.select_related('user', 'wing'), user__username=slug)
        user = profile.user
        
        startups = list(StartupMember.objects.filter(member=profile).values_list('startup__name', flat=True))
        
        snapshots = ContributionSnapshot.objects.filter(user=user)
        issues_closed = snapshots.aggregate(total=Sum('issues_closed'))['total'] or 0
        issues_assigned = snapshots.aggregate(total=Sum('issues_assigned'))['total'] or 0
        points = snapshots.aggregate(total=Sum('points'))['total'] or 0
        
        graph_dict = {}
        for snap in snapshots:
            graph_data = snap.contribution_graph or []
            for item in graph_data:
                d = item.get('date')
                c = item.get('count', 0)
                if d:
                    graph_dict[d] = graph_dict.get(d, 0) + c
                    
        contribution_graph = [{"date": k, "count": v} for k, v in sorted(graph_dict.items())]

        projects = []
        for snap in snapshots:
            projects.append({
                "name": snap.project.name,
                "role": "contributor",
                "issues_closed": snap.issues_closed
            })

        data = {
            "username": user.username,
            "display_name": user.display_name or f"{user.first_name} {user.last_name}".strip() or user.username,
            "is_club_member": profile.is_club_member,
            "wing": profile.wing.name if profile.wing else None,
            "startups": startups,
            "contribution_summary": {
                "issues_closed": issues_closed,
                "issues_assigned": issues_assigned,
                "points": points
            },
            "contribution_graph": contribution_graph,
            "projects": projects
        }
        
        return Response(data, status=status.HTTP_200_OK)

class PublicStartupProfileEndpoint(generics.RetrieveAPIView):
    serializer_class = StartupSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return Startup.objects.filter(public_visibility=True)

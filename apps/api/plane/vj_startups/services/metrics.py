from django.db.models import Sum, Count
from plane.vj_startups.models.organization import OrganizationMemberProfile, Wing
from plane.vj_startups.models.startup import Startup
from plane.vj_startups.models.contribution import Contribution

class MetricsService:
    @staticmethod
    def get_dashboard_metrics():
        total_startups = Startup.objects.count()
        active_startups = Startup.objects.filter(status="active").count()
        funding_raised = Startup.objects.aggregate(Sum('funding_raised'))['funding_raised__sum'] or 0.0
        users_acquired = Startup.objects.aggregate(Sum('users'))['users__sum'] or 0
        total_members = OrganizationMemberProfile.objects.count()

        return {
            "total_startups": total_startups,
            "active_startups": active_startups,
            "funding_raised": float(funding_raised),
            "users_acquired": users_acquired,
            "total_members": total_members,
            "jobs_created": 0, # Could be derived from StartupMember where role != founder
            "deployments": Contribution.objects.filter(type="deployment").count(),
            "internships": 0 # Could be derived from Opportunities
        }

    @staticmethod
    def get_wing_metrics(wing: Wing):
        members = OrganizationMemberProfile.objects.filter(wing=wing)
        total_members = members.count()
        
        # Startups created by members of this wing (as founders)
        startups = Startup.objects.filter(members__member__in=members).distinct().count()
        
        return {
            "wing_name": wing.name,
            "total_members": total_members,
            "startups_associated": startups,
        }

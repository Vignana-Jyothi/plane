from django.db.models import Sum
from plane.vj_startups.models.organization import OrganizationMemberProfile
from plane.vj_startups.models.contribution import Contribution
from plane.db.models import Issue

class ReputationService:
    @staticmethod
    def calculate_reputation(member_profile: OrganizationMemberProfile) -> float:
        """
        Calculates and updates the member's reputation score based on the formula:
        Reputation = 40% execution + 30% impact + 20% leadership + 10% learning
        """
        # Calculate execution score (based on hours/contributions)
        total_hours = Contribution.objects.filter(member=member_profile).aggregate(Sum('hours'))['hours__sum'] or 0.0
        execution_score = min(total_hours * 1.5, 100.0) # Example logic

        # Calculate impact score (based on impact_score of contributions)
        total_impact = Contribution.objects.filter(
            member=member_profile
        ).aggregate(Sum('impact_score'))['impact_score__sum'] or 0.0
        impact_score = min(total_impact * 2.0, 100.0)

        # Calculate leadership score (based on mentorship, ops, etc.)
        leadership_contributions = Contribution.objects.filter(
            member=member_profile, type__in=["mentorship", "operations"]
        ).count()
        leadership_score = min(leadership_contributions * 5.0, 100.0)

        # Calculate learning score (based on research, learning types)
        learning_contributions = Contribution.objects.filter(
            member=member_profile, type__in=["research"]
        ).count()
        learning_score = min(learning_contributions * 5.0, 100.0)

        # Calculate reliability
        completed_issues = Issue.objects.filter(
            assignees__id=member_profile.user.id,
            state__group="completed"
        ).count()
        total_issues = Issue.objects.filter(
            assignees__id=member_profile.user.id
        ).count()
        reliability_score = (completed_issues / total_issues * 100.0) if total_issues > 0 else 100.0

        # Weighted calculation
        reputation = (
            (execution_score * 0.40)
            + (impact_score * 0.30)
            + (leadership_score * 0.20)
            + (learning_score * 0.10)
        )

        # Update member profile
        member_profile.execution_score = execution_score
        member_profile.impact_score = impact_score
        member_profile.leadership_score = leadership_score
        member_profile.learning_score = learning_score
        member_profile.reliability_score = reliability_score
        member_profile.reputation_score = reputation
        member_profile.save()

        return reputation

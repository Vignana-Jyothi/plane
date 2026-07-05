from plane.vj_startups.models.organization import OrganizationMemberProfile
from plane.vj_startups.models.contribution import Contribution

class MemberProgressionService:
    STAGES = [
        "explorer",
        "builder",
        "contributor",
        "founding_team",
        "founder",
        "mentor",
        "partner",
        "legend"
    ]

    @staticmethod
    def evaluate_stage(member_profile: OrganizationMemberProfile) -> str:
        """
        Evaluates the member's stage based on their reputation and contributions.
        Returns the new stage.
        """
        score = member_profile.reputation_score
        contributions_count = Contribution.objects.filter(member=member_profile).count()

        new_stage = "explorer"
        if score >= 90 and contributions_count >= 100:
            new_stage = "legend"
        elif score >= 80 and contributions_count >= 50:
            new_stage = "partner"
        elif score >= 70 and contributions_count >= 30:
            new_stage = "mentor"
        elif score >= 60:
            # Requires explicit manual promotion to founder usually, but keeping it metric-based for now
            new_stage = "founder"
        elif score >= 40 and contributions_count >= 10:
            new_stage = "founding_team"
        elif score >= 20 and contributions_count >= 5:
            new_stage = "contributor"
        elif score >= 10 and contributions_count >= 1:
            new_stage = "builder"

        if member_profile.member_stage != new_stage:
            # We don't downgrade automatically in most cases, but for this MVP we just set it
            current_idx = MemberProgressionService.STAGES.index(member_profile.member_stage)
            new_idx = MemberProgressionService.STAGES.index(new_stage)
            if new_idx > current_idx:
                member_profile.member_stage = new_stage
                member_profile.save()

        return member_profile.member_stage

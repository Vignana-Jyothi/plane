import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate
from plane.db.models import User, Project, Issue, WorkspaceMember
from plane.vj_startups.models.contribution_snapshot import ContributionSnapshot
from plane.vj_startups.models.organization import OrganizationMemberProfile

class Command(BaseCommand):
    help = "Syncs member contribution snapshots and calculates reputation points from Plane issues."

    def handle(self, *args, **options):
        # We target the global VJ Startups workspace
        workspace_slug = "vj-startups"
        members = WorkspaceMember.objects.filter(
            workspace__slug=workspace_slug,
            member__is_bot=False,
            deleted_at__isnull=True
        ).select_related('member')

        self.stdout.write(f"Found {len(members)} active members in workspace '{workspace_slug}'")

        cutoff_date = timezone.now() - datetime.timedelta(days=90)

        for member in members:
            user = member.member
            # Ensure member has a profile
            profile, _ = OrganizationMemberProfile.objects.get_or_create(user=user)

            self.stdout.write(f"Syncing contributions for: {user.email}")

            # Get projects in this workspace
            projects = Project.objects.filter(workspace__slug=workspace_slug, deleted_at__isnull=True)

            for project in projects:
                # Count issues currently assigned
                issues_assigned = Issue.issue_objects.filter(
                    project=project,
                    assignees=user,
                    deleted_at__isnull=True
                ).exclude(state__group__in=["completed", "cancelled"]).count()

                # Count issues closed (completed) in last 90 days
                issues_closed = Issue.issue_objects.filter(
                    project=project,
                    assignees=user,
                    state__group="completed",
                    completed_at__gte=cutoff_date,
                    deleted_at__isnull=True
                ).count()

                # Points formula: closed * 10 + assigned * 2
                points = (issues_closed * 10) + (issues_assigned * 2)

                # Fetch daily completed issue counts for last 90 days to construct the heatmap
                daily_counts = Issue.issue_objects.filter(
                    project=project,
                    assignees=user,
                    state__group="completed",
                    completed_at__gte=cutoff_date,
                    deleted_at__isnull=True
                ).annotate(
                    closed_date=TruncDate('completed_at')
                ).values('closed_date').annotate(
                    count=Count('id')
                ).order_by('closed_date')

                contribution_graph = [
                    {"date": item['closed_date'].strftime('%Y-%m-%d'), "count": item['count']}
                    for item in daily_counts if item['closed_date']
                ]

                # Update or create snapshot
                ContributionSnapshot.objects.update_or_create(
                    user=user,
                    project=project,
                    defaults={
                        "issues_closed": issues_closed,
                        "issues_assigned": issues_assigned,
                        "points": points,
                        "contribution_graph": contribution_graph
                    }
                )

            # Update Member Profile reputation metrics
            # Recalculate reputation score
            from plane.vj_startups.services.reputation import ReputationService
            from plane.vj_startups.services.progression import MemberProgressionService
            ReputationService.calculate_reputation(profile)
            MemberProgressionService.evaluate_stage(profile)

        self.stdout.write(self.style.SUCCESS("Successfully synced contribution snapshots!"))

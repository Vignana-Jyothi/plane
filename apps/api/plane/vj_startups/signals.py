from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from plane.db.models import Issue
from plane.vj_startups.models.startup import Startup
from plane.vj_startups.models.contribution import Milestone
from plane.vj_startups.models.extension import VJProjectExtension
from plane.vj_startups.services.onboarding_service import OnboardingService
from plane.vj_startups.models.organization import Wing, OrganizationMemberProfile

User = get_user_model()

@receiver(post_save, sender=Wing)
def setup_wing_project(sender, instance, created, **kwargs):
    if created:
        OnboardingService.auto_provision_wing(instance)

@receiver(post_save, sender=OrganizationMemberProfile)
def setup_wing_member(sender, instance, created, **kwargs):
    # If the user has a wing assigned, onboard them
    if instance.wing and instance.user:
        OnboardingService.onboard_user_to_wing(instance.user, instance.wing)

@receiver(post_save, sender=Startup)
def setup_startup_project(sender, instance, created, **kwargs):
    if created:
        OnboardingService.auto_provision_startup(instance)

@receiver(post_save, sender=User)
def setup_user_workspace(sender, instance, created, **kwargs):
    if created and not instance.is_bot:
        if OnboardingService.should_auto_onboard(instance):
            OnboardingService.auto_onboard_user(instance)

@receiver(post_save, sender=Issue)
def create_milestone_on_issue_completion(sender, instance, created, **kwargs):
    """
    Listens for Plane Issues being marked as completed.
    If the Issue belongs to a project mapped to a Startup,
    we automatically generate a Milestone for that Startup.
    """
    # Only proceed if the issue has a state and it's completed
    if not instance.state or instance.state.group != "completed":
        return

    # Check if the project is associated with a startup
    try:
        project_ext = VJProjectExtension.objects.select_related('startup').get(project=instance.project)
        startup = project_ext.startup
    except VJProjectExtension.DoesNotExist:
        return

    # To avoid duplicate milestones if an issue is updated multiple times while completed
    # we use the issue ID as metadata to check if it already exists.
    milestone_exists = Milestone.objects.filter(
        startup=startup,
        metadata__issue_id=str(instance.id)
    ).exists()

    if not milestone_exists:
        Milestone.objects.create(
            startup=startup,
            title=instance.name, # Use issue name as milestone title
            description=instance.description_html or "",
            type="task_completion",
            achieved_at=instance.completed_at or timezone.now(),
            metadata={"issue_id": str(instance.id), "url": f"/projects/{instance.project.id}/issues/{instance.id}"}
        )

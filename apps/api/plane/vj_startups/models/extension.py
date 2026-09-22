from django.db import models
from plane.db.models import BaseModel, Project, Issue, Cycle
from plane.vj_startups.models.organization import Wing
from .startup import Startup

class VJProjectExtension(BaseModel):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="vj_extension")
    startup = models.ForeignKey(Startup, on_delete=models.SET_NULL, null=True, blank=True, related_name="projects")
    wing = models.ForeignKey(Wing, on_delete=models.SET_NULL, null=True, blank=True, related_name="projects")

    class Meta:
        verbose_name = "VJ Project Extension"
        verbose_name_plural = "VJ Project Extensions"
        db_table = "vj_project_extensions"

    def __str__(self):
        return f"Extension for Project {self.project.name}"

class VJIssueExtension(BaseModel):
    """
    Links a Plane Issue back to the Startup it belongs to - same OneToOneField
    extension pattern as VJProjectExtension (see vj_startups_upgrade_guide.md),
    used so a startup's Issues can be queried directly without joining through
    Project. Populated by OnboardingService._create_seed_issue_from_idea when
    an Issue is seeded from an Idea.
    """
    issue = models.OneToOneField(Issue, on_delete=models.CASCADE, related_name="vj_extension")
    startup = models.ForeignKey(Startup, on_delete=models.SET_NULL, null=True, blank=True, related_name="issues")

    class Meta:
        verbose_name = "VJ Issue Extension"
        verbose_name_plural = "VJ Issue Extensions"
        db_table = "vj_issue_extensions"

    def __str__(self):
        return f"Extension for Issue {self.issue.name}"

class VJCycleExtension(BaseModel):
    cycle = models.OneToOneField(Cycle, on_delete=models.CASCADE, related_name="vj_extension")
    startup = models.ForeignKey(Startup, on_delete=models.SET_NULL, null=True, blank=True, related_name="cycles")
    quarter = models.CharField(max_length=10, blank=True) # e.g., "Q1 2024"
    objectives = models.TextField(blank=True)
    key_results = models.TextField(blank=True)

    class Meta:
        verbose_name = "VJ Cycle Extension"
        verbose_name_plural = "VJ Cycle Extensions"
        db_table = "vj_cycle_extensions"

    def __str__(self):
        return f"Extension for Cycle {self.cycle.name}"

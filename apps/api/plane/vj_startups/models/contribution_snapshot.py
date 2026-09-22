from django.db import models
from django.conf import settings
from plane.db.models import BaseModel, Project

class ContributionSnapshot(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vj_contribution_snapshots")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="vj_contribution_snapshots")
    issues_closed = models.IntegerField(default=0)
    issues_assigned = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    contribution_graph = models.JSONField(default=list, blank=True)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contribution Snapshot"
        verbose_name_plural = "Contribution Snapshots"
        db_table = "vj_contribution_snapshots"

    def __str__(self):
        return f"{self.user.email} - Project: {self.project.name} - Points: {self.points}"

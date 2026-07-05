from django.db import models
from django.conf import settings
from plane.db.models import BaseModel, Issue, Project
from .organization import OrganizationMemberProfile
from .startup import Startup

class Contribution(BaseModel):
    member = models.ForeignKey(OrganizationMemberProfile, on_delete=models.CASCADE, related_name="contributions")
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name="contributions")
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="vj_contributions")
    issue = models.ForeignKey(Issue, on_delete=models.SET_NULL, null=True, blank=True, related_name="vj_contributions")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=50) # code, design, marketing, etc.
    impact_score = models.FloatField(default=0.0)
    hours = models.FloatField(default=0.0)
    evidence_url = models.URLField(blank=True)
    # created_at is inherited from BaseModel

    class Meta:
        verbose_name = "Contribution"
        verbose_name_plural = "Contributions"
        db_table = "vj_contributions"

    def __str__(self):
        return f"{self.member} - {self.title}"

class Milestone(BaseModel):
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name="milestones")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=50) # first_customer, mvp_launched, etc.
    achieved_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Milestone"
        verbose_name_plural = "Milestones"
        db_table = "vj_milestones"

    def __str__(self):
        return f"{self.startup.name} - {self.title}"

class Opportunity(BaseModel):
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name="opportunities", null=True, blank=True)
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=50) # grant, competition, etc.
    description = models.TextField(blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    external_url = models.URLField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="vj_opportunities_created"
    )

    class Meta:
        verbose_name = "Opportunity"
        verbose_name_plural = "Opportunities"
        db_table = "vj_opportunities"

    def __str__(self):
        return self.title

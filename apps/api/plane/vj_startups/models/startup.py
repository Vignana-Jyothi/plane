from django.db import models
from django.conf import settings
from plane.db.models import BaseModel
from .organization import OrganizationMemberProfile

class Startup(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    logo = models.URLField(blank=True)
    website = models.URLField(blank=True)
    tagline = models.CharField(max_length=255, blank=True)
    problem_statement = models.TextField(blank=True)
    solution_statement = models.TextField(blank=True)
    trl_stage = models.IntegerField(default=1)
    industry = models.CharField(max_length=100, blank=True)
    founded_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, default="active")
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    users = models.IntegerField(default=0)
    funding_raised = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    team_size = models.IntegerField(default=1)
    github_url = models.URLField(blank=True)
    pitch_deck_url = models.URLField(blank=True)
    public_visibility = models.BooleanField(default=False)
    invited_emails = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = "Startup"
        verbose_name_plural = "Startups"
        db_table = "vj_startups"

    def __str__(self):
        return self.name

class StartupMember(BaseModel):
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name="members")
    member = models.ForeignKey(OrganizationMemberProfile, on_delete=models.CASCADE, related_name="startup_memberships")
    role = models.CharField(max_length=255)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    equity_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Startup Member"
        verbose_name_plural = "Startup Members"
        db_table = "vj_startup_members"

    def __str__(self):
        return f"{self.member} - {self.startup.name}"

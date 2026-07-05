from django.db import models
from django.conf import settings
from plane.db.models import BaseModel

class Wing(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, blank=True)
    icon = models.CharField(max_length=255, blank=True)
    wing_master = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_wings"
    )
    invited_emails = models.JSONField(default=list)

    class Meta:
        verbose_name = "Wing"
        verbose_name_plural = "Wings"
        db_table = "vj_wings"

    def __str__(self):
        return self.name

class OrganizationMemberProfile(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vj_profile"
    )
    bio = models.TextField(blank=True)
    headline = models.CharField(max_length=255, blank=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    skills = models.JSONField(default=list)
    wing = models.ForeignKey(
        Wing,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members"
    )
    member_stage = models.CharField(max_length=50, default="explorer")
    execution_score = models.FloatField(default=0.0)
    impact_score = models.FloatField(default=0.0)
    leadership_score = models.FloatField(default=0.0)
    learning_score = models.FloatField(default=0.0)
    reliability_score = models.FloatField(default=0.0)
    reputation_score = models.FloatField(default=0.0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Organization Member Profile"
        verbose_name_plural = "Organization Member Profiles"
        db_table = "vj_organization_member_profiles"

    def __str__(self):
        return f"{self.user.email}'s Profile"

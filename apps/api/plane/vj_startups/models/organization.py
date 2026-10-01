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
    class PublicRole(models.TextChoices):
        USER = "USER", "User"
        STUDENT = "STUDENT", "Student"
        WING_MEMBER = "WING_MEMBER", "Wing Member"
        WING_MASTER = "WING_MASTER", "Wing Master"
        ADMIN = "ADMIN", "Admin"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vj_profile"
    )
    bio = models.TextField(blank=True)
    headline = models.CharField(max_length=255, blank=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    # Nullable on purpose: the public site's backend (Prisma) writes to this table too, and a
    # NOT NULL column without a database default would break its inserts.
    instagram_url = models.URLField(max_length=200, null=True, blank=True)
    # A directly loadable image URL for the public team page (set from the team sheet).
    photo_url = models.URLField(max_length=500, null=True, blank=True)
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
    is_club_member = models.BooleanField(default=False)
    role = models.CharField(max_length=255, default="Member")
    execution_score = models.FloatField(default=0.0)
    impact_score = models.FloatField(default=0.0)
    leadership_score = models.FloatField(default=0.0)
    learning_score = models.FloatField(default=0.0)
    reliability_score = models.FloatField(default=0.0)
    reputation_score = models.FloatField(default=0.0)
    joined_at = models.DateTimeField(auto_now_add=True)

    # Merged from the vjstartups-main-website (public site) User model. This is
    # the public site's own permission level (who can verify problems/ideas,
    # promote others, post announcements) - a separate concept from Plane's own
    # workspace roles/InstanceAdmin, not a replacement for them.
    public_role = models.CharField(max_length=20, choices=PublicRole.choices, default=PublicRole.STUDENT)
    public_admin_token = models.CharField(max_length=255, null=True, blank=True, unique=True)
    public_admin_token_created_at = models.DateTimeField(null=True, blank=True)
    public_session_token = models.CharField(max_length=255, null=True, blank=True, unique=True)
    public_session_token_created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Organization Member Profile"
        verbose_name_plural = "Organization Member Profiles"
        db_table = "vj_organization_member_profiles"

    def __str__(self):
        return f"{self.user.email}'s Profile"

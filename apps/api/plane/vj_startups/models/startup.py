from django.db import models
from plane.db.models import BaseModel
from .organization import OrganizationMemberProfile

class Startup(BaseModel):
    class FundingStatus(models.TextChoices):
        BOOTSTRAPPED = "BOOTSTRAPPED", "Bootstrapped"
        SEEKING_FUNDING = "SEEKING_FUNDING", "Seeking Funding"
        PRE_SEED = "PRE_SEED", "Pre-Seed"
        SEED = "SEED", "Seed"
        SERIES_A = "SERIES_A", "Series A"
        LATER_STAGE = "LATER_STAGE", "Later Stage"

    class IncorporationStatus(models.TextChoices):
        NOT_INCORPORATED = "NOT_INCORPORATED", "Not Incorporated"
        INCORPORATED = "INCORPORATED", "Incorporated"
        LLC = "LLC", "LLC"
        PARTNERSHIP = "PARTNERSHIP", "Partnership"
        OTHER = "OTHER", "Other"

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    logo = models.URLField(blank=True)
    cover_image = models.URLField(blank=True)
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
    one_pager_url = models.URLField(blank=True)
    public_visibility = models.BooleanField(default=False)
    invited_emails = models.JSONField(default=list, blank=True)

    # Merged from the vjstartups-main-website (public site) Startup model.
    # free-text fallback where no linked StartupMember exists yet
    founders_text = models.CharField(max_length=500, blank=True)
    funding_status = models.CharField(max_length=30, choices=FundingStatus.choices, blank=True)
    incorporation_status = models.CharField(max_length=30, choices=IncorporationStatus.choices, blank=True)
    # free-text revenue/funding detail that doesn't fit the structured decimal fields
    financial_notes = models.TextField(blank=True)
    customers = models.CharField(max_length=255, blank=True)
    markets = models.CharField(max_length=255, blank=True)
    business_model = models.TextField(blank=True)
    key_features = models.JSONField(default=list, blank=True)
    technology_stack = models.JSONField(default=list, blank=True)
    market_size = models.CharField(max_length=255, blank=True)
    annual_growth_rate = models.CharField(max_length=100, blank=True)
    target_users = models.TextField(blank=True)
    target_audience = models.TextField(blank=True)
    competitive_advantage = models.TextField(blank=True)
    upvotes = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    # soft reference to backend2's Idea.ideaId - Idea stays a Prisma-only model
    related_idea_id = models.CharField(max_length=255, null=True, blank=True, unique=True)

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

class StartupTeamMember(BaseModel):
    """A team member shown on a startup's public page who may not have a
    registered platform account (and therefore no OrganizationMemberProfile) -
    distinct from StartupMember, which is real operational membership."""
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name="team_members")
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    avatar = models.URLField(blank=True)

    class Meta:
        verbose_name = "Startup Team Member"
        verbose_name_plural = "Startup Team Members"
        db_table = "vj_startup_team_members"

    def __str__(self):
        return f"{self.name} ({self.role}) - {self.startup.name}"

class StartupSupportProgram(BaseModel):
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name="support_programs")
    program = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Startup Support Program"
        verbose_name_plural = "Startup Support Programs"
        db_table = "vj_startup_support_programs"

    def __str__(self):
        return f"{self.program} - {self.startup.name}"

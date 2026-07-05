from django.db import models
from plane.db.models import BaseModel
from .organization import OrganizationMemberProfile

class Badge(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    icon_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Badge"
        verbose_name_plural = "Badges"
        db_table = "vj_badges"

    def __str__(self):
        return self.name

class MemberBadge(BaseModel):
    member = models.ForeignKey(OrganizationMemberProfile, on_delete=models.CASCADE, related_name="badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="awarded_to")
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Member Badge"
        verbose_name_plural = "Member Badges"
        db_table = "vj_member_badges"
        unique_together = ("member", "badge")

    def __str__(self):
        return f"{self.member} - {self.badge.name}"

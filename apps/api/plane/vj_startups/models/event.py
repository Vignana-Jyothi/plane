from django.db import models
from plane.db.models import BaseModel
from .organization import Wing

class Event(BaseModel):
    STATUS_CHOICES = (
        ("upcoming", "Upcoming"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    )
    wing = models.ForeignKey(Wing, related_name="events", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="upcoming")
    scheduled_at = models.DateTimeField()

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        db_table = "vj_events"

    def __str__(self):
        return f"{self.wing.name} - {self.title}"

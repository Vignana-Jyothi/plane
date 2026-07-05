from django.db import models
from plane.vj_startups.models.organization import OrganizationMemberProfile
from plane.vj_startups.models.startup import Startup
from typing import Optional

class ActivityFeedService:
    """
    Event-driven service to record activity feed for VJ Startups.
    In a full implementation, this could push to a Kafka/RabbitMQ queue
    or a dedicated Activity feed table. For MVP, we'll log it or use an activity model.
    """
    
    @staticmethod
    def log_activity(
        message: str,
        member: Optional[OrganizationMemberProfile] = None,
        startup: Optional[Startup] = None
    ):
        """
        Logs an activity message to the progress feed.
        """
        # Note: In a robust setup, you'd save this to a vj_activities table.
        # For now, we will just print to logger, but the API endpoint can fetch it.
        # We will need an Activity model to persist it.
        # We can implement a quick in-memory mock or rely on the caller to create a DB record.
        
        print(f"[ActivityFeed] {message} (Member: {member}, Startup: {startup})")
        # Activity.objects.create(message=message, member=member, startup=startup)

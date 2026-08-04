from django.urls import path
from .views import (
    MemberLeaderboardEndpoint,
    StartupLeaderboardEndpoint,
    WingLeaderboardEndpoint,
    PublicMemberProfileEndpoint,
    PublicStartupProfileEndpoint,
    ShowcaseStartupsEndpoint,
    ShowcaseMetricsEndpoint,
    ShowcaseMembersEndpoint
)
from .views.admin import (
    AdminStartupEndpoint,
    AdminStartupsMetricsEndpoint,
    AdminStartupDetailEndpoint,
    AdminStartupInviteEndpoint,
    AdminWingEndpoint,
    AdminWingDetailEndpoint,
    AdminWingsMetricsEndpoint,
    AdminWingInviteEndpoint,
    AdminWingMembersEndpoint,
    AdminWingRemoveMemberEndpoint,
    AdminEventEndpoint,
    AdminEventDetailEndpoint,
    AdminClubMemberEndpoint,
    AdminClubMemberDetailEndpoint
)
from .views.bot import BotProxyEndpoint

urlpatterns = [
    # Admin
    path("admin/startups/", AdminStartupEndpoint.as_view(), name="admin-startups"),
    path("admin/startups/<str:slug>/", AdminStartupDetailEndpoint.as_view(), name="admin-startup-detail"),
    path("admin/startups/<str:slug>/invite/", AdminStartupInviteEndpoint.as_view(), name="admin-startup-invite"),
    path("admin/wings/", AdminWingEndpoint.as_view(), name="admin-wings"),
    path("admin/wings/metrics/", AdminWingsMetricsEndpoint.as_view(), name="admin-wings-metrics"),
    path("admin/wings/<str:slug>/", AdminWingDetailEndpoint.as_view(), name="admin-wing-detail"),
    path("admin/wings/<str:slug>/members/", AdminWingMembersEndpoint.as_view(), name="admin-wing-members"),
    path("admin/wings/<str:slug>/members/<uuid:user_id>/", AdminWingRemoveMemberEndpoint.as_view(), name="admin-wing-remove-member"),
    path("admin/wings/<str:slug>/invite/", AdminWingInviteEndpoint.as_view(), name="admin-wing-invite"),
    path("admin/metrics/", AdminStartupsMetricsEndpoint.as_view(), name="admin-metrics"),
    path("admin/events/", AdminEventEndpoint.as_view(), name="admin-events"),
    path("admin/events/<uuid:pk>/", AdminEventDetailEndpoint.as_view(), name="admin-event-detail"),
    path("admin/members/", AdminClubMemberEndpoint.as_view(), name="admin-club-members"),
    path("admin/members/<uuid:pk>/", AdminClubMemberDetailEndpoint.as_view(), name="admin-club-member-detail"),

    # Discord Bot Proxy
    path("bot/proxy/", BotProxyEndpoint.as_view(), name="bot-proxy"),

    # Leaderboards
    path("leaderboards/members/", MemberLeaderboardEndpoint.as_view(), name="leaderboard-members"),
    path("leaderboards/startups/", StartupLeaderboardEndpoint.as_view(), name="leaderboard-startups"),
    path("leaderboards/wings/", WingLeaderboardEndpoint.as_view(), name="leaderboard-wings"),

    # Public Profiles
    path("public/members/<str:slug>/", PublicMemberProfileEndpoint.as_view(), name="public-member-profile"),
    path("public/startups/<str:slug>/", PublicStartupProfileEndpoint.as_view(), name="public-startup-profile"),

    # Showcase
    path("showcase/startups/", ShowcaseStartupsEndpoint.as_view(), name="showcase-startups"),
    path("showcase/metrics/", ShowcaseMetricsEndpoint.as_view(), name="showcase-metrics"),
    path("showcase/members/", ShowcaseMembersEndpoint.as_view(), name="showcase-members"),
]

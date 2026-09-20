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
    AdminClubMemberDetailEndpoint,
    AdminMicroserviceIdeasProxyEndpoint,
    AdminMicroserviceProblemsProxyEndpoint,
    AdminMicroserviceUsersProxyEndpoint,
    AdminMicroserviceUserDetailProxyEndpoint,
    AdminMicroserviceProblemVerifyProxyEndpoint,
    AdminMicroserviceIdeaVerifyProxyEndpoint
)
from .views.bot import BotProxyEndpoint
from .views.public_auth import PublicSiteUpsertUserEndpoint

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

    # Microservice proxy routes
    path("admin/microservice/ideas/", AdminMicroserviceIdeasProxyEndpoint.as_view(), name="admin-microservice-ideas"),
    path("admin/microservice/problems/", AdminMicroserviceProblemsProxyEndpoint.as_view(), name="admin-microservice-problems"),
    path("admin/microservice/users/", AdminMicroserviceUsersProxyEndpoint.as_view(), name="admin-microservice-users"),
    path("admin/microservice/users/<str:pk>/", AdminMicroserviceUserDetailProxyEndpoint.as_view(), name="admin-microservice-user-detail"),
    path("admin/microservice/problems/<str:pk>/verify/", AdminMicroserviceProblemVerifyProxyEndpoint.as_view(), name="admin-microservice-problem-verify"),
    path("admin/microservice/ideas/<str:pk>/verify/", AdminMicroserviceIdeaVerifyProxyEndpoint.as_view(), name="admin-microservice-idea-verify"),

    # Discord Bot Proxy
    path("bot/proxy/", BotProxyEndpoint.as_view(), name="bot-proxy"),

    # Public site (vjstartups-main-website) internal auth bridge
    path("public-auth/upsert-user/", PublicSiteUpsertUserEndpoint.as_view(), name="public-auth-upsert-user"),

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

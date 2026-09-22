import os
import uuid

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

import requests

from plane.db.models import User
from plane.vj_startups.models.organization import OrganizationMemberProfile
from plane.vj_startups.models.extension import VJProjectExtension
from plane.vj_startups.models.startup import Startup
from plane.vj_startups.services.onboarding_service import OnboardingService

THIRTY_DAYS_SECONDS = 60 * 60 * 24 * 30
TOKEN_ROLES = {
    OrganizationMemberProfile.PublicRole.ADMIN,
    OrganizationMemberProfile.PublicRole.WING_MEMBER,
    OrganizationMemberProfile.PublicRole.WING_MASTER,
}


class PublicSiteUpsertUserEndpoint(APIView):
    """
    Server-to-server only - called by the public site's Express backend after
    IT has already verified the caller's Google ID token. Protected by a
    shared secret (PUBLIC_SITE_INTERNAL_TOKEN header), never by a user
    session, and must never be reachable directly from a browser.

    This is the only place public-site login creates a Django User: doing it
    here (rather than from Prisma) means it goes through the same shape
    Django's own signup uses and correctly fires the post_save onboarding
    signal (workspace membership, etc). Role changes and token
    issuance/rotation on an *existing* OrganizationMemberProfile are simple
    enough that the public site updates them directly via Prisma afterwards -
    only user creation needs to cross into Django.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        expected_token = os.environ.get("PUBLIC_SITE_INTERNAL_TOKEN")
        provided_token = request.headers.get("X-Internal-Token")
        if not expected_token or provided_token != expected_token:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        email = (request.data.get("email") or "").strip().lower()
        if not email:
            return Response({"error": "email is required"}, status=status.HTTP_400_BAD_REQUEST)

        first_name = request.data.get("first_name") or ""
        last_name = request.data.get("last_name") or ""
        picture = request.data.get("picture") or ""
        should_be_admin = bool(request.data.get("should_be_admin"))

        user = User.objects.filter(email=email).first()
        if not user:
            user = User(email=email, username=uuid.uuid4().hex)
            user.set_password(uuid.uuid4().hex)
            user.is_password_autoset = True
            user.is_email_verified = True
            user.first_name = first_name
            user.last_name = last_name
            if picture:
                user.avatar = picture
            user.save()  # fires post_save -> auto_onboard_user (if eligible)
        else:
            update_fields = []
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                update_fields.append("first_name")
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                update_fields.append("last_name")
            if picture and user.avatar != picture:
                user.avatar = picture
                update_fields.append("avatar")
            if update_fields:
                user.save(update_fields=update_fields)

        profile, _ = OrganizationMemberProfile.objects.get_or_create(user=user)

        # Promote to ADMIN if the caller's ADMIN_EMAILS says this email should
        # be one; never silently demote an existing elevated role here.
        if should_be_admin and profile.public_role != OrganizationMemberProfile.PublicRole.ADMIN:
            profile.public_role = OrganizationMemberProfile.PublicRole.ADMIN

        now = timezone.now()

        def is_valid(token, created_at):
            return bool(token) and (not created_at or (now - created_at).total_seconds() <= THIRTY_DAYS_SECONDS)

        # Every logged-in user gets a session token, any role.
        if not is_valid(profile.public_session_token, profile.public_session_token_created_at):
            profile.public_session_token = str(uuid.uuid4())
            profile.public_session_token_created_at = now

        # Only token-eligible roles get an admin token (matches verifierAuth).
        if profile.public_role in TOKEN_ROLES:
            if not is_valid(profile.public_admin_token, profile.public_admin_token_created_at):
                profile.public_admin_token = str(uuid.uuid4())
                profile.public_admin_token_created_at = now
        else:
            profile.public_admin_token = None
            profile.public_admin_token_created_at = None

        profile.save()

        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "avatar": user.avatar,
                "public_role": profile.public_role,
                "public_session_token": profile.public_session_token,
                "public_admin_token": profile.public_admin_token,
            },
            status=status.HTTP_200_OK,
        )


class InternalProvisionStartupEndpoint(APIView):
    """
    Server-to-server only, same shared-secret model as
    PublicSiteUpsertUserEndpoint above. Called by backend 2 right after it
    creates a Startup row (Prisma writes directly into Django's vj_startups
    table - see the header comment in backend/prisma/schema.prisma - so
    Django's own post_save signal on Startup, which normally provisions the
    Plane project, never fires for that path). This is the only way a
    publicly-submitted startup (vjstartup.com's own startup form) ever gets
    a Plane project; startups created through the admin panel already get
    one automatically via the signal and don't need this endpoint at all.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        expected_token = os.environ.get("PUBLIC_SITE_INTERNAL_TOKEN")
        provided_token = request.headers.get("X-Internal-Token")
        if not expected_token or provided_token != expected_token:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        startup_id = request.data.get("startup_id")
        if not startup_id:
            return Response({"error": "startup_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        startup = Startup.objects.filter(id=startup_id).first()
        if not startup:
            return Response({"error": "Startup not found"}, status=status.HTTP_404_NOT_FOUND)

        existing = VJProjectExtension.objects.filter(startup=startup).select_related("project").first()
        if existing:
            return Response(
                {
                    "already_provisioned": True,
                    "project_id": str(existing.project_id),
                    "project_identifier": existing.project.identifier,
                },
                status=status.HTTP_200_OK,
            )

        project = OnboardingService.auto_provision_startup(startup)

        return Response(
            {
                "already_provisioned": False,
                "project_id": str(project.id),
                "project_identifier": project.identifier,
            },
            status=status.HTTP_201_CREATED,
        )


class DiagnoseMicroserviceProxyEndpoint(APIView):
    """
    TEMPORARY - for diagnosing the admin proxy's persistent 401 in production
    without needing server shell access. Reports this container's actual
    runtime config (never the token value itself) and makes the real proxied
    call to backend 2, returning its raw status/body. Protected by the same
    shared secret as the other internal endpoints - remove once the 401 is
    resolved and confirmed fixed.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        expected_token = os.environ.get("PUBLIC_SITE_INTERNAL_TOKEN")
        provided_token = request.headers.get("X-Internal-Token")
        if not expected_token or provided_token != expected_token:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        base_url = (
            os.environ.get("VJ_MICROSERVICE_URL")
            or os.environ.get("NEXT_PUBLIC_MICROSERVICE_URL")
            or "http://localhost:6220"
        )
        internal_token = os.environ.get("PUBLIC_SITE_INTERNAL_TOKEN")
        acting_email = request.query_params.get("email", "admin@vnrvjiet.in")

        result = {
            "config": {
                "VJ_MICROSERVICE_URL_env": os.environ.get("VJ_MICROSERVICE_URL"),
                "NEXT_PUBLIC_MICROSERVICE_URL_env": os.environ.get("NEXT_PUBLIC_MICROSERVICE_URL"),
                "resolved_base_url": base_url,
                "PUBLIC_SITE_INTERNAL_TOKEN_set": bool(internal_token),
                "PUBLIC_SITE_INTERNAL_TOKEN_length": len(internal_token) if internal_token else 0,
            }
        }

        try:
            res = requests.get(
                f"{base_url}/admin-api/problems?page=1&limit=1",
                headers={
                    "X-Internal-Token": internal_token or "",
                    "X-Acting-Admin-Email": acting_email,
                    "Content-Type": "application/json",
                },
                timeout=8,
            )
            result["proxy_call"] = {
                "url": f"{base_url}/admin-api/problems?page=1&limit=1",
                "status_code": res.status_code,
                "content_type": res.headers.get("content-type"),
                "body_preview": res.text[:500],
            }
        except Exception as e:
            result["proxy_call"] = {
                "url": f"{base_url}/admin-api/problems?page=1&limit=1",
                "error": f"{type(e).__name__}: {str(e)}",
            }

        return Response(result, status=status.HTTP_200_OK)

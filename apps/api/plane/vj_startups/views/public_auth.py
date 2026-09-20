import os
import uuid

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from plane.db.models import User
from plane.vj_startups.models.organization import OrganizationMemberProfile

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

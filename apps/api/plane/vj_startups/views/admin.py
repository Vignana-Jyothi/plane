from rest_framework import generics, status, serializers
from rest_framework.response import Response
from django.utils.text import slugify
from django.utils import timezone
import datetime
from plane.vj_startups.models.startup import Startup
from plane.vj_startups.models.organization import Wing, OrganizationMemberProfile
from plane.vj_startups.models.event import Event
from plane.vj_startups.serializers import StartupSerializer, EventSerializer, OrganizationMemberProfileSerializer
from plane.license.api.permissions.instance import InstanceAdminPermission
from plane.authentication.session import BaseSessionAuthentication

class WingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wing
        fields = '__all__'

class AdminWingEndpoint(generics.ListCreateAPIView):
    queryset = Wing.objects.all().order_by('-created_at')
    serializer_class = WingSerializer
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if "name" in data and not data.get("slug"):
            base_slug = slugify(data["name"])
            slug = base_slug
            counter = 1
            while Wing.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            data["slug"] = slug
            
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class AdminWingDetailEndpoint(generics.RetrieveUpdateDestroyAPIView):
    queryset = Wing.objects.all()
    serializer_class = WingSerializer
    lookup_field = 'slug'
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        data = request.data.copy()
        wing_master_email = data.pop('wing_master_email', None)
        
        if wing_master_email:
            from django.contrib.auth import get_user_model
            from plane.vj_startups.services.onboarding_service import OnboardingService
            User = get_user_model()
            
            # Resolve email to user
            user = User.objects.filter(email=wing_master_email).first()
            if user:
                data['wing_master'] = user.id
                # Ensure they are onboarded to the wing
                OnboardingService.onboard_user_to_wing(user, instance, role=20)
            else:
                return Response({"error": f"No user found with email {wing_master_email}"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class AdminWingInviteEndpoint(generics.GenericAPIView):
    queryset = Wing.objects.all()
    lookup_field = 'slug'
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

    def post(self, request, *args, **kwargs):
        try:
            wing = self.get_object()
            emails = request.data.get('emails', [])
            if isinstance(emails, str):
                emails = [e.strip() for e in emails.split(",") if e.strip()]
                
            if not emails:
                return Response({"error": "No emails provided"}, status=status.HTTP_400_BAD_REQUEST)

            current_emails = set(wing.invited_emails or [])
            new_emails = set(emails) - current_emails
            
            from django.contrib.auth import get_user_model
            from plane.vj_startups.services.onboarding_service import OnboardingService
            User = get_user_model()
            
            registered_users = User.objects.filter(email__in=emails)
            for user in registered_users:
                from plane.vj_startups.models.organization import OrganizationMemberProfile
                profile, _ = OrganizationMemberProfile.objects.get_or_create(user=user)
                if profile.wing != wing:
                    profile.wing = wing
                    profile.save(update_fields=['wing'])
                OnboardingService.onboard_user_to_wing(user, wing, role=15)

            if not new_emails:
                return Response({"message": f"Processed {len(emails)} emails. Users instantly onboarded."}, status=status.HTTP_200_OK)
                
            if wing.invited_emails is None:
                wing.invited_emails = []
                
            wing.invited_emails.extend(list(new_emails))
            wing.save(update_fields=['invited_emails'])

            return Response({"message": f"Invited {len(new_emails)} member(s)."}, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            return Response({"error": f"Exception: {str(e)}", "trace": traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminWingMembersEndpoint(generics.GenericAPIView):
    queryset = Wing.objects.all()
    lookup_field = 'slug'
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

    def get(self, request, *args, **kwargs):
        wing = self.get_object()
        from plane.vj_startups.models.organization import OrganizationMemberProfile
        
        profiles = OrganizationMemberProfile.objects.filter(wing=wing).select_related('user')
        
        members_data = []
        for profile in profiles:
            is_master = False
            if wing.wing_master_id and profile.user_id == wing.wing_master_id:
                is_master = True
                
            members_data.append({
                "id": profile.user.id,
                "email": profile.user.email,
                "first_name": profile.user.first_name,
                "last_name": profile.user.last_name,
                "role": "Wing Master" if is_master else "Member",
                "joined_at": profile.joined_at,
            })
            
        return Response(members_data, status=status.HTTP_200_OK)

class AdminWingRemoveMemberEndpoint(generics.GenericAPIView):
    queryset = Wing.objects.all()
    lookup_field = 'slug'
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

    def delete(self, request, *args, **kwargs):
        wing = self.get_object()
        user_id = kwargs.get('user_id')
        
        from django.contrib.auth import get_user_model
        from plane.vj_startups.models.organization import OrganizationMemberProfile
        from plane.vj_startups.models.extension import VJProjectExtension
        from plane.db.models import ProjectMember
        User = get_user_model()
        
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
        # 1. Remove wing from profile
        profile = OrganizationMemberProfile.objects.filter(user=user, wing=wing).first()
        if profile:
            profile.wing = None
            profile.save(update_fields=['wing'])
            
        # 2. If Wing Master, remove them
        if wing.wing_master_id == user.id:
            wing.wing_master = None
            wing.save(update_fields=['wing_master'])
            
        # 3. Remove from Wing's Plane Project
        ext = VJProjectExtension.objects.filter(wing=wing).select_related('project').first()
        if ext and ext.project:
            ProjectMember.objects.filter(project=ext.project, member=user).delete()
            
        return Response({"message": "Member removed successfully"}, status=status.HTTP_200_OK)

class AdminWingsMetricsEndpoint(generics.GenericAPIView):
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

    def get(self, request, *args, **kwargs):
        active_wings = Wing.objects.count()
        total_events = Event.objects.count()
        
        if active_wings > 0:
            completed_events_last_30d = Event.objects.filter(
                status="completed",
                scheduled_at__gte=timezone.now() - datetime.timedelta(days=30)
            ).count()
            in_progress_events = Event.objects.filter(status="in_progress").count()
            score = (completed_events_last_30d * 3 + in_progress_events * 1) / active_wings
            engagement_score = f"{int(round(score))}%"
        else:
            engagement_score = "–"
            
        return Response({
            "active_wings": active_wings,
            "total_events": total_events,
            "engagement_score": engagement_score
        }, status=status.HTTP_200_OK)


class AdminStartupEndpoint(generics.ListCreateAPIView):
    queryset = Startup.objects.all().order_by('-created_at')
    serializer_class = StartupSerializer
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        
        # Auto-generate slug from name if not provided
        if "name" in data and not data.get("slug"):
            base_slug = slugify(data["name"])
            slug = base_slug
            counter = 1
            while Startup.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            data["slug"] = slug

        # Ensure invited_emails is correctly parsed if sent as comma-separated string
        emails = data.get("invited_emails", [])
        if isinstance(emails, str):
            data["invited_emails"] = [e.strip() for e in emails.split(",") if e.strip()]

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class AdminStartupDetailEndpoint(generics.RetrieveUpdateDestroyAPIView):
    queryset = Startup.objects.all()
    serializer_class = StartupSerializer
    lookup_field = 'slug'
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

    def perform_update(self, serializer):
        import os
        import requests
        instance = serializer.save()
        try:
            base_url = os.environ.get("VJ_MICROSERVICE_URL") or os.environ.get("NEXT_PUBLIC_MICROSERVICE_URL") or "http://localhost:6220"
            token = os.environ.get("VJ_MICROSERVICE_ADMIN_TOKEN")
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            requests.patch(f"{base_url}/admin-api/startups/{instance.id}/stage", json={"stage": instance.trl_stage}, headers=headers, timeout=2)
        except Exception as e:
            print("Failed to sync stage update to microservice:", e)

    def perform_destroy(self, instance):
        from plane.vj_startups.models.extension import VJProjectExtension
        # Find associated project and delete it first
        try:
            ext = VJProjectExtension.objects.get(startup=instance)
            if ext.project:
                ext.project.delete()
        except VJProjectExtension.DoesNotExist:
            pass
        # Now delete the startup
        instance.delete()

class AdminStartupInviteEndpoint(generics.GenericAPIView):
    queryset = Startup.objects.all()
    lookup_field = 'slug'
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

    def post(self, request, *args, **kwargs):
        try:
            startup = self.get_object()
            emails = request.data.get('emails', [])
            if isinstance(emails, str):
                emails = [e.strip() for e in emails.split(",") if e.strip()]

            if not emails:
                return Response({"error": "No emails provided"}, status=status.HTTP_400_BAD_REQUEST)

            # Append unique emails to startup
            current_emails = set(startup.invited_emails or [])
            new_emails = set(emails) - current_emails

            # Try to instantly onboard any registered users (even if previously invited)
            from django.contrib.auth import get_user_model
            from plane.vj_startups.services.onboarding_service import OnboardingService
            User = get_user_model()

            registered_users = User.objects.filter(email__in=emails)
            for user in registered_users:
                OnboardingService.onboard_user_to_startup(user, startup, role=15)

            if not new_emails:
                return Response({"message": f"Processed {len(emails)} emails. Users instantly onboarded."}, status=status.HTTP_200_OK)

            if startup.invited_emails is None:
                startup.invited_emails = []

            startup.invited_emails.extend(list(new_emails))
            startup.save(update_fields=['invited_emails'])

            return Response({"message": f"Invited {len(new_emails)} member(s)."}, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            return Response({"error": f"Exception: {str(e)}", "trace": traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminStartupsMetricsEndpoint(generics.GenericAPIView):
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

    def get(self, request, *args, **kwargs):
        from plane.vj_startups.models.startup import Startup, StartupMember
        from django.contrib.auth import get_user_model
        from django.db.models import Sum
        
        User = get_user_model()
        
        total_startups = Startup.objects.count()
        active_members = StartupMember.objects.count()
        funding_raised = Startup.objects.aggregate(total=Sum('funding_raised'))['total'] or 0.0
        total_users = User.objects.count()

        return Response({
            "total_startups": total_startups,
            "active_members": active_members,
            "funding_raised": float(funding_raised),
            "total_users": total_users,
        }, status=status.HTTP_200_OK)

class AdminEventEndpoint(generics.ListCreateAPIView):
    queryset = Event.objects.all().order_by('-scheduled_at')
    serializer_class = EventSerializer
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            statuses = status_param.split(',')
            queryset = queryset.filter(status__in=statuses)
        return queryset

class AdminEventDetailEndpoint(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

class AdminClubMemberEndpoint(generics.ListCreateAPIView):
    queryset = OrganizationMemberProfile.objects.all().select_related('user', 'wing').order_by('-created_at')
    serializer_class = OrganizationMemberProfileSerializer
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

    def create(self, request, *args, **kwargs):
        from django.contrib.auth import get_user_model
        from plane.vj_startups.models.organization import OrganizationMemberProfile, Wing
        from plane.vj_startups.serializers import OrganizationMemberProfileSerializer
        from django.db import transaction
        from django.utils.text import slugify

        User = get_user_model()
        email = request.data.get("email", "").strip().lower()
        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()
        role = request.data.get("role", "Member").strip()
        wing_id = request.data.get("wing")
        is_club_member = request.data.get("is_club_member", False)
        
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

       # Auto-upload a photo URL if provided
        avatar = request.data.get("avatar") or ""

        with transaction.atomic():
            username = email.split('@')[0]
            base_username = slugify(username) or "user"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exclude(email=email).exists():
                username = f"{base_username}-{counter}"
                counter += 1

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "avatar": avatar,
                    "is_active": True,
                }
            )
            
            if created:
                user.set_unusable_password()
                user.save()
            else:
                if first_name:
                    user.first_name = first_name
                if last_name:
                    user.last_name = last_name
                if avatar:
                    user.avatar = avatar
                user.save()

            from plane.vj_startups.services.onboarding_service import OnboardingService
            OnboardingService.auto_onboard_user(user)

            profile, _ = OrganizationMemberProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.is_club_member = is_club_member
            
            if wing_id:
                wing = Wing.objects.filter(id=wing_id).first()
                if wing:
                    profile.wing = wing
            else:
                profile.wing = None

            profile.save()

        serializer = OrganizationMemberProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class AdminClubMemberDetailEndpoint(generics.RetrieveUpdateDestroyAPIView):
    queryset = OrganizationMemberProfile.objects.all()
    serializer_class = OrganizationMemberProfileSerializer
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        data = request.data
        
        user_data = data.get("user")
        if user_data and isinstance(user_data, dict):
            user = profile.user
            if "first_name" in user_data:
                user.first_name = user_data["first_name"]
            if "last_name" in user_data:
                user.last_name = user_data["last_name"]
            if "avatar" in user_data:
                user.avatar = user_data["avatar"] or ""
            user.save()

        if "role" in data:
            profile.role = data["role"]

        if "is_club_member" in data:
            profile.is_club_member = data["is_club_member"]

        if "wing" in data:
            wing_id = data["wing"]
            if wing_id:
                from plane.vj_startups.models.organization import Wing
                wing = Wing.objects.filter(id=wing_id).first()
                if wing:
                    profile.wing = wing
            else:
                profile.wing = None

        profile.save()
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


import os
import requests
from rest_framework.views import APIView

class AdminMicroserviceProxyBase(APIView):
    authentication_classes = [BaseSessionAuthentication]
    permission_classes = [InstanceAdminPermission]

    def get_microservice_base_url(self):
        return os.environ.get("VJ_MICROSERVICE_URL") or os.environ.get("NEXT_PUBLIC_MICROSERVICE_URL") or "http://localhost:6220"

    def get_microservice_url(self, path):
        return f"{self.get_microservice_base_url()}/admin-api{path}"

    def get_headers(self):
        # Forward the real acting admin's identity, authenticated by the same
        # shared secret the public-auth upsert bridge already requires
        # (PUBLIC_SITE_INTERNAL_TOKEN here == PLANE_INTERNAL_TOKEN on backend
        # 2 - see public_auth.py). BaseSessionAuthentication +
        # InstanceAdminPermission have already confirmed self.request.user is
        # a real, currently-logged-in Instance Admin by the time this runs.
        # backend 2's internalProxyAuth.js validates the token and looks up
        # this email itself - never trust a client-supplied identity without
        # the shared secret backing it.
        #
        # This replaced forwarding one specific admin's own publicAdminToken,
        # which attributed every write made through this proxy - by any
        # admin - to whichever single account that token belonged to.
        headers = {"Content-Type": "application/json"}
        internal_token = os.environ.get("PUBLIC_SITE_INTERNAL_TOKEN")
        if internal_token:
            headers["X-Internal-Token"] = internal_token
            headers["X-Acting-Admin-Email"] = self.request.user.email
        return headers

class AdminMicroserviceIdeasProxyEndpoint(AdminMicroserviceProxyBase):
    def get(self, request):
        page = request.query_params.get("page", 1)
        limit = request.query_params.get("limit", 20)
        search = request.query_params.get("search", "")
        url = self.get_microservice_url(f"/ideas?page={page}&limit={limit}&search={search}")
        try:
            res = requests.get(url, headers=self.get_headers(), timeout=5)
            return Response(res.json(), status=res.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminMicroserviceProblemsProxyEndpoint(AdminMicroserviceProxyBase):
    def get(self, request):
        page = request.query_params.get("page", 1)
        limit = request.query_params.get("limit", 20)
        search = request.query_params.get("search", "")
        url = self.get_microservice_url(f"/problems?page={page}&limit={limit}&search={search}")
        try:
            res = requests.get(url, headers=self.get_headers(), timeout=5)
            return Response(res.json(), status=res.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminMicroserviceUsersProxyEndpoint(AdminMicroserviceProxyBase):
    def get(self, request):
        page = request.query_params.get("page", 1)
        limit = request.query_params.get("limit", 20)
        search = request.query_params.get("search", "")
        url = self.get_microservice_url(f"/users?page={page}&limit={limit}&search={search}")
        try:
            res = requests.get(url, headers=self.get_headers(), timeout=5)
            return Response(res.json(), status=res.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminMicroserviceUserDetailProxyEndpoint(AdminMicroserviceProxyBase):
    def patch(self, request, pk):
        url = self.get_microservice_url(f"/users/{pk}/role")
        try:
            res = requests.patch(url, json=request.data, headers=self.get_headers(), timeout=5)
            return Response(res.json(), status=res.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        url = self.get_microservice_url(f"/users/{pk}")
        try:
            res = requests.delete(url, headers=self.get_headers(), timeout=5)
            return Response(res.json(), status=res.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminMicroserviceProblemVerifyProxyEndpoint(AdminMicroserviceProxyBase):
    """
    Talent Wing's daily approve/reject action (Plan of Action SOP: "Talent Wing
    logs into vjos.vjstartup.com and filters for pending triage tickets...
    If approved, set review status to approved"). Proxies to backend-2's
    verifierAuth-gated /problem-api/problem/:id/verify|unverify.
    """
    def patch(self, request, pk):
        action = "verify" if request.data.get("verified", True) else "unverify"
        url = f"{self.get_microservice_base_url()}/problem-api/problem/{pk}/{action}"
        try:
            res = requests.patch(
                url,
                json={"verificationNotes": request.data.get("verificationNotes", "")},
                headers=self.get_headers(),
                timeout=5,
            )
            return Response(res.json(), status=res.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminMicroserviceIdeaVerifyProxyEndpoint(AdminMicroserviceProxyBase):
    """Same as AdminMicroserviceProblemVerifyProxyEndpoint, for ideas."""
    def patch(self, request, pk):
        action = "verify" if request.data.get("verified", True) else "unverify"
        url = f"{self.get_microservice_base_url()}/idea-api/idea/{pk}/{action}"
        try:
            res = requests.patch(
                url,
                json={"verificationNotes": request.data.get("verificationNotes", "")},
                headers=self.get_headers(),
                timeout=5,
            )
            return Response(res.json(), status=res.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


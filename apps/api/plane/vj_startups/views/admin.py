from rest_framework import generics, status, serializers
from rest_framework.response import Response
from django.utils.text import slugify
from plane.vj_startups.models.startup import Startup
from plane.vj_startups.models.organization import Wing
from plane.vj_startups.serializers import StartupSerializer
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
        # Count active wings
        active_wings = Wing.objects.count()
        
        # Zeroed out until we configure actual event tracking logic
        total_events = 0
        engagement_score = 0
        
        return Response({
            "active_wings": active_wings,
            "total_events": total_events,
            "engagement_score": f"{engagement_score}%"
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
            from plane.vj_startups.models.organization import OrganizationMemberProfile
            from plane.vj_startups.models.startup import StartupMember
            profile, _ = OrganizationMemberProfile.objects.get_or_create(user=user)
            StartupMember.objects.get_or_create(user=user, startup=startup, defaults={'role': 'Member'})
            OnboardingService.onboard_user_to_startup(user, startup, role=15)

        if not new_emails:
            return Response({"message": f"Processed {len(emails)} emails. Users instantly onboarded."}, status=status.HTTP_200_OK)
            
        if startup.invited_emails is None:
            startup.invited_emails = []
            
        startup.invited_emails.extend(list(new_emails))
        startup.save(update_fields=['invited_emails'])

        return Response({"message": f"Invited {len(new_emails)} member(s)."}, status=status.HTTP_200_OK)

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

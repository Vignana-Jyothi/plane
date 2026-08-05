import string
import random
from django.db import transaction
from django.contrib.auth import get_user_model
from plane.db.models import Workspace, WorkspaceMember, Project, ProjectMember
from plane.vj_startups.models.startup import Startup, StartupMember
from plane.vj_startups.models.organization import OrganizationMemberProfile
from plane.vj_startups.models.extension import VJProjectExtension

User = get_user_model()

class OnboardingService:
    WORKSPACE_NAME = "VJ Startups"
    WORKSPACE_SLUG = "vj-startups"
    COMMON_PROJECT_NAME = "General"

    @classmethod
    def get_or_create_global_workspace(cls):
        # We need an owner for the workspace. We'll pick the first superuser or create a dummy one if none exists.
        # In a real app, a specific admin user would own the "General" workspace.
        owner = User.objects.filter(is_superuser=True).first()
        if not owner:
            owner = User.objects.order_by('created_at').first()
            
        workspace, created = Workspace.objects.get_or_create(
            slug=cls.WORKSPACE_SLUG,
            defaults={
                "name": cls.WORKSPACE_NAME,
                "owner": owner
            }
        )
        if created and owner:
            WorkspaceMember.objects.get_or_create(
                workspace=workspace,
                member=owner,
                defaults={"role": 20} # Admin role
            )
        return workspace

    @classmethod
    def get_or_create_common_project(cls, workspace):
        identifier = "COMMON"
        project, created = Project.objects.get_or_create(
            workspace=workspace,
            identifier=identifier,
            defaults={
                "name": cls.COMMON_PROJECT_NAME,
                "network": 2, # Public within workspace
                "description": "Global project for all VJ Startups members"
            }
        )
        return project

    @classmethod
    def _generate_project_identifier(cls, name: str) -> str:
        # Plane identifier must be 1-12 chars, uppercase, alphanumeric
        base = "".join([c.upper() for c in name if c.isalnum()])
        if not base:
            base = "STARTUP"
        identifier = base[:12]
        
        # Ensure uniqueness
        original = identifier
        counter = 1
        while Project.objects.filter(identifier=identifier).exists():
            suffix = str(counter)
            identifier = f"{original[:12 - len(suffix)]}{suffix}"
            counter += 1
            
        return identifier

    @classmethod
    def _generate_project_name(cls, workspace, base_name: str) -> str:
        name = base_name
        counter = 1
        while Project.objects.filter(workspace=workspace, name=name, deleted_at__isnull=True).exists():
            name = f"{base_name} {counter}"
            counter += 1
        return name

    @classmethod
    @transaction.atomic
    def auto_provision_startup(cls, startup: Startup):
        """Called when a Startup is created."""
        workspace = cls.get_or_create_global_workspace()
        
        # Create Project
        identifier = cls._generate_project_identifier(startup.name)
        project_name = cls._generate_project_name(workspace, startup.name)
        project = Project.objects.create(
            workspace=workspace,
            name=project_name,
            identifier=identifier,
            description=startup.description,
            network=0 # Secret/Private by default
        )
        
        # Map Project to Startup
        VJProjectExtension.objects.create(
            project=project,
            startup=startup
        )
        
        # Determine users to immediately onboard
        users_to_onboard = []
        if startup.created_by:
            users_to_onboard.append(startup.created_by)
            
        if startup.invited_emails:
            existing_users = User.objects.filter(email__in=startup.invited_emails)
            users_to_onboard.extend(existing_users)
            
        # Deduplicate users
        users_to_onboard = list(set(users_to_onboard))
        
        common_project = cls.get_or_create_common_project(workspace)
        
        for user in users_to_onboard:
            # Add to Workspace
            WorkspaceMember.objects.get_or_create(
                workspace=workspace,
                member=user,
                defaults={"role": 15} # Member role, or 20 for creator? Keep it simple: 15
            )
            
            # Add to Startup Project
            ProjectMember.objects.get_or_create(
                workspace=workspace,
                project=project,
                member=user,
                defaults={"role": 20} # Founders get Admin role in their own startup
            )
            
            # Add to Common Project
            ProjectMember.objects.get_or_create(
                workspace=workspace,
                project=common_project,
                member=user,
                defaults={"role": 15}
            )
            
            # Create Profile and StartupMember for invited emails
            if user.email and user.email in startup.invited_emails:
                profile, _ = OrganizationMemberProfile.objects.get_or_create(user=user)
                StartupMember.objects.get_or_create(
                    startup=startup,
                    member=profile,
                    defaults={"role": "Founder/Member"}
                )

        return project

    @classmethod
    @transaction.atomic
    def auto_provision_wing(cls, wing):
        """Called when a Wing is created."""
        from plane.vj_startups.models.organization import Wing
        workspace = cls.get_or_create_global_workspace()
        
        identifier = cls._generate_project_identifier(wing.name)
        project_name = cls._generate_project_name(workspace, wing.name)
        project = Project.objects.create(
            workspace=workspace,
            name=project_name,
            identifier=identifier,
            description=wing.description,
            network=0 # Secret/Private by default
        )
        
        VJProjectExtension.objects.create(
            project=project,
            wing=wing
        )
        
        # Grant wing master Admin access
        if wing.wing_master:
            cls.onboard_user_to_wing(wing.wing_master, wing, role=20)
            
        return project

    @classmethod
    @transaction.atomic
    def onboard_user_to_wing(cls, user, wing, role=15):
        """Called when a user is assigned to a Wing."""
        workspace = cls.get_or_create_global_workspace()
        
        # If this is the Wing Master for the Vision Wing, escalate their Workspace role
        workspace_role = 20 if role == 20 and "vision" in wing.slug.lower() else 15
        
        # Add to Workspace
        wm, created = WorkspaceMember.objects.get_or_create(
            workspace=workspace,
            member=user,
            defaults={"role": workspace_role}
        )
        if not created and wm.role < workspace_role:
            wm.role = workspace_role
            wm.save(update_fields=['role'])
        
        # Add to Common Project
        common_project = cls.get_or_create_common_project(workspace)
        ProjectMember.objects.get_or_create(
            workspace=workspace,
            project=common_project,
            member=user,
            defaults={"role": 15}
        )
        
        # Add to Wing Project
        ext = VJProjectExtension.objects.filter(wing=wing).select_related('project').first()
        if ext and ext.project:
            ProjectMember.objects.get_or_create(
                workspace=workspace,
                project=ext.project,
                member=user,
                defaults={"role": role}
            )

    @classmethod
    @transaction.atomic
    def auto_onboard_user(cls, user: User):
        """Called when a new User is created."""
        workspace = cls.get_or_create_global_workspace()
        
        # 1. Add to Workspace
        WorkspaceMember.objects.get_or_create(
            workspace=workspace,
            member=user,
            defaults={"role": 15} # Member role
        )
        
        # 2. Add to Common Project
        common_project = cls.get_or_create_common_project(workspace)
        ProjectMember.objects.get_or_create(
            workspace=workspace,
            project=common_project,
            member=user,
            defaults={"role": 15}
        )
        
        # 3. Create or get Member Profile
        profile, _ = OrganizationMemberProfile.objects.get_or_create(
            user=user
        )

        # 3.1 Update Plane's native Profile onboarding state to skip wizard
        from plane.db.models import Profile
        plane_profile, _ = Profile.objects.get_or_create(user=user)
        plane_profile.is_onboarded = True
        plane_profile.onboarding_step = {
            "profile_complete": True,
            "workspace_join": True,
            "workspace_create": True,
            "workspace_invite": True
        }
        plane_profile.last_workspace_id = workspace.id
        plane_profile.save()
        
        # 4. Check invited emails for Startups
        if not user.email:
            return
            
        # We need to find Startups where user.email is in the invited_emails list.
        # Since invited_emails is a JSONField, we can filter using contains or iter.
        # For simplicity and cross-db compatibility (SQLite/PG), we can fetch all and check in Python, 
        # or use JSONField __contains. Plane uses PG.
        startups = Startup.objects.filter(invited_emails__contains=[user.email])
        
        for startup in startups:
            # Find the linked Project
            ext = VJProjectExtension.objects.filter(startup=startup).select_related('project').first()
            if ext and ext.project:
                # Add user to Startup's Plane Project
                ProjectMember.objects.get_or_create(
                    workspace=workspace,
                    project=ext.project,
                    member=user,
                    defaults={"role": 15} # Member
                )
                
            # Create StartupMember record
            StartupMember.objects.get_or_create(
                startup=startup,
                member=profile,
                defaults={"role": "Founder/Member"}
            )
            
        # 5. Check invited emails for Wings
        from plane.vj_startups.models.organization import Wing
        wings = Wing.objects.filter(invited_emails__contains=[user.email])
        
        for wing in wings:
            if not profile.wing:
                profile.wing = wing
                profile.save(update_fields=['wing'])
            cls.onboard_user_to_wing(user, wing, role=15)

    @classmethod
    def should_auto_onboard(cls, user: User) -> bool:
        """Determines if a newly registered user should be auto-onboarded to the global VJ Startups workspace."""
        if not user.email:
            return False

        # 1. Superusers and staff are always auto-onboarded
        if user.is_superuser or user.is_staff:
            return True

        email_lower = user.email.lower()
        
        # 2. Institutional domain check (e.g. @vnrvjiet.in)
        if email_lower.endswith("@vnrvjiet.in"):
            return True

        # 3. Check if explicitly invited to any Startup
        if Startup.objects.filter(invited_emails__contains=[user.email]).exists():
            return True

        # 4. Check if explicitly invited to any Wing
        from plane.vj_startups.models.organization import Wing
        if Wing.objects.filter(invited_emails__contains=[user.email]).exists():
            return True

        return False

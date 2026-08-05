import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plane.settings.local")
django.setup()

from django.contrib.auth import get_user_model
from plane.vj_startups.models.startup import Startup, StartupMember
from plane.vj_startups.models.organization import OrganizationMemberProfile
from plane.db.models import Workspace, WorkspaceMember, Project, ProjectMember

User = get_user_model()

print("Creating dummy superuser if not exists...")
su, _ = User.objects.get_or_create(email="admin@vjstartups.com", username="admin_vj")
su.is_superuser = True
su.save()

print("Creating test startup...")
startup, _ = Startup.objects.get_or_create(name="Alpha Test", slug="alpha-test")
startup.invited_emails = ["founder@alpha.com"]
startup.save()

print("Creating new user 'founder@alpha.com'...")
user, created = User.objects.get_or_create(email="founder@alpha.com", username="founder_alpha")
if not created:
    # Delete and recreate to trigger post_save properly for testing
    user.delete()
    user = User.objects.create(email="founder@alpha.com", username="founder_alpha")

print("Validating Workspace and Project memberships...")
general_ws = Workspace.objects.filter(slug="vj-startups").first()
if general_ws:
    print("✅ General workspace (vj-startups) created successfully.")
else:
    print("❌ General workspace (vj-startups) missing.")

common_proj = Project.objects.filter(name="General").first()
if common_proj:
    print("✅ General common project created successfully.")
else:
    print("❌ General common project missing.")

# Check if user is in Common project
common_member = ProjectMember.objects.filter(member=user, project=common_proj).exists()
if common_member:
    print("✅ User added to Club Common project.")
else:
    print("❌ User missing from Club Common project.")

# Check if Startup project was created
startup_proj = Project.objects.filter(name="Alpha Test").first()
if startup_proj:
    print("✅ Startup Project created successfully.")
    
    # Check if user is in Startup project
    startup_member = ProjectMember.objects.filter(member=user, project=startup_proj).exists()
    if startup_member:
        print("✅ User added to Startup Project.")
    else:
        print("❌ User missing from Startup Project.")
else:
    print("❌ Startup Project missing.")

# Check StartupMember
sm = StartupMember.objects.filter(member__user=user, startup=startup).exists()
if sm:
    print("✅ StartupMember profile created successfully.")
else:
    print("❌ StartupMember profile missing.")

print("Test complete.")

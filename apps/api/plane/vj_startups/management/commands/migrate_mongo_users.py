import json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from plane.vj_startups.models.organization import OrganizationMemberProfile
from plane.vj_startups.services.onboarding_service import OnboardingService

User = get_user_model()

class Command(BaseCommand):
    help = "Migrates user accounts from MongoDB (or a JSON dump) to Plane Postgres."

    def add_arguments(self, parser):
        parser.add_argument('--mongo-uri', type=str, help='MongoDB connection URI')
        parser.add_argument('--json-file', type=str, help='Path to JSON dump of MongoDB users collection')
        parser.add_argument('--dry-run', action='store_true', help='Print migration plan without writing to DB')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        mongo_uri = options.get('mongo_uri')
        json_file = options.get('json_file')

        users_data = []

        if json_file:
            self.stdout.write(f"Reading user data from JSON file: {json_file}")
            try:
                with open(json_file, 'r') as f:
                    content = f.read().strip()
                    if content.startswith('['):
                        users_data = json.loads(content)
                    else:
                        users_data = [json.loads(line) for line in content.split('\n') if line.strip()]
            except Exception as e:
                self.stderr.write(f"Failed to read JSON file: {str(e)}")
                return
        elif mongo_uri:
            self.stdout.write("Connecting to MongoDB...")
            try:
                import pymongo
            except ImportError:
                self.stderr.write(
                    "Error: pymongo library is not installed. Run 'pip install pymongo' or use --json-file instead."
                )
                return

            try:
                client = pymongo.MongoClient(mongo_uri)
                db = client.get_default_database()
                if db is None or db.name == 'admin':
                    db = client['vjstartup']
                collection = db['users']
                users_data = list(collection.find())
                self.stdout.write(f"Fetched {len(users_data)} users from MongoDB.")
            except Exception as e:
                self.stderr.write(f"Failed to connect to MongoDB: {str(e)}")
                return
        else:
            self.stderr.write("Error: Please provide either --mongo-uri or --json-file.")
            return

        self.stdout.write(f"Processing {len(users_data)} user records...")

        success_count = 0
        skipped_count = 0

        for doc in users_data:
            email = doc.get('email', '').strip().lower()
            if not email:
                self.stdout.write(self.style.WARNING("Skipping record with no email"))
                skipped_count += 1
                continue

            name = doc.get('name', '').strip()
            picture = doc.get('picture', '').strip()
            role = doc.get('role', 'user').strip()
            
            # Split name
            parts = name.split(' ', 1)
            first_name = parts[0] if len(parts) > 0 else ""
            last_name = parts[1] if len(parts) > 1 else ""

            # Generate unique username
            username = email.split('@')[0]
            base_username = slugify(username) or "user"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exclude(email=email).exists():
                username = f"{base_username}-{counter}"
                counter += 1

            if dry_run:
                self.stdout.write(f"[Dry Run] Would migrate: {email} ({name}) -> username: {username}, role: {role}")
                success_count += 1
                continue

            try:
                with transaction.atomic():
                    # Create or retrieve user
                    user, created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            "username": username,
                            "first_name": first_name,
                            "last_name": last_name,
                            "avatar": picture,
                            "is_active": True,
                        }
                    )
                    
                    if created:
                        user.set_unusable_password()
                        user.save()
                        self.stdout.write(f"Created new user: {email}")
                    else:
                        self.stdout.write(f"User already exists, updating: {email}")
                        user.first_name = first_name or user.first_name
                        user.last_name = last_name or user.last_name
                        user.avatar = picture or user.avatar
                        user.save()

                    # Onboard them to the workspace & common project
                    OnboardingService.auto_onboard_user(user)

                    # Update profile
                    profile = OrganizationMemberProfile.objects.get(user=user)
                    profile.is_club_member = (role == 'admin' or doc.get('is_club_member', False))
                    profile.save()

                    success_count += 1
            except Exception as e:
                self.stderr.write(f"Failed to migrate user {email}: {str(e)}")
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Migration completed. Success: {success_count}, Skipped/Failed: {skipped_count}"
        ))

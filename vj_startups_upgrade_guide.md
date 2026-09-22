# VJ Startups OS - Developer & Upgrade Guide

## Architecture Overview

VJ Startups OS is integrated into Plane as an isolated Django application (`apps/api/plane/vj_startups`). This pattern was chosen specifically to minimize friction when upgrading Plane to future upstream open-source releases.

### Key Principles
1. **No Core Model Modifications**: Instead of altering Plane's core `Project`, `Issue`, or `Cycle` models directly (which would lead to complex migration conflicts), we use `OneToOneField` extensions (`VJProjectExtension`, `VJIssueExtension`, `VJCycleExtension`).
2. **Dedicated App**: All API views, serializers, models, and services live in `vj_startups`.
3. **Environment Flags**: Features can be toggled using `VITE_ENABLE_VJ_STARTUPS` and related `.env` flags.

## How to Upgrade Plane Upstream

Because of the decoupled architecture, upgrading Plane is safe and straightforward:

1. **Fetch Upstream**: `git fetch upstream`
2. **Merge Upstream**: `git merge upstream/master`
3. **Resolve Conflicts (if any)**: The only files modified in the core are:
   - `apps/api/plane/settings/common.py` (added `plane.vj_startups` to `INSTALLED_APPS`)
   - `apps/api/plane/urls.py` (added `api/vj-startups/` to `urlpatterns`)
   These conflicts are trivial to resolve. Just ensure the `vj_startups` entries remain.
4. **Apply Migrations**: `docker compose exec api python manage.py migrate`

## Development Guide

### Adding New Domain Models
If you need to track new VJ Startups entities:
1. Create the model in `apps/api/plane/vj_startups/models/`.
2. Ensure it is imported in `apps/api/plane/vj_startups/models/__init__.py`.
3. Generate migrations: `docker compose exec api python manage.py makemigrations vj_startups`.
4. Apply migrations: `docker compose exec api python manage.py migrate vj_startups`.

### Testing
To run tests for the `vj_startups` app:
```bash
docker compose -f docker-compose-test.yml run --rm api-tests pytest apps/api/plane/vj_startups/
```

### Seeding Data
If you drop the database and need to populate the default Wings, Badges, and setup config, run:
```bash
docker compose -f docker-compose-local.yml exec api python manage.py seed_vj_startups
```

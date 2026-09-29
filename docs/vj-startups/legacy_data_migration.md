# Legacy data migration: team members, problems and ideas

Fills the new Postgres database from what the currently deployed site (`www.vjstartup.com`, the
old MongoDB backend) already holds. Run on the machine that runs Plane and backend 2
(`dev-ai`, `103.248.208.119`) and use `--dry-run` first every time - dry runs write nothing.

Two containers are involved. Find their names once:

```bash
docker ps --format '{{.Names}}   {{.Image}}'
```

- `API_CONTAINER` - Plane's Django API (has `manage.py`).
- `BACKEND_CONTAINER` - backend 2's Express container (has `scripts/`, port 6220).

The scripts only exist in the containers after both repos have deployed the PRs that add them.

## Part A - team members (wings, roles, headline, LinkedIn)

Source: the "VJ Startups Team" sheet exported as CSV (File > Download > CSV). Phone numbers and
roll numbers are never read into the database. People are matched by email; rows with no email
are listed and skipped.

1. Put the CSV into the API container:

   ```bash
   docker cp "VJ Startups Team - Details.csv" API_CONTAINER:/tmp/team.csv
   ```

2. Dry run - read the summary and the skipped lists:

   ```bash
   docker exec -it API_CONTAINER python manage.py import_team_members --csv-file /tmp/team.csv --create-missing --dry-run
   ```

3. Apply:

   ```bash
   docker exec -it API_CONTAINER python manage.py import_team_members --csv-file /tmp/team.csv --create-missing
   ```

Options:

- `--create-missing` creates a Plane account for sheet emails that have none yet (they sign in
  with Google later and land on the same account). Without it, only existing accounts are updated.
- `--set-public-roles` also gives wing masters/members the public-site verifier role (they can
  approve problems and ideas). Off by default; never changes an existing ADMIN.
- Safe to re-run. Existing headline/LinkedIn values are kept; wing and role follow the sheet.
- After this, run `grant_wing_project_access` (see the wing access steps) so members see the
  workspace projects.

## Part B - problems and ideas

Order matters: people first (the tables link to users), then problems, then ideas.

1. Download everything from the live site's public API (read-only):

   ```bash
   docker exec -it BACKEND_CONTAINER node scripts/fetch-legacy-public-data.js --out /tmp/legacy
   ```

   It prints the counts (331 problems and 8 ideas at the time of writing) and warns if the
   number downloaded does not match what the site reports.

2. List the people who need accounts (authors, upvoters, commenters):

   ```bash
   docker exec -it BACKEND_CONTAINER node scripts/extract-legacy-users.js --problems /tmp/legacy/problems.json --ideas /tmp/legacy/ideas.json --out /tmp/legacy/users.json
   ```

3. Move the files across (the two containers do not share a filesystem):

   ```bash
   docker cp BACKEND_CONTAINER:/tmp/legacy /tmp/legacy
   docker cp /tmp/legacy/users.json API_CONTAINER:/tmp/users.json
   ```

4. Create the accounts - dry run, then apply. This also adds each person to the workspace and
   common project, exactly as a first Google sign-in would:

   ```bash
   docker exec -it API_CONTAINER python manage.py migrate_mongo_users --json-file /tmp/users.json --dry-run
   docker exec -it API_CONTAINER python manage.py migrate_mongo_users --json-file /tmp/users.json
   ```

5. Import problems and ideas - dry run first. It must report `without: 0` people; if not, it
   lists the missing emails - create them and re-run:

   ```bash
   docker exec -it BACKEND_CONTAINER node scripts/import-legacy-mongo.js --problems /tmp/legacy/problems.json --ideas /tmp/legacy/ideas.json --dry-run
   docker exec -it BACKEND_CONTAINER node scripts/import-legacy-mongo.js --problems /tmp/legacy/problems.json --ideas /tmp/legacy/ideas.json
   ```

6. Check: Plane admin > VJ Startups > Ecosystem Problems / Ideas should now list the records.

Notes:

- The importer is idempotent (upserts on the legacy `problemId` / `ideaId`), so a failed run can
  simply be repeated. Original ids are preserved, so existing links keep working.
- Legacy records carry no verified flag (none were verified), so all imported items start as
  Pending in the admin panel.
- Delete `/tmp/legacy` and `/tmp/users.json` afterwards - they contain email addresses.
- These scripts read the public list API. If the old MongoDB is ever exported directly, pass the
  `mongoexport` JSON to `import-legacy-mongo.js` instead - it reads either.

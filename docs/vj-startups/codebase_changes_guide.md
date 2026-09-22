# Codebase Changes Guide

This checklist guides developers on exactly which files to edit to deploy the microservice integrations and member directory enhancements.

---

## 1. Plane Admin Frontend (apps/admin/)

### [MODIFY] [vj-startups.service.ts](file:///Users/manojkumarlakkala/Work/VJStartups/plane/apps/admin/services/vj-startups.service.ts)
- Add API methods for members management:
  - `fetchMembers()` -> calls `/api/vj-startups/admin/members/`
  - `updateMember(profileId, data)` -> PATCH `/api/vj-startups/admin/members/${profileId}/`
- Add API methods pointing to the `backend 2` port (or proxy) for ideas/problems auditing if not already handled:
  - `fetchAuditIdeas()` -> `GET http://localhost:5001/admin-api/ideas`

### [MODIFY] [UpcomingEventsKanban](file:///Users/manojkumarlakkala/Work/VJStartups/plane/apps/admin/components/club-activities/upcoming-events-kanban.tsx)
- Call `vjStartupsService.fetchEvents()` and hook it to SWR.
- Map columns to render the returned card values (`wing_name`, `wing_color`, `scheduled_at`).

### [MODIFY] [routes.ts](file:///Users/manojkumarlakkala/Work/VJStartups/plane/apps/admin/app/routes.ts)
- Registered the `member-directory` route and the subroutes `vj-startups/ideas`, `vj-startups/problems`, and `vj-startups/users`.

### [MODIFY] [sidebar config files](file:///Users/manojkumarlakkala/Work/VJStartups/plane/apps/admin/hooks/use-sidebar-menu/core.ts)
- Appended `memberDirectory`, `vjIdeas`, `vjProblems`, and `vjUsers` link keys, names, and descriptions referencing the respective path locations.

### [DELETE] [Standalone Admin Folder](file:///Users/manojkumarlakkala/Work/VJStartups/plane/admin)
- Completely deleted the initial workspace root `admin` folder after successfully migrating and merging all its view components, services, and routing rules into the main Plane Admin panel.

### [NEW] [Microservice Route Pages](file:///Users/manojkumarlakkala/Work/VJStartups/plane/apps/admin/app/(all)/(dashboard)/vj-startups/)
- Implemented individual route folders:
  - `ideas/page.tsx` -> Paginated auditing tool for submitted ecosystem ideas.
  - `problems/page.tsx` -> Paginated auditing tool for ecosystem problems.
  - `users/page.tsx` -> Dashboard view to toggle roles or delete website user records.

### [NEW] [MemberDirectory View](file:///Users/manojkumarlakkala/Work/VJStartups/plane/apps/admin/app/(all)/(dashboard)/member-directory/page.tsx)
- Implemented global members directory view featuring real-time showcase toggle controls, custom roles inline inputs, and "+ Add Member" overlays.

### [MODIFY] Wing Details Dashboard Page [page.tsx](file:///Users/manojkumarlakkala/Work/VJStartups/plane/apps/admin/app/(all)/(dashboard)/club-activities/[slug]/page.tsx)
- Replaced the invitation overlay with a directory search panel to add/remove existing members in real-time.

---

## 2. VJ Startups Service (backend 2/)

### [MODIFY] [server.js](file:///Users/manojkumarlakkala/Work/VJStartups/plane/backend%202/server.js)
- Ensure CORS rules allow credentials and cover `http://localhost:4000` / `admin.vjstartup.com`.
- Manage ports via process env.

### [MODIFY] [adminAuth.js](file:///Users/manojkumarlakkala/Work/VJStartups/plane/backend%202/middlewares/adminAuth.js)
- Update verification logic to decrypt and validate authorization headers.

---

## 3. Plane Django Backend (apps/api/)

### [MODIFY] [models/organization.py](file:///Users/manojkumarlakkala/Work/VJStartups/plane/apps/api/plane/vj_startups/models/organization.py)
- Ensure `is_club_member` is a BooleanField on `OrganizationMemberProfile`.
- Ensure `role = models.CharField(max_length=255, default="Member")` is declared.

### [MODIFY] [views/admin.py](file:///Users/manojkumarlakkala/Work/VJStartups/plane/apps/api/plane/vj_startups/views/admin.py)
- Added `AdminClubMemberEndpoint` (`ListCreateAPIView`) to create and list profiles.
- Added `AdminClubMemberDetailEndpoint` (`RetrieveUpdateDestroyAPIView`) supporting customized role fields and deletion.
- Implemented avatar empty string default normalization (`avatar = avatar or ""` / `user.avatar = user.avatar or ""`) to avoid database null constraint violations.
- Overrode `perform_update` on `AdminStartupDetailEndpoint` to automatically dispatch TRL stage changes to the Express microservice.
- Added proxy views: `AdminMicroserviceIdeasProxyEndpoint`, `AdminMicroserviceProblemsProxyEndpoint`, `AdminMicroserviceUsersProxyEndpoint`, and `AdminMicroserviceUserDetailProxyEndpoint` to securely bridge and authorize access to `backend 2` data.

### [MODIFY] [views/showcase.py](file:///Users/manojkumarlakkala/Work/VJStartups/plane/apps/api/plane/vj_startups/views/showcase.py)
- Added `ShowcaseMembersEndpoint` to output showcased profiles.

### [MODIFY] [urls.py](file:///Users/manojkumarlakkala/Work/VJStartups/plane/apps/api/plane/vj_startups/urls.py)
- Registered `/admin/members/`, `/admin/members/<pk>/`, `/showcase/members/`, and the microservice proxy routes under `/admin/microservice/` path prefix.

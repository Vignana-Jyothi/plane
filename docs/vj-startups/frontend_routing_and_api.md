# Frontend Routing and API Specifications

This guide documents the API routes that the **Plane Admin Panel** (`apps/admin`) and the **Main Website** (`vjstartup.com`) call to interact with Plane and the `backend 2` microservice.

---

## 1. Plane Admin Panel (apps/admin) API Directory

The admin panel routes requests to **two different backends** depending on the resource type.

### Call Route: Plane Django Backend (api/vj-startups/)
These endpoints handle workspaces, wings, events, and metrics.

#### `GET /api/vj-startups/admin/startups/`
- **Purpose**: List all startups.
- **Headers**: Cookie session auth.
- **Response**: Array of startup objects (slug, name, tagline, stage, status, etc.).

#### `POST /api/vj-startups/admin/startups/`
- **Purpose**: Create a new startup.
- **Payload**:
  ```json
  { "name": "Acme Corp", "tagline": "Slogan", "description": "Details", "invited_emails": ["founder@example.com"] }
  ```

#### `GET /api/vj-startups/admin/wings/`
- **Purpose**: Fetch all wings.
- **Response**: Array of wings (name, slug, color, description).

#### `GET /api/vj-startups/admin/wings/metrics/`
- **Purpose**: Get counts and wing performance.
- **Response**:
  ```json
  { "active_wings": 4, "total_events": 12, "engagement_score": "75%" }
  ```

#### `GET /api/vj-startups/admin/events/?status=upcoming,in_progress,completed`
- **Purpose**: Fetch events list, used by the Kanban board.
- **Response**: Array of events (title, status, scheduled_at, wing_name, wing_color).

#### `GET /api/vj-startups/admin/members/`
- **Purpose**: Fetch all directory members.
- **Response**: Array of profile objects (id, user, role, is_club_member, wing, etc.).

#### `POST /api/vj-startups/admin/members/`
- **Purpose**: Create/onboard a new club member into Plane and assign roles/wings.
- **Payload**:
  ```json
  {
    "email": "user@example.com",
    "first_name": "Test",
    "last_name": "User",
    "role": "Lead Architect",
    "wing": "<uuid>",
    "is_club_member": true,
    "avatar": "http://minio-url/bucket/avatar.png"
  }
  ```

#### `PATCH /api/vj-startups/admin/members/:id/`
- **Purpose**: Update a member's custom role name, active wing association, avatar URL, name, or public showcase visibility in real time.
- **Payload**:
  ```json
  {
    "user": {
      "first_name": "Updated",
      "last_name": "Name",
      "avatar": "http://new-url.png"
    },
    "role": "New Role Name",
    "wing": "<wing_id_or_null>",
    "is_club_member": false
  }
  ```

#### `DELETE /api/vj-startups/admin/members/:id/`
- **Purpose**: Delete/remove a member from the directory.

---

## 2. Plane Admin Panel Frontend Page Routes (React Router)

The following front-end routes are declared in `apps/admin/app/routes.ts` for rendering dashboard interfaces:

- **VJ Startups OS**: `/vj-startups/` -> Workspace health, startups audits, TRL promoters.
- **Club Activities**: `/club-activities/` -> Wings lists, Upcoming/In-Progress/Completed events Kanban column board.
- **Member Directory**: `/member-directory/` -> Showcase toggle switches, editable user roles, directory user creators.

---

## 3. Plane Admin Panel (apps/admin) Call Route: VJ Startups Service (backend 2) via Django Proxy
The admin panel calls Django API proxy endpoints to fetch and manage microservice data. Django authorizes the request using Plane session cookies and then forwards the call to `backend 2` using the server's configured `VJ_MICROSERVICE_ADMIN_TOKEN` token.

#### `GET /api/vj-startups/admin/microservice/ideas/?page=<page>&limit=<limit>&search=<query>`
- **Purpose**: Paginated audit list of student-submitted ideas.
- **Headers**: Session Cookie (`SessionId`)
- **Response**: Array of idea documents.

#### `GET /api/vj-startups/admin/microservice/problems/?page=<page>&limit=<limit>&search=<query>`
- **Purpose**: Paginated audit list of student-submitted problems.
- **Headers**: Session Cookie (`SessionId`)

#### `PATCH /api/vj-startups/admin/startups/:slug/`
- **Purpose**: Updates the startup details and its TRL validation stage. Django automatically syncs the validation stage level (1-9) to the Express microservice via `PATCH /admin-api/startups/:id/stage`.
- **Payload**: `{ "trl_stage": 5 }`

#### `GET /api/vj-startups/admin/microservice/users/?page=<page>&limit=<limit>&search=<query>`
- **Purpose**: Paginated list of registered main website users.
- **Headers**: Session Cookie (`SessionId`)

#### `PATCH /api/vj-startups/admin/microservice/users/:id/`
- **Purpose**: Toggle user role between `user` and `admin`.
- **Headers**: Session Cookie (`SessionId`)
- **Payload**: `{ "role": "admin" | "user" }`

#### `DELETE /api/vj-startups/admin/microservice/users/:id/`
- **Purpose**: Delete a user account from the microservice database.
- **Headers**: Session Cookie (`SessionId`)

---

## 4. Public Main Website (vjstartup.com) API Directory

The public portal interacts directly with the `backend 2` microservice for submissions/evaluations and reads from Plane's public showcase/profile endpoints.

### Call Route: Plane Django public API (/api/vj-startups/public/ & /api/vj-startups/showcase/)

#### `GET /api/vj-startups/showcase/members/`
- **Purpose**: Retrieve the list of active showcased club members to display directly on the public directory page.
- **Response**: Array of member profile cards (names, email, avatar URL, role name, wing details).

#### `GET /api/vj-startups/public/members/:username/`
- **Purpose**: Load individual user profile contributions dashboard.
- **Response**:
  ```json
  {
    "username": "manoj",
    "display_name": "Manoj Kumar",
    "is_club_member": true,
    "wing": "Development",
    "startups": ["BandiWala"],
    "contribution_summary": { "issues_closed": 84, "issues_assigned": 6, "points": 852 },
    "contribution_graph": [ { "date": "2026-05-01", "count": 3 } ]
  }
  ```

### Call Route: VJ Startups Service (backend 2)

#### `POST http://localhost:6220/problem-api/problem`
- **Purpose**: Add new problem statement.
- **Payload**: Form data (title, briefparagraph, background, tags, scalability, addedByName, addedByEmail).

#### `POST http://localhost:6220/problem-api/problem/:id/upvote`
- **Purpose**: Toggle upvote.
- **Payload**: `{ "email": "user@example.com" }`

#### `POST http://localhost:6220/idea-api/idea`
- **Purpose**: Submit startup concept.
- **Payload**: Form data (title, description, contact, addedByEmail, team, links).

#### `POST http://localhost:6220/questionnaire-api/response`
- **Purpose**: Submit stage-evaluation questionnaire responses.
- **Payload**: Answers payload, triggers automatic TRL level evaluation.

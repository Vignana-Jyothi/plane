# VJ Startups Microservices Architecture

This document describes the design of the VJ Startups ecosystem, treating the core task-tracking tool (Plane) and the idea-validation engine (Backend 2) as separate, decoupled microservices.

## System Topology

```
                  ┌───────────────────────────────┐
                  │       Main Public Site        │
                  │       (vjstartup.com)         │
                  └───────┬───────────────┬───────┘
                          │               │
      Public profile read │               │ Idea submission/votes
            & Heatmaps    │               │
                          ▼               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│     Plane Core Service    │   │   VJ Startups Service     │
│   (plane.vjstartup.com)   │   │     (backend 2)           │
│   Django / PostgreSQL     │   │  Express / Mongo/Postgres │
└─────────────▲─────────────┘   └─────────────▲─────────────┘
              │                               │
              │                               │ Admin tasks
              │   ┌───────────────────────┐   │ (manage ideas/problems)
              └───┤  Plane Admin Panel    ├───┘
                  │  (admin.vjstartup.com)│
                  └───────────────────────┘
```

## Service Boundaries & Responsibilities

### 1. Plane Core Service (Django + Postgres)
- **Task Management**: Organizes boards, issues, status pipelines, cycles, and labels.
- **Organization Structure**: Manages `Wings` and workspace roles.
- **Contributions Engine**: Syncs and aggregates user issues into the `ContributionSnapshot` table to power public profile heatmap graphs.
- **Auth Provider**: Authenticates team members accessing workspaces.

### 2. VJ Startups Service (Backend 2 — Express + Database)
- **Ecosystem Ideas**: Manages `Ideas` submitted by students.
- **Problems Directory**: Stores industry/community `Problems` along with comments, nested replies, upvotes, and likes.
- **TRL Evaluations**: Runs stage transition questionnaires and rates startup worthiness.
- **Stage Notifications**: Manages transition alerts for dashboard feeds.

## Cross-Service Data Correlation

Because the systems run on independent backends, they correlate entities via unique keys:

1. **User Identity**: Users are mapped by their unique email addresses (e.g. `user@vnrvjiet.in`). Plane holds the primary account profile; when a user logs in, `backend 2` stores their email to correlate comments, upvotes, and idea ownership.
2. **Projects to Startups**: Startups are created as workspaces/projects in Plane. The `vj_project_extensions` table in Plane associates a Plane `Project.id` with a `Startup.id` from the VJ Startups database.

## Authentication & Authorization Architecture

- **admin.vjstartup.com**: Logs in via Plane session cookies. To access `backend 2` APIs, the admin frontend passes the admin's email or an `adminToken` in the authorization header.
- **vjstartup.com**: Logs in via Firebase Google OAuth. The client frontend verifies the login, extracts the email, and sends the user's email in request bodies or headers to verify permission.

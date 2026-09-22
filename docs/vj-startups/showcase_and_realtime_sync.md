# Showcase Members & Real-time Synchronization Specification

This specification documents the public showcase routes and the real-time cache sync design for presenting club members on the public main website (`vjstartup.com`).

---

## 1. Public Showcase Route (vjstartup.com)

The public website calls this route to fetch the list of club members currently selected for public showcase.

### `GET /api/vj-startups/showcase/members/`
- **Method**: `GET`
- **Authentication**: None (`AllowAny`)
- **Query Params**: None

### Response Payload:
Returns an array of member profiles marked with `is_club_member = true`.
```json
[
  {
    "id": "e9b72a6b-d826-4d0f-b258-29ef3c28b7e2",
    "user": {
      "id": "c7a82b12-b924-4d89-a291-a1b7e0129bc3",
      "email": "manoj@vnrvjiet.in",
      "first_name": "Manoj",
      "last_name": "Kumar",
      "avatar": "http://minio-url/bucket/avatar.png",
      "username": "manoj"
    },
    "role": "Lead Architect",
    "is_club_member": true,
    "wing": {
      "id": "4f9d0c27-393f-4e08-9df8-2c286d9a9cb2",
      "name": "Vision & Leadership",
      "color": "#3B82F6"
    },
    "created_at": "2026-08-04T12:00:00Z"
  }
]
```

---

## 2. Real-time Changes & Synchronization Flow

The dashboard ensures **real-time changes** by employing optimistic cache updates paired with immediate database mutations:

```
┌─────────────────────┐       PATCH Request        ┌──────────────────────┐
│  Plane Admin Panel  ├───────────────────────────>│ Plane Django Backend │
│  (Member Directory) │                            │ (PostgreSQL Database)│
└──────────┬──────────┘                            └──────────┬───────────┘
           │                                                  │
           │ Optimistic                                       │ Live DB
           │ Update (Instant UI)                              │ Update
           ▼                                                  ▼
┌─────────────────────┐                            ┌──────────────────────┐
│  Local SWR Cache    │                            │ Showcase API Query   │
│  (State mutated)    │                            │ (GET /showcase/mem)  │
└─────────────────────┘                            └──────────▲───────────┘
                                                              │
                                                              │ Instant Read
                                                   ┌──────────┴───────────┐
                                                   │   Main Public Site   │
                                                   │   (vjstartup.com)    │
                                                   └──────────────────────┘
```

1. **State Mutation**:
   When the admin changes a member's wing, role name, or showcase status toggle:
   - SWR's local cache is updated immediately with the new value (optimistic rendering).
   - A `PATCH /api/vj-startups/admin/members/<profile_id>/` request is fired asynchronously.
2. **Instant Propagation**:
   - The PostgreSQL database updates the record instantly.
   - Subsequent calls to `GET /api/vj-startups/showcase/members/` from the public site return the updated information, ensuring the changes reflect on the public page in real time.

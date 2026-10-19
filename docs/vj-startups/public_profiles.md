# Public member profiles

A GitHub-style profile for every VJ Startups member, shown on the main website (vjstartup.com) so
the club can showcase work done on VJOS: contribution calendar, streaks, reputation, badges and
the startups a member belongs to.

The main website is a separate repository. This repo owns the **data, the privacy rules and the
API**; the website only renders what the API returns.

## Principles

1. **Opt-in.** A profile is private until its owner publishes it. Private and unknown handles both
   answer `404`, so the API never confirms that a private profile exists.
2. **Whitelist, never blacklist.** The public payload is built field by field
   (`public_profile_payload`). New columns on the profile are not public until someone adds them.
3. **Counts, not titles.** The calendar contains only numbers. Titles of work appear only for
   projects of startups the club marked `public_visibility`; secret startup projects stay secret.
4. **Computed from the source.** The calendar is read from Plane's own tables, not a stored
   snapshot, so it cannot drift from the real work. It is cached for 10 minutes.

## What counts as a contribution

| Kind        | Source                                                       |
| ----------- | ------------------------------------------------------------ |
| `completed` | an issue assigned to the member that reached a completed state |
| `created`   | an issue the member opened                                   |
| `comments`  | a comment the member wrote on an issue                       |
| `pages`     | a page the member created (not archived)                     |

Scope is the global VJ Startups workspace. Days are cut in `Asia/Kolkata`, not UTC, so evening
work is not pushed onto the next day. The window is the last 365 days.

Streaks: the current streak keeps counting if today is still empty but yesterday was active.

## API

All paths are under `/api/vj-startups/`.

### `GET public/profiles/<handle>/` — public, no auth

`404` unless the owner published the profile. Cacheable for 5 minutes.

```jsonc
{
  "handle": "asha-rao",
  "name": "Asha Rao",
  "headline": "Information Technology - 3rd Year",
  "bio": "…",
  "photo_url": "https://…",            // "" when none; never an internal path
  "role": "Wing Member",
  "member_stage": "explorer",
  "is_club_member": true,
  "wing": { "name": "Vision", "slug": "vision" },   // or null
  "joined_at": "2026-01-05T10:00:00Z",
  "skills": ["Python", "React"],
  "links": { "github": "", "linkedin": "", "portfolio": "" },
  "reputation": { "score": 41.5, "rank": 3, "execution": 60, "impact": 22, "leadership": 15, "learning": 5, "reliability": 100 },
  "badges": [{ "name": "", "slug": "", "description": "", "icon_url": "", "awarded_at": "" }],
  "startups": [{ "name": "", "slug": "", "role": "" }],          // public startups only
  "recent_work": [{ "title": "", "project": "", "completed_at": "" }],  // public startups only, max 10
  "activity": {
    "range": { "from": "2025-10-20", "to": "2026-10-19" },
    "timezone": "Asia/Kolkata",
    "total": 132, "active_days": 61, "max_daily": 9,
    "current_streak": 4, "longest_streak": 12,
    "breakdown": { "completed": 40, "created": 25, "comments": 60, "pages": 7 },
    "days": [{ "date": "2026-10-18", "count": 4, "level": 4, "completed": 3, "created": 0, "comments": 1, "pages": 0 }]
  }
}
```

`days` is **sparse**: only days with activity are listed. Draw every day in `range` and treat a
missing day as `count: 0, level: 0`. `level` is 0–4, relative to the member's busiest day.

### `GET public/members/<handle-or-username>/` — legacy

The older endpoint keeps its response shape but now also returns `404` for profiles that are not
published. It accepts a handle or the old username.

### `GET profile/me/` and `PATCH profile/me/` — signed-in member (session cookie)

Reads or edits the caller's own settings. Editable: `handle`, `profile_visibility`
(`"public"` | `"private"`), `headline`, `bio`, `skills`, `github_url`, `linkedin_url`,
`portfolio_url`. Anything else in the body is ignored, so this can never change a role, score,
wing or token.

* Publishing without a handle picks one from the member's name.
* `400 {"errors": {field: message}}` for invalid values; `409` if the handle is taken.

### `GET profile/handle-available/?handle=x` — signed-in member

`{"handle": "x", "available": true|false, "reason": null|"…"}` for live validation in the form.

### Handles

3–30 characters, lower-case letters, digits and single hyphens, starting and ending with a letter
or digit. Reserved words (`admin`, `api`, `settings`, …) are refused. Stored lower-case, unique.

## Rollout

* Phase 1 (this change): handle + visibility, calendar service, public profile API, settings API.
* Phase 2: "Public profile" page in Plane's settings (`apps/web`) to edit the above.
* Phase 3 (main website repo): `/u/<handle>` page that renders the payload above, with the calendar.
* Later ideas: more badge rules, pinned work, a README-embeddable heatmap image, wing leaderboards
  linking to profiles.

## Known follow-ups

* `sync_contributions` and the member leaderboard still read the older snapshot table and list
  every member regardless of visibility. The leaderboard should be restricted to published
  profiles before it is shown on the website.
* The calendar covers the global workspace only (`OnboardingService.WORKSPACE_SLUG`).

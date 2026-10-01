# Wing access model: who can see and manage what in Plane

Plane has one **workspace** for VJ Startups (`vj-startups`, at `vjos.vjstartup.com`). Wings are
modelled as **projects inside that workspace**, not as separate workspaces. This page says how
roles follow wings today and why.

## The roles

| Level                       | Roles                  | What it controls                                                            |
| --------------------------- | ---------------------- | --------------------------------------------------------------------------- |
| Instance (`/god-mode/`)     | Instance Admin         | Plane's own settings for the whole installation                             |
| Workspace (`vj-startups`)   | Admin, Member, Guest   | Workspace settings, members, and visibility of projects                     |
| Project (one per wing)      | Admin, Member, Guest   | That project's settings, members and work items                             |
| Site (Ecosystem Users page) | ADMIN, WING_MASTER, .. | Approving problems and ideas on the public site (separate from Plane roles) |

## How wings map to roles

- Every wing has its own project, private by default, created automatically.
- **Wing member** -> Member of their wing's project (and of the General project).
- **Wing master** -> **Admin of their wing's project**.
- The master of each wing listed in `VJ_WORKSPACE_ADMIN_WINGS` (default: `vision`) is also an
  **Admin of the whole workspace**. Set the variable to a comma-separated list of wing slugs to
  change that, or to an empty value to give no wing master workspace admin.
- Everyone with a college email is a plain workspace Member and is in the General project.

Roles only ever go **up** automatically: the system promotes a wing master to Admin but never
demotes anyone. Demoting is done by hand in Plane (Workspace settings, Members).

## Why wings are projects and not workspaces

A Plane workspace is a hard boundary: projects, members and work items cannot be shared between
workspaces, a person needs a separate membership in each, and nothing can be searched or reported
across them. The integration code (automatic onboarding, wing and startup project provisioning,
the importers) is written around the single `vj-startups` workspace. Splitting wings into
separate workspaces would mean rewriting that and would hide wings from each other, including
from the people meant to coordinate them. Projects give each wing its own space with its own
admins while keeping one place to see everything.

## Applying changes

- A person's wing, and whether they are a wing master, comes from the team sheet via the
  `import_team_members` command (Actions > "Data operations" > `team-members`). It is safe to
  re-run, and re-running promotes masters whose roles were set before this model was in place.
- Giving a wing access to every project (as was done for Vision) is the `wing-access` part of the
  same workflow.
- Instance Admin is the `instance-admin` part.

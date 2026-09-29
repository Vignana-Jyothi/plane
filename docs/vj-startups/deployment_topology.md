# Deployment topology: which machine runs what

Written down after a deploy failed for hours because two machines were confused. Everything
below was checked against real workflow logs and DNS on 2026-09-29; re-check before relying
on it if the infrastructure has changed.

## The two machines

|               | **dev-ai**                                                                                                                                 | **gamma**                                                                                    |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| Private IP    | `10.100.0.15`                                                                                                                              | `10.100.0.16`                                                                                |
| Public IP     | `103.248.208.119`                                                                                                                          | not confirmed (`www.vjstartup.com` resolves to `103.248.208.120`)                            |
| GitHub runner | `dev-ai` (`/home/campus/...`)                                                                                                              | `gamma-runner` (`/home/pavani/...`)                                                          |
| Runs          | The whole Plane stack (`vjos.vjstartup.com`), Plane's Postgres, and the `dev` branch of `vjstartups-main-website` (`dev-vj.vjstartup.com`) | The `main` branch of `vjstartups-main-website` (frontend on port 3005, backend on port 6220) |
| Deployed by   | `deploy-plane.yml` (Plane) and `deploy.yml` on non-`main` branches                                                                         | `deploy.yml` on `main`                                                                       |

`deploy.yml` in `vjstartups-main-website` picks the machine by branch: `main` goes to `gamma`
and every other branch goes to `dev-ai`.

## The database

There is **one** Postgres database, `plane`, and it lives on **dev-ai** in Plane's `plane-db`
container. It is published on the host at port `5434`.

- **Plane** reaches it inside Docker as `plane-db:5432`.
- **Backend 2 on dev-ai** reaches it as `host.docker.internal:5434`. That name means "this same
  machine", which is correct only on dev-ai. It is the built-in default in `docker-compose.yml`.
- **Backend 2 on gamma** must use dev-ai's private address, `10.100.0.15:5434`. This is set with
  the `PLANE_DATABASE_URL` secret in the `vj-production` environment of
  `vjstartups-main-website`:

  ```
  postgresql://USER:PASSWORD@10.100.0.15:5434/plane
  ```

Do **not** use `10.100.0.16` for the database: that is gamma itself.

Setting the secret from a terminal, without pasting into a hidden prompt (an empty paste is
accepted silently and shows up as `PLANE_DATABASE_URL:` with no value in the deploy log):

```bash
gh secret set PLANE_DATABASE_URL --env vj-production --repo Vignana-Jyothi/vjstartups-main-website --body "postgresql://USER:PASSWORD@10.100.0.15:5434/plane"
```

## Symptoms and what they mean

| Deploy log says                                                               | Meaning                                                                                                                                  |
| ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `Can't reach database server at host.docker.internal:5434` on a `main` deploy | The secret is unset (empty), so the backend on gamma is looking for a database on gamma itself.                                          |
| `Can't reach database server at 10.100.0.16:5434`                             | The secret points at gamma. Use `10.100.0.15`.                                                                                           |
| `PLANE_DATABASE_URL secret is not set` warning                                | The secret is missing or empty.                                                                                                          |
| Exit code `137` in a deploy step                                              | A process was killed, here because the backend was restarting in a loop while the step ran. Look at the container logs printed after it. |

## What is still not confirmed

- Whether port `5434` on dev-ai accepts connections from gamma at the firewall level (the
  deploys succeeded after the address was corrected, which indicates it does).
- The database still uses Plane's default credentials (`plane` / `plane`) and the port is
  published on all interfaces of dev-ai. It was tested closed from the public internet, but it
  should be restricted to gamma's address and given a real password; changing the password
  must be done in Plane's `.env`, the `PLANE_DATABASE_URL` secret and the database together.
- `www.vjstartup.com` is still served by the previous MongoDB-backed site on the `.120` host,
  not by the containers `gamma` deploys.

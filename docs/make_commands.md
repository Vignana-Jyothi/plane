# Makefile Commands Reference

This guide documents the available commands in the root [Makefile](file:///Users/manojkumarlakkala/Work/VJStartups/plane/Makefile) to streamline local development, testing, and quality assurance.

---

## Command Overview

| Unix Command (`make`) | Cross-Platform (`pnpm`) | Action | Scope |
| :--- | :--- | :--- | :--- |
| `make setup` | `pnpm run setup` | Runs configuration init scripts and installs dependencies. | Initial Setup |
| `make start` | `pnpm run start` | Launches development containers and starts local web/admin servers. | Local Run |
| `make stop` | `pnpm run docker:stop` | Stops and downs local development containers. | Cleanup / Stop |
| `make restart` | `pnpm run docker:restart` | Restarts local Docker services. | Troubleshooting |
| `make build` | `pnpm run build` | Builds all packages and Next.js/React Router applications. | Production Build |
| `make clean` | `pnpm run clean` | Wipes output directories and build caches. | Reset / Clean |
| `make seed` | `pnpm run seed` | Seeds the databases inside running API container. | Database Seeding |
| `make check` | `pnpm run check` | Runs linters, formatters, and TypeScript compilers. | Verification |
| `make fix` | `pnpm run fix` | Automatically fixes code style and linter violations. | Auto Formatting |
| `make test-api` | `pnpm run test-api` | Runs Django backend integration tests inside test containers. | Backend Testing |
| `make test-api-teardown` | `pnpm run test-api-teardown` | Wipes backend test containers and volumes. | Test Cleanup |

---

## Detailed Command Specifications

### 1. `make setup`
- **Underlying Command**: 
  ```bash
  chmod +x ./setup.sh && ./setup.sh
  ```
- **Use Case**: 
  Run this command **once** when setting up the workspace on a new machine. It copies environment templates (e.g. creating `apps/api/.env` from `.env.example`), configures default local keys, and validates system dependencies.
- **Example**:
  ```bash
  make setup
  ```

### 2. `make start`
- **Underlying Command**: 
  ```bash
  docker compose -f docker-compose-local.yml up -d && pnpm dev
  ```
- **Use Case**: 
  Used for active daily development. It starts the local dependency services (PostgreSQL, Redis, MinIO) in the background inside Docker, and launches the hot-reloading development servers for the frontend workspace applications (`apps/admin` on port `3001` and `apps/web` on port `3000`).
- **Example**:
  ```bash
  make start
  ```

### 3. `make stop`
- **Underlying Command**: 
  ```bash
  docker compose -f docker-compose-local.yml down
  ```
- **Use Case**: 
  Use this to halt all active background Docker containers and free system memory. It preserves database data volumes, allowing you to resume work later.
- **Example**:
  ```bash
  make stop
  ```

### 4. `make restart`
- **Underlying Command**: 
  ```bash
  docker compose -f docker-compose-local.yml down && docker compose -f docker-compose-local.yml up -d
  ```
- **Use Case**: 
  Used when database connections time out, configuration variables change, or local background services become unhealthy and need a fresh restart.
- **Example**:
  ```bash
  make restart
  ```

### 5. `make build`
- **Underlying Command**: 
  ```bash
  pnpm build
  ```
- **Use Case**: 
  Compiles all libraries, components, and admin panels into production bundles. Run this before deploying, or to verify that type declarations compile cleanly without errors.
- **Example**:
  ```bash
  make build
  ```

### 6. `make clean`
- **Underlying Command**: 
  ```bash
  pnpm clean
  ```
- **Use Case**: 
  Deletes all generated `.turbo`, `dist`, `.next`, and `.react-router` directories, along with package `node_modules`. Useful when facing corrupted dependency trees or build caching anomalies.
- **Example**:
  ```bash
  make clean
  ```

### 7. `make seed`
- **Underlying Command**: 
  ```bash
  docker compose -f docker-compose-local.yml exec api python manage.py seed_vj_startups
  ```
- **Use Case**: 
  Seeds the postgres databases inside the running API docker container with wings, badges, default admin/founder/member user accounts, workspace configurations, and default events.
- **Example**:
  ```bash
  make seed
  ```

### 8. `make check`
- **Underlying Command**: 
  ```bash
  pnpm check
  ```
- **Use Case**: 
  Used as a pre-commit check. It runs TypeScript compilers (`tsc`), OxLint, and formatting checkers to ensure that there are no style or syntax violations.
- **Example**:
  ```bash
  make check
  ```

### 8. `make fix`
- **Underlying Command**: 
  ```bash
  pnpm fix
  ```
- **Use Case**: 
  Automatically format your code and fix minor linting violations (such as missing semicolons, incorrect indentation, or sorting imports) across the repository.
- **Example**:
  ```bash
  make fix
  ```

### 9. `make test-api`
- **Underlying Command**: 
  ```bash
  docker compose -f docker-compose-test.yml up --build --abort-on-container-exit --exit-code-from api-tests
  ```
- **Use Case**: 
  Runs the Django backend integration and unit test suite inside a dedicated, isolated test container. If any test fails, it exits with the specific error code.
- **Example**:
  ```bash
  make test-api
  ```

### 10. `make test-api-teardown`
- **Underlying Command**: 
  ```bash
  docker compose -f docker-compose-test.yml down -v
  ```
- **Use Case**: 
  Wipes and downs all test-related databases, volumes, and networks to prevent residual data from affecting future test runs.
- **Example**:
  ```bash
  make test-api-teardown
  ```

---

## Windows Running Guide

Since default Windows Command Prompt (`cmd.exe`) and PowerShell do not support `make` out-of-the-box, the repository includes a suite of native cross-platform **`pnpm` scripts** inside `package.json`. These are the recommended commands for Windows:

### 1. Initial Setup
Run the cross-platform setup script to create `.env` files, generate a secret key, and install dependencies:
```powershell
pnpm run setup
```

### 2. Start Development Environment
Launches Docker containers in the background and starts the local Web and Admin servers:
```powershell
pnpm run start
```

### 3. Seed Database
Runs the VJ Startups database seeding script inside the running API container:
```powershell
pnpm run seed
```

### 4. Stop Docker Services
Stops all background Docker dev containers:
```powershell
pnpm run docker:stop
```

### 5. Restart Docker Services
```powershell
pnpm run docker:restart
```

### 6. Running Tests
Run the Django backend test suite or tear it down:
```powershell
pnpm run test-api
pnpm run test-api-teardown
```

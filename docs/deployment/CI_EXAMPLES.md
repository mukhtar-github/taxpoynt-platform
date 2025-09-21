# CI/CD Examples for Migrations

This doc shows how to run Alembic migrations as a pre‑deploy step, aligned with our deployment guidance.

## GitHub Actions (workflow_dispatch)

- File: `.github/workflows/db-migrate.yml` (already added)
- Usage:
  1. Store your `DATABASE_URL` in repo or environment secrets.
  2. Run the workflow manually from the Actions tab, select environment.

Notes:
- App instances should run with `ALEMBIC_RUN_ON_STARTUP=false` in production/staging.
- For development/single‑instance, keep `ALEMBIC_RUN_ON_STARTUP=true` or run the script manually.

## GitLab CI (example)

```yaml
stages:
  - migrate

migrate:db:
  stage: migrate
  image: python:3.11-slim
  variables:
    ENVIRONMENT: "staging"
    ALEMBIC_RUN_ON_STARTUP: "false"
    # Set via CI/CD settings
    DATABASE_URL: $DATABASE_URL
  before_script:
    - pip install --no-cache-dir -r platform/backend/requirements.txt
  script:
    - cd platform/backend && ./scripts/migrate.sh
  rules:
    - when: manual
```

## Docker entrypoint (optional)

If you want a container to run migrations conditionally:

```bash
#!/usr/bin/env bash
set -e

if [ "${RUN_MIGRATIONS}" = "true" ]; then
  echo "Running DB migrations..."
  cd /app/platform/backend && ./scripts/migrate.sh
fi

exec "$@"
```

- Build the image with this entrypoint and set `RUN_MIGRATIONS=true` only in pre‑deploy jobs.
- Keep app runtime with `ALEMBIC_RUN_ON_STARTUP=false` in production/staging.


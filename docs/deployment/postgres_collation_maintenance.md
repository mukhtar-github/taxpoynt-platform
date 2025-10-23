# PostgreSQL Collation Maintenance (Railway)

Railway periodically upgrades the underlying Ubuntu image, which bumps the GNU C
library collation version. When the database was created on an older version
PostgreSQL writes warnings like:

```
WARNING:  database "railway" has a collation version mismatch
DETAIL:  The database was created using collation version 2.36, but the operating system provides version 2.41.
HINT:  Rebuild all objects in this database that use the default collation and run ALTER DATABASE railway REFRESH COLLATION VERSION.
```

Ignoring the warning risks inconsistent text ordering or index lookups. Run the
refresh during the next maintenance window.

## Prerequisites

- Read/write access to the production Railway database.
- `psycopg2-binary` is already part of the backend requirements, so a Python
  environment is sufficient.
- Ensure `DATABASE_URL` points at the target database.

## Refresh Procedure

1. **Confirm the warning** (optional):

   ```sql
   SELECT datname, datcollate, datcollversion
   FROM pg_database
   WHERE datname = current_database();
   ```

   `datcollversion` will show the stored version. Compare with the actual
   version reported in `railway logs`.

2. **Run the helper script** from the repo root:

   ```bash
   export DATABASE_URL="postgresql://user:pass@host:port/railway"
   python scripts/refresh_collation_version.py
   ```

   The script prints the stored and actual versions, executes
   `ALTER DATABASE ... REFRESH COLLATION VERSION`, and exits. It skips the
   expensive reindex step by default.

3. **(Optional) Rebuild indexes** if the instance has heavy text-search
   workloads and you can afford downtime:

   ```bash
   python scripts/refresh_collation_version.py --reindex
   ```

   `REINDEX DATABASE` will block writes, so schedule it outside peak hours.

4. **Verify** the warning disappears:

   ```bash
   railway logs -s web | grep -i collation
   ```

   Alternatively, rerun the SQL from step 1 to ensure `datcollversion`
   matches the new actual version.

## Rollback / Safety

- `ALTER DATABASE ... REFRESH COLLATION VERSION` is idempotent. If the new
  version already matches the stored value nothing changes.
- The refresh must run with autocommit and no open transaction. The helper
  script enforces this.
- If a reindex was started accidentally and needs to be stopped, cancel the
  session in PostgreSQL (`pg_terminate_backend`) and rebuild indexes later.

## Tracking

- Log the execution time and whether `--reindex` was used in your ops runbook.
- Repeat after each Railway base image upgrade or if the warning resurfaces.

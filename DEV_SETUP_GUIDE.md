# TaxPoynt Platform - Development Setup Guide

## 🚨 Database Issue Resolution

**Problem**: The 500 error during user registration was caused by database schema mismatch between environments.

**Root Cause**: 
- Production: PostgreSQL (Railway) ✅
- Development: SQLite ❌ (Schema drift)
- Missing columns: `organization_id`, `is_deleted`, `deleted_at`

**Solution**: Unified PostgreSQL across ALL environments.

## 🔧 Quick Development Setup

### 1. Environment Configuration

**Single Source of Truth**: We now use ONE `.env` file with environment detection.

```bash
# Set your development environment
ENVIRONMENT=development  # Change this to switch environments
```

### 2. Start Development Database

```bash
# Start PostgreSQL and Redis for development
docker-compose -f docker-compose.dev.yml up -d

# Verify services are running
docker-compose -f docker-compose.dev.yml ps
```

### 3. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install missing dependencies
pip install aiofiles psycopg2-binary

# Install all requirements
pip install -r platform/backend/requirements.txt
```

### 4. Apply Database Migrations

```bash
# Navigate to backend
cd platform/backend

# Set environment for development
export ENVIRONMENT=development

# Apply migrations
source venv/bin/activate
cd migrations
alembic upgrade head
```

### 5. Start Development Server

```bash
# From platform/backend
uvicorn main:app --reload --port 8000
```

## 🚀 Production Deployment Fix

### Immediate 500 Error Fix

The 500 error will be fixed by applying this migration in Railway:

**SSH into Railway container and run:**

```sql
-- Connect to PostgreSQL and apply schema changes
ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE users ADD CONSTRAINT IF NOT EXISTS fk_users_organization_id 
  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;

ALTER TABLE users ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

ALTER TABLE organizations ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
```

**Or via Railway CLI:**

```bash
# Connect to Railway database
railway connect postgres

# Run the SQL above
```

## 🏗️ Architecture Improvements

### ✅ What We Fixed

1. **Unified Configuration**: Single `.env` file with environment detection
2. **Environment-Aware Database Config**: Automatic PostgreSQL for all environments
3. **Fixed Alembic**: Robust migration system with error handling
4. **Development Docker Setup**: PostgreSQL + Redis via Docker Compose

### 📋 Environment Variables

The application now automatically detects `ENVIRONMENT` and overrides:

- **Development**: `DATABASE_URL=postgresql://taxpoynt_user:taxpoynt_dev_pass@localhost:5433/taxpoynt_platform`
- **Production**: Uses Railway-provided `DATABASE_URL`

### 🔍 Debugging

Check environment detection:
```bash
cd platform/backend
python -c "from core_platform.config.environment import get_config; config = get_config(); print(f'Environment: {config.environment.value}'); print(f'Database URL: {config.get_database_url()}')"
```

## 📚 Development Workflow

### Daily Development

1. **Start Services**: `docker-compose -f docker-compose.dev.yml up -d`
2. **Activate Environment**: `source venv/bin/activate`
3. **Set Environment**: `export ENVIRONMENT=development`
4. **Start Backend**: `uvicorn main:app --reload`
5. **Start Frontend**: `cd platform/frontend && npm run dev`

### OAuth Client Seeding

Use the helper to create baseline OAuth 2.0 clients (monitoring dashboards, participant gateway, etc.) without hand-writing SQL:

```bash
export OAUTH2_MONITORING_CLIENT_SECRET="<strong-password>"
export OAUTH2_PARTICIPANT_GATEWAY_CLIENT_SECRET="<strong-password>"

# Optional: override the client ids while keeping secrets in env vars
export OAUTH2_MONITORING_CLIENT_ID="taxpoynt-monitoring-dashboard"
export OAUTH2_PARTICIPANT_GATEWAY_CLIENT_ID="participant-gateway"

python platform/backend/scripts/seed_default_oauth_clients.py
```

The script respects any JSON you already provide via `OAUTH2_DEFAULT_CLIENTS` and skips entries without matching secrets, so it is safe to rerun.

### Observability Dashboards

Queue throughput and SLA metrics now flow into the `/metrics` endpoint (port `9090`). To visualise them locally:

```bash
# Start Prometheus + Grafana + Jaeger in a separate terminal
docker-compose -f docker-compose.monitoring.yml up -d

# Grafana: http://localhost:3002 (admin/admin by default)
# Prometheus: http://localhost:9091
# Jaeger: http://localhost:16686
```

Grafana auto-loads the `Queue & SLA Overview` dashboard from `monitoring/grafana/dashboards/queue_sla.json`. Import additional dashboards by placing them in the same directory.

> **Tip:** export `OTEL_ENABLED=true` before starting the backend so spans flow into Jaeger via the built-in OpenTelemetry exporter.

### Making Database Changes

1. **Create Migration**: `alembic revision --autogenerate -m "description"`
2. **Review Migration**: Check generated file in `migrations/versions/`
3. **Apply Migration**: `alembic upgrade head`
4. **Test Changes**: Verify application works

### Testing

- **Unit Tests**: `pytest platform/backend/tests/`
- **Integration Tests**: `pytest platform/backend/tests/integration/`
- **E2E Tests**: `playwright test platform/tests/e2e/`

## 🚨 Troubleshooting

### "Module not found" errors
```bash
pip install aiofiles psycopg2-binary redis
```

### Database connection errors
```bash
# Check Docker services
docker-compose -f docker-compose.dev.yml ps

# Restart services
docker-compose -f docker-compose.dev.yml restart
```

### Migration errors
```bash
# Reset migrations (CAUTION: Development only)
alembic stamp head

# Or start fresh
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

## 🎯 Next Steps

1. Apply the production migration to fix the 500 error immediately
2. Use the development setup for local testing
3. All new features should use the unified PostgreSQL environment
4. Remove any remaining SQLite references from the codebase

---

**Priority Action**: Apply the production migration first to fix the 500 error, then use this development setup for ongoing work.

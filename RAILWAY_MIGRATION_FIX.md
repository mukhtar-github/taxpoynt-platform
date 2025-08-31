# 🚨 URGENT: Railway Production Database Migration

## Fix the 500 Registration Error Immediately

### Option 1: Railway Dashboard (Recommended)

1. **Open Railway Dashboard** → Your TaxPoynt Project
2. **Click on PostgreSQL Service**
3. **Go to "Connect" Tab**
4. **Click "Connect via Web Terminal"**
5. **Run these commands:**

```sql
-- Check current schema
\d+ users;
\d+ organizations;

-- Add missing columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- Add foreign key constraint
ALTER TABLE users ADD CONSTRAINT IF NOT EXISTS fk_users_organization_id 
  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;

-- Add missing columns to organizations table  
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- Verify changes
\d+ users;
\d+ organizations;

-- Exit
\q
```

### Option 2: Railway CLI

```bash
# Install Railway CLI (if not installed)
npm install -g @railway/cli

# Login to Railway
railway login

# Connect to your project
railway link

# Connect to PostgreSQL
railway connect postgres

# Run the SQL commands above
```

### Option 3: Using Database Client

Use the connection string from Railway:
```
postgresql://postgres:nyXssxTuCmDbXGUwwBqNQhUYacxBsXYI@postgres.railway.internal:5432/railway
```

**Note**: Replace `postgres.railway.internal` with the external host from Railway dashboard.

## ✅ Verification

After applying the migration, test user registration:

1. Go to your deployed frontend
2. Try to register a new user
3. The 500 error should be resolved

## 🔍 What This Fixes

- **organization_id**: Links users to organizations (required by new model)
- **is_deleted**: Enables soft delete functionality
- **deleted_at**: Tracks when records were soft deleted
- **Foreign Key**: Maintains data integrity between users and organizations

## 📋 Migration Record

Once applied, create this migration record for tracking:

```sql
-- Record this migration in alembic_version table (if using Alembic)
INSERT INTO alembic_version (version_num) VALUES ('add_user_org_soft_delete');
```

---

**Priority**: Apply this immediately to fix the 500 error in production!

##  🏗️ Development Environment Setup - Manual Steps

  Since Docker isn't available on this system, here's how to complete the local development setup:

  Option 1: Install Docker and Run Services

  # Install Docker (Ubuntu/Debian)
  sudo apt update
  sudo apt install docker.io docker-compose-plugin
  sudo systemctl start docker
  sudo usermod -aG docker $USER

  # Then restart terminal and run:
  docker compose -f docker-compose.dev.yml up -d

  Option 2: Use Local PostgreSQL Installation

  # Install PostgreSQL locally
  sudo apt install postgresql postgresql-contrib

  # Create development database
  sudo -u postgres createdb taxpoynt_platform
  sudo -u postgres createuser taxpoynt_user --createdb
  sudo -u postgres psql -c "ALTER USER taxpoynt_user PASSWORD 'taxpoynt_dev_pass';"

  # Update .env file
  export ENVIRONMENT=development
  export DATABASE_URL="postgresql://taxpoynt_user:taxpoynt_dev_pass@localhost:5432/taxpoynt_platform"



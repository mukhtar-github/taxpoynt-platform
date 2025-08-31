-- TaxPoynt Platform - Development Database Initialization
-- ========================================================
-- This script sets up the development PostgreSQL database
-- with proper extensions and initial configurations

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create test database if it doesn't exist
SELECT 'CREATE DATABASE taxpoynt_test OWNER taxpoynt_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'taxpoynt_test')\gexec

-- Grant necessary privileges
GRANT ALL PRIVILEGES ON DATABASE taxpoynt_platform TO taxpoynt_user;
GRANT ALL PRIVILEGES ON DATABASE taxpoynt_test TO taxpoynt_user;

-- Set up proper schemas
\c taxpoynt_platform

-- Create schemas for different modules
CREATE SCHEMA IF NOT EXISTS users_management;
CREATE SCHEMA IF NOT EXISTS organizations;
CREATE SCHEMA IF NOT EXISTS integrations;
CREATE SCHEMA IF NOT EXISTS banking;
CREATE SCHEMA IF NOT EXISTS firs_submissions;
CREATE SCHEMA IF NOT EXISTS audit_logs;

-- Grant schema permissions
GRANT ALL ON SCHEMA users_management TO taxpoynt_user;
GRANT ALL ON SCHEMA organizations TO taxpoynt_user;
GRANT ALL ON SCHEMA integrations TO taxpoynt_user;
GRANT ALL ON SCHEMA banking TO taxpoynt_user;
GRANT ALL ON SCHEMA firs_submissions TO taxpoynt_user;
GRANT ALL ON SCHEMA audit_logs TO taxpoynt_user;

-- Set up search path for user
ALTER USER taxpoynt_user SET search_path = public,users_management,organizations,integrations,banking,firs_submissions,audit_logs;

-- Refresh connections to apply settings
\q
#!/bin/bash
"""
TaxPoynt Platform Database Migration Script
==========================================
Production-ready database migration script with environment detection.
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKEND_DIR="$PROJECT_ROOT/platform/backend"

echo -e "${BLUE}🚀 TaxPoynt Platform Database Migration${NC}"
echo "========================================"

# Activate virtual environment
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    echo -e "${BLUE}📦 Activating virtual environment...${NC}"
    source "$PROJECT_ROOT/venv/bin/activate"
else
    echo -e "${RED}❌ Virtual environment not found at $PROJECT_ROOT/venv${NC}"
    exit 1
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Environment detection and DATABASE_URL setup
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️  DATABASE_URL not set, detecting environment...${NC}"
    
    if [ "$RAILWAY_DEPLOYMENT_ID" ]; then
        echo -e "${GREEN}🚂 Railway environment detected${NC}"
        # Railway sets DATABASE_URL automatically
        if [ -z "$DATABASE_URL" ]; then
            echo -e "${RED}❌ Railway deployment but no DATABASE_URL set${NC}"
            exit 1
        fi
    elif [ "$VERCEL" ]; then
        echo -e "${GREEN}▲ Vercel environment detected${NC}"
        # Use Vercel's database URL or fall back to development
        if [ -z "$POSTGRES_URL" ]; then
            echo -e "${YELLOW}⚠️  Using SQLite for Vercel development${NC}"
            export DATABASE_URL="sqlite:///taxpoynt_vercel.db"
        else
            export DATABASE_URL="$POSTGRES_URL"
        fi
    elif [ "$ENVIRONMENT" = "production" ]; then
        echo -e "${RED}❌ Production environment requires DATABASE_URL${NC}"
        exit 1
    elif [ "$ENVIRONMENT" = "staging" ]; then
        echo -e "${YELLOW}🧪 Staging environment requires DATABASE_URL${NC}"
        exit 1
    else
        echo -e "${YELLOW}🏠 Development environment - using SQLite${NC}"
        export DATABASE_URL="sqlite:///taxpoynt_dev.db"
    fi
else
    echo -e "${GREEN}✅ DATABASE_URL found: ${DATABASE_URL//:\/\/*:*@/:\/\/*****:****@}${NC}"
fi

# Show migration status
echo -e "${BLUE}📊 Current migration status:${NC}"
python -m alembic -c migrations/alembic.ini current

# Run migrations
echo -e "${BLUE}⬆️  Applying migrations...${NC}"
python -m alembic -c migrations/alembic.ini upgrade head

# Show final status
echo -e "${BLUE}📊 Final migration status:${NC}"
python -m alembic -c migrations/alembic.ini current

echo -e "${GREEN}✅ Database migration completed successfully!${NC}"

# Optional: Show migration history
if [ "$1" = "--history" ]; then
    echo -e "${BLUE}📜 Migration history:${NC}"
    python -m alembic -c migrations/alembic.ini history
fi
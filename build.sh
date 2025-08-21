#!/bin/bash

# TaxPoynt Platform - Robust Build Script for Railway Deployment
# =============================================================

set -e  # Exit on any error

echo "🚀 Starting TaxPoynt Platform build process..."

# Update pip itself first
echo "📦 Updating pip to latest version..."
python -m pip install --upgrade pip --no-cache-dir --timeout 300 --retries 5

# Install requirements with robust error handling
echo "📦 Installing Python dependencies..."
pip install \
    --no-cache-dir \
    --timeout 300 \
    --retries 5 \
    --prefer-binary \
    --force-reinstall \
    --no-warn-script-location \
    -r requirements.txt

# Verify critical imports work
echo "✅ Verifying critical imports..."
python -c "import fastapi; import uvicorn; import pydantic; print('✅ Core dependencies verified')"

echo "🎉 Build completed successfully!"
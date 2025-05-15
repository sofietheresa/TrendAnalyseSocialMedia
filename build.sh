#!/bin/bash
# Railway build script to ensure dependencies are installed

echo "=== RAILWAY BUILD SCRIPT ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create database.ini if needed
if [ ! -f "database.ini" ]; then
    echo "Creating database.ini from environment variables..."
    echo "[postgresql]" > database.ini
    echo "host=${DB_HOST}" >> database.ini
    echo "database=${DB_NAME}" >> database.ini
    echo "user=${DB_USER}" >> database.ini
    echo "password=${DB_PASSWORD}" >> database.ini
    echo "port=${DB_PORT:-5432}" >> database.ini
fi

# Test imports
echo "Testing imports..."
cd app
python test_import.py
cd ..

echo "Build script complete!" 
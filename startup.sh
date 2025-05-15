#!/bin/bash
# Railway startup script

echo "=== RAILWAY STARTUP SCRIPT ==="
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run the app
echo "Starting the application..."
cd app
python railway.py 
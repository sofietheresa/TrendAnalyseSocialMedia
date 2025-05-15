#!/usr/bin/env python3
"""
Test import script to verify all dependencies are installed correctly
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dependency-test")

def test_imports():
    """Test importing all required dependencies"""
    
    # List of modules to test
    required_modules = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "psycopg2",
        "dotenv"
    ]
    
    missing_modules = []
    
    # Test each module
    for module in required_modules:
        try:
            __import__(module)
            logger.info(f"✅ Successfully imported {module}")
        except ImportError:
            logger.error(f"❌ Failed to import {module}")
            missing_modules.append(module)
    
    # Summary
    if missing_modules:
        logger.error(f"Missing modules: {', '.join(missing_modules)}")
        return False
    else:
        logger.info("All required dependencies are installed!")
        return True

def main():
    """Main function"""
    logger.info("=== DEPENDENCY TEST SCRIPT ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
    logger.info(f"PORT: {os.getenv('PORT', '8000')}")
    
    success = test_imports()
    
    if success:
        logger.info("Dependency test passed!")
        sys.exit(0)
    else:
        logger.error("Dependency test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 
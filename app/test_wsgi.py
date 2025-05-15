#!/usr/bin/env python3
"""Test script to verify WSGI app imports correctly"""

import os
import sys

def test_wsgi_import():
    print("Testing WSGI app import...")
    try:
        # Try importing the app from wsgi.py
        from wsgi import application
        print("✅ Successfully imported 'application' from wsgi.py")
        
        # Try importing the app directly from main.py
        from main import app
        print("✅ Successfully imported 'app' from main.py")
        
        # Verify they are the same object
        if application is app:
            print("✅ 'application' and 'app' are the same object")
        else:
            print("❌ WARNING: 'application' and 'app' are different objects")
        
        # Print app details
        print(f"App name: {app.name}")
        print(f"App import path: {app.__module__}")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_wsgi_import()
    sys.exit(0 if success else 1) 
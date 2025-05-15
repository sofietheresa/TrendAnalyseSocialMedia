#!/usr/bin/env python3
"""
Test-Skript zum Überprüfen, ob die FastAPI-App korrekt importiert werden kann.
Dieses Skript sollte immer erfolgreich laufen, wenn die App richtig konfiguriert ist.
"""

import sys
import importlib.util
import os

def test_imports():
    """Test, ob die notwendigen Module importiert werden können"""
    try:
        print("Python-Version:", sys.version)
        print("Aktuelles Verzeichnis:", os.getcwd())
        print("Dateien im Verzeichnis:", os.listdir())
        
        print("\nVersuche 'fastapi' zu importieren...")
        import fastapi
        print("FastAPI-Version:", fastapi.__version__)
        
        print("\nVersuche 'main' zu importieren...")
        import main
        print("main Modul gefunden!")
        
        print("\nVersuche 'app' aus 'main' zu importieren...")
        assert hasattr(main, 'app'), "main hat kein 'app' Attribut"
        from main import app
        print("app-Objekt erfolgreich importiert!")
        print("app-Typ:", type(app))
        
        print("\nVersuche 'wsgi' zu importieren...")
        import wsgi
        print("wsgi Modul gefunden!")
        
        assert hasattr(wsgi, 'app'), "wsgi hat kein 'app' Attribut"
        print("wsgi.app ist vorhanden!")
        
        print("\nALLE IMPORTS ERFOLGREICH!")
        return True
    except Exception as e:
        print(f"FEHLER: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1) 
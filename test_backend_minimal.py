"""
Minimal backend test to isolate ACCESS_VIOLATION crash
This script tests if basic Python execution works in PyInstaller
"""

import sys
import os
import time

print("\n" + "="*60)
print("MINIMAL BACKEND TEST")
print("="*60)
print(f"[TEST] Python version: {sys.version}")
print(f"[TEST] Platform: {sys.platform}")
print(f"[TEST] Frozen: {getattr(sys, 'frozen', False)}")
print(f"[TEST] CWD: {os.getcwd()}")

if getattr(sys, 'frozen', False):
    print(f"[TEST] Bundle dir (_MEIPASS): {sys._MEIPASS}")
    print(f"[TEST] Executable: {sys.executable}")
    print(f"[TEST] Executable dir: {os.path.dirname(sys.executable)}")

    # List bundle contents
    try:
        bundle_files = os.listdir(sys._MEIPASS)
        print(f"[TEST] Bundle contains {len(bundle_files)} files/folders")
        print(f"[TEST] First 10 items: {bundle_files[:10]}")
    except Exception as e:
        print(f"[TEST] Could not list bundle: {e}")

print("\n[TEST] Basic Python execution works!")
print("[TEST] Testing module imports...")

# Test standard library
try:
    import json
    print("[OK] json module imported")
except Exception as e:
    print(f"[FAIL] json import failed: {e}")

try:
    import datetime
    print("[OK] datetime module imported")
except Exception as e:
    print(f"[FAIL] datetime import failed: {e}")

# Test Flask
try:
    import flask
    print(f"[OK] Flask imported (version: {flask.__version__})")
except Exception as e:
    print(f"[FAIL] Flask import failed: {e}")

# Test MySQL connector with pure-Python mode
try:
    os.environ['MYSQL_CONNECTOR_PYTHON_USE_PURE'] = '1'
    import mysql.connector
    print(f"[OK] MySQL connector imported (version: {mysql.connector.__version__})")
    print(f"[OK] Pure mode: {os.environ.get('MYSQL_CONNECTOR_PYTHON_USE_PURE')}")
except Exception as e:
    print(f"[FAIL] MySQL connector import failed: {e}")
    import traceback
    print(f"[FAIL] Traceback:\n{traceback.format_exc()}")

print("\n" + "="*60)
print("TEST COMPLETED SUCCESSFULLY - No crashes!")
print("="*60)
print("\nThe backend will stay running for 10 seconds...")
print("If you see this message, Python execution works fine.")
print("\n")

# Keep running for 10 seconds
for i in range(10, 0, -1):
    print(f"Shutting down in {i} seconds...")
    sys.stdout.flush()
    time.sleep(1)

print("\n[TEST] Clean exit")
sys.exit(0)

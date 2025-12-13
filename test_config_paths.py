import sys
import os
import json

print("="*60)
print("CONFIG.JSON PATH RESOLUTION TEST")
print("="*60)
print()

# Check if frozen
is_frozen = getattr(sys, 'frozen', False)
print(f"Is Frozen (packaged): {is_frozen}")
print(f"Python Executable: {sys.executable}")
print(f"Script Location: {__file__}")
print()

# Simulate frozen mode paths
if is_frozen:
    bundle_dir = sys._MEIPASS
    exe_dir = os.path.dirname(sys.executable)
    print(f"Bundle Dir (_MEIPASS): {bundle_dir}")
    print(f"Exe Dir: {exe_dir}")
else:
    bundle_dir = "N/A"
    exe_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Development Mode")
    print(f"Working Dir: {os.getcwd()}")

print()
print("="*60)
print("TESTING PATHS")
print("="*60)
print()

# Test paths
test_paths = []

if is_frozen:
    test_paths = [
        os.path.join(exe_dir, '..', '..', 'resources', 'config.json'),
        os.path.join(exe_dir, '..', 'config.json'),
        os.path.join(bundle_dir, 'config.json'),
        os.path.join(exe_dir, 'config.json'),
    ]
else:
    test_paths = [
        os.path.join(exe_dir, 'config.json'),
        os.path.join(exe_dir, '..', 'config.json'),
    ]

for i, path in enumerate(test_paths, 1):
    normalized = os.path.normpath(os.path.abspath(path))
    exists = os.path.exists(normalized)
    status = "[OK]" if exists else "[NOT FOUND]"
    
    print(f"{i}. {status} {normalized}")
    
    if exists:
        try:
            with open(normalized, 'r') as f:
                config = json.load(f)
                db_config = config.get('database', {})
                print(f"   MySQL: {db_config.get('user')}@{db_config.get('host')}:{db_config.get('port')}/{db_config.get('database')}")
        except Exception as e:
            print(f"   [ERROR] Could not read: {e}")

print()
print("="*60)
print("TEST COMPLETE")
print("="*60)

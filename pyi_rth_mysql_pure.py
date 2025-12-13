"""
PyInstaller runtime hook to force pure-Python MySQL connector
This prevents ACCESS_VIOLATION crashes from C extensions
"""

import os
import sys

# Force pure-Python implementation of MySQL connector
os.environ['MYSQL_CONNECTOR_PYTHON_USE_PURE'] = '1'

# Also set it via mysql.connector if already imported
try:
    import mysql.connector
    # Force use_pure mode
    if hasattr(mysql.connector, '_CONNECTION_POOL_KWARGS'):
        mysql.connector._CONNECTION_POOL_KWARGS['use_pure'] = True
except ImportError:
    pass

print("[RUNTIME HOOK] MySQL connector forced to pure-Python mode")

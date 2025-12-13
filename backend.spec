# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec file for Smart Purchase Slip Backend
Fixed version to prevent ACCESS_VIOLATION crashes (exit code 3221225477)
"""

import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Collect all Flask dependencies
flask_datas, flask_binaries, flask_hiddenimports = collect_all('flask')
jinja2_datas, jinja2_binaries, jinja2_hiddenimports = collect_all('jinja2')
mysql_datas, mysql_binaries, mysql_hiddenimports = collect_all('mysql')

# Combine all collected data
all_datas = flask_datas + jinja2_datas + mysql_datas
all_binaries = flask_binaries + jinja2_binaries + mysql_binaries
all_hiddenimports = flask_hiddenimports + jinja2_hiddenimports + mysql_hiddenimports

# Add application-specific data files
all_datas += [
    ('backend/templates', 'templates'),
    ('config.json', '.'),
]

# Add all backend Python files
all_datas += [
    ('backend/database.py', '.'),
    ('backend/routes/__init__.py', 'routes'),
    ('backend/routes/slips.py', 'routes'),
    ('backend/routes/auth.py', 'routes'),
]

# Ensure all critical imports are included
all_hiddenimports += [
    # Flask ecosystem
    'flask',
    'flask_cors',
    'jinja2',
    'jinja2.ext',
    'werkzeug',
    'werkzeug.security',
    'werkzeug.routing',
    'werkzeug.serving',
    'werkzeug.middleware',
    'werkzeug.middleware.proxy_fix',
    'click',
    'markupsafe',
    'itsdangerous',

    # MySQL connector
    'mysql.connector',
    'mysql.connector.pooling',
    'mysql.connector.cursor',
    'mysql.connector.cursor_cext',
    'mysql.connector.connection',
    'mysql.connector.connection_cext',
    'mysql.connector.errors',
    'mysql.connector.constants',
    'mysql.connector.conversion',
    'mysql.connector.protocol',
    'mysql.connector.abstracts',
    'mysql.connector.charsets',
    'mysql.connector.locales',
    'mysql.connector.utils',

    # Standard library
    'pytz',
    'datetime',
    'decimal',
    'json',
    'logging',
    'sqlite3',

    # Application modules
    'database',
    'routes',
    'routes.slips',
    'routes.auth',
]

# Remove duplicates
all_hiddenimports = list(set(all_hiddenimports))

a = Analysis(
    ['backend/app.py'],
    pathex=['backend', '.'],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PyQt5',
        'PySide2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='purchase_slips_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # CRITICAL: UPX disabled to prevent ACCESS_VIOLATION crashes
    console=True,  # Keep console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # CRITICAL: UPX disabled
    upx_exclude=[],
    name='dist-backend'
)

# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec file for Smart Purchase Slip Backend
Fixed version to prevent ACCESS_VIOLATION crashes and ensure all files are bundled

CRITICAL FIX: Forces pure-Python MySQL connector to prevent C extension crashes
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Force pure-Python mode for MySQL connector (prevents ACCESS_VIOLATION crashes)
os.environ['MYSQL_CONNECTOR_PYTHON_USE_PURE'] = '1'

block_cipher = None

# Collect data files for Flask/Jinja2
flask_datas = collect_data_files('flask')
jinja2_datas = collect_data_files('jinja2')

# Build the datas list explicitly
datas = [
    # Application templates
    ('backend/templates', 'templates'),

    # Frontend files for desktop app (CRITICAL - loaded in iframe)
    ('frontend/index.html', 'frontend'),
    ('frontend/reports.html', 'frontend'),
    ('frontend/static', 'frontend/static'),

    # Configuration file - CRITICAL
    ('config.json', '.'),

    # Backend Python modules as data files
    ('backend/__init__.py', '.'),
    ('backend/database.py', '.'),
    ('backend/app.py', '.'),
    ('backend/routes/__init__.py', 'routes'),
    ('backend/routes/slips.py', 'routes'),
    ('backend/routes/auth.py', 'routes'),
]

# Add Flask and Jinja2 data files
datas.extend(flask_datas)
datas.extend(jinja2_datas)

# Collect all MySQL connector submodules
mysql_hiddenimports = collect_submodules('mysql.connector')

# Build comprehensive hidden imports list
hiddenimports = [
    # Flask ecosystem
    'flask',
    'flask.json',
    'flask.json.provider',
    'flask_cors',
    'jinja2',
    'jinja2.ext',
    'werkzeug',
    'werkzeug.security',
    'werkzeug.routing',
    'werkzeug.serving',
    'werkzeug.middleware',
    'werkzeug.middleware.proxy_fix',
    'werkzeug.datastructures',
    'werkzeug.http',
    'werkzeug.urls',
    'werkzeug.useragents',
    'werkzeug.utils',
    'werkzeug.wrappers',
    'werkzeug.exceptions',
    'click',
    'markupsafe',
    'itsdangerous',

    # Standard library
    'pytz',
    'datetime',
    'decimal',
    'json',
    'logging',
    'sqlite3',
    'email',
    'email.mime',
    'email.mime.text',
    'email.mime.multipart',

    # Application modules
    'backend',
    'backend.database',
    'backend.routes',
    'backend.routes.slips',
    'backend.routes.auth',
]

# Add all MySQL connector imports
hiddenimports.extend(mysql_hiddenimports)

# Add specific MySQL connector modules that might be missed
hiddenimports.extend([
    'mysql.connector',
    'mysql.connector.pooling',
    'mysql.connector.cursor',
    'mysql.connector.connection',
    'mysql.connector.errors',
    'mysql.connector.constants',
    'mysql.connector.conversion',
    'mysql.connector.protocol',
    'mysql.connector.abstracts',
    'mysql.connector.charsets',
    'mysql.connector.locales',
    'mysql.connector.locales.eng',
    'mysql.connector.locales.eng.client_error',
    'mysql.connector.utils',
])

# Remove duplicates
hiddenimports = list(set(hiddenimports))

a = Analysis(
    ['backend/app.py'],
    pathex=['.', 'backend'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_mysql_pure.py'],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PyQt5',
        'PySide2',
        'IPython',
        'notebook',
        'pytest',
        # Exclude MySQL C extensions to force pure-Python mode
        '_mysql_connector',
        'mysql.connector.connection_cext',
        'mysql.connector.cursor_cext',
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
    upx=False,  # CRITICAL: Disabled to prevent ACCESS_VIOLATION
    console=True,
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
    upx=False,  # CRITICAL: Disabled
    upx_exclude=[],
    name='dist-backend'
)

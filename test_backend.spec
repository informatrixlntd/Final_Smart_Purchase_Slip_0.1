# -*- mode: python ; coding: utf-8 -*-

"""
Minimal test backend spec to diagnose ACCESS_VIOLATION
"""

import os

# Force pure-Python mode for MySQL connector
os.environ['MYSQL_CONNECTOR_PYTHON_USE_PURE'] = '1'

block_cipher = None

a = Analysis(
    ['test_backend_minimal.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'mysql.connector',
        'mysql.connector.pooling',
        'flask',
        'flask_cors',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_mysql_pure.py'],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        # Exclude MySQL C extensions
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
    name='test_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name='test-backend'
)

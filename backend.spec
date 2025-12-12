# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['backend/app.py'],
    pathex=['backend'],
    binaries=[],
    datas=[
        ('backend/templates', 'templates'),
        ('config.json', '.'),
        ('backend/database.py', '.'),
        ('backend/routes', 'routes'),
    ],
    hiddenimports=[
        'mysql.connector',
        'mysql.connector.pooling',
        'flask',
        'flask_cors',
        'jinja2',
        'werkzeug',
        'database',
        'routes',
        'routes.slips',
        'routes.auth',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='desktop/assets/spslogo.png'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='dist-backend'
)

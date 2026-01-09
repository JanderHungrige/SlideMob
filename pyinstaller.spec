# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Get the absolute path to the project root
project_root = os.path.abspath(os.getcwd())

added_files = [
    (os.path.join(project_root, 'src/slidemob/config.json'), 'slidemob'),
    (os.path.join(project_root, 'src/slidemob/config_gui.json'), 'slidemob'),
    (os.path.join(project_root, 'src/slidemob/config_languages.json'), 'slidemob'),
    (os.path.join(project_root, 'src/slidemob/utils/reasoning_model_list.json'), 'slidemob/utils'),
    (os.path.join(project_root, 'src/slidemob/images'), 'slidemob/images'),
    (os.path.join(project_root, 'src/slidemob/gui/assets'), 'slidemob/gui/assets'),
]

# Add external dependencies mappings if needed
# added_files += collect_data_files('some_package')

a = Analysis(
    [os.path.join(project_root, 'src/slidemob/__main__.py')],
    pathex=[os.path.join(project_root, 'src')],
    binaries=[],
    datas=added_files,
    hiddenimports=['ttkthemes', 'customtkinter', 'darkdetect', 'PIL._tkinter_finder', 'dotenv', 'slidemob.gui.settings_window', 'slidemob.utils.model_settings'],
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
    name='SlideMob',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'src/slidemob/images/icon.ico') if os.path.exists(os.path.join(project_root, 'src/slidemob/images/icon.ico')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SlideMob',
)

app = BUNDLE(
    coll,
    name='SlideMob.app',
    icon=os.path.join(project_root, 'src/slidemob/images/Appleicon.icns') if os.path.exists(os.path.join(project_root, 'src/slidemob/images/Appleicon.icns')) else None,
    bundle_identifier='com.slidemob.app',
)

# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


ROOT = Path(SPECPATH).resolve()
SOURCE = ROOT / "source"
APP_ICON = ROOT / "build" / "GodiusCrystalBuffTimer.ico"


a = Analysis(
    [str(SOURCE / "godius_buff_timer.py")],
    pathex=[str(SOURCE)],
    binaries=[],
    datas=[
        (str(SOURCE / "config.json"), "."),
        (str(SOURCE / "icons"), "icons"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="GodiusCrystalBuffTimer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(APP_ICON) if APP_ICON.exists() else None,
)

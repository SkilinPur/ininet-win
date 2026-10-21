# PyInstaller spec for ininet-win: single-file, console (TUI/CLI).
# Build:  pyinstaller ininet-win.spec --noconfirm
# Output: dist/ininet-win.exe

import re
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH)
VERSION = re.search(
    r'version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8")
).group(1)

datas = [
    (str(ROOT / "src" / "ininet_win" / "i18n" / "locales"), "ininet_win/i18n/locales"),
]

# textual and rich import plugins/widgets dynamically; pull them all in.
hiddenimports = (
    collect_submodules("textual")
    + collect_submodules("rich")
    + ["ininet_win.tui.app"]
)

block_cipher = None

a = Analysis(
    [str(ROOT / "src" / "ininet_win" / "__main__.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "PIL", "pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ininet-win",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "assets" / "ininet.ico"),
    version=str(ROOT / "assets" / "version_info.txt"),
)

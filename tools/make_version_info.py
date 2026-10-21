"""Generate assets/version_info.txt (Windows EXE metadata) from pyproject.toml.

Usage: python tools/make_version_info.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.search(
    r'version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8")
).group(1)

parts = (VERSION.split(".") + ["0", "0", "0", "0"])[:4]
try:
    nums = [int(p) for p in parts]
except ValueError:
    nums = [0, 0, 0, 0]
tuple_str = ", ".join(str(n) for n in nums)

TEMPLATE = f"""\
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({tuple_str}),
    prodvers=({tuple_str}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [StringStruct('CompanyName', 'InIProject / SkilinPur'),
           StringStruct('FileDescription', 'ininet-win — network scanner & monitor'),
           StringStruct('FileVersion', '{VERSION}'),
           StringStruct('InternalName', 'ininet-win'),
           StringStruct('LegalCopyright', 'Copyright (c) SkilinPur. MIT License.'),
           StringStruct('OriginalFilename', 'ininet-win.exe'),
           StringStruct('ProductName', 'ininet-win'),
           StringStruct('ProductVersion', '{VERSION}')])
      ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""

target = ROOT / "assets" / "version_info.txt"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(TEMPLATE, encoding="utf-8")
print(f"wrote {target} (version {VERSION})")

"""Build standalone executables for vsi2wm using PyInstaller.

This wrapper ensures consistent output paths across platforms so the
GitHub Actions workflow can simply invoke `python scripts/build_pyinstaller.py`.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PyInstaller.__main__ import run as pyinstaller_run


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUILD_ROOT = PROJECT_ROOT / "build" / "pyinstaller"
DIST_ROOT = PROJECT_ROOT / "dist" / "pyinstaller"
WORK_ROOT = BUILD_ROOT / "work"


def ensure_clean_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def main() -> int:
    ensure_clean_directory(BUILD_ROOT)
    ensure_clean_directory(DIST_ROOT)
    ensure_clean_directory(WORK_ROOT)

    args = [
        "--onefile",
        "--clean",
        "--name",
        "vsi2wm",
        "--distpath",
        str(DIST_ROOT),
        "--workpath",
        str(WORK_ROOT),
        "--specpath",
        str(BUILD_ROOT),
        str(PROJECT_ROOT / "vsi2wm" / "cli.py"),
    ]

    pyinstaller_run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


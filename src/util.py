"""Cross-platform utility helpers shared across the installer."""
from __future__ import annotations

import os
import subprocess
import sys


def open_in_file_manager(path: str) -> None:
    """Open a folder in the system file manager (cross-platform)."""
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def open_file(path: str) -> None:
    """Open a file with the system default application (cross-platform)."""
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def exe_name(name: str) -> str:
    """Append .exe suffix on Windows, return as-is on Linux/Mac."""
    if sys.platform == "win32" and not name.endswith(".exe"):
        return name + ".exe"
    return name


def sa_exe_names() -> list[str]:
    """Return all possible SA executable names for the current platform.

    Priority: gta_sa.exe (mod provides this) > gta-sa.exe (Steam)
    """
    names = ["gta_sa", "gta-sa"]
    if sys.platform == "win32":
        return [n + ".exe" for n in names]
    return names

"""Archive extractor supporting .zip, .rar, and .7z.

    .zip  -> zipfile (stdlib)
    .7z   -> py7zr
    .rar  -> rarfile (needs unrar.exe or 7z.exe on PATH on Windows)

All extracted files land in a per-mod subfolder under the shared cache so
re-installs skip extraction. The wizard then copies/merges those files
into the SA root.
"""
from __future__ import annotations

import logging
import os
import shutil
import zipfile
from typing import Callable, Optional

from . import cache

log = logging.getLogger(__name__)

ProgressCb = Callable[[int, int], None]   # (current, total) — best-effort


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def extract(
    archive_path: str,
    dest_dir: str,
    progress: Optional[ProgressCb] = None,
) -> str:
    """Extract any supported archive type into dest_dir.

    For loose mod files (.cleo, .cs, .asi), copies them directly.
    Returns dest_dir. Raises on unsupported extension or extraction error.
    """
    if not os.path.isfile(archive_path):
        raise FileNotFoundError(archive_path)

    ext = _ext(archive_path)
    os.makedirs(dest_dir, exist_ok=True)

    # Loose mod files — just copy
    if ext in supported_mod_extensions():
        import shutil
        dest_file = os.path.join(dest_dir, os.path.basename(archive_path))
        shutil.copy2(archive_path, dest_file)
        if progress:
            progress(1, 1)
        return dest_dir

    if ext in ("", ".tmp", ".download"):
        ext = _detect_ext_by_magic(archive_path)

    if ext == ".zip":
        _extract_zip(archive_path, dest_dir, progress)
    elif ext == ".7z":
        _extract_7z(archive_path, dest_dir, progress)
    elif ext == ".rar":
        _extract_rar(archive_path, dest_dir, progress)
    else:
        raise ValueError(f"Unsupported archive type: {ext}")

    return dest_dir


def supported_extensions() -> tuple[str, ...]:
    return (".zip", ".rar", ".7z")


def supported_mod_extensions() -> tuple[str, ...]:
    """File extensions that are valid mod files (not archives — just copy)."""
    return (".cleo", ".cs", ".cs4", ".asi")


def is_archive(path: str) -> bool:
    return _ext(path) in supported_extensions()


def is_mod_file(path: str) -> bool:
    """Check if a file is a recognized mod file (.cleo, .cs, .asi)."""
    return _ext(path) in supported_mod_extensions()


def verify_mod_file(path: str) -> tuple[bool, str]:
    """Verify a mod file is valid. Returns (is_valid, reason).

    Uses magic bytes + size check (no full archive parsing — avoids
    false "corrupted" reports from libraries that can't handle all formats).
    """
    if not os.path.isfile(path):
        return False, "File does not exist"

    size = os.path.getsize(path)
    ext = _ext(path)

    if ext in supported_extensions():
        if size < 1024:
            return False, f"Archive too small ({size} bytes)"
        # Check magic bytes to verify it's a real archive
        try:
            with open(path, "rb") as f:
                header = f.read(8)
        except Exception:
            return False, "Cannot read file"

        if ext == ".zip":
            if not header.startswith(b"PK\x03\x04"):
                return False, "Not a valid ZIP file (bad magic bytes)"
        elif ext == ".7z":
            if not header.startswith(b"7z\xBC\xAF\x27\x1C"):
                return False, "Not a valid 7z file (bad magic bytes)"
        elif ext == ".rar":
            if not header.startswith(b"Rar!\x1a\x07"):
                return False, "Not a valid RAR file (bad magic bytes)"
        return True, "Valid archive"

    if ext == ".cleo":
        if size < 1024:
            return False, f"CLEO file too small ({size} bytes) — may be invalid"
        return True, "Valid CLEO plugin"

    if ext in (".cs", ".cs4"):
        if size < 100:
            return False, f"Script too small ({size} bytes) — may be empty"
        return True, "Valid CLEO script"

    if ext == ".asi":
        if size < 1024:
            return False, f"ASI file too small ({size} bytes) — may be invalid"
        return True, "Valid ASI plugin"

    return False, f"Unknown file type: {ext}"


def scan_archives(folder: str, exclude_dirs: Optional[list[str]] = None) -> list[str]:
    """Return a list of all mod files in `folder` (recursive).

    Scans for archives (.zip/.rar/.7z) AND loose mod files (.cleo/.cs/.asi).
    Skips any directories in exclude_dirs.
    """
    out: list[str] = []
    if not folder or not os.path.isdir(folder):
        return out
    exclude_set = set(os.path.normpath(d) for d in (exclude_dirs or []))
    for root, _dirs, files in os.walk(folder):
        if os.path.normpath(root) in exclude_set:
            _dirs.clear()
            continue
        for name in files:
            if is_archive(name) or is_mod_file(name):
                out.append(os.path.join(root, name))
    return out


def find_mod_in_archives(
    archives: list[str],
    mod_id: str,
    mod_name: str,
    file_matchers: Optional[list[str]] = None,
) -> Optional[str]:
    """Try to find an archive that looks like it contains the given mod.

    Heuristic: match by mod_id, mod_name, or file_matchers appearing in the
    filename (case-insensitive, underscore/space normalized).

    Returns the archive path or None.
    """
    import re
    needles = [mod_id.lower().replace("_", " "), mod_id.lower(), mod_name.lower()]
    if file_matchers:
        needles.extend(m.lower() for m in file_matchers)

    has_version_matchers = bool(file_matchers and any(re.search(r'\d+\.\d+', m) for m in file_matchers))

    for arc in archives:
        base = os.path.basename(arc).lower()
        base_norm = base.replace("_", " ")
        has_version_in_name = bool(re.search(r'\d+\.\d+', base))

        # Try version-specific matchers first (most precise)
        if file_matchers:
            for fm in file_matchers:
                fml = fm.lower()
                fml_norm = fml.replace("_", " ")
                if fml in base or fml_norm in base_norm:
                    return arc

        # Try mod_name match
        if mod_name.lower() in base or mod_name.lower() in base_norm:
            return arc

        # Try generic mod_id — but only if the file has no version number
        # (to prevent "dyom" from matching "DYOM_8.3.zip")
        if mod_id.lower() in base or mod_id.lower().replace("_", " ") in base_norm:
            if has_version_in_name and has_version_matchers:
                continue  # Skip — let a version-specific mod claim this file
            return arc

    return None


# ----------------------------------------------------------------------
# Per-type extractors
# ----------------------------------------------------------------------
def _extract_zip(arc: str, dest: str, progress: Optional[ProgressCb]) -> None:
    with zipfile.ZipFile(arc) as zf:
        members = zf.infolist()
        total = len(members)
        for i, m in enumerate(members, 1):
            zf.extract(m, dest)
            if progress:
                try:
                    progress(i, total)
                except Exception:
                    pass


def _extract_7z(arc: str, dest: str, progress: Optional[ProgressCb]) -> None:
    try:
        import py7zr  # type: ignore
    except ImportError as e:
        raise RuntimeError("py7zr not installed — cannot extract .7z files.") from e
    with py7zr.SevenZipFile(arc, mode="r") as z:
        z.extractall(path=dest)
    if progress:
        try:
            progress(1, 1)
        except Exception:
            pass


def _extract_rar(arc: str, dest: str, progress: Optional[ProgressCb]) -> None:
    """Extract RAR files using 7-Zip subprocess (supports RAR5 format).

    The Python rarfile library does not support RAR5. 7-Zip handles all
    RAR versions including RAR5.
    """
    seven_zip = _find_unrar_tool()
    if not seven_zip or not os.path.isfile(seven_zip):
        raise RuntimeError(
            "7-Zip not found — cannot extract .rar files. "
            "Install 7-Zip from https://www.7-zip.org/"
        )

    import subprocess
    progress("Extracting with 7-Zip...", 50) if progress else None
    result = subprocess.run(
        [seven_zip, "x", arc, f"-o{dest}", "-y"],
        capture_output=True, text=True, timeout=600
    )
    if result.returncode != 0:
        raise RuntimeError(f"7-Zip extraction failed: {result.stderr[:500]}")
    if progress:
        progress(1, 1)


def _find_unrar_tool() -> str:
    """Find an unrar-compatible binary (cross-platform)."""
    import shutil as sh
    found = sh.which("unrar") or sh.which("UnRAR") or sh.which("unrar-free")
    if found:
        return found
    # Try common install paths on Windows
    import sys
    if sys.platform == "win32":
        candidates = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
            r"C:\Program Files\WinRAR\unrar.exe",
            r"C:\Program Files (x86)\WinRAR\unrar.exe",
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
    elif sys.platform == "darwin":
        # macOS: try Homebrew paths
        candidates = [
            "/opt/homebrew/bin/unrar",
            "/usr/local/bin/unrar",
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
    else:
        # Linux: try common paths
        candidates = [
            "/usr/bin/unrar",
            "/usr/local/bin/unrar",
            "/snap/bin/unrar",
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
    return "unrar"  # let rarfile raise a clear error if missing


# ----------------------------------------------------------------------
# Merge helper — copies extracted files into the SA root
# ----------------------------------------------------------------------
def merge_into_sa_root(
    extracted_dir: str,
    sa_root: str,
    pick_paths: Optional[list[str]] = None,
    progress: Optional[Callable[[int, int], None]] = None,
) -> int:
    """Copy extracted files into the SA root.

    If pick_paths is set, only those subpaths (relative to extracted_dir)
    are copied. Otherwise the entire extracted_dir is merged.

    Mod files (.cleo, .cs, .asi) are placed in appropriate subdirectories:
        .cleo -> cleo/
        .cs/.cs4 -> cleo/
        .asi -> root (ASI loader finds them here)

    Returns the number of files copied.
    """
    # Count total files first for progress reporting
    total_files = sum(len(files) for _, _, files in os.walk(extracted_dir))
    count = 0

    if pick_paths:
        for rel in pick_paths:
            src = os.path.join(extracted_dir, rel)
            if not os.path.exists(src):
                log.warning("pick_path missing in extracted archive: %s", rel)
                continue
            dst = os.path.join(sa_root, rel)
            if os.path.isdir(src):
                for root, _dirs, files in os.walk(src):
                    for name in files:
                        src_file = os.path.join(root, name)
                        rel_path = os.path.relpath(src_file, src)
                        dst_file = os.path.join(dst, rel_path)
                        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                        count += 1
                        if progress and count % 100 == 0:
                            progress(count, total_files)
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                count += 1
    else:
        for entry in os.listdir(extracted_dir):
            src = os.path.join(extracted_dir, entry)
            if os.path.isfile(src):
                ext_lower = os.path.splitext(entry)[1].lower()
                if ext_lower in (".cleo", ".cs", ".cs4"):
                    dst = os.path.join(sa_root, "cleo", entry)
                elif ext_lower == ".asi":
                    dst = os.path.join(sa_root, entry)
                else:
                    dst = os.path.join(sa_root, entry)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                count += 1
            else:
                dst = os.path.join(sa_root, entry)
                for root, _dirs, files in os.walk(src):
                    rel = os.path.relpath(root, src)
                    target_dir = dst if rel == "." else os.path.join(dst, rel)
                    os.makedirs(target_dir, exist_ok=True)
                    for name in files:
                        src_file = os.path.join(root, name)
                        dst_file = os.path.join(target_dir, name)
                        shutil.copy2(src_file, dst_file)
                        count += 1
                        if progress and count % 100 == 0:
                            progress(count, total_files)
    return count


def safe_overwrite(src: str, dst: str) -> bool:
    """Safely overwrite dst with src, creating .old backup of existing file.

    Returns True on success, False on failure (logs error).
    """
    try:
        # If destination exists, backup to .old
        if os.path.isfile(dst):
            old_path = dst + ".old"
            # Remove previous .old if exists
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError as e:
                    log.warning("Could not remove old backup %s: %s", old_path, e)
            # Rename current to .old
            try:
                os.rename(dst, old_path)
            except OSError as e:
                log.warning("Could not backup %s to %s: %s", dst, old_path, e)
        # Copy new file
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        log.error("Failed to overwrite %s with %s: %s", dst, src, e)
        return False


def smart_overwrite(src: str, dst: str) -> bool:
    """Overwrite dst with src only if they differ (size or content hash).

    Skips copy if files are identical. Creates .old backup if overwriting.
    Returns True on success (or if files are identical), False on failure.
    """
    try:
        # If destination doesn't exist, just copy
        if not os.path.isfile(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            return True

        # Quick check: same size and modification time = likely identical
        src_stat = os.stat(src)
        dst_stat = os.stat(dst)
        if src_stat.st_size == dst_stat.st_size:
            # Same size - check if modification time is newer
            if src_stat.st_mtime <= dst_stat.st_mtime:
                # Source is older or same - skip copy
                log.debug("Skipping %s (identical or newer exists)", os.path.basename(dst))
                return True

        # Files differ - use safe_overwrite
        return safe_overwrite(src, dst)
    except Exception as e:
        log.error("Smart overwrite failed for %s: %s", dst, e)
        return False


def _copy_tree(src: str, dst: str) -> int:
    """Merge src dir into dst (overwrites files, never deletes extras)."""
    count = 0
    os.makedirs(dst, exist_ok=True)
    for root, _dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        target_dir = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(target_dir, exist_ok=True)
        for name in files:
            src_file = os.path.join(root, name)
            dst_file = os.path.join(target_dir, name)
            # Use smart_overwrite - skip if identical, backup if different
            if not smart_overwrite(src_file, dst_file):
                log.warning("Failed to copy %s", src_file)
            else:
                log.debug("Processed: %s", os.path.basename(src_file))
            count += 1
    return count


def _ext(path: str) -> str:
    p = path.lower()
    for e in (".zip", ".rar", ".7z"):
        if p.endswith(e):
            return e
    return os.path.splitext(p)[1]


def _detect_ext_by_magic(path: str) -> str:
    """Detect archive type by reading magic bytes. Returns extension or empty string."""
    try:
        with open(path, "rb") as f:
            header = f.read(16)
    except (OSError, IOError):
        return ""
    if header[:4] == b"PK\x03\x04":
        return ".zip"
    if header[:4] == b"Rar!":
        return ".rar"
    if header[:6] == b"7z\xbc\xaf\x27\x1c":
        return ".7z"
    return ""

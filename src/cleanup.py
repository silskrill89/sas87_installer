"""Startup cleanup — prune old logs, backups, crash logs, orphaned _MEI* dirs.

Called once at startup from installer.py. Safe to run multiple times.
"""
from __future__ import annotations

import glob
import logging
import os
import tempfile
import time
from typing import Optional

from . import config

logger = logging.getLogger(__name__)

# How many files to keep in each category
KEEP_LOGS = 10
KEEP_BACKUPS = 5
KEEP_CRASH_LOGS = 3


def cleanup_old_logs(keep: int = KEEP_LOGS) -> int:
    """Remove install_*.log files beyond the newest `keep`. Returns count removed."""
    log_dir = config.CACHE_LOGS
    if not os.path.isdir(log_dir):
        return 0
    logs = sorted(
        glob.glob(os.path.join(log_dir, "install_*.log")),
        key=os.path.getmtime,
        reverse=True,
    )
    removed = 0
    for old_log in logs[keep:]:
        try:
            os.remove(old_log)
            removed += 1
        except OSError as e:
            logger.debug("Failed to remove old log %s: %s", old_log, e)
    if removed:
        logger.info("Cleaned %d old log(s), kept %d", removed, min(len(logs), keep))
    return removed


def cleanup_old_backups(keep: int = KEEP_BACKUPS) -> int:
    """Remove backup_*.zip files beyond the newest `keep`. Returns count removed."""
    backup_dir = config.CACHE_BACKUPS
    if not os.path.isdir(backup_dir):
        return 0
    backups = sorted(
        glob.glob(os.path.join(backup_dir, "backup_*.zip")),
        key=os.path.getmtime,
        reverse=True,
    )
    removed = 0
    for old_backup in backups[keep:]:
        try:
            os.remove(old_backup)
            removed += 1
        except OSError as e:
            logger.debug("Failed to remove old backup %s: %s", old_backup, e)
    if removed:
        logger.info("Cleaned %d old backup(s), kept %d", removed, min(len(backups), keep))
    return removed


def cleanup_crash_logs(keep: int = KEEP_CRASH_LOGS) -> int:
    """Remove crash_*.log files next to the project root beyond `keep`. Returns count removed."""
    crash_dir = config.PROJECT_ROOT
    logs = sorted(
        glob.glob(os.path.join(crash_dir, "crash_*.log")),
        key=os.path.getmtime,
        reverse=True,
    )
    removed = 0
    for old_log in logs[keep:]:
        try:
            os.remove(old_log)
            removed += 1
        except OSError as e:
            logger.debug("Failed to remove old crash log %s: %s", old_log, e)
    if removed:
        logger.info("Cleaned %d old crash log(s), kept %d", removed, min(len(logs), keep))
    return removed


def cleanup_orphaned_mei(max_age_hours: float = 1.0) -> int:
    """Remove orphaned PyInstaller _MEI* temp dirs older than `max_age_hours`.

    When a PyInstaller onefile exe crashes, _MEI* directories are left behind
    in %TEMP%. This cleans them up if they're old enough to not be from a
    currently-running instance. Returns count removed.
    """
    temp_dir = tempfile.gettempdir()
    mei_dirs = glob.glob(os.path.join(temp_dir, "_MEI*"))
    cutoff = time.time() - (max_age_hours * 3600)
    removed = 0
    for d in mei_dirs:
        if not os.path.isdir(d):
            continue
        try:
            mtime = os.path.getmtime(d)
            if mtime < cutoff:
                import shutil
                shutil.rmtree(d, ignore_errors=True)
                if not os.path.exists(d):
                    removed += 1
        except OSError:
            pass
    if removed:
        logger.info("Cleaned %d orphaned _MEI* temp dir(s)", removed)
    return removed


def run_all() -> dict:
    """Run all cleanup tasks. Returns a summary dict of what was cleaned."""
    summary = {}
    summary["logs_removed"] = cleanup_old_logs()
    summary["backups_removed"] = cleanup_old_backups()
    summary["crash_logs_removed"] = cleanup_crash_logs()
    summary["mei_dirs_removed"] = cleanup_orphaned_mei()
    total = sum(summary.values())
    if total:
        logger.info("Startup cleanup complete: %d items removed", total)
    return summary


def cleanup_downloads(mod_ids: list[str]) -> int:
    """Remove downloaded archives for specific mod IDs. Returns count removed."""
    downloads_dir = config.CACHE_DOWNLOADS
    if not os.path.isdir(downloads_dir):
        return 0
    removed = 0
    for f in os.listdir(downloads_dir):
        for mid in mod_ids:
            if f.startswith(mid) or mid in f:
                try:
                    os.remove(os.path.join(downloads_dir, f))
                    removed += 1
                except OSError:
                    pass
    return removed


def cleanup_extracted(mod_ids: list[str]) -> int:
    """Remove extracted files for specific mod IDs. Returns count removed."""
    import shutil
    extracted_dir = config.CACHE_EXTRACTED
    if not os.path.isdir(extracted_dir):
        return 0
    removed = 0
    for mid in mod_ids:
        d = os.path.join(extracted_dir, mid)
        if os.path.isdir(d):
            try:
                shutil.rmtree(d, ignore_errors=True)
                if not os.path.exists(d):
                    removed += 1
            except OSError:
                pass
    return removed


def cleanup_all_logs() -> int:
    """Remove ALL install logs. Returns count removed."""
    return cleanup_old_logs(keep=0)


def cleanup_all_crash_logs() -> int:
    """Remove ALL crash logs. Returns count removed."""
    return cleanup_crash_logs(keep=0)


def cleanup_all_backups() -> int:
    """Remove ALL backups. Returns count removed."""
    return cleanup_old_backups(keep=0)


def cleanup_extracted_all() -> int:
    """Remove all extracted mod files. Returns count removed."""
    import shutil
    extracted_dir = config.CACHE_EXTRACTED
    if not os.path.isdir(extracted_dir):
        return 0
    count = len(os.listdir(extracted_dir))
    try:
        shutil.rmtree(extracted_dir, ignore_errors=True)
        os.makedirs(extracted_dir, exist_ok=True)
    except OSError:
        return 0
    return count


def cleanup_downloads_all() -> int:
    """Remove all downloaded archives. Returns count removed."""
    downloads_dir = config.CACHE_DOWNLOADS
    if not os.path.isdir(downloads_dir):
        return 0
    files = os.listdir(downloads_dir)
    removed = 0
    for f in files:
        try:
            os.remove(os.path.join(downloads_dir, f))
            removed += 1
        except OSError:
            pass
    return removed


def get_space_freed_mb() -> float:
    """Estimate total size of all cache contents in MB."""
    total = 0
    for d in (config.CACHE_DOWNLOADS, config.CACHE_EXTRACTED, config.CACHE_BACKUPS, config.CACHE_LOGS):
        if not os.path.isdir(d):
            continue
        for root, dirs, files in os.walk(d):
            for f in files:
                total += os.path.getsize(os.path.join(root, f))
    return total / (1024 * 1024)

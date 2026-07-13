"""High-level install stages for the v2 installer:

    1. copy_sa           — clone the source SA folder to the destination
    2. backup            — back up the freshly-prepared dest folder
    3. install_mods      — download/locate + extract + merge each mod

The original source SA folder is NEVER modified — everything happens in the
destination folder. This produces a fully portable, standalone modded SA
install that the user can move, copy, or share.
"""
from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass, field
from typing import Callable, Optional

from . import backup, cache, config, downloader, extractor

log = logging.getLogger(__name__)

# Progress callback: (stage_id, stage_message, percent_0_100) -> None
ProgressCb = Callable[[str, str, int], None]


def _url_to_ext(url: str) -> str:
    """Extract the file extension from a download URL (e.g. '.zip', '.rar')."""
    if not url:
        return ""
    base = url.split("?")[0].split("/")[-1]
    if "." in base:
        return "." + base.rsplit(".", 1)[1].lower()
    return ""


# ----------------------------------------------------------------------
# Install context
# ----------------------------------------------------------------------
@dataclass
class InstallContext:
    # Source: where the user's vanilla SA install lives
    source_sa_root: str
    # Destination: where the wizard creates the standalone modded SA folder
    dest_sa_root: str

    # Mod source choice
    have_local_mods: bool = False
    archives_folder: Optional[str] = None       # only set if have_local_mods
    downloads_folder: Optional[str] = None      # user's Downloads folder to scan

    # Backup
    skip_backup: bool = False

    # Mod selection
    enabled_mod_ids: list[str] = field(default_factory=list)
    mod_sources: list[config.ModSource] = field(default_factory=list)

    # Callback: confirm_download(mod_name, mod_url) -> bool
    # Called before each auto-download. Return False to skip.
    confirm_download: Optional[Callable[[str, str], bool]] = None

    # Filled in during the run
    backup_path: Optional[str] = None
    installed_mods: list[str] = field(default_factory=list)
    failed_mods: list[str] = field(default_factory=list)


# ----------------------------------------------------------------------
# Stage: copy vanilla SA to destination
# ----------------------------------------------------------------------
# Files/folders we copy from the source SA install to the destination.
# Everything except user-specific save files and the uninstaller.
COPY_IGNORE_PATTERNS = shutil.ignore_patterns(
    "*.log", "*.tmp", "uninstall*", "Uninstall*", "config.dat",
    "gta_sa.set",  # user settings file — regenerated on first launch
)

COPY_SIZE_THRESHOLD = 100 * 1024 * 1024  # warn if a single file is > 100MB


def stage_copy_sa(ctx: InstallContext, progress: ProgressCb) -> bool:
    """Copy the entire source SA folder to ctx.dest_sa_root.

    This produces a complete, standalone SA install in the destination
    that we can then mod without touching the original.
    """
    src = ctx.source_sa_root
    dst = ctx.dest_sa_root
    if not src or not os.path.isdir(src):
        progress("copy", f"ERROR: source SA folder missing: {src}", 100)
        return False
    if not dst:
        progress("copy", "ERROR: destination folder not set.", 100)
        return False

    # Count files first for progress reporting
    progress("copy", "Counting source files...", 5)
    total = 0
    for _root, _dirs, files in os.walk(src):
        total += len(files)
    if total == 0:
        progress("copy", "ERROR: source SA folder is empty.", 100)
        return False

    os.makedirs(dst, exist_ok=True)
    progress("copy", f"Copying {total:,} files from source SA to destination...", 10)

    # Use shutil.copytree with dirs_exist_ok=True to merge into an existing dest.
    # We do our own file-by-file copy so we can report progress.
    copied = 0
    for root, dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        target_dir = dst if rel_root == "." else os.path.join(dst, rel_root)
        os.makedirs(target_dir, exist_ok=True)

        # Filter ignored patterns
        kept_files = [f for f in files if not _is_ignored(f)]
        for name in kept_files:
            src_file = os.path.join(root, name)
            dst_file = os.path.join(target_dir, name)
            try:
                # Always copy to ensure content is fresh (size-only check unreliable)
                shutil.copy2(src_file, dst_file)
            except Exception as e:
                log.warning("Failed to copy %s: %s", src_file, e)
            copied += 1
            if copied % 50 == 0:
                pct = 10 + int(copied * 80 / max(total, 1))
                progress("copy", f"Copied {copied:,}/{total:,} files...", pct)

    progress("copy", f"Done: copied {copied:,} files to {dst}", 100)
    return True


def _is_ignored(filename: str) -> bool:
    """True if the file matches our copy-ignore patterns."""
    lower = filename.lower()
    if lower.endswith(".log") or lower.endswith(".tmp"):
        return True
    if lower.startswith("uninstall"):
        return True
    if lower == "gta_sa.set":
        return True
    return False


# ----------------------------------------------------------------------
# Stage: backup
# ----------------------------------------------------------------------
def stage_backup(ctx: InstallContext, progress: ProgressCb) -> bool:
    """Back up the freshly-prepared destination folder before mods are applied."""
    if ctx.skip_backup:
        progress("backup", "Skipped (user choice).", 100)
        return True

    progress("backup", "Backing up destination folder...", 0)
    try:
        path = backup.backup_sa_root(ctx.dest_sa_root, progress=lambda c, t: progress(
            "backup", f"Backing up... {c}/{t} files", int(c * 100 / max(t, 1))
        ))
    except Exception as e:
        progress("backup", f"Backup failed: {e}", 100)
        log.exception("Backup failed")
        return False

    ctx.backup_path = path
    if path:
        progress("backup", f"Backup saved: {os.path.basename(path)}", 100)
    else:
        progress("backup", "Nothing to back up.", 100)
    return True


# ----------------------------------------------------------------------
# Stage: install a single mod
# ----------------------------------------------------------------------
def stage_install_mod(
    mod: config.ModSource,
    ctx: InstallContext,
    progress: ProgressCb,
) -> bool:
    """Download (or pull from cache/archives) → extract → merge into dest root."""
    stage_id = f"mod:{mod.id}"

    if mod.id not in ctx.enabled_mod_ids and not mod.is_main_mod:
        progress(stage_id, f"Skipped: {mod.name} (disabled).", 100)
        return True

    # ---- 1. Locate the archive -----------------------------------------
    archive_path: Optional[str] = None
    log.info("[%s] Searching for archive...", mod.id)

    # 1a. User's local archives folder (only if they said they have mods)
    if ctx.have_local_mods and ctx.archives_folder:
        archives = extractor.scan_archives(ctx.archives_folder,
                                            exclude_dirs=[config.CACHE_EXTRACTED])
        hit = extractor.find_mod_in_archives(archives, mod.id, mod.name, mod.file_matchers)
        if hit:
            progress(stage_id, f"Found local archive: {os.path.basename(hit)}", 20)
            archive_path = hit
            log.info("[%s] Found in archives folder: %s", mod.id, hit)

    # 1b. Shared cache (already-downloaded)
    if not archive_path:
        ext = _url_to_ext(mod.url)
        if cache.is_cached(mod.url, ext=ext):
            cached = cache.cache_path_for_url(mod.url, ext=ext)
            # Validate cached file is not HTML (Cloudflare block)
            try:
                with open(cached, "rb") as f:
                    header = f.read(8)
                is_html = header.startswith(b"\xef\xbb\xbf") or header.startswith(b"<!") or header.startswith(b"<html")
                if is_html:
                    log.warning("[%s] Cached file is HTML (Cloudflare block), removing: %s", mod.id, cached)
                    os.remove(cached)
                else:
                    archive_path = cached
                    progress(stage_id, "Using cached download.", 20)
                    log.info("[%s] Using cached: %s", mod.id, cached)
            except Exception:
                pass

    # 1b-extra. Scan Downloads folder if provided
    if not archive_path and ctx.downloads_folder:
        dl_archives = extractor.scan_archives(ctx.downloads_folder,
                                               exclude_dirs=[config.CACHE_EXTRACTED])
        hit = extractor.find_mod_in_archives(dl_archives, mod.id, mod.name, mod.file_matchers)
        if hit:
            progress(stage_id, f"Found in Downloads folder: {os.path.basename(hit)}", 20)
            archive_path = hit
            log.info("[%s] Found in Downloads: %s", mod.id, hit)

    # 1c. Download (only if user opted to download — i.e. not have_local_mods,
    #     OR they have local mods but we couldn't find this one locally)
    if not archive_path:
        if ctx.have_local_mods:
            progress(stage_id,
                     f"Not found in your archives folder. Skipping {mod.name}. "
                     "(Untick 'I have mods' on the mod-source page to download instead.)",
                     100)
            ctx.failed_mods.append(mod.id)
            return False

        # Ask user to confirm before auto-downloading
        if ctx.confirm_download:
            if not ctx.confirm_download(mod.name, mod.url):
                progress(stage_id, f"Skipped: {mod.name} (user declined download).", 100)
                ctx.failed_mods.append(mod.id)
                return False

        ext = _url_to_ext(mod.url)
        dest = cache.cache_path_for_url(mod.url, ext=ext)
        progress(stage_id, f"Downloading {mod.name}...", 25)
        try:
            def _dl_progress(done, total):
                if total:
                    pct = 25 + int(done * 50 / max(total, 1))
                else:
                    pct = 25
                progress(stage_id, f"Downloading {mod.name}... {done // 1024} KiB", pct)

            downloader.download(
                mod.url,
                dest,
                progress=_dl_progress,
                is_mediafire=mod.is_mediafire,
                is_github_release=mod.is_github_release,
                is_article_page=mod.is_article_page,
                is_libertycity=mod.is_libertycity,
            )
            archive_path = dest
        except Exception as e:
            hint = ""
            if mod.is_article_page:
                hint = (
                    f"  (Article-page mods like {mod.name} often sit behind "
                    "Cloudflare bot protection. Download the .zip manually "
                    f"from {mod.url}, then drop it in your archives folder "
                    "and re-run the wizard.)"
                )
            progress(stage_id, f"Download failed: {e}{hint}", 100)
            log.exception("Download failed for %s", mod.id)
            ctx.failed_mods.append(mod.id)
            return False

    # ---- 2. Extract or copy loose mod file -------------------------------
    # Loose mod files (.cleo, .cs, .asi) should be copied directly,
    # not extracted as archives.
    archive_ext = os.path.splitext(archive_path)[1].lower()
    if archive_ext in extractor.supported_mod_extensions():
        progress(stage_id, f"Installing {mod.name}...", 80)
        log.info("[%s] Loose mod file, copying directly: %s", mod.id, archive_path)
        try:
            if archive_ext == ".cleo":
                dest_dir = os.path.join(ctx.dest_sa_root, "CLEO")
            elif archive_ext == ".cs":
                dest_dir = os.path.join(ctx.dest_sa_root, "CLEO")
            else:
                dest_dir = ctx.dest_sa_root
            os.makedirs(dest_dir, exist_ok=True)
            dest_file = os.path.join(dest_dir, os.path.basename(archive_path))
            import shutil
            shutil.copy2(archive_path, dest_file)
            log.info("[%s] Copied %s -> %s", mod.id, archive_path, dest_file)
        except Exception as e:
            progress(stage_id, f"Install failed: {e}", 100)
            log.exception("Loose mod copy failed for %s", mod.id)
            ctx.failed_mods.append(mod.id)
            return False
        progress(stage_id, f"Done: {mod.name} (1 file).", 100)
        ctx.installed_mods.append(mod.id)
        return True

    extracted_dir = cache.extracted_dir_for(mod.id)
    cache.clear_extracted(mod.id)
    progress(stage_id, f"Extracting {mod.name}...", 75)
    log.info("[%s] Extracting to: %s", mod.id, extracted_dir)
    try:
        extractor.extract(archive_path, extracted_dir)
        file_count = sum(len(files) for _, _, files in os.walk(extracted_dir))
        log.info("[%s] Extracted %d files", mod.id, file_count)
    except Exception as e:
        progress(stage_id, f"Extraction failed: {e}", 100)
        log.exception("Extraction failed for %s", mod.id)
        ctx.failed_mods.append(mod.id)
        return False

    # Verify extraction produced files
    if not os.path.isdir(extracted_dir) or not os.listdir(extracted_dir):
        progress(stage_id, f"Extraction produced no files for {mod.name}.", 100)
        log.error("Extraction produced empty directory: %s", extracted_dir)
        ctx.failed_mods.append(mod.id)
        return False

    # ---- 3. Merge into DEST root (not source!) ------------------------
    progress(stage_id, f"Installing {mod.name} into destination...", 90)
    log.info("[%s] Merging %s -> %s", mod.id, extracted_dir, ctx.dest_sa_root)
    try:
        count = extractor.merge_into_sa_root(
            extracted_dir,
            ctx.dest_sa_root,
            pick_paths=mod.pick_paths or None,
        )
    except Exception as e:
        # Fallback: try file-by-file copy from extracted cache
        progress(stage_id, f"Batch merge failed ({e}), trying file-by-file...", 92)
        count = _fallback_copy(extracted_dir, ctx.dest_sa_root, mod, progress, stage_id)
        if count == 0:
            progress(stage_id, f"Install failed: {e}", 100)
            log.exception("Merge failed for %s", mod.id)
            ctx.failed_mods.append(mod.id)
            return False

    progress(stage_id, f"Done: {mod.name} ({count} files).", 100)
    ctx.installed_mods.append(mod.id)
    return True


def _fallback_copy(extracted_dir: str, dest_root: str, mod, progress, stage_id) -> int:
    """Fallback: copy files one-by-one from extracted cache, skipping failures."""
    count = 0
    failed = 0
    for root, _dirs, files in os.walk(extracted_dir):
        for name in files:
            src_file = os.path.join(root, name)
            rel = os.path.relpath(src_file, extracted_dir)
            dst_file = os.path.join(dest_root, rel)
            try:
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                # Use smart_overwrite - skip if identical, backup if different
                from .extractor import smart_overwrite
                smart_overwrite(src_file, dst_file)
                count += 1
            except Exception as e:
                failed += 1
                log.warning("Fallback copy failed for %s: %s", rel, e)
    if failed:
        progress(stage_id, f"Fallback: copied {count} files, {failed} failed.", 95)
    return count


# ----------------------------------------------------------------------
# Stage: install all mods in order
# ----------------------------------------------------------------------
def stage_install_all_mods(ctx: InstallContext, progress: ProgressCb) -> bool:
    """Run every mod in install_order. Failures of optional mods are non-fatal."""
    mods = ctx.mod_sources or config.ALL_MODS
    to_run = [m for m in mods if m.is_main_mod or m.id in ctx.enabled_mod_ids]
    total = len(to_run)
    if not total:
        progress("mods", "No mods selected.", 100)
        return True

    for i, mod in enumerate(to_run):
        overall_pct = int(i * 100 / total)
        progress("mods", f"[{i+1}/{total}] {mod.name}", overall_pct)

        def _wrapped(stage_id, msg, pct, _base=overall_pct, _span=int(100/total)):
            progress(stage_id, msg, min(100, _base + int(pct * _span / 100)))

        ok = stage_install_mod(mod, ctx, _wrapped)
        if not ok and not mod.optional:
            progress("mods", f"Aborting: required mod {mod.name} failed.", 100)
            return False

    progress("mods", f"All mods processed. OK={len(ctx.installed_mods)} FAIL={len(ctx.failed_mods)}", 100)
    return True


# ----------------------------------------------------------------------
# Full pipeline
# ----------------------------------------------------------------------
def run_full_install(ctx: InstallContext, progress: ProgressCb) -> bool:
    """Run every stage in order. Returns True if all critical stages passed."""
    cache.ensure_dirs()
    log.info("=== Full install started ===")
    log.info("Source: %s", ctx.source_sa_root)
    log.info("Destination: %s", ctx.dest_sa_root)
    log.info("Downloads folder: %s", ctx.downloads_folder)
    log.info("Enabled mods: %s", ctx.enabled_mod_ids)

    if not stage_copy_sa(ctx, progress):
        log.error("SA copy failed")
        return False

    if not stage_backup(ctx, progress):
        progress("backup", "WARNING: Backup failed — continuing anyway.", 100)
        log.warning("Backup failed")

    if not stage_install_all_mods(ctx, progress):
        log.error("Mod installation failed")
        return False

    log.info("=== Full install completed OK ===")
    return True

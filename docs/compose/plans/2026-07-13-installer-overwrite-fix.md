# Installer Overwrite & Completion Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix file overwrite logic, installer completion handling, backup bug, clean up dead code, and reduce build footprint to ~50MB.

**Architecture:** Consolidate all overwrite logic into a single `safe_overwrite()` utility function. Fix wizard flow bugs. Remove unused files and cross-platform stubs. Target x64 Windows 7+ only.

**Tech Stack:** Python 3.10+, PySide6, shutil, os, logging

## Global Constraints

- Target platform: x64 Windows 7+ only
- Build footprint target: ~50MB (PyInstaller)
- All file operations must use proper error handling (no bare except)
- All overwrite operations use consolidated `safe_overwrite()` function
- Preserve `.old` backup mechanism for user safety

---

## File Structure

**Modified Files:**
- `src/extractor.py` - Add `safe_overwrite()`, remove dead code
- `src/installer_stages.py` - Use `safe_overwrite()`, fix size-only dedup
- `src/ui/setup_page.py` - Fix backup skip bug
- `src/ui/install_page.py` - Fix completion flow, add logging import

**Deleted Files:**
- `src/ui/destination_page.py` (unused)
- `src/ui/source_sa_page.py` (unused)
- `src/ui/downgrade_page.py` (if exists, unused)
- `src/ui/download_window.py` (unused Xbox download assistant)

**No New Files** - Consolidate into existing modules

---

## Task 1: Add safe_overwrite utility to extractor.py

**Covers:** S1, S2, S3 (overwrite logic consolidation)

**Files:**
- Modify: `src/extractor.py:1-20` (imports), `src/extractor.py:300-370` (new function)

**Interfaces:**
- Consumes: None
- Produces: `safe_overwrite(src: str, dst: str) -> bool`

- [ ] **Step 1: Add imports and function definition**

```python
# At top of extractor.py, after existing imports
import logging

log = logging.getLogger(__name__)
```

- [ ] **Step 2: Add safe_overwrite function after merge_into_sa_root**

```python
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
```

- [ ] **Step 3: Run syntax check**

Run: `python -m py_compile src/extractor.py`
Expected: No output (success)

---

## Task 2: Refactor extractor.py to use safe_overwrite and remove dead code

**Covers:** S1, S2, S3, S8

**Files:**
- Modify: `src/extractor.py:348-395` (merge_into_sa_root and _copy_tree)

**Interfaces:**
- Consumes: `safe_overwrite()` from Task 1
- Produces: Refactored functions using safe_overwrite

- [ ] **Step 1: Refactor merge_into_sa_root file copy section**

Replace lines 348-361 with:
```python
                # Use safe_overwrite for consistent behavior
                if not safe_overwrite(src, dst):
                    log.warning("Failed to copy %s", src)
                else:
                    log.info("Merged: %s -> %s", os.path.basename(src), dst)
                count += 1
```

- [ ] **Step 2: Refactor _copy_tree to use safe_overwrite**

Replace lines 380-393 with:
```python
            # Use safe_overwrite for consistent behavior
            if not safe_overwrite(src_file, dst_file):
                log.warning("Failed to copy %s", src_file)
            else:
                log.info("Copied: %s", os.path.basename(src_file))
            count += 1
```

- [ ] **Step 3: Remove duplicate return statement**

Delete line 395 (the second `return count`)

- [ ] **Step 4: Run syntax check**

Run: `python -m py_compile src/extractor.py`
Expected: No output (success)

---

## Task 3: Fix installer_stages.py to use safe_overwrite and improve error handling

**Covers:** S1, S2, S3, S4, S7

**Files:**
- Modify: `src/installer_stages.py:119-130` (size-only dedup), `src/installer_stages.py:373-376` (fallback copy)

**Interfaces:**
- Consumes: `safe_overwrite()` from Task 1
- Produces: Improved file copy logic

- [ ] **Step 1: Fix size-only dedup in stage_copy_sa**

Replace lines 122-126 with:
```python
            try:
                # Always copy to ensure content is fresh (size-only check unreliable)
                shutil.copy2(src_file, dst_file)
            except Exception as e:
                log.warning("Failed to copy %s: %s", src_file, e)
            copied += 1
```

- [ ] **Step 2: Fix fallback copy to use safe_overwrite**

Replace lines 373-376 with:
```python
            try:
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                # Use safe_overwrite instead of os.remove + copy2
                from .extractor import safe_overwrite
                safe_overwrite(src_file, dst_file)
                count += 1
```

- [ ] **Step 3: Run syntax check**

Run: `python -m py_compile src/installer_stages.py`
Expected: No output (success)

---

## Task 4: Fix backup skip bug in setup_page.py

**Covers:** S5

**Files:**
- Modify: `src/ui/setup_page.py:226` (remove skip_backup override)

**Interfaces:**
- Consumes: None
- Produces: Respects user's backup choice from WelcomePage

- [ ] **Step 1: Remove the unconditional skip_backup override**

Delete or comment out line 226:
```python
        # REMOVED: self.wizard().setProperty("skip_backup", True)
        # Now respects user's choice from WelcomePage
```

- [ ] **Step 2: Run syntax check**

Run: `python -m py_compile src/ui/setup_page.py`
Expected: No output (success)

---

## Task 5: Fix installer completion flow in install_page.py

**Covers:** S6, S9

**Files:**
- Modify: `src/ui/install_page.py:167-194` (_on_finished method)

**Interfaces:**
- Consumes: None
- Produces: Only advances wizard on success

- [ ] **Step 1: Add logging import at module level**

Add after line 8:
```python
import logging
```

- [ ] **Step 2: Fix _on_finished to only advance on success**

Replace lines 167-194 with:
```python
    def _on_finished(self, ok: bool):
        self._ok = ok
        # Auto-save log to cache
        try:
            log_path = os.path.join(cache.CACHE_LOGS,
                                    f"install_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(self.log.toPlainText())
        except Exception:
            pass

        from PySide6.QtWidgets import QWizard
        self.wizard().setButtonLayout([
            QWizard.BackButton, QWizard.NextButton, QWizard.FinishButton,
            QWizard.CancelButton,
        ])
        if ok:
            self.stage_label.setText(
                "<span style='color:#5bff8a;font-weight:bold;'>INSTALL COMPLETE!</span>"
            )
            self.progress.setValue(100)
            # Show cleanup dialog
            self._show_cleanup_dialog()
            self.wizard().next()
        else:
            self.stage_label.setText(
                "<span style='color:#ff5b5b;font-weight:bold;'>INSTALL FAILED — see log.</span>"
            )
            # Do NOT advance wizard on failure
```

- [ ] **Step 3: Run syntax check**

Run: `python -m py_compile src/ui/install_page.py`
Expected: No output (success)

---

## Task 6: Delete unused page files

**Covers:** S10 (code cleanup)

**Files:**
- Delete: `src/ui/destination_page.py`
- Delete: `src/ui/source_sa_page.py`
- Delete: `src/ui/downgrade_page.py` (if exists)
- Delete: `src/ui/download_window.py`

**Interfaces:**
- Consumes: None
- Produces: Reduced codebase size

- [ ] **Step 1: Verify files are not imported anywhere**

Run: `grep -r "destination_page\|source_sa_page\|downgrade_page\|download_window" src/`
Expected: No results or only self-references

- [ ] **Step 2: Delete the files**

```bash
del src\ui\destination_page.py
del src\ui\source_sa_page.py
del src\ui\download_window.py
```

- [ ] **Step 3: Verify project still works**

Run: `python -m py_compile src/ui/wizard.py`
Expected: No output (success)

---

## Task 7: Remove cross-platform stubs from sa_detector.py

**Covers:** S10 (platform targeting)

**Files:**
- Modify: `src/sa_detector.py` (remove macOS/Linux detection stubs)

**Interfaces:**
- Consumes: None
- Produces: Windows-only code, smaller footprint

- [ ] **Step 1: Read sa_detector.py to find cross-platform stubs**

Look for `_from_steam_mac` and `_from_steam_linux` function references

- [ ] **Step 2: Remove or comment out cross-platform detection code**

Remove macOS/Linux specific code paths, keep only Windows detection

- [ ] **Step 3: Run syntax check**

Run: `python -m py_compile src/sa_detector.py`
Expected: No output (success)

---

## Task 8: Optimize imports to reduce build footprint

**Covers:** S10 (build size optimization)

**Files:**
- Modify: `src/installer.py` (lazy imports)
- Modify: `src/ui/*.py` (lazy imports where possible)

**Interfaces:**
- Consumes: None
- Produces: Reduced PyInstaller bundle size

- [ ] **Step 1: Move PySide6 imports to be lazy where possible**

In wizard.py, theme.py, and other UI files, move PySide6 imports inside functions that use them

- [ ] **Step 2: Remove unused imports across all files**

Run: `python -m py_compile src/*.py src/ui/*.py` to verify no import errors

- [ ] **Step 3: Test build**

Run: `python build_portable.bat` or equivalent PyInstaller command
Expected: Build succeeds, check output size

---

## Task 9: Verify and test all changes

**Covers:** S1-S10 (verification)

**Files:**
- None (verification only)

**Interfaces:**
- Consumes: All previous tasks
- Produces: Verified working installer

- [ ] **Step 1: Run syntax check on all modified files**

```bash
python -m py_compile src/extractor.py
python -m py_compile src/installer_stages.py
python -m py_compile src/ui/setup_page.py
python -m py_compile src/ui/install_page.py
python -m py_compile src/ui/wizard.py
python -m py_compile src/sa_detector.py
```

- [ ] **Step 2: Run installer in test mode**

```bash
python installer.py --test
```
Expected: Wizard launches without errors

- [ ] **Step 3: Test overwrite logic**

Create test scenario:
1. Run installer with a test mod
2. Run installer again with same mod
3. Verify .old files are created and new files overwrite correctly

- [ ] **Step 4: Test backup feature**

1. Run installer with backup enabled
2. Verify backup is created in cache/backups/
3. Run installer with backup disabled
4. Verify no backup is created

- [ ] **Step 5: Test failure handling**

1. Simulate a failed mod installation
2. Verify wizard does NOT advance to CompletePage
3. Verify error message is displayed

- [ ] **Step 6: Build and check footprint**

Run PyInstaller build
Expected: Output ~50MB or less

---

## Task 10: Commit changes

**Covers:** All

**Files:**
- All modified files

**Interfaces:**
- Consumes: All previous tasks
- Produces: Committed code

- [ ] **Step 1: Stage all changes**

```bash
git add -A
```

- [ ] **Step 2: Create commit**

```bash
git commit -m "fix: consolidate overwrite logic, fix installer completion, remove dead code

- Add safe_overwrite() utility for consistent file replacement
- Fix setup_page.py backup skip bug
- Fix install_page.py to not advance on failure
- Remove unused pages (destination_page, source_sa_page)
- Remove cross-platform stubs (target x64 Windows 7+)
- Remove duplicate return statement in _copy_tree
- Add logging import to install_page.py
- Improve error handling throughout"
```

- [ ] **Step 3: Verify build**

Run PyInstaller and verify ~50MB output

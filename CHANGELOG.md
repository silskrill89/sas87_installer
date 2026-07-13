# GTA San Andreas Stories 1987 — Installer Changelog

Cumulative: each version includes all changes from previous versions.
Version format: CalVer YYMM.patch (e.g. v2607.0)

---

## v2607.0 (2026-07-13)

NEW:
- CalVer versioning (YYMM.patch) — aligns with Open 3D Foundation convention
- Smart file overwrite — only copies files that have changed
- Local folder scanning before site scraping — faster, fewer network calls
- Manual download support for Cloudflare-protected mods
- SAS 1987 Team branding throughout

CHANGED:
- Simplified README for better readability
- Removed references to unnecessary dependencies
- Updated Discord invite link

FIXED:
- Overwrite logic consolidated into single function
- Wizard only advances on success (not failure)
- Backup respects user choice (no longer auto-skipped)

---

## v5.0.2.0 (2026-06-26)

NEW:
- Per-mod file matchers — download window only detects matching archive
- Fallback: shows all archives if no matchers match
- Backup skips files >100MB, uses ZIP_STORED for files >5MB (no freeze)
- Progress reported every 10 files instead of every file (smoother UI)

FIXED:
- Backup freeze at 283/402 files (large audio files caused zip compression hang)
- CLEOPlus.zip detected for every mod instead of just CLEO+ mod

CHANGED:
- Body text color #c8bca8 → #c0c0c0 (brighter, more readable)
- Dim text color #7a7068 → #999999 (was too dark)
- Minimum font size 12pt across all UI elements
- Content panel: rounded corners (12px radius, Vista Aero style)
- GroupBox: rounded corners (10px radius)
- Buttons: rounded corners (6px radius)
- Log pane: rounded corners (8px radius)
- QWizardPage: padding for proper content positioning inside panel
- Log pane font 9pt → 12pt

---

## v5.0.1.0 (2026-06-26)

NEW:
- Close confirmation prompt — "Are you sure?" with settings-save notice
- Persistent settings — saves SA source, destination, archives folder, enabled mods
- Settings auto-restored next run from same install location
- Parallax slideshow: FG and BG layers move in opposite directions
- More dramatic Ken Burns scaling (FG: 1.18→1.02, BG: 0.92→1.08)

FIXED:
- QFileDialog native dialog crash on Windows 10 (DontUseNativeDialog + styled Qt dialog)
- File dialogs across all pages now use readable styled fallback

CHANGED:
- All QFileDialog calls use browse_folder/browse_file/browse_save_file helpers from theme.py

---

## v5.0.0.1 (2026-06-26)

FIXED:
- Parallax slideshow jittering: switched from frame-counting to QElapsedTimer with smoothstep easing
- download_window.py crash: _watch_timer AttributeError (hasattr guard)
- _MEI temp directory cleanup path typo
- install_page.py unused import cleanup

CHANGED:
- SynthwaveBackground uses smoothstep easing for jitter-free parallax movement
- Two-layer parallax: FG (sharp, 45% opacity) + BG (inpainted, 35% opacity)
- "Open Save Folder" button validates download page was opened first
- CREDITS button moved to wizard bottom bar (same line as BACK/NEXT/CANCEL)

---

## v1.3 (2026-06-26)

NEW:
- Rockstar Games website-style theme (dark, gritty, gold accents)
- VCS neon color palette (purple, teal, pink, sunset amber)
- Late 80s LA skyline silhouette with palm trees and neon signs
- Credits window with scrolling credits (name + link per row)
- Support Creators popup (Patreon/donation links for Seemann, Junior_Djjr, etc.)
- Credits button on Welcome and Completion pages
- Startup cleanup: prunes old logs (keep 10), backups (keep 5), crash logs (keep 3)
- Orphaned PyInstaller _MEI* temp directory cleanup
- Cache consolidation: moves orphaned cache from Downloads/Documents
- Post-install cleanup dialog (remove downloads, extracted files, logs, backups)
- DYOM 8.3 Alpha option added alongside DYOM 8.1 stable
- Working DYOM download URLs (old gtagames.nl links were 404)
- Download mirrors: every mod now shows 2-3 alternative download sources
- Empty archives folder validation: warns and halts if "I have mods" but folder is empty

FIXED:
- DYOM download URL was broken (dyom.gtagames.nl → 404)
- install_page.py cleanup dialog wired to post-install flow

CHANGED:
- Download window now shows mirror buttons for each mod
- Theme palette: Grove Street green is now an accent, not dominant
- Headings use gold (#f0c060), subheadings use teal (#00d4aa)
- Buttons: gold border, teal hover, dark backgrounds

---

## v1.2 (2026-06-26)

NEW:
- Xbox-easy download assistant window (one-click browser open + folder watcher)
- Random mod screenshot frame in wizard background
- Screenshot cache: downloads 30 images from GitHub repos at startup
- Cross-platform OS detection (Windows, macOS, Linux)
- Cross-platform file manager and exe launch helpers

FIXED:
- PySide6 font loading crash (access violation) — deferred QFontDatabase to apply_theme()
- scraper.py _with_url() was dropping manual_download_required and other fields
- sa_detector.py referenced non-existent config constants
- Removed unused local imports
- installer_stages.py had duplicated URL-to-extension logic
- Duplicate QWizard import in theme.py

CHANGED:
- Removed unused dependencies
- Cached splash images and scanlines for paintEvent performance

---

## v1.1 (2026-06-26)

NEW:
- Lean PyInstaller build: 77MB → 48.5MB (7z compressed)
- Manual DLL/plugin selection instead of collect_all('PySide6')
- Only Qt6Core, Qt6Gui, Qt6Widgets bundled (all other Qt DLLs removed)
- Removed unused .pyd files from bundle
- Removed Pillow/PIL from bundle (screenshot cache has fallback)

FIXED:
- Exe was 318MB due to collecting all PySide6 modules
- Unnecessary Qt modules bundled (Qt6Svg, Qt6Network, Qt6OpenGL, etc.)

---

## v1.0 (2026-06-26)

NEW:
- Initial release
- Full installer wizard: source detection, copy, backup, mod install
- Auto-detection of GTA San Andreas install (registry, Steam, common paths)
- Mod provides its own exe (no NO-CD needed)
- MediaFire resolver for main mod download
- GitHub release resolver for CLEO 5
- Mod selection page with optional/required toggles
- Progress log with save-to-file
- Backup/restore system
- Crash log handler with GUI dialog
- PricedownBl font (GTA-style)
- GTA San Andreas sunset theme with LA skyline and palm trees

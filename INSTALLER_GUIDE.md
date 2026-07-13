# GTA San Andreas Stories 1987 — Installer Guide & Credits

**v2607.0** — Built by the SAS 1987 Team

Fan-made tool. Not affiliated with Rockstar Games or Take-Two Interactive.
GTA San Andreas is required and must be legally purchased.

---

## Introduction

This document is the canonical reference for the GTA San Andreas Stories 1987 Installer — a fan-made Python tool that builds a fully portable, standalone modded San Andreas install.

**For end users:** You only need to read the Credits section to understand who built what.

**For developers:** Jump to the Fork Guide to rebuild, modify, or extend the installer.

---

## Credits & Attribution

### GTA San Andreas Stories 1987 — Mod Team

This installer exists only to make it easier to install the GTA San Andreas Stories 1987 total-conversion mod. All credit for the mod itself belongs to its development team.

- **Official site:** https://gtasas.netlify.app/
- **Discord:** https://discord.gg/DbVQqJqYg7

### Project Lead

| Name | Role |
|------|------|
| cerdopalo | Project Creator & Lead |

### Mod Team

| Name | Contribution |
|------|--------------|
| Rule Breakers | Mappings and models |
| Cheseg Remastered | Missions and feedback |
| Karammii | Testing and billboards |
| Abdullah | Missions, models, scripts, testing |
| NorthStationX | Billboards and retextures |
| Nightlaw | Screenshots, testing, trailer clips |
| FrankoU | Manual writing and mappings |
| Mike | Missions and feedback |
| GTAMissionsCreator | Video recording and testing |
| bolszewik | Testing and screenshots |
| 14todoeltiempodc | Retextures |
| Elrico | Testing, feedback, screenshots |
| Tix | Mission testing and screenshots |

### DYOM — Design Your Own Mission

| Name | Role |
|------|------|
| Dutchy3010 | DYOM co-creator |
| PatrickW | DYOM co-creator |

### CLEO Library

| Name | Role |
|------|------|
| Seemann | CLEO Library creator |
| Alien | CLEO for GTA SA |
| Deji | CLEO for GTA SA |
| LINK/2012 | ModLoader |

### CLEO+

| Name | Role |
|------|------|
| Junior_Djjr | CLEO+ creator, MixMods founder |

### NewOpcodes

| Name | Role |
|------|------|
| DK22Pac | NewOpcodes, plugin-sdk |

### Special Thanks

- Rockstar Games — For creating GTA San Andreas
- The GTA modding community — For keeping this game alive
- GTAForums.com — Community hub

---

## Supporting Mods

The GTA SAS 1987 mod already bundles all required dependencies. The installer offers these as optional extras for users who want to update them independently.

| Mod | Source | Author | License |
|-----|--------|--------|---------|
| CLEO 5 | github.com/cleolibrary/CLEO5 | CLEO Library team | BSD 3-Clause |
| CLEO+ | github.com/JuniorDjjr/CLEOPlus | JuniorDjjr | See repo README |
| NewOpcodes | mixmods.com.br | DK22Pac | See MixMods page |
| DYOM 8.1 | Bundled in main mod | Dutchy3010 & PatrickW | Free for personal use |

---

## Tools & Services

| Service | Used for |
|---------|----------|
| LibertyCity.net | Fallback search when main mod isn't on official site |
| MixMods.com.br | Original article pages for CLEO+ and NewOpcodes |
| GitHub | Source hosting for CLEO 5, CLEO+ |
| MediaFire | Hosts the official GTA SAS 1987 main mod archive |
| Pricedown Bl font | The actual GTA logo typeface (free for commercial use) |

---

## Python Dependencies

| Library | Author | License |
|---------|--------|---------|
| PySide6 (Qt6) | The Qt Company | LGPL v3 |
| requests | Kenneth Reitz | Apache 2.0 |
| beautifulsoup4 | Leonard Richardson | MIT |
| py7zr | Hiroshi Miura | LGPL-3.0 |

---

## Legal Disclaimer

This installer is a fan-made tool and is not affiliated with, endorsed by, or sponsored by Rockstar Games, Take-Two Interactive, or any of the mod authors listed above.

- GTA San Andreas is a trademark of Rockstar Games / Take-Two Interactive
- You must own a legal copy of the game to use this installer
- The installer does not distribute the game, mod, or copyrighted assets
- It only downloads them from official sources at install time

If you are a copyright holder and believe any part of this installer infringes your rights, please open an issue and we will address it promptly.

---

# Fork Guide — How to Rebuild the Installer

This section is for developers who want to fork, modify, or extend the installer.

## 1. Project Layout

```
installer.py              — Application entry point
src/
  config.py               — Mod URLs, version constants, cache paths
  cache.py                — Shared cache manager
  sa_detector.py          — Locates GTA SA install (registry/Steam/paths)
  scraper.py              — Scrapes gtasas.netlify.app for live mod URLs
  downloader.py           — HTTP downloader + link resolvers
  extractor.py            — Archive extraction + merge into SA root
  backup.py               — Backup originals to .zip
  installer_stages.py     — Install pipeline (copy → backup → mods)
  screenshot_cache.py     — Download mod screenshots
  settings.py             — Persistent user settings (JSON)
  util.py                 — Cross-platform helpers
  ui/
    theme.py              — VCS dark-green palette + Pricedown font
    wizard.py             — QWizard subclass + page wiring
    welcome_page.py       — Welcome + backup checkbox
    mod_source_page.py    — "I have mods" vs "Download for me"
    setup_page.py         — Source SA + destination folder
    prereqs_page.py       — Mod selection grid
    install_page.py       — Progress + log during install
    complete_page.py      — Summary + launch button
    credits_window.py     — Credits/attribution window
    cleanup_dialog.py     — Post-install cleanup
    splash/               — Slideshow images (any .png added appears in slideshow)
data/
  exe_hashes.json         — SA exe version detection (optional)
fonts/
  PricedownBl.otf         — GTA logo font
tools/
  build_release.py        — Build versioned release archives
  render_pages.py         — Render wizard pages to PNG for screenshots
```

## 2. Data Flow

1. User clicks through wizard pages, setting properties on the wizard
2. InstallPage reads all properties and constructs an `InstallContext`
3. Context is passed to `installer_stages.run_full_install()` on a worker thread
4. Stages run sequentially: copy SA → backup → install mods
5. Each stage reports progress via callback (Qt signals back to UI thread)

**Mod install order** is determined by `install_order` field on each ModSource:
- CLEO 5 (#10)
- CLEO+ (#20)
- NewOpcodes (#30)
- DYOM (#40)
- GTA SAS 1987 main mod (#100)

## 3. Adding a New Mod

1. Add a `ModSource` entry to `src/config.py`
2. Set `install_order` to control when it runs
3. Set resolver flag: `is_mediafire`, `is_github_release`, `is_article_page`, or `is_libertycity`
4. If new host, add resolver to `src/downloader.py`
5. Test with full install

## 4. Adding a New Wizard Page

1. Create `src/ui/my_new_page.py`, subclass `QWizardPage`
2. Set `splash_image_name` class attribute (any .png in `src/ui/splash/`)
3. Add `PAGE_ID` constant to `src/ui/wizard.py`
4. Register page in `InstallerWizard.__init__`
5. Update `nextId()` of preceding page

## 5. Building the Standalone .exe

```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller>=6.0

# Build
python -m PyInstaller installer.spec --noconfirm

# Output
dist/GTA_SAS_1987_Installer.exe
```

## 6. Building a Release Archive

```bash
python tools/build_release.py
```

Output: `dist/GTA_SAS_1987_Installer_v2607.0.7z`

## 7. Customizing the Theme

- Colors: Edit `COLOR_*` constants in `src/ui/theme.py`
- Stylesheet: Edit QSS in `theme.py`
- Slideshow: Add any `.png` to `src/ui/splash/`

## 8. Testing

```bash
# Syntax check
python -m py_compile installer.py src/*.py src/ui/*.py

# Scraper test
python -c "from src import scraper; print(scraper.resolve_mod_sources())"

# Full test
python installer.py
```

## 9. Licensing

- **Installer code:** MIT or Apache 2.0 recommended
- **PySide6 (Qt6):** LGPL v3 — free for commercial use
- **Pricedown Bl font:** Free for commercial use (keep FONT_LICENSE.html)
- **Mod:** Property of its authors — download only, don't redistribute

---

*End of guide. For questions, open an issue on the project repository.*
*For mod-specific questions, visit https://gtasas.netlify.app/ or join https://discord.gg/DbVQqJqYg7*

# GTA San Andreas Stories 1987 — Installer

A standalone installer for the **GTA San Andreas Stories 1987** total-conversion mod.

*Made with love by the [GTA SAS 1987](https://gtasas.netlify.app/) team.*

---

## General Information

- **Website:** https://gtasas.netlify.app/
- **Discord:** https://discord.gg/DbVQqJqYg7
- **Source code:** https://github.com/silskrill89/sas87_installer
- **Issue tracker:** https://github.com/silskrill89/sas87_installer/issues

---

## What is this?

Installing GTA mods shouldn't require a CS degree. This wizard takes you from a clean GTA San Andreas install to a fully modded, story-ready setup without touching a single config file.

**What you get:**
- A complete, standalone modded GTA San Andreas folder
- Your original install stays untouched — always
- All dependencies handled automatically
- One-click launch when you're done

---

## How it works

```
Pick your SA folder → Auto-detect & download → Copy & install → Play
```

1. Point to your GTA San Andreas install (auto-detected from Steam, registry, or common paths)
2. Pick where you want the modded version to live
3. We handle everything — copy, download, install, backup
4. Hit Play. You're playing.

> **Note:** Some mods require manual download due to creator hosting preferences. Links and credits are provided in the installer to respect the wishes of original mod creators.

---

## Features

| Feature | Description |
|---------|-------------|
| Auto-detect SA | Finds your install via Steam, registry, or common paths |
| Smart downloads | Scans your local folders first, only downloads what's missing |
| Live mod URLs | Pulls the latest download links from gtasas.netlify.app |
| Portable installs | Your original SA is never touched |
| Backup system | Automatic backups before any changes |
| Shared cache | Re-runs are instant — downloads are cached |

---

## Installation

### For players

1. Download `GTA_SAS_1987_Installer.exe`
2. Run it — no Python needed
3. Follow the 4-step wizard
4. Play

### Requirements

- **GTA San Andreas** — any version works (the mod provides its own exe)
- **Windows 7+** (x64)

---

## For developers

```bash
git clone https://github.com/silskrill89/sas87_installer.git
cd sas87_installer
pip install -r requirements.txt
python installer.py
```

### Build a standalone .exe

```bash
python -m PyInstaller installer.spec --noconfirm
```

Output: `dist/GTA_SAS_1987_Installer.exe`

---

## License

This is a **fan-made installer** — not affiliated with Rockstar Games or Take-Two Interactive.

- You need a legal copy of GTA San Andreas to use this
- The installer downloads mods from official sources at install time
- No copyrighted content is distributed with the installer itself

---

## Credits

This installer was built by the **GTA SAS 1987 Team** to make installing our mod easier.

### Project Lead

- **cerdopalo** — Project Creator & Lead

### Mod Team

- Rule Breakers — Mappings and models
- Cheseg Remastered — Missions and feedback
- Karammii — Testing and billboards
- Abdullah — Missions, models, scripts, testing
- NorthStationX — Billboards and retextures
- Nightlaw — Screenshots, testing, trailer clips
- FrankoU — Manual writing and mappings
- Mike — Missions and feedback
- GTAMissionsCreator — Video recording and testing

### DYOM — Design Your Own Mission

- Dutchy3010 & PatrickW — DYOM creators

### CLEO Library

- Seemann — CLEO Library creator
- Alien, Deji, LINK/2012 — CLEO for GTA SA

### CLEO+

- Junior_Djjr — CLEO+ creator, MixMods founder

### NewOpcodes

- DK22Pac — NewOpcodes, plugin-sdk

### Special Thanks

- Rockstar Games — For creating GTA San Andreas
- The GTA modding community — For keeping this game alive
- GTAForums.com — Community hub

### Built with

- PySide6 (Qt6) — Cross-platform GUI
- Pricedown Bl — The actual GTA logo font (free for commercial use)
- Vice City Stories palette — Dark greens, neon accents, sunset vibes

### AI Assistance

This installer was built with the help of:

- [MiMo v2.5](https://github.com/XiaomiMiMo/MiMo) — AI model
- [MiMoCode](https://github.com/XiaomiMiMo/MiMoCode) — AI coding assistant

Share your creations in the MiMoCode Discord showcase!

---

*See [CREDITS.md](CREDITS.md) for the complete list of contributors and supporting mods.*

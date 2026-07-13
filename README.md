# GTA San Andreas Stories 1987 — Installer

**Built by the SAS 1987 Team. One click. Full mod. Zero hassle.**

> The GTA San Andreas Stories 1987 mod is the total conversion you've been waiting for — full storyline, custom missions, new vehicles, the works. This installer gets you playing in minutes, not hours.

*Made with love by the [GTA SAS 1987](https://gtasas.netlify.app/) team.*

---

## Why this exists

Installing GTA mods shouldn't require a CS degree. We built this wizard so you can go from a clean GTA San Andreas install to a fully modded, story-ready setup without touching a single config file.

**What you get:**
- A complete, standalone modded GTA San Andreas folder
- Your original install stays untouched — always
- All dependencies handled automatically (CLEO 5, CLEO+, DYOM 8.1)
- Live mod links from the official site — never outdated
- One-click launch when you're done

---

## How it works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Pick your  │ ──▶ │  Auto-detect │ ──▶ │  Copy +     │ ──▶ │  Launch &    │
│  SA folder  │     │  & download  │     │  install    │     │  play        │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
```

**Step 1:** Point to your GTA San Andreas install (we auto-detect it from Steam, registry, or common paths)

**Step 2:** Pick where you want the modded version to live

**Step 3:** We handle everything:
- Copy your vanilla SA to the new folder
- Download & install CLEO 5, CLEO+, NewOpcodes
- Install the full GTA SAS 1987 modpack
- Back up your fresh install before touching anything

**Step 4:** Hit Launch. You're playing.

---

## Features that actually matter

| Feature | Why it matters |
|---------|----------------|
| **Auto-detect SA** | Finds your install via Steam, registry, or common paths — no manual browsing |
| **Smart downloads** | Scans your local folders first, only downloads what's missing |
| **Live mod URLs** | Pulls the latest download links from gtasas.netlify.app every run |
| **Portable installs** | Your original SA is never touched. The modded folder is self-contained |
| **Backup system** | Automatic backups before any changes. Restore anytime |
| **Shared cache** | Re-run the wizard? Downloads are cached. Instant setup |
| **Clean completion** | One-click launch when done. Open install folder, view logs, whatever |

---

## Quick start

### For players

1. **Download** the latest release
2. **Extract** anywhere
3. **Double-click** `run.bat` (or `GTA_SAS_1987_Installer.exe` if you have the portable build)
4. **Follow** the 4-step wizard
5. **Play**

> **Requires:** GTA San Andreas (v1.0 HOODLUM recommended). The mod provides its own exe.

### For developers

```bash
git clone https://github.com/silskrill89/sas87_installer.git
cd sas87_installer
pip install -r requirements.txt
python installer.py
```

---

## Requirements

- **GTA San Andreas** — v1.0 HOODLUM recommended (the mod includes its own exe)
- **Python 3.10+** — only needed if running from source
- **7-Zip or WinRAR** — for .rar extraction (optional)

---

## Built with

- **PySide6 (Qt6)** — cross-platform GUI
- **Pricedown Bl** — the actual GTA logo font (free for commercial use)
- **Vice City Stories palette** — dark greens, neon accents, sunset vibes

---

## Credits

This installer was built by the **GTA SAS 1987 Team** to make installing our mod easier.

**Official site:** [gtasas.netlify.app](https://gtasas.netlify.app/)

**Full credits:** See [CREDITS.md](CREDITS.md) for the complete list of mod contributors and supporting mods.

**Supporting mods:** CLEO 5, CLEO+, NewOpcodes, DYOM 8.1 — all credit to their respective authors.

---

## Disclaimer

This is a **fan-made installer** — not affiliated with Rockstar Games or Take-Two Interactive.

- You need a legal copy of GTA San Andreas to use this
- The installer downloads mods from official sources at install time
- No copyrighted content is distributed with the installer itself

**Questions?** Open an issue or join the [Discord](https://discord.gg/DbVQqJqYg7).

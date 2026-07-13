"""Translation system for the GTA SAS 1987 Installer.

Supports: English, Arabic, Spanish, Portuguese, Czech, Russian, Persian (Farsi)
"""
from __future__ import annotations

import os
import json
from typing import Optional

_current_lang = "en"
_translations: dict[str, str] = {}

# Available languages
LANGUAGES = {
    "en": "English",
    "ar": "العربية (Arabic)",
    "es": "Español (Spanish)",
    "pt": "Português (Portuguese)",
    "cs": "Čeština (Czech)",
    "ru": "Русский (Russian)",
    "fa": "فارسی (Persian/Farsi)",
}

# Default English strings
_DEFAULTS: dict[str, str] = {
    # App
    "app_title": "GTA San Andreas Stories 1987 — Installer",
    "app_subtitle": "Built by the SAS 1987 Team",

    # Welcome page
    "welcome_title": "WELCOME",
    "welcome_heading": "GTA San Andreas Stories 1987",
    "welcome_subheading": "Installer Wizard",
    "welcome_description": "This wizard will install the GTA San Andreas Stories 1987 total-conversion mod.\n\nThe mod provides its own exe — works with any version of GTA San Andreas.",
    "welcome_backup": "Create backup before installing",
    "welcome_backup_desc": "Recommended — backs up your fresh install before applying mods.",

    # Mod source page
    "mod_source_title": "MOD SOURCE",
    "mod_source_intro": "Do you already have the mod files downloaded on your computer, or should the wizard download them for you?",
    "mod_source_have": "I already have mod files",
    "mod_source_have_desc": "You have .zip / .rar / .7z archives of the mods already. The wizard will scan a folder and use them instead of downloading.",
    "mod_source_download": "Download everything for me",
    "mod_source_download_desc": "The wizard will fetch the main mod from MediaFire and prerequisites from GitHub.",
    "mod_source_choose": "Choose one",
    "mod_source_archives": "Archives folder",
    "mod_source_archives_desc": "Point the wizard at the folder containing your mod archives. It will scan for .zip / .rar / .7z and use them instead of downloading.",
    "mod_source_browse": "Browse...",
    "mod_source_downloads": "Downloads folder",
    "mod_source_scan": "Scan my Downloads folder for mod files",

    # Setup page
    "setup_title": "SETUP",
    "setup_source": "Source — Your GTA San Andreas folder",
    "setup_source_desc": "Point to your existing GTA San Andreas install. The wizard will copy these files to a new modded folder.",
    "setup_dest": "Destination — Modded install folder",
    "setup_dest_desc": "Pick where to create the standalone modded SA install. At least 5 GB free space recommended.",
    "setup_auto": "Auto-detect",
    "setup_suggest": "Suggest",

    # Prereqs page
    "prereqs_title": "MODS TO INSTALL",
    "prereqs_desc": "The wizard scans your folders for mod files. Click Download on any missing mod to open its download page.",
    "prereqs_browse": "Browse for Files...",
    "prereqs_rescan": "Rescan",
    "prereqs_found": "Found",
    "prereqs_missing": "Missing",
    "prereqs_download": "Download",
    "prereqs_ready": "All mods found — ready to install!",

    # Install page
    "install_title": "INSTALLING...",
    "install_complete": "INSTALL COMPLETE!",
    "install_failed": "INSTALL FAILED — see log.",
    "install_save_log": "Save log...",

    # Complete page
    "complete_title": "INSTALLATION COMPLETE",
    "complete_success": "All stages completed successfully!",
    "complete_source": "Source (vanilla SA):",
    "complete_dest": "Modded install:",
    "complete_mods": "Mods installed:",
    "complete_log": "Install log:",
    "complete_backup": "Backup location:",
    "complete_launch": "Play GTA San Andreas Stories 1987",
    "complete_open_dest": "Open install folder",
    "complete_open_cache": "Open cache folder",
    "complete_tip": "Your standalone modded install is fully portable — copy the destination folder anywhere. The original SA install was never modified.",

    # Language selection
    "lang_title": "SELECT LANGUAGE",
    "lang_desc": "Choose your preferred language for the installer.\n\nNote: The mod itself is only available in English.",
    "lang_continue": "Continue",

    # Common
    "btn_next": "Next",
    "btn_back": "Back",
    "btn_cancel": "Cancel",
    "btn_finish": "Finish",
    "btn_browse": "Browse...",
    "btn_close": "Close",

    # Status messages
    "status_scanning": "Scanning...",
    "status_found": "Found {count} mod archive(s)",
    "status_missing": "No files found",
    "status_ready": "Ready to install",
    "status_installing": "Installing...",
    "status_complete": "Installation complete!",
    "status_failed": "Installation failed",

    # Errors
    "error_no_sa": "No gta_sa.exe found. Pick the SA install root.",
    "error_same_folder": "Cannot be the same as source.",
    "error_inside_source": "Cannot be inside the source folder.",
    "error_no_space": "Not enough free space.",
    "error_pick_folder": "Please pick a valid folder.",

    # Credits
    "credits_title": "CREDITS",
    "credits_support": "Support Creators",
}


def set_language(lang_code: str) -> None:
    """Set the current language."""
    global _current_lang, _translations
    _current_lang = lang_code
    _translations = _load_translations(lang_code)


def get_language() -> str:
    """Get the current language code."""
    return _current_lang


def t(key: str, **kwargs) -> str:
    """Get translated string by key. Supports {placeholder} formatting."""
    text = _translations.get(key, _DEFAULTS.get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def _load_translations(lang_code: str) -> dict[str, str]:
    """Load translations for a language. Falls back to English."""
    if lang_code == "en":
        return dict(_DEFAULTS)

    # Try to load from file
    i18n_dir = os.path.dirname(os.path.abspath(__file__))
    lang_file = os.path.join(i18n_dir, f"{lang_code}.json")

    if os.path.isfile(lang_file):
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge with defaults (English fallback for missing keys)
            result = dict(_DEFAULTS)
            result.update(data)
            return result
        except Exception:
            pass

    # Fallback to English
    return dict(_DEFAULTS)


def get_available_languages() -> dict[str, str]:
    """Return dict of available language codes and names."""
    return dict(LANGUAGES)

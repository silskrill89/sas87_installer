"""Persistent user settings — saved as JSON next to the installer .exe.

Restores: archives folder, destination folder, SA source, enabled mods,
and last page reached. Loaded on startup, saved on close.
"""
from __future__ import annotations

import json
import logging
import os
import sys

log = logging.getLogger(__name__)

_SETTINGS_FILE = "installer_settings.json"


def _settings_path() -> str:
    """Path to the JSON settings file, next to the .exe or script."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        base = os.path.dirname(here)  # project root
    return os.path.join(base, _SETTINGS_FILE)


def load_settings() -> dict:
    """Load settings from disk. Returns empty dict on any error."""
    path = _settings_path()
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        log.info("Loaded settings from %s", path)
        return data
    except Exception as e:
        log.warning("Failed to load settings: %s", e)
        return {}


def save_settings(data: dict) -> bool:
    """Save settings to disk. Returns True on success."""
    path = _settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        log.info("Saved settings to %s", path)
        return True
    except Exception as e:
        log.warning("Failed to save settings: %s", e)
        return False


def save_wizard_state(wizard) -> bool:
    """Extract and save all relevant wizard state for next run."""
    data = {}
    try:
        # Page fields
        sa_root = wizard.field("source_sa_root")
        if sa_root:
            data["source_sa_root"] = str(sa_root)

        dest_root = wizard.field("dest_root")
        if dest_root:
            data["dest_root"] = str(dest_root)

        mod_archives = wizard.field("mod_archives")
        if mod_archives:
            data["mod_archives"] = str(mod_archives)

        # Wizard properties
        for key in ("have_local_mods", "archives_folder", "enabled_mod_ids",
                     "install_in_subfolder", "subfolder_name"):
            val = wizard.property(key)
            if val is not None:
                data[key] = val

        # Last page reached
        data["last_page_id"] = wizard.currentId()

    except Exception as e:
        log.warning("Failed to capture wizard state: %s", e)

    return save_settings(data)


def restore_wizard_state(wizard, settings: dict) -> None:
    """Apply saved settings back into wizard fields and properties."""
    if not settings:
        return

    try:
        if "source_sa_root" in settings:
            wizard.setField("source_sa_root", settings["source_sa_root"])
        if "dest_root" in settings:
            wizard.setField("dest_root", settings["dest_root"])
        if "mod_archives" in settings:
            wizard.setField("mod_archives", settings["mod_archives"])

        for key in ("have_local_mods", "archives_folder", "enabled_mod_ids",
                     "install_in_subfolder", "subfolder_name"):
            if key in settings:
                wizard.setProperty(key, settings[key])

        # Skip to last page if it's valid (don't jump past page 1 on fresh run)
        last_page = settings.get("last_page_id", 0)
        if last_page and last_page > 1:
            # Only restore if not too far (max page_backup = 1 page back)
            wizard.setProperty("_restore_page", last_page)

    except Exception as e:
        log.warning("Failed to restore wizard state: %s", e)

"""Central configuration for the GTA SAS 1987 Installer.

All mod URLs, paths, version constants, and tunable defaults live here.
Edit this file to add/remove mods or point at different mirrors.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional


# ----------------------------------------------------------------------
# App identity
# ----------------------------------------------------------------------
APP_NAME = "GTA San Andreas Stories 1987 — Installer"
APP_SHORT = "GTA SAS 1987 Installer"
APP_VERSION = "5.0.2.0"
APP_AUTHOR = "Fan-made installer"

# OS detection — used throughout the codebase for cross-platform logic
IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

# Landing page the wizard scrapes for the official mod list.
MOD_SITE_URL = "https://gtasas.netlify.app/"

# Direct MediaFire link for the main mod archive (June 2026 build).
MAIN_MOD_MEDIAFIRE_URL = "https://www.mediafire.com/file/7e4lbbv76k3s0c8/GTA_SAS_june_2026.rar/file"

# LibertyCity.net — alternative download source for GTA SA mods.
# Search URL template — {q} is replaced with the search query (URL-encoded).
LIBERTYCITY_SEARCH_URL = "https://libertycity.net/index.php?do=files&op=search&search_text={q}"

# ----------------------------------------------------------------------
# Filesystem layout — cache/ folder next to the script (or .exe)
# ----------------------------------------------------------------------
# The cache lives in a 'cache/' subfolder of the directory the installer
# was launched from. This keeps the install fully portable — extract the
# ZIP anywhere, run it, and all downloads/extracts/backups stay in that
# folder. Nothing is written to %LOCALAPPDATA% or the registry.


def _resolve_project_root() -> str:
    """Find the directory the installer was launched from.

    - When running from source: the folder containing installer.py
      (i.e. the parent of the src/ package).
    - When running as a PyInstaller-bundled .exe: the folder containing
      the .exe (sys.executable's directory, NOT _MEIPASS which is a
      temp extraction folder).
    - Fallback: the current working directory.
    """
    # PyInstaller one-file: sys.frozen is set, sys.executable is the .exe path
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))

    # Running from source: this file is src/config.py, project root is its parent
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)  # parent of src/


PROJECT_ROOT = _resolve_project_root()
CACHE_ROOT = os.path.join(PROJECT_ROOT, "cache")
CACHE_DOWNLOADS = os.path.join(CACHE_ROOT, "downloads")    # downloaded archives
CACHE_EXTRACTED = os.path.join(CACHE_ROOT, "extracted")    # extracted mod files
CACHE_BACKUPS = os.path.join(CACHE_ROOT, "backups")        # backup .zip files
CACHE_LOGS = os.path.join(CACHE_ROOT, "logs")              # install logs


# ----------------------------------------------------------------------
# San Andreas version detection
# ----------------------------------------------------------------------
# Known file sizes (bytes) of well-known SA exe builds.
# Source: https://gtaforums.com/topic/931236-san-andreas-exe-versions/
SA_EXE_SIZES = {
    "v1.0_us_hoodlum":   6170624,   # Original US v1.0 (HOODLUM) — BEST FOR MODS
    "v1.0_eu_hoodlum":   6180864,   # Original EU v1.0 (HOODLUM)
    "v1.01_us":          6236160,   # v1.01 US patch (most mods work)
    "v1.01_eu":          6236160,   # v1.01 EU patch
    "v2.0_us":           6823936,   # v2.0 US (SecuROM — breaks many mods)
    "v2.0_eu":           6823936,   # v2.0 EU (SecuROM — breaks many mods)
    "v3.0_steam":        9867264,   # Steam Compact exe (breaks most mods)
    "v3.0_steam_alt":    9502720,   # Steam alternate build
    "v3.0_steam_2025":   5971456,   # Steam 2025 depot (gta-sa.exe, no PE version info)
}

# Sizes considered "v1.0 / mod-compatible"
SA_V10_SIZES = {
    SA_EXE_SIZES["v1.0_us_hoodlum"],
    SA_EXE_SIZES["v1.0_eu_hoodlum"],
    SA_EXE_SIZES["v1.01_us"],
    SA_EXE_SIZES["v1.01_eu"],
}

# Sizes considered "Steam v3.0"
SA_STEAM_SIZES = {
    SA_EXE_SIZES["v3.0_steam"],
    SA_EXE_SIZES["v3.0_steam_alt"],
    SA_EXE_SIZES["v3.0_steam_2025"],
}


# ----------------------------------------------------------------------
# Mod sources
# ----------------------------------------------------------------------
@dataclass
class ModSource:
    """Describes one downloadable mod the wizard can install."""
    id: str
    name: str
    description: str
    url: str                       # direct download URL (or page URL to resolve)
    page_url: str = ""             # human-readable 'more info' page
    install_order: int = 50        # lower runs first
    extract_to_sa_root: bool = True
    # If set, only this single file/folder inside the archive is moved.
    # If empty, the entire archive is merged into the SA root.
    pick_paths: List[str] = field(default_factory=list)
    # MediaFire links need a two-step resolver (page → direct download URL).
    is_mediafire: bool = False
    # GitHub releases page — resolve via api.github.com/repos/<owner>/<repo>/releases/latest.
    is_github_release: bool = False
    # MixMods-style article page — scrape the article for a .zip download link.
    is_article_page: bool = False
    # LibertyCity file page — scrape the page for the .zip download link.
    is_libertycity: bool = False
    # Mark the main mod so the wizard can label it specially.
    is_main_mod: bool = False
    # If True, this mod is optional and the user can untick it.
    optional: bool = False
    # Default installed state (only used when optional=True).
    enabled_by_default: bool = True
    # If True, the wizard cannot auto-download this mod (Cloudflare-blocked,
    # requires login, etc.). The UI will show a prominent "MANUAL DOWNLOAD
    # REQUIRED" banner with a clickable link, and the user must drop the
    # downloaded archive into their archives folder.
    manual_download_required: bool = False
    # Direct download URL shown to the user for manual download (may differ
    # from `url` which is what the wizard tries to scrape). If empty, `url`
    # is used.
    manual_download_url: str = ""
    # Alternative download mirrors — list of (label, url) tuples shown in
    # the download window so the user has backup options.
    mirror_urls: List[tuple] = field(default_factory=list)
    # Filename substrings that identify THIS mod's archive (case-insensitive).
    # The download window only matches files containing one of these strings.
    # If empty, matches any archive file (legacy behavior).
    file_matchers: List[str] = field(default_factory=list)


# The main mod — pulled from the official MediaFire link supplied by the user.
MAIN_MOD = ModSource(
    id="gta_sas_1987",
    name="GTA San Andreas Stories 1987 (June 2026 build)",
    description=(
        "The main total-conversion mod. Storyline is built on DYOM 8.1, "
        "which is already included and fully configured inside the archive."
    ),
    url=MAIN_MOD_MEDIAFIRE_URL,
    page_url=MOD_SITE_URL,
    install_order=100,
    extract_to_sa_root=True,
    is_mediafire=True,
    is_main_mod=True,
    file_matchers=["gta_sas", "GTA_SAS", "gta_sas_1987", "GTA_SAS_1987", "stories", "june_2026", "july_2026"],
)

# Prerequisite / supporting mods. These mirror the "Additional Downloads"
# list on gtasas.netlify.app.
#
# IMPORTANT: Per the official site's note:
#   "GTA San Andreas Stories already includes all required dependencies.
#    The storyline is built on DYOM 8.1, which is already included and
#    fully configured inside the archive."
#
# So all of these are OPTIONAL and OFF by default. They're listed here so
# users who want to update them independently can do so.
#
# Some mods (CLEO+, NewOpcodes, DYOM) are hosted on MixMods which sits
# behind Cloudflare bot protection — the wizard CANNOT auto-download
# them. Those are marked manual_download_required=True, and the UI will
# show a prominent banner with a clickable link telling the user to
# download manually and drop the archive into their archives folder.
PREREQUISITE_MODS: List[ModSource] = [
    ModSource(
        id="cleo5",
        name="CLEO 5",
        description=(
            "Required for running CLEO scripts. Already included in the main mod — "
            "only install this if you want to update CLEO separately. "
            "The wizard can auto-download this from GitHub."
        ),
        url="https://github.com/cleolibrary/CLEO5/releases",
        page_url="https://cleo.li/",
        manual_download_url="https://github.com/cleolibrary/CLEO5/releases/latest",
        install_order=10,
        extract_to_sa_root=True,
        is_github_release=True,
        optional=True,
        enabled_by_default=True,
        manual_download_required=False,
        mirror_urls=[
            ("GitHub (Latest)", "https://github.com/cleolibrary/CLEO5/releases/latest"),
            ("GitHub (All Releases)", "https://github.com/cleolibrary/CLEO5/releases"),
            ("CLEO Official Site", "https://cleo.li/"),
        ],
        file_matchers=["cleo_5", "cleo5", "CLEO_5", "CLEO5", "SA.CLEO", "sa.cleo"],
    ),
    ModSource(
        id="cleo_plus",
        name="CLEO+",
        description=(
            "Enhances CLEO with more opcodes and features. Already included in the "
            "main mod. Hosted on MixMods (Cloudflare-protected) — the wizard CANNOT "
            "auto-download this. Click the link below, download the .zip manually, "
            "and drop it in your archives folder."
        ),
        url="https://github.com/JuniorDjjr/CLEOPlus/releases",
        page_url="https://www.mixmods.com.br/2023/10/cleoplus/",
        manual_download_url="https://github.com/JuniorDjjr/CLEOPlus/releases/latest",
        install_order=20,
        extract_to_sa_root=True,
        is_github_release=True,
        optional=True,
        enabled_by_default=True,
        manual_download_required=True,
        mirror_urls=[
            ("GitHub (Releases)", "https://github.com/JuniorDjjr/CLEOPlus/releases"),
            ("MixMods (Official)", "https://www.mixmods.com.br/2023/10/cleoplus/"),
            ("GTAForums Thread", "https://gtaforums.com/topic/1101792-cleo/"),
        ],
        file_matchers=["cleoplus", "cleo_plus", "CLEOPlus", "CLEO_Plus", "CLEO+", "cleo+"],
    ),
    ModSource(
        id="newopcodes",
        name="NewOpcodes",
        description=(
            "Adds additional opcodes for CLEO compatibility and gameplay enhancements. "
            "Already included in the main mod. Hosted on MixMods (Cloudflare-protected) — "
            "the wizard CANNOT auto-download this. Click the link below, download the .zip "
            "manually, and drop it in your archives folder."
        ),
        url="https://www.mixmods.com.br/2020/10/newopcodes-cleo-v2-1/",
        page_url="https://www.mixmods.com.br/2020/10/newopcodes-cleo-v2-1/",
        manual_download_url="https://www.mixmods.com.br/2020/10/newopcodes-cleo-v2-1/",
        install_order=30,
        extract_to_sa_root=True,
        is_article_page=True,
        optional=False,
        enabled_by_default=True,
        manual_download_required=True,
        mirror_urls=[
            ("MixMods (Official)", "https://www.mixmods.com.br/2020/10/newopcodes-cleo-v2-1/"),
            ("GTAForums Thread", "https://gtaforums.com/topic/518780-cleo4newopcodes-by-dk22pac/"),
            ("DK22Pac GitHub", "https://github.com/DK22Pac"),
        ],
        file_matchers=["newopcodes", "new_opcodes", "NewOpcodes", "NewOpcodes_CLEO"],
    ),
    ModSource(
        id="dyom",
        name="DYOM 8.1 (Design Your Own Mission)",
        description=(
            "The storyline of GTA SAS 1987 is built on DYOM 8.1. Already included "
            "and fully configured inside the main mod archive — you do NOT need to "
            "install this separately unless you want to use DYOM standalone. "
            "Recommended stable version."
        ),
        url="https://www.gtagarage.com/mods/download.php?f=35188",
        page_url="https://www.gtagarage.com/mods/download.php?f=35188",
        manual_download_url="https://www.gtagarage.com/mods/download.php?f=35188",
        install_order=40,
        extract_to_sa_root=True,
        optional=True,
        enabled_by_default=True,
        manual_download_required=True,
        mirror_urls=[
            ("GTAGarage (Official)", "https://www.gtagarage.com/mods/show.php?id=5038"),
            ("DYOM Official Site", "https://dyom.gtagames.nl/"),
            ("GTAForums Thread", "https://gtaforums.com/topic/836909-dyom-design-your-own-mission-v83-alpha/"),
        ],
        file_matchers=["dyom_8.1", "DYOM_8.1", "dyom81", "DYOM81", "design_your_own"],
    ),
    ModSource(
        id="dyom_v83",
        name="DYOM 8.3 Alpha (Latest)",
        description=(
            "<b style='color:#ff5b5b;'>ALPHA — may have bugs.</b> "
            "DYOM 8.3 Alpha with performance fixes and new animations. "
            "Use DYOM 8.1 stable instead unless you know what you're doing."
        ),
        url="https://www.mediafire.com/file/srnb9q5txnev2sf/DYOM_8.3_Alpha_10.zip/file",
        page_url="https://www.mediafire.com/file/srnb9q5txnev2sf/DYOM_8.3_Alpha_10.zip/file",
        manual_download_url="https://www.mediafire.com/file/srnb9q5txnev2sf/DYOM_8.3_Alpha_10.zip/file",
        install_order=42,
        extract_to_sa_root=True,
        optional=True,
        enabled_by_default=False,
        manual_download_required=True,
        is_mediafire=True,
        mirror_urls=[
            ("MediaFire (Direct)", "https://www.mediafire.com/file/srnb9q5txnev2sf/DYOM_8.3_Alpha_10.zip/file"),
            ("DYOM Official Site", "https://dyom.gtagames.nl/"),
            ("GTAForums Thread", "https://gtaforums.com/topic/836909-dyom-design-your-own-mission-v83-alpha/"),
        ],
        file_matchers=["dyom_8.3", "DYOM_8.3", "dyom_83", "DYOM_83", "DYOM_Alpha"],
    ),
]

# Full ordered list (prereqs first by install_order, main mod last).
ALL_MODS: List[ModSource] = sorted(
    PREREQUISITE_MODS + [MAIN_MOD],
    key=lambda m: m.install_order,
)


# ----------------------------------------------------------------------
# Backup configuration
# ----------------------------------------------------------------------
# Files and folders inside the source SA root that get backed up before any
# mod is applied. The wizard will skip any that don't exist (no error).
BACKUP_PATHS = [
    "gta_sa.exe",
    "gta-sa.exe",
    "data",
    "models",
    "scripts",
    "cleo",
    "modloader",
    "text",
    "audio",
    "SAMP",
]


# ----------------------------------------------------------------------
# Network
# ----------------------------------------------------------------------
HTTP_TIMEOUT = 30              # seconds
HTTP_USER_AGENT = f"{APP_SHORT}/{APP_VERSION} (+{MOD_SITE_URL})"
CHUNK_SIZE = 1024 * 64         # 64 KiB chunks during download


def ensure_cache_dirs() -> None:
    """Create all cache directories if missing. Safe to call multiple times."""
    for p in (CACHE_DOWNLOADS, CACHE_EXTRACTED, CACHE_BACKUPS, CACHE_LOGS):
        os.makedirs(p, exist_ok=True)

"""Screenshot cache — downloads mod screenshots from GitHub on first run.

All images are downloaded into cache/screenshots/ next to the project,
downscaled to max 800px width, and compressed to JPEG quality 75
to keep the cache small (~25-30KB per image instead of 500KB-2MB).

On subsequent runs, the cache is reused. If the cache already has enough
images, no network requests are made.
"""
from __future__ import annotations

import logging
import os
import random
from typing import List, Optional

log = logging.getLogger(__name__)

# All screenshot URLs from the mod's GitHub repos.
# Each entry is (url, filename).
_SCREENSHOT_URLS: list[tuple[str, str]] = [
    # gtasasmanual repo
    ("https://raw.githubusercontent.com/babamohammed2022/gtasasmanual/main/Immagine%202025-04-23%20220835.png", "manual_immagine.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gtasasmanual/main/SETTINGUP.png", "manual_settingup.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gtasasmanual/main/cover.png", "manual_cover.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gtasasmanual/main/customization.png", "manual_customization.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gtasasmanual/main/placestoeat.png", "manual_placestoeat.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gtasasmanual/main/weap1.png", "manual_weap1.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gtasasmanual/main/weap2..png", "manual_weap2.png"),
    # gtasashtml repo
    ("https://raw.githubusercontent.com/babamohammed2022/gtasashtml/main/Media_Player_7_13_2025_6_41_45_PM.webp", "html_screenshot5.webp"),
    ("https://raw.githubusercontent.com/babamohammed2022/gtasashtml/main/Media_Player_7_13_2025_6_43_44_PM.webp", "html_screenshot6.webp"),
    ("https://raw.githubusercontent.com/babamohammed2022/gtasashtml/main/image.webp", "html_image.webp"),
    ("https://raw.githubusercontent.com/babamohammed2022/gtasashtml/main/loadsc12.png", "html_loadsc12.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gtasashtml/main/loadsc4.png", "html_loadsc4.png"),
    # gta-1987-remastered-mod repo — src/assets/
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/Media_Player_12_10_2024_10_11_09.png", "remastered_dec2024.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/Media_Player_7_27_2025_9_49_21_A.png", "remastered_jul2025_a.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/Media_Player_7_27_2025_9_49_30_A.png", "remastered_jul2025_b.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/Media_Player_8_11_2025_1_04_40_P.png", "remastered_aug2025.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/Media_Player_8_25_2025_1_18_00_PM.webp", "remastered_aug25_a.webp"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/Media_Player_8_25_2025_1_20_37_PM.webp", "remastered_aug25_b.webp"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/NO_cleanup%20(1).png", "remastered_nocleanup.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/WIP.png", "remastered_wip.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/captura_by_FrankoU_28.png", "remastered_frankou.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/ig.png", "remastered_ig.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/igna.png", "remastered_igna.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/image%20(15).png", "remastered_img15.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/image%20(4).png", "remastered_img4.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/image%20(5).png", "remastered_img5.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/image%20(7).png", "remastered_img7.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/image%20(8).png", "remastered_img8.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/oold.png", "remastered_oold.png"),
    ("https://raw.githubusercontent.com/babamohammed2022/gta-1987-remastered-mod/main/src/assets/san.png", "remastered_san.png"),
]

# Minimum number of cached images before we consider the cache "ready"
_MIN_CACHE_COUNT = 10


def _screenshots_dir() -> str:
    """Return the path to the screenshots cache directory."""
    from . import config
    return os.path.join(config.CACHE_ROOT, "screenshots")


def _is_cache_ready() -> bool:
    """True if we have enough cached screenshots."""
    d = _screenshots_dir()
    if not os.path.isdir(d):
        return False
    count = len([f for f in os.listdir(d) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
    return count >= _MIN_CACHE_COUNT


def _download_and_compress(url: str, dest_path: str) -> bool:
    """Download an image, downscale to 800px width, compress to JPEG q75."""
    try:
        import requests
        from io import BytesIO

        resp = requests.get(url, timeout=15, stream=True)
        resp.raise_for_status()

        # Read into memory first
        data = resp.content
        if len(data) < 1024:
            return False

        # Try to process with PIL if available, otherwise save raw
        try:
            from PIL import Image
            img = Image.open(BytesIO(data))
            # Convert to RGB if needed (RGBA -> RGB for JPEG)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            # Downscale to max 800px width
            max_w = 800
            if img.width > max_w:
                ratio = max_w / img.width
                new_h = int(img.height * ratio)
                img = img.resize((max_w, new_h), Image.LANCZOS)
            # Save as compressed JPEG
            img.save(dest_path, 'JPEG', quality=75, optimize=True)
        except ImportError:
            # No PIL — save the raw file as-is
            with open(dest_path, 'wb') as f:
                f.write(data)

        return os.path.isfile(dest_path) and os.path.getsize(dest_path) > 1024
    except Exception as e:
        log.warning("Failed to download %s: %s", url, e)
        return False


def ensure_screenshots() -> None:
    """Download all screenshots if cache is not ready. Non-fatal — fails silently."""
    if _is_cache_ready():
        log.info("Screenshot cache is ready (%s)", _screenshots_dir())
        return

    d = _screenshots_dir()
    os.makedirs(d, exist_ok=True)

    log.info("Downloading mod screenshots to %s ...", d)
    downloaded = 0
    for url, filename in _SCREENSHOT_URLS:
        dest = os.path.join(d, filename)
        if os.path.isfile(dest) and os.path.getsize(dest) > 1024:
            downloaded += 1
            continue
        if _download_and_compress(url, dest):
            downloaded += 1
            log.debug("Downloaded: %s", filename)

    log.info("Screenshot cache: %d/%d images downloaded", downloaded, len(_SCREENSHOT_URLS))


def get_random_screenshots(count: int = 1) -> List[str]:
    """Return `count` random screenshot file paths from the cache.

    Returns empty list if cache is not populated.
    """
    d = _screenshots_dir()
    if not os.path.isdir(d):
        return []

    files = [
        os.path.join(d, f)
        for f in os.listdir(d)
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
        and os.path.getsize(os.path.join(d, f)) > 1024
    ]
    if not files:
        return []

    if count >= len(files):
        return files[:]
    return random.sample(files, count)


def get_random_screenshot() -> Optional[str]:
    """Return a single random screenshot path, or None if cache is empty."""
    shots = get_random_screenshots(1)
    return shots[0] if shots else None

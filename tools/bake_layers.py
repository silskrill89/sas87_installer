"""Bake separated FG/BG layers from splash images using rembg + OpenCV inpainting.

Run once at build time:
    py bake_layers.py

Outputs to src/ui/splash_layers/:
    <name>_fg.png   — Character/foreground with alpha transparency
    <name>_bg.png   — Background with character removed, AI-inpainted
"""
from __future__ import annotations

import os
import sys
import numpy as np
from pathlib import Path
from PIL import Image, ImageFilter
from rembg import remove, new_session
import cv2

SPLASH_DIR = Path(__file__).parent / "src" / "ui" / "splash"
OUTPUT_DIR = Path(__file__).parent / "src" / "ui" / "splash_layers"
OUTPUT_DIR.mkdir(exist_ok=True)

print("Loading rembg model...")
session = new_session("u2net")


def inpaint_background(original: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """AI-assisted inpainting: fill removed FG area with plausible background."""
    h, w = mask.shape[:2]

    # 1. Dilate the mask heavily so inpainting has room to work
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35))
    dilated = cv2.dilate(mask, kernel, iterations=3)

    # 2. Feather the edges for smooth blending
    feathered = cv2.GaussianBlur(dilated.astype(np.float32) / 255.0, (51, 51), 0)
    inpaint_mask = (feathered * 255).astype(np.uint8)

    # 3. Use OpenCV Navier-Stokes inpainting for the main fill
    #    (fast, decent quality for small-medium holes)
    bg_ns = cv2.inpaint(original, inpaint_mask, inpaintRadius=15, flags=cv2.INPAINT_NS)

    # 4. Use Telea inpainting for comparison — often better for texture
    bg_telea = cv2.inpaint(original, inpaint_mask, inpaintRadius=20, flags=cv2.INPAINT_TELEA)

    # 5. Blend both results 50/50 for best coverage
    blend_mask = feathered[:, :, np.newaxis]
    bg_blended = (bg_ns.astype(np.float64) * (1 - blend_mask) +
                  bg_telea.astype(np.float64) * blend_mask).astype(np.uint8)

    # 6. Final smooth pass — slight Gaussian to blend inpaint seams
    bg_smooth = cv2.GaussianBlur(bg_blended, (5, 5), 0)

    # 7. Re-composite original pixels where mask was clean (no FG removal)
    clean = (feathered < 0.1)
    bg_smooth[clean] = original[clean]

    return bg_smooth


def bake_image(src: Path, name: str):
    """Separate FG from BG, inpaint BG, save both layers."""
    fg_path = OUTPUT_DIR / f"{name}_fg.png"
    bg_path = OUTPUT_DIR / f"{name}_bg.png"

    if fg_path.exists() and bg_path.exists():
        print(f"  [skip] {name} already baked")
        return

    print(f"  [bake] {name}...")
    img = Image.open(src).convert("RGBA")

    # rembg with alpha matting for clean FG edges
    result = remove(
        img,
        session=session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=20,
        alpha_matting_erode_size=10,
    )

    # ── FG layer: original + rembg alpha ──
    fg = result.copy()
    fg.save(str(fg_path), "PNG", optimize=True)

    # ── BG layer: inpaint where character was removed ──
    orig_np = np.array(img)[:, :, :3][:, :, ::-1]  # RGBA -> BGR
    alpha = np.array(result)[:, :, 3]

    # Create binary mask: 1 = FG was here (needs inpainting)
    fg_mask = (alpha < 200).astype(np.uint8) * 255

    if fg_mask.sum() > 0:
        bg_bgr = inpaint_background(orig_np, fg_mask)
    else:
        bg_bgr = orig_np

    # Convert BGR -> RGB -> RGBA
    bg_rgb = bg_bgr[:, :, ::-1]
    bg_rgba = np.dstack([bg_rgb, np.full(bg_rgb.shape[:2], 255, dtype=np.uint8)])
    bg_img = Image.fromarray(bg_rgba, "RGBA")

    # Slight blur to smooth any remaining seams
    bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=1.5))

    bg_img.save(str(bg_path), "PNG", optimize=True)

    fg_kb = fg_path.stat().st_size / 1024
    bg_kb = bg_path.stat().st_size / 1024
    print(f"  -> {name}_fg.png ({fg_kb:.0f} KB), {name}_bg.png ({bg_kb:.0f} KB)")


def main():
    images = sorted(SPLASH_DIR.glob("*.png"))
    if not images:
        print(f"No images found in {SPLASH_DIR}")
        sys.exit(1)

    print(f"Baking {len(images)} splash images -> FG/BG layers with AI inpainting")
    print(f"Output: {OUTPUT_DIR}\n")

    for src in images:
        name = src.stem
        bake_image(src, name)

    fg_count = len(list(OUTPUT_DIR.glob("*_fg.png")))
    bg_count = len(list(OUTPUT_DIR.glob("*_bg.png")))
    print(f"\nDone! {fg_count} FG + {bg_count} BG layers baked.")
    print("Bundled with the installer for the parallax slideshow.")


if __name__ == "__main__":
    main()

"""GTA San Andreas Stories 1987 — Rockstar-style website themed wizard.

Visual identity:
    - Rockstar Games early-2000s website aesthetic (dark, gritty, bold)
    - VCS (Vice City Stories) neon color palette — purples, teals, sunset amber
    - Late 80s LA vibrant life — palm trees, neon signs, sunset glow
    - GTA IV modern polish — clean panels, subtle gradients, refined typography
    - Grove Street green as an accent (not dominant)

Paint layers (back to front):
    1. Dark Rockstar-style gradient (near-black → deep purple)
    2. LA sunset horizon band (amber/rose glow)
    3. City skyline silhouette (downtown LA + Vinewood sign)
    4. Neon sign accents (VCS-style glowing text/shapes)
    5. Palm tree silhouettes
    6. Mod screenshot (full-width, behind text, with amber tint)
    7. Dark semi-transparent content panel (text readability)
    8. CRT scanlines + subtle noise
    9. QWizardPage widgets paint on top
"""
from __future__ import annotations

import math
import os
import random
import time as _time

from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, QElapsedTimer
from PySide6.QtGui import (
    QColor, QFont, QFontDatabase, QLinearGradient, QPainter, QPen, QPixmap,
    QPolygonF, QRadialGradient, QImage,
)
from PySide6.QtWidgets import QApplication, QWizard

# ─────────────────────────────────────────────────────────────────────────────
# Palette — Rockstar Website × VCS × GTA SA Stories × Late 80s LA
# ─────────────────────────────────────────────────────────────────────────────

# Rockstar dark base
COLOR_ROCKSTAR_BLACK = "#0a0a0f"
COLOR_ROCKSTAR_DARK = "#111118"
COLOR_ROCKSTAR_PANEL = "#14141e"

# VCS neon palette
COLOR_VCS_PURPLE = "#7b2fbe"
COLOR_VCS_PURPLE_LIGHT = "#a855f7"
COLOR_VCS_TEAL = "#00d4aa"
COLOR_VCS_TEAL_DIM = "#0a7a62"
COLOR_VCS_TEAL_LIGHT = "#5ff5d5"
COLOR_VCS_NEON_PINK = "#ff2d7b"
COLOR_VCS_NEON_BLUE = "#3b82f6"

# Sunset / golden hour (LA 1987)
COLOR_SUNSET_AMBER = "#ff8c42"
COLOR_SUNSET_ROSE = "#c94a30"
COLOR_SUNSET_GOLD = "#f0c060"
COLOR_SUNSET_CORAL = "#ff6b6b"

# Grove Street green (accent only)
COLOR_GROVE_GREEN = "#3d8a3d"
COLOR_GROVE_GREEN_LIGHT = "#5fc45f"

# Text
COLOR_TEXT_BRIGHT = "#f0e6d6"
COLOR_TEXT_BODY = "#c0c0c0"
COLOR_TEXT_DIM = "#999999"
COLOR_TEXT_ACCENT = COLOR_SUNSET_GOLD

# Status
COLOR_DANGER = "#ff5b5b"
COLOR_SUCCESS = "#5bff8a"
COLOR_WARNING = "#ffe600"

# Gradient stops — Rockstar website dark-to-purple
COLOR_BG_TOP = "#0a0a0f"
COLOR_BG_MID = "#1a0e28"
COLOR_BG_HORIZON = "#2a1040"

# Content panel overlay
COLOR_CONTENT_PANEL = QColor(10, 10, 15, 210)

# Backward-compat aliases (used by download_window, cleanup_dialog, etc.)
COLOR_DARK_GREEN = COLOR_ROCKSTAR_DARK
COLOR_PANEL_BG = COLOR_ROCKSTAR_DARK
COLOR_PANEL_BG_LIGHT = COLOR_ROCKSTAR_PANEL


# ─────────────────────────────────────────────────────────────────────────────
# Font registration
# ─────────────────────────────────────────────────────────────────────────────
_PRICEDOWN_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "fonts", "PricedownBl.otf",
)
_PRICEDOWN_FAMILY: str | None = None


def _register_pricedown() -> str | None:
    global _PRICEDOWN_FAMILY
    if _PRICEDOWN_FAMILY is not None:
        return _PRICEDOWN_FAMILY
    path = _PRICEDOWN_PATH
    if not os.path.isfile(path):
        meipass = os.environ.get("_MEIPASS")
        if meipass:
            alt = os.path.join(meipass, "fonts", "PricedownBl.otf")
            if os.path.isfile(alt):
                path = alt
    if not os.path.isfile(path):
        return None
    font_id = QFontDatabase.addApplicationFont(path)
    if font_id < 0:
        return None
    families = QFontDatabase.applicationFontFamilies(font_id)
    if families:
        _PRICEDOWN_FAMILY = families[0]
        return _PRICEDOWN_FAMILY
    return None


DISPLAY_FONT = "Impact"
UI_FONT = "Segoe UI"
MONO_FONT = "Consolas"


def apply_theme(app: QApplication) -> None:
    global DISPLAY_FONT, _PRICEDOWN_FAMILY
    _register_pricedown()
    if _PRICEDOWN_FAMILY:
        DISPLAY_FONT = _PRICEDOWN_FAMILY
    app.setStyleSheet(_build_qss())
    from PySide6.QtGui import QPalette
    pal = app.palette()
    pal.setColor(QPalette.Window, QColor(0, 0, 0, 0))
    pal.setColor(QPalette.Base, QColor(0, 0, 0, 0))
    pal.setColor(QPalette.Button, QColor(0, 0, 0, 0))
    app.setPalette(pal)


def heading_font(size: int = 28, bold: bool = True) -> QFont:
    f = QFont(DISPLAY_FONT, size)
    f.setBold(bold)
    return f


def body_font(size: int = 12) -> QFont:
    return QFont(UI_FONT, size)


def mono_font(size: int = 12) -> QFont:
    return QFont(MONO_FONT, size)


# ─────────────────────────────────────────────────────────────────────────────
# Caches
# ─────────────────────────────────────────────────────────────────────────────
_SCREENSHOT_CACHE: dict[str, QPixmap] = {}
_SCANLINE_CACHE: dict[tuple[int, int], QPixmap] = {}


def _get_screenshot_pixmap(path: str) -> QPixmap:
    pix = _SCREENSHOT_CACHE.get(path)
    if pix is None or pix.isNull():
        pix = QPixmap(path)
        if not pix.isNull():
            _SCREENSHOT_CACHE[path] = pix
    return pix


def _get_scanlines(w: int, h: int) -> QPixmap:
    key = (w, h)
    tex = _SCANLINE_CACHE.get(key)
    if tex is None or tex.isNull():
        tex = QPixmap(w, h)
        tex.fill(QColor(0, 0, 0, 0))
        p = QPainter(tex)
        # CRT scanlines — subtle horizontal lines
        p.setPen(QPen(QColor(0, 0, 0, 20), 1))
        for y in range(0, h, 3):
            p.drawLine(0, y, w, y)
        # Slight vignette at edges
        for y in range(0, min(h, 40)):
            alpha = int(30 * (1 - y / 40))
            p.setPen(QPen(QColor(0, 0, 0, alpha), 1))
            p.drawLine(0, y, w, y)
        for y in range(max(0, h - 40), h):
            alpha = int(30 * ((y - (h - 40)) / 40))
            p.setPen(QPen(QColor(0, 0, 0, alpha), 1))
            p.drawLine(0, y, w, y)
        p.end()
        _SCANLINE_CACHE[key] = tex
    return tex


# ─────────────────────────────────────────────────────────────────────────────
# RockstarBackground — main wizard background
# ─────────────────────────────────────────────────────────────────────────────

class SynthwaveBackground(QWizard):
    """QWizard with GTA IV-style parallax slideshow background."""

    splash_image_name: str | None = None

    _SLIDE_DURATION = 12.0
    _SLIDE_TRANSITION = 2.5
    _SLIDE_FPS = 30

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_screenshot_path: str | None = None

        # ── Slideshow state ──
        self._slide_pool: list[str] = []
        self._slide_idx = 0
        self._slide_next = 1
        self._slide_t = 0.0
        self._slide_alpha = 0.0
        self._slide_transitioning = False

        # ── Per-slide parallax params (randomized per image) ──
        self._slide_dir = (0.0, 0.0)
        self._slide_kb_zoom = (1.0, 1.0)
        self._slide_offset = [0.0, 0.0]
        self._randomize_slide_params()

        # ── Cached processed pixmaps: (bg, fg) per path ──
        self._pixmap_cache: dict[str, tuple[QPixmap, QPixmap]] = {}

        # ── Smooth elapsed-time timer ──
        self._elapsed = QElapsedTimer()
        self._elapsed.start()
        self._last_tick_ms = 0.0

        self._slide_timer = QTimer(self)
        self._slide_timer.timeout.connect(self._on_slide_tick)
        self._slide_timer.start(1000 // self._SLIDE_FPS)

    # ─────────────────────────────────────────────────────────────────────
    # Slideshow API
    # ─────────────────────────────────────────────────────────────────────

    def set_screenshot(self, path: str | None):
        """Legacy API — ignored. Slideshow runs independently."""
        pass

    def load_slideshow(self, paths: list[str]):
        """Set the pool of images for the slideshow."""
        self._slide_pool = [p for p in paths if os.path.isfile(p)]
        if len(self._slide_pool) < 2:
            if self._current_screenshot_path:
                self._slide_pool.insert(0, self._current_screenshot_path)
        if len(self._slide_pool) >= 2:
            self._slide_idx = 0
            self._slide_next = 1
            self._slide_t = 0.0
            self._slide_alpha = 0.0
            self._slide_transitioning = False
            self._randomize_slide_params()

    def _randomize_slide_params(self):
        """Randomize parallax direction + Ken Burns for current slide."""
        # Pick a primary angle for the FG layer
        angle = random.uniform(-0.5, 0.5)
        speed = random.uniform(40, 80)
        fg_dx = math.sin(angle) * speed
        fg_dy = -math.cos(angle) * speed
        # BG moves OPPOSITE direction at roughly 60% speed
        self._slide_dir_fg = (fg_dx, fg_dy)
        self._slide_dir_bg = (-fg_dx * 0.6, -fg_dy * 0.6)

        # FG zooms OUT (1.18 → 1.02), BG zooms IN (0.92 → 1.08)
        if random.random() < 0.5:
            self._slide_kb_zoom_fg = (1.18, 1.02)
            self._slide_kb_zoom_bg = (0.92, 1.08)
        else:
            self._slide_kb_zoom_fg = (1.02, 1.18)
            self._slide_kb_zoom_bg = (1.08, 0.92)

        self._slide_offset_fg = [0.0, 0.0]
        self._slide_offset_bg = [0.0, 0.0]

    # ─────────────────────────────────────────────────────────────────────
    # Timer tick
    # ─────────────────────────────────────────────────────────────────────

    def _on_slide_tick(self):
        if len(self._slide_pool) < 2:
            return

        now_ms = self._elapsed.elapsed()
        dt = (now_ms - self._last_tick_ms) / 1000.0
        self._last_tick_ms = now_ms
        if dt > 0.5:
            dt = 1.0 / self._SLIDE_FPS

        self._slide_t += dt

        # Smooth Ken Burns offset — ease-in-out
        progress = min(self._slide_t / self._SLIDE_DURATION, 1.0)
        ease = progress * progress * (3 - 2 * progress)  # smoothstep
        self._slide_offset_fg[0] = self._slide_dir_fg[0] * ease
        self._slide_offset_fg[1] = self._slide_dir_fg[1] * ease
        self._slide_offset_bg[0] = self._slide_dir_bg[0] * ease
        self._slide_offset_bg[1] = self._slide_dir_bg[1] * ease

        # Start crossfade near end of slide
        fade_start = self._SLIDE_DURATION - self._SLIDE_TRANSITION
        if self._slide_t >= fade_start and not self._slide_transitioning:
            self._slide_transitioning = True
            self._slide_alpha = 0.0

        if self._slide_transitioning:
            self._slide_alpha += dt / self._SLIDE_TRANSITION
            if self._slide_alpha >= 1.0:
                self._slide_alpha = 0.0
                self._slide_idx = self._slide_next
                self._slide_next = (self._slide_next + 1) % len(self._slide_pool)
                self._slide_t = 0.0
                self._slide_transitioning = False
                self._randomize_slide_params()

        self.update()

    # ─────────────────────────────────────────────────────────────────────
    # Pixmap preparation (lazy, cached)
    # ─────────────────────────────────────────────────────────────────────

    def _get_slide_pixmaps(self, path: str, w: int, h: int) -> tuple[QPixmap, QPixmap]:
        """Return (bg_pixmap, fg_pixmap) for a slide — uses pre-baked AI layers."""
        key = f"{path}|{w}|{h}"
        if key in self._pixmap_cache:
            return self._pixmap_cache[key]

        # ── Check for pre-baked FG/BG layers ──
        base = os.path.splitext(os.path.basename(path))[0]
        layers_dir = os.path.join(os.path.dirname(path), "..", "splash_layers")
        fg_baked = os.path.join(layers_dir, f"{base}_fg.png")
        bg_baked = os.path.join(layers_dir, f"{base}_bg.png")

        if os.path.isfile(fg_baked) and os.path.isfile(bg_baked):
            fg = self._load_and_scale(QPixmap(fg_baked), w, h, scale=1.25)
            bg = self._load_and_scale(QPixmap(bg_baked), w, h, scale=1.20)
        else:
            # ── Fallback: no baked layers, use single image for both ──
            orig = QPixmap(path)
            if orig.isNull():
                null = QPixmap(w, h)
                null.fill(Qt.black)
                return null, null
            fg = self._load_and_scale(orig, w, h, scale=1.25)
            bg = self._load_and_scale(orig, w, h, scale=1.20)
            # Darken BG fallback
            dark = QImage(bg.size(), QImage.Format_ARGB32)
            dark.fill(Qt.transparent)
            dp = QPainter(dark)
            dp.drawPixmap(0, 0, bg)
            dp.setCompositionMode(QPainter.CompositionMode_SourceIn)
            dp.fillRect(dark.rect(), QColor(0, 0, 0, 140))
            dp.end()
            bg = QPixmap.fromImage(dark)

        self._pixmap_cache[key] = (bg, fg)
        return bg, fg

    def _load_and_scale(self, pix: QPixmap, w: int, h: int, scale: float = 1.0) -> QPixmap:
        """Load pixmap and scale to fill window with aspect-crop."""
        if pix.isNull():
            pix = QPixmap(w, h)
            pix.fill(Qt.black)
            return pix
        pw = int(pix.width() * scale)
        ph = int(pix.height() * scale)
        return pix.scaled(max(pw, 1), max(ph, 1), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    # ─────────────────────────────────────────────────────────────────────
    # Paint event — renders the full background
    # ─────────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        rect = self.rect()
        w, h = rect.width(), rect.height()

        # ---- 1. Rockstar dark gradient base ----
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.00, QColor("#0a0a0f"))
        grad.setColorAt(0.15, QColor("#0e0a18"))
        grad.setColorAt(0.35, QColor("#1a0e28"))
        grad.setColorAt(0.55, QColor("#2a1040"))
        grad.setColorAt(0.65, QColor("#4a1a30"))
        grad.setColorAt(0.72, QColor(COLOR_SUNSET_AMBER))
        grad.setColorAt(0.76, QColor(COLOR_SUNSET_ROSE))
        grad.setColorAt(0.80, QColor("#1a0808"))
        grad.setColorAt(1.00, QColor("#050508"))
        painter.fillRect(rect, grad)

        # ---- 2–5: Static background elements ----
        self._paint_horizon_glow(painter, w, h)
        self._paint_la_skyline(painter, w, h)
        self._paint_neon_accents(painter, w, h)
        self._paint_palms(painter, w, h)

        # ---- 6. Parallax slideshow ----
        self._paint_parallax_slideshow(painter, w, h)

        # ---- 7. Dark content panel with rounded Vista Aero corners ----
        panel_margin_left = int(w * 0.04)
        panel_margin_top = int(h * 0.05)
        panel_margin_right = int(w * 0.04)
        panel_margin_bottom = int(h * 0.10)
        panel_rect = QRectF(
            panel_margin_left, panel_margin_top,
            w - panel_margin_left - panel_margin_right,
            h - panel_margin_top - panel_margin_bottom,
        )
        panel_radius = 12.0

        # Fill panel with rounded rect
        from PySide6.QtGui import QPainterPath
        panel_path = QPainterPath()
        panel_path.addRoundedRect(panel_rect, panel_radius, panel_radius)

        panel_grad = QLinearGradient(panel_rect.topLeft(), panel_rect.bottomLeft())
        panel_grad.setColorAt(0.0, QColor(10, 10, 15, 190))
        panel_grad.setColorAt(0.5, QColor(10, 10, 15, 210))
        panel_grad.setColorAt(1.0, QColor(10, 10, 15, 190))
        painter.setClipPath(panel_path)
        painter.fillPath(panel_path, panel_grad)

        # Rounded border — Vista Aero gold glow
        painter.setClipping(False)
        border_pen = QPen(QColor(COLOR_SUNSET_GOLD), 1.5)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(panel_rect, panel_radius, panel_radius)

        # ---- 8. CRT scanlines ----
        scanlines = _get_scanlines(w, h)
        painter.drawPixmap(0, 0, scanlines)

        painter.end()

    # ─────────────────────────────────────────────────────────────────────
    # Parallax slideshow renderer
    # ─────────────────────────────────────────────────────────────────────

    def _paint_parallax_slideshow(self, painter: QPainter, w: int, h: int):
        """Paint two-layer parallax images with crossfade."""
        if len(self._slide_pool) < 1:
            return

        def _draw_slide(path: str, alpha: float, t: float, is_next: bool):
            bg_pix, fg_pix = self._get_slide_pixmaps(path, w, h)
            if bg_pix.isNull():
                return

            progress = min(t / self._SLIDE_DURATION, 1.0)

            # Separate zoom curves for FG and BG
            zoom_fg = self._slide_kb_zoom_fg[0] + (self._slide_kb_zoom_fg[1] - self._slide_kb_zoom_fg[0]) * progress
            zoom_bg = self._slide_kb_zoom_bg[0] + (self._slide_kb_zoom_bg[1] - self._slide_kb_zoom_bg[0]) * progress

            # Separate offsets — already opposite direction
            ox_fg = self._slide_offset_fg[0]
            oy_fg = self._slide_offset_fg[1]
            ox_bg = self._slide_offset_bg[0]
            oy_bg = self._slide_offset_bg[1]
            if is_next:
                ox_fg, oy_fg = -ox_fg * 0.5, -oy_fg * 0.5
                ox_bg, oy_bg = -ox_bg * 0.5, -oy_bg * 0.5

            painter.save()
            painter.setOpacity(alpha)

            # ── BG layer: darkened, moves slowly in its own direction ──
            bg_w = int(bg_pix.width() * zoom_bg)
            bg_h = int(bg_pix.height() * zoom_bg)
            bg_scaled = bg_pix.scaled(bg_w, bg_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # Centered + offset
            bg_ox = (w - bg_scaled.width()) // 2 + int(ox_bg)
            bg_oy = (h - bg_scaled.height()) // 2 + int(oy_bg)
            painter.setOpacity(alpha * 0.35)
            painter.drawPixmap(bg_ox, bg_oy, bg_scaled)

            # ── FG layer: sharp, zooms OUT, moves opposite to BG ──
            fg_w = int(fg_pix.width() * zoom_fg)
            fg_h = int(fg_pix.height() * zoom_fg)
            fg_scaled = fg_pix.scaled(fg_w, fg_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # Centered + offset (opposite direction to BG)
            fg_ox = (w - fg_scaled.width()) // 2 + int(ox_fg)
            fg_oy = (h - fg_scaled.height()) // 2 + int(oy_fg)
            painter.setOpacity(alpha * 0.50)
            painter.drawPixmap(fg_ox, fg_oy, fg_scaled)

            painter.restore()

        # Draw current slide
        current_path = self._slide_pool[self._slide_idx]
        current_alpha = 1.0 - self._slide_alpha
        if current_alpha > 0.01:
            _draw_slide(current_path, current_alpha, self._slide_t, is_next=False)

        # Draw next slide (during crossfade)
        if self._slide_transitioning and self._slide_alpha > 0.01:
            next_path = self._slide_pool[self._slide_next]
            _draw_slide(next_path, self._slide_alpha, self._slide_t + self._SLIDE_DURATION, is_next=True)

    # ─────────────────────────────────────────────────────────────────────
    # Painting helpers
    # ─────────────────────────────────────────────────────────────────────

    def _paint_horizon_glow(self, painter: QPainter, w: int, h: int) -> None:
        """Draw a radial glow at the horizon — sunset behind the city."""
        horizon_y = int(h * 0.72)
        center_x = int(w * 0.5)
        glow = QRadialGradient(center_x, horizon_y, int(w * 0.35))
        glow.setColorAt(0.0, QColor(COLOR_SUNSET_AMBER))
        glow.setColorAt(0.3, QColor(COLOR_SUNSET_ROSE))
        glow.setColorAt(0.6, QColor("#4a1a30"))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        glow_rect = QRectF(center_x - int(w * 0.35), horizon_y - int(h * 0.2),
                           int(w * 0.7), int(h * 0.4))
        painter.fillRect(glow_rect, glow)

    def _paint_la_skyline(self, painter: QPainter, w: int, h: int) -> None:
        """Draw a Los Angeles city skyline silhouette along the horizon."""
        horizon_y = int(h * 0.72)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(5, 5, 8, 200))

        # Building definitions: (x_fraction, width_fraction, height_fraction)
        buildings = [
            # Downtown LA cluster (center-left)
            (0.12, 0.020, 0.14),
            (0.15, 0.030, 0.20),
            (0.19, 0.025, 0.18),
            (0.22, 0.035, 0.28),   # tallest — US Bank stand-in
            (0.26, 0.025, 0.22),
            (0.29, 0.040, 0.16),
            (0.33, 0.020, 0.12),
            # Mid-city
            (0.42, 0.030, 0.10),
            (0.46, 0.025, 0.14),
            (0.50, 0.020, 0.08),
            # Vinewood Hills area (right)
            (0.62, 0.030, 0.12),
            (0.66, 0.025, 0.16),
            (0.69, 0.020, 0.10),
            (0.72, 0.035, 0.14),
            # Far right
            (0.84, 0.025, 0.10),
            (0.87, 0.020, 0.12),
            (0.90, 0.030, 0.08),
        ]
        for xf, wf, hf in buildings:
            bx = int(w * xf)
            bw = int(w * wf)
            bh = int(h * hf)
            by = horizon_y - bh
            painter.drawRect(bx, by, bw, bh + 5)

        # Antenna spikes on tallest buildings
        painter.setPen(QPen(QColor(10, 10, 15, 180), 1))
        for xf, wf, hf in [(0.22, 0.035, 0.28), (0.15, 0.030, 0.20), (0.66, 0.025, 0.16)]:
            bx = int(w * xf) + int(w * wf) // 2
            by = horizon_y - int(h * hf)
            painter.drawLine(bx, by, bx, by - 14)

    def _paint_neon_accents(self, painter: QPainter, w: int, h: int) -> None:
        """Draw VCS-style neon sign accents — glowing shapes on the skyline."""
        horizon_y = int(h * 0.72)

        # Neon "Vice City Stories" inspired bar signs
        neon_signs = [
            # (x_frac, y_offset, width, color, text)
            (0.36, -35, 60, COLOR_VCS_NEON_PINK, "BAR"),
            (0.55, -25, 50, COLOR_VCS_TEAL, "CLUB"),
            (0.78, -30, 55, COLOR_VCS_PURPLE_LIGHT, "DINER"),
        ]

        for xf, y_off, sign_w, color, text in neon_signs:
            sx = int(w * xf)
            sy = horizon_y + y_off

            # Glow behind sign
            glow = QRadialGradient(sx + sign_w // 2, sy + 8, sign_w * 0.6)
            glow_color = QColor(color)
            glow_color.setAlpha(60)
            glow.setColorAt(0.0, glow_color)
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            glow_rect = QRectF(sx - sign_w // 2, sy - sign_w // 3, sign_w * 2, sign_w)
            painter.fillRect(glow_rect, glow)

            # Sign bar
            painter.setPen(QPen(QColor(color), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(sx, sy, sign_w, 16)

            # Neon text
            painter.setPen(QPen(QColor(color), 1))
            font = QFont(DISPLAY_FONT, 9)
            painter.setFont(font)
            painter.drawText(QRectF(sx, sy + 1, sign_w, 14), Qt.AlignCenter, text)

    def _paint_palms(self, painter: QPainter, w: int, h: int) -> None:
        """Draw LA-style palm tree silhouettes — late 80s sunset vibes."""
        horizon_y = int(h * 0.72)

        palms = [
            (0.05, 150),
            (0.10, 120),
            (0.35, 140),
            (0.50, 110),
            (0.75, 145),
            (0.92, 130),
        ]
        for xf, height in palms:
            bx = int(w * xf)
            by = horizon_y + 18
            self._draw_palm(painter, bx, by, height)

    def _draw_palm(self, painter: QPainter, base_x: int, base_y: int, height: int) -> None:
        """Draw a single LA-style palm tree silhouette."""
        trunk_top_x = base_x + (height // 10)
        trunk_top_y = base_y - height

        painter.save()
        # Trunk
        painter.setBrush(QColor(5, 5, 8, 220))
        painter.setPen(QPen(QColor(5, 5, 8, 220), 4))
        painter.drawPolygon(QPolygonF([
            QPointF(base_x - 3, base_y),
            QPointF(base_x + 3, base_y),
            QPointF(trunk_top_x + 2, trunk_top_y + 5),
            QPointF(trunk_top_x - 2, trunk_top_y + 5),
        ]))

        # Fronds
        painter.setPen(QPen(QColor(5, 5, 8, 210), 3))
        frond_len = int(height * 0.55)
        for i in range(9):
            angle_deg = -90 + (i - 4) * 22
            angle = math.radians(angle_deg)
            end_x = trunk_top_x + math.cos(angle) * frond_len
            end_y = trunk_top_y + math.sin(angle) * frond_len * 0.6
            mid_x = (trunk_top_x + end_x) // 2 + math.sin(angle) * 10
            mid_y = (trunk_top_y + end_y) // 2 - 8
            painter.drawLine(QPointF(trunk_top_x, trunk_top_y), QPointF(mid_x, mid_y))
            painter.drawLine(QPointF(mid_x, mid_y), QPointF(end_x, end_y))

        painter.restore()



# ─────────────────────────────────────────────────────────────────────────────
# Stylesheet — Rockstar Website × GTA IV × VCS × Late 80s LA
# ─────────────────────────────────────────────────────────────────────────────
def _build_qss() -> str:
    return f"""
/* ═══════════════════════════════════════════════════════════════════════════
   GTA San Andreas Stories 1987 — Rockstar Website Theme
   ═══════════════════════════════════════════════════════════════════════════ */

QWizard, QWizardPage {{
    background: transparent;
    color: {COLOR_TEXT_BODY};
    font-family: "{UI_FONT}", "Arial", sans-serif;
    font-size: 12pt;
}}
QWizardPage {{
    padding: 16px 8px 8px 8px;
}}

/* ── Labels ─────────────────────────────────────────────────────────────── */
QLabel {{
    color: {COLOR_TEXT_BODY};
    background: transparent;
}}
QLabel[heading="true"] {{
    font-family: "{DISPLAY_FONT}", "Impact", "Arial Black", sans-serif;
    font-size: 22pt;
    color: {COLOR_SUNSET_GOLD};
    letter-spacing: 2px;
}}
QLabel[subheading="true"] {{
    font-family: "{DISPLAY_FONT}", "Impact", "Arial Black", sans-serif;
    font-size: 12pt;
    color: {COLOR_VCS_TEAL};
    letter-spacing: 1px;
}}
QLabel[dim="true"] {{
    color: {COLOR_TEXT_DIM};
    font-size: 12pt;
}}
QLabel[success="true"] {{ color: {COLOR_SUCCESS}; }}
QLabel[danger="true"]  {{ color: {COLOR_DANGER}; }}

/* ── Buttons — Rockstar dark + gold accent ─────────────────────────────── */
QPushButton {{
    background-color: {COLOR_ROCKSTAR_DARK};
    color: {COLOR_TEXT_BRIGHT};
    border: 2px solid {COLOR_SUNSET_GOLD};
    border-radius: 6px;
    padding: 8px 22px;
    font-family: "{DISPLAY_FONT}", "Impact", "Arial Black", sans-serif;
    font-size: 12pt;
    letter-spacing: 1px;
    min-width: 90px;
}}
QPushButton:hover {{
    color: #ffffff;
    border-color: {COLOR_VCS_TEAL};
    background-color: {COLOR_ROCKSTAR_PANEL};
}}
QPushButton:pressed {{
    color: {COLOR_SUNSET_GOLD};
    border-color: {COLOR_SUNSET_GOLD};
    background-color: {COLOR_ROCKSTAR_BLACK};
}}
QPushButton:disabled {{
    color: #4a4050;
    border-color: #2a2030;
    background-color: {COLOR_ROCKSTAR_BLACK};
}}
QPushButton[primary="true"] {{
    color: {COLOR_ROCKSTAR_BLACK};
    background-color: {COLOR_SUNSET_GOLD};
    border-color: {COLOR_SUNSET_GOLD};
}}
QPushButton[primary="true"]:hover {{
    background-color: {COLOR_VCS_TEAL};
    border-color: {COLOR_VCS_TEAL};
    color: {COLOR_ROCKSTAR_BLACK};
}}
QPushButton[accent="true"] {{
    color: {COLOR_ROCKSTAR_BLACK};
    background-color: {COLOR_VCS_TEAL};
    border-color: {COLOR_VCS_TEAL};
}}
QPushButton[accent="true"]:hover {{
    background-color: {COLOR_VCS_TEAL_LIGHT};
    border-color: {COLOR_VCS_TEAL_LIGHT};
}}

/* ── Input widgets — dark panels with gold/teal borders ─────────────────── */
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextEdit {{
    background-color: {COLOR_ROCKSTAR_DARK};
    color: {COLOR_TEXT_BODY};
    border: 1px solid {COLOR_SUNSET_GOLD};
    border-radius: 3px;
    padding: 6px 8px;
    selection-background-color: {COLOR_VCS_PURPLE};
    selection-color: #ffffff;
}}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QTextEdit:focus {{
    border: 1px solid {COLOR_VCS_TEAL};
    background-color: {COLOR_ROCKSTAR_PANEL};
}}
QLineEdit:disabled {{
    color: #4a4050;
    background-color: {COLOR_ROCKSTAR_BLACK};
}}
QComboBox::drop-down {{
    border: 0;
    width: 20px;
    background: {COLOR_ROCKSTAR_DARK};
}}
QComboBox QAbstractItemView {{
    background-color: {COLOR_ROCKSTAR_DARK};
    color: {COLOR_TEXT_BODY};
    selection-background-color: {COLOR_VCS_PURPLE};
    selection-color: #ffffff;
    border: 1px solid {COLOR_SUNSET_GOLD};
    outline: 0;
}}

/* ── Radio + check — VCS neon style ────────────────────────────────────── */
QRadioButton {{
    color: {COLOR_TEXT_BODY};
    spacing: 8px;
    background: transparent;
    font-size: 12pt;
}}
QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLOR_SUNSET_GOLD};
    border-radius: 9px;
    background: {COLOR_ROCKSTAR_DARK};
}}
QRadioButton::indicator:checked {{
    background: {COLOR_VCS_TEAL};
    border-color: {COLOR_VCS_TEAL};
}}
QRadioButton::indicator:hover {{
    border-color: {COLOR_VCS_TEAL};
}}

QCheckBox {{
    color: {COLOR_TEXT_BODY};
    spacing: 8px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLOR_SUNSET_GOLD};
    background: {COLOR_ROCKSTAR_DARK};
    border-radius: 2px;
}}
QCheckBox::indicator:checked {{
    background: {COLOR_VCS_TEAL};
    border-color: {COLOR_VCS_TEAL};
}}
QCheckBox::indicator:hover {{
    border-color: {COLOR_VCS_TEAL};
}}

/* ── Progress bar — Rockstar gold → teal ───────────────────────────────── */
QProgressBar {{
    background-color: {COLOR_ROCKSTAR_DARK};
    border: 1px solid {COLOR_SUNSET_GOLD};
    border-radius: 3px;
    text-align: center;
    color: {COLOR_ROCKSTAR_BLACK};
    height: 22px;
    font-weight: bold;
}}
QProgressBar::chunk {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLOR_SUNSET_GOLD}, stop:0.5 {COLOR_VCS_TEAL}, stop:1 {COLOR_VCS_PURPLE_LIGHT});
}}

/* ── Group boxes — Rockstar dark panel ─────────────────────────────────── */
QGroupBox {{
    color: {COLOR_SUNSET_GOLD};
    background-color: {COLOR_CONTENT_PANEL};
    border: 1px solid {COLOR_SUNSET_GOLD};
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 10px;
    font-family: "{DISPLAY_FONT}", "Impact", "Arial Black", sans-serif;
    font-size: 12pt;
    letter-spacing: 1px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    background-color: {COLOR_ROCKSTAR_DARK};
    color: {COLOR_SUNSET_GOLD};
}}

/* ── Log pane — terminal green on dark ─────────────────────────────────── */
QTextBrowser, QPlainTextEdit {{
    background-color: rgba(5, 5, 10, 235);
    color: {COLOR_VCS_TEAL};
    border: 1px solid {COLOR_SUNSET_GOLD};
    border-radius: 8px;
    font-family: "{MONO_FONT}", "Courier New", monospace;
    font-size: 12pt;
}}

/* ── Scrollbars — gold handle on dark ──────────────────────────────────── */
QScrollBar:vertical {{
    background: {COLOR_ROCKSTAR_BLACK};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_SUNSET_GOLD};
    min-height: 30px;
    border-radius: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLOR_VCS_TEAL};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: {COLOR_ROCKSTAR_BLACK};
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: {COLOR_ROCKSTAR_PANEL};
}}

QWizard QPushButton#qt_wizard_close {{
    color: {COLOR_TEXT_DIM};
}}
"""


def browse_folder(parent, title="Select folder"):
    """Open a readable Qt file dialog (avoids native dialog crash on Win10)."""
    from PySide6.QtWidgets import QFileDialog
    dlg = QFileDialog(parent, title)
    dlg.setOption(QFileDialog.DontUseNativeDialog, True)
    dlg.setFileMode(QFileDialog.Directory)
    dlg.setOption(QFileDialog.ShowDirsOnly, True)
    dlg.setStyleSheet(
        "QFileDialog { background: #1a1a2e; color: #e0e0e0; }"
        "QTreeView, QListView, QComboBox {"
        "  background: #0d0d1a; color: #e0e0e0;"
        "  border: 1px solid #333; selection-background-color: #1a6b3a;"
        "  font-size: 12px;"
        "}"
        "QLineEdit { background: #0d0d1a; color: #e0e0e0; border: 1px solid #555; padding: 4px; }"
        "QPushButton { background: #2a5a3a; color: #fff; border: 1px solid #3d8a3d; "
        "  padding: 6px 16px; border-radius: 3px; min-width: 60px; }"
        "QPushButton:hover { background: #3d8a3d; }"
        "QLabel { color: #c0c0c0; }"
    )
    if dlg.exec() == QFileDialog.Accepted:
        files = dlg.selectedFiles()
        return files[0] if files else ""
    return ""


def browse_file(parent, title="Select file", filter_str="All files (*)"):
    """Open a readable Qt file dialog for selecting a single file."""
    from PySide6.QtWidgets import QFileDialog
    dlg = QFileDialog(parent, title)
    dlg.setOption(QFileDialog.DontUseNativeDialog, True)
    dlg.setFileMode(QFileDialog.ExistingFile)
    dlg.setNameFilter(filter_str)
    dlg.setStyleSheet(
        "QFileDialog { background: #1a1a2e; color: #e0e0e0; }"
        "QTreeView, QListView, QComboBox {"
        "  background: #0d0d1a; color: #e0e0e0;"
        "  border: 1px solid #333; selection-background-color: #1a6b3a;"
        "  font-size: 12px;"
        "}"
        "QLineEdit { background: #0d0d1a; color: #e0e0e0; border: 1px solid #555; padding: 4px; }"
        "QPushButton { background: #2a5a3a; color: #fff; border: 1px solid #3d8a3d; "
        "  padding: 6px 16px; border-radius: 3px; min-width: 60px; }"
        "QPushButton:hover { background: #3d8a3d; }"
        "QLabel { color: #c0c0c0; }"
    )
    if dlg.exec() == QFileDialog.Accepted:
        files = dlg.selectedFiles()
        return files[0] if files else ""
    return ""


def browse_save_file(parent, title="Save file", default_path="", filter_str="All files (*)"):
    """Open a readable Qt save-file dialog."""
    from PySide6.QtWidgets import QFileDialog
    dlg = QFileDialog(parent, title)
    dlg.setOption(QFileDialog.DontUseNativeDialog, True)
    dlg.setFileMode(QFileDialog.AnyFile)
    dlg.setAcceptMode(QFileDialog.AcceptSave)
    dlg.setNameFilter(filter_str)
    if default_path:
        dlg.selectFile(default_path)
    dlg.setStyleSheet(
        "QFileDialog { background: #1a1a2e; color: #e0e0e0; }"
        "QTreeView, QListView, QComboBox {"
        "  background: #0d0d1a; color: #e0e0e0;"
        "  border: 1px solid #333; selection-background-color: #1a6b3a;"
        "  font-size: 12px;"
        "}"
        "QLineEdit { background: #0d0d1a; color: #e0e0e0; border: 1px solid #555; padding: 4px; }"
        "QPushButton { background: #2a5a3a; color: #fff; border: 1px solid #3d8a3d; "
        "  padding: 6px 16px; border-radius: 3px; min-width: 60px; }"
        "QPushButton:hover { background: #3d8a3d; }"
        "QLabel { color: #c0c0c0; }"
    )
    if dlg.exec() == QFileDialog.Accepted:
        files = dlg.selectedFiles()
        return files[0] if files else ""
    return ""

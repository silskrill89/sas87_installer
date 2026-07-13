"""Top-level QWizard subclass — wires pages together with the SA sunset bg."""
from __future__ import annotations

import os
import random

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWizard

from .theme import SynthwaveBackground, COLOR_SUNSET_GOLD, COLOR_VCS_TEAL
from .welcome_page import WelcomePage
from .mod_source_page import ModSourcePage
from .setup_page import SetupPage
from .prereqs_page import PrereqsPage
from .install_page import InstallPage
from .complete_page import CompletePage

# Page IDs (must be imported by individual pages via .wizard)
PAGE_WELCOME = 1
PAGE_MOD_SOURCE = 2
PAGE_SETUP = 3
PAGE_PREREQS = 7
PAGE_INSTALL = 8
PAGE_COMPLETE = 9


class InstallerWizard(SynthwaveBackground):
    """The main wizard window. Inherits the painted GTA SA sunset background."""

    # Signal emitted when language changes
    language_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GTA San Andreas Stories 1987 — Installer")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setMinimumSize(1040, 740)
        self.setOptions(
            QWizard.NoBackButtonOnStartPage
            | QWizard.NoBackButtonOnLastPage
            | QWizard.HaveCustomButton1
        )
        # Set window flags properly for maximize button
        flags = self.windowFlags()
        flags &= ~Qt.WindowContextHelpButtonHint
        flags |= Qt.WindowMinimizeButtonHint
        flags |= Qt.WindowMaximizeButtonHint
        flags |= Qt.WindowFullscreenButtonHint
        self.setWindowFlags(flags)

        # Load saved settings for this install location
        from .. import settings as _settings
        self._saved_settings = _settings.load_settings()

        # Credits button — custom button in the bottom bar
        from PySide6.QtWidgets import QPushButton
        credits_btn = QPushButton("CREDITS")
        credits_btn.setCursor(Qt.PointingHandCursor)
        credits_btn.setStyleSheet(
            f"QPushButton {{ color: #0a0a0f; font-size: 12pt; font-weight: bold; "
            f"background: {COLOR_SUNSET_GOLD}; border: 2px solid {COLOR_SUNSET_GOLD}; "
            f"border-radius: 4px; padding: 8px 24px; }} "
            f"QPushButton:hover {{ background: {COLOR_VCS_TEAL}; border-color: {COLOR_VCS_TEAL}; }}"
        )
        credits_btn.clicked.connect(self._open_credits)
        self.setButton(QWizard.CustomButton1, credits_btn)

        # Add pages
        self.setPage(PAGE_WELCOME, WelcomePage(self))
        self.setPage(PAGE_MOD_SOURCE, ModSourcePage(self))
        self.setPage(PAGE_SETUP, SetupPage(self))
        self.setPage(PAGE_PREREQS, PrereqsPage(self))
        self.setPage(PAGE_INSTALL, InstallPage(self))
        self.setPage(PAGE_COMPLETE, CompletePage(self))

        self.setStartId(PAGE_WELCOME)

        # Load slideshow images
        self._load_slideshow_pool()

        # Restore saved settings into wizard fields/properties
        from .. import settings as _settings
        _settings.restore_wizard_state(self, self._saved_settings)

        # Repaint when page changes + re-scale fonts for new page
        self.currentIdChanged.connect(self._on_page_changed)

        # Emit language_changed signal when page is initialized
        self.currentIdChanged.connect(self._emit_language_on_page_change)

    def showEvent(self, event):
        super().showEvent(event)
        self._reposition_credits_btn()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_credits_btn()
        self._scale_fonts_to_window()

    def _reposition_credits_btn(self):
        """Move credits button to the left side of the button bar."""
        from PySide6.QtWidgets import QDialogButtonBox
        btn = self.button(QWizard.CustomButton1)
        if not btn:
            return
        btn_box = self.findChild(QDialogButtonBox)
        if btn_box:
            btn_box.removeButton(btn)
            btn_box.addButton(btn, QDialogButtonBox.ActionRole)
            # Move to far left
            layout = btn_box.layout()
            if layout:
                layout.removeWidget(btn)
                layout.insertWidget(0, btn)

    def _scale_fonts_to_window(self):
        """Scale all QLabel fonts proportionally to window size.

        At the minimum window size (1040x740), fonts stay at their base size.
        When the window is maximized or resized larger, fonts scale up
        proportionally so text is readable at any window size.
        """
        from PySide6.QtWidgets import QLabel
        from .theme import heading_font, body_font, mono_font

        min_w = 1040
        min_h = 740
        w = max(self.width(), 1)
        h = max(self.height(), 1)
        scale = min(w / min_w, h / min_h)
        scale = max(1.0, min(scale, 2.5))

        for lbl in self.findChildren(QLabel):
            cur = lbl.font()
            sz = cur.pointSizeF()
            if sz <= 0:
                continue
            # Detect font family from current font
            fam = cur.family()
            from .theme import DISPLAY_FONT, UI_FONT, MONO_FONT
            if fam == UI_FONT:
                new_font = body_font(round(sz * scale))
            elif fam == MONO_FONT:
                new_font = mono_font(round(sz * scale))
            else:
                new_font = heading_font(round(sz * scale), cur.bold())
            lbl.setFont(new_font)

    def _on_page_changed(self):
        """Repaint background + scale fonts for the new page."""
        self.update()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(10, self._scale_fonts_to_window)

    def _emit_language_on_page_change(self, page_id):
        """Emit language_changed signal when a page is initialized."""
        from .. import i18n
        # Emit signal so the new page can refresh its text
        self.language_changed.emit(i18n.get_language())

    def _open_credits(self):
        from .credits_window import open_credits
        open_credits(self)

    def _load_slideshow_pool(self):
        """Gather all splash images + cached screenshots into the slideshow pool.
        Splash images have pre-baked FG/BG layers in splash_layers/."""
        import glob as _glob

        pool = []

        # Splash images (have baked FG/BG layers)
        splash_dir = os.path.join(os.path.dirname(__file__), "splash")
        if os.path.isdir(splash_dir):
            for ext in ("*.png", "*.jpg", "*.jpeg"):
                pool.extend(_glob.glob(os.path.join(splash_dir, ext)))

        # Cached screenshots from GitHub (no baked layers, use fallback)
        try:
            from .. import screenshot_cache
            pool.extend(screenshot_cache.get_random_screenshots(20))
        except Exception:
            pass

        random.shuffle(pool)
        self.load_slideshow(pool)

    def next(self):
        super().next()

    def closeEvent(self, event):
        """Confirm close + save settings for next run."""
        from PySide6.QtWidgets import QMessageBox
        from .. import settings as _settings

        # Don't ask on the final page (install complete)
        current_page = self.currentId()
        from .wizard import PAGE_COMPLETE
        if current_page == PAGE_COMPLETE:
            _settings.save_wizard_state(self)
            event.accept()
            return

        reply = QMessageBox.question(
            self,
            "Quit Installer?",
            "Are you sure you want to close the installer?\n\n"
            "Your settings will be saved and restored next time you run "
            "the installer from this location.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            _settings.save_wizard_state(self)
            event.accept()
        else:
            event.ignore()

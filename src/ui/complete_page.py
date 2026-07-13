"""Completion page - final summary + launch button."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWizardPage,
)

from .. import cache, util, i18n


class CompletePage(QWizardPage):
    splash_image_name = "install.png"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("")
        self._dest_sa_root = ""

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(40, 30, 40, 30)

        # Title
        self._title = QLabel(i18n.t("complete_title"))
        self._title.setProperty("heading", True)
        self._title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._title)

        self.summary = QLabel("")
        self.summary.setWordWrap(True)
        self.summary.setTextFormat(Qt.RichText)
        layout.addWidget(self.summary)

        layout.addSpacing(12)

        btn_row = QHBoxLayout()

        # Launch button
        self._launch_btn = QPushButton(i18n.t("complete_launch"))
        self._launch_btn.setProperty("accent", True)
        self._launch_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d8a3d;
                color: #ffffff;
                border: 2px solid #5fc45f;
                border-radius: 8px;
                padding: 12px 32px;
                font-size: 14pt;
                font-weight: bold;
                min-width: 280px;
                text-shadow: 0 0 10px #5fc45f;
            }
            QPushButton:hover {
                background-color: #5fc45f;
                border-color: #7fff7f;
                color: #0a0a0f;
            }
            QPushButton:pressed {
                background-color: #2d6a2d;
            }
        """)
        self._launch_btn.clicked.connect(self._launch)
        btn_row.addWidget(self._launch_btn)

        # Open dest button
        self._open_dest_btn = QPushButton(i18n.t("complete_open_dest"))
        self._open_dest_btn.clicked.connect(self._open_dest)
        btn_row.addWidget(self._open_dest_btn)

        # Open cache button
        self._open_cache_btn = QPushButton(i18n.t("complete_open_cache"))
        self._open_cache_btn.clicked.connect(self._open_cache)
        btn_row.addWidget(self._open_cache_btn)

        btn_row.addStretch()

        layout.addLayout(btn_row)

        layout.addStretch()

        # Footer
        self._footer = QLabel(i18n.t("complete_tip"))
        self._footer.setProperty("dim", True)
        self._footer.setWordWrap(True)
        layout.addWidget(self._footer)

    def initializePage(self):
        dest = self.wizard().property("dest_sa_root") or ""
        if hasattr(dest, "toString"):
            dest = dest.toString()
        self._dest_sa_root = str(dest).strip()

        installed = self.wizard().property("enabled_mod_ids") or []
        source_sa = self.wizard().property("source_sa_root") or ""
        if hasattr(source_sa, "toString"):
            source_sa = source_sa.toString()

        # Find the latest log file
        import glob as _glob
        log_files = sorted(_glob.glob(os.path.join(cache.CACHE_LOGS, "install_*.log")),
                           key=os.path.getmtime, reverse=True)
        log_path = log_files[0] if log_files else cache.CACHE_LOGS

        self.summary.setText(
            "<div style='line-height:160%;'>"
            "<span style='color:#5bff8a;font-size:14pt;'>All stages completed successfully!</span><br><br>"
            "<b>Source (vanilla SA):</b> <code>" + str(source_sa) + "</code><br>"
            "<b>Modded install:</b> <code>" + self._dest_sa_root + "</code><br>"
            "<b>Mods installed:</b> " + (", ".join(installed) if installed else "(none - check log)") + "<br>"
            "<b>Install log:</b> <code>" + log_path + "</code><br>"
            "<b>Backup location:</b> <code>" + cache.CACHE_BACKUPS + "</code><br><br>"
            "Click <b>Play GTA San Andreas Stories 1987</b> to start the game, "
            "or use the buttons below to open the install folder."
            "</div>"
        )

    def _launch(self):
        if not self._dest_sa_root:
            return
        # Priority: gta_sa.exe (mod provides this) > gta-sa.exe (Steam)
        for name in ["gta_sa.exe", "gta-sa.exe"]:
            exe = os.path.join(self._dest_sa_root, name)
            if os.path.isfile(exe):
                util.open_file(exe)
                return

    def _open_dest(self):
        if self._dest_sa_root and os.path.isdir(self._dest_sa_root):
            util.open_in_file_manager(self._dest_sa_root)

    def _open_cache(self):
        cache.ensure_dirs()
        util.open_in_file_manager(cache.CACHE_ROOT)

    def initializePage(self):
        """Connect to wizard's language_changed signal."""
        self.wizard().language_changed.connect(self._on_language_changed)

    def _on_language_changed(self, lang_code):
        """Update all text when language changes."""
        self._title.setText(i18n.t("complete_title"))
        self._launch_btn.setText(i18n.t("complete_launch"))
        self._open_dest_btn.setText(i18n.t("complete_open_dest"))
        self._open_cache_btn.setText(i18n.t("complete_open_cache"))
        self._footer.setText(i18n.t("complete_tip"))

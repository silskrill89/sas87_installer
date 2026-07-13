"""Combined setup page — source SA and destination in one step.

Merges two separate pages into one to reduce clicks:
1. Source SA folder (auto-detect + browse)
2. Destination folder (suggest + browse)
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QWizardPage,
)

from .. import sa_detector
from .theme import browse_folder


class SetupPage(QWizardPage):
    splash_image_name = "source_sa.png"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("")

        self._auto_ran = False

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(30, 20, 30, 20)

        title = QLabel("SETUP")
        title.setProperty("subheading", True)
        layout.addWidget(title)

        # ── Source SA ──
        src_box = QGroupBox("Source — Your GTA San Andreas folder")
        src_layout = QVBoxLayout(src_box)

        src_hint = QLabel(
            "Point to your existing GTA San Andreas install. "
            "The wizard will copy these files to a new modded folder."
        )
        src_hint.setProperty("dim", True)
        src_hint.setWordWrap(True)
        src_layout.addWidget(src_hint)

        src_row = QHBoxLayout()
        self.sa_edit = QLineEdit()
        self.sa_edit.setPlaceholderText("e.g. C:\\Program Files (x86)\\Steam\\...")
        src_row.addWidget(self.sa_edit, 1)
        browse_src = QPushButton("Browse...")
        browse_src.clicked.connect(self._browse_sa)
        src_row.addWidget(browse_src)
        auto_btn = QPushButton("Auto-detect")
        auto_btn.clicked.connect(self._autodetect)
        src_row.addWidget(auto_btn)
        src_layout.addLayout(src_row)

        self.sa_status = QLabel("")
        self.sa_status.setWordWrap(True)
        self.sa_status.setTextFormat(Qt.RichText)
        src_layout.addWidget(self.sa_status)
        layout.addWidget(src_box)

        # ── Destination ──
        self.dest_box = QGroupBox("Destination — Modded install folder")
        dest_layout = QVBoxLayout(self.dest_box)

        dest_hint = QLabel(
            "Pick where to create the standalone modded SA install. "
            "At least 5 GB free space recommended."
        )
        dest_hint.setProperty("dim", True)
        dest_hint.setWordWrap(True)
        dest_layout.addWidget(dest_hint)

        dest_row = QHBoxLayout()
        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText("e.g. D:\\Games\\GTA SAS 1987")
        dest_row.addWidget(self.dest_edit, 1)
        browse_dest = QPushButton("Browse...")
        browse_dest.clicked.connect(self._browse_dest)
        dest_row.addWidget(browse_dest)
        suggest_btn = QPushButton("Suggest")
        suggest_btn.clicked.connect(self._suggest_dest)
        dest_row.addWidget(suggest_btn)
        dest_layout.addLayout(dest_row)

        self.dest_status = QLabel("")
        self.dest_status.setWordWrap(True)
        self.dest_status.setTextFormat(Qt.RichText)
        dest_layout.addWidget(self.dest_status)

        layout.addWidget(self.dest_box)

        layout.addStretch()

        self.registerField("source_sa_root*", self.sa_edit)
        self.registerField("dest_sa_root*", self.dest_edit)

    # ── Source SA methods ──

    def _browse_sa(self):
        path = browse_folder(self, "Select your vanilla San Andreas install folder")
        if path:
            self.sa_edit.setText(path)
            self._validate_and_detect(path)

    def _autodetect(self, silent: bool = False):
        install = sa_detector.detect_install()
        if install:
            self.sa_edit.setText(install.root)
            self._show_sa_status(install)
            self._suggest_dest()
        elif not silent:
            self.sa_status.setText(
                "<span style='color:#ff5b5b'>Could not auto-detect. Browse to it manually.</span>"
            )

    def _validate_and_detect(self, path: str):
        install = sa_detector.validate_root(path)
        if install:
            self._show_sa_status(install)
            self._suggest_dest()
        else:
            self.sa_status.setText(
                "<span style='color:#ff5b5b'>No gta_sa.exe found. Pick the SA install root.</span>"
            )

    def _show_sa_status(self, install: sa_detector.SAInstall):
        self.sa_status.setText(
            f"<span style='color:#5bff8a'>Found GTA San Andreas install via {install.source}.</span>"
        )

    # ── Destination methods ──

    def _browse_dest(self):
        path = browse_folder(self, "Select destination folder")
        if path:
            self.dest_edit.setText(path)
            self._validate_dest(path)

    def _suggest_dest(self):
        source = self.sa_edit.text().strip()
        if source:
            drive = os.path.splitdrive(source)[0]
            if not drive:
                drive = os.path.splitdrive(os.path.abspath(source))[0]
            suggestion = os.path.join(drive + os.sep, "Games", "GTA SAS 1987")
        else:
            suggestion = os.path.join(os.path.expanduser("~"), "Games", "GTA SAS 1987")
        self.dest_edit.setText(suggestion)
        self._validate_dest(suggestion)

    def _validate_dest(self, path: str):
        source = self.sa_edit.text().strip()
        if source and os.path.normpath(path) == os.path.normpath(source):
            self.dest_status.setText(
                "<span style='color:#ff5b5b'>Cannot be the same as source.</span>"
            )
            return
        if source and os.path.normpath(path).startswith(os.path.normpath(source) + os.sep):
            self.dest_status.setText(
                "<span style='color:#ff5b5b'>Cannot be inside the source folder.</span>"
            )
            return
        if os.path.isdir(path) and os.listdir(path):
            self.dest_status.setText(
                "<span style='color:#ffe600'>Folder exists and is non-empty — will merge.</span>"
            )
        else:
            try:
                import shutil as _sh
                _, _, free = _sh.disk_usage(path if os.path.isdir(path) else os.path.dirname(path) or ".")
                free_gb = free / (1024 ** 3)
                color = "#5bff8a" if free_gb >= 5 else "#ffe600"
                self.dest_status.setText(
                    f"<span style='color:{color}'>OK — {free_gb:.1f} GB free.</span>"
                )
            except Exception:
                self.dest_status.setText("<span style='color:#5bff8a'>OK</span>")

    # ── Validate ──

    def validatePage(self):
        sa_path = self.sa_edit.text().strip()
        dest_path = self.dest_edit.text().strip()

        # Validate source
        if not sa_path or not os.path.isdir(sa_path):
            self.sa_status.setText(
                "<span style='color:#ff5b5b'>Please pick a valid SA folder.</span>"
            )
            return False
        install = sa_detector.validate_root(sa_path)
        if not install:
            self.sa_status.setText(
                "<span style='color:#ff5b5b'>No gta_sa.exe found. Pick the SA install root.</span>"
            )
            return False
        self.wizard().setProperty("source_sa_root", sa_path)

        # Validate destination
        if not dest_path:
            self.dest_status.setText(
                "<span style='color:#ff5b5b'>Please pick a destination folder.</span>"
            )
            return False
        if os.path.normpath(dest_path) == os.path.normpath(sa_path):
            self.dest_status.setText(
                "<span style='color:#ff5b5b'>Cannot be the same as source.</span>"
            )
            return False
        try:
            os.makedirs(dest_path, exist_ok=True)
        except Exception as e:
            self.dest_status.setText(
                f"<span style='color:#ff5b5b'>Could not create folder: {e}</span>"
            )
            return False
        self.wizard().setProperty("dest_sa_root", dest_path)

        # skip_backup is now set by WelcomePage; do not override here

        return True

    def nextId(self):
        from .wizard import PAGE_PREREQS
        return PAGE_PREREQS

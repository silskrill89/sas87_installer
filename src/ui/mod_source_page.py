"""Mod source choice page.

The user must choose:
    * "I already have mod files (.zip/.rar/.7z) downloaded" — wizard will
      scan a folder of archives and use those instead of downloading.
    * "Download everything for me" — wizard will fetch every mod from the
      internet (MediaFire / GitHub / MixMods / LibertyCity as configured).

Also optionally scans the user's Downloads folder for mod files.
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QVBoxLayout, QWizardPage, QButtonGroup,
)

from .. import config, extractor
from .theme import browse_folder


class ModSourcePage(QWizardPage):
    splash_image_name = "mod_source.png"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("")

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(40, 30, 40, 30)

        title = QLabel("MOD  SOURCE")
        title.setProperty("subheading", True)
        layout.addWidget(title)

        intro = QLabel(
            "<div style='line-height:150%;'>"
            "Do you already have the mod files downloaded on your computer, "
            "or should the wizard download them for you?"
            "</div>"
        )
        intro.setWordWrap(True)
        intro.setTextFormat(Qt.RichText)
        layout.addWidget(intro)

        # --- Radio choices ---
        choice_box = QGroupBox("Choose one")
        choice_layout = QVBoxLayout(choice_box)

        self.rb_have = QRadioButton("I already have mod files")
        self.rb_have.setToolTip(
            "You have .zip / .rar / .7z archives of the mods already. "
            "The wizard will scan a folder and use them instead of downloading."
        )
        choice_layout.addWidget(self.rb_have)

        self.rb_download = QRadioButton("Download everything for me")
        self.rb_download.setToolTip(
            "The wizard will fetch the main mod from MediaFire "
            "and prerequisites from GitHub/MixMods."
        )
        choice_layout.addWidget(self.rb_download)

        # Default: download (the common case)
        self.rb_download.setChecked(True)

        self._choice_group = QButtonGroup(self)
        self._choice_group.addButton(self.rb_have, 1)
        self._choice_group.addButton(self.rb_download, 2)
        self._choice_group.buttonClicked.connect(self._on_choice_changed)

        layout.addWidget(choice_box)

        # --- Archives folder (only visible if "I have mods" selected) ---
        self.arch_box = QGroupBox("Archives folder")
        arch_layout = QVBoxLayout(self.arch_box)

        arch_hint = QLabel(
            "Point the wizard at the folder containing your mod archives. "
            "It will scan for .zip / .rar / .7z and use them instead of downloading."
        )
        arch_hint.setProperty("dim", True)
        arch_hint.setWordWrap(True)
        arch_layout.addWidget(arch_hint)

        row = QHBoxLayout()
        self.arch_edit = QLineEdit()
        self.arch_edit.setPlaceholderText(
            "e.g.  /home/user/Downloads/GTA SAS 1987 mods"
            if not config.IS_WINDOWS else
            "e.g.  D:\\Downloads\\GTA SAS 1987 mods"
        )
        row.addWidget(self.arch_edit, 1)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_archives)
        row.addWidget(browse_btn)
        arch_layout.addLayout(row)

        self.arch_status = QLabel("")
        self.arch_status.setWordWrap(True)
        arch_layout.addWidget(self.arch_status)
        layout.addWidget(self.arch_box)

        # --- Downloads folder scan (always visible) ---
        dl_box = QGroupBox("Downloads folder")
        dl_layout = QVBoxLayout(dl_box)

        self.scan_dl_cb = QCheckBox(
            "Scan my Downloads folder for mod files"
        )
        self.scan_dl_cb.setChecked(True)
        self.scan_dl_cb.setToolTip(
            "The wizard will look in your Downloads folder for mod files "
            "in addition to the archives folder above."
        )
        dl_layout.addWidget(self.scan_dl_cb)

        dl_row = QHBoxLayout()
        self.dl_edit = QLineEdit()
        default_dl = os.path.join(os.path.expanduser("~"), "Downloads")
        self.dl_edit.setText(default_dl)
        self.dl_edit.setPlaceholderText("e.g.  C:\\Users\\You\\Downloads")
        dl_row.addWidget(self.dl_edit, 1)
        dl_browse = QPushButton("Browse...")
        dl_browse.clicked.connect(self._browse_downloads)
        dl_row.addWidget(dl_browse)
        dl_layout.addLayout(dl_row)

        self.dl_status = QLabel("")
        self.dl_status.setWordWrap(True)
        dl_layout.addWidget(self.dl_status)
        layout.addWidget(dl_box)

        layout.addStretch()

        # Register fields
        self.registerField("have_local_mods", self.rb_have, "checked")
        self.registerField("archives_folder", self.arch_edit)
        self.registerField("scan_downloads", self.scan_dl_cb, "checked")
        self.registerField("downloads_folder", self.dl_edit)

        # Initial state
        self._on_choice_changed()
        self._auto_detected = False

    def initializePage(self):
        """Auto-detect mod archives in the installer's directory."""
        if self._auto_detected:
            return
        self._auto_detected = True

        # Scan the directory where the .exe (or script) lives
        exe_dir = config.PROJECT_ROOT
        archives = extractor.scan_archives(exe_dir, exclude_dirs=[config.CACHE_EXTRACTED])
        if archives:
            # Found mod archives next to the installer — auto-select "I have mods"
            self.rb_have.setChecked(True)
            self._on_choice_changed()
            self.arch_edit.setText(exe_dir)
            self.arch_status.setText(
                f"<span style='color:#5bff8a'>Found {len(archives)} mod archive(s) "
                f"next to the installer. Auto-selected.</span>"
            )

    # ------------------------------------------------------------------
    def _on_choice_changed(self, *_args):
        have = self.rb_have.isChecked()
        self.arch_box.setVisible(have)
        self.arch_edit.setEnabled(have)

    def _browse_archives(self):
        path = browse_folder(self, "Select folder containing mod archives")
        if path:
            self.arch_edit.setText(path)
            archives = extractor.scan_archives(path, exclude_dirs=[config.CACHE_EXTRACTED])
            if not archives:
                self.arch_status.setText(
                    "<span style='color:#ffe600'>No .zip / .rar / .7z files found in that folder. "
                    "Pick another folder or switch to 'Download for me'.</span>"
                )
            else:
                self.arch_status.setText(
                    f"<span style='color:#5bff8a'>Found {len(archives)} archive(s). "
                    "The wizard will look here before downloading.</span>"
                )

    def _browse_downloads(self):
        path = browse_folder(self, "Select your Downloads folder")
        if path:
            self.dl_edit.setText(path)

    # ------------------------------------------------------------------
    def validatePage(self):
        # Store choice on the wizard for later pages
        have = self.rb_have.isChecked()
        self.wizard().setProperty("have_local_mods", have)
        self.wizard().setProperty("archives_folder", self.arch_edit.text().strip() if have else "")
        # Store downloads folder
        scan_dl = self.scan_dl_cb.isChecked()
        dl_folder = self.dl_edit.text().strip() if scan_dl else ""
        self.wizard().setProperty("scan_downloads", scan_dl)
        self.wizard().setProperty("downloads_folder", dl_folder)
        if have:
            folder = self.arch_edit.text().strip()
            if not folder:
                self.arch_status.setText(
                    "<span style='color:#ff5b5b'>Please pick an archives folder, "
                    "or switch to 'Download for me'.</span>"
                )
                return False
        return True

    def nextId(self):
        from .wizard import PAGE_SETUP
        return PAGE_SETUP

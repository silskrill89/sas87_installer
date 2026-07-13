"""Prerequisites & mod selection page.

Auto-detects which mod files are available across all sources.
Each missing mod has a Download button that opens its specific download page.
When all required mods are present, the user can proceed.
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QRadioButton, QVBoxLayout, QWizardPage,
)

from .. import config, extractor, scraper, i18n
from .theme import COLOR_GROVE_GREEN_LIGHT, COLOR_TEXT_BRIGHT, COLOR_SUNSET_GOLD


class PrereqsPage(QWizardPage):
    splash_image_name = "prereqs.png"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("")

        self._mod_sources: list[config.ModSource] = []
        self._checkboxes: dict[str, QCheckBox] = {}
        self._dyom_radios: dict[str, QRadioButton] = {}
        self._dyom_group: QButtonGroup | None = None
        self._found_archives: dict[str, str] = {}
        self._download_buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(40, 30, 40, 30)

        # Title
        self._title = QLabel(i18n.t("prereqs_title"))
        self._title.setProperty("subheading", True)
        layout.addWidget(self._title)

        # Description
        self._body = QLabel(
            "<div style='line-height:150%;'>"
            + i18n.t("prereqs_desc")
            + "</div>"
        )
        self._body.setWordWrap(True)
        self._body.setTextFormat(Qt.RichText)
        layout.addWidget(self._body)

        # --- Mod list ---
        self._grid_box = QGroupBox(i18n.t("prereqs_title"))
        self.grid = QGridLayout(self._grid_box)
        self.grid.setColumnStretch(3, 1)
        layout.addWidget(self._grid_box)

        # --- Buttons ---
        btn_row = QHBoxLayout()

        self._browse_btn = QPushButton(i18n.t("prereqs_browse"))
        self._browse_btn.setStyleSheet(
            f"QPushButton {{ color: {COLOR_SUNSET_GOLD}; border-color: {COLOR_SUNSET_GOLD}; "
            f"padding: 8px 20px; font-size: 11pt; }} "
            f"QPushButton:hover {{ background-color: rgba(255,184,77,40); color: #ffffff; }}"
        )
        self._browse_btn.clicked.connect(self._browse_for_files)
        btn_row.addWidget(self._browse_btn)

        self._rescan_btn = QPushButton(i18n.t("prereqs_rescan"))
        self._rescan_btn.setStyleSheet(
            f"QPushButton {{ color: #c0c0c0; border-color: #555; "
            f"padding: 8px 20px; font-size: 11pt; }} "
            f"QPushButton:hover {{ background-color: rgba(100,100,100,40); color: #ffffff; }}"
        )
        self._rescan_btn.clicked.connect(lambda: self._rescrape(silent=True))
        btn_row.addWidget(self._rescan_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

        self._rescrape(silent=True)

    # ------------------------------------------------------------------
    def _get_folders(self) -> tuple[str, str]:
        wiz = self.wizard()
        archives = (wiz.property("archives_folder") if wiz else None) or ""
        if hasattr(archives, "toString"):
            archives = archives.toString()
        archives = str(archives).strip()
        downloads = (wiz.property("downloads_folder") if wiz else None) or ""
        if hasattr(downloads, "toString"):
            downloads = downloads.toString()
        downloads = str(downloads).strip()
        return archives, downloads

    def _scan_all_archives(self) -> list[str]:
        archives_folder, downloads_folder = self._get_folders()
        exclude = [config.CACHE_EXTRACTED]
        all_archives = []
        if archives_folder:
            all_archives.extend(extractor.scan_archives(archives_folder, exclude_dirs=exclude))
        if downloads_folder:
            all_archives.extend(extractor.scan_archives(downloads_folder, exclude_dirs=exclude))
        from .. import cache
        cache.ensure_dirs()
        all_archives.extend(extractor.scan_archives(config.CACHE_DOWNLOADS, exclude_dirs=exclude))
        return all_archives

    def _rescrape(self, silent: bool = False):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._checkboxes.clear()
        self._dyom_radios.clear()
        self._dyom_group = None
        self._found_archives.clear()
        self._download_buttons.clear()

        if not silent:
            self.status_label.setText("Scanning local folders...")
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()

        # Start with hardcoded mod list
        self._mod_sources = list(config.ALL_MODS)

        # Scan local folders FIRST - skip site scraping if files found locally
        all_archives = self._scan_all_archives()

        # Pre-match archives to find what we have locally
        local_matches: dict[str, str] = {}
        for mod in self._mod_sources:
            found = extractor.find_mod_in_archives(
                all_archives, mod.id, mod.name, mod.file_matchers
            )
            if found:
                local_matches[mod.id] = found

        # Only scrape site for mods not found locally
        missing_ids = [m.id for m in self._mod_sources if m.id not in local_matches]
        if missing_ids:
            if not silent:
                self.status_label.setText("Checking online sources for missing mods...")
                from PySide6.QtWidgets import QApplication
                QApplication.processEvents()

            try:
                scraped_sources = scraper.resolve_mod_sources()
                # Merge scraped URLs for missing mods only
                for mod in self._mod_sources:
                    if mod.id in missing_ids:
                        for scraped_mod in scraped_sources:
                            if scraped_mod.id == mod.id:
                                # Update URL if scraped version has a better source
                                if not mod.manual_download_required:
                                    idx = self._mod_sources.index(mod)
                                    self._mod_sources[idx] = scraped_mod
                                break
            except Exception as e:
                if not silent:
                    self.status_label.setText(
                        f"<span style='color:#ffe600;'>Online check failed ({e}); "
                        "using local files only.</span>"
                    )

        # Store local matches
        self._found_archives = local_matches

        # Header
        header_name = QLabel("MOD")
        header_status = QLabel("STATUS")
        header_action = QLabel("")
        for h in (header_name, header_status):
            f = h.font(); f.setBold(True); h.setFont(f)
            h.setStyleSheet("color: #5fff8c;")
        self.grid.addWidget(header_name, 0, 0)
        self.grid.addWidget(header_status, 0, 1)
        self.grid.addWidget(header_action, 0, 2)

        for i, mod in enumerate(self._mod_sources, start=1):
            has_file = mod.id in self._found_archives
            found_archive = self._found_archives.get(mod.id)

            # Mod name
            if mod.is_main_mod:
                name_lbl = QLabel(
                    f"<b>{mod.name}</b><br>"
                    f"<span style='color:#5bff8a;'>(REQUIRED)</span>"
                )
                name_lbl.setTextFormat(Qt.RichText)
                cb = QCheckBox()
                cb.setChecked(True)
                cb.setEnabled(False)
                self._checkboxes[mod.id] = cb
            elif mod.id in ("dyom", "dyom_v83"):
                # DYOM versions use radio buttons (only one can be selected)
                name_lbl = QLabel(mod.name)
                rb = QRadioButton()
                rb.setChecked(mod.enabled_by_default)
                rb.setProperty("mod_id", mod.id)
                # Create group on first DYOM mod
                if self._dyom_group is None:
                    self._dyom_group = QButtonGroup(self)
                    self._dyom_group.setExclusive(True)
                self._dyom_group.addButton(rb)
                self._dyom_radios[mod.id] = rb
            else:
                name_lbl = QLabel(mod.name)
                cb = QCheckBox()
                cb.setChecked(mod.enabled_by_default)
                if not mod.optional:
                    cb.setEnabled(False)
                    cb.setChecked(True)
                self._checkboxes[mod.id] = cb

            # Status
            if has_file:
                is_valid, reason = extractor.verify_mod_file(found_archive)
                if is_valid:
                    status_lbl = QLabel(
                        f"<span style='color: #5bff8a;'>✓ Found</span> "
                        f"<code style='color:#7a6a9b; font-size:9pt;'>{os.path.basename(found_archive)}</code>"
                    )
                else:
                    status_lbl = QLabel(
                        f"<span style='color: #ffe600;'>⚠ {reason}</span> "
                        f"<code style='color:#7a6a9b; font-size:9pt;'>{os.path.basename(found_archive)}</code>"
                    )
            else:
                status_lbl = QLabel("<b style='color: #ff5b5b;'>Missing</b>")
            status_lbl.setTextFormat(Qt.RichText)
            status_lbl.setWordWrap(True)

            # Action button
            if has_file:
                action_btn = QLabel("✓")
                action_btn.setStyleSheet("color: #5bff8a; font-size: 14pt; font-weight: bold;")
            else:
                dl_url = mod.manual_download_url or mod.url or mod.page_url
                if dl_url:
                    action_btn = QPushButton("Download")
                    action_btn.setStyleSheet(
                        "QPushButton { color: #ffb84d; border-color: #ffb84d; "
                        "min-width: 90px; padding: 4px 12px; font-size: 11pt; }"
                        "QPushButton:hover { background-color: rgba(255,184,77,40); "
                        "color: #ffffff; }"
                    )
                    action_btn.clicked.connect(
                        lambda _checked, url=dl_url:
                            self._open_download_url(url)
                    )
                    self._download_buttons[mod.id] = action_btn
                else:
                    action_btn = QLabel("(no link)")
                    action_btn.setProperty("dim", True)

            self.grid.addWidget(name_lbl, i, 0)
            self.grid.addWidget(status_lbl, i, 1)
            self.grid.addWidget(action_btn, i, 2)

        # Status summary
        missing = [m for m in self._mod_sources if m.id not in self._found_archives]
        found = len(self._mod_sources) - len(missing)
        total = len(self._mod_sources)

        if not missing:
            self.status_label.setText(
                f"<span style='color:#5bff8a; font-size:11pt;'>"
                f"All {total} mod(s) found — ready to install!</span>"
            )
        else:
            self.status_label.setText(
                f"<span style='color:#ffe600;'>{found}/{total} found. "
                f"<b style='color:#ff5b5b;'>{len(missing)} missing</b> — "
                f"click Download on each, or use Browse for Files.</span>"
            )

    # ------------------------------------------------------------------
    def _open_download_url(self, url: str):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl(url))

    # ------------------------------------------------------------------
    def _browse_for_files(self):
        from PySide6.QtWidgets import QFileDialog
        missing = [m for m in self._mod_sources if m.id not in self._found_archives]
        if not missing:
            return

        for mod in missing:
            path, _ = QFileDialog.getOpenFileName(
                self, f"Select archive for {mod.name}",
                "", "All supported (*.zip *.rar *.7z *.cleo *.cs *.asi);;Archives (*.zip *.rar *.7z);;Mod files (*.cleo *.cs *.asi);;All files (*)",
                options=QFileDialog.DontUseNativeDialog,
            )
            if path:
                from .. import cache
                cache.ensure_dirs()
                import shutil
                ext = os.path.splitext(path)[1]
                dest = os.path.join(config.CACHE_DOWNLOADS, f"{mod.id}{ext}")
                shutil.copy2(path, dest)

        self._rescrape(silent=True)

    # ------------------------------------------------------------------
    def validatePage(self):
        enabled = [mid for mid, cb in self._checkboxes.items() if cb.isChecked()]

        # Add selected DYOM version from radio buttons
        for mid, rb in self._dyom_radios.items():
            if rb.isChecked():
                enabled.append(mid)

        self.wizard().setProperty("enabled_mod_ids", enabled)
        self.wizard().setProperty("mod_sources", self._mod_sources)
        self.wizard().setProperty("found_archives", self._found_archives)
        return True

    def nextId(self):
        from .wizard import PAGE_INSTALL
        return PAGE_INSTALL

    def initializePage(self):
        """Connect to wizard's language_changed signal."""
        self.wizard().language_changed.connect(self._on_language_changed)

    def _on_language_changed(self, lang_code):
        """Update all text when language changes."""
        self._title.setText(i18n.t("prereqs_title"))
        self._body.setText(
            "<div style='line-height:150%;'>"
            + i18n.t("prereqs_desc")
            + "</div>"
        )
        self._grid_box.setTitle(i18n.t("prereqs_title"))
        self._browse_btn.setText(i18n.t("prereqs_browse"))
        self._rescan_btn.setText(i18n.t("prereqs_rescan"))

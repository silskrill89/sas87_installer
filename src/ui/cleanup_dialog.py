"""Post-install cleanup dialog — offers to remove installer artifacts after install."""
from __future__ import annotations

import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout,
)

from .. import cleanup

logger = logging.getLogger(__name__)


class CleanupDialog(QDialog):
    """Modal dialog shown after successful install — offers cleanup options."""

    def __init__(self, has_local_mods: bool = False, sa_copy_path: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Installation Complete — Cleanup Options")
        self.setMinimumWidth(560)
        self.setMinimumHeight(380)
        self.setModal(True)

        # Store what the user selected
        self.remove_downloads = False
        self.remove_extracted = False
        self.remove_sa_copy = False
        self.clean_logs = False
        self.clean_backups = False

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        # Header
        header = QLabel("INSTALLATION COMPLETE")
        header.setProperty("heading", True)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #5bff8a; font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        # Space info
        space_mb = cleanup.get_space_freed_mb()
        info = QLabel(
            f"<div style='line-height:150%; text-align:center;'>"
            f"Your modded San Andreas is ready.<br><br>"
            f"Cache files used: <b>{space_mb:.1f} MB</b><br><br>"
            f"Select what to clean up:"
            f"</div>"
        )
        info.setWordWrap(True)
        info.setTextFormat(Qt.RichText)
        layout.addWidget(info)

        # Checkboxes
        checks_box = QGroupBox("Cleanup options")
        checks_layout = QVBoxLayout(checks_box)

        self.chk_downloads = QCheckBox("Remove downloaded archives (saves download cache)")
        self.chk_extracted = QCheckBox("Remove extracted mod files (saves extraction cache)")
        self.chk_logs = QCheckBox("Clean old logs (keep last 10)")
        self.chk_backups = QCheckBox("Clean old backups (keep last 5)")

        # Only show SA copy option if we have a source path
        self.chk_sa_copy = QCheckBox(f"Remove vanilla SA source copy")
        self.chk_sa_copy.setVisible(bool(sa_copy_path))
        if sa_copy_path:
            self.chk_sa_copy.setText(f"Remove vanilla SA source copy ({sa_copy_path})")

        # Check the sensible defaults
        self.chk_downloads.setChecked(True)
        self.chk_extracted.setChecked(True)
        self.chk_logs.setChecked(True)
        self.chk_backups.setChecked(False)

        checks_layout.addWidget(self.chk_downloads)
        checks_layout.addWidget(self.chk_extracted)
        checks_layout.addWidget(self.chk_logs)
        checks_layout.addWidget(self.chk_backups)
        checks_layout.addWidget(self.chk_sa_copy)
        layout.addWidget(checks_box)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        skip_btn = QPushButton("Skip Cleanup")
        skip_btn.clicked.connect(self._on_skip)
        btn_row.addWidget(skip_btn)

        clean_btn = QPushButton("Clean & Finish")
        clean_btn.setProperty("accent", True)
        clean_btn.clicked.connect(self._on_clean)
        btn_row.addWidget(clean_btn)

        layout.addLayout(btn_row)

    def _on_skip(self):
        self.done(QDialog.Rejected)

    def _on_clean(self):
        self.remove_downloads = self.chk_downloads.isChecked()
        self.remove_extracted = self.chk_extracted.isChecked()
        self.remove_sa_copy = self.chk_sa_copy.isChecked()
        self.clean_logs = self.chk_logs.isChecked()
        self.clean_backups = self.chk_backups.isChecked()
        self.done(QDialog.Accepted)

    def perform_cleanup(self):
        """Execute the selected cleanup actions. Call after dialog accepted."""
        removed = 0
        if self.remove_downloads:
            c = cleanup.cleanup_downloads_all()
            removed += c
            logger.info("Removed %d cached download(s)", c)
        if self.remove_extracted:
            c = cleanup.cleanup_extracted_all()
            removed += c
            logger.info("Removed %d extracted mod cache(s)", c)
        if self.clean_logs:
            c = cleanup.cleanup_all_logs()
            removed += c
            logger.info("Removed %d old log(s)", c)
        if self.clean_backups:
            c = cleanup.cleanup_old_backups(keep=0)
            removed += c
            logger.info("Removed %d old backup(s)", c)
        logger.info("Cleanup complete: %d items removed", removed)
        return removed


def show_cleanup_dialog(parent=None, has_local_mods: bool = False, sa_copy_path: str = "") -> int:
    """Show the cleanup dialog and perform cleanup if accepted. Returns items removed."""
    dlg = CleanupDialog(has_local_mods=has_local_mods, sa_copy_path=sa_copy_path, parent=parent)
    result = dlg.exec()
    if result == QDialog.Accepted:
        return dlg.perform_cleanup()
    return 0

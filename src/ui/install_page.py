"""Install page — runs all stages on a worker thread, shows live log + progress.

Stages (in order):
    1. copy_sa         — clone source SA folder into dest
    2. backup          — back up the freshly-prepared dest folder
    3. install_mods    — download/extract/merge each selected mod
"""
from __future__ import annotations

import logging
import os
import threading
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPlainTextEdit, QProgressBar, QPushButton,
    QVBoxLayout, QWizardPage,
)

from .. import cache, config, installer_stages, i18n
from ..installer_stages import InstallContext


class _Signals(QObject):
    log = Signal(str, str)               # (level, message)
    progress = Signal(str, str, int)     # (stage_id, message, percent)
    finished = Signal(bool)


class InstallPage(QWizardPage):
    splash_image_name = "install.png"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("")
        self._started = False
        self._ok = False

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(40, 30, 40, 30)

        # Title
        self._title = QLabel(i18n.t("install_title"))
        self._title.setProperty("subheading", True)
        layout.addWidget(self._title)

        self.stage_label = QLabel("Starting...")
        self.stage_label.setStyleSheet("color: #ffb84d; font-weight: bold;")
        layout.addWidget(self.stage_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        layout.addWidget(self.log, 1)

        btn_row = QHBoxLayout()
        self.save_log_btn = QPushButton("Save log...")
        self.save_log_btn.clicked.connect(self._save_log)
        btn_row.addWidget(self.save_log_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    def initializePage(self):
        if self._started:
            return
        self._started = True
        self.wizard().setButtonLayout([])  # hide nav buttons during install

        cache.ensure_dirs()

        def _str(v):
            if hasattr(v, "toString"):
                return v.toString()
            return str(v) if v else ""

        source_sa_root = _str(self.wizard().property("source_sa_root")).strip()
        dest_sa_root = _str(self.wizard().property("dest_sa_root")).strip()
        archives_folder = _str(self.wizard().property("archives_folder")).strip() or None
        have_local_mods = bool(self.wizard().property("have_local_mods"))
        skip_backup = self.wizard().property("skip_backup") or False
        backup_wanted = self.wizard().property("backup_wanted")
        if backup_wanted is not None and not backup_wanted:
            skip_backup = True
        enabled_mod_ids = self.wizard().property("enabled_mod_ids") or []
        mod_sources = self.wizard().property("mod_sources") or list(config.ALL_MODS)

        ctx = InstallContext(
            source_sa_root=source_sa_root,
            dest_sa_root=dest_sa_root,
            have_local_mods=have_local_mods,
            archives_folder=archives_folder,
            downloads_folder=_str(self.wizard().property("downloads_folder")).strip() or None,
            skip_backup=bool(skip_backup),
            enabled_mod_ids=list(enabled_mod_ids),
            mod_sources=list(mod_sources),
        )

        self._signals = _Signals()
        self._signals.log.connect(self._on_log)
        self._signals.progress.connect(self._on_progress)
        self._signals.finished.connect(self._on_finished)

        self._thread = threading.Thread(target=self._run, args=(ctx,), daemon=True)
        self._thread.start()

    def _run(self, ctx: InstallContext):
        import logging
        sig = self._signals
        _last_log_pct = [-1]
        _last_log_time = [0.0]

        def progress_cb(stage_id, msg, pct):
            sig.progress.emit(stage_id, msg, pct)
            now = datetime.now().timestamp()
            # Throttle log: emit if pct jumped >=5 or >=2s elapsed
            pct_jump = abs(pct - _last_log_pct[0]) >= 5
            time_elapsed = (now - _last_log_time[0]) >= 2.0
            if pct_jump or time_elapsed or pct >= 100:
                _last_log_pct[0] = pct
                _last_log_time[0] = now
                ts = datetime.now().strftime("%H:%M:%S")
                sig.log.emit("INFO", f"[{ts}] {stage_id}: {msg} ({pct}%)")
                logging.info("[%s] %s: %s (%d%%)", ts, stage_id, msg, pct)

        try:
            sig.log.emit("INFO", "=== Install started ===")
            logging.info("=== Install started ===")
            logging.info("Source SA: %s", ctx.source_sa_root)
            logging.info("Destination: %s", ctx.dest_sa_root)
            logging.info("Have local mods: %s", ctx.have_local_mods)
            logging.info("Archives folder: %s", ctx.archives_folder or "(none)")
            logging.info("Downloads folder: %s", ctx.downloads_folder or "(none)")
            logging.info("Mods selected: %s", ctx.enabled_mod_ids)
            logging.info("Mod sources count: %d", len(ctx.mod_sources))
            ok = installer_stages.run_full_install(ctx, progress_cb)
            sig.log.emit(
                "INFO" if ok else "ERROR",
                f"=== Install finished. OK={ok} "
                f"installed={ctx.installed_mods} failed={ctx.failed_mods} ==="
            )
            logging.info("=== Install finished. OK=%s installed=%s failed=%s ===",
                         ok, ctx.installed_mods, ctx.failed_mods)
            sig.finished.emit(ok)
        except Exception as e:
            sig.log.emit("ERROR", f"Unhandled exception: {e}")
            sig.finished.emit(False)

    # ------------------------------------------------------------------
    def _on_log(self, level: str, msg: str):
        color = {
            "INFO": "#ffb84d",
            "WARNING": "#ffe600",
            "ERROR": "#ff5b5b",
        }.get(level, "#ffffff")
        self.log.appendHtml(f"<span style='color:{color};'>[{level}] {msg}</span>")

    def _on_progress(self, stage_id: str, msg: str, pct: int):
        self.stage_label.setText(f"<b>{stage_id}</b> — {msg}")
        self.progress.setValue(max(0, min(100, pct)))

    def _on_finished(self, ok: bool):
        self._ok = ok
        # Auto-save log to cache
        try:
            log_path = os.path.join(cache.CACHE_LOGS,
                                    f"install_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(self.log.toPlainText())
        except Exception:
            pass

        from PySide6.QtWidgets import QWizard
        self.wizard().setButtonLayout([
            QWizard.BackButton, QWizard.NextButton, QWizard.FinishButton,
            QWizard.CancelButton,
        ])
        if ok:
            self.stage_label.setText(
                "<span style='color:#5bff8a;font-weight:bold;'>INSTALL COMPLETE!</span>"
            )
            self.progress.setValue(100)
            # Show cleanup dialog
            self._show_cleanup_dialog()
            self.wizard().next()
        else:
            self.stage_label.setText(
                "<span style='color:#ff5b5b;font-weight:bold;'>INSTALL FAILED — see log.</span>"
            )
            # Do NOT advance wizard on failure

    def _show_cleanup_dialog(self):
        """Offer to clean up installer artifacts after a successful install."""
        try:
            from .cleanup_dialog import show_cleanup_dialog
            sa_copy_path = ""
            if not self.wizard().property("have_local_mods"):
                sa_copy_path = str(self.wizard().property("source_sa_root") or "")
            show_cleanup_dialog(
                parent=self,
                has_local_mods=bool(self.wizard().property("have_local_mods")),
                sa_copy_path=sa_copy_path,
            )
        except Exception as e:
            logging.warning("Cleanup dialog failed (non-fatal): %s", e)

    # ------------------------------------------------------------------
    def isComplete(self):
        return self._ok

    def nextId(self):
        from .wizard import PAGE_COMPLETE
        return PAGE_COMPLETE

    def _save_log(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "Save install log",
            os.path.join(cache.CACHE_LOGS,
                         f"install_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            "Log files (*.log *.txt);;All files (*)",
            options=QFileDialog.DontUseNativeDialog,
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log.toPlainText())

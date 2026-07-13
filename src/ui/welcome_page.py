"""Welcome page — title, mod description, start button."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWizardPage

from .. import config, i18n
from .theme import heading_font, body_font


class WelcomePage(QWizardPage):
    splash_image_name = "welcome.png"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("")

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(40, 30, 40, 30)

        title = QLabel("GTA SAN ANDREAS\nSTORIES  1987")
        title.setProperty("heading", True)
        title.setFont(heading_font(38))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ff6a2b;")
        layout.addWidget(title)

        subtitle = QLabel("// " + i18n.t("welcome_subheading") + "  v" + config.APP_VERSION)
        subtitle.setProperty("subheading", True)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #3d8a3d; letter-spacing: 4px;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        body = QLabel(
            "<div style='line-height:160%;'>"
            + i18n.t("welcome_description").replace("\n", "<br>")
            + "</div>"
        )
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignLeft)
        body.setFont(body_font(10))
        layout.addWidget(body)

        # Backup option
        layout.addSpacing(10)
        self.backup_cb = QCheckBox(i18n.t("welcome_backup"))
        self.backup_cb.setChecked(False)
        self.backup_cb.setStyleSheet(
            "QCheckBox { color: #c0c0c0; font-size: 10pt; spacing: 8px; }"
            "QCheckBox::indicator { width: 18px; height: 18px; }"
        )
        layout.addWidget(self.backup_cb)

        backup_hint = QLabel(
            "<span style='color:#7a6a9b; font-size:9pt;'>"
            + i18n.t("welcome_backup_desc")
            + "</span>"
        )
        backup_hint.setWordWrap(True)
        backup_hint.setTextFormat(Qt.RichText)
        layout.addWidget(backup_hint)

        layout.addStretch()

        footer = QLabel(
            "Fan-made installer. Not affiliated with Rockstar Games or Take-Two. "
            "You must own a legal copy of GTA San Andreas."
        )
        footer.setProperty("dim", True)
        footer.setWordWrap(True)
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

    def initializePage(self):
        # Store backup preference on the wizard
        self.wizard().setProperty("backup_wanted", self.backup_cb.isChecked())
        # Connect checkbox changes to update the property
        self.backup_cb.toggled.connect(
            lambda checked: self.wizard().setProperty("backup_wanted", checked)
        )

    def nextId(self):
        from .wizard import PAGE_MOD_SOURCE
        return PAGE_MOD_SOURCE

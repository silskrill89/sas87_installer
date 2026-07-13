"""Language selection page — first page of the wizard."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWizardPage,
)

from .. import i18n


class LanguagePage(QWizardPage):
    splash_image_name = "welcome.png"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(60, 40, 60, 40)

        # Title
        title = QLabel("SELECT LANGUAGE")
        title.setProperty("heading", True)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "Choose your preferred language for the installer.\n\n"
            "<span style='color:#999999;'>Note: The mod itself is only available in English. "
            "This changes the installer interface language only.</span>"
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setTextFormat(Qt.RichText)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(20)

        # Language selector
        lang_row = QHBoxLayout()
        lang_row.addStretch()

        lang_label = QLabel("Language:")
        lang_label.setStyleSheet("font-size: 12pt;")
        lang_row.addWidget(lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.setMinimumWidth(250)
        self.lang_combo.setStyleSheet(
            "QComboBox { font-size: 12pt; padding: 8px 16px; }"
        )
        # Add languages
        for code, name in i18n.get_available_languages().items():
            self.lang_combo.addItem(name, code)
        lang_row.addWidget(self.lang_combo)
        lang_row.addStretch()

        layout.addLayout(lang_row)

        layout.addSpacing(30)

        # Continue button
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setProperty("primary", True)
        self.continue_btn.setMinimumWidth(200)
        self.continue_btn.setStyleSheet(
            "QPushButton { font-size: 12pt; padding: 10px 30px; }"
        )
        self.continue_btn.clicked.connect(self._on_continue)
        btn_row.addWidget(self.continue_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()

    def _on_continue(self):
        """Set language and proceed."""
        lang_code = self.lang_combo.currentData()
        if lang_code:
            i18n.set_language(lang_code)
        self.wizard().next()

    def nextId(self):
        from .wizard import PAGE_MOD_SOURCE
        return PAGE_MOD_SOURCE

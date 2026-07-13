"""Scrolling credits window + Support Creators popup for the GTA SAS 1987 Installer.

Scrolling credits: name on left, link on right — condensed, one row per person.
Support Creators: only opens via the bottom button, shows Patreon/donation cards.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)


def _open_url(url: str):
    from PySide6.QtCore import QUrl
    QDesktopServices.openUrl(QUrl(url))


# ─── Credits data ───────────────────────────────────────────────────────────
# Each row: (name, role, url_or_None, link_label_or_None)
# link_label: "Patreon" / "Website" / "GitHub" / "Forum" etc.

_CREDITS_PROJECT = [
    ("cerdopalo", "Project Creator & Lead", "https://gtasas.netlify.app/", "Website"),
]

_CREDITS_TEAM = [
    ("Rule Breakers", "Mappings and models", None, None),
    ("Cheseg Remastered", "Missions and feedback", None, None),
    ("Karammii", "Testing and billboards", None, None),
    ("Abdullah", "Missions, models, scripts, testing", None, None),
    ("Armin Love", "Testing", None, None),
    ("NorthStationX", "Billboards and retextures", None, None),
    ("Nightlaw", "Screenshots, testing, trailer clips", None, None),
    ("Noobshakespeare", "Testing and retextures", None, None),
    ("Tix", "Mission testing and screenshots", None, None),
    ("Yasa", "Feedback", None, None),
    ("Elrico", "Testing, feedback, screenshots", None, None),
    ("FrankoU", "Manual writing and mappings", None, None),
    ("Cerdquad", "Animations", None, None),
    ("Mike", "Missions and feedback", None, None),
    ("bolszewik", "Testing and screenshots", None, None),
    ("GTAMissionsCreator", "Video recording and testing", None, None),
    ("14todoeltiempodc", "Retextures", None, None),
]

_CREDITS_DYOM = [
    ("Dutchy3010", "DYOM co-creator", "https://dyom.gtagames.nl/", "Forum"),
    ("PatrickW", "DYOM co-creator", "https://dyom.gtagames.nl/", "Forum"),
    ("AnDReJ98", "DYOM site admin", "https://dyom.gtagames.nl/", "Forum"),
    ("MiranDMC", "DYOM Editor Tool", "https://dyom.gtagames.nl/", "Forum"),
]

_CREDITS_CLEO = [
    ("Seemann", "CLEO Library creator", "https://patreon.com/seemann", "Patreon"),
    ("Alien", "CLEO for GTA SA", None, None),
    ("Deji", "CLEO for GTA SA", None, None),
    ("LINK/2012", "ModLoader", None, None),
    ("ThirteenAG", "CLEO for GTA III/VC", None, None),
    ("squ1dd13", "CLEO iOS", None, None),
]

_CREDITS_CLEO_PLUS = [
    ("Junior_Djjr", "CLEO+ creator, MixMods founder", "https://www.patreon.com/c/djjr", "Patreon"),
]

_CREDITS_NEWOPCODES = [
    ("DK22Pac", "NewOpcodes, plugin-sdk", "https://github.com/DK22Pac", "GitHub"),
    ("BoPoH", "NewOpcodes contributor", None, None),
    ("Den_spb", "NewOpcodes contributor", None, None),
    ("fastman92", "Limit Adjuster", None, None),
    ("Wesser", "NewOpcodes contributor", None, None),
]

_CREDITS_MIXMODS = [
    ("Junior_Djjr", "MixMods founder, 500+ mods", "https://www.mixmods.com.br/", "Website"),
    ("aap", "SkyGfx creator", None, None),
    ("Silent", "SilentPatch, ASI Loader", None, None),
]

_CREDITS_TOOLS = [
    ("Sanny Builder", "CLEO script compiler", "https://www.patreon.com/posts/sanny-builder-4-109066935", "Patreon"),
    ("LibertyCity.net", "Mod hosting", "https://libertycity.net/", "Website"),
    ("MediaFire", "File hosting", "https://www.mediafire.com/", "Website"),
]

_CREDITS_THANKS = [
    ("Rockstar Games", "For creating GTA San Andreas", None, None),
    ("The GTA modding community", "For keeping this game alive", None, None),
    ("GTAForums.com", "Community hub", "https://gtaforums.com/", "Forum"),
    ("Discord communities", "Real-time collaboration", None, None),
    ("Everyone who plays this mod", "", None, None),
]

# Full credits: section header, then list
_CREDITS = [
    ("GTA SAN ANDREAS STORIES 1987", None),
    ("Fan-made total-conversion mod", None),
    ("_blank", None),
    ("PROJECT LEAD", _CREDITS_PROJECT),
    ("MOD TEAM", _CREDITS_TEAM),
    ("DYOM — DESIGN YOUR OWN MISSION", _CREDITS_DYOM),
    ("CLEO LIBRARY", _CREDITS_CLEO),
    ("CLEO+", _CREDITS_CLEO_PLUS),
    ("NEWOPCODES", _CREDITS_NEWOPCODES),
    ("MIXMODS", _CREDITS_MIXMODS),
    ("TOOLS & SITES", _CREDITS_TOOLS),
    ("SPECIAL THANKS", _CREDITS_THANKS),
]


# ─── Support Creators — only people with Patreon/donation links ─────────────

_SUPPORT_CREATORS = [
    {
        "name": "Seemann",
        "role": "CLEO Library creator",
        "support_url": "https://patreon.com/seemann",
        "support_label": "Patreon",
        "site_url": "https://cleo.li/",
        "description": "Created the CLEO Library — the script engine powering thousands of GTA mods.",
    },
    {
        "name": "Junior_Djjr",
        "role": "MixMods founder, CLEO+ creator",
        "support_url": "https://www.patreon.com/c/djjr",
        "support_label": "Patreon",
        "site_url": "https://www.mixmods.com.br/",
        "description": "500+ GTA mods, CLEO+, ModLoader ecosystem, the backbone of GTA modding.",
    },
    {
        "name": "Jéssica Natália",
        "role": "Proper Shaders collaborator",
        "support_url": "https://www.patreon.com/jessica_natalia",
        "support_label": "Patreon",
        "site_url": None,
        "description": "Contributed to Proper Shaders for MixMods.",
    },
    {
        "name": "Sanny Builder",
        "role": "CLEO script compiler",
        "support_url": "https://www.patreon.com/posts/sanny-builder-4-109066935",
        "support_label": "Patreon",
        "site_url": "https://sannybuilder.com/",
        "description": "The essential compiler for CLEO scripts — used by every CLEO modder.",
    },
]


# ─── Colors ──────────────────────────────────────────────────────────────────
_BG = "#0a0a0f"
_BG_DARK = "#12121a"
_BG_CARD = "#16161e"
_GOLD = "#f0c060"
_TEAL = "#00d4aa"
_PINK = "#ff2d7b"
_TEXT = "#e0d0c0"
_TEXT_DIM = "#9a8a7a"
_BORDER = "#2a2a3a"


# ─── Scrolling Credits Window ───────────────────────────────────────────────

class CreditsWindow(QDialog):
    """Movie-style scrolling credits — name left, link right, one row per person."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Credits — GTA SAS 1987 Installer")
        self.setMinimumSize(700, 600)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: {_BG}; }}")
        layout.addWidget(scroll, 1)

        # Content
        content = QWidget()
        content.setStyleSheet(f"background: {_BG};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(50, 30, 50, 20)
        cl.setSpacing(2)

        for section_name, people in _CREDITS:
            if section_name == "_blank":
                cl.addSpacing(20)
                continue

            if people is None:
                # Title card
                lbl = QLabel(section_name)
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet(f"color: {_PINK}; font-size: 20px; font-weight: bold; background: transparent;")
                lbl.setFont(QFont("PricedownBl", 18))
                cl.addWidget(lbl)
                continue

            # Section header
            hdr = QLabel(section_name)
            hdr.setStyleSheet(
                f"color: {_GOLD}; font-size: 14px; font-weight: bold; "
                f"letter-spacing: 3px; padding-top: 10px; background: transparent;"
            )
            cl.addWidget(hdr)

            # People rows: name left, role + link right
            for name, role, url, link_label in people:
                row = QHBoxLayout()
                row.setContentsMargins(0, 2, 0, 2)
                row.setSpacing(0)

                # Name (left)
                name_lbl = QLabel(name)
                name_lbl.setStyleSheet(
                    f"color: {_TEXT}; font-size: 14px; font-weight: bold; background: transparent;"
                )
                row.addWidget(name_lbl)

                # Role (middle, dimmed)
                if role:
                    role_lbl = QLabel(f"  — {role}")
                    role_lbl.setStyleSheet(f"color: {_TEXT_DIM}; font-size: 13px; background: transparent;")
                    row.addWidget(role_lbl)

                row.addStretch()

                # Link (right side)
                if url and link_label:
                    link_btn = QPushButton(link_label)
                    link_btn.setStyleSheet(
                        f"color: {_TEAL}; font-size: 13px; background: transparent; "
                        f"border: none; text-decoration: underline; padding: 0;"
                    )
                    link_btn.setCursor(Qt.PointingHandCursor)
                    link_btn.clicked.connect(lambda checked=False, u=url: _open_url(u))
                    row.addWidget(link_btn)

                cl.addLayout(row)

        cl.addStretch()
        scroll.setWidget(content)

        # Bottom bar
        bottom = QWidget()
        bottom.setStyleSheet(f"background: {_BG_DARK}; padding: 10px;")
        bl = QHBoxLayout(bottom)
        bl.setContentsMargins(30, 10, 30, 10)

        support_btn = QPushButton("♥  Support Creators")
        support_btn.setStyleSheet(
            f"QPushButton {{ color: {_PINK}; font-size: 13px; font-weight: bold; "
            f"background: {_BG_CARD}; border: 2px solid {_PINK}; border-radius: 6px; "
            f"padding: 8px 24px; }} "
            f"QPushButton:hover {{ background: {_PINK}; color: {_BG}; }}"
        )
        support_btn.setCursor(Qt.PointingHandCursor)
        support_btn.clicked.connect(self._open_support)
        bl.addWidget(support_btn)

        bl.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            f"QPushButton {{ color: {_TEXT_DIM}; font-size: 12px; background: {_BG_CARD}; "
            f"border: 1px solid {_BORDER}; border-radius: 6px; padding: 8px 20px; }} "
            f"QPushButton:hover {{ background: #2a2a3a; }}"
        )
        close_btn.clicked.connect(self.close)
        bl.addWidget(close_btn)

        layout.addWidget(bottom)

    def _open_support(self):
        SupportCreatorsWindow(self).exec()


# ─── Support Creators Popup ─────────────────────────────────────────────────

class SupportCreatorsWindow(QDialog):
    """Popup listing creators with Patreon/donation links. Only opens via button."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Support the Creators")
        self.setMinimumSize(700, 480)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet(f"background: {_BG_DARK}; padding: 20px;")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(30, 20, 30, 10)

        title = QLabel("SUPPORT THE CREATORS")
        title.setStyleSheet(f"color: {_PINK}; font-size: 18px; font-weight: bold;")
        title.setFont(QFont("PricedownBl", 16))
        hl.addWidget(title)

        subtitle = QLabel(
            "These creators have made their work freely available. "
            "If you enjoy this mod, consider supporting them directly."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {_TEXT_DIM}; font-size: 11px; padding-top: 6px;")
        hl.addWidget(subtitle)
        layout.addWidget(header)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: {_BG}; }}")
        layout.addWidget(scroll, 1)

        content = QWidget()
        content.setStyleSheet(f"background: {_BG};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(30, 16, 30, 16)
        cl.setSpacing(12)

        for c in _SUPPORT_CREATORS:
            card = QWidget()
            card.setStyleSheet(
                f"background: {_BG_CARD}; border: 1px solid {_BORDER}; "
                f"border-radius: 8px; padding: 12px;"
            )
            card_l = QVBoxLayout(card)
            card_l.setContentsMargins(16, 12, 16, 12)
            card_l.setSpacing(4)

            name = QLabel(c["name"])
            name.setStyleSheet(f"color: {_TEXT}; font-size: 14px; font-weight: bold; background: transparent;")
            card_l.addWidget(name)

            role = QLabel(c["role"])
            role.setStyleSheet(f"color: #7a6a9b; font-size: 11px; background: transparent;")
            card_l.addWidget(role)

            desc = QLabel(c["description"])
            desc.setWordWrap(True)
            desc.setStyleSheet(f"color: {_TEXT_DIM}; font-size: 11px; background: transparent;")
            card_l.addWidget(desc)

            btn_row = QHBoxLayout()

            p = QPushButton(f"♥  {c['support_label']}")
            p.setStyleSheet(
                f"QPushButton {{ color: {_PINK}; font-size: 12px; font-weight: bold; "
                f"background: {_BG_CARD}; border: 1px solid {_PINK}; border-radius: 5px; "
                f"padding: 6px 16px; }} "
                f"QPushButton:hover {{ background: {_PINK}; color: {_BG}; }}"
            )
            p.setCursor(Qt.PointingHandCursor)
            p.clicked.connect(lambda checked=False, u=c["support_url"]: _open_url(u))
            btn_row.addWidget(p)

            if c.get("site_url"):
                s = QPushButton("Website")
                s.setStyleSheet(
                    f"QPushButton {{ color: #5b9bd5; font-size: 11px; "
                    f"background: transparent; border: 1px solid #3a3a5a; border-radius: 5px; "
                    f"padding: 6px 14px; }} "
                    f"QPushButton:hover {{ background: {_BG_CARD}; }}"
                )
                s.setCursor(Qt.PointingHandCursor)
                s.clicked.connect(lambda checked=False, u=c["site_url"]: _open_url(u))
                btn_row.addWidget(s)

            btn_row.addStretch()
            card_l.addLayout(btn_row)
            cl.addWidget(card)

        cl.addStretch()
        scroll.setWidget(content)

        # Close
        bottom = QWidget()
        bottom.setStyleSheet(f"background: {_BG_DARK}; padding: 10px;")
        bl = QHBoxLayout(bottom)
        bl.setContentsMargins(30, 10, 30, 10)
        bl.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            f"QPushButton {{ color: {_TEXT_DIM}; font-size: 12px; background: {_BG_CARD}; "
            f"border: 1px solid {_BORDER}; border-radius: 6px; padding: 8px 20px; }} "
            f"QPushButton:hover {{ background: #2a2a3a; }}"
        )
        close_btn.clicked.connect(self.close)
        bl.addWidget(close_btn)
        layout.addWidget(bottom)


def open_credits(parent=None):
    """Convenience function to open the credits window."""
    CreditsWindow(parent).exec()

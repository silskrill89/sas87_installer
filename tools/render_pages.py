"""Render wizard pages to PNG images for README screenshots.

Usage:
    python tools/render_pages.py

Output: screenshots/ folder with page mockups
"""
import os
import sys

# Add project root to path
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QPainter

# Import pages
from src.ui.welcome_page import WelcomePage
from src.ui.mod_source_page import ModSourcePage
from src.ui.setup_page import SetupPage
from src.ui.prereqs_page import PrereqsPage
from src.ui.install_page import InstallPage
from src.ui.complete_page import CompletePage

OUTPUT_DIR = os.path.join(PROJECT, "screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Page configs: (page_class, filename, title)
PAGES = [
    (WelcomePage, "01_welcome.png", "Welcome"),
    (ModSourcePage, "02_mod_source.png", "Mod Source"),
    (SetupPage, "03_setup.png", "Setup"),
    (PrereqsPage, "04_prereqs.png", "Prerequisites"),
    (InstallPage, "05_install.png", "Installing"),
    (CompletePage, "06_complete.png", "Complete"),
]


def render_page(page_class, filename, title):
    """Render a single wizard page to PNG."""
    print(f"Rendering {title}...")

    # Create a container widget to hold the page
    from PySide6.QtWidgets import QWidget, QVBoxLayout

    container = QWidget()
    container.setWindowTitle(f"GTA SAS 1987 Installer - {title}")
    container.setMinimumSize(1040, 740)
    container.setStyleSheet("background: #0a0a0f;")

    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)

    # Create the page
    page = page_class(container)
    layout.addWidget(page)

    # Show to render
    container.show()
    app.processEvents()

    # Render to pixmap
    pixmap = container.grab()
    filepath = os.path.join(OUTPUT_DIR, filename)
    pixmap.save(filepath, "PNG")
    print(f"  Saved: {filepath}")

    container.close()
    return filepath


def main():
    print("=" * 60)
    print("  GTA SAS 1987 Installer — Page Renderer")
    print("=" * 60)
    print()

    # Create app
    global app
    app = QApplication(sys.argv)

    # Apply theme
    from src.ui.theme import apply_theme
    apply_theme(app)

    # Render pages
    rendered = []
    for page_class, filename, title in PAGES:
        try:
            path = render_page(page_class, filename, title)
            rendered.append(path)
        except Exception as e:
            print(f"  ERROR rendering {title}: {e}")

    print()
    print(f"Done! Rendered {len(rendered)} pages to {OUTPUT_DIR}")
    print()
    print("Files:")
    for f in rendered:
        print(f"  {os.path.basename(f)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""GTA San Andreas Stories 1987 — Installer Wizard.

Entry point. Run with:

    python installer.py

Build a standalone .exe with:

    build_portable.bat       (Windows)
    pyinstaller installer.spec

If anything crashes, the full traceback is written to:
    crash_<timestamp>.log   (next to this script)
    cache/logs/install_*.log  (the normal install log, if logging started)
    wizard_output.log       (captured by run.bat)

The faulthandler module is enabled to catch native segfaults (e.g. Qt6
DLL issues) that bypass sys.excepthook.
"""
from __future__ import annotations

import datetime
import faulthandler
import logging
import os
import sys
import traceback

# Enable faulthandler IMMEDIATELY — before any imports — so we catch
# native segfaults (e.g. Qt6 DLL crashes) that bypass sys.excepthook.
# This writes to stderr (which run.bat captures to wizard_output.log).
try:
    faulthandler.enable()
    # Also write faulthandler output to a file so we definitely have it
    _fault_log = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "crash_faulthandler.log",
    )
    faulthandler.dump_traceback_later(timeout=300, file=open(_fault_log, "w"))  # 5 min timeout
except Exception:
    pass

# Make sure the `src` package is importable when running from source.
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _crash_log_path() -> str:
    """Return the path to a fresh crash log file (next to this script)."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(HERE, f"crash_{ts}.log")


def _write_crash_log(exc_type, exc_value, exc_tb) -> str:
    """Write the full traceback to a crash log file. Returns the path."""
    log_path = _crash_log_path()
    try:
        os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("GTA SAS 1987 Installer — Crash Log\n")
            f.write("=" * 60 + "\n")
            f.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
            f.write(f"Python:    {sys.version}\n")
            f.write(f"Platform:  {sys.platform}\n")
            try:
                import platform
                f.write(f"OS:        {platform.platform()}\n")
            except Exception:
                pass
            f.write(f"Executable: {sys.executable}\n")
            f.write(f"CWD:       {os.getcwd()}\n")
            f.write(f"Script:    {os.path.abspath(__file__)}\n")
            f.write("=" * 60 + "\n\n")
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
            f.write("\n" + "=" * 60 + "\n")
            f.write("End of crash log. Share this file when reporting the bug.\n")
    except Exception:
        # If we can't even write the crash log, fall back to stderr
        traceback.print_exception(exc_type, exc_value, exc_tb, file=sys.stderr)
        return ""
    return log_path


def _show_crash_dialog(log_path: str, exc_value: Exception) -> None:
    """Try to show a GUI dialog telling the user where the crash log is.

    Falls back to a console message if no GUI toolkit is available.
    """
    msg = (
        f"The GTA SAS 1987 Installer crashed.\n\n"
        f"Error: {exc_value}\n\n"
        f"A full crash log has been written to:\n"
        f"{log_path}\n\n"
        f"Please share this file when reporting the bug."
    )
    # Try Qt first (if PySide6 is installed)
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "GTA SAS 1987 Installer — Crash", msg)
        return
    except Exception:
        pass
    # Try Tkinter as a fallback
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("GTA SAS 1987 Installer — Crash", msg)
        root.destroy()
        return
    except Exception:
        pass
    # Last resort: print to stderr
    print("\n" + "=" * 60, file=sys.stderr)
    print("CRASH: " + msg, file=sys.stderr)
    print("=" * 60 + "\n", file=sys.stderr)


def _setup_logging() -> str:
    """Set up logging to both stdout and a log file. Returns the log file path."""
    from src import cache, config

    cache.ensure_dirs()
    log_file = cache.log_path()
    fmt = "%(asctime)s %(levelname)-7s %(name)s — %(message)s"
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers, force=True)
    logging.info("=== %s v%s ===", config.APP_NAME, config.APP_VERSION)
    logging.info("Python: %s", sys.version)
    logging.info("Executable: %s", sys.executable)
    logging.info("CWD: %s", os.getcwd())
    logging.info("Script: %s", os.path.abspath(__file__))
    logging.info("Cache root: %s", config.CACHE_ROOT)
    return log_file


def _consolidate_cache():
    """Scan for cache dirs in common locations and move them next to the exe.

    If the user previously ran the installer from Downloads or Documents and
    left a cache/ folder there, move it to the current PROJECT_ROOT/cache/.
    """
    from src import config
    import shutil

    project_root = config.PROJECT_ROOT
    # Skip if cache is already in the right place
    if os.path.isdir(config.CACHE_ROOT):
        return

    # Common locations where cache might be orphaned
    search_dirs = []
    if config.IS_WINDOWS:
        for env_var in ("USERPROFILE", "HOMEDRIVE"):
            home = os.environ.get(env_var, "")
            if home:
                search_dirs.append(os.path.join(home, "Downloads"))
                search_dirs.append(os.path.join(home, "Documents"))
                search_dirs.append(os.path.join(home, "Desktop"))
    elif config.IS_LINUX or config.IS_MACOS:
        import pathlib
        home = pathlib.Path.home()
        search_dirs.extend([
            home / "Downloads",
            home / "Documents",
            home / "Desktop",
        ])

    for search_dir in search_dirs:
        candidate = os.path.join(search_dir, "cache")
        if os.path.isdir(candidate) and os.path.isdir(os.path.join(candidate, "logs")):
            # Found an orphaned cache — move it
            try:
                os.makedirs(project_root, exist_ok=True)
                dest = os.path.join(project_root, "cache")
                shutil.move(candidate, dest)
                logging.info("Consolidated cache from %s to %s", candidate, dest)
                return
            except OSError as e:
                logging.debug("Failed to consolidate cache from %s: %s", candidate, e)


def main() -> int:
    """Main entry point. Wraps everything in a crash handler."""
    # Set up logging early so we capture import errors
    try:
        log_file = _setup_logging()
    except Exception as e:
        # If logging setup fails, we still want to run — just print to stderr
        print(f"[WARNING] Logging setup failed: {e}", file=sys.stderr)
        log_file = None

    # Log PySide6 diagnostic info BEFORE importing it — so if the import
    # crashes (native segfault), we at least know what was about to happen.
    logging.info("Attempting to import PySide6...")
    try:
        import PySide6
        logging.info("PySide6 module found at: %s", getattr(PySide6, "__file__", "(unknown)"))
        from PySide6 import QtCore
        logging.info("PySide6.QtCore version: %s", QtCore.__version__)
    except Exception as e:
        logging.error("PySide6 import failed: %s", e)
        msg = (
            "PySide6 failed to import.\n\n"
            f"Error: {e}\n\n"
            "Try reinstalling PySide6:\n"
            "    pip install --upgrade --force-reinstall PySide6\n\n"
            "If that fails, you may need to install the Visual C++ Redistributable:\n"
            "    https://aka.ms/vs/17/release/vc_redist.x64.exe"
        )
        print("ERROR: " + msg, file=sys.stderr)
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("GTA SAS 1987 Installer — PySide6 Error", msg)
            root.destroy()
        except Exception:
            pass
        return 2

    # Now import QApplication (we already know QtCore works)
    try:
        from PySide6.QtWidgets import QApplication
    except Exception as e:
        logging.error("PySide6.QtWidgets import failed: %s", e)
        _show_crash_dialog("", e)
        return 2

    from src.ui.theme import apply_theme
    from src.ui.wizard import InstallerWizard

    # Run startup cleanup — prune old logs, backups, crash logs, orphaned _MEI* dirs
    try:
        from src import cleanup
        cleanup_summary = cleanup.run_all()
        if any(v > 0 for v in cleanup_summary.values()):
            logging.info("Startup cleanup: %s", cleanup_summary)
    except Exception as e:
        logging.warning("Startup cleanup failed (non-fatal): %s", e)

    # Consolidate cache from other locations (e.g. Downloads, Documents)
    try:
        _consolidate_cache()
    except Exception as e:
        logging.warning("Cache consolidation failed (non-fatal): %s", e)

    # Download mod screenshots in background (non-blocking, non-fatal)
    try:
        from src import screenshot_cache
        logging.info("Ensuring screenshot cache...")
        screenshot_cache.ensure_screenshots()
    except Exception as e:
        logging.warning("Screenshot cache setup failed (non-fatal): %s", e)

    logging.info("Creating QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("GTA SAS 1987 Installer")
    from src import config
    app.setApplicationVersion(config.APP_VERSION)
    logging.info("Applying theme...")
    apply_theme(app)
    logging.info("Creating wizard...")
    wizard = InstallerWizard()
    logging.info("Showing wizard...")
    wizard.show()
    logging.info("Entering Qt event loop...")
    return app.exec()


def main_with_crash_handler() -> int:
    """Wrap main() in a sys.excepthook that writes a crash log + shows a dialog."""
    def _excepthook(exc_type, exc_value, exc_tb):
        # Don't catch KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        log_path = _write_crash_log(exc_type, exc_value, exc_tb)
        _show_crash_dialog(log_path, exc_value)
        # Also call the default hook so it prints to stderr too
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook
    try:
        return main()
    except SystemExit:
        raise
    except BaseException as e:
        # Catch anything that escapes main() before Qt's event loop starts
        log_path = _write_crash_log(type(e), e, e.__traceback__)
        _show_crash_dialog(log_path, e)
        traceback.print_exception(type(e), e, e.__traceback__)
        return 1


if __name__ == "__main__":
    sys.exit(main_with_crash_handler())

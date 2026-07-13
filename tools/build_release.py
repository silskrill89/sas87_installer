"""Build + versioned 7z release packager.

Usage:
    py build_release.py              # auto-increment patch (v1.1 -> v1.2)
    py build_release.py --minor      # increment minor (v1.1 -> v2.0)
    py build_release.py --set 1.5    # explicit version

Archives are saved to E:\\games\\GTA_SAS_87_LATEST\\ as:
    GTA_SAS_1987_Installer_vX.Y.7z

NEVER deletes old archives — only creates new ones.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import time

PROJECT = os.path.dirname(os.path.abspath(__file__))
RELEASE_DIR = r"E:\games\GTA_SAS_87_LATEST"
ARCHIVE_PREFIX = "GTA_SAS_1987_Installer_v"
SEVENZIP = r"C:\Program Files\7-Zip\7z.exe"


def latest_version():
    """Parse existing archives, return (major, minor) of latest."""
    pattern = os.path.join(RELEASE_DIR, f"{ARCHIVE_PREFIX}*.7z")
    best = (0, 0)
    for path in glob.glob(pattern):
        name = os.path.basename(path)
        ver_str = name.replace(ARCHIVE_PREFIX, "").replace(".7z", "")
        parts = ver_str.split(".")
        if len(parts) == 2:
            try:
                major, minor = int(parts[0]), int(parts[1])
                if (major, minor) > best:
                    best = (major, minor)
            except ValueError:
                pass
    return best


def increment_version(mode, explicit=None):
    """Return next version string."""
    if explicit:
        return explicit
    major, minor = latest_version()
    if mode == "minor":
        return f"{major + 1}.0"
    return f"{major}.{minor + 1}"


def stage_files(stage_dir):
    """Copy exe + source into staging directory."""
    if os.path.isdir(stage_dir):
        shutil.rmtree(stage_dir)
    os.makedirs(stage_dir, exist_ok=True)

    # Exe
    exe_src = os.path.join(PROJECT, "dist", "GTA_SAS_1987_Installer.exe")
    if not os.path.isfile(exe_src):
        print("ERROR: exe not found at", exe_src)
        sys.exit(1)
    shutil.copy2(exe_src, os.path.join(stage_dir, "GTA_SAS_1987_Installer.exe"))
    exe_mb = os.path.getsize(exe_src) / 1024 / 1024

    # Source code (no __pycache__, .pyc, splash PNGs — bundled in exe)
    src_dst = os.path.join(stage_dir, "src")
    shutil.copytree(
        os.path.join(PROJECT, "src"), src_dst,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "splash"),
    )

    # Key files
    for f in ["installer.py", "installer.spec", "requirements.txt",
              "CREDITS.md", "build_portable.bat", "diagnose.bat"]:
        src_f = os.path.join(PROJECT, f)
        if os.path.isfile(src_f):
            shutil.copy2(src_f, os.path.join(stage_dir, f))

    total = sum(
        os.path.getsize(os.path.join(r, f))
        for r, _, files in os.walk(stage_dir) for f in files
    )
    print(f"  Exe: {exe_mb:.1f} MB | Staged: {total / 1024 / 1024:.1f} MB")
    return total


def compress_7z(stage_dir, archive_path):
    """Compress with maximum 7z settings (128 MB dict, LZMA2 ultra)."""
    cmd = [
        SEVENZIP, "a", "-t7z",
        "-mx=9",          # Ultra
        "-md=128m",       # 128 MB dictionary
        "-mfb=273",       # 273 fast bytes
        "-ms=on",         # Solid archive
        "-mmt=on",        # Multi-threaded
        "-m0=LZMA2",
        archive_path,
        stage_dir + "\\*",
    ]
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"  7z FAILED:\n{result.stderr}")
        sys.exit(1)

    sz = os.path.getsize(archive_path)
    return sz, elapsed


def main():
    parser = argparse.ArgumentParser(description="Build versioned release archive")
    parser.add_argument("--minor", action="store_true", help="Bump major version")
    parser.add_argument("--set", type=str, help="Set explicit version (e.g. 1.5)")
    args = parser.parse_args()

    ver = increment_version("minor" if args.minor else "patch", args.set)
    archive_name = f"{ARCHIVE_PREFIX}{ver}.7z"
    archive_path = os.path.join(RELEASE_DIR, archive_name)

    if os.path.isfile(archive_path):
        print(f"WARNING: {archive_name} already exists ({os.path.getsize(archive_path)/1024/1024:.1f} MB)")
        print("Incrementing patch version...")
        major, minor = [int(x) for x in ver.split(".")]
        ver = f"{major}.{minor + 1}"
        archive_name = f"{ARCHIVE_PREFIX}{ver}.7z"
        archive_path = os.path.join(RELEASE_DIR, archive_name)

    print(f"\n{'='*60}")
    print(f"  GTA SAS 1987 Installer — Release Build")
    print(f"  Version: {ver}")
    print(f"  Output:  {archive_name}")
    print(f"{'='*60}\n")

    stage_dir = os.path.join(PROJECT, "build", "_stage")
    print("[1/3] Staging files...")
    stage_files(stage_dir)

    print(f"\n[2/3] Compressing with 7z (LZMA2 ultra, 128 MB dict)...")
    sz, elapsed = compress_7z(stage_dir, archive_path)

    print(f"\n[3/3] Done!")
    print(f"  Archive:  {archive_name}")
    print(f"  Size:     {sz / 1024 / 1024:.1f} MB")
    print(f"  Time:     {elapsed:.0f}s")
    if sz < 50 * 1024 * 1024:
        print(f"  Status:   UNDER 50 MB TARGET")
    else:
        print(f"  Status:   {(sz - 50*1024*1024)/1024/1024:.1f} MB over 50 MB")

    # List all archives
    print(f"\nAll release archives in {RELEASE_DIR}:")
    for f in sorted(glob.glob(os.path.join(RELEASE_DIR, f"{ARCHIVE_PREFIX}*.7z"))):
        sz_i = os.path.getsize(f)
        print(f"  {os.path.basename(f):50s} {sz_i/1024/1024:.1f} MB")

    # Cleanup staging
    shutil.rmtree(stage_dir, ignore_errors=True)
    print("\nStaging cleaned up.")


if __name__ == "__main__":
    main()

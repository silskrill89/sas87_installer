# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the GTA SAS 1987 Installer — MAXIMUM LEAN build.

Only bundles the 3 core Qt6 DLLs (Core, Gui, Widgets) and the minimal
PySide6 .pyd modules. Drops ALL unused Qt modules, PIL/Pillow, and
other third-party bloat.

Build with:
    pyinstaller installer.spec
"""
import os

block_cipher = None

# --- Data files to bundle ---
datas = [
    ('data', 'data'),
    ('fonts', 'fonts'),
    ('src/ui/splash', 'src/ui/splash'),
    ('src/ui/splash_layers', 'src/ui/splash_layers'),
    ('CREDITS.md', '.'),
    ('CHANGELOG.md', '.'),
]

# --- Python hidden imports (only what we actually use at runtime) ---
hiddenimports = [
    # Core third-party
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'bs4',
    'soupsieve',
    'py7zr',
    'rarfile',
    'psutil',
    # py7zr transitive deps (dynamically imported)
    'brotli',
    'inflate64',
    'pyppmd',
    'texttable',
    'py7zr.compressor',
    'py7zr.archiveinfo',
    'py7zr.callbacks',
    'py7zr.exceptions',
    'py7zr.helpers',
    'py7zr.io',
    'py7zr.member',
    'py7zr.properties',
    'py7zr.py7zr',
    'py7zr.win32compat',
    # PySide6 core only
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtSvg',
    'PySide6.QtSvgWidgets',
    # Shiboken (required by PySide6)
    'shiboken6',
]

# --- Minimal Qt6 DLLs and PySide6 .pyd modules ---
binaries = []

try:
    import PySide6
    _pyside6_dir = os.path.dirname(PySide6.__file__)
except ImportError:
    _pyside6_dir = None

if _pyside6_dir:
    # ONLY the 3 core Qt6 DLLs we actually import (~25 MB vs 318 MB for all)
    _QT_DLLS = [
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
    ]
    for _dll in _QT_DLLS:
        _src = os.path.join(_pyside6_dir, _dll)
        if os.path.isfile(_src):
            binaries.append((_src, '.'))

    # Shiboken6 runtime DLLs (tiny, required)
    for _f in os.listdir(_pyside6_dir):
        if _f.startswith('shiboken6') and _f.endswith('.dll'):
            binaries.append((os.path.join(_pyside6_dir, _f), '.'))

    # PySide6 .pyd modules — ONLY QtCore, QtGui, QtWidgets + __init__
    _KEEP_PREFIXES = ('QtCore', 'QtGui', 'QtWidgets', '__init__')
    for _f in os.listdir(_pyside6_dir):
        if _f.endswith('.pyd') and any(_f.startswith(p) for p in _KEEP_PREFIXES):
            binaries.append((os.path.join(_pyside6_dir, _f), '.'))

    # Qt6 platform plugin — REQUIRED for Qt to create windows
    _plat_dir = os.path.join(_pyside6_dir, 'plugins', 'platforms')
    if os.path.isdir(_plat_dir):
        for _f in os.listdir(_plat_dir):
            # Only qwindows.dll is needed — skip everything else
            if _f.lower() == 'qwindows.dll':
                binaries.append((os.path.join(_plat_dir, _f), 'platforms'))

    # Style plugin — skip entirely (saves ~225KB, not critical)
    # _style_dir = os.path.join(_pyside6_dir, 'plugins', 'styles')
    # if os.path.isdir(_style_dir):
    #     for _f in os.listdir(_style_dir):
    #         if _f.endswith('.dll'):
    #             binaries.append((os.path.join(_style_dir, _f), 'styles'))

    # Image format plugins — ONLY jpeg and ico (saves ~2MB of unused formats)
    _img_dir = os.path.join(_pyside6_dir, 'plugins', 'imageformats')
    if os.path.isdir(_img_dir):
        for _f in os.listdir(_img_dir):
            if _f.endswith('.dll') and any(_f.lower().startswith(p) for p in ('qjpeg', 'qico')):
                binaries.append((os.path.join(_img_dir, _f), 'imageformats'))

# --- Analysis ---
a = Analysis(
    ['installer.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # === Qt modules we DON'T use (saves ~290 MB of DLLs) ===
        'PySide6.Qt3DAnimation', 'PySide6.Qt3DCore', 'PySide6.Qt3DExtras',
        'PySide6.Qt3DInput', 'PySide6.Qt3DLogic', 'PySide6.Qt3DRender',
        'PySide6.QtAsyncio', 'PySide6.QtAxContainer', 'PySide6.QtBluetooth',
        'PySide6.QtCharts', 'PySide6.QtConcurrent', 'PySide6.QtDataVisualization',
        'PySide6.QtDesigner', 'PySide6.QtGraphs', 'PySide6.QtGraphsWidgets',
        'PySide6.QtHelp', 'PySide6.QtHttpServer', 'PySide6.QtLocation',
        'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
        'PySide6.QtNfc', 'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets',
        'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
        'PySide6.QtPositioning', 'PySide6.QtPrintSupport',
        'PySide6.QtRemoteObjects', 'PySide6.QtScxml', 'PySide6.QtSensors',
        'PySide6.QtSerialBus', 'PySide6.QtSerialPort',
        'PySide6.QtSpatialAudio', 'PySide6.QtSql',
        'PySide6.QtStateMachine', 'PySide6.QtSvg', 'PySide6.QtSvgWidgets',
        'PySide6.QtTest', 'PySide6.QtTextToSpeech',
        'PySide6.QtUiTools', 'PySide6.QtWebChannel',
        'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineQuick',
        'PySide6.QtWebEngineWidgets', 'PySide6.QtWebSockets',
        'PySide6.QtWebView', 'PySide6.QtQuick',
        'PySide6.QtQuick3D', 'PySide6.QtQuickControls2',
        'PySide6.QtQuickTest', 'PySide6.QtQuickWidgets',
        'PySide6.QtDBus', 'PySide6.QtNetwork',
        'PySide6.QtQml',
        # === PIL / Pillow — save raw images instead (~14 MB savings) ===
        'PIL',
        'PIL.Image',
        'PIL.JpegImagePlugin',
        'PIL.PngImagePlugin',
        # === Bloat we don't need ===
        'tkinter', 'matplotlib', 'numpy', 'pandas',
        'IPython', 'notebook', 'jupyter',
        'unittest', 'test', 'doctest',
        'pydoc', 'pdb', 'profile', 'cProfile',
        'xmlrpc', 'wsgiref',
        'py_compile', 'compileall',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GTA_SAS_1987_Installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=['qwindows.dll', 'qjpeg.dll', 'qico.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch='x86_64',
    codesign_identity=None,
    entitlements_file=None,
    icon='src/resources/icon.ico' if os.path.exists('src/resources/icon.ico') else None,
)

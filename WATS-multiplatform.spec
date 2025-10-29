# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os
import sys

# Detecta a plataforma
is_windows = sys.platform.startswith('win')
is_linux = sys.platform.startswith('linux')

# Dados comuns para todas as plataformas
datas = [
    ('assets', 'assets'),
    ('config/config.json', '.'),
    ('config/.env', '.'),
    ('wats_settings.json', '.')
]

binaries = []

# Importações específicas por plataforma
if is_windows:
    hiddenimports = ['win32api', 'win32con', 'win32gui', 'win32process', 'dotenv', 'mss', 'psutil']
    # Inclui apenas rdp.exe no Windows
    datas.append(('assets/rdp.exe', 'assets'))
else:
    # Linux - sem dependências do Windows e sem rdp.exe
    hiddenimports = ['dotenv', 'mss', 'psutil']
    # Não inclui rdp.exe (não funciona em Linux)

# CustomTkinter com inclusão específica de recursos
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Inclui especificamente os assets do CustomTkinter
import customtkinter
ctk_path = os.path.dirname(customtkinter.__file__)
assets_path = os.path.join(ctk_path, 'assets')
if os.path.exists(assets_path):
    datas.append((assets_path, 'customtkinter/assets'))

# Outras dependências comuns
for module in ['pyodbc', 'cv2', 'wats_app', 'dotenv', 'mss', 'psutil']:
    try:
        tmp_ret = collect_all(module)
        datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    except Exception:
        pass  # Módulo não encontrado, ignorar

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# Configurações específicas por plataforma
if is_windows:
    # Windows - executable com ícone
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='WATS',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=['assets/ats.ico'],
    )
else:
    # Linux - executable sem ícone específico
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='wats',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WATS' if is_windows else 'wats',
)
# -*- mode: python ; coding: utf-8 -*-# -*- mode: python ; coding: utf-8 -*-# -*- mode: python ; coding: utf-8 -*-# build_executable.spec - VERSÃO COMPLETA COM TODAS AS DEPENDÊNCIAS

import sys

from pathlib import Path



# Define pathsa = Analysis(# -*- mode: python ; coding: utf-8 -*-

script_dir = Path(__file__).parent

project_root = script_dir.parent    ['../run.py'],



# Verifica se estamos na estrutura correta    pathex=['../'],# ========== CONFIGURAÇÃO DE BUILD ==========

if not (project_root / 'run.py').exists():

    raise FileNotFoundError("run.py não encontrado! Verifique se está na estrutura correta do projeto.")    binaries=[



a = Analysis(        ('../assets/rdp.exe', 'assets/')print("\n=== CONFIGURAÇÃO DE BUILD ===")import os

    ['../run.py'],

    pathex=[str(project_root)],    ],

    binaries=[],

    datas=[    datas=[print("Nome do executável: WATS.exe")import sys

        ('../assets', 'assets'),

        ('../wats_settings.json', '.'),        ('../assets/ats.ico', 'assets/'),

    ],

    hiddenimports=[        ('../wats_settings.json', './'),print("Ícone: ../assets/ats.ico")from pathlib import Path

        # WATS Application modules

        'wats_app',        ('../wats_app/', 'wats_app/')

        'wats_app.main',

        'wats_app.app_window',    ],print("Console: Desabilitado")

        'wats_app.config',

        'wats_app.dialogs',    hiddenimports=[

        'wats_app.utils',

        'wats_app.db',        'wats_app',print("Modo: One-folder distribution")block_cipher = None

        'wats_app.db.database_manager',

        'wats_app.db.db_service',        'wats_app.main',

        'wats_app.db.exceptions',

        'wats_app.db.repositories',        'wats_app.app_window',print("UPX: Habilitado (se disponível)")

        'wats_app.db.repositories.base_repository',

        'wats_app.db.repositories.connection_repository',        'wats_app.config',

        'wats_app.db.repositories.group_repository',

        'wats_app.db.repositories.log_repository',        'wats_app.dialogs',print("=====================================\n")# Paths

        'wats_app.db.repositories.user_repository',

        'wats_app.admin_panels',        'wats_app.utils',

        'wats_app.admin_panels.admin_hub',

        'wats_app.admin_panels.connection_manager',        'wats_app.admin_panels',project_root = Path('..').resolve()

        'wats_app.admin_panels.group_manager',

        'wats_app.admin_panels.user_manager',        'wats_app.admin_panels.admin_hub',

        # External dependencies

        'customtkinter',        'wats_app.admin_panels.connection_manager',# ========== HIDDEN IMPORTS ==========venv_path = project_root / 'venv'

        'pyodbc',

        'psycopg2',        'wats_app.admin_panels.group_manager',

        'cv2',

        'win32api',        'wats_app.admin_panels.user_manager',hiddenimports = [

        'win32con',

        'win32gui',        'wats_app.db',

        'win32process',

        'pydantic',        'wats_app.db.database_manager',    # WATS Application modules# --- IMPORTANTE: Aponta para o run.py ---

        'requests',

        'urllib3',        'wats_app.db.db_service',

        'certifi'

    ],        'wats_app.db.exceptions',    'wats_app',a = Analysis(['../run.py'], # <-- Verifica se é 'run.py' (agora referenciando da pasta scripts)

    hookspath=[],

    runtime_hooks=[],        'wats_app.db.repositories',

    excludes=[],

    noarchive=False,        'wats_app.db.repositories.base_repository',    'wats_app.main',             pathex=[str(project_root)], # Adiciona o diretório raiz (WATS_Project) ao path

)

        'wats_app.db.repositories.connection_repository',

pyz = PYZ(a.pure)

        'wats_app.db.repositories.group_repository',    'wats_app.app_window',             

exe = EXE(

    pyz,        'wats_app.db.repositories.log_repository',

    a.scripts,

    [],        'wats_app.db.repositories.user_repository',    'wats_app.config',             # Binários necessários para OpenCV e outras libs

    exclude_binaries=True,

    name='WATS',        'customtkinter',

    debug=False,

    bootloader_ignore_signals=False,        'pyodbc',    'wats_app.dialogs',             binaries=[

    strip=False,

    upx=True,        'psycopg2',

    console=False,

    icon='../assets/ats.ico',        'cv2',    'wats_app.utils',                 (str(venv_path / 'Lib/site-packages/cv2/*.dll'), 'cv2'),

)

        'win32api',

coll = COLLECT(

    exe,        'win32con',                     (str(venv_path / 'Lib/site-packages/cv2/*.pyd'), 'cv2'),

    a.binaries,

    a.datas,        'win32gui',

    strip=False,

    upx=True,        'win32process',    # Admin panels                 # Adiciona DLLs do Windows se existirem

    name='WATS',

)        'pydantic',

        'requests',    'wats_app.admin_panels',                 (str(venv_path / 'Lib/site-packages/win32/*.dll'), 'win32'),

        'urllib3',

        'certifi'    'wats_app.admin_panels.admin_hub',                 (str(venv_path / 'Lib/site-packages/win32/*.pyd'), 'win32'),

    ],

    hookspath=[],    'wats_app.admin_panels.connection_manager',             ],

    runtime_hooks=[],

    excludes=[],    'wats_app.admin_panels.group_manager', 

    win_no_prefer_redirects=False,

    win_private_assemblies=False,    'wats_app.admin_panels.user_manager',             # --- DADOS E ASSETS ---

    cipher=None,

    noarchive=False                 # Copia a pasta 'assets' para dentro do pacote do .exe

)

    # Database modules             # Inclui o arquivo .env para as configurações de banco

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

    'wats_app.db',             # Inclui o config.json para configurações do usuário

exe = EXE(

    pyz,    'wats_app.db.database_manager',             # Inclui docs para sistema de proteção de sessão

    a.scripts,

    [],    'wats_app.db.db_service',             datas=[

    exclude_binaries=True,

    name='WATS',    'wats_app.db.exceptions',                 ('../assets', 'assets'), 

    debug=False,

    bootloader_ignore_signals=False,                     ('../config/.env', '.'), 

    strip=False,

    upx=True,    # Repository modules                 ('../config/config.json', '.'),

    console=False,

    icon='../assets/ats.ico',    'wats_app.db.repositories',                 ('../docs', 'docs'),  # Para sistema de proteção de sessão

    disable_windowed_traceback=False

)    'wats_app.db.repositories.base_repository',             ],



coll = COLLECT(    'wats_app.db.repositories.connection_repository',

    exe,

    a.binaries,    'wats_app.db.repositories.group_repository',             # --- HIDDEN IMPORTS COMPLETOS ---

    a.zipfiles,

    a.datas,    'wats_app.db.repositories.log_repository',             hiddenimports=[

    strip=False,

    upx=True,    'wats_app.db.repositories.user_repository',                 # ========== CORE WATS MODULES ==========

    upx_exclude=[],

    name='WATS'                     'src.wats',

)
    # CustomTkinter and dependencies                 'src.wats.main',

    'customtkinter',                 'src.wats.app_window',

    'customtkinter.windows',                 'src.wats.config',

    'customtkinter.windows.widgets',                 'src.wats.utils',

    'customtkinter.windows.ctk_tk',                 'src.wats.dialogs',

    'customtkinter.windows.ctk_toplevel',                 

    'customtkinter.widgets',                 # ========== DATABASE MODULES ==========

    'customtkinter.widgets.core_rendering',                 'src.wats.db',

    'customtkinter.widgets.core_widget_classes',                 'src.wats.db.db_service',

    'customtkinter.widgets.ctk_button',                 'src.wats.db.database_manager',

    'customtkinter.widgets.ctk_canvas',                 'src.wats.db.exceptions',

    'customtkinter.widgets.ctk_checkbox',                 'src.wats.db.demo_adapter',

    'customtkinter.widgets.ctk_combobox',                 'src.wats.db.repositories',

    'customtkinter.widgets.ctk_entry',                 'src.wats.db.repositories.base_repository',

    'customtkinter.widgets.ctk_font',                 'src.wats.db.repositories.connection_repository',

    'customtkinter.widgets.ctk_frame',                 'src.wats.db.repositories.group_repository',

    'customtkinter.widgets.ctk_image',                 'src.wats.db.repositories.log_repository',

    'customtkinter.widgets.ctk_input_dialog',                 'src.wats.db.repositories.user_repository',

    'customtkinter.widgets.ctk_label',                 'src.wats.db.repositories.session_protection_repository',  # NOVO

    'customtkinter.widgets.ctk_optionmenu',                 

    'customtkinter.widgets.ctk_progressbar',                 # ========== ADMIN PANELS ==========

    'customtkinter.widgets.ctk_radiobutton',                 'src.wats.admin_panels',

    'customtkinter.widgets.ctk_scrollable_frame',                 'src.wats.admin_panels.admin_hub',

    'customtkinter.widgets.ctk_scrollbar',                 'src.wats.admin_panels.connection_manager',

    'customtkinter.widgets.ctk_segmented_button',                 'src.wats.admin_panels.group_manager',

    'customtkinter.widgets.ctk_slider',                 'src.wats.admin_panels.user_manager',

    'customtkinter.widgets.ctk_switch',                 

    'customtkinter.widgets.ctk_tabview',                 # ========== SISTEMA DE PROTEÇÃO DE SESSÃO ==========

    'customtkinter.widgets.ctk_textbox',                 'docs.session_protection',  # NOVO E IMPORTANTE

    'customtkinter.widgets.theme',                 

    'customtkinter.widgets.font',                 # ========== RECORDING DEPENDENCIES ==========

    'customtkinter.widgets.scaling',                 'src.wats.recording',

    'customtkinter.widgets.appearance_mode',                 'src.wats.recording.session_recorder',

    'customtkinter.widgets.theme_manager',                 'src.wats.recording.recording_manager',

    'customtkinter.widgets.scaling_tracker',                 'src.wats.api',

                     'src.wats.api.upload_client',

    # Database drivers                 'src.wats.api.upload_manager',

    'pyodbc',                 'src.wats.api.api_integration',

    'psycopg2',                 

    'psycopg2._psycopg',                 # ========== ESSENTIAL EXTERNAL DEPENDENCIES ==========

    'psycopg2.extensions',                 'cv2',

                     'cv2.cv2',

    # OpenCV                 'mss',

    'cv2',                 'mss.windows',

    'cv2.cv2',                 'mss.base',

                     'numpy',

    # Windows specific                 'numpy.core',

    'win32api',                 'numpy.lib',

    'win32con',                 

    'win32gui',                 # ========== WINDOWS SYSTEM DEPENDENCIES ==========

    'win32process',                 'psutil',

    'win32file',                 'win32gui',

    'win32pipe',                 'win32process',

    'win32event',                 'win32api',

    'win32security',                 'win32con',

    'win32service',                 'win32file',

    'win32timezone',                 'win32service',

    'win32clipboard',                 'pywintypes',

    'pywintypes',                 'pythoncom',

    'pythoncom',                 

    'win32com',                 # ========== UI DEPENDENCIES ==========

    'win32com.client',                 'customtkinter',

    'win32com.shell',                 'customtkinter.windows',

                     'customtkinter.windows.widgets',

    # Data validation                 'tkinter',

    'pydantic',                 'tkinter.ttk',

    'pydantic.v1',                 'tkinter.messagebox',

    'pydantic.main',                 'tkinter.filedialog',

    'pydantic.fields',                 'tkinter.simpledialog',

    'pydantic.validators',                 

    'pydantic.typing',                 # ========== DATABASE DEPENDENCIES ==========

                     'pyodbc',

    # HTTP requests                 'psycopg2',

    'requests',                 'psycopg2._psycopg',

    'urllib3',                 'sqlite3',

    'certifi',                 

    'charset_normalizer',                 # ========== CONFIGURATION DEPENDENCIES ==========

    'idna',                 'dotenv',

                     'pydantic',

    # Essential Python modules                 'pydantic.dataclasses',

    'tkinter',                 'pydantic.fields',

    'tkinter.ttk',                 'pydantic.main',

    'tkinter.filedialog',                 

    'tkinter.messagebox',                 # ========== NETWORKING DEPENDENCIES ==========

    'tkinter.font',                 'requests',

    'PIL',                 'requests.adapters',

    'PIL.Image',                 'requests.auth',

    'PIL.ImageTk',                 'requests.models',

    'json',                 'urllib3',

    'logging',                 'urllib3.util',

    'subprocess',                 'urllib3.poolmanager',

    'threading',                 

    'queue',                 # ========== STANDARD LIBRARY ESSENTIALS ==========

    'datetime',                 'json',

    'os',                 'logging',

    'sys',                 'logging.handlers',

    'pathlib',                 'datetime',

    'hashlib',                 'time',

    'base64',                 'threading',

    'configparser'                 'socket',

]                 'subprocess',

                 'webbrowser',

# ========== ANÁLISE ==========                 'hashlib',

a = Analysis(                 'secrets',

    ['../run.py'],  # Script principal                 'string',

    pathex=['../'],  # Caminhos de busca                 'pathlib',

    binaries=[                 'os',

        # Executável RDP personalizado                 'sys',

        ('../assets/rdp.exe', 'assets/')                 'typing',

    ],                 'collections',

    datas=[                 'functools',

        # Ícone da aplicação                 'operator',

        ('../assets/ats.ico', 'assets/'),                 'math',

        # Configurações da aplicação                 'random',

        ('../wats_settings.json', './'),                 'tempfile',

        # Módulos da aplicação WATS completos                 'shutil',

        ('../wats_app/', 'wats_app/'),                 'glob',

        ('../wats_app/admin_panels/', 'wats_app/admin_panels/'),                 'ast',

        ('../wats_app/db/', 'wats_app/db/'),                 'importlib',

        ('../wats_app/db/repositories/', 'wats_app/db/repositories/')                 're',

    ],             ],

    hiddenimports=hiddenimports,

    hookspath=[],             # Módulos para pular durante análise (otimização)

    runtime_hooks=[],             excludes=[

    excludes=[                 'matplotlib',

        # Módulos de teste desnecessários                 'pandas',

        'unittest', 'test', 'tests', '_pytest', 'py._pytest',                 'scipy',

        'doctest', 'pdb', 'pydoc',                 'IPython',

                         'jupyter',

        # Módulos de desenvolvimento desnecessários                 'notebook',

        'IPython', 'jupyter', 'notebook', 'ipykernel',                 'sphinx',

        'matplotlib', 'scipy', 'pandas', 'numpy.testing',                 'pytest',

                         'setuptools',

        # Módulos de interface gráfica alternativos                 'distutils',

        'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx',                 'pkg_resources',

                         'test',

        # Módulos de documentação                 'tests',

        'sphinx', 'docutils',             ],

        

        # Módulos de empacotamento             # Configurações de otimização

        'setuptools', 'distutils', 'pip'             noarchive=False,

    ],             optimize=0,

    win_no_prefer_redirects=False,             cipher=block_cipher)

    win_private_assemblies=False,

    cipher=None,# ========== CONFIGURAÇÃO PYZ ==========

    noarchive=Falsepyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

)

# ========== CONFIGURAÇÃO EXE ==========

# ========== PYZ ==========exe = EXE(pyz,

pyz = PYZ(a.pure, a.zipped_data, cipher=None)          a.scripts,

          [],

# ========== EXECUTÁVEL ==========          exclude_binaries=True,

exe = EXE(pyz,          name='WATS',

          a.scripts,          debug=False,  # Set to True for debugging

          [],          bootloader_ignore_signals=False,

          exclude_binaries=True,          strip=False,

          name='WATS',          upx=True,  # Compressão UPX (se disponível)

          debug=False,          console=False,  # False = janela sem console

          bootloader_ignore_signals=False,          icon='../assets/ats.ico',  # Ícone do aplicativo

          strip=False,          disable_windowed_traceback=False)

          upx=True,

          console=False,  # False = janela sem console# ========== CONFIGURAÇÃO COLLECT ==========

          icon='../assets/ats.ico',  # Ícone do aplicativocoll = COLLECT(exe,

          disable_windowed_traceback=False)               a.binaries,

               a.zipfiles,

# ========== COLLECT ==========               a.datas,

coll = COLLECT(exe,               strip=False,

               a.binaries,               upx=True,

               a.zipfiles,               upx_exclude=[],

               a.datas,               name='WATS')

               strip=False,

               upx=True,# ========== INFORMAÇÕES DE BUILD ==========

               upx_exclude=[],print("\n=== CONFIGURAÇÃO DE BUILD ===")

               name='WATS')print("Nome do executável: WATS.exe")
print("Ícone: ../assets/ats.ico")
print("Console: Desabilitado")
print("Modo: One-folder distribution")
print("UPX: Habilitado (se disponível)")
print("=====================================\n")
                 'psycopg2',
                 
                 # Essential API dependencies
                 'requests',
                 'urllib3',
                 'certifi'
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[
                 # Módulos de teste desnecessários
                 'unittest', 'test', 'tests', '_pytest', 'py._pytest',
                 'doctest', 'pdb', 'pydoc',
                 
                 # Tkinter desnecessários (já temos customtkinter)
                 'tkinter.test', 'tkinter.tix', 'turtle',
                 
                 # Matplotlib (se não usado)
                 'matplotlib', 'mpl_toolkits',
                 
                 # Jupyter/IPython
                 'IPython', 'jupyter', 'notebook',
                 
                 # Desenvolvimento
                 'distutils', 'setuptools', 'pip', 'wheel',
                 
                 # NumPy opcionais (reduz ~10MB)
                 'numpy.f2py', 'numpy.distutils', 'numpy.testing',
                 'numpy.ma', 'numpy.polynomial', 'numpy.typing',
                 
                 # OpenCV opcionais
                 'cv2.gapi', 'cv2.ml', 'cv2.dnn', 'cv2.face',
                 'cv2.objdetect', 'cv2.stereo', 'cv2.superres',
                 
                 # SSL/Crypto desnecessários
                 'cryptography.hazmat.backends.openssl.x25519',
                 'cryptography.hazmat.backends.openssl.x448',
                 
                 # Requests opcionais
                 'requests_toolbelt', 'requests_oauthlib',
                 
                 # Pillow desnecessários (se não usando imagens)
                 'PIL.ImageShow', 'PIL.ImageQt', 'PIL.ImageWin',
                 
                 # Outros grandes e desnecessários
                 'sqlite3', 'xml', 'html', 'http.server',
                 'email', 'calendar', 'difflib'
             ],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='WATS_App',      # <--- Nome do seu .exe (pode mudar se quiser)
          debug=False,
          bootloader_ignore_signals=False,
          strip=True,          # Remove símbolos de debug
          upx=True,            # ✅ ATIVA compressão UPX (reduz ~30-50%)
          upx_exclude=[],
          runtime_tmpdir=None,

          # --- JANELA COM CONSOLE (para debug temporário) ---
          console=True,        # ✅ Ativa console para verificar erros

          # --- ÍCONE ---
          icon='assets/ats.ico') # <--- Caminho para o ícone
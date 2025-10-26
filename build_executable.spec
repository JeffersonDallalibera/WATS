# build_executable.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# --- IMPORTANTE: Aponta para o run.py ---
a = Analysis(['run.py'], # <-- Verifica se é 'run.py'
             pathex=['.'], # Adiciona o diretório raiz (WATS_Project) ao path
             binaries=[],

             # --- VERIFICA SE OS ASSETS ESTÃO AQUI ---
             # Copia a pasta 'assets' para dentro do pacote do .exe
             # Inclui o arquivo .env para as configurações de banco
             datas=[('assets', 'assets'), ('.env', '.')], # <-- Inclui .env no executável

             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
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
          strip=True,
          upx=False,           # UPX comprime o executável (requer UPX instalado separadamente)
          upx_exclude=[],
          runtime_tmpdir=None,

          # --- JANELA COM CONSOLE (temporário para debug) ---
          console=False,     # <--- Habilita console para depuração de startup

          # --- ÍCONE ---
          icon='assets/ats.ico') # <--- Caminho para o ícone
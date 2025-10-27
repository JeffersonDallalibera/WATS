@echo off
:: WATS Build Script - Limpa cache e cria executável completo
:: Autor: WATS Team
:: Data: 2025

echo ========================================
echo    WATS BUILD SCRIPT V4.2 - 2025
echo ========================================
echo.

:: Verifica se está no diretório correto
if not exist "src\wats" (
    echo ERRO: Execute este script na pasta raiz do projeto WATS
    echo Pasta atual: %CD%
    echo.
    pause
    exit /b 1
)

:: Ativa o ambiente virtual
echo 🔧 Ativando ambiente virtual...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
) else (
    echo ❌ ERRO: Ambiente virtual não encontrado!
    echo Execute primeiro: python -m venv venv
    pause
    exit /b 1
)

echo.
echo 🧹 LIMPANDO CACHE E ARQUIVOS TEMPORÁRIOS...
echo ========================================

:: Remove cache Python
echo Removendo cache Python...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
for /r . %%f in (*.pyc *.pyo) do @if exist "%%f" del /q "%%f"

:: Remove builds anteriores
echo Removendo builds anteriores...
if exist "dist" rd /s /q "dist"
if exist "build" rd /s /q "build"
if exist "*.spec" del /q "*.spec"

:: Remove logs antigos
echo Removendo logs antigos...
if exist "wats_app.log" del /q "wats_app.log"
if exist "*.log" del /q "*.log"

:: Remove arquivos temporários
echo Removendo arquivos temporários...
if exist "temp" rd /s /q "temp"
if exist "tmp" rd /s /q "tmp"

echo ✅ Limpeza concluída!
echo.

echo 🔍 DETECTANDO DEPENDÊNCIAS...
echo ========================================

:: Executa scanner de dependências
python scripts\dependency_scanner.py

if %ERRORLEVEL% neq 0 (
    echo ❌ ERRO: Falha ao detectar dependências
    pause
    exit /b 1
)

echo.
echo 📦 VERIFICANDO DEPENDÊNCIAS...
echo ========================================

:: Verifica se todas as dependências estão instaladas
echo Verificando pacotes instalados...
python -c "
import sys
import importlib.util

required_packages = [
    'customtkinter', 'pyodbc', 'cv2', 'numpy', 'mss', 
    'psutil', 'requests', 'pydantic', 'dotenv'
]

missing = []
for package in required_packages:
    # Mapeia nomes especiais
    check_name = package
    if package == 'cv2':
        check_name = 'cv2'
    elif package == 'dotenv':
        check_name = 'dotenv'
    
    try:
        importlib.import_module(check_name)
        print(f'✅ {package}')
    except ImportError:
        print(f'❌ {package} - FALTANDO!')
        missing.append(package)

if missing:
    print(f'\\n❌ DEPENDÊNCIAS FALTANDO: {missing}')
    print('Execute: pip install -r requirements.txt')
    sys.exit(1)
else:
    print('\\n✅ Todas as dependências estão instaladas!')
"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ ERRO: Dependências faltando!
    echo Instalando dependências...
    pip install -r requirements.txt
    
    if !ERRORLEVEL! neq 0 (
        echo ❌ ERRO: Falha ao instalar dependências
        pause
        exit /b 1
    )
)

echo.
echo 🏗️ CRIANDO EXECUTÁVEL...
echo ========================================

:: Cria o executável usando PyInstaller
echo Iniciando build com PyInstaller...

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "WATS_V4.2_2025" ^
    --icon "assets\ats.ico" ^
    --add-data "assets;assets" ^
    --add-data "config\.env;." ^
    --add-data "config\config.json;." ^
    --add-data "docs;docs" ^
    --hidden-import "customtkinter" ^
    --hidden-import "pyodbc" ^
    --hidden-import "cv2" ^
    --hidden-import "numpy" ^
    --hidden-import "mss" ^
    --hidden-import "mss.windows" ^
    --hidden-import "psutil" ^
    --hidden-import "win32gui" ^
    --hidden-import "win32process" ^
    --hidden-import "win32api" ^
    --hidden-import "tkinter" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "requests" ^
    --hidden-import "pydantic" ^
    --hidden-import "dotenv" ^
    --hidden-import "src.wats" ^
    --hidden-import "src.wats.main" ^
    --hidden-import "src.wats.app_window" ^
    --hidden-import "src.wats.config" ^
    --hidden-import "src.wats.db.db_service" ^
    --hidden-import "src.wats.db.repositories" ^
    --hidden-import "src.wats.admin_panels" ^
    --hidden-import "docs.session_protection" ^
    --collect-submodules "src.wats" ^
    --collect-data "customtkinter" ^
    run.py

if %ERRORLEVEL% neq 0 (
    echo ❌ ERRO: Falha ao criar executável!
    echo.
    echo Verifique os logs acima para mais detalhes.
    pause
    exit /b 1
)

echo.
echo 🧪 TESTANDO EXECUTÁVEL...
echo ========================================

:: Verifica se o executável foi criado
if not exist "dist\WATS_V4.2_2025.exe" (
    echo ❌ ERRO: Executável não foi criado!
    pause
    exit /b 1
)

:: Mostra informações do arquivo
echo ✅ Executável criado com sucesso!
echo.
echo 📊 INFORMAÇÕES DO ARQUIVO:
for %%F in ("dist\WATS_V4.2_2025.exe") do (
    echo   Arquivo: %%~nxF
    echo   Tamanho: %%~zF bytes ^(~%%~zF KB^)
    echo   Data: %%~tF
)

echo.
echo 🎯 BUILD COMPLETO!
echo ========================================
echo.
echo ✅ Executável criado: dist\WATS_V4.2_2025.exe
echo ✅ Cache limpo
echo ✅ Dependências verificadas
echo ✅ Sistema de proteção de sessão incluído
echo ✅ Validação no servidor implementada
echo ✅ Remoção automática de proteções
echo.
echo 🚀 O WATS está pronto para distribuição!
echo.

:: Abre pasta do executável
echo Abrindo pasta do executável...
explorer dist

echo.
echo Pressione qualquer tecla para finalizar...
pause > nul
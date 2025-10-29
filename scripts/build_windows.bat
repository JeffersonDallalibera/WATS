@echo off
:: Build script para Windows - WATS
:: Cria executável Windows usando o spec multiplataforma

echo ========================================
echo    WATS BUILD SCRIPT - WINDOWS V1.0
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

:: Remove logs antigos
echo Removendo logs antigos...
if exist "wats_app.log" del /q "wats_app.log"
if exist "*.log" del /q "*.log"

echo.
echo 📦 INSTALANDO DEPENDÊNCIAS...
echo ==============================

:: Atualiza pip e instala dependências
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo 🏗️  CONSTRUINDO EXECUTÁVEL...
echo =============================

:: Usa o spec file multiplataforma
pyinstaller --clean --noconfirm WATS-multiplatform.spec

if %ERRORLEVEL% EQU 0 (
    echo ✅ Executável criado com sucesso!
    echo Localização: dist\WATS\
) else (
    echo ❌ Erro ao criar executável!
    pause
    exit /b 1
)

echo.
echo 📦 CRIANDO INSTALADOR WINDOWS...
echo ================================

:: Verifica se o NSIS está disponível (opcional)
where makensis >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo NSIS encontrado, criando instalador...
    :: Aqui você pode adicionar script NSIS se necessário
    echo (Instalador NSIS pode ser implementado aqui)
) else (
    echo NSIS não encontrado - pulando criação de instalador
    echo Você pode instalar o NSIS para criar instaladores automáticos
)

echo.
echo 🎉 BUILD COMPLETO!
echo ==================
echo Executável: dist\WATS\WATS.exe
echo.
echo Para executar:
echo .\dist\WATS\WATS.exe
echo.
pause
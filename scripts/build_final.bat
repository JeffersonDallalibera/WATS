@echo off
:: ============================================================================
:: WATS - BUILD FINAL COMPLETO COM LIMPEZA E VERIFICAÇÃO DE DEPENDÊNCIAS
:: ============================================================================
:: Este script executa um build completo do WATS com todas as verificações
:: Criado: Dezembro 2024
:: ============================================================================

title WATS - Build Final Completo
color 0A

echo.
echo ========================================================================
echo                        WATS - BUILD FINAL COMPLETO
echo ========================================================================
echo Iniciando processo de build completo...
echo Data/Hora: %date% %time%
echo.

:: ============================================================================
:: ETAPA 1: VERIFICAÇÃO DO AMBIENTE
:: ============================================================================
echo [ETAPA 1/7] Verificando ambiente...

:: Verifica se estamos no diretório correto
if not exist "..\run.py" (
    echo ERRO: run.py nao encontrado! Execute este script da pasta scripts\
    pause
    exit /b 1
)

:: Verifica se o venv existe
if not exist "..\venv\" (
    echo ERRO: Ambiente virtual nao encontrado em ..\venv\
    echo Crie o ambiente virtual primeiro!
    pause
    exit /b 1
)

echo ✓ Ambiente verificado com sucesso!

:: ============================================================================
:: ETAPA 2: ATIVAÇÃO DO AMBIENTE VIRTUAL
:: ============================================================================
echo.
echo [ETAPA 2/7] Ativando ambiente virtual...

call "..\venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERRO: Falha ao ativar ambiente virtual!
    pause
    exit /b 1
)

echo ✓ Ambiente virtual ativado!

:: ============================================================================
:: ETAPA 3: LIMPEZA COMPLETA DE CACHE
:: ============================================================================
echo.
echo [ETAPA 3/7] Limpando cache Python e build anteriores...

:: Remove cache Python
echo Removendo __pycache__ recursivamente...
for /d /r ".." %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

:: Remove arquivos .pyc
echo Removendo arquivos .pyc...
del /s /q "..\*.pyc" >nul 2>&1

:: Remove builds anteriores
echo Removendo builds anteriores...
if exist "build\" rd /s /q "build\"
if exist "dist\" rd /s /q "dist\"
if exist "..\build\" rd /s /q "..\build\"
if exist "..\dist\" rd /s /q "..\dist\"

:: Remove spec antigo se existir
if exist "..\*.spec" del /q "..\*.spec"

echo ✓ Cache limpo com sucesso!

:: ============================================================================
:: ETAPA 4: ATUALIZAÇÃO DE DEPENDÊNCIAS
:: ============================================================================
echo.
echo [ETAPA 4/7] Verificando e atualizando dependências...

:: Executa o scanner de dependências
echo Executando scanner de dependências...
python dependency_scanner.py
if errorlevel 1 (
    echo AVISO: Scanner de dependencias reportou problemas, mas continuando...
)

:: Instala/atualiza dependências do requirements.txt
echo Instalando dependencias do requirements.txt...
pip install -r "..\requirements.txt" --upgrade
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias!
    pause
    exit /b 1
)

:: Instala PyInstaller se não estiver instalado
echo Verificando PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller...
    pip install pyinstaller
)

echo ✓ Dependências verificadas e atualizadas!

:: ============================================================================
:: ETAPA 5: VALIDAÇÃO DE ARQUIVOS ESSENCIAIS
:: ============================================================================
echo.
echo [ETAPA 5/7] Validando arquivos essenciais...

:: Verifica arquivos principais
set "missing_files="
if not exist "..\run.py" set "missing_files=%missing_files% run.py"
if not exist "..\src\wats\main.py" set "missing_files=%missing_files% main.py"
if not exist "..\assets\ats.ico" set "missing_files=%missing_files% ats.ico"

if not "%missing_files%"=="" (
    echo ERRO: Arquivos essenciais nao encontrados: %missing_files%
    pause
    exit /b 1
)

echo ✓ Todos os arquivos essenciais encontrados!

:: ============================================================================
:: ETAPA 6: BUILD DO EXECUTÁVEL
:: ============================================================================
echo.
echo [ETAPA 6/7] Iniciando build do executavel...
echo Este processo pode levar varios minutos...
echo.

:: Copia o spec file para o diretório raiz temporariamente
copy "build_executable.spec" "..\build_executable.spec" >nul

:: Muda para o diretório raiz para o build
cd ..

:: Executa PyInstaller
echo Executando PyInstaller...
pyinstaller --clean --noconfirm build_executable.spec

:: Verifica se o build foi bem-sucedido
if not exist "dist\WATS\WATS.exe" (
    echo.
    echo ERRO: Build falhou! Executavel nao encontrado.
    echo Verifique os logs acima para detalhes.
    echo.
    pause
    goto cleanup_and_exit
)

echo ✓ Build concluido com sucesso!

:: ============================================================================
:: ETAPA 7: VERIFICAÇÃO FINAL E LIMPEZA
:: ============================================================================
echo.
echo [ETAPA 7/7] Verificacao final e limpeza...

:: Verifica tamanho do executável
for %%A in ("dist\WATS\WATS.exe") do set "file_size=%%~zA"
echo Tamanho do executavel: %file_size% bytes

:: Lista conteúdo do diretório dist
echo.
echo Conteudo da pasta dist\WATS:
dir /b "dist\WATS" | findstr /v "^$"

:: Volta para o diretório scripts
cd scripts

:: Remove spec temporário
del "..\build_executable.spec" >nul 2>&1

echo.
echo ========================================================================
echo                          BUILD CONCLUIDO COM SUCESSO!
echo ========================================================================
echo.
echo Executavel criado em: ..\dist\WATS\WATS.exe
echo Tamanho: %file_size% bytes
echo.
echo Para testar o executavel:
echo   1. Navegue ate ..\dist\WATS\
echo   2. Execute WATS.exe
echo.
echo Para distribuir:
echo   - Copie toda a pasta ..\dist\WATS\ (nao apenas o .exe)
echo   - Todos os arquivos da pasta sao necessarios
echo.
echo ========================================================================

goto end

:cleanup_and_exit
cd scripts
del "..\build_executable.spec" >nul 2>&1
echo.
echo Build interrompido devido a erros.
echo.

:end
echo.
echo Pressione qualquer tecla para finalizar...
pause >nul
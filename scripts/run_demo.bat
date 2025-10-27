@echo off
REM WATS - Script para executar em modo demo
REM Este script define a variável de ambiente e executa o WATS

echo WATS - Modo Demo
echo ================
echo.
echo Ativando modo demo...
set WATS_DEMO_MODE=true

echo Executando WATS...
echo.

REM Executa o WATS com Python do ambiente virtual
C:\Users\Jefferson\Documents\wats\venv\Scripts\python.exe run.py

echo.
echo WATS finalizado.
pause
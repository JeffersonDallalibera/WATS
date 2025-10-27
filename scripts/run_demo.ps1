# WATS - Script PowerShell para modo demo
# Execute este script no PowerShell para ativar o modo demo

Write-Host "WATS - Modo Demo" -ForegroundColor Green
Write-Host "================" -ForegroundColor Green
Write-Host ""

Write-Host "Ativando modo demo..." -ForegroundColor Yellow
$env:WATS_DEMO_MODE = "true"

Write-Host "Executando WATS..." -ForegroundColor Yellow
Write-Host ""

# Executa o WATS com Python do ambiente virtual
& "C:\Users\Jefferson\Documents\wats\venv\Scripts\python.exe" "run.py"

Write-Host ""
Write-Host "WATS finalizado." -ForegroundColor Green
Read-Host "Pressione Enter para continuar"
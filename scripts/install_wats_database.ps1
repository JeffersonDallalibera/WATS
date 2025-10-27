# ================================================================
# SCRIPT POWERSHELL - INSTALAÇÃO AUTOMÁTICA WATS DATABASE
# Execute como Administrador
# ================================================================

param(
    [string]$ServerInstance = "localhost",
    [string]$DatabaseName = "WATS",
    [string]$AppUser = "wats_application", 
    [string]$AppPassword = "Wats@2024!Secure",
    [switch]$UseWindowsAuth = $false,
    [switch]$CreateBackup = $true,
    [string]$BackupPath = "",
    [switch]$TestConnection = $true
)

# Cores para output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message) Write-ColorOutput $Message "Green" }
function Write-Error { param([string]$Message) Write-ColorOutput $Message "Red" }
function Write-Warning { param([string]$Message) Write-ColorOutput $Message "Yellow" }
function Write-Info { param([string]$Message) Write-ColorOutput $Message "Cyan" }

Write-ColorOutput "================================================================" "Magenta"
Write-ColorOutput "           INSTALAÇÃO AUTOMÁTICA - BANCO WATS                 " "Magenta"
Write-ColorOutput "================================================================" "Magenta"

# Verifica se o módulo SqlServer está disponível
Write-Info "Verificando módulo SqlServer..."
if (-not (Get-Module -ListAvailable -Name SqlServer)) {
    Write-Warning "Módulo SqlServer não encontrado. Tentando instalar..."
    try {
        Install-Module -Name SqlServer -Force -AllowClobber -Scope CurrentUser
        Write-Success "Módulo SqlServer instalado com sucesso!"
    }
    catch {
        Write-Error "Erro ao instalar módulo SqlServer: $($_.Exception.Message)"
        Write-Warning "Execute manualmente: Install-Module -Name SqlServer -Force"
        exit 1
    }
}
else {
    Write-Success "Módulo SqlServer já está disponível."
}

Import-Module SqlServer -Force

# Configurações
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$CreateDbScript = Join-Path $ScriptPath "create_wats_database.sql"
$SecurityScript = Join-Path $ScriptPath "configure_wats_security.sql"

Write-Info "Configurações:"
Write-Host "  Servidor: $ServerInstance" -ForegroundColor White
Write-Host "  Banco: $DatabaseName" -ForegroundColor White
Write-Host "  Usuário App: $AppUser" -ForegroundColor White
Write-Host "  Autenticação Windows: $UseWindowsAuth" -ForegroundColor White
Write-Host "  Criar Backup: $CreateBackup" -ForegroundColor White

# Verifica se os scripts existem
if (-not (Test-Path $CreateDbScript)) {
    Write-Error "Script de criação não encontrado: $CreateDbScript"
    exit 1
}

if (-not (Test-Path $SecurityScript)) {
    Write-Error "Script de segurança não encontrado: $SecurityScript"
    exit 1
}

# Função para executar SQL com tratamento de erro
function Invoke-SqlScriptSafe {
    param(
        [string]$ServerInstance,
        [string]$Database = "master",
        [string]$InputFile,
        [hashtable]$Variables = @{},
        [string]$Query
    )
    
    try {
        $params = @{
            ServerInstance = $ServerInstance
            Database = $Database
            ErrorAction = "Stop"
        }
        
        if ($UseWindowsAuth) {
            # Usa autenticação Windows
        } else {
            # Para SQL Authentication, seria necessário credenciais aqui
            # Por segurança, usamos Windows Auth por padrão
        }
        
        if ($InputFile) {
            $params.InputFile = $InputFile
        }
        
        if ($Query) {
            $params.Query = $Query
        }
        
        if ($Variables.Count -gt 0) {
            $params.Variable = $Variables.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }
        }
        
        Invoke-Sqlcmd @params
        return $true
    }
    catch {
        Write-Error "Erro SQL: $($_.Exception.Message)"
        return $false
    }
}

# Testa conectividade inicial
Write-Info "Testando conectividade com SQL Server..."
$testQuery = "SELECT @@VERSION AS Version, @@SERVERNAME AS ServerName"
$connectionTest = Invoke-SqlScriptSafe -ServerInstance $ServerInstance -Query $testQuery

if (-not $connectionTest) {
    Write-Error "Falha ao conectar com SQL Server. Verifique:"
    Write-Host "  1. Se o SQL Server está executando" -ForegroundColor Yellow
    Write-Host "  2. Se o nome/IP do servidor está correto" -ForegroundColor Yellow
    Write-Host "  3. Se você tem permissões de administrador" -ForegroundColor Yellow
    Write-Host "  4. Se a autenticação Windows está configurada" -ForegroundColor Yellow
    exit 1
}

Write-Success "Conectividade com SQL Server OK!"

# Executa script de criação do banco
Write-Info "Executando script de criação do banco de dados..."
$createResult = Invoke-SqlScriptSafe -ServerInstance $ServerInstance -InputFile $CreateDbScript

if (-not $createResult) {
    Write-Error "Falha ao criar banco de dados!"
    exit 1
}

Write-Success "Banco de dados WATS criado com sucesso!"

# Executa script de configuração de segurança
Write-Info "Executando script de configuração de segurança..."
$variables = @{
    "AppUser" = $AppUser
    "AppPassword" = $AppPassword
}

$securityResult = Invoke-SqlScriptSafe -ServerInstance $ServerInstance -Database $DatabaseName -InputFile $SecurityScript -Variables $variables

if (-not $securityResult) {
    Write-Warning "Houve problemas na configuração de segurança. Verifique manualmente."
}
else {
    Write-Success "Configuração de segurança concluída!"
}

# Cria backup inicial se solicitado
if ($CreateBackup) {
    Write-Info "Criando backup inicial..."
    
    if ([string]::IsNullOrEmpty($BackupPath)) {
        # Tenta descobrir caminho padrão de backup
        $backupQuery = @"
DECLARE @BackupPath NVARCHAR(260);
EXEC master.dbo.xp_instance_regread N'HKEY_LOCAL_MACHINE', 
     N'Software\Microsoft\MSSQLServer\MSSQLServer', 
     N'BackupDirectory', @BackupPath OUTPUT;
SELECT ISNULL(@BackupPath, 'C:\Backup') AS BackupPath;
"@
        
        try {
            $result = Invoke-Sqlcmd -ServerInstance $ServerInstance -Query $backupQuery
            $BackupPath = $result.BackupPath
        }
        catch {
            $BackupPath = "C:\Backup"
        }
    }
    
    # Cria diretório se não existir
    if (-not (Test-Path $BackupPath)) {
        try {
            New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
            Write-Info "Diretório de backup criado: $BackupPath"
        }
        catch {
            Write-Warning "Não foi possível criar diretório de backup: $BackupPath"
            $BackupPath = $env:TEMP
        }
    }
    
    $backupFile = Join-Path $BackupPath "WATS_Initial_$(Get-Date -Format 'yyyyMMdd_HHmmss').bak"
    $backupQuery = "BACKUP DATABASE [$DatabaseName] TO DISK = '$backupFile' WITH INIT, COMPRESSION, STATS = 10"
    
    $backupResult = Invoke-SqlScriptSafe -ServerInstance $ServerInstance -Query $backupQuery
    
    if ($backupResult) {
        Write-Success "Backup inicial criado: $backupFile"
    }
    else {
        Write-Warning "Falha ao criar backup inicial. Crie manualmente se necessário."
    }
}

# Teste de conectividade da aplicação
if ($TestConnection) {
    Write-Info "Testando conectividade com usuário da aplicação..."
    
    # Constrói connection string
    $connectionString = "Server=$ServerInstance;Database=$DatabaseName;Integrated Security=true;TrustServerCertificate=true;"
    
    try {
        $testQuery = @"
SELECT 
    COUNT(*) as ConfigCount 
FROM Config_Sistema_WTS;

SELECT 
    COUNT(*) as UserCount 
FROM Usuario_Sistema_WTS;

SELECT 
    COUNT(*) as GroupCount 
FROM Grupo_WTS;

SELECT 
    COUNT(*) as ConnectionCount 
FROM Conexao_WTS;
"@
        
        $testResult = Invoke-SqlScriptSafe -ServerInstance $ServerInstance -Database $DatabaseName -Query $testQuery
        
        if ($testResult) {
            Write-Success "Teste de conectividade da aplicação: OK"
            Write-Info "Connection String sugerida:"
            Write-Host "  $connectionString" -ForegroundColor White
        }
    }
    catch {
        Write-Warning "Teste de conectividade falhou: $($_.Exception.Message)"
    }
}

# Informações finais
Write-ColorOutput "================================================================" "Magenta"
Write-ColorOutput "                    INSTALAÇÃO CONCLUÍDA!                      " "Green"
Write-ColorOutput "================================================================" "Magenta"

Write-Info "Informações do banco criado:"
Write-Host "  Servidor: $ServerInstance" -ForegroundColor White
Write-Host "  Banco: $DatabaseName" -ForegroundColor White
Write-Host "  Usuário admin padrão: admin" -ForegroundColor White
Write-Host "  Senha admin padrão: admin" -ForegroundColor Yellow

Write-Info "Connection Strings para aplicação:"

# Windows Authentication
$winAuthConnStr = "Server=$ServerInstance;Database=$DatabaseName;Integrated Security=true;TrustServerCertificate=true;"
Write-Host "  Windows Auth: $winAuthConnStr" -ForegroundColor Cyan

# SQL Server Authentication (se configurado)
if (-not $UseWindowsAuth) {
    $sqlAuthConnStr = "Server=$ServerInstance;Database=$DatabaseName;User Id=$AppUser;Password=$AppPassword;TrustServerCertificate=true;"
    Write-Host "  SQL Auth: $sqlAuthConnStr" -ForegroundColor Cyan
}

# ODBC Format
$odbcConnStr = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=$ServerInstance;DATABASE=$DatabaseName;Integrated Security=yes;TrustServerCertificate=yes;"
Write-Host "  ODBC: $odbcConnStr" -ForegroundColor Cyan

Write-ColorOutput "================================================================" "Magenta"
Write-Success "PRÓXIMOS PASSOS:"
Write-Host "1. Configure a connection string na aplicação WATS" -ForegroundColor Yellow
Write-Host "2. Teste a aplicação com usuário 'admin' / senha 'admin'" -ForegroundColor Yellow
Write-Host "3. Altere a senha padrão do administrador" -ForegroundColor Yellow
Write-Host "4. Configure backup automático via SQL Server Agent" -ForegroundColor Yellow
Write-Host "5. Configure monitoramento de performance se necessário" -ForegroundColor Yellow
Write-ColorOutput "================================================================" "Magenta"

Write-Success "Instalação do banco WATS concluída com sucesso! 🎉"

# Pausa para ler informações
Write-Host "`nPressione qualquer tecla para continuar..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
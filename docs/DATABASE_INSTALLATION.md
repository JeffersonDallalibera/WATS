# 🗄️ INSTALAÇÃO DO BANCO SQL SERVER - WATS

## 📋 Pré-requisitos

### 1. SQL Server

- **SQL Server 2016** ou superior
- **SQL Server Express** (gratuito) ou versões completas
- **SQL Server Management Studio (SSMS)** recomendado

### 2. Permissões

- **Administrador do Windows** para execução dos scripts
- **sysadmin** no SQL Server ou permissões para:
  - Criar bancos de dados
  - Criar logins e usuários
  - Configurar permissões

### 3. Ferramentas

- **PowerShell 5.1** ou superior
- **Módulo SqlServer** (será instalado automaticamente)

## 🚀 Instalação Automática (Recomendada)

### Método 1: PowerShell Script

```powershell
# Execute como Administrador
cd "C:\Users\Jefferson\Documents\wats\scripts"

# Instalação padrão (localhost)
.\install_wats_database.ps1

# Instalação personalizada
.\install_wats_database.ps1 -ServerInstance "MeuServidor\SQLEXPRESS" -DatabaseName "WATS" -AppUser "wats_app" -AppPassword "MinhaSenh@123!"
```

### Parâmetros Disponíveis:

- `-ServerInstance`: Nome/IP do servidor SQL Server (padrão: localhost)
- `-DatabaseName`: Nome do banco (padrão: WATS)
- `-AppUser`: Nome do usuário da aplicação (padrão: wats_application)
- `-AppPassword`: Senha do usuário da aplicação
- `-UseWindowsAuth`: Usar autenticação Windows (switch)
- `-CreateBackup`: Criar backup inicial (padrão: true)
- `-BackupPath`: Caminho para backup (detecta automaticamente)
- `-TestConnection`: Testar conectividade (padrão: true)

## 🛠️ Instalação Manual

### Passo 1: Criar o Banco de Dados

```sql
-- No SQL Server Management Studio, execute:
-- Arquivo: scripts/create_wats_database.sql
```

### Passo 2: Configurar Segurança

```sql
-- Execute em seguida:
-- Arquivo: scripts/configure_wats_security.sql
```

### Passo 3: Configurar Usuário da Aplicação

#### Opção A: SQL Server Authentication

```sql
-- Substituir valores conforme necessário
CREATE LOGIN [wats_application] WITH PASSWORD = 'SuaSenhaSegura123!';
USE [WATS];
CREATE USER [wats_application] FOR LOGIN [wats_application];
ALTER ROLE [wats_app_role] ADD MEMBER [wats_application];
```

#### Opção B: Windows Authentication

```sql
-- Ajustar DOMINIO\usuario conforme seu ambiente
CREATE LOGIN [DOMINIO\wats_service] FROM WINDOWS;
USE [WATS];
CREATE USER [wats_service] FOR LOGIN [DOMINIO\wats_service];
ALTER ROLE [wats_app_role] ADD MEMBER [wats_service];
```

## 🔗 Configuração da Connection String

### Para Desenvolvimento (.env)

```bash
# SQL Server Authentication
DB_TYPE=sqlserver
DB_HOST=localhost
DB_PORT=1433
DB_NAME=WATS
DB_USER=wats_application
DB_PASSWORD=SuaSenhaSegura123!
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_TRUST_CERT=true
DB_ENCRYPT=false
DB_INTEGRATED_AUTH=false
DB_MARS=true
DB_TIMEOUT=30
```

### Para Produção (config/environments/production.json)

```json
{
  "database": {
    "type": "sqlserver",
    "host": "servidor-producao.empresa.com",
    "port": 1433,
    "database": "WATS",
    "username": "wats_application",
    "password": "${DB_PASSWORD}",
    "driver": "ODBC Driver 17 for SQL Server",
    "trust_server_certificate": true,
    "encrypt": true,
    "integrated_security": false,
    "mars_connection": true,
    "connection_timeout": 30
  }
}
```

## 📊 Estrutura do Banco Criado

### Tabelas Principais

| Tabela                  | Propósito                       |
| ----------------------- | ------------------------------- |
| **Config_Sistema_WTS**  | Configurações do sistema        |
| **Usuario_Sistema_WTS** | Usuários da aplicação           |
| **Grupo_WTS**           | Grupos de permissão             |
| **Permissao_Grupo_WTS** | Relação usuário x grupo         |
| **Conexao_WTS**         | Servidores/conexões disponíveis |
| **Usuario_Conexao_WTS** | Log de conexões ativas          |
| **Log_Acesso_WTS**      | Histórico detalhado de acessos  |

### Stored Procedures

- `sp_Limpar_Conexoes_Fantasma` - Remove conexões inativas
- `sp_Relatorio_Conexoes_Ativas` - Relatório de conexões atuais
- `sp_Relatorio_Acessos_Periodo` - Relatório por período

### Views

- `vw_Conexoes_Completas` - Conexões com informações completas
- `vw_Usuarios_Permissoes` - Usuários com grupos associados

### Dados Iniciais

- **Usuário admin**: admin / admin (altere a senha!)
- **Grupos padrão**: Administradores, Usuarios_Basicos, TI_Infraestrutura, Desenvolvimento
- **Conexões exemplo**: Servidores de demonstração
- **Configurações**: Timeout, versão, parâmetros do sistema

## 🔐 Segurança

### Usuários Criados

- **wats_application**: Usuário para a aplicação
- **wats_app_role**: Role com permissões específicas

### Permissões da Role

- **SELECT, INSERT, UPDATE, DELETE** em todas as tabelas WTS
- **EXECUTE** em stored procedures
- **SELECT** em views

### Triggers de Auditoria

- Atualização automática de campos `Data_Alteracao`
- Histórico de modificações

## 🔧 Validação da Instalação

### 1. Verificar Estrutura

```sql
-- Contar tabelas criadas
SELECT COUNT(*) AS Tabelas
FROM sys.tables
WHERE name LIKE '%_WTS';

-- Verificar dados iniciais
SELECT COUNT(*) AS Usuarios FROM Usuario_Sistema_WTS;
SELECT COUNT(*) AS Grupos FROM Grupo_WTS;
SELECT COUNT(*) AS Conexoes FROM Conexao_WTS;
```

### 2. Testar Conectividade

```python
# Script Python para teste
import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=WATS;Integrated Security=yes;TrustServerCertificate=yes"

try:
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Usuario_Sistema_WTS")
        result = cursor.fetchone()
        print(f"Teste OK - Usuários: {result[0]}")
except Exception as e:
    print(f"Erro: {e}")
```

### 3. Testar Aplicação WATS

```bash
# No diretório do projeto
cd "C:\Users\Jefferson\Documents\wats"

# Configurar ambiente
cp config/.env.example .env
# Editar .env com suas configurações

# Executar aplicação
python run.py
```

## 🚨 Troubleshooting

### Erro: "Login failed"

**Causa**: Credenciais incorretas ou usuário sem permissão
**Solução**:

1. Verificar usuário/senha
2. Confirmar se usuário existe no SQL Server
3. Verificar se está na role correta

### Erro: "Cannot open database"

**Causa**: Banco não existe ou sem permissão
**Solução**:

1. Verificar se banco WATS foi criado
2. Confirmar permissões do usuário
3. Testar connection string

### Erro: "Driver not found"

**Causa**: ODBC Driver não instalado
**Solução**:

1. Baixar [ODBC Driver 17 for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
2. Instalar driver
3. Verificar nome do driver na connection string

### Erro: "Trust relationship failed"

**Causa**: Problemas de certificado SSL
**Solução**:

1. Adicionar `TrustServerCertificate=yes` na connection string
2. Ou configurar certificados SSL válidos

### Performance Lenta

**Soluções**:

1. Verificar índices criados
2. Atualizar estatísticas: `UPDATE STATISTICS`
3. Configurar maintenance plan
4. Monitorar queries com SQL Profiler

## 📈 Manutenção

### Backup Regular

```sql
-- Backup completo
BACKUP DATABASE [WATS]
TO DISK = 'C:\Backup\WATS_Full.bak'
WITH COMPRESSION;

-- Backup diferencial
BACKUP DATABASE [WATS]
TO DISK = 'C:\Backup\WATS_Diff.bak'
WITH DIFFERENTIAL, COMPRESSION;
```

### Limpeza de Logs

```sql
-- Executar periodicamente (via SQL Server Agent)
EXEC sp_Limpar_Conexoes_Fantasma;

-- Limpar logs antigos (ajustar período conforme necessário)
DELETE FROM Log_Acesso_WTS
WHERE Log_DataHora_Inicio < DATEADD(DAY, -90, GETDATE());
```

### Monitoramento

```sql
-- Verificar tamanho do banco
SELECT
    DB_NAME() AS DatabaseName,
    SUM(size * 8.0 / 1024) AS SizeMB
FROM sys.database_files;

-- Verificar conexões ativas
EXEC sp_Relatorio_Conexoes_Ativas;

-- Verificar performance
SELECT
    total_worker_time/execution_count AS avg_cpu_time,
    total_elapsed_time/execution_count AS avg_elapsed_time,
    text
FROM sys.dm_exec_query_stats
CROSS APPLY sys.dm_exec_sql_text(sql_handle)
WHERE text LIKE '%WTS%'
ORDER BY avg_elapsed_time DESC;
```

## ✅ Checklist Final

- [ ] SQL Server instalado e funcionando
- [ ] Scripts executados com sucesso
- [ ] Usuário da aplicação criado
- [ ] Connection string configurada
- [ ] Teste de conectividade realizado
- [ ] Aplicação WATS testada
- [ ] Backup inicial criado
- [ ] Senha padrão alterada
- [ ] Documentação salva

---

**🎉 Parabéns! Seu banco SQL Server para WATS está pronto para uso!**

Para suporte adicional, consulte:

- `docs/SQL_SERVER_CONFIG.md` - Configurações detalhadas
- `scripts/validate_sqlserver_config.py` - Script de validação
- Logs da aplicação em `wats_app.log`

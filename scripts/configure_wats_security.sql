-- ================================================================
-- SCRIPT DE CONFIGURAÇÃO DE USUÁRIOS E SEGURANÇA - WATS
-- Execute APÓS a criação do banco principal
-- ================================================================

USE [WATS];
GO

PRINT '================================================================';
PRINT 'CONFIGURAÇÃO DE USUÁRIOS E SEGURANÇA - WATS';
PRINT '================================================================';

-- ================================================================
-- 1. CRIAÇÃO DE USUÁRIOS PARA APLICAÇÃO
-- ================================================================

-- Configurações de exemplo - AJUSTE CONFORME SEU AMBIENTE
DECLARE @AppUser NVARCHAR(128) = 'wats_application';
DECLARE @AppPassword NVARCHAR(128) = 'Wats@2024!Secure';
DECLARE @Domain NVARCHAR(128) = 'EMPRESA'; -- Ajuste para seu domínio
DECLARE @ServiceAccount NVARCHAR(128) = 'wats_service';

-- ----------------------------------------------------------------
-- OPÇÃO 1: Usuário SQL Server Authentication
-- ----------------------------------------------------------------
PRINT 'Criando usuário SQL Server Authentication...';

-- Verifica se o login já existe
IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = @AppUser)
BEGIN
    DECLARE @SqlCreateLogin NVARCHAR(500);
    SET @SqlCreateLogin = 'CREATE LOGIN [' + @AppUser + '] WITH PASSWORD = ''' + @AppPassword + ''', 
                          CHECK_POLICY = ON, CHECK_EXPIRATION = OFF, DEFAULT_DATABASE = [WATS]';
    EXEC sp_executesql @SqlCreateLogin;
    PRINT 'Login criado: ' + @AppUser;
END
ELSE
BEGIN
    PRINT 'Login já existe: ' + @AppUser;
END

-- Verifica se o usuário já existe no banco
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = @AppUser)
BEGIN
    DECLARE @SqlCreateUser NVARCHAR(200);
    SET @SqlCreateUser = 'CREATE USER [' + @AppUser + '] FOR LOGIN [' + @AppUser + ']';
    EXEC sp_executesql @SqlCreateUser;
    PRINT 'Usuário de banco criado: ' + @AppUser;
END
ELSE
BEGIN
    PRINT 'Usuário de banco já existe: ' + @AppUser;
END

-- Adiciona à role da aplicação
IF IS_ROLEMEMBER('wats_app_role', @AppUser) = 0
BEGIN
    DECLARE @SqlAddRole NVARCHAR(200);
    SET @SqlAddRole = 'ALTER ROLE [wats_app_role] ADD MEMBER [' + @AppUser + ']';
    EXEC sp_executesql @SqlAddRole;
    PRINT 'Usuário adicionado à role wats_app_role: ' + @AppUser;
END
ELSE
BEGIN
    PRINT 'Usuário já é membro da role wats_app_role: ' + @AppUser;
END

-- ----------------------------------------------------------------
-- OPÇÃO 2: Windows Authentication (comentado - descomente se necessário)
-- ----------------------------------------------------------------
/*
PRINT 'Configurando Windows Authentication...';

DECLARE @WindowsUser NVARCHAR(256) = @Domain + '\' + @ServiceAccount;

-- Criar login Windows
IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = @WindowsUser)
BEGIN
    DECLARE @SqlCreateWindowsLogin NVARCHAR(300);
    SET @SqlCreateWindowsLogin = 'CREATE LOGIN [' + @WindowsUser + '] FROM WINDOWS';
    EXEC sp_executesql @SqlCreateWindowsLogin;
    PRINT 'Login Windows criado: ' + @WindowsUser;
END

-- Criar usuário
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = @ServiceAccount)
BEGIN
    DECLARE @SqlCreateWindowsUser NVARCHAR(300);
    SET @SqlCreateWindowsUser = 'CREATE USER [' + @ServiceAccount + '] FOR LOGIN [' + @WindowsUser + ']';
    EXEC sp_executesql @SqlCreateWindowsUser;
    PRINT 'Usuário Windows criado: ' + @ServiceAccount;
END

-- Adicionar à role
IF IS_ROLEMEMBER('wats_app_role', @ServiceAccount) = 0
BEGIN
    DECLARE @SqlAddWindowsRole NVARCHAR(300);
    SET @SqlAddWindowsRole = 'ALTER ROLE [wats_app_role] ADD MEMBER [' + @ServiceAccount + ']';
    EXEC sp_executesql @SqlAddWindowsRole;
    PRINT 'Usuário Windows adicionado à role: ' + @ServiceAccount;
END
*/

-- ================================================================
-- 2. CONFIGURAÇÕES DE SEGURANÇA ADICIONAIS
-- ================================================================

PRINT 'Aplicando configurações de segurança...';

-- Força uso de criptografia (comentado - habilite se necessário)
/*
-- Requer conexões criptografadas
EXEC sp_configure 'force encryption', 1;
RECONFIGURE;
*/

-- Configuração de auditoria (opcional)
-- CREATE SERVER AUDIT [WATS_Audit] TO FILE (FILEPATH = 'C:\Audit\');
-- ALTER SERVER AUDIT [WATS_Audit] WITH (STATE = ON);

-- ================================================================
-- 3. CONFIGURAÇÕES DE CONNECTION STRING
-- ================================================================

PRINT 'Exemplos de Connection String:';
PRINT '================================================================';

-- SQL Server Authentication
PRINT 'SQL Server Authentication:';
PRINT 'Server=localhost,1433;Database=WATS;User Id=' + @AppUser + ';Password=' + @AppPassword + ';TrustServerCertificate=true;';
PRINT '';

-- Windows Authentication
PRINT 'Windows Authentication:';
PRINT 'Server=localhost,1433;Database=WATS;Integrated Security=true;TrustServerCertificate=true;';
PRINT '';

-- Com ODBC Driver
PRINT 'ODBC Driver Format:';
PRINT 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=WATS;UID=' + @AppUser + ';PWD=' + @AppPassword + ';TrustServerCertificate=yes;';
PRINT '';

-- ================================================================
-- 4. SCRIPT DE TESTE DE CONECTIVIDADE
-- ================================================================

PRINT 'Testando permissões do usuário da aplicação...';

-- Testa permissões básicas
BEGIN TRY
    -- Teste de SELECT
    DECLARE @TestCount INT;
    SELECT @TestCount = COUNT(*) FROM [dbo].[Config_Sistema_WTS];
    PRINT 'Teste SELECT: OK (' + CAST(@TestCount AS VARCHAR(10)) + ' registros)';
    
    -- Teste de INSERT/UPDATE/DELETE (rollback para não modificar dados)
    BEGIN TRANSACTION;
    
    INSERT INTO [dbo].[Config_Sistema_WTS] ([Cfg_Chave], [Cfg_Valor], [Cfg_Descricao])
    VALUES ('TEST_KEY', 'TEST_VALUE', 'Teste de conectividade');
    PRINT 'Teste INSERT: OK';
    
    UPDATE [dbo].[Config_Sistema_WTS] 
    SET [Cfg_Valor] = 'UPDATED_VALUE' 
    WHERE [Cfg_Chave] = 'TEST_KEY';
    PRINT 'Teste UPDATE: OK';
    
    DELETE FROM [dbo].[Config_Sistema_WTS] 
    WHERE [Cfg_Chave] = 'TEST_KEY';
    PRINT 'Teste DELETE: OK';
    
    ROLLBACK TRANSACTION;
    PRINT 'Testes de DML concluídos (rollback executado)';
    
    -- Teste de execução de procedure
    EXEC [dbo].[sp_Limpar_Conexoes_Fantasma];
    PRINT 'Teste EXECUTE PROCEDURE: OK';
    
    PRINT 'TODOS OS TESTES DE PERMISSÃO PASSARAM!';
    
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    PRINT 'ERRO NO TESTE: ' + ERROR_MESSAGE();
END CATCH

-- ================================================================
-- 5. BACKUP INICIAL
-- ================================================================

PRINT 'Criando backup inicial...';

DECLARE @BackupPath NVARCHAR(260);
DECLARE @BackupFileName NVARCHAR(260);
DECLARE @BackupDate NVARCHAR(20);

SET @BackupDate = FORMAT(GETDATE(), 'yyyyMMdd_HHmmss');
SET @BackupFileName = 'WATS_Initial_Backup_' + @BackupDate + '.bak';

-- Tenta descobrir o caminho padrão de backup
DECLARE @DefaultBackupPath NVARCHAR(260);
EXEC master.dbo.xp_instance_regread N'HKEY_LOCAL_MACHINE', N'Software\Microsoft\MSSQLServer\MSSQLServer', N'BackupDirectory', @DefaultBackupPath OUTPUT;

IF @DefaultBackupPath IS NOT NULL
BEGIN
    SET @BackupPath = @DefaultBackupPath + '\' + @BackupFileName;
    
    BEGIN TRY
        BACKUP DATABASE [WATS] TO DISK = @BackupPath
        WITH INIT, SKIP, NOREWIND, NOUNLOAD, COMPRESSION, STATS = 10;
        PRINT 'Backup inicial criado: ' + @BackupPath;
    END TRY
    BEGIN CATCH
        PRINT 'Erro ao criar backup: ' + ERROR_MESSAGE();
        PRINT 'Crie o backup manualmente quando necessário.';
    END CATCH
END
ELSE
BEGIN
    PRINT 'Caminho de backup padrão não encontrado.';
    PRINT 'Crie backup manual com o comando:';
    PRINT 'BACKUP DATABASE [WATS] TO DISK = ''C:\Backup\WATS_Initial.bak''';
END

-- ================================================================
-- 6. SCRIPT DE LIMPEZA DE TESTE (OPCIONAL)
-- ================================================================

-- Procedure para resetar dados de teste (use com cuidado!)
CREATE OR ALTER PROCEDURE [dbo].[sp_Reset_Test_Data]
AS
BEGIN
    SET NOCOUNT ON;
    
    PRINT 'ATENÇÃO: Este procedimento remove TODOS os dados de teste!';
    PRINT 'Use apenas em ambiente de desenvolvimento/teste.';
    
    -- Remove logs
    DELETE FROM [dbo].[Log_Acesso_WTS];
    DELETE FROM [dbo].[Usuario_Conexao_WTS];
    
    -- Remove conexões de teste
    DELETE FROM [dbo].[Conexao_WTS] WHERE [Con_Nome] LIKE '%Teste%' OR [Con_Nome] LIKE '%Test%';
    
    -- Remove permissões de usuários de teste
    DELETE FROM [dbo].[Permissao_Grupo_WTS] WHERE [Usu_Id] IN (
        SELECT [Usu_Id] FROM [dbo].[Usuario_Sistema_WTS] 
        WHERE [Usu_Nome] LIKE '%test%' OR [Usu_Nome] LIKE '%teste%'
    );
    
    -- Remove usuários de teste
    DELETE FROM [dbo].[Usuario_Sistema_WTS] 
    WHERE [Usu_Nome] LIKE '%test%' OR [Usu_Nome] LIKE '%teste%';
    
    -- Remove grupos de teste
    DELETE FROM [dbo].[Grupo_WTS] 
    WHERE [Gru_Nome] LIKE '%Test%' OR [Gru_Nome] LIKE '%Teste%';
    
    PRINT 'Dados de teste removidos.';
END
GO

-- ================================================================
-- 7. INFORMAÇÕES FINAIS
-- ================================================================

PRINT '================================================================';
PRINT 'CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!';
PRINT '================================================================';
PRINT 'Usuário criado: ' + @AppUser;
PRINT 'Role da aplicação: wats_app_role';
PRINT '================================================================';
PRINT 'PRÓXIMOS PASSOS:';
PRINT '1. Configure a connection string na aplicação';
PRINT '2. Teste a conectividade da aplicação';
PRINT '3. Altere a senha padrão do admin (hash SHA-256)';
PRINT '4. Configure backup automático se necessário';
PRINT '5. Configure monitoramento de performance';
PRINT '================================================================';
PRINT 'INFORMAÇÕES DE CONFIGURAÇÃO:';
PRINT 'Connection String SQL Auth: Server=localhost;Database=WATS;User Id=' + @AppUser + ';Password=' + @AppPassword + ';';
PRINT 'Connection String Windows: Server=localhost;Database=WATS;Integrated Security=true;';
PRINT '================================================================';

-- Query para verificar configuração atual
SELECT 
    'Configuração Atual' AS [Status],
    COUNT(DISTINCT t.name) AS [Tabelas],
    COUNT(DISTINCT p.name) AS [Procedures],
    COUNT(DISTINCT v.name) AS [Views],
    (SELECT COUNT(*) FROM [dbo].[Usuario_Sistema_WTS]) AS [Usuarios],
    (SELECT COUNT(*) FROM [dbo].[Grupo_WTS]) AS [Grupos],
    (SELECT COUNT(*) FROM [dbo].[Conexao_WTS]) AS [Conexoes]
FROM sys.tables t, sys.procedures p, sys.views v
WHERE t.schema_id = SCHEMA_ID('dbo') AND t.name LIKE '%_WTS'
  AND p.schema_id = SCHEMA_ID('dbo') AND p.name LIKE 'sp_%'
  AND v.schema_id = SCHEMA_ID('dbo') AND v.name LIKE 'vw_%';

PRINT 'Script de configuração finalizado!';
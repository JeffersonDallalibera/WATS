-- ================================================================
-- STORED PROCEDURE: Limpar Logs de Acesso Órfãos
-- ================================================================
-- Esta procedure finaliza automaticamente logs de acesso que:
-- 1. Foram iniciados há mais de 24 horas
-- 2. Ainda não possuem data/hora de fim (Log_DataHora_Fim IS NULL)
-- 3. Não possuem conexão ativa correspondente em Usuario_Conexao_WTS
--
-- Casos de uso:
-- - Usuário fechou o WATS sem fechar o RDP
-- - Crash do aplicativo WATS
-- - Conexões que "ficaram para trás" no banco
--
-- Deve ser executada periodicamente (ex: a cada 1 hora via Job do SQL Server)
-- ================================================================
-- COMPATÍVEL COM: DBeaver, SSMS, Azure Data Studio
-- ================================================================

USE WATS;

-- ================================================================
-- PASSO 1: Verifica e cria a coluna Log_Observacoes se não existir
-- ================================================================
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID(N'[dbo].[Log_Acesso_WTS]') 
    AND name = 'Log_Observacoes'
)
BEGIN
    PRINT '📝 Adicionando coluna Log_Observacoes na tabela Log_Acesso_WTS...';
    
    ALTER TABLE [dbo].[Log_Acesso_WTS]
    ADD [Log_Observacoes] NVARCHAR(1000) NULL;
    
    PRINT '✅ Coluna Log_Observacoes adicionada com sucesso!';
    PRINT '';
END
ELSE
BEGIN
    PRINT '✅ Coluna Log_Observacoes já existe.';
END;

-- ================================================================
-- PASSO 2: Remove procedure existente (se houver)
-- ================================================================
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sp_Limpar_Logs_Orfaos]') AND type in (N'P', N'PC'))
BEGIN
    DROP PROCEDURE [dbo].[sp_Limpar_Logs_Orfaos];
    PRINT 'Procedure sp_Limpar_Logs_Orfaos existente removida.';
END;

-- ================================================================
-- PASSO 3: Cria a stored procedure
-- ================================================================
CREATE PROCEDURE [dbo].[sp_Limpar_Logs_Orfaos]
    @HorasLimite INT = 24,  -- Logs mais antigos que X horas
    @SimularExecucao BIT = 0  -- Se 1, apenas mostra o que seria feito (não executa UPDATE)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @DataLimite DATETIME2(3);
    DECLARE @RowsAffected INT = 0;
    DECLARE @LogsParaFinalizar TABLE (
        Log_Id INT,
        Usu_Nome_Maquina NVARCHAR(100),
        Con_Nome_Acessado NVARCHAR(150),
        Log_DataHora_Inicio DATETIME2(3),
        Tempo_Decorrido_Horas DECIMAL(10,2),
        Possui_Conexao_Ativa BIT
    );
    
    -- Calcula data limite (logs mais antigos que @HorasLimite horas atrás)
    SET @DataLimite = DATEADD(HOUR, -@HorasLimite, GETDATE());
    
    PRINT '================================================================';
    PRINT 'LIMPEZA DE LOGS DE ACESSO ÓRFÃOS';
    PRINT '================================================================';
    PRINT 'Data/Hora Atual: ' + CONVERT(VARCHAR, GETDATE(), 120);
    PRINT 'Data/Hora Limite: ' + CONVERT(VARCHAR, @DataLimite, 120);
    PRINT 'Modo: ' + CASE WHEN @SimularExecucao = 1 THEN 'SIMULAÇÃO (nada será alterado)' ELSE 'EXECUÇÃO REAL' END;
    PRINT '';
    
    -- Identifica logs órfãos
    INSERT INTO @LogsParaFinalizar
    SELECT 
        la.Log_Id,
        la.Usu_Nome_Maquina,
        la.Con_Nome_Acessado,
        la.Log_DataHora_Inicio,
        CAST(DATEDIFF(MINUTE, la.Log_DataHora_Inicio, GETDATE()) / 60.0 AS DECIMAL(10,2)) AS Tempo_Decorrido_Horas,
        CASE 
            WHEN EXISTS (
                SELECT 1 FROM Usuario_Conexao_WTS uc
                WHERE uc.Con_Codigo = la.Con_Codigo
                  AND uc.Usu_Nome = SUBSTRING(la.Usu_Nome_Maquina, 1, CHARINDEX('@', la.Usu_Nome_Maquina + '@') - 1)
            ) THEN 1
            ELSE 0
        END AS Possui_Conexao_Ativa
    FROM Log_Acesso_WTS la
    WHERE la.Log_DataHora_Fim IS NULL  -- Sem data de fim
      AND la.Log_DataHora_Inicio < @DataLimite  -- Mais antigo que o limite
    ORDER BY la.Log_DataHora_Inicio;
    
    -- Mostra logs encontrados
    SELECT @RowsAffected = COUNT(*) FROM @LogsParaFinalizar;
    
    IF @RowsAffected = 0
    BEGIN
        PRINT '✅ Nenhum log órfão encontrado.';
        PRINT '================================================================';
        RETURN 0;
    END
    
    PRINT '📊 LOGS ÓRFÃOS ENCONTRADOS: ' + CAST(@RowsAffected AS VARCHAR(10));
    PRINT '';
    PRINT 'Detalhes:';
    PRINT '----------------------------------------------------------------';
    
    SELECT 
        Log_Id AS [ID],
        Usu_Nome_Maquina AS [Usuário],
        Con_Nome_Acessado AS [Servidor],
        CONVERT(VARCHAR, Log_DataHora_Inicio, 120) AS [Início],
        Tempo_Decorrido_Horas AS [Horas Decorridas],
        CASE Possui_Conexao_Ativa 
            WHEN 1 THEN '⚠️ AINDA ATIVO' 
            ELSE '❌ Sem Conexão' 
        END AS [Status Conexão]
    FROM @LogsParaFinalizar
    ORDER BY Log_DataHora_Inicio;
    
    PRINT '';
    
    -- Se for simulação, apenas mostra e sai
    IF @SimularExecucao = 1
    BEGIN
        PRINT '🔍 SIMULAÇÃO: Nenhuma alteração foi feita.';
        PRINT '   Para executar de verdade, chame: EXEC sp_Limpar_Logs_Orfaos @SimularExecucao = 0';
        PRINT '================================================================';
        RETURN @RowsAffected;
    END
    
    -- Execução real: Finaliza os logs órfãos
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Atualiza logs órfãos SEM conexão ativa
        -- (usa último heartbeat como estimativa de fim)
        UPDATE la
        SET la.Log_DataHora_Fim = ISNULL(
            (SELECT TOP 1 uc.Usu_Last_Heartbeat 
             FROM Usuario_Conexao_WTS uc
             WHERE uc.Con_Codigo = la.Con_Codigo
               AND uc.Usu_Nome = SUBSTRING(la.Usu_Nome_Maquina, 1, CHARINDEX('@', la.Usu_Nome_Maquina + '@') - 1)
             ORDER BY uc.Usu_Last_Heartbeat DESC),
            -- Se não encontrou heartbeat, usa +1 hora após o início como estimativa
            DATEADD(HOUR, 1, la.Log_DataHora_Inicio)
        ),
        la.Log_Observacoes = COALESCE(la.Log_Observacoes + ' | ', '') + 
                            '⚠️ Finalizado automaticamente por limpeza de logs órfãos em ' + 
                            CONVERT(VARCHAR, GETDATE(), 120)
        FROM Log_Acesso_WTS la
        INNER JOIN @LogsParaFinalizar lpf ON la.Log_Id = lpf.Log_Id
        WHERE lpf.Possui_Conexao_Ativa = 0;  -- Apenas logs SEM conexão ativa
        
        DECLARE @LogsSemConexao INT = @@ROWCOUNT;
        
        -- Para logs COM conexão ativa, apenas adiciona observação (não finaliza)
        UPDATE la
        SET la.Log_Observacoes = COALESCE(la.Log_Observacoes + ' | ', '') + 
                                '⚠️ Log antigo mas conexão ainda ativa - verificado em ' + 
                                CONVERT(VARCHAR, GETDATE(), 120)
        FROM Log_Acesso_WTS la
        INNER JOIN @LogsParaFinalizar lpf ON la.Log_Id = lpf.Log_Id
        WHERE lpf.Possui_Conexao_Ativa = 1;  -- Apenas logs COM conexão ativa
        
        DECLARE @LogsComConexao INT = @@ROWCOUNT;
        
        COMMIT TRANSACTION;
        
        PRINT '';
        PRINT '✅ LIMPEZA CONCLUÍDA COM SUCESSO:';
        PRINT '   - Logs finalizados (sem conexão ativa): ' + CAST(@LogsSemConexao AS VARCHAR(10));
        PRINT '   - Logs marcados (ainda com conexão ativa): ' + CAST(@LogsComConexao AS VARCHAR(10));
        PRINT '   - Total processado: ' + CAST(@RowsAffected AS VARCHAR(10));
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
        DECLARE @ErrorState INT = ERROR_STATE();
        
        PRINT '';
        PRINT '❌ ERRO DURANTE A LIMPEZA:';
        PRINT '   ' + @ErrorMessage;
        
        RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState);
    END CATCH
    
    PRINT '================================================================';
    
    RETURN @RowsAffected;
END;

-- Mensagens de sucesso
PRINT '';
PRINT '✅ Stored Procedure [sp_Limpar_Logs_Orfaos] criada com sucesso!';
PRINT '';
PRINT '📖 COMO USAR:';
PRINT '   -- Simulação (mostra o que seria feito):';
PRINT '   EXEC sp_Limpar_Logs_Orfaos @SimularExecucao = 1;';
PRINT '';
PRINT '   -- Execução real (padrão: 24 horas):';
PRINT '   EXEC sp_Limpar_Logs_Orfaos;';
PRINT '';
PRINT '   -- Execução real (customizar limite de horas):';
PRINT '   EXEC sp_Limpar_Logs_Orfaos @HorasLimite = 12;';
PRINT '';
PRINT '💡 RECOMENDAÇÃO: Agende esta procedure para executar a cada 1-6 horas';
PRINT '   via SQL Server Agent Job para manutenção automática.';
PRINT '';

-- Exemplo de execução imediata em modo simulação
PRINT '🔍 Executando verificação inicial (simulação)...';
PRINT '';
EXEC sp_Limpar_Logs_Orfaos @SimularExecucao = 1;

-- ================================================================
-- STORED PROCEDURE: Limpar Logs de Acesso Órfãos
-- VERSÃO DBEAVER - Executar em 3 etapas separadas
-- ================================================================

-- ════════════════════════════════════════════════════════════════
-- ETAPA 1: Remover procedure existente (se houver)
-- Execute este bloco primeiro
-- ════════════════════════════════════════════════════════════════

USE WATS;

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sp_Limpar_Logs_Orfaos]') AND type in (N'P', N'PC'))
BEGIN
    DROP PROCEDURE [dbo].[sp_Limpar_Logs_Orfaos];
    PRINT 'Procedure sp_Limpar_Logs_Orfaos existente removida.';
END;

-- ════════════════════════════════════════════════════════════════
-- ETAPA 2: Criar a procedure
-- Execute este bloco depois da Etapa 1
-- ════════════════════════════════════════════════════════════════

CREATE PROCEDURE [dbo].[sp_Limpar_Logs_Orfaos]
    @HorasLimite INT = 24,
    @SimularExecucao BIT = 0
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
    
    SET @DataLimite = DATEADD(HOUR, -@HorasLimite, GETDATE());
    
    PRINT '================================================================';
    PRINT 'LIMPEZA DE LOGS DE ACESSO ÓRFÃOS';
    PRINT '================================================================';
    PRINT 'Data/Hora Atual: ' + CONVERT(VARCHAR, GETDATE(), 120);
    PRINT 'Data/Hora Limite: ' + CONVERT(VARCHAR, @DataLimite, 120);
    PRINT 'Modo: ' + CASE WHEN @SimularExecucao = 1 THEN 'SIMULAÇÃO (nada será alterado)' ELSE 'EXECUÇÃO REAL' END;
    PRINT '';
    
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
    WHERE la.Log_DataHora_Fim IS NULL
      AND la.Log_DataHora_Inicio < @DataLimite
    ORDER BY la.Log_DataHora_Inicio;
    
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
    
    IF @SimularExecucao = 1
    BEGIN
        PRINT '🔍 SIMULAÇÃO: Nenhuma alteração foi feita.';
        PRINT '   Para executar de verdade, chame: EXEC sp_Limpar_Logs_Orfaos @SimularExecucao = 0';
        PRINT '================================================================';
        RETURN @RowsAffected;
    END
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        UPDATE la
        SET la.Log_DataHora_Fim = ISNULL(
            (SELECT TOP 1 uc.Usu_Last_Heartbeat 
             FROM Usuario_Conexao_WTS uc
             WHERE uc.Con_Codigo = la.Con_Codigo
               AND uc.Usu_Nome = SUBSTRING(la.Usu_Nome_Maquina, 1, CHARINDEX('@', la.Usu_Nome_Maquina + '@') - 1)
             ORDER BY uc.Usu_Last_Heartbeat DESC),
            DATEADD(HOUR, 1, la.Log_DataHora_Inicio)
        ),
        la.Log_Observacoes = COALESCE(la.Log_Observacoes + ' | ', '') + 
                            '⚠️ Finalizado automaticamente por limpeza de logs órfãos em ' + 
                            CONVERT(VARCHAR, GETDATE(), 120)
        FROM Log_Acesso_WTS la
        INNER JOIN @LogsParaFinalizar lpf ON la.Log_Id = lpf.Log_Id
        WHERE lpf.Possui_Conexao_Ativa = 0;
        
        DECLARE @LogsSemConexao INT = @@ROWCOUNT;
        
        UPDATE la
        SET la.Log_Observacoes = COALESCE(la.Log_Observacoes + ' | ', '') + 
                                '⚠️ Log antigo mas conexão ainda ativa - verificado em ' + 
                                CONVERT(VARCHAR, GETDATE(), 120)
        FROM Log_Acesso_WTS la
        INNER JOIN @LogsParaFinalizar lpf ON la.Log_Id = lpf.Log_Id
        WHERE lpf.Possui_Conexao_Ativa = 1;
        
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

-- ════════════════════════════════════════════════════════════════
-- ETAPA 3: Testar a procedure (SIMULAÇÃO)
-- Execute este bloco depois da Etapa 2
-- ════════════════════════════════════════════════════════════════

PRINT '';
PRINT '✅ Stored Procedure criada com sucesso!';
PRINT '';
PRINT '🔍 Executando verificação inicial em modo SIMULAÇÃO...';
PRINT '';

EXEC sp_Limpar_Logs_Orfaos @SimularExecucao = 1;

-- ════════════════════════════════════════════════════════════════
-- ETAPA 4 (OPCIONAL): Executar limpeza REAL
-- Execute este bloco APENAS quando quiser limpar de verdade
-- ════════════════════════════════════════════════════════════════

-- EXEC sp_Limpar_Logs_Orfaos @SimularExecucao = 0;

-- ════════════════════════════════════════════════════════════════
-- 📖 GUIA DE USO NO DBEAVER
-- ════════════════════════════════════════════════════════════════
/*
INSTRUÇÕES:

1. Selecione TODO o código da ETAPA 1 e execute (Ctrl+Enter)
2. Selecione TODO o código da ETAPA 2 e execute (Ctrl+Enter)
3. Selecione TODO o código da ETAPA 3 e execute (Ctrl+Enter)
4. Se estiver tudo OK na simulação, descomente e execute ETAPA 4

COMANDOS ÚTEIS:

-- Ver logs órfãos sem executar nada:
EXEC sp_Limpar_Logs_Orfaos @SimularExecucao = 1;

-- Limpar logs órfãos de verdade (24 horas):
EXEC sp_Limpar_Logs_Orfaos;

-- Limpar logs órfãos mais recentes (12 horas):
EXEC sp_Limpar_Logs_Orfaos @HorasLimite = 12;

-- Verificar se a procedure existe:
SELECT * FROM sys.procedures WHERE name = 'sp_Limpar_Logs_Orfaos';

-- Ver logs sem data de fim:
SELECT 
    Log_Id,
    Usu_Nome_Maquina,
    Con_Nome_Acessado,
    Log_DataHora_Inicio,
    DATEDIFF(HOUR, Log_DataHora_Inicio, GETDATE()) AS Horas_Aberto
FROM Log_Acesso_WTS
WHERE Log_DataHora_Fim IS NULL
ORDER BY Log_DataHora_Inicio;
*/

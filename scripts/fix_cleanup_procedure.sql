-- ================================================================
-- FIX: Corrige erro de truncamento na sp_Limpar_Logs_Orfaos
-- ================================================================
USE WATS;
GO

-- Remove procedure existente
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sp_Limpar_Logs_Orfaos]') AND type in (N'P', N'PC'))
BEGIN
    DROP PROCEDURE [dbo].[sp_Limpar_Logs_Orfaos];
    PRINT 'Procedure existente removida.';
END;
GO

-- Recria procedure com mensagens mais curtas
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
    
    -- Identifica logs órfãos
    INSERT INTO @LogsParaFinalizar
    SELECT 
        la.Log_Id,
        la.Usu_Nome_Maquina,
        la.Con_Nome_Acessado,
        la.Log_DataHora_Inicio,
        CAST(DATEDIFF(MINUTE, la.Log_DataHora_Inicio, GETDATE()) / 60.0 AS DECIMAL(10,2)),
        CASE 
            WHEN EXISTS (
                SELECT 1 FROM Usuario_Conexao_WTS uc
                WHERE uc.Con_Codigo = la.Con_Codigo
                  AND uc.Usu_Nome = SUBSTRING(la.Usu_Nome_Maquina, 1, CHARINDEX('@', la.Usu_Nome_Maquina + '@') - 1)
            ) THEN 1
            ELSE 0
        END
    FROM Log_Acesso_WTS la
    WHERE la.Log_DataHora_Fim IS NULL
      AND la.Log_DataHora_Inicio < @DataLimite
    ORDER BY la.Log_DataHora_Inicio;
    
    SELECT @RowsAffected = COUNT(*) FROM @LogsParaFinalizar;
    
    IF @RowsAffected = 0
    BEGIN
        RETURN 0;
    END
    
    IF @SimularExecucao = 1
    BEGIN
        RETURN @RowsAffected;
    END
    
    -- Execução real
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Atualiza logs órfãos SEM conexão ativa (CORRIGIDO - mensagem mais curta)
        UPDATE la
        SET la.Log_DataHora_Fim = ISNULL(
            (SELECT TOP 1 uc.Usu_Last_Heartbeat 
             FROM Usuario_Conexao_WTS uc
             WHERE uc.Con_Codigo = la.Con_Codigo
               AND uc.Usu_Nome = SUBSTRING(la.Usu_Nome_Maquina, 1, CHARINDEX('@', la.Usu_Nome_Maquina + '@') - 1)
             ORDER BY uc.Usu_Last_Heartbeat DESC),
            DATEADD(HOUR, 1, la.Log_DataHora_Inicio)
        ),
        la.Log_Observacoes = LEFT(
            ISNULL(la.Log_Observacoes, '') + 
            CASE WHEN LEN(ISNULL(la.Log_Observacoes, '')) > 0 THEN ' | ' ELSE '' END +
            'Auto-finalizado ' + CONVERT(VARCHAR(16), GETDATE(), 120),
            1000
        )
        FROM Log_Acesso_WTS la
        INNER JOIN @LogsParaFinalizar lpf ON la.Log_Id = lpf.Log_Id
        WHERE lpf.Possui_Conexao_Ativa = 0;
        
        DECLARE @LogsSemConexao INT = @@ROWCOUNT;
        
        -- Logs COM conexão ativa apenas marca (CORRIGIDO - mensagem mais curta)
        UPDATE la
        SET la.Log_Observacoes = LEFT(
            ISNULL(la.Log_Observacoes, '') +
            CASE WHEN LEN(ISNULL(la.Log_Observacoes, '')) > 0 THEN ' | ' ELSE '' END +
            'Verificado ' + CONVERT(VARCHAR(16), GETDATE(), 120),
            1000
        )
        FROM Log_Acesso_WTS la
        INNER JOIN @LogsParaFinalizar lpf ON la.Log_Id = lpf.Log_Id
        WHERE lpf.Possui_Conexao_Ativa = 1;
        
        COMMIT TRANSACTION;
        
        RETURN @RowsAffected;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        DECLARE @ErrorMessage NVARCHAR(500) = LEFT(ERROR_MESSAGE(), 500);
        
        RAISERROR(@ErrorMessage, 16, 1);
        RETURN -1;
        
    END CATCH
END;
GO

PRINT 'Procedure sp_Limpar_Logs_Orfaos corrigida com sucesso!';
PRINT 'Mensagens de observacao reduzidas para evitar truncamento.';
GO

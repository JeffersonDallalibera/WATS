-- ================================================================
-- ADICIONAR COLUNA Log_Observacoes NA TABELA Log_Acesso_WTS
-- ================================================================
-- Este script adiciona a coluna Log_Observacoes se ela não existir
-- Compatível com: DBeaver, SSMS, Azure Data Studio
-- ================================================================

USE WATS;

-- Verifica se a coluna já existe
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
    PRINT 'Detalhes da coluna:';
    PRINT '  - Nome: Log_Observacoes';
    PRINT '  - Tipo: NVARCHAR(1000)';
    PRINT '  - Permite NULL: Sim';
    PRINT '  - Valor padrão: NULL';
END
ELSE
BEGIN
    PRINT '⚠️ A coluna Log_Observacoes já existe na tabela Log_Acesso_WTS.';
    PRINT '   Nenhuma alteração foi feita.';
END;

PRINT '';
PRINT '================================================================';

-- Mostra informações da coluna
SELECT 
    c.name AS [Nome_Coluna],
    t.name AS [Tipo_Dados],
    c.max_length AS [Tamanho_Maximo],
    c.is_nullable AS [Permite_NULL]
FROM sys.columns c
INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID(N'[dbo].[Log_Acesso_WTS]')
  AND c.name = 'Log_Observacoes';

PRINT '';
PRINT '✅ Script concluído!';
PRINT '';
PRINT '💡 Próximos passos:';
PRINT '   1. Execute o script cleanup_orphaned_access_logs.sql';
PRINT '   2. Teste com: EXEC sp_Limpar_Logs_Orfaos @SimularExecucao = 1';

-- ============================================================================
-- Script de Otimização de Índices - WATS
-- Data: 01/11/2025
-- Objetivo: Limpar índices antigos e criar apenas os necessários
-- ATENÇÃO: Este script remove TODOS os índices não-clustered customizados
--          e recria apenas os índices otimizados
-- ============================================================================

USE [WATS_DB]
GO

SET NOCOUNT ON;
GO

PRINT '============================================================================'
PRINT 'WATS - Otimização de Índices'
PRINT 'Passo 1: Limpeza de índices existentes'
PRINT 'Passo 2: Criação de índices otimizados'
PRINT '============================================================================'
PRINT ''

-- ============================================================================
-- PASSO 1: REMOVER ÍNDICES EXISTENTES (Customizados)
-- ============================================================================

PRINT '----------------------------------------------------------------------------'
PRINT 'PASSO 1: Removendo índices customizados existentes...'
PRINT '----------------------------------------------------------------------------'
PRINT ''

DECLARE @DropSQL NVARCHAR(MAX) = '';
DECLARE @TableName NVARCHAR(128);
DECLARE @IndexName NVARCHAR(128);
DECLARE @DroppedCount INT = 0;

-- Cursor para percorrer todos os índices customizados
DECLARE index_cursor CURSOR FOR
SELECT 
    OBJECT_NAME(i.object_id) AS TableName,
    i.name AS IndexName
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name LIKE '%_WTS'
  AND i.type_desc = 'NONCLUSTERED'  -- Apenas não-clustered
  AND i.is_primary_key = 0          -- Não remove PKs
  AND i.is_unique_constraint = 0    -- Não remove UQ constraints de FK
  AND i.name NOT LIKE 'FK_%'        -- Não remove índices de Foreign Keys
ORDER BY OBJECT_NAME(i.object_id), i.name;

OPEN index_cursor;
FETCH NEXT FROM index_cursor INTO @TableName, @IndexName;

WHILE @@FETCH_STATUS = 0
BEGIN
    BEGIN TRY
        SET @DropSQL = 'DROP INDEX [' + @IndexName + '] ON [dbo].[' + @TableName + ']';
        EXEC sp_executesql @DropSQL;
        PRINT '  ✓ Removido: ' + @IndexName + ' em ' + @TableName;
        SET @DroppedCount = @DroppedCount + 1;
    END TRY
    BEGIN CATCH
        PRINT '  ✗ ERRO ao remover: ' + @IndexName + ' em ' + @TableName + ' - ' + ERROR_MESSAGE();
    END CATCH
    
    FETCH NEXT FROM index_cursor INTO @TableName, @IndexName;
END

CLOSE index_cursor;
DEALLOCATE index_cursor;

PRINT ''
PRINT 'Total de índices removidos: ' + CAST(@DroppedCount AS VARCHAR(10))
PRINT ''

-- ============================================================================
-- PASSO 2: CRIAR ÍNDICES OTIMIZADOS
-- ============================================================================

PRINT '----------------------------------------------------------------------------'
PRINT 'PASSO 2: Criando índices otimizados...'
PRINT '----------------------------------------------------------------------------'
PRINT ''

-- ============================================================================
-- 1. TABELA: Usuario_Sistema_WTS
-- Queries frequentes: Autenticação, listagem de usuários
-- ============================================================================

PRINT '1. Criando índices para Usuario_Sistema_WTS...'

-- Índice para autenticação (WHERE Usu_Nome = ? AND Usu_Ativo = ?)
CREATE NONCLUSTERED INDEX IX_Usuario_Sistema_Nome_Ativo
ON Usuario_Sistema_WTS(Usu_Nome, Usu_Ativo)
INCLUDE (Usu_Id, Usu_Is_Admin, Usu_Email);
PRINT '  ✓ IX_Usuario_Sistema_Nome_Ativo criado'

-- Índice para ordenação por nome
CREATE NONCLUSTERED INDEX IX_Usuario_Sistema_Nome
ON Usuario_Sistema_WTS(Usu_Nome)
INCLUDE (Usu_Ativo, Usu_Is_Admin);
PRINT '  ✓ IX_Usuario_Sistema_Nome criado'

-- Índice para busca por Usu_Id (muito usado em JOINs)
CREATE NONCLUSTERED INDEX IX_Usuario_Sistema_Id
ON Usuario_Sistema_WTS(Usu_Id)
INCLUDE (Usu_Nome, Usu_Email, Usu_Ativo, Usu_Is_Admin);
PRINT '  ✓ IX_Usuario_Sistema_Id criado'

PRINT ''

-- ============================================================================
-- 2. TABELA: Conexao_WTS
-- Queries frequentes: Listagem de conexões, filtros por grupo
-- ============================================================================

PRINT '2. Criando índices para Conexao_WTS...'

-- Índice para filtros por grupo
CREATE NONCLUSTERED INDEX IX_Conexao_Grupo
ON Conexao_WTS(Gru_Codigo)
INCLUDE (Con_Codigo, Con_Nome, Con_IP, con_tipo);
PRINT '  ✓ IX_Conexao_Grupo criado'

-- Índice para ordenação por nome
CREATE NONCLUSTERED INDEX IX_Conexao_Nome
ON Conexao_WTS(Con_Nome)
INCLUDE (Con_IP, Gru_Codigo, con_tipo);
PRINT '  ✓ IX_Conexao_Nome criado'

-- Índice composto para filtros combinados
CREATE NONCLUSTERED INDEX IX_Conexao_Tipo_Grupo
ON Conexao_WTS(con_tipo, Gru_Codigo)
INCLUDE (Con_Codigo, Con_Nome, Con_IP);
PRINT '  ✓ IX_Conexao_Tipo_Grupo criado'

PRINT ''

-- ============================================================================
-- 3. TABELA: Permissao_Grupo_WTS
-- Queries frequentes: Verificação de permissões, JOINs
-- ============================================================================

PRINT '3. Criando índices para Permissao_Grupo_WTS...'

-- Índice para busca por usuário
CREATE NONCLUSTERED INDEX IX_Permissao_Grupo_Usuario
ON Permissao_Grupo_WTS(Usu_Id)
INCLUDE (Gru_Codigo);
PRINT '  ✓ IX_Permissao_Grupo_Usuario criado'

-- Índice para busca por grupo
CREATE NONCLUSTERED INDEX IX_Permissao_Grupo_Grupo
ON Permissao_Grupo_WTS(Gru_Codigo)
INCLUDE (Usu_Id);
PRINT '  ✓ IX_Permissao_Grupo_Grupo criado'

-- Índice composto único (evita duplicatas)
CREATE UNIQUE NONCLUSTERED INDEX UQ_Permissao_Grupo_Usuario_Grupo
ON Permissao_Grupo_WTS(Usu_Id, Gru_Codigo);
PRINT '  ✓ UQ_Permissao_Grupo_Usuario_Grupo criado'

PRINT ''

-- ============================================================================
-- 4. TABELA: Permissao_Conexao_Individual_WTS
-- Queries frequentes: Verificação de acesso, permissões temporárias
-- ============================================================================

PRINT '4. Criando índices para Permissao_Conexao_Individual_WTS...'

-- Índice CRÍTICO para verificação de acesso
CREATE NONCLUSTERED INDEX IX_Permissao_Individual_Usuario_Conexao_Ativo
ON Permissao_Conexao_Individual_WTS(Usu_Id, Con_Codigo, Ativo)
INCLUDE (Data_Inicio, Data_Fim, Id);
PRINT '  ✓ IX_Permissao_Individual_Usuario_Conexao_Ativo criado'

-- Índice para listagem por usuário
CREATE NONCLUSTERED INDEX IX_Permissao_Individual_Usuario
ON Permissao_Conexao_Individual_WTS(Usu_Id)
INCLUDE (Con_Codigo, Data_Inicio, Data_Fim, Ativo, Observacoes);
PRINT '  ✓ IX_Permissao_Individual_Usuario criado'

-- Índice para listagem por conexão
CREATE NONCLUSTERED INDEX IX_Permissao_Individual_Conexao
ON Permissao_Conexao_Individual_WTS(Con_Codigo)
INCLUDE (Usu_Id, Data_Inicio, Data_Fim, Ativo);
PRINT '  ✓ IX_Permissao_Individual_Conexao criado'

-- Índice filtrado para permissões temporárias ativas
CREATE NONCLUSTERED INDEX IX_Permissao_Individual_Temporarias_Ativas
ON Permissao_Conexao_Individual_WTS(Data_Inicio, Data_Fim)
INCLUDE (Usu_Id, Con_Codigo)
WHERE Ativo = 1 AND Data_Fim IS NOT NULL;
PRINT '  ✓ IX_Permissao_Individual_Temporarias_Ativas criado'

-- Índice único (evita duplicatas de permissão)
CREATE UNIQUE NONCLUSTERED INDEX UQ_Permissao_Individual_Usuario_Conexao
ON Permissao_Conexao_Individual_WTS(Usu_Id, Con_Codigo);
PRINT '  ✓ UQ_Permissao_Individual_Usuario_Conexao criado'

PRINT ''

-- ============================================================================
-- 5. TABELA: Usuario_Conexao_WTS
-- Queries frequentes: Heartbeat updates, listagem de conexões ativas
-- ============================================================================

PRINT '5. Criando índices para Usuario_Conexao_WTS...'

-- Índice CRÍTICO para heartbeat (query mais frequente!)
CREATE NONCLUSTERED INDEX IX_Usuario_Conexao_Heartbeat
ON Usuario_Conexao_WTS(Con_Codigo, Usu_Nome)
INCLUDE (Usu_Last_Heartbeat, Usu_Dat_Conexao);
PRINT '  ✓ IX_Usuario_Conexao_Heartbeat criado'

-- Índice para limpeza de conexões fantasmas
CREATE NONCLUSTERED INDEX IX_Usuario_Conexao_Last_Heartbeat
ON Usuario_Conexao_WTS(Usu_Last_Heartbeat)
INCLUDE (Con_Codigo, Usu_Nome);
PRINT '  ✓ IX_Usuario_Conexao_Last_Heartbeat criado'

PRINT ''

-- ============================================================================
-- 6. TABELA: Log_Acesso_WTS
-- Queries frequentes: Relatórios, auditoria
-- ============================================================================

PRINT '6. Criando índices para Log_Acesso_WTS...'

-- Índice para ordenação DESC (relatórios mais recentes primeiro)
CREATE NONCLUSTERED INDEX IX_Log_Acesso_DataInicio
ON Log_Acesso_WTS(Log_DataHora_Inicio DESC)
INCLUDE (Con_Codigo, Usu_Nome_Maquina, Log_DataHora_Fim);
PRINT '  ✓ IX_Log_Acesso_DataInicio criado'

-- Índice para filtros por usuário
CREATE NONCLUSTERED INDEX IX_Log_Acesso_Usuario
ON Log_Acesso_WTS(Usu_Nome_Maquina, Log_DataHora_Inicio);
PRINT '  ✓ IX_Log_Acesso_Usuario criado'

-- Índice para filtros por conexão
CREATE NONCLUSTERED INDEX IX_Log_Acesso_Conexao
ON Log_Acesso_WTS(Con_Codigo, Log_DataHora_Inicio);
PRINT '  ✓ IX_Log_Acesso_Conexao criado'

PRINT ''

-- ============================================================================
-- 7. TABELA: Sessao_Protecao_WTS
-- Queries frequentes: Verificação de senha, sessões ativas
-- ============================================================================

PRINT '7. Criando índices para Sessao_Protecao_WTS...'

-- Índice CRÍTICO para verificação de sessões ativas
CREATE NONCLUSTERED INDEX IX_Sessao_Protecao_Conexao_Status
ON Sessao_Protecao_WTS(Con_Codigo, Prot_Status)
INCLUDE (Prot_Senha, Prot_Data_Expiracao, Usu_Nome_Criador);
PRINT '  ✓ IX_Sessao_Protecao_Conexao_Status criado'

-- Índice filtrado para sessões ativas (menor e mais rápido)
CREATE NONCLUSTERED INDEX IX_Sessao_Protecao_Ativas
ON Sessao_Protecao_WTS(Prot_Data_Expiracao)
INCLUDE (Con_Codigo, Prot_Senha, Usu_Nome_Criador)
WHERE Prot_Status = 'ATIVA';
PRINT '  ✓ IX_Sessao_Protecao_Ativas criado'

-- Índice para histórico por usuário
CREATE NONCLUSTERED INDEX IX_Sessao_Protecao_Usuario
ON Sessao_Protecao_WTS(Usu_Nome_Criador, Prot_Data_Criacao);
PRINT '  ✓ IX_Sessao_Protecao_Usuario criado'

-- Índice para limpeza de sessões expiradas
CREATE NONCLUSTERED INDEX IX_Sessao_Protecao_Expiracao
ON Sessao_Protecao_WTS(Prot_Data_Expiracao, Prot_Status);
PRINT '  ✓ IX_Sessao_Protecao_Expiracao criado'

PRINT ''

-- ============================================================================
-- 8. TABELA: Log_Tentativa_Protecao_WTS
-- Queries frequentes: Auditoria de tentativas de acesso
-- ============================================================================

PRINT '8. Criando índices para Log_Tentativa_Protecao_WTS...'

-- Índice para auditoria por sessão
CREATE NONCLUSTERED INDEX IX_Log_Tentativa_Protecao_Sessao
ON Log_Tentativa_Protecao_WTS(Prot_Id, LTent_Data_Hora);
PRINT '  ✓ IX_Log_Tentativa_Protecao_Sessao criado'

-- Índice para auditoria por conexão
CREATE NONCLUSTERED INDEX IX_Log_Tentativa_Protecao_Conexao
ON Log_Tentativa_Protecao_WTS(Con_Codigo, LTent_Data_Hora);
PRINT '  ✓ IX_Log_Tentativa_Protecao_Conexao criado'

PRINT ''

-- ============================================================================
-- 9. TABELA: Config_Sistema_WTS
-- Queries frequentes: Lookup de configurações por chave
-- ============================================================================

PRINT '9. Criando índices para Config_Sistema_WTS...'

-- Índice único para lookup por chave
CREATE UNIQUE NONCLUSTERED INDEX UQ_Config_Sistema_Chave
ON Config_Sistema_WTS(Config_Chave);
PRINT '  ✓ UQ_Config_Sistema_Chave criado'

PRINT ''

-- ============================================================================
-- PASSO 3: ATUALIZAR ESTATÍSTICAS
-- ============================================================================

PRINT '----------------------------------------------------------------------------'
PRINT 'PASSO 3: Atualizando estatísticas...'
PRINT '----------------------------------------------------------------------------'
PRINT ''

UPDATE STATISTICS Usuario_Sistema_WTS WITH FULLSCAN;
PRINT '  ✓ Estatísticas de Usuario_Sistema_WTS atualizadas'

UPDATE STATISTICS Conexao_WTS WITH FULLSCAN;
PRINT '  ✓ Estatísticas de Conexao_WTS atualizadas'

UPDATE STATISTICS Permissao_Grupo_WTS WITH FULLSCAN;
PRINT '  ✓ Estatísticas de Permissao_Grupo_WTS atualizadas'

UPDATE STATISTICS Permissao_Conexao_Individual_WTS WITH FULLSCAN;
PRINT '  ✓ Estatísticas de Permissao_Conexao_Individual_WTS atualizadas'

UPDATE STATISTICS Usuario_Conexao_WTS WITH FULLSCAN;
PRINT '  ✓ Estatísticas de Usuario_Conexao_WTS atualizadas'

UPDATE STATISTICS Log_Acesso_WTS WITH FULLSCAN;
PRINT '  ✓ Estatísticas de Log_Acesso_WTS atualizadas'

UPDATE STATISTICS Sessao_Protecao_WTS WITH FULLSCAN;
PRINT '  ✓ Estatísticas de Sessao_Protecao_WTS atualizadas'

UPDATE STATISTICS Log_Tentativa_Protecao_WTS WITH FULLSCAN;
PRINT '  ✓ Estatísticas de Log_Tentativa_Protecao_WTS atualizadas'

UPDATE STATISTICS Config_Sistema_WTS WITH FULLSCAN;
PRINT '  ✓ Estatísticas de Config_Sistema_WTS atualizadas'

PRINT ''

-- ============================================================================
-- PASSO 4: VALIDAÇÃO FINAL
-- ============================================================================

PRINT '----------------------------------------------------------------------------'
PRINT 'PASSO 4: Validação final...'
PRINT '----------------------------------------------------------------------------'
PRINT ''

-- Contar índices criados
DECLARE @IndexCount INT;
SELECT @IndexCount = COUNT(*)
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name LIKE '%_WTS'
  AND i.type_desc = 'NONCLUSTERED'
  AND (i.name LIKE 'IX_%' OR i.name LIKE 'UQ_%');

PRINT 'Total de índices customizados ativos: ' + CAST(@IndexCount AS VARCHAR(10))
PRINT ''

-- Listar todos os índices criados
PRINT 'Índices criados por tabela:'
PRINT ''

SELECT
    t.name AS TableName,
    i.name AS IndexName,
    i.type_desc AS IndexType,
    CASE WHEN i.is_unique = 1 THEN 'UNIQUE' ELSE '' END AS IsUnique,
    CASE WHEN i.has_filter = 1 THEN i.filter_definition ELSE '' END AS FilterDefinition
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name LIKE '%_WTS'
  AND i.type_desc = 'NONCLUSTERED'
  AND (i.name LIKE 'IX_%' OR i.name LIKE 'UQ_%')
ORDER BY t.name, i.name;

PRINT ''
PRINT '============================================================================'
PRINT 'Otimização de índices concluída com sucesso!'
PRINT '============================================================================'
PRINT ''
PRINT 'Próximos passos recomendados:'
PRINT '1. Testar queries críticas e verificar execution plans'
PRINT '2. Monitorar uso dos índices após 1 semana'
PRINT '3. Verificar fragmentação mensalmente'
PRINT ''
PRINT 'Para monitorar uso dos índices:'
PRINT 'SELECT * FROM sys.dm_db_index_usage_stats WHERE database_id = DB_ID(''WATS_DB'')'
PRINT ''

GO

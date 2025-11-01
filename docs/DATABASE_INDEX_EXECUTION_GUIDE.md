# 🗄️ Guia de Execução - Otimização de Índices no Banco WATS

## 📋 Informações Gerais

**Arquivo**: `scripts/optimize_database_indexes.sql`  
**Banco de Dados**: WATS (SQL Server)  
**Tempo Estimado**: 2-5 minutos  
**Privilégios Necessários**: `db_ddladmin` ou `db_owner`  
**Impacto**: BAIXO (somente criação de índices, sem alteração de dados)

---

## ⚠️ Pré-requisitos

### 1. Backup OBRIGATÓRIO

**NUNCA execute DDL sem backup!**

```sql
-- Backup completo
BACKUP DATABASE [WATS]
TO DISK = 'C:\Backup\WATS_PreIndex_20250101.bak'
WITH COMPRESSION, STATS = 10;

-- Verificar backup
RESTORE VERIFYONLY
FROM DISK = 'C:\Backup\WATS_PreIndex_20250101.bak';
```

### 2. Verificar Espaço Disponível

```sql
-- Verificar espaço livre no banco
EXEC sp_spaceused;

-- Detalhes por tabela
SELECT
    t.name AS TableName,
    p.rows AS RowCount,
    SUM(a.total_pages) * 8 / 1024 AS TotalSpaceMB,
    SUM(a.used_pages) * 8 / 1024 AS UsedSpaceMB,
    (SUM(a.total_pages) - SUM(a.used_pages)) * 8 / 1024 AS UnusedSpaceMB
FROM sys.tables t
INNER JOIN sys.indexes i ON t.object_id = i.object_id
INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
WHERE t.name LIKE '%_WTS'
GROUP BY t.name, p.rows
ORDER BY TotalSpaceMB DESC;
```

**Espaço Necessário**: ~10-20% do tamanho atual das tabelas (para os índices).

### 3. Janela de Manutenção

**Recomendação**: Executar em horário de baixo uso (madrugada ou fim de semana).

**Por quê?**:

- Criação de índices pode gerar locks temporários
- Pode impactar queries em execução
- Atualização de estatísticas é intensiva em I/O

---

## 🚀 Execução do Script

### Passo 1: Conectar ao Banco

```sql
-- SQL Server Management Studio (SSMS)
-- Ou Azure Data Studio

USE [WATS];
GO

-- Verificar conexão
SELECT @@SERVERNAME AS ServerName, DB_NAME() AS DatabaseName;
```

### Passo 2: Executar Script de Índices

**Opção A: Execução Completa (Recomendado)**

```sql
-- Abrir arquivo no SSMS
-- scripts/optimize_database_indexes.sql
-- Pressionar F5 ou clicar em "Execute"
```

**Opção B: Execução Seletiva (Por Tabela)**

Caso prefira criar índices por partes:

```sql
-- 1. Começar com tabelas críticas
-- Usuario_Sistema_WTS (autenticação)
-- Execute seção correspondente no script

-- 2. Permissões
-- Permissao_Grupo_WTS
-- Permissao_Conexao_Individual_WTS
-- Execute seções correspondentes

-- 3. Heartbeat e conexões
-- Usuario_Conexao_WTS
-- Conexao_WTS

-- 4. Logs e proteção
-- Log_Acesso_WTS
-- Sessao_Protecao_WTS
-- Log_Tentativa_Protecao_WTS

-- 5. Configurações
-- Config_Sistema_WTS
```

### Passo 3: Validar Criação dos Índices

```sql
-- Verificar todos os índices criados
SELECT
    t.name AS TableName,
    i.name AS IndexName,
    i.type_desc AS IndexType,
    i.is_unique AS IsUnique,
    i.fill_factor AS FillFactor,
    CASE WHEN i.has_filter = 1 THEN i.filter_definition ELSE '' END AS FilterDefinition
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name LIKE '%_WTS'
  AND (i.name LIKE 'IX_%' OR i.name LIKE 'UQ_%')
ORDER BY t.name, i.name;

-- Deve retornar 27+ índices
```

**Resultado Esperado**:

```
TableName                          | IndexName                                     | IndexType
-----------------------------------|-----------------------------------------------|------------------
Conexao_WTS                        | IX_Conexao_Grupo                              | NONCLUSTERED
Conexao_WTS                        | IX_Conexao_Nome                               | NONCLUSTERED
Conexao_WTS                        | IX_Conexao_Tipo                               | NONCLUSTERED
Config_Sistema_WTS                 | UQ_Config_Sistema_Chave                       | NONCLUSTERED
Log_Acesso_WTS                     | IX_Log_Acesso_Conexao                         | NONCLUSTERED
Log_Acesso_WTS                     | IX_Log_Acesso_DataInicio                      | NONCLUSTERED
Log_Acesso_WTS                     | IX_Log_Acesso_Usuario                         | NONCLUSTERED
Log_Tentativa_Protecao_WTS         | IX_Log_Tentativa_Protecao_Conexao             | NONCLUSTERED
Log_Tentativa_Protecao_WTS         | IX_Log_Tentativa_Protecao_Sessao              | NONCLUSTERED
Permissao_Conexao_Individual_WTS   | IX_Permissao_Individual_Conexao               | NONCLUSTERED
Permissao_Conexao_Individual_WTS   | IX_Permissao_Individual_Temporarias_Ativas    | NONCLUSTERED (filtered)
Permissao_Conexao_Individual_WTS   | IX_Permissao_Individual_Usuario                | NONCLUSTERED
Permissao_Conexao_Individual_WTS   | IX_Permissao_Individual_Usuario_Conexao_Ativo  | NONCLUSTERED
Permissao_Conexao_Individual_WTS   | UQ_Permissao_Individual_Usuario_Conexao        | NONCLUSTERED (unique)
Permissao_Grupo_WTS                | IX_Permissao_Grupo_Grupo_Usuario               | NONCLUSTERED
Permissao_Grupo_WTS                | IX_Permissao_Grupo_Usuario_Grupo               | NONCLUSTERED
Permissao_Grupo_WTS                | UQ_Permissao_Grupo_Usuario_Grupo               | NONCLUSTERED (unique)
Sessao_Protecao_WTS                | IX_Sessao_Protecao_Ativas                      | NONCLUSTERED (filtered)
Sessao_Protecao_WTS                | IX_Sessao_Protecao_Conexao_Status              | NONCLUSTERED
Sessao_Protecao_WTS                | IX_Sessao_Protecao_Expiracao                   | NONCLUSTERED
Sessao_Protecao_WTS                | IX_Sessao_Protecao_Usuario                     | NONCLUSTERED
Usuario_Conexao_WTS                | IX_Usuario_Conexao_Heartbeat                   | NONCLUSTERED
Usuario_Conexao_WTS                | IX_Usuario_Conexao_Last_Heartbeat              | NONCLUSTERED
Usuario_Sistema_WTS                | IX_Usuario_Sistema_Ativo                       | NONCLUSTERED
Usuario_Sistema_WTS                | IX_Usuario_Sistema_Email                       | NONCLUSTERED
Usuario_Sistema_WTS                | IX_Usuario_Sistema_Nome_Ativo                  | NONCLUSTERED
(27 rows)
```

### Passo 4: Atualizar Estatísticas

```sql
-- Atualiza estatísticas de todas as tabelas
EXEC sp_updatestats;

-- Ou atualizar por tabela (mais controle)
UPDATE STATISTICS Usuario_Sistema_WTS WITH FULLSCAN;
UPDATE STATISTICS Conexao_WTS WITH FULLSCAN;
UPDATE STATISTICS Permissao_Grupo_WTS WITH FULLSCAN;
UPDATE STATISTICS Permissao_Conexao_Individual_WTS WITH FULLSCAN;
UPDATE STATISTICS Usuario_Conexao_WTS WITH FULLSCAN;
UPDATE STATISTICS Log_Acesso_WTS WITH FULLSCAN;
UPDATE STATISTICS Sessao_Protecao_WTS WITH FULLSCAN;
UPDATE STATISTICS Log_Tentativa_Protecao_WTS WITH FULLSCAN;
UPDATE STATISTICS Config_Sistema_WTS WITH FULLSCAN;
```

---

## 📊 Validação de Performance

### Antes e Depois

**Query de Teste 1: Autenticação**

```sql
SET STATISTICS IO ON;
SET STATISTICS TIME ON;

-- Query de login (executar antes e depois)
SELECT Usu_Id, Usu_Nome, Usu_Is_Admin, Usu_Email
FROM Usuario_Sistema_WTS
WHERE Usu_Nome = 'admin' AND Usu_Ativo = 1;

-- Verificar "logical reads" e "CPU time"
-- Antes: 10-20 logical reads
-- Depois: 2-3 logical reads (usando índice)
```

**Query de Teste 2: Listagem de Conexões**

```sql
-- Query de listagem (não-admin)
SELECT
    Con.Con_Codigo, Con.Con_IP, Con.Con_Nome, Gru.Gru_Nome
FROM Conexao_WTS Con
LEFT JOIN Grupo_WTS Gru ON Con.Gru_Codigo = Gru.Gru_Codigo
WHERE EXISTS (
    SELECT 1 FROM Permissao_Grupo_WTS p
    WHERE p.Usu_Id = 123 AND p.Gru_Codigo = Con.Gru_Codigo
);

-- Verificar execution plan (Ctrl+L no SSMS)
-- Deve usar: IX_Permissao_Grupo_Usuario_Grupo, IX_Conexao_Grupo
```

**Query de Teste 3: Heartbeat Update**

```sql
-- Query de heartbeat (mais frequente!)
UPDATE Usuario_Conexao_WTS
SET Usu_Last_Heartbeat = GETDATE()
WHERE Con_Codigo = 456 AND Usu_Nome = 'user123';

-- Verificar execution plan
-- Deve usar: IX_Usuario_Conexao_Heartbeat (seek)
-- Antes: Table Scan (ruim)
-- Depois: Index Seek (ótimo)
```

### Análise de Execution Plans

**Como Analisar**:

1. No SSMS, pressione `Ctrl+M` para ativar "Include Actual Execution Plan"
2. Execute a query
3. Clique na aba "Execution Plan"
4. Procure por:
   - ✅ **Index Seek** (ótimo)
   - ⚠️ **Index Scan** (aceitável, mas pode melhorar)
   - ❌ **Table Scan** (ruim, significa que índice não está sendo usado)

**Exemplo de Bom Execution Plan**:

```
|-- Nested Loops (Inner Join)
    |-- Index Seek (IX_Permissao_Grupo_Usuario_Grupo) <-- ✅ ÓTIMO
    |-- Index Seek (IX_Conexao_Grupo)                  <-- ✅ ÓTIMO
```

---

## 🔍 Monitoramento

### Verificar Uso dos Índices (Após 1 Semana)

```sql
-- Estatísticas de uso
SELECT
    OBJECT_NAME(s.object_id) AS TableName,
    i.name AS IndexName,
    s.user_seeks AS UserSeeks,
    s.user_scans AS UserScans,
    s.user_lookups AS UserLookups,
    s.user_updates AS UserUpdates,
    s.last_user_seek AS LastSeek,
    s.last_user_scan AS LastScan,
    CASE
        WHEN s.user_updates > 0
        THEN CAST((s.user_seeks + s.user_scans + s.user_lookups) AS FLOAT) / s.user_updates
        ELSE -1
    END AS ReadWriteRatio
FROM sys.dm_db_index_usage_stats s
INNER JOIN sys.indexes i ON s.object_id = i.object_id AND s.index_id = i.index_id
WHERE s.database_id = DB_ID('WATS')
  AND OBJECTPROPERTY(s.object_id, 'IsUserTable') = 1
  AND (i.name LIKE 'IX_%' OR i.name LIKE 'UQ_%')
ORDER BY (s.user_seeks + s.user_scans + s.user_lookups) DESC;
```

**Interpretação**:

- **UserSeeks + UserScans > 0**: Índice está sendo usado ✅
- **ReadWriteRatio > 1**: Índice é benéfico (mais leituras que escritas)
- **ReadWriteRatio < 0.5**: Considerar remover índice (overhead de update)

### Verificar Fragmentação (Mensal)

```sql
SELECT
    OBJECT_NAME(ips.object_id) AS TableName,
    i.name AS IndexName,
    ips.index_type_desc AS IndexType,
    ips.avg_fragmentation_in_percent AS FragmentationPercent,
    ips.page_count AS PageCount
FROM sys.dm_db_index_physical_stats(DB_ID('WATS'), NULL, NULL, NULL, 'SAMPLED') ips
INNER JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
WHERE ips.avg_fragmentation_in_percent > 10
  AND ips.page_count > 100  -- Só índices com >100 páginas
ORDER BY ips.avg_fragmentation_in_percent DESC;
```

**Ações**:

- **Fragmentação 10-30%**: `ALTER INDEX ... REORGANIZE` (online, rápido)
- **Fragmentação >30%**: `ALTER INDEX ... REBUILD` (offline, mais lento)

---

## 🔧 Manutenção

### Reorganizar Índices (Online - Semanal)

```sql
-- Reorganiza todos os índices com fragmentação >10%
DECLARE @sql NVARCHAR(MAX) = '';

SELECT @sql += 'ALTER INDEX [' + i.name + '] ON [' + OBJECT_NAME(ips.object_id) + '] REORGANIZE; '
FROM sys.dm_db_index_physical_stats(DB_ID('WATS'), NULL, NULL, NULL, 'SAMPLED') ips
INNER JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
WHERE ips.avg_fragmentation_in_percent > 10
  AND ips.avg_fragmentation_in_percent < 30
  AND ips.page_count > 100;

PRINT @sql;  -- Verificar antes de executar
EXEC sp_executesql @sql;
```

### Rebuild Índices (Offline - Mensal)

```sql
-- Rebuild índices com fragmentação >30%
DECLARE @sql NVARCHAR(MAX) = '';

SELECT @sql += 'ALTER INDEX [' + i.name + '] ON [' + OBJECT_NAME(ips.object_id) + '] REBUILD WITH (ONLINE = OFF, FILLFACTOR = 90); '
FROM sys.dm_db_index_physical_stats(DB_ID('WATS'), NULL, NULL, NULL, 'SAMPLED') ips
INNER JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
WHERE ips.avg_fragmentation_in_percent >= 30
  AND ips.page_count > 100;

PRINT @sql;
EXEC sp_executesql @sql;
```

### Atualizar Estatísticas (Semanal)

```sql
-- Atualizar apenas tabelas com atividade
UPDATE STATISTICS Usuario_Sistema_WTS WITH FULLSCAN;
UPDATE STATISTICS Permissao_Grupo_WTS WITH FULLSCAN;
UPDATE STATISTICS Permissao_Conexao_Individual_WTS WITH FULLSCAN;
UPDATE STATISTICS Usuario_Conexao_WTS WITH FULLSCAN;  -- Alta atividade (heartbeat)
UPDATE STATISTICS Log_Acesso_WTS WITH FULLSCAN;
```

---

## ⏮️ Rollback

### Remover Todos os Índices Criados

**⚠️ Use SOMENTE se houver problemas graves!**

```sql
USE [WATS];
GO

-- BACKUP PRIMEIRO!
BACKUP DATABASE [WATS]
TO DISK = 'C:\Backup\WATS_PreRollback_20250101.bak'
WITH COMPRESSION;

-- Script de rollback
DECLARE @sql NVARCHAR(MAX) = '';

-- Remove índices customizados (mantém PKs e FKs!)
SELECT @sql += 'DROP INDEX [' + i.name + '] ON [' + OBJECT_NAME(i.object_id) + ']; '
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name LIKE '%_WTS'
  AND (i.name LIKE 'IX_%' OR i.name LIKE 'UQ_Config%')  -- Só nossos índices
  AND i.is_primary_key = 0  -- Não remove PK
  AND i.is_unique_constraint = 0;  -- Não remove UQ constraints originais

-- Verificar SQL gerado
PRINT @sql;

-- Executar (CUIDADO!)
-- EXEC sp_executesql @sql;
```

### Remover Índice Específico

```sql
-- Remover apenas um índice problemático
DROP INDEX IX_Usuario_Conexao_Heartbeat ON Usuario_Conexao_WTS;
```

---

## 📋 Checklist de Execução

### Antes da Execução

- [ ] Backup do banco criado e verificado
- [ ] Espaço disponível verificado (>20% do tamanho das tabelas)
- [ ] Janela de manutenção agendada (horário de baixo uso)
- [ ] Privilégios de DBA confirmados (`db_ddladmin` ou superior)
- [ ] Script `optimize_database_indexes.sql` revisado
- [ ] Stakeholders notificados (downtime potencial)

### Durante a Execução

- [ ] Conectado ao banco correto (`USE [WATS]`)
- [ ] Script executado com sucesso (sem erros)
- [ ] 27+ índices criados (query de validação)
- [ ] Estatísticas atualizadas (`sp_updatestats`)

### Após a Execução

- [ ] Queries de teste executadas (antes/depois comparados)
- [ ] Execution plans analisados (Index Seeks confirmados)
- [ ] Performance melhorada (logical reads reduzidos)
- [ ] Aplicação WATS testada (funcionalidade normal)
- [ ] Monitoramento ativado (uso dos índices)
- [ ] Documentação atualizada (data de execução, resultados)

### Após 1 Semana

- [ ] Uso dos índices verificado (DMVs consultadas)
- [ ] Índices não usados identificados (se houver)
- [ ] Fragmentação medida (baseline estabelecida)
- [ ] Performance monitorada (comparação com baseline)

---

## 📞 Suporte

**Problemas Durante a Execução**:

1. **Erro: "Cannot create index... duplicate key"**

   - Causa: Dados duplicados na tabela
   - Solução: Verificar constraint unique, limpar duplicatas primeiro

2. **Erro: "Insufficient disk space"**

   - Causa: Pouco espaço livre no disco
   - Solução: Limpar espaço ou adicionar disco

3. **Erro: "Permission denied"**

   - Causa: Usuário sem privilégios DDL
   - Solução: Usar conta com `db_ddladmin` ou `db_owner`

4. **Performance piorou após índices**
   - Causa: Estatísticas desatualizadas ou índice inadequado
   - Solução: `EXEC sp_updatestats`, verificar execution plans

**Logs de Erro**:

```sql
-- Verificar erros recentes no SQL Server
EXEC xp_readerrorlog 0, 1, 'index';
```

---

## 📚 Referências

- **Documentação Oficial**: [SQL Server Index Design Guide](https://docs.microsoft.com/en-us/sql/relational-databases/sql-server-index-design-guide)
- **Best Practices**: [Indexing Best Practices](https://docs.microsoft.com/en-us/sql/relational-databases/indexes/indexes)
- **DMVs**: [Index Usage Statistics](https://docs.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-views/sys-dm-db-index-usage-stats-transact-sql)
- **WATS Docs**: `docs/PERFORMANCE_OPTIMIZATIONS_APPLIED.md`

---

**Autor**: GitHub Copilot  
**Data**: 01/11/2025  
**Versão**: 1.0  
**Status**: Pronto para Execução

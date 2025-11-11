/*
================================================================================
STORED PROCEDURE: sp_Relatorio_Conexoes
================================================================================
Descrição:
    Gera relatório detalhado de conexões com filtros por período, usuário e conexão.
    
Parâmetros:
    @DataInicio      DATETIME - Data/hora inicial do período (obrigatório)
    @DataFim         DATETIME - Data/hora final do período (obrigatório)
    @Usuario         NVARCHAR(100) - Nome do usuário (NULL = todos)
    @Conexao         NVARCHAR(255) - Nome da conexão (NULL = todas)
    @ApenasAtivas    BIT - 1 = apenas conexões ativas, 0 = todas (padrão: 0)

Campos retornados:
    - Log_ID: ID do log de acesso
    - Nome_Usuario: Nome do usuário da máquina que conectou
    - Nome_Conexao: Nome da conexão utilizada
    - IP_Servidor: IP do servidor de destino
    - Tipo_Conexao: Tipo de conexão (RDP, SSH, etc)
    - Usuario_Conexao: Usuário utilizado na conexão
    - Cliente: Nome do cliente (se informado)
    - Grupo: Nome do grupo da conexão
    - Data_Inicio: Data/hora de início da conexão
    - Data_Fim: Data/hora de fim da conexão
    - Duracao_Minutos: Tempo total de conexão em minutos
    - Duracao_Formatada: Duração formatada (HH:mm:ss)
    - Status: Status da conexão (Ativa/Finalizada/Órfã Limpa)
    - Observacoes: Observações sobre a conexão

Exemplos de uso:
    -- Relatório de todas as conexões de hoje
    EXEC sp_Relatorio_Conexoes 
        @DataInicio = '2024-01-01 00:00:00',
        @DataFim = '2024-01-01 23:59:59'
    
    -- Relatório de um usuário específico
    EXEC sp_Relatorio_Conexoes 
        @DataInicio = '2024-01-01',
        @DataFim = '2024-01-31',
        @Usuario = 'Jefferson'
    
    -- Apenas conexões ativas
    EXEC sp_Relatorio_Conexoes 
        @DataInicio = '2024-01-01',
        @DataFim = GETDATE(),
        @ApenasAtivas = 1
    
    -- Conexão específica no último mês
    EXEC sp_Relatorio_Conexoes 
        @DataInicio = DATEADD(MONTH, -1, GETDATE()),
        @DataFim = GETDATE(),
        @Conexao = 'Servidor Produção'

Autor: Sistema WATS
Data: 2024-11-07
================================================================================
*/

-- ============================================================================
-- PASSO 1: Remover procedure existente (se houver)
-- ============================================================================
IF OBJECT_ID('dbo.sp_Relatorio_Conexoes', 'P') IS NOT NULL
BEGIN
    DROP PROCEDURE dbo.sp_Relatorio_Conexoes;
    PRINT 'Procedure sp_Relatorio_Conexoes removida com sucesso.';
END
ELSE
BEGIN
    PRINT 'Procedure sp_Relatorio_Conexoes não existia. Criando nova...';
END


-- ============================================================================
-- PASSO 2: Criar nova procedure
-- ============================================================================
CREATE PROCEDURE dbo.sp_Relatorio_Conexoes
    @DataInicio      DATETIME,
    @DataFim         DATETIME,
    @Usuario         NVARCHAR(100) = NULL,
    @Conexao         NVARCHAR(255) = NULL,
    @ApenasAtivas    BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Validação de parâmetros
    IF @DataInicio IS NULL OR @DataFim IS NULL
    BEGIN
        RAISERROR('Os parâmetros @DataInicio e @DataFim são obrigatórios.', 16, 1);
        RETURN;
    END
    
    IF @DataInicio > @DataFim
    BEGIN
        RAISERROR('A data inicial não pode ser maior que a data final.', 16, 1);
        RETURN;
    END
    
    -- Query principal do relatório
    SELECT 
        LA.Log_Id AS Log_ID,
        LA.Usu_Nome_Maquina AS Nome_Usuario,
        ISNULL(LA.Con_Nome_Acessado, C.con_nome) AS Nome_Conexao,
        C.con_ip AS IP_Servidor,
        ISNULL(LA.Log_Tipo_Conexao, C.con_tipo) AS Tipo_Conexao,
        C.con_usuario AS Usuario_Conexao,
        C.con_cliente AS Cliente,
        G.Gru_Nome AS Grupo,
        LA.Log_DataHora_Inicio AS Data_Inicio,
        LA.Log_DataHora_Fim AS Data_Fim,
        
        -- Cálculo da duração em minutos
        CASE 
            WHEN LA.Log_DataHora_Fim IS NOT NULL THEN 
                DATEDIFF(MINUTE, LA.Log_DataHora_Inicio, LA.Log_DataHora_Fim)
            ELSE 
                DATEDIFF(MINUTE, LA.Log_DataHora_Inicio, GETDATE())
        END AS Duracao_Minutos,
        
        -- Duração formatada como HH:mm:ss
        CASE 
            WHEN LA.Log_DataHora_Fim IS NOT NULL THEN 
                CONVERT(VARCHAR(8), 
                    DATEADD(SECOND, 
                        DATEDIFF(SECOND, LA.Log_DataHora_Inicio, LA.Log_DataHora_Fim), 
                        0
                    ), 
                    108
                )
            ELSE 
                CONVERT(VARCHAR(8), 
                    DATEADD(SECOND, 
                        DATEDIFF(SECOND, LA.Log_DataHora_Inicio, GETDATE()), 
                        0
                    ), 
                    108
                ) + ' (em andamento)'
        END AS Duracao_Formatada,
        
        -- Status da conexão
        CASE 
            WHEN LA.Log_DataHora_Fim IS NULL THEN 'Ativa'
            WHEN LA.Log_Observacoes LIKE '%Órfão%' OR LA.Log_Observacoes LIKE '%órfão%' THEN 'Órfã Limpa'
            ELSE 'Finalizada'
        END AS Status,
        
        -- Observações
        ISNULL(LA.Log_Observacoes, '') AS Observacoes
        
    FROM 
        Log_Acesso_WTS LA
        LEFT JOIN Conexao_WTS C ON LA.Con_Codigo = C.con_codigo
        LEFT JOIN Grupo_WTS G ON C.gru_codigo = G.Gru_Codigo
        
    WHERE 
        -- Filtro por período
        LA.Log_DataHora_Inicio BETWEEN @DataInicio AND @DataFim
        
        -- Filtro por usuário (se informado)
        AND (@Usuario IS NULL OR LA.Usu_Nome_Maquina LIKE '%' + @Usuario + '%')
        
        -- Filtro por conexão (se informado)
        AND (@Conexao IS NULL 
             OR LA.Con_Nome_Acessado LIKE '%' + @Conexao + '%'
             OR C.con_nome LIKE '%' + @Conexao + '%')
        
        -- Filtro por status (apenas ativas se solicitado)
        AND (@ApenasAtivas = 0 OR LA.Log_DataHora_Fim IS NULL)
        
    ORDER BY 
        LA.Log_DataHora_Inicio DESC;
        
END

PRINT 'Procedure sp_Relatorio_Conexoes criada com sucesso!';
PRINT '';
PRINT '================================================================================';
PRINT 'EXEMPLOS DE USO:';
PRINT '================================================================================';
PRINT '';
PRINT '-- 1. Relatório de hoje:';
PRINT 'EXEC sp_Relatorio_Conexoes';
PRINT '    @DataInicio = ''' + CONVERT(VARCHAR(10), GETDATE(), 120) + ' 00:00:00'',';
PRINT '    @DataFim = ''' + CONVERT(VARCHAR(10), GETDATE(), 120) + ' 23:59:59''';
PRINT '';
PRINT '-- 2. Relatório de um usuário específico:';
PRINT 'EXEC sp_Relatorio_Conexoes';
PRINT '    @DataInicio = DATEADD(MONTH, -1, GETDATE()),';
PRINT '    @DataFim = GETDATE(),';
PRINT '    @Usuario = ''Jefferson''';
PRINT '';
PRINT '-- 3. Apenas conexões ativas:';
PRINT 'EXEC sp_Relatorio_Conexoes';
PRINT '    @DataInicio = ''' + CONVERT(VARCHAR(10), GETDATE(), 120) + ' 00:00:00'',';
PRINT '    @DataFim = GETDATE(),';
PRINT '    @ApenasAtivas = 1';
PRINT '';
PRINT '================================================================================';

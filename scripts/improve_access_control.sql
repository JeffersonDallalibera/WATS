-- ================================================================
-- MELHORIAS PARA LIBERAÇÃO DE ACESSO INDIVIDUAL
-- Adiciona tabela para permissões específicas por conexão
-- ================================================================

-- ================================================================
-- NOVA TABELA: PERMISSÕES ESPECÍFICAS POR CONEXÃO
-- ================================================================

CREATE TABLE [dbo].[Permissao_Conexao_WTS] (
    [Pcon_Id] INT IDENTITY(1,1) NOT NULL,
    [Usu_Id] INT NOT NULL,
    [Con_Codigo] INT NOT NULL,
    [Pcon_Liberado] BIT DEFAULT 1, -- Se o acesso está liberado
    [Pcon_Data_Liberacao] DATETIME2(3) DEFAULT GETDATE(),
    [Pcon_Data_Expiracao] DATETIME2(3) NULL, -- Data de expiração (opcional)
    [Pcon_Liberado_Por] NVARCHAR(100) NULL, -- Quem liberou o acesso
    [Pcon_Motivo] NVARCHAR(500) NULL, -- Motivo da liberação/bloqueio
    [Pcon_Data_Criacao] DATETIME2(3) DEFAULT GETDATE(),
    [Pcon_Data_Alteracao] DATETIME2(3) DEFAULT GETDATE(),
    
    CONSTRAINT [PK_Permissao_Conexao_WTS] PRIMARY KEY CLUSTERED ([Pcon_Id]),
    CONSTRAINT [UK_Permissao_Conexao_WTS] UNIQUE ([Usu_Id], [Con_Codigo]),
    CONSTRAINT [FK_Permissao_Conexao_WTS_Usuario] 
        FOREIGN KEY ([Usu_Id]) REFERENCES [dbo].[Usuario_Sistema_WTS]([Usu_Id])
        ON DELETE CASCADE,
    CONSTRAINT [FK_Permissao_Conexao_WTS_Conexao] 
        FOREIGN KEY ([Con_Codigo]) REFERENCES [dbo].[Conexao_WTS]([Con_Codigo])
        ON DELETE CASCADE
);

-- Índices para otimização de consultas
CREATE NONCLUSTERED INDEX [IX_Permissao_Conexao_WTS_Usuario] 
ON [dbo].[Permissao_Conexao_WTS] ([Usu_Id]);

CREATE NONCLUSTERED INDEX [IX_Permissao_Conexao_WTS_Conexao] 
ON [dbo].[Permissao_Conexao_WTS] ([Con_Codigo]);

CREATE NONCLUSTERED INDEX [IX_Permissao_Conexao_WTS_Liberado] 
ON [dbo].[Permissao_Conexao_WTS] ([Pcon_Liberado]);

CREATE NONCLUSTERED INDEX [IX_Permissao_Conexao_WTS_Expiracao] 
ON [dbo].[Permissao_Conexao_WTS] ([Pcon_Data_Expiracao]);

PRINT 'Tabela Permissao_Conexao_WTS criada com sucesso!';

-- ================================================================
-- STORED PROCEDURE PARA VERIFICAR ACESSO INDIVIDUAL
-- ================================================================

CREATE OR ALTER PROCEDURE [dbo].[sp_verificar_acesso_conexao]
    @UsuarioId INT,
    @ConexaoId INT,
    @TemAcesso BIT OUTPUT,
    @TipoAcesso NVARCHAR(50) OUTPUT, -- 'GRUPO', 'INDIVIDUAL', 'ADMIN', 'BLOQUEADO'
    @Motivo NVARCHAR(500) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @IsAdmin BIT = 0;
    DECLARE @AcessoGrupo BIT = 0;
    DECLARE @AcessoIndividual BIT = 0;
    DECLARE @GrupoConexao INT = NULL;
    
    -- Verifica se é admin
    SELECT @IsAdmin = Usu_Is_Admin 
    FROM Usuario_Sistema_WTS 
    WHERE Usu_Id = @UsuarioId AND Usu_Ativo = 1;
    
    IF @IsAdmin = 1
    BEGIN
        SET @TemAcesso = 1;
        SET @TipoAcesso = 'ADMIN';
        SET @Motivo = 'Usuário administrador';
        RETURN;
    END
    
    -- Verifica acesso individual específico
    SELECT @AcessoIndividual = Pcon_Liberado,
           @Motivo = ISNULL(Pcon_Motivo, 'Acesso individual')
    FROM Permissao_Conexao_WTS pc
    WHERE pc.Usu_Id = @UsuarioId 
      AND pc.Con_Codigo = @ConexaoId
      AND (pc.Pcon_Data_Expiracao IS NULL OR pc.Pcon_Data_Expiracao > GETDATE());
    
    -- Se tem permissão individual específica
    IF @AcessoIndividual IS NOT NULL
    BEGIN
        SET @TemAcesso = @AcessoIndividual;
        IF @AcessoIndividual = 1
            SET @TipoAcesso = 'INDIVIDUAL';
        ELSE
        BEGIN
            SET @TipoAcesso = 'BLOQUEADO';
            SET @Motivo = ISNULL(@Motivo, 'Acesso individual bloqueado');
        END
        RETURN;
    END
    
    -- Se não tem permissão individual, verifica por grupo
    SELECT @GrupoConexao = Gru_Codigo
    FROM Conexao_WTS
    WHERE Con_Codigo = @ConexaoId;
    
    IF @GrupoConexao IS NOT NULL
    BEGIN
        SELECT @AcessoGrupo = 1
        FROM Permissao_Grupo_WTS pg
        WHERE pg.Usu_Id = @UsuarioId 
          AND pg.Gru_Codigo = @GrupoConexao;
        
        IF @AcessoGrupo = 1
        BEGIN
            SET @TemAcesso = 1;
            SET @TipoAcesso = 'GRUPO';
            SET @Motivo = 'Acesso via grupo';
            RETURN;
        END
    END
    
    -- Sem acesso
    SET @TemAcesso = 0;
    SET @TipoAcesso = 'SEM_ACESSO';
    SET @Motivo = 'Usuário não possui permissão para esta conexão';
END;

PRINT 'Stored procedure sp_verificar_acesso_conexao criada com sucesso!';

-- ================================================================
-- STORED PROCEDURE PARA LIBERAR/BLOQUEAR ACESSO INDIVIDUAL
-- ================================================================

CREATE OR ALTER PROCEDURE [dbo].[sp_gerenciar_acesso_individual]
    @UsuarioId INT,
    @ConexaoId INT,
    @Liberado BIT,
    @LiberadoPor NVARCHAR(100),
    @Motivo NVARCHAR(500) = NULL,
    @DataExpiracao DATETIME2(3) = NULL,
    @Sucesso BIT OUTPUT,
    @Mensagem NVARCHAR(500) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Verifica se já existe registro
        IF EXISTS (SELECT 1 FROM Permissao_Conexao_WTS WHERE Usu_Id = @UsuarioId AND Con_Codigo = @ConexaoId)
        BEGIN
            -- Atualiza registro existente
            UPDATE Permissao_Conexao_WTS
            SET Pcon_Liberado = @Liberado,
                Pcon_Data_Liberacao = GETDATE(),
                Pcon_Data_Expiracao = @DataExpiracao,
                Pcon_Liberado_Por = @LiberadoPor,
                Pcon_Motivo = @Motivo,
                Pcon_Data_Alteracao = GETDATE()
            WHERE Usu_Id = @UsuarioId AND Con_Codigo = @ConexaoId;
            
            SET @Mensagem = CASE 
                WHEN @Liberado = 1 THEN 'Acesso individual liberado com sucesso'
                ELSE 'Acesso individual bloqueado com sucesso'
            END;
        END
        ELSE
        BEGIN
            -- Cria novo registro
            INSERT INTO Permissao_Conexao_WTS 
            (Usu_Id, Con_Codigo, Pcon_Liberado, Pcon_Data_Expiracao, Pcon_Liberado_Por, Pcon_Motivo)
            VALUES 
            (@UsuarioId, @ConexaoId, @Liberado, @DataExpiracao, @LiberadoPor, @Motivo);
            
            SET @Mensagem = CASE 
                WHEN @Liberado = 1 THEN 'Permissão individual criada e liberada com sucesso'
                ELSE 'Permissão individual criada e bloqueada'
            END;
        END
        
        COMMIT TRANSACTION;
        SET @Sucesso = 1;
        
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        SET @Sucesso = 0;
        SET @Mensagem = 'Erro ao gerenciar acesso: ' + ERROR_MESSAGE();
    END CATCH
END;

PRINT 'Stored procedure sp_gerenciar_acesso_individual criada com sucesso!';

-- ================================================================
-- VIEW PARA CONSULTAS DE ACESSO CONSOLIDADAS
-- ================================================================

CREATE OR ALTER VIEW [dbo].[vw_acessos_usuarios] AS
SELECT 
    u.Usu_Id,
    u.Usu_Nome,
    c.Con_Codigo,
    c.Con_Nome,
    c.Con_IP,
    g.Gru_Nome,
    
    -- Tipo de acesso
    CASE 
        WHEN u.Usu_Is_Admin = 1 THEN 'ADMIN'
        WHEN pc.Pcon_Liberado = 1 THEN 'INDIVIDUAL_LIBERADO'
        WHEN pc.Pcon_Liberado = 0 THEN 'INDIVIDUAL_BLOQUEADO'
        WHEN pg.Usu_Id IS NOT NULL THEN 'GRUPO'
        ELSE 'SEM_ACESSO'
    END AS Tipo_Acesso,
    
    -- Detalhes da permissão individual
    pc.Pcon_Data_Liberacao,
    pc.Pcon_Data_Expiracao,
    pc.Pcon_Liberado_Por,
    pc.Pcon_Motivo,
    
    -- Status consolidado
    CASE 
        WHEN u.Usu_Is_Admin = 1 THEN 1
        WHEN pc.Pcon_Liberado = 1 AND (pc.Pcon_Data_Expiracao IS NULL OR pc.Pcon_Data_Expiracao > GETDATE()) THEN 1
        WHEN pc.Pcon_Liberado = 0 THEN 0
        WHEN pg.Usu_Id IS NOT NULL THEN 1
        ELSE 0
    END AS Tem_Acesso

FROM Usuario_Sistema_WTS u
CROSS JOIN Conexao_WTS c
LEFT JOIN Grupo_WTS g ON c.Gru_Codigo = g.Gru_Codigo
LEFT JOIN Permissao_Conexao_WTS pc ON u.Usu_Id = pc.Usu_Id AND c.Con_Codigo = pc.Con_Codigo
LEFT JOIN Permissao_Grupo_WTS pg ON u.Usu_Id = pg.Usu_Id AND c.Gru_Codigo = pg.Gru_Codigo

WHERE u.Usu_Ativo = 1 AND c.Con_Ativo = 1;

PRINT 'View vw_acessos_usuarios criada com sucesso!';

PRINT '=================================================================';
PRINT 'MELHORIAS DE LIBERAÇÃO DE ACESSO IMPLEMENTADAS COM SUCESSO!';
PRINT '=================================================================';
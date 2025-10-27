-- ================================================================
-- SCRIPT SQL SERVER - BANCO WATS (Windows Access To Servers)
-- Criação completa do banco de dados e estruturas
-- ================================================================

-- ================================================================
-- 1. CRIAÇÃO DO BANCO DE DADOS
-- ================================================================

-- Verifica se o banco já existe e remove se necessário
IF EXISTS (SELECT name FROM sys.databases WHERE name = 'WATS')
BEGIN
    ALTER DATABASE [WATS] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE [WATS];
    PRINT 'Banco WATS existente removido.';
END

-- Cria o banco WATS
CREATE DATABASE [WATS]
COLLATE SQL_Latin1_General_CP1_CI_AS;
GO

-- Usa o banco criado
USE [WATS];
GO

PRINT 'Banco WATS criado com sucesso!';

-- ================================================================
-- 2. TABELA DE CONFIGURAÇÕES DO SISTEMA
-- ================================================================

CREATE TABLE [dbo].[Config_Sistema_WTS] (
    [Cfg_Id] INT IDENTITY(1,1) NOT NULL,
    [Cfg_Chave] NVARCHAR(100) NOT NULL,
    [Cfg_Valor] NVARCHAR(500) NULL,
    [Cfg_Descricao] NVARCHAR(255) NULL,
    [Cfg_Data_Criacao] DATETIME2(3) DEFAULT GETDATE(),
    [Cfg_Data_Alteracao] DATETIME2(3) DEFAULT GETDATE(),
    
    CONSTRAINT [PK_Config_Sistema_WTS] PRIMARY KEY CLUSTERED ([Cfg_Id]),
    CONSTRAINT [UK_Config_Sistema_WTS_Chave] UNIQUE ([Cfg_Chave])
);

-- Índice para busca por chave
CREATE NONCLUSTERED INDEX [IX_Config_Sistema_WTS_Chave] 
ON [dbo].[Config_Sistema_WTS] ([Cfg_Chave]);

PRINT 'Tabela Config_Sistema_WTS criada.';

-- ================================================================
-- 3. TABELA DE GRUPOS DE PERMISSÃO
-- ================================================================

CREATE TABLE [dbo].[Grupo_WTS] (
    [Gru_Codigo] INT IDENTITY(1,1) NOT NULL,
    [Gru_Nome] NVARCHAR(100) NOT NULL,
    [Gru_Descricao] NVARCHAR(500) NULL,
    [Gru_Data_Criacao] DATETIME2(3) DEFAULT GETDATE(),
    [Gru_Data_Alteracao] DATETIME2(3) DEFAULT GETDATE(),
    [Gru_Ativo] BIT DEFAULT 1,
    
    CONSTRAINT [PK_Grupo_WTS] PRIMARY KEY CLUSTERED ([Gru_Codigo]),
    CONSTRAINT [UK_Grupo_WTS_Nome] UNIQUE ([Gru_Nome])
);

-- Índice para busca por nome
CREATE NONCLUSTERED INDEX [IX_Grupo_WTS_Nome] 
ON [dbo].[Grupo_WTS] ([Gru_Nome]);

PRINT 'Tabela Grupo_WTS criada.';

-- ================================================================
-- 4. TABELA DE USUÁRIOS DO SISTEMA
-- ================================================================

CREATE TABLE [dbo].[Usuario_Sistema_WTS] (
    [Usu_Id] INT IDENTITY(1,1) NOT NULL,
    [Usu_Nome] NVARCHAR(100) NOT NULL,
    [Usu_Email] NVARCHAR(255) NULL,
    [Usu_Ativo] BIT DEFAULT 1,
    [Usu_Is_Admin] BIT DEFAULT 0,
    [Usu_Data_Criacao] DATETIME2(3) DEFAULT GETDATE(),
    [Usu_Data_Alteracao] DATETIME2(3) DEFAULT GETDATE(),
    [Usu_Ultimo_Login] DATETIME2(3) NULL,
    
    CONSTRAINT [PK_Usuario_Sistema_WTS] PRIMARY KEY CLUSTERED ([Usu_Id]),
    CONSTRAINT [UK_Usuario_Sistema_WTS_Nome] UNIQUE ([Usu_Nome])
);

-- Índices para otimização
CREATE NONCLUSTERED INDEX [IX_Usuario_Sistema_WTS_Nome_Ativo] 
ON [dbo].[Usuario_Sistema_WTS] ([Usu_Nome], [Usu_Ativo]);

CREATE NONCLUSTERED INDEX [IX_Usuario_Sistema_WTS_Ativo] 
ON [dbo].[Usuario_Sistema_WTS] ([Usu_Ativo]);

PRINT 'Tabela Usuario_Sistema_WTS criada.';

-- ================================================================
-- 5. TABELA DE PERMISSÕES GRUPO x USUÁRIO
-- ================================================================

CREATE TABLE [dbo].[Permissao_Grupo_WTS] (
    [Perm_Id] INT IDENTITY(1,1) NOT NULL,
    [Usu_Id] INT NOT NULL,
    [Gru_Codigo] INT NOT NULL,
    [Perm_Data_Criacao] DATETIME2(3) DEFAULT GETDATE(),
    
    CONSTRAINT [PK_Permissao_Grupo_WTS] PRIMARY KEY CLUSTERED ([Perm_Id]),
    CONSTRAINT [UK_Permissao_Grupo_WTS] UNIQUE ([Usu_Id], [Gru_Codigo]),
    CONSTRAINT [FK_Permissao_Grupo_WTS_Usuario] 
        FOREIGN KEY ([Usu_Id]) REFERENCES [dbo].[Usuario_Sistema_WTS]([Usu_Id])
        ON DELETE CASCADE,
    CONSTRAINT [FK_Permissao_Grupo_WTS_Grupo] 
        FOREIGN KEY ([Gru_Codigo]) REFERENCES [dbo].[Grupo_WTS]([Gru_Codigo])
        ON DELETE CASCADE
);

-- Índices para otimização de consultas
CREATE NONCLUSTERED INDEX [IX_Permissao_Grupo_WTS_Usuario] 
ON [dbo].[Permissao_Grupo_WTS] ([Usu_Id]);

CREATE NONCLUSTERED INDEX [IX_Permissao_Grupo_WTS_Grupo] 
ON [dbo].[Permissao_Grupo_WTS] ([Gru_Codigo]);

PRINT 'Tabela Permissao_Grupo_WTS criada.';

-- ================================================================
-- 6. TABELA DE CONEXÕES/SERVIDORES
-- ================================================================

CREATE TABLE [dbo].[Conexao_WTS] (
    [Con_Codigo] INT IDENTITY(1,1) NOT NULL,
    [Con_Nome] NVARCHAR(150) NOT NULL,
    [Con_IP] NVARCHAR(50) NOT NULL,
    [Con_Usuario] NVARCHAR(100) NULL,
    [Con_Senha] NVARCHAR(500) NULL, -- Pode ser criptografada
    [Gru_Codigo] INT NULL, -- Grupo associado
    [Con_Tipo] NVARCHAR(20) DEFAULT 'RDP', -- RDP, SSH, VNC, etc.
    [Con_Particularidade] NVARCHAR(500) NULL, -- Configurações específicas
    [Con_Cliente] NVARCHAR(100) NULL, -- Cliente/Empresa
    [Extra] NVARCHAR(1000) NULL, -- Informações extras (JSON, etc.)
    [Sec] NVARCHAR(100) NULL, -- Configurações de segurança
    [Con_Porta] INT NULL, -- Porta da conexão
    [Con_Data_Criacao] DATETIME2(3) DEFAULT GETDATE(),
    [Con_Data_Alteracao] DATETIME2(3) DEFAULT GETDATE(),
    [Con_Ativo] BIT DEFAULT 1,
    
    CONSTRAINT [PK_Conexao_WTS] PRIMARY KEY CLUSTERED ([Con_Codigo]),
    CONSTRAINT [FK_Conexao_WTS_Grupo] 
        FOREIGN KEY ([Gru_Codigo]) REFERENCES [dbo].[Grupo_WTS]([Gru_Codigo])
        ON DELETE SET NULL
);

-- Índices para otimização
CREATE NONCLUSTERED INDEX [IX_Conexao_WTS_Nome] 
ON [dbo].[Conexao_WTS] ([Con_Nome]);

CREATE NONCLUSTERED INDEX [IX_Conexao_WTS_Grupo] 
ON [dbo].[Conexao_WTS] ([Gru_Codigo]);

CREATE NONCLUSTERED INDEX [IX_Conexao_WTS_IP] 
ON [dbo].[Conexao_WTS] ([Con_IP]);

CREATE NONCLUSTERED INDEX [IX_Conexao_WTS_Tipo] 
ON [dbo].[Conexao_WTS] ([Con_Tipo]);

PRINT 'Tabela Conexao_WTS criada.';

-- ================================================================
-- 7. TABELA DE LOG DE CONEXÕES ATIVAS
-- ================================================================

CREATE TABLE [dbo].[Usuario_Conexao_WTS] (
    [UCon_Id] INT IDENTITY(1,1) NOT NULL,
    [Con_Codigo] INT NOT NULL,
    [Usu_Nome] NVARCHAR(100) NOT NULL,
    [Usu_IP] NVARCHAR(50) NULL,
    [Usu_Nome_Maquina] NVARCHAR(100) NULL,
    [Usu_Usuario_Maquina] NVARCHAR(100) NULL,
    [Usu_Dat_Conexao] DATETIME2(3) DEFAULT GETDATE(),
    [Usu_Last_Heartbeat] DATETIME2(3) DEFAULT GETDATE(),
    
    CONSTRAINT [PK_Usuario_Conexao_WTS] PRIMARY KEY CLUSTERED ([UCon_Id]),
    CONSTRAINT [FK_Usuario_Conexao_WTS_Conexao] 
        FOREIGN KEY ([Con_Codigo]) REFERENCES [dbo].[Conexao_WTS]([Con_Codigo])
        ON DELETE CASCADE
);

-- Índices para otimização
CREATE NONCLUSTERED INDEX [IX_Usuario_Conexao_WTS_Conexao] 
ON [dbo].[Usuario_Conexao_WTS] ([Con_Codigo]);

CREATE NONCLUSTERED INDEX [IX_Usuario_Conexao_WTS_Usuario] 
ON [dbo].[Usuario_Conexao_WTS] ([Usu_Nome]);

CREATE NONCLUSTERED INDEX [IX_Usuario_Conexao_WTS_Heartbeat] 
ON [dbo].[Usuario_Conexao_WTS] ([Usu_Last_Heartbeat]);

PRINT 'Tabela Usuario_Conexao_WTS criada.';

-- ================================================================
-- 8. TABELA DE LOG DE ACESSOS DETALHADO
-- ================================================================

CREATE TABLE [dbo].[Log_Acesso_WTS] (
    [Log_Id] INT IDENTITY(1,1) NOT NULL,
    [Usu_Nome_Maquina] NVARCHAR(100) NOT NULL,
    [Con_Codigo] INT NOT NULL,
    [Con_Nome_Acessado] NVARCHAR(150) NULL,
    [Log_DataHora_Inicio] DATETIME2(3) DEFAULT GETDATE(),
    [Log_DataHora_Fim] DATETIME2(3) NULL,
    [Log_Tipo_Conexao] NVARCHAR(20) DEFAULT 'RDP',
    [Log_IP_Usuario] NVARCHAR(50) NULL,
    [Log_Observacoes] NVARCHAR(500) NULL,
    
    CONSTRAINT [PK_Log_Acesso_WTS] PRIMARY KEY CLUSTERED ([Log_Id]),
    CONSTRAINT [FK_Log_Acesso_WTS_Conexao] 
        FOREIGN KEY ([Con_Codigo]) REFERENCES [dbo].[Conexao_WTS]([Con_Codigo])
        ON DELETE CASCADE
);

-- Índices para relatórios e consultas
CREATE NONCLUSTERED INDEX [IX_Log_Acesso_WTS_Conexao] 
ON [dbo].[Log_Acesso_WTS] ([Con_Codigo]);

CREATE NONCLUSTERED INDEX [IX_Log_Acesso_WTS_Usuario] 
ON [dbo].[Log_Acesso_WTS] ([Usu_Nome_Maquina]);

CREATE NONCLUSTERED INDEX [IX_Log_Acesso_WTS_Data_Inicio] 
ON [dbo].[Log_Acesso_WTS] ([Log_DataHora_Inicio]);

CREATE NONCLUSTERED INDEX [IX_Log_Acesso_WTS_Data_Fim] 
ON [dbo].[Log_Acesso_WTS] ([Log_DataHora_Fim]);

PRINT 'Tabela Log_Acesso_WTS criada.';

-- ================================================================
-- 9. TABELA DE PROTEÇÃO DE SESSÕES TEMPORÁRIAS
-- ================================================================

CREATE TABLE [dbo].[Sessao_Protecao_WTS] (
    [Prot_Id] INT IDENTITY(1,1) NOT NULL,
    [Con_Codigo] INT NOT NULL, -- Conexão protegida
    [Usu_Nome_Protetor] NVARCHAR(100) NOT NULL, -- Usuário que criou a proteção
    [Usu_Maquina_Protetor] NVARCHAR(100) NULL, -- Máquina do protetor
    [Prot_Senha_Hash] NVARCHAR(256) NOT NULL, -- Hash da senha de proteção
    [Prot_Observacoes] NVARCHAR(500) NULL, -- Observações do protetor
    [Prot_Data_Criacao] DATETIME2(3) DEFAULT GETDATE(),
    [Prot_Data_Expiracao] DATETIME2(3) NOT NULL, -- Quando expira
    [Prot_Duracao_Minutos] INT NOT NULL, -- Duração em minutos
    [Prot_Status] NVARCHAR(20) DEFAULT 'ATIVA', -- ATIVA, EXPIRADA, REMOVIDA
    [Prot_IP_Criador] NVARCHAR(50) NULL, -- IP da máquina que criou
    [Prot_Data_Remocao] DATETIME2(3) NULL, -- Quando foi removida
    [Prot_Removida_Por] NVARCHAR(100) NULL, -- Quem removeu
    
    CONSTRAINT [PK_Sessao_Protecao_WTS] PRIMARY KEY CLUSTERED ([Prot_Id]),
    CONSTRAINT [FK_Sessao_Protecao_WTS_Conexao] 
        FOREIGN KEY ([Con_Codigo]) REFERENCES [dbo].[Conexao_WTS]([Con_Codigo])
        ON DELETE CASCADE,
    CONSTRAINT [CK_Sessao_Protecao_Status] 
        CHECK ([Prot_Status] IN ('ATIVA', 'EXPIRADA', 'REMOVIDA'))
);

-- Índices para otimização
CREATE NONCLUSTERED INDEX [IX_Sessao_Protecao_WTS_Conexao_Status] 
ON [dbo].[Sessao_Protecao_WTS] ([Con_Codigo], [Prot_Status]);

CREATE NONCLUSTERED INDEX [IX_Sessao_Protecao_WTS_Protetor] 
ON [dbo].[Sessao_Protecao_WTS] ([Usu_Nome_Protetor]);

CREATE NONCLUSTERED INDEX [IX_Sessao_Protecao_WTS_Expiracao] 
ON [dbo].[Sessao_Protecao_WTS] ([Prot_Data_Expiracao], [Prot_Status]);

CREATE NONCLUSTERED INDEX [IX_Sessao_Protecao_WTS_Data_Criacao] 
ON [dbo].[Sessao_Protecao_WTS] ([Prot_Data_Criacao]);

PRINT 'Tabela Sessao_Protecao_WTS criada.';

-- ================================================================
-- 10. TABELA DE LOG DE TENTATIVAS DE ACESSO A SESSÕES PROTEGIDAS
-- ================================================================

CREATE TABLE [dbo].[Log_Tentativa_Protecao_WTS] (
    [LTent_Id] INT IDENTITY(1,1) NOT NULL,
    [Prot_Id] INT NOT NULL, -- Referência à proteção
    [Con_Codigo] INT NOT NULL, -- Conexão tentada
    [Usu_Nome_Solicitante] NVARCHAR(100) NOT NULL, -- Usuário tentando acessar
    [Usu_Maquina_Solicitante] NVARCHAR(100) NULL, -- Máquina do solicitante
    [LTent_Senha_Tentativa] NVARCHAR(256) NULL, -- Hash da senha tentada (para auditoria)
    [LTent_Resultado] NVARCHAR(20) NOT NULL, -- SUCESSO, SENHA_INCORRETA, EXPIRADA, NEGADA
    [LTent_Data_Hora] DATETIME2(3) DEFAULT GETDATE(),
    [LTent_IP_Solicitante] NVARCHAR(50) NULL, -- IP da máquina solicitante
    [LTent_Observacoes] NVARCHAR(500) NULL, -- Detalhes adicionais
    
    CONSTRAINT [PK_Log_Tentativa_Protecao_WTS] PRIMARY KEY CLUSTERED ([LTent_Id]),
    CONSTRAINT [FK_Log_Tentativa_Protecao_WTS_Protecao] 
        FOREIGN KEY ([Prot_Id]) REFERENCES [dbo].[Sessao_Protecao_WTS]([Prot_Id])
        ON DELETE CASCADE,
    CONSTRAINT [FK_Log_Tentativa_Protecao_WTS_Conexao] 
        FOREIGN KEY ([Con_Codigo]) REFERENCES [dbo].[Conexao_WTS]([Con_Codigo])
        ON DELETE CASCADE,
    CONSTRAINT [CK_Log_Tentativa_Resultado] 
        CHECK ([LTent_Resultado] IN ('SUCESSO', 'SENHA_INCORRETA', 'EXPIRADA', 'NEGADA', 'CANCELADA'))
);

-- Índices para relatórios e auditoria
CREATE NONCLUSTERED INDEX [IX_Log_Tentativa_Protecao_WTS_Protecao] 
ON [dbo].[Log_Tentativa_Protecao_WTS] ([Prot_Id]);

CREATE NONCLUSTERED INDEX [IX_Log_Tentativa_Protecao_WTS_Solicitante] 
ON [dbo].[Log_Tentativa_Protecao_WTS] ([Usu_Nome_Solicitante]);

CREATE NONCLUSTERED INDEX [IX_Log_Tentativa_Protecao_WTS_Resultado] 
ON [dbo].[Log_Tentativa_Protecao_WTS] ([LTent_Resultado]);

CREATE NONCLUSTERED INDEX [IX_Log_Tentativa_Protecao_WTS_Data] 
ON [dbo].[Log_Tentativa_Protecao_WTS] ([LTent_Data_Hora]);

CREATE NONCLUSTERED INDEX [IX_Log_Tentativa_Protecao_WTS_Conexao_Data] 
ON [dbo].[Log_Tentativa_Protecao_WTS] ([Con_Codigo], [LTent_Data_Hora]);

PRINT 'Tabela Log_Tentativa_Protecao_WTS criada.';

-- ================================================================
-- 11. STORED PROCEDURES
-- ================================================================

-- Procedimento para limpeza de conexões fantasma
CREATE PROCEDURE [dbo].[sp_Limpar_Conexoes_Fantasma]
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @RowsDeleted INT;
    
    -- Remove conexões sem heartbeat há mais de 1 hora
    DELETE FROM [dbo].[Usuario_Conexao_WTS]
    WHERE [Usu_Last_Heartbeat] < DATEADD(HOUR, -1, GETDATE());
    
    SET @RowsDeleted = @@ROWCOUNT;
    
    PRINT 'Limpeza de conexões fantasma executada. Registros removidos: ' + CAST(@RowsDeleted AS VARCHAR(10));
    
    RETURN @RowsDeleted;
END
GO

-- Procedimento para limpeza de proteções expiradas
CREATE PROCEDURE [dbo].[sp_Limpar_Protecoes_Expiradas]
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @RowsUpdated INT;
    
    -- Marca proteções expiradas como 'EXPIRADA'
    UPDATE [dbo].[Sessao_Protecao_WTS]
    SET [Prot_Status] = 'EXPIRADA'
    WHERE [Prot_Status] = 'ATIVA' 
      AND [Prot_Data_Expiracao] < GETDATE();
    
    SET @RowsUpdated = @@ROWCOUNT;
    
    PRINT 'Limpeza de proteções expiradas executada. Proteções expiradas: ' + CAST(@RowsUpdated AS VARCHAR(10));
    
    RETURN @RowsUpdated;
END
GO

-- Procedimento para criar proteção de sessão
CREATE PROCEDURE [dbo].[sp_Criar_Protecao_Sessao]
    @Con_Codigo INT,
    @Usu_Nome_Protetor NVARCHAR(100),
    @Usu_Maquina_Protetor NVARCHAR(100),
    @Prot_Senha_Hash NVARCHAR(256),
    @Prot_Duracao_Minutos INT,
    @Prot_Observacoes NVARCHAR(500) = NULL,
    @Prot_IP_Criador NVARCHAR(50) = NULL,
    @Prot_Id INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @DataExpiracao DATETIME2(3);
    SET @DataExpiracao = DATEADD(MINUTE, @Prot_Duracao_Minutos, GETDATE());
    
    -- Remove proteção anterior se existir (apenas uma proteção ativa por conexão)
    UPDATE [dbo].[Sessao_Protecao_WTS]
    SET [Prot_Status] = 'REMOVIDA',
        [Prot_Data_Remocao] = GETDATE(),
        [Prot_Removida_Por] = @Usu_Nome_Protetor
    WHERE [Con_Codigo] = @Con_Codigo 
      AND [Prot_Status] = 'ATIVA';
    
    -- Cria nova proteção
    INSERT INTO [dbo].[Sessao_Protecao_WTS] (
        [Con_Codigo], [Usu_Nome_Protetor], [Usu_Maquina_Protetor], 
        [Prot_Senha_Hash], [Prot_Observacoes], [Prot_Data_Expiracao], 
        [Prot_Duracao_Minutos], [Prot_IP_Criador]
    ) VALUES (
        @Con_Codigo, @Usu_Nome_Protetor, @Usu_Maquina_Protetor,
        @Prot_Senha_Hash, @Prot_Observacoes, @DataExpiracao,
        @Prot_Duracao_Minutos, @Prot_IP_Criador
    );
    
    SET @Prot_Id = SCOPE_IDENTITY();
    
    RETURN @Prot_Id;
END
GO

-- Procedimento para validar senha de proteção
CREATE PROCEDURE [dbo].[sp_Validar_Protecao_Sessao]
    @Con_Codigo INT,
    @Prot_Senha_Hash NVARCHAR(256),
    @Usu_Nome_Solicitante NVARCHAR(100),
    @Usu_Maquina_Solicitante NVARCHAR(100),
    @LTent_IP_Solicitante NVARCHAR(50) = NULL,
    @Resultado NVARCHAR(20) OUTPUT,
    @Prot_Id INT OUTPUT,
    @Usu_Nome_Protetor NVARCHAR(100) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @ProtecaoAtiva INT = 0;
    DECLARE @SenhaCorreta BIT = 0;
    
    -- Primeiro, limpa proteções expiradas
    EXEC [dbo].[sp_Limpar_Protecoes_Expiradas];
    
    -- Verifica se existe proteção ativa
    SELECT @Prot_Id = [Prot_Id], 
           @Usu_Nome_Protetor = [Usu_Nome_Protetor],
           @SenhaCorreta = CASE WHEN [Prot_Senha_Hash] = @Prot_Senha_Hash THEN 1 ELSE 0 END
    FROM [dbo].[Sessao_Protecao_WTS]
    WHERE [Con_Codigo] = @Con_Codigo 
      AND [Prot_Status] = 'ATIVA'
      AND [Prot_Data_Expiracao] > GETDATE();
    
    -- Determina resultado
    IF @Prot_Id IS NULL
    BEGIN
        SET @Resultado = 'NEGADA'; -- Não há proteção ativa
    END
    ELSE IF @SenhaCorreta = 1
    BEGIN
        SET @Resultado = 'SUCESSO';
    END
    ELSE
    BEGIN
        SET @Resultado = 'SENHA_INCORRETA';
    END
    
    -- Registra tentativa apenas se havia proteção
    IF @Prot_Id IS NOT NULL
    BEGIN
        INSERT INTO [dbo].[Log_Tentativa_Protecao_WTS] (
            [Prot_Id], [Con_Codigo], [Usu_Nome_Solicitante], 
            [Usu_Maquina_Solicitante], [LTent_Senha_Tentativa], 
            [LTent_Resultado], [LTent_IP_Solicitante]
        ) VALUES (
            @Prot_Id, @Con_Codigo, @Usu_Nome_Solicitante,
            @Usu_Maquina_Solicitante, @Prot_Senha_Hash,
            @Resultado, @LTent_IP_Solicitante
        );
    END
    
    RETURN CASE WHEN @Resultado = 'SUCESSO' THEN 1 ELSE 0 END;
END
GO

-- Procedimento para remover proteção de sessão
CREATE PROCEDURE [dbo].[sp_Remover_Protecao_Sessao]
    @Con_Codigo INT,
    @Usu_Nome_Removedor NVARCHAR(100),
    @Sucesso BIT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Prot_Id INT;
    DECLARE @Usu_Nome_Protetor NVARCHAR(100);
    
    SET @Sucesso = 0;
    
    -- Verifica se existe proteção ativa e se o usuário pode remover
    SELECT @Prot_Id = [Prot_Id], @Usu_Nome_Protetor = [Usu_Nome_Protetor]
    FROM [dbo].[Sessao_Protecao_WTS]
    WHERE [Con_Codigo] = @Con_Codigo 
      AND [Prot_Status] = 'ATIVA';
    
    -- Apenas o próprio protetor ou admin pode remover
    IF @Prot_Id IS NOT NULL AND (@Usu_Nome_Removedor = @Usu_Nome_Protetor OR 
        EXISTS(SELECT 1 FROM [dbo].[Usuario_Sistema_WTS] WHERE [Usu_Nome] = @Usu_Nome_Removedor AND [Usu_Is_Admin] = 1))
    BEGIN
        UPDATE [dbo].[Sessao_Protecao_WTS]
        SET [Prot_Status] = 'REMOVIDA',
            [Prot_Data_Remocao] = GETDATE(),
            [Prot_Removida_Por] = @Usu_Nome_Removedor
        WHERE [Prot_Id] = @Prot_Id;
        
        SET @Sucesso = 1;
    END
    
    RETURN @Sucesso;
END
GO

-- Procedimento para relatório de proteções ativas
CREATE PROCEDURE [dbo].[sp_Relatorio_Protecoes_Ativas]
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        sp.Prot_Id,
        c.Con_Nome AS [Servidor_Protegido],
        c.Con_IP,
        sp.Usu_Nome_Protetor AS [Protegido_Por],
        sp.Usu_Maquina_Protetor AS [Maquina_Protetor],
        sp.Prot_Data_Criacao AS [Criado_Em],
        sp.Prot_Data_Expiracao AS [Expira_Em],
        sp.Prot_Duracao_Minutos AS [Duracao_Min],
        sp.Prot_Observacoes AS [Observacoes],
        DATEDIFF(MINUTE, GETDATE(), sp.Prot_Data_Expiracao) AS [Minutos_Restantes],
        -- Conta tentativas de acesso
        (SELECT COUNT(*) FROM [dbo].[Log_Tentativa_Protecao_WTS] lt 
         WHERE lt.Prot_Id = sp.Prot_Id) AS [Total_Tentativas],
        (SELECT COUNT(*) FROM [dbo].[Log_Tentativa_Protecao_WTS] lt 
         WHERE lt.Prot_Id = sp.Prot_Id AND lt.LTent_Resultado = 'SUCESSO') AS [Acessos_Autorizados],
        (SELECT COUNT(*) FROM [dbo].[Log_Tentativa_Protecao_WTS] lt 
         WHERE lt.Prot_Id = sp.Prot_Id AND lt.LTent_Resultado = 'SENHA_INCORRETA') AS [Tentativas_Incorretas]
    FROM [dbo].[Sessao_Protecao_WTS] sp
    INNER JOIN [dbo].[Conexao_WTS] c ON sp.Con_Codigo = c.Con_Codigo
    WHERE sp.Prot_Status = 'ATIVA'
      AND sp.Prot_Data_Expiracao > GETDATE()
    ORDER BY sp.Prot_Data_Criacao DESC;
END
GO

-- Procedimento para relatório de conexões ativas (incluindo proteções)
CREATE PROCEDURE [dbo].[sp_Relatorio_Conexoes_Ativas]
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        uc.UCon_Id,
        c.Con_Nome,
        c.Con_IP,
        c.Con_Tipo,
        g.Gru_Nome,
        uc.Usu_Nome,
        uc.Usu_Nome_Maquina,
        uc.Usu_Dat_Conexao,
        uc.Usu_Last_Heartbeat,
        DATEDIFF(MINUTE, uc.Usu_Dat_Conexao, GETDATE()) AS [Minutos_Conectado],
        -- Informações de proteção
        CASE WHEN sp.Prot_Id IS NOT NULL THEN '🔒 PROTEGIDA' ELSE '🔓 Livre' END AS [Status_Protecao],
        sp.Usu_Nome_Protetor AS [Protegida_Por],
        sp.Prot_Data_Expiracao AS [Protecao_Expira_Em],
        DATEDIFF(MINUTE, GETDATE(), sp.Prot_Data_Expiracao) AS [Protecao_Minutos_Restantes]
    FROM [dbo].[Usuario_Conexao_WTS] uc
    INNER JOIN [dbo].[Conexao_WTS] c ON uc.Con_Codigo = c.Con_Codigo
    LEFT JOIN [dbo].[Grupo_WTS] g ON c.Gru_Codigo = g.Gru_Codigo
    LEFT JOIN [dbo].[Sessao_Protecao_WTS] sp ON c.Con_Codigo = sp.Con_Codigo 
        AND sp.Prot_Status = 'ATIVA' AND sp.Prot_Data_Expiracao > GETDATE()
    WHERE uc.Usu_Last_Heartbeat > DATEADD(MINUTE, -10, GETDATE()) -- Últimos 10 minutos
    ORDER BY uc.Usu_Dat_Conexao DESC;
END
GO

-- Procedimento para relatório de acessos por período
CREATE PROCEDURE [dbo].[sp_Relatorio_Acessos_Periodo]
    @DataInicio DATETIME2(3),
    @DataFim DATETIME2(3)
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        la.Log_Id,
        la.Usu_Nome_Maquina,
        c.Con_Nome,
        c.Con_IP,
        la.Log_DataHora_Inicio,
        la.Log_DataHora_Fim,
        la.Log_Tipo_Conexao,
        CASE 
            WHEN la.Log_DataHora_Fim IS NOT NULL 
            THEN DATEDIFF(MINUTE, la.Log_DataHora_Inicio, la.Log_DataHora_Fim)
            ELSE NULL 
        END AS [Duracao_Minutos],
        g.Gru_Nome
    FROM [dbo].[Log_Acesso_WTS] la
    INNER JOIN [dbo].[Conexao_WTS] c ON la.Con_Codigo = c.Con_Codigo
    LEFT JOIN [dbo].[Grupo_WTS] g ON c.Gru_Codigo = g.Gru_Codigo
    WHERE la.Log_DataHora_Inicio >= @DataInicio 
      AND la.Log_DataHora_Inicio <= @DataFim
    ORDER BY la.Log_DataHora_Inicio DESC;
END
GO

PRINT 'Stored Procedures criadas.';

-- ================================================================
-- 10. TRIGGERS PARA AUDITORIA E AUTOMAÇÃO
-- ================================================================

-- Trigger para atualizar data de alteração na tabela Usuario_Sistema_WTS
CREATE TRIGGER [dbo].[TR_Usuario_Sistema_WTS_Update]
ON [dbo].[Usuario_Sistema_WTS]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE [dbo].[Usuario_Sistema_WTS]
    SET [Usu_Data_Alteracao] = GETDATE()
    FROM [dbo].[Usuario_Sistema_WTS] u
    INNER JOIN inserted i ON u.Usu_Id = i.Usu_Id;
END
GO

-- Trigger para atualizar data de alteração na tabela Grupo_WTS
CREATE TRIGGER [dbo].[TR_Grupo_WTS_Update]
ON [dbo].[Grupo_WTS]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE [dbo].[Grupo_WTS]
    SET [Gru_Data_Alteracao] = GETDATE()
    FROM [dbo].[Grupo_WTS] g
    INNER JOIN inserted i ON g.Gru_Codigo = i.Gru_Codigo;
END
GO

-- Trigger para atualizar data de alteração na tabela Conexao_WTS
CREATE TRIGGER [dbo].[TR_Conexao_WTS_Update]
ON [dbo].[Conexao_WTS]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE [dbo].[Conexao_WTS]
    SET [Con_Data_Alteracao] = GETDATE()
    FROM [dbo].[Conexao_WTS] c
    INNER JOIN inserted i ON c.Con_Codigo = i.Con_Codigo;
END
GO

-- Trigger para limpar proteções ao desconectar usuário
CREATE TRIGGER [dbo].[TR_Usuario_Conexao_WTS_Delete]
ON [dbo].[Usuario_Conexao_WTS]
AFTER DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Quando um usuário desconecta, remove suas proteções ativas
    UPDATE sp
    SET [Prot_Status] = 'REMOVIDA',
        [Prot_Data_Remocao] = GETDATE(),
        [Prot_Removida_Por] = 'SISTEMA_DESCONEXAO'
    FROM [dbo].[Sessao_Protecao_WTS] sp
    INNER JOIN deleted d ON sp.Con_Codigo = d.Con_Codigo 
        AND sp.Usu_Nome_Protetor = d.Usu_Nome
    WHERE sp.Prot_Status = 'ATIVA';
    
    -- Log das proteções removidas automaticamente
    INSERT INTO [dbo].[Log_Tentativa_Protecao_WTS] (
        [Prot_Id], [Con_Codigo], [Usu_Nome_Solicitante], 
        [LTent_Resultado], [LTent_Observacoes]
    )
    SELECT 
        sp.Prot_Id, 
        sp.Con_Codigo, 
        'SISTEMA',
        'CANCELADA',
        'Proteção removida automaticamente - usuário desconectou'
    FROM [dbo].[Sessao_Protecao_WTS] sp
    INNER JOIN deleted d ON sp.Con_Codigo = d.Con_Codigo 
        AND sp.Usu_Nome_Protetor = d.Usu_Nome
    WHERE sp.Prot_Status = 'REMOVIDA' 
      AND sp.Prot_Removida_Por = 'SISTEMA_DESCONEXAO';
END
GO

PRINT 'Triggers criados.';

-- ================================================================
-- 11. DADOS INICIAIS
-- ================================================================

-- Configurações do sistema
INSERT INTO [dbo].[Config_Sistema_WTS] ([Cfg_Chave], [Cfg_Valor], [Cfg_Descricao])
VALUES 
    ('ADMIN_PASSWORD', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Hash SHA-256 da senha admin (padrão: admin)'),
    ('SESSION_TIMEOUT', '3600', 'Timeout da sessão em segundos'),
    ('MAX_CONCURRENT_CONNECTIONS', '100', 'Máximo de conexões simultâneas'),
    ('LOG_RETENTION_DAYS', '90', 'Dias para manter logs de acesso'),
    ('HEARTBEAT_INTERVAL', '300', 'Intervalo de heartbeat em segundos'),
    ('VERSION', '2.0.0', 'Versão do sistema WATS');

-- Grupo padrão de administradores
INSERT INTO [dbo].[Grupo_WTS] ([Gru_Nome], [Gru_Descricao])
VALUES 
    ('Administradores', 'Grupo com acesso total ao sistema'),
    ('Usuarios_Basicos', 'Grupo com acesso limitado'),
    ('TI_Infraestrutura', 'Grupo para equipe de TI'),
    ('Desenvolvimento', 'Grupo para desenvolvedores');

-- Usuário administrador padrão
INSERT INTO [dbo].[Usuario_Sistema_WTS] ([Usu_Nome], [Usu_Email], [Usu_Ativo], [Usu_Is_Admin])
VALUES 
    ('admin', 'admin@empresa.com', 1, 1),
    ('wats_user', 'user@empresa.com', 1, 0);

-- Permissões para o administrador
INSERT INTO [dbo].[Permissao_Grupo_WTS] ([Usu_Id], [Gru_Codigo])
SELECT 1, [Gru_Codigo] FROM [dbo].[Grupo_WTS] WHERE [Gru_Nome] = 'Administradores';

-- Permissões para usuário básico
INSERT INTO [dbo].[Permissao_Grupo_WTS] ([Usu_Id], [Gru_Codigo])
SELECT 2, [Gru_Codigo] FROM [dbo].[Grupo_WTS] WHERE [Gru_Nome] = 'Usuarios_Basicos';

-- Conexões de exemplo
INSERT INTO [dbo].[Conexao_WTS] ([Con_Nome], [Con_IP], [Con_Usuario], [Gru_Codigo], [Con_Tipo], [Con_Particularidade])
VALUES 
    ('Servidor Principal', '192.168.1.100', 'administrator', 1, 'RDP', 'Servidor principal da empresa'),
    ('Servidor Backup', '192.168.1.101', 'backup_user', 1, 'RDP', 'Servidor de backup'),
    ('Servidor Web', '192.168.1.102', 'web_admin', 2, 'SSH', 'Servidor web Linux'),
    ('Database Server', '192.168.1.103', 'sa', 1, 'RDP', 'Servidor de banco de dados');

PRINT 'Dados iniciais inseridos.';

-- ================================================================
-- 12. VIEWS PARA CONSULTAS COMUNS
-- ================================================================

-- View para conexões com informações completas (incluindo proteções)
CREATE VIEW [dbo].[vw_Conexoes_Completas]
AS
SELECT 
    c.Con_Codigo,
    c.Con_Nome,
    c.Con_IP,
    c.Con_Usuario,
    c.Con_Tipo,
    c.Con_Particularidade,
    c.Con_Cliente,
    g.Gru_Nome,
    g.Gru_Descricao,
    c.Con_Data_Criacao,
    c.Con_Ativo,
    -- Conta usuários conectados atualmente
    (SELECT COUNT(*) 
     FROM [dbo].[Usuario_Conexao_WTS] uc 
     WHERE uc.Con_Codigo = c.Con_Codigo 
       AND uc.Usu_Last_Heartbeat > DATEADD(MINUTE, -10, GETDATE())
    ) AS [Usuarios_Conectados],
    -- Informações de proteção
    CASE WHEN sp.Prot_Id IS NOT NULL THEN 1 ELSE 0 END AS [Esta_Protegida],
    sp.Usu_Nome_Protetor AS [Protegida_Por],
    sp.Prot_Data_Criacao AS [Protecao_Criada_Em],
    sp.Prot_Data_Expiracao AS [Protecao_Expira_Em],
    sp.Prot_Observacoes AS [Motivo_Protecao],
    DATEDIFF(MINUTE, GETDATE(), sp.Prot_Data_Expiracao) AS [Protecao_Minutos_Restantes]
FROM [dbo].[Conexao_WTS] c
LEFT JOIN [dbo].[Grupo_WTS] g ON c.Gru_Codigo = g.Gru_Codigo
LEFT JOIN [dbo].[Sessao_Protecao_WTS] sp ON c.Con_Codigo = sp.Con_Codigo 
    AND sp.Prot_Status = 'ATIVA' AND sp.Prot_Data_Expiracao > GETDATE()
WHERE c.Con_Ativo = 1;
GO

-- View para usuários com permissões
CREATE VIEW [dbo].[vw_Usuarios_Permissoes]
AS
SELECT 
    u.Usu_Id,
    u.Usu_Nome,
    u.Usu_Email,
    u.Usu_Ativo,
    u.Usu_Is_Admin,
    u.Usu_Data_Criacao,
    u.Usu_Ultimo_Login,
    STRING_AGG(g.Gru_Nome, ', ') AS [Grupos]
FROM [dbo].[Usuario_Sistema_WTS] u
LEFT JOIN [dbo].[Permissao_Grupo_WTS] p ON u.Usu_Id = p.Usu_Id
LEFT JOIN [dbo].[Grupo_WTS] g ON p.Gru_Codigo = g.Gru_Codigo
GROUP BY u.Usu_Id, u.Usu_Nome, u.Usu_Email, u.Usu_Ativo, u.Usu_Is_Admin, u.Usu_Data_Criacao, u.Usu_Ultimo_Login;
GO

-- View para proteções ativas com detalhes
CREATE VIEW [dbo].[vw_Protecoes_Ativas]
AS
SELECT 
    sp.Prot_Id,
    c.Con_Nome AS [Servidor],
    c.Con_IP,
    c.Con_Tipo,
    sp.Usu_Nome_Protetor AS [Protegida_Por],
    sp.Usu_Maquina_Protetor AS [Maquina_Protetor],
    sp.Prot_Data_Criacao AS [Criada_Em],
    sp.Prot_Data_Expiracao AS [Expira_Em],
    sp.Prot_Duracao_Minutos AS [Duracao_Min],
    sp.Prot_Observacoes AS [Motivo],
    DATEDIFF(MINUTE, GETDATE(), sp.Prot_Data_Expiracao) AS [Minutos_Restantes],
    -- Estatísticas de tentativas
    (SELECT COUNT(*) 
     FROM [dbo].[Log_Tentativa_Protecao_WTS] lt 
     WHERE lt.Prot_Id = sp.Prot_Id) AS [Total_Tentativas],
    (SELECT COUNT(*) 
     FROM [dbo].[Log_Tentativa_Protecao_WTS] lt 
     WHERE lt.Prot_Id = sp.Prot_Id AND lt.LTent_Resultado = 'SUCESSO') AS [Acessos_Autorizados],
    (SELECT COUNT(*) 
     FROM [dbo].[Log_Tentativa_Protecao_WTS] lt 
     WHERE lt.Prot_Id = sp.Prot_Id AND lt.LTent_Resultado = 'SENHA_INCORRETA') AS [Tentativas_Incorretas],
    -- Último acesso autorizado
    (SELECT TOP 1 lt.Usu_Nome_Solicitante 
     FROM [dbo].[Log_Tentativa_Protecao_WTS] lt 
     WHERE lt.Prot_Id = sp.Prot_Id AND lt.LTent_Resultado = 'SUCESSO'
     ORDER BY lt.LTent_Data_Hora DESC) AS [Ultimo_Acesso_Autorizado]
FROM [dbo].[Sessao_Protecao_WTS] sp
INNER JOIN [dbo].[Conexao_WTS] c ON sp.Con_Codigo = c.Con_Codigo
WHERE sp.Prot_Status = 'ATIVA' AND sp.Prot_Data_Expiracao > GETDATE();
GO

PRINT 'Views criadas.';

-- ================================================================
-- 13. JOBS DE MANUTENÇÃO (OPCIONAL)
-- ================================================================

-- Job para limpeza automática de conexões fantasma (comentado - implementar via SQL Server Agent se necessário)
/*
EXEC msdb.dbo.sp_add_job 
    @job_name = 'WATS - Limpeza Conexoes Fantasma',
    @description = 'Remove conexões fantasma do sistema WATS automaticamente';

EXEC msdb.dbo.sp_add_jobstep
    @job_name = 'WATS - Limpeza Conexoes Fantasma',
    @step_name = 'Executar Limpeza',
    @command = 'EXEC [WATS].[dbo].[sp_Limpar_Conexoes_Fantasma]',
    @database_name = 'WATS';

EXEC msdb.dbo.sp_add_schedule
    @schedule_name = 'A cada 30 minutos',
    @freq_type = 4,
    @freq_interval = 1,
    @freq_subday_type = 4,
    @freq_subday_interval = 30;

EXEC msdb.dbo.sp_attach_schedule
    @job_name = 'WATS - Limpeza Conexoes Fantasma',
    @schedule_name = 'A cada 30 minutos';

EXEC msdb.dbo.sp_add_jobserver
    @job_name = 'WATS - Limpeza Conexoes Fantasma';
*/

-- ================================================================
-- 14. PERMISSÕES DE SEGURANÇA
-- ================================================================

-- Criar role para aplicação
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'wats_app_role')
BEGIN
    CREATE ROLE [wats_app_role];
END

-- Conceder permissões necessárias para a aplicação
GRANT SELECT, INSERT, UPDATE, DELETE ON [dbo].[Config_Sistema_WTS] TO [wats_app_role];
GRANT SELECT, INSERT, UPDATE, DELETE ON [dbo].[Grupo_WTS] TO [wats_app_role];
GRANT SELECT, INSERT, UPDATE, DELETE ON [dbo].[Usuario_Sistema_WTS] TO [wats_app_role];
GRANT SELECT, INSERT, UPDATE, DELETE ON [dbo].[Permissao_Grupo_WTS] TO [wats_app_role];
GRANT SELECT, INSERT, UPDATE, DELETE ON [dbo].[Conexao_WTS] TO [wats_app_role];
GRANT SELECT, INSERT, UPDATE, DELETE ON [dbo].[Usuario_Conexao_WTS] TO [wats_app_role];
GRANT SELECT, INSERT, UPDATE, DELETE ON [dbo].[Log_Acesso_WTS] TO [wats_app_role];
GRANT SELECT, INSERT, UPDATE, DELETE ON [dbo].[Sessao_Protecao_WTS] TO [wats_app_role];
GRANT SELECT, INSERT, UPDATE, DELETE ON [dbo].[Log_Tentativa_Protecao_WTS] TO [wats_app_role];

-- Permissões para executar procedures
GRANT EXECUTE ON [dbo].[sp_Limpar_Conexoes_Fantasma] TO [wats_app_role];
GRANT EXECUTE ON [dbo].[sp_Limpar_Protecoes_Expiradas] TO [wats_app_role];
GRANT EXECUTE ON [dbo].[sp_Criar_Protecao_Sessao] TO [wats_app_role];
GRANT EXECUTE ON [dbo].[sp_Validar_Protecao_Sessao] TO [wats_app_role];
GRANT EXECUTE ON [dbo].[sp_Remover_Protecao_Sessao] TO [wats_app_role];
GRANT EXECUTE ON [dbo].[sp_Relatorio_Conexoes_Ativas] TO [wats_app_role];
GRANT EXECUTE ON [dbo].[sp_Relatorio_Acessos_Periodo] TO [wats_app_role];
GRANT EXECUTE ON [dbo].[sp_Relatorio_Protecoes_Ativas] TO [wats_app_role];
GRANT EXECUTE ON [dbo].[sp_Relatorio_Tentativas_Protecao] TO [wats_app_role];

-- Permissões para views
GRANT SELECT ON [dbo].[vw_Conexoes_Completas] TO [wats_app_role];
GRANT SELECT ON [dbo].[vw_Usuarios_Permissoes] TO [wats_app_role];
GRANT SELECT ON [dbo].[vw_Protecoes_Ativas] TO [wats_app_role];

PRINT 'Permissões configuradas.';

-- ================================================================
-- 15. SCRIPT DE VALIDAÇÃO FINAL
-- ================================================================

PRINT '================================================================';
PRINT 'VALIDAÇÃO DA ESTRUTURA DO BANCO WATS';
PRINT '================================================================';

-- Conta tabelas criadas
SELECT 'Tabelas criadas: ' + CAST(COUNT(*) AS VARCHAR(10))
FROM sys.tables 
WHERE schema_id = SCHEMA_ID('dbo')
  AND name LIKE '%_WTS';

-- Conta procedures criadas
SELECT 'Procedures criadas: ' + CAST(COUNT(*) AS VARCHAR(10))
FROM sys.procedures 
WHERE schema_id = SCHEMA_ID('dbo')
  AND name LIKE 'sp_%';

-- Conta triggers criados
SELECT 'Triggers criados: ' + CAST(COUNT(*) AS VARCHAR(10))
FROM sys.triggers 
WHERE parent_class = 1; -- Triggers de tabela

-- Conta views criadas
SELECT 'Views criadas: ' + CAST(COUNT(*) AS VARCHAR(10))
FROM sys.views 
WHERE schema_id = SCHEMA_ID('dbo')
  AND name LIKE 'vw_%';

-- Conta registros de dados iniciais
SELECT 'Configurações inseridas: ' + CAST(COUNT(*) AS VARCHAR(10))
FROM [dbo].[Config_Sistema_WTS];

SELECT 'Grupos criados: ' + CAST(COUNT(*) AS VARCHAR(10))
FROM [dbo].[Grupo_WTS];

SELECT 'Usuários criados: ' + CAST(COUNT(*) AS VARCHAR(10))
FROM [dbo].[Usuario_Sistema_WTS];

SELECT 'Conexões de exemplo: ' + CAST(COUNT(*) AS VARCHAR(10))
FROM [dbo].[Conexao_WTS];

PRINT '================================================================';
PRINT 'BANCO WATS CRIADO COM SUCESSO!';
PRINT '================================================================';
PRINT 'Usuário padrão: admin';
PRINT 'Senha padrão: admin';
PRINT 'Role da aplicação: wats_app_role';
PRINT '================================================================';
PRINT 'PRÓXIMOS PASSOS:';
PRINT '1. Criar usuário SQL Server para a aplicação';
PRINT '2. Adicionar usuário à role wats_app_role';
PRINT '3. Configurar connection string na aplicação';
PRINT '4. Alterar senha padrão do administrador';
PRINT '5. Configurar backup automático do banco';
PRINT '================================================================';

-- Exemplo de criação de usuário para aplicação (ajustar conforme necessário)
/*
-- Para autenticação SQL Server
CREATE LOGIN [wats_user] WITH PASSWORD = 'SuaSenhaSegura123!';
CREATE USER [wats_user] FOR LOGIN [wats_user];
ALTER ROLE [wats_app_role] ADD MEMBER [wats_user];

-- Para autenticação Windows (ajustar o domínio/usuário)
CREATE LOGIN [DOMINIO\wats_service] FROM WINDOWS;
CREATE USER [wats_service] FOR LOGIN [DOMINIO\wats_service];
ALTER ROLE [wats_app_role] ADD MEMBER [wats_service];
*/
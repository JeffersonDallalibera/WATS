-- Script para criar tabela de permissões individuais de conexão
-- WATS Project - Individual Connection Permissions

-- Verificar se a tabela já existe antes de criar
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Permissao_Conexao_Individual_WTS' AND xtype='U')
BEGIN
    CREATE TABLE Permissao_Conexao_Individual_WTS (
        Id INT IDENTITY(1,1) PRIMARY KEY,
        Usu_Id INT NOT NULL,
        Con_Codigo INT NOT NULL,
        Data_Inicio DATETIME NOT NULL DEFAULT GETDATE(),
        Data_Fim DATETIME NULL, -- NULL = permanente
        Criado_Por_Usu_Id INT NOT NULL,
        Data_Criacao DATETIME NOT NULL DEFAULT GETDATE(),
        Ativo BIT NOT NULL DEFAULT 1,
        Observacoes VARCHAR(500) NULL,
        
        -- Chaves estrangeiras
        CONSTRAINT FK_PCI_Usuario FOREIGN KEY (Usu_Id) REFERENCES Usuario_Sistema_WTS(Usu_Id),
        CONSTRAINT FK_PCI_Conexao FOREIGN KEY (Con_Codigo) REFERENCES Conexao_WTS(Con_Codigo),
        CONSTRAINT FK_PCI_CriadoPor FOREIGN KEY (Criado_Por_Usu_Id) REFERENCES Usuario_Sistema_WTS(Usu_Id),
        
        -- Índices únicos para evitar duplicatas
        CONSTRAINT UQ_PCI_Usuario_Conexao_Ativo UNIQUE (Usu_Id, Con_Codigo, Ativo)
    );
    
    PRINT 'Tabela Permissao_Conexao_Individual_WTS criada com sucesso.';
END
ELSE
BEGIN
    PRINT 'Tabela Permissao_Conexao_Individual_WTS já existe.';
END

-- Criar índices para melhor performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_PCI_Usuario_Ativo')
BEGIN
    CREATE INDEX IX_PCI_Usuario_Ativo ON Permissao_Conexao_Individual_WTS (Usu_Id, Ativo);
    PRINT 'Índice IX_PCI_Usuario_Ativo criado.';
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_PCI_Conexao_Ativo')
BEGIN
    CREATE INDEX IX_PCI_Conexao_Ativo ON Permissao_Conexao_Individual_WTS (Con_Codigo, Ativo);
    PRINT 'Índice IX_PCI_Conexao_Ativo criado.';
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_PCI_Datas')
BEGIN
    CREATE INDEX IX_PCI_Datas ON Permissao_Conexao_Individual_WTS (Data_Inicio, Data_Fim);
    PRINT 'Índice IX_PCI_Datas criado.';
END

-- Script para PostgreSQL (comentado - descomente se necessário)
/*
-- Versão PostgreSQL:
CREATE TABLE IF NOT EXISTS Permissao_Conexao_Individual_WTS (
    Id SERIAL PRIMARY KEY,
    Usu_Id INTEGER NOT NULL,
    Con_Codigo INTEGER NOT NULL,
    Data_Inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Data_Fim TIMESTAMP NULL,
    Criado_Por_Usu_Id INTEGER NOT NULL,
    Data_Criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Ativo BOOLEAN NOT NULL DEFAULT TRUE,
    Observacoes VARCHAR(500) NULL,
    
    CONSTRAINT FK_PCI_Usuario FOREIGN KEY (Usu_Id) REFERENCES Usuario_Sistema_WTS(Usu_Id),
    CONSTRAINT FK_PCI_Conexao FOREIGN KEY (Con_Codigo) REFERENCES Conexao_WTS(Con_Codigo),
    CONSTRAINT FK_PCI_CriadoPor FOREIGN KEY (Criado_Por_Usu_Id) REFERENCES Usuario_Sistema_WTS(Usu_Id),
    CONSTRAINT UQ_PCI_Usuario_Conexao_Ativo UNIQUE (Usu_Id, Con_Codigo, Ativo)
);

CREATE INDEX IF NOT EXISTS IX_PCI_Usuario_Ativo ON Permissao_Conexao_Individual_WTS (Usu_Id, Ativo);
CREATE INDEX IF NOT EXISTS IX_PCI_Conexao_Ativo ON Permissao_Conexao_Individual_WTS (Con_Codigo, Ativo);
CREATE INDEX IF NOT EXISTS IX_PCI_Datas ON Permissao_Conexao_Individual_WTS (Data_Inicio, Data_Fim);
*/
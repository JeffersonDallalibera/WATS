# Permissões Individuais de Conexão - WATS

## Visão Geral

Esta implementação adiciona a funcionalidade de **permissões individuais de conexão** ao sistema WATS, permitindo conceder acesso específico a conexões individuais, independente das permissões de grupo.

## Funcionalidades Implementadas

### 1. **Acesso Individual a Conexões**
- Conceder acesso a uma conexão específica para um usuário
- Independe das permissões de grupo
- Acesso permanente (sem data de expiração)

### 2. **Gerenciamento de Permissões**
- Listar permissões individuais de um usuário
- Listar usuários com acesso individual a uma conexão
- Revogar permissões individuais
- Verificar se um usuário tem acesso individual

### 3. **Integração com Sistema Existente**
- O `select_all()` agora verifica **TANTO** permissões de grupo **QUANTO** permissões individuais
- Usuários com acesso individual veem essas conexões mesmo sem acesso ao grupo

## Estrutura de Banco de Dados

### Nova Tabela: `Permissao_Conexao_Individual_WTS`

```sql
CREATE TABLE Permissao_Conexao_Individual_WTS (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Usu_Id INT NOT NULL,                    -- ID do usuário
    Con_Codigo INT NOT NULL,                -- ID da conexão
    Data_Inicio DATETIME NOT NULL,          -- Quando a permissão começa
    Data_Fim DATETIME NULL,                 -- Quando expira (NULL = permanente)
    Criado_Por_Usu_Id INT NOT NULL,         -- Quem concedeu a permissão
    Data_Criacao DATETIME NOT NULL,         -- Quando foi criada
    Ativo BIT NOT NULL DEFAULT 1,           -- Se está ativa
    Observacoes VARCHAR(500) NULL           -- Observações opcionais
);
```

## Como Usar

### 1. **Criação da Tabela**
Execute o script SQL:
```bash
# No SQL Server Management Studio ou similar
-- Execute o arquivo: scripts/create_individual_permissions_table.sql
```

### 2. **Usando no Código**

```python
from src.wats.db.repositories.connection_repository import ConnectionRepository

# Inicializar repositório
conn_repo = ConnectionRepository(db_manager, user_repo)

# Conceder acesso individual
success, message = conn_repo.grant_individual_access(
    user_id=5,
    connection_id=10,
    granted_by_user_id=1,  # ID do admin que está concedendo
    observations="Acesso para projeto específico"
)

# Verificar se usuário tem acesso
has_access = conn_repo.has_individual_access(user_id=5, connection_id=10)

# Listar permissões do usuário
permissions = conn_repo.list_user_individual_permissions(user_id=5)

# Revogar acesso
success, message = conn_repo.revoke_individual_access(user_id=5, connection_id=10)
```

### 3. **Lógica de Acesso**

O sistema agora funciona com **dupla verificação**:

1. **Usuário Admin**: Vê todas as conexões
2. **Usuário Comum**: Vê conexões se tiver **QUALQUER UM** dos acessos:
   - Permissão de grupo (sistema original)
   - Permissão individual (nova funcionalidade)

## Exemplos Práticos

### Cenário 1: Acesso Específico
```
Grupo "Saphir" possui:
- ats-bd 01 (banco de dados)
- ats-app 01 (aplicação)

Usuário "João" precisa apenas do ats-app 01:
- NÃO dar acesso ao grupo Saphir (ele veria ambas)
- DAR acesso individual ao ats-app 01 (ele vê só essa)
```

### Cenário 2: Acesso Adicional
```
Usuário "Maria" já tem acesso ao grupo "Desenvolvimento"
Precisa de acesso adicional a uma conexão do grupo "Produção":
- Manter acesso ao grupo Desenvolvimento
- DAR acesso individual à conexão específica de Produção
- Resultado: Maria vê conexões do grupo Desenvolvimento + a conexão específica de Produção
```

## Métodos Disponíveis

### ConnectionRepository - Novos Métodos

| Método | Descrição |
|--------|-----------|
| `grant_individual_access()` | Concede acesso individual permanente |
| `revoke_individual_access()` | Revoga acesso individual |
| `list_user_individual_permissions()` | Lista permissões de um usuário |
| `list_connection_individual_permissions()` | Lista usuários com acesso a uma conexão |
| `has_individual_access()` | Verifica acesso individual |
| `get_available_connections_for_individual_grant()` | Lista conexões disponíveis |
| `get_available_users_for_individual_grant()` | Lista usuários disponíveis |

## Teste da Implementação

Execute o teste para verificar se tudo está funcionando:

```bash
cd c:\Users\jefferson.dallaliber\Documents\ATS\wats
python test_individual_permissions.py
```

## Próximos Passos

1. **✅ Implementado**: Permissões individuais permanentes
2. **🔄 Próximo**: Implementar permissões temporárias (com data de expiração)
3. **🔄 Futuro**: Interface administrativa para gerenciar permissões

## Compatibilidade

- ✅ SQL Server
- ✅ PostgreSQL (ajustar dialeto se necessário)
- ✅ Mantém compatibilidade total com sistema existente
- ✅ Não quebra funcionalidades atuais

## Notas Técnicas

- A implementação usa OR na query para verificar ambos os tipos de permissão
- Índices foram criados para otimizar performance
- Constraint única evita permissões duplicadas
- Soft delete (campo `Ativo`) para histórico
- Foreign keys garantem integridade referencial
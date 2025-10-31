# Sistema de Liberação de Acesso Melhorado

## Visão Geral

Este sistema melhora significativamente a lógica de liberação de acesso no WATS, permitindo:

1. **Acesso por Grupo** (existente): Usuários herdam acesso através de grupos
2. **Acesso Individual** (novo): Permissões específicas por conexão, que sobrepõem o acesso por grupo
3. **Bloqueio Específico** (novo): Bloquear usuário de uma conexão específica, mesmo tendo acesso por grupo
4. **Acesso Temporário** (novo): Liberações com data de expiração automática

## Casos de Uso

### 1. Acesso Emergencial
```python
# Técnico precisa de acesso urgente a servidor que não tem permissão
access_service.liberar_acesso_temporario(
    user_id=123, 
    conexao_id=456, 
    responsavel="admin_plantao",
    horas_duracao=2,
    motivo="Emergência - Falha crítica"
)
```

### 2. Bloqueio Específico
```python
# Usuário de um grupo precisa ser bloqueado de conexão específica
access_service.bloquear_acesso_usuario(
    user_id=123, 
    conexao_id=456,
    responsavel="security_admin",
    motivo="Investigação de segurança"
)
```

### 3. Consultor Externo
```python
# Acesso temporário para consultor
access_service.liberar_acesso_temporario(
    user_id=789,
    conexao_id=100,
    responsavel="project_manager",
    horas_duracao=8,
    motivo="Consultoria - Análise performance"
)

# Renovar se necessário
access_service.renovar_acesso_temporario(
    user_id=789,
    conexao_id=100,
    responsavel="project_manager",
    novas_horas=4
)
```

## Estrutura do Sistema

### Nova Tabela: `Permissao_Conexao_WTS`

```sql
CREATE TABLE [dbo].[Permissao_Conexao_WTS] (
    [Pcon_Id] INT IDENTITY(1,1) NOT NULL,
    [Usu_Id] INT NOT NULL,                    -- ID do usuário
    [Con_Codigo] INT NOT NULL,                -- ID da conexão
    [Pcon_Liberado] BIT DEFAULT 1,           -- Se está liberado (1) ou bloqueado (0)
    [Pcon_Data_Liberacao] DATETIME2(3),      -- Quando foi liberado
    [Pcon_Data_Expiracao] DATETIME2(3) NULL, -- Quando expira (NULL = permanente)
    [Pcon_Liberado_Por] NVARCHAR(100),       -- Quem liberou/bloqueou
    [Pcon_Motivo] NVARCHAR(500),             -- Motivo da ação
    [Pcon_Data_Criacao] DATETIME2(3),
    [Pcon_Data_Alteracao] DATETIME2(3)
);
```

### Lógica de Prioridade

1. **Administrador**: Sempre tem acesso total
2. **Permissão Individual**: Se existe, sobrepõe qualquer acesso por grupo
   - `Pcon_Liberado = 1` → Acesso liberado
   - `Pcon_Liberado = 0` → Acesso bloqueado (mesmo estando no grupo)
3. **Permissão por Grupo**: Aplicada apenas se não existe permissão individual
4. **Sem Permissão**: Acesso negado

## Classes Principais

### `UserRepository` (Melhorado)

Novos métodos adicionados:

- `verificar_acesso_conexao(user_id, conexao_id)` - Verifica tipo de acesso
- `liberar_acesso_individual(user_id, conexao_id, responsavel, motivo, data_expiracao)` - Libera acesso
- `bloquear_acesso_individual(user_id, conexao_id, responsavel, motivo)` - Bloqueia acesso
- `remover_acesso_individual(user_id, conexao_id)` - Remove permissão individual
- `listar_acessos_usuario(user_id)` - Lista todos os acessos do usuário
- `listar_acessos_conexao(conexao_id)` - Lista usuários com acesso à conexão

### `AccessManagementService` (Nova)

Classe de alto nível para operações complexas:

- `liberar_acesso_temporario()` - Acesso com expiração automática
- `liberar_acesso_permanente()` - Acesso sem expiração
- `bloquear_acesso_usuario()` - Bloqueio específico
- `restaurar_acesso_grupo()` - Remove permissão individual
- `renovar_acesso_temporario()` - Estende acesso existente
- `verificar_status_acesso()` - Status detalhado
- `relatorio_acessos_por_usuario()` - Relatório completo

## Instalação

### 1. Executar Script SQL

```bash
# Execute o script de melhorias no banco
sqlcmd -S servidor -d WATS -i scripts/improve_access_control.sql
```

### 2. Usar no Código

```python
from src.wats.services.access_management_service import AccessManagementService
from src.wats.db.repositories.user_repository import UserRepository
from src.wats.db.repositories.connection_repository import ConnectionRepository

# Configurar serviço
user_repo = UserRepository(db_manager)
connection_repo = ConnectionRepository(db_manager, user_repo)
access_service = AccessManagementService(user_repo, connection_repo)

# Usar funcionalidades
status = access_service.verificar_status_acesso(user_id, conexao_id)
```

## Exemplos Práticos

### Verificar Acesso
```python
status = access_service.verificar_status_acesso(123, 456)
print(f"Acesso: {status['tem_acesso']}")
print(f"Tipo: {status['tipo_acesso']}")  
# Tipos: ADMIN, GRUPO, INDIVIDUAL_LIBERADO, INDIVIDUAL_BLOQUEADO, SEM_ACESSO
```

### Relatório de Usuário
```python
relatorio = access_service.relatorio_acessos_por_usuario(123)
print(f"Total conexões: {relatorio['total_conexoes']}")
print(f"Liberados: {relatorio['acessos_liberados']}")
print(f"Bloqueados: {relatorio['acessos_bloqueados']}")
```

### Listar Usuários de uma Conexão
```python
usuarios = access_service.listar_usuarios_com_acesso_individual(456)
for usuario in usuarios:
    print(f"{usuario['usu_nome']}: {usuario['tipo_acesso']}")
```

## Stored Procedures

### `sp_verificar_acesso_conexao`
```sql
EXEC sp_verificar_acesso_conexao 
    @UsuarioId = 123, 
    @ConexaoId = 456, 
    @TemAcesso = @tem OUTPUT, 
    @TipoAcesso = @tipo OUTPUT, 
    @Motivo = @motivo OUTPUT
```

### `sp_gerenciar_acesso_individual`
```sql
EXEC sp_gerenciar_acesso_individual 
    @UsuarioId = 123, 
    @ConexaoId = 456, 
    @Liberado = 1, 
    @LiberadoPor = 'admin', 
    @Motivo = 'Acesso emergencial',
    @Sucesso = @sucesso OUTPUT, 
    @Mensagem = @msg OUTPUT
```

## View de Consulta

### `vw_acessos_usuarios`
```sql
SELECT * FROM vw_acessos_usuarios 
WHERE Usu_Id = 123;  -- Ver todos os acessos do usuário

SELECT * FROM vw_acessos_usuarios 
WHERE Con_Codigo = 456;  -- Ver quem tem acesso à conexão
```

## Compatibilidade

- ✅ **SQL Server**: Funcionalidade completa com SPs
- ✅ **SQLite**: Funcionalidade completa sem SPs
- ✅ **PostgreSQL**: Funcionalidade completa (adaptação automática)

## Logs e Auditoria

Todas as operações são logadas:

```
[ACCESS_MGMT] Acesso temporário liberado: Usuário 123 -> Conexão 456 por 24h
[ACCESS_MGMT] Acesso bloqueado: Usuário 789 -> Conexão 100
[ACCESS_MGMT] Acesso renovado: Usuário 123 -> Conexão 456 por 8h
```

## Migração de Dados Existentes

O sistema é **compatível com dados existentes**:

- Usuários continuam funcionando com acesso por grupo
- Permissões individuais são adicionadas conforme necessário
- Não há quebra de funcionalidade existente

## Testes

Execute os exemplos para testar:

```python
from src.wats.examples.access_management_examples import AccessManagementExamples

examples = AccessManagementExamples(db_manager)
examples.exemplo_casos_uso_completos()
```

## Considerações de Segurança

1. **Auditoria**: Todas as ações são registradas com responsável e motivo
2. **Expiração**: Acessos temporários expiram automaticamente
3. **Prioridade**: Bloqueios individuais sobrepõem acessos de grupo
4. **Validação**: Verificação de parâmetros em todas as operações

## FAQ

**Q: O que acontece se um usuário tem acesso por grupo e individual?**
R: A permissão individual sempre tem prioridade sobre a de grupo.

**Q: Como remover uma permissão individual?**
R: Use `restaurar_acesso_grupo()` para voltar ao acesso apenas por grupo.

**Q: Acessos temporários expiram automaticamente?**
R: Sim, são verificados automaticamente nas consultas de acesso.

**Q: É compatível com o sistema atual?**
R: Sim, é completamente compatível. Usuários continuam funcionando normalmente.

**Q: Como fazer backup das permissões?**
R: Faça backup da nova tabela `Permissao_Conexao_WTS` junto com as existentes.
# 🔧 Guia de Manutenção do WATS

**Documento Técnico para Equipe de Manutenção e Desenvolvimento**

Este documento descreve a função de cada arquivo importante do projeto WATS, facilitando a manutenção e evolução do sistema.

---

## 📋 Índice

- [Estrutura Geral](#estrutura-geral)
- [Arquivos Raiz](#arquivos-raiz)
- [Código Fonte (src/wats/)](#código-fonte-srcwats)
- [Painéis Administrativos](#painéis-administrativos)
- [Banco de Dados](#banco-de-dados)
- [Sistema de Gravação](#sistema-de-gravação)
- [Scripts](#scripts)
- [Testes](#testes)
- [Fluxo de Dados](#fluxo-de-dados)
- [Guia de Modificação](#guia-de-modificação)

---

## 🏗️ Estrutura Geral

```
WATS/
├── src/wats/          # Código fonte principal
├── assets/            # Recursos estáticos (ícones, imagens)
├── config/            # Arquivos de configuração
├── scripts/           # Scripts de build, deploy e manutenção
├── docs/              # Documentação
├── tests/             # Testes automatizados
└── logs/              # Logs da aplicação
```

---

## 📄 Arquivos Raiz

### `run.py`

**Função:** Ponto de entrada da aplicação em modo desenvolvimento.

**O que faz:**

- Verifica dependências
- Carrega configurações
- Inicializa logging
- Inicia a aplicação principal (`main.py`)

**Quando modificar:**

- Adicionar verificações de pré-requisitos
- Alterar modo de inicialização (demo, debug, etc.)
- Adicionar flags de linha de comando

**Exemplo:**

```python
# Executar em modo debug
python run.py --debug

# Executar em modo demo
python run.py --demo
```

---

### `build.py`

**Função:** Script universal para gerar executáveis do WATS.

**O que faz:**

- Detecta plataforma (Windows/Linux)
- Configura PyInstaller
- Coleta dependências e recursos
- Gera executável standalone
- Cria pacotes de distribuição

**Quando modificar:**

- Adicionar novos arquivos de recursos
- Modificar configurações de build
- Adicionar novos módulos externos
- Otimizar tamanho do executável

**Comandos:**

```powershell
# Build para Windows
python build.py --platform windows

# Build para Linux
python build.py --platform linux

# Build com debug
python build.py --debug
```

---

### `requirements.txt` / `requirements-linux.txt` / `requirements-dev.txt`

**Função:** Gerenciamento de dependências Python.

| Arquivo                  | Uso                                                   |
| ------------------------ | ----------------------------------------------------- |
| `requirements.txt`       | Dependências de produção (Windows)                    |
| `requirements-linux.txt` | Dependências de produção (Linux)                      |
| `requirements-dev.txt`   | Dependências de desenvolvimento (testes, build, etc.) |

**Quando modificar:**

- Adicionar novas bibliotecas
- Atualizar versões (cuidado com breaking changes)
- Remover dependências não utilizadas

**Atualização segura:**

```powershell
# Verificar versões desatualizadas
pip list --outdated

# Atualizar com cuidado (testar após cada)
pip install --upgrade nome-pacote

# Congelar novas versões
pip freeze > requirements.txt
```

---

### `pyproject.toml`

**Função:** Configuração moderna do projeto Python.

**Contém:**

- Metadados do projeto (nome, versão, autor)
- Configurações de ferramentas (pytest, black, flake8)
- Scripts de console
- Dependências opcionais

**Quando modificar:**

- Atualizar versão do projeto
- Adicionar novos scripts de console
- Configurar novas ferramentas de dev

---

### `WATS.spec` / `WATS-multiplatform.spec`

**Função:** Configuração do PyInstaller para build.

**O que define:**

- Arquivos Python incluídos
- Bibliotecas externas (DLLs, SOs)
- Recursos (ícones, imagens, configs)
- Opções de compilação (console/window, one-file/one-dir)
- Exclusões (reduzir tamanho)

**Quando modificar:**

- Adicionar novos módulos ao projeto
- Incluir novos recursos (imagens, fontes)
- Otimizar tamanho do executável
- Resolver problemas de módulos não encontrados

**Exemplo de adição:**

```python
# Adicionar novo arquivo de recurso
datas=[
    ('assets/icons/*.ico', 'assets/icons'),
    ('config/*.json', 'config'),
    ('novo_recurso/*', 'novo_recurso'),  # <-- ADICIONAR AQUI
],
```

---

## 💻 Código Fonte (src/wats/)

### `main.py`

**Função:** Ponto de entrada real da aplicação.

**Responsabilidades:**

- Inicializar configurações
- Configurar sistema de logs
- Conectar ao banco de dados
- Criar e exibir janela principal
- Tratar exceções não capturadas

**Fluxo:**

```
main() → load_config() → init_database() → create_app_window() → mainloop()
```

**Quando modificar:**

- Adicionar inicializações globais
- Modificar tratamento de erros críticos
- Adicionar verificações de sistema

---

### `app_window.py`

**Função:** Janela principal da aplicação.

**Responsabilidades:**

- Interface gráfica principal (CustomTkinter)
- Árvore de servidores e grupos
- Barra de ferramentas e menus
- Conexão com servidores RDP
- Atualização em tempo real da lista
- Gerenciamento de temas
- Callbacks de eventos

**Principais Métodos:**

| Método                        | Função                          |
| ----------------------------- | ------------------------------- |
| `__init__()`                  | Inicializa janela e componentes |
| `_create_widgets()`           | Cria interface gráfica          |
| `_populate_tree()`            | Popula árvore de servidores     |
| `_connect_to_server()`        | Inicia conexão RDP              |
| `_on_tree_double_click()`     | Handler de duplo clique         |
| `_update_connection_status()` | Atualiza status de conexões     |

**Quando modificar:**

- Adicionar novos elementos de UI
- Modificar layout da janela
- Adicionar novos menus ou atalhos
- Alterar comportamento de conexão
- Adicionar novos filtros ou buscas

**Cache e Performance:**

```python
# Cache é invalidado automaticamente ao modificar dados
# Ver: performance.py → invalidate_user_caches()
```

---

### `config.py`

**Função:** Gerenciador centralizado de configurações.

**Responsabilidades:**

- Carregar config.json
- Carregar variáveis de ambiente (.env)
- Mesclar configurações (env override json)
- Validar configurações obrigatórias
- Fornecer acesso via singleton

**Estrutura:**

```python
from config import Config

# Acessar configuração
db_type = Config.get('database.type')
recording_enabled = Config.get('recording.enabled', default=True)
```

**Quando modificar:**

- Adicionar novas configurações
- Modificar validações
- Adicionar novos arquivos de config
- Implementar configurações por ambiente

---

### `performance.py`

**Função:** Sistema de cache e otimizações de performance.

**Responsabilidades:**

- Cache multinível com TTL
- Invalidação automática de cache
- Pool de conexões de banco
- Métricas de performance
- Otimização de queries

**Principais Funções:**

| Função                           | Uso                                  |
| -------------------------------- | ------------------------------------ |
| `get_cached()`                   | Obter valor do cache                 |
| `set_cached()`                   | Armazenar no cache                   |
| `invalidate_cache_pattern()`     | Limpar cache por padrão              |
| `invalidate_user_caches()`       | Limpar todos os caches de um usuário |
| `invalidate_group_caches()`      | Limpar todos os caches de um grupo   |
| `invalidate_connection_caches()` | Limpar todos os caches de conexões   |

**Padrões de Cache:**

- `users:*` - Dados de usuários
- `groups:*` - Dados de grupos
- `connections:*` - Dados de conexões
- `permissions:*` - Dados de permissões

**Quando modificar:**

- Ajustar TTL do cache
- Adicionar novos padrões de cache
- Implementar cache warming
- Adicionar métricas customizadas

**⚠️ IMPORTANTE:**
Ao adicionar novos repositórios que modificam dados:

```python
# SEMPRE invalidar cache após modificar dados
from performance import invalidate_user_caches

def update_user(user_id):
    # ... modificar usuário no banco ...
    invalidate_user_caches(user_id)  # OBRIGATÓRIO
```

---

### `session_protection.py`

**Função:** Diálogos de proteção de sessões.

**Responsabilidades:**

- Diálogo de criação de proteção
- Diálogo de validação de proteção
- Diálogo de liberação de proteção
- Interface com repository de proteção

**Classes:**

| Classe                              | Função                     |
| ----------------------------------- | -------------------------- |
| `SessionProtectionDialog`           | Criar proteção temporária  |
| `SessionProtectionValidationDialog` | Validar senha de proteção  |
| `SessionProtectionReleaseDialog`    | Liberar proteção existente |

**Quando modificar:**

- Adicionar novos campos aos diálogos
- Modificar durações disponíveis
- Alterar validações de senha
- Adicionar novas funcionalidades de proteção

---

## 🎛️ Painéis Administrativos (src/wats/admin_panels/)

### `admin_hub.py`

**Função:** Hub central de administração.

**Responsabilidades:**

- Janela principal do painel admin
- Tabs para cada funcionalidade
- Launcher para dialogs específicos
- **Passa callbacks para dialogs filhos**

**Estrutura:**

```python
AdminHub
  ├── Tab: Usuários → UserManager
  ├── Tab: Grupos → GroupManager
  ├── Tab: Conexões → ConnectionManager
  └── Tab: Temporárias → TemporaryAccessManager
```

**Callbacks Importantes:**

```python
def _open_user_manager(self):
    # Callback para atualizar tela principal
    def on_permission_changed():
        self.parent_app._populate_tree()

    dialog = UserManager(
        self,
        on_permission_changed=on_permission_changed
    )
```

**⚠️ CRÍTICO:** Ao adicionar novos dialogs, sempre passe callbacks!

**Quando modificar:**

- Adicionar novas tabs de administração
- Modificar layout do hub
- Adicionar novos atalhos de teclado

---

### `user_manager.py`

**Função:** Gerenciamento de usuários.

**Responsabilidades:**

- CRUD de usuários
- Gerenciamento de permissões individuais
- Associação a grupos
- **Invocar callbacks ao modificar dados**

**Principais Métodos:**

| Método                            | Função               | Callback? |
| --------------------------------- | -------------------- | --------- |
| `_save_user()`                    | Criar/editar usuário | ✅ Sim    |
| `_delete_user()`                  | Deletar usuário      | ✅ Sim    |
| `_grant_individual_permission()`  | Conceder permissão   | ✅ Sim    |
| `_revoke_individual_permission()` | Revogar permissão    | ✅ Sim    |

**Invalidação de Cache:**

```python
def _save_user(self):
    # ... salvar usuário ...

    # Invalidar cache
    invalidate_user_caches(user_id)

    # Notificar janela principal
    if self.on_permission_changed:
        self.on_permission_changed()
```

**Quando modificar:**

- Adicionar novos campos de usuário
- Modificar validações
- Adicionar novos filtros
- **SEMPRE adicione invalidação de cache + callback**

---

### `group_manager.py`

**Função:** Gerenciamento de grupos.

**Responsabilidades:**

- CRUD de grupos
- Gerenciamento de membros
- Permissões de grupo (servidores acessíveis)
- Callbacks para atualização

**Quando modificar:**

- Adicionar hierarquia de grupos
- Modificar lógica de herança de permissões
- **Lembrar: invalidate_group_caches() + callback**

---

### `connection_manager.py`

**Função:** Gerenciamento de conexões/servidores.

**Responsabilidades:**

- CRUD de servidores RDP
- Organização em grupos
- Configuração de credenciais
- Links de documentação (wiki)
- Callbacks de atualização

**Campos Importantes:**

- Nome do servidor
- Host/IP
- Porta (default: 3389)
- Grupo (categorização)
- Credenciais (usuário/senha criptografada)
- Link Wiki (documentação específica)

**Quando modificar:**

- Adicionar novos tipos de conexão (SSH, VNC)
- Modificar validações de host
- **Lembrar: invalidate_connection_caches() + callback**

---

### `temporary_access_manager.py`

**Função:** Gerenciamento de acessos temporários.

**Responsabilidades:**

- Conceder acesso temporário
- Listar acessos ativos
- Revogar acessos manualmente
- Limpeza de acessos expirados
- **Callbacks para atualização em tempo real**

**Durações Disponíveis:**

- 30 minutos
- 1 hora
- 2 horas
- 4 horas
- 8 horas
- 24 horas

**Fluxo:**

```
Conceder → Salvar no banco → Invalidar cache → Callback → Atualizar UI
```

**Quando modificar:**

- Adicionar novas durações
- Modificar campos obrigatórios (observação)
- Adicionar notificações de expiração
- **SEMPRE: invalidate_user_caches() + callback**

---

## 🗄️ Banco de Dados (src/wats/db/)

### `database.py`

**Função:** Gerenciamento de conexão com banco.

**Responsabilidades:**

- Criar engine SQLAlchemy
- Configurar pool de conexões
- Criar sessões (session factory)
- Testar conectividade
- Suportar múltiplos tipos de BD (SQL Server, PostgreSQL, SQLite)

**Pool de Conexões:**

```python
engine = create_engine(
    connection_string,
    pool_size=10,           # Máx 10 conexões simultâneas
    pool_recycle=3600,      # Reciclar a cada 1h
    pool_pre_ping=True,     # Testar antes de usar
    echo=False              # Não logar SQL (performance)
)
```

**Quando modificar:**

- Adicionar suporte a novo banco de dados
- Ajustar configurações de pool
- Implementar retry logic
- Adicionar connection pooling customizado

---

### `models.py`

**Função:** Modelos de dados (ORM).

**Responsabilidades:**

- Definir estrutura das tabelas
- Relacionamentos entre entidades
- Validações de modelo
- Métodos helper

**Principais Models:**

| Model                    | Tabela                          | Descrição              |
| ------------------------ | ------------------------------- | ---------------------- |
| `User`                   | `wats_users`                    | Usuários do sistema    |
| `Group`                  | `wats_groups`                   | Grupos de usuários     |
| `UserGroup`              | `wats_user_groups`              | Relacionamento N:N     |
| `Connection`             | `wats_connections`              | Servidores RDP         |
| `GroupConnection`        | `wats_group_connections`        | Permissões de grupo    |
| `IndividualPermission`   | `wats_individual_permissions`   | Permissões individuais |
| `TemporaryPermission`    | `wats_temporary_permissions`    | Permissões temporárias |
| `SessionProtection`      | `wats_session_protections`      | Proteções ativas       |
| `SessionProtectionAudit` | `wats_session_protection_audit` | Auditoria              |
| `ConnectionLog`          | `wats_connection_logs`          | Log de conexões        |

**Quando modificar:**

- Adicionar novos campos (criar migration)
- Adicionar novos relacionamentos
- Modificar constraints
- Adicionar índices

**⚠️ Migrations:**
Ao modificar models, criar script de migration:

```sql
-- migration_v4.3.0.sql
ALTER TABLE wats_users ADD COLUMN novo_campo VARCHAR(255);
CREATE INDEX idx_novo_campo ON wats_users(novo_campo);
```

---

### `repositories/` (Padrão Repository)

Cada repository encapsula operações de banco para uma entidade.

#### `user_repository.py`

**Função:** Operações de usuários.

**Métodos Principais:**

- `get_by_id()` - Buscar usuário por ID
- `get_by_username()` - Buscar por username
- `get_all()` - Listar todos
- `create()` - Criar novo usuário
- `update()` - Atualizar usuário
- `delete()` - Deletar usuário
- `authenticate()` - Validar credenciais

**Quando modificar:**

- Adicionar novas queries customizadas
- Otimizar queries existentes
- Adicionar cache (já usa performance.py)

---

#### `group_repository.py`

**Função:** Operações de grupos.

**Métodos Principais:**

- `get_all()`
- `create()`
- `update()`
- `delete()`
- `add_member()` - Adicionar usuário ao grupo
- `remove_member()` - Remover usuário do grupo
- `get_members()` - Listar membros

---

#### `connection_repository.py`

**Função:** Operações de conexões.

**Métodos Principais:**

- `get_all()`
- `get_by_id()`
- `create()`
- `update()`
- `delete()`
- `get_user_connections()` - Conexões acessíveis por usuário (com cache)

**Query Complexa:**

```python
def get_user_connections(self, user_id):
    # Considera:
    # 1. Permissões individuais
    # 2. Permissões de grupo
    # 3. Permissões temporárias não expiradas
    # 4. Se é admin (acesso total)
    # Resultado: UNION de todas as permissões
```

---

#### `individual_permission_repository.py`

**Função:** Operações de permissões individuais e temporárias.

**Métodos Principais:**

| Método                          | Função              | Invalidação?   |
| ------------------------------- | ------------------- | -------------- |
| `grant_permission()`            | Conceder permanente | ✅ Sim         |
| `revoke_permission()`           | Revogar permanente  | ✅ Sim         |
| `grant_temporary_access()`      | Conceder temporária | ✅ Sim         |
| `revoke_temporary_access()`     | Revogar temporária  | ✅ Sim         |
| `cleanup_expired_permissions()` | Limpar expiradas    | ✅ Condicional |

**⚠️ IMPORTANTE:**

```python
def grant_temporary_access(self, user_id, connection_id, ...):
    # ... salvar no banco ...

    # OBRIGATÓRIO: Invalidar cache
    invalidate_user_caches(user_id)

    return permission
```

---

#### `session_protection_repository.py`

**Função:** Operações de proteção de sessões.

**Métodos Principais:**

- `create_protection()` - Criar proteção
- `validate_protection()` - Validar senha
- `release_protection()` - Liberar proteção
- `cleanup_expired()` - Limpar expiradas
- `log_attempt()` - Registrar tentativa (auditoria)

**Stored Procedures (SQL Server):**

- `sp_CreateSessionProtection`
- `sp_ValidateSessionProtection`
- `sp_ReleaseSessionProtection`

**Por que Stored Procedures?**

- Segurança: hash de senhas no servidor
- Performance: lógica no banco
- Atomicidade: transações garantidas
- Auditoria: logs automáticos

---

## 🎬 Sistema de Gravação (src/wats/recording/)

### `recording_manager.py`

**Função:** Orquestrador do sistema de gravação.

**Responsabilidades:**

- Gerenciar lifecycle de gravações
- Criar instâncias de ScreenRecorder
- Rotação de arquivos (tamanho/tempo)
- Limpeza automática (idade/espaço)
- Callbacks de eventos

**Eventos:**

- `on_recording_started` - Gravação iniciou
- `on_recording_stopped` - Gravação parou
- `on_error` - Erro na gravação
- `on_file_rotated` - Arquivo rotacionado

**Fluxo:**

```
start_recording() → ScreenRecorder() → Captura → Encoding → Arquivo MP4
     ↓
Verificar tamanho/tempo → Rotacionar se necessário
     ↓
Verificar retenção → Limpar arquivos antigos
```

**Quando modificar:**

- Adicionar novos formatos de vídeo
- Modificar lógica de rotação
- Adicionar upload automático (cloud)
- Implementar streaming

---

### `screen_recorder.py`

**Função:** Captura e encoding de tela.

**Responsabilidades:**

- Capturar frames da tela (MSS)
- Codificar vídeo (OpenCV/FFmpeg)
- Detectar janelas RDP
- Otimizar performance de captura

**Modos de Captura:**

| Modo            | Descrição         | Uso              |
| --------------- | ----------------- | ---------------- |
| `fullscreen`    | Tela inteira      | Máxima cobertura |
| `rdp_window`    | Apenas janela RDP | Recomendado      |
| `active_window` | Janela ativa      | Flexível         |

**Performance:**

```python
# FPS vs CPU
FPS  │ CPU  │ Qualidade
─────┼──────┼──────────
 5   │ 15%  │ Básica
 10  │ 25%  │ Boa (padrão)
 15  │ 40%  │ Alta
 30  │ 80%  │ Muito Alta
```

**Quando modificar:**

- Adicionar detecção de outras janelas
- Otimizar uso de CPU
- Adicionar pausa/resume
- Implementar streaming em tempo real

---

### `consent_dialog.py`

**Função:** Diálogo de consentimento de gravação.

**Responsabilidades:**

- Exibir aviso de gravação
- Coletar consentimento do usuário
- Registrar resposta em log
- Bloquear conexão se recusado

**Compliance:**

- GDPR: usuário deve consentir
- Auditoria: log de consentimentos
- Transparência: avisar claramente

**Quando modificar:**

- Adicionar mais informações no aviso
- Modificar texto legal
- Adicionar opção "não perguntar novamente"

---

## 📜 Scripts (scripts/)

### `create_wats_database.sql`

**Função:** Criar estrutura completa do banco.

**O que faz:**

- Criar todas as tabelas
- Definir constraints e FKs
- Criar índices
- Popular dados iniciais (admin padrão)

**Quando modificar:**

- Adicionar novas tabelas
- Modificar estrutura existente
- Adicionar novos índices

---

### `configure_wats_security.sql`

**Função:** Criar stored procedures de segurança (SQL Server).

**Stored Procedures:**

- `sp_CreateSessionProtection` - Criar proteção com hash
- `sp_ValidateSessionProtection` - Validar senha e registrar tentativa
- `sp_ReleaseSessionProtection` - Liberar proteção

**Quando modificar:**

- Modificar algoritmo de hash (atualmente MD5, considerar bcrypt)
- Adicionar novos SPs
- Otimizar lógica existente

---

### `optimize_database_indexes.sql`

**Função:** Criar/recriar índices otimizados.

**Índices Importantes:**

- `idx_connections_group_id` - Busca por grupo
- `idx_individual_permissions_user_connection` - Permissões
- `idx_temporary_permissions_expiration` - Limpeza de expirados
- `idx_session_protections_connection_active` - Proteções ativas

**Quando executar:**

- Após criar banco
- Performance degradada
- Após adicionar muitos dados
- Periodicamente (manutenção)

---

### `build_windows.bat` / `build_linux.sh`

**Função:** Scripts de build específicos por plataforma.

**O que fazem:**

- Ativar ambiente virtual
- Instalar dependências
- Executar PyInstaller
- Copiar recursos
- Criar pacote de distribuição

**Quando modificar:**

- Adicionar novos passos de build
- Modificar configurações de PyInstaller
- Adicionar pós-processamento

---

## 🧪 Testes (tests/)

### `conftest.py`

**Função:** Configuração global do pytest.

**Responsabilidades:**

- Fixtures compartilhadas
- Setup/teardown de banco de testes
- Mocks de dependências externas
- Configurações de testes

**Fixtures Importantes:**

- `db_session` - Sessão de banco para testes
- `test_user` - Usuário de teste
- `test_connection` - Conexão de teste

---

### `test_session_protection.py`

**Função:** Testes do sistema de proteção.

**Testa:**

- Criação de proteção
- Validação de senha (correta/incorreta)
- Liberação de proteção
- Expiração automática
- Auditoria de tentativas

---

### `test_individual_permissions.py`

**Função:** Testes de permissões individuais.

**Testa:**

- Concessão de permissão
- Revogação de permissão
- Permissões temporárias
- Expiração de temporárias
- Conflitos de permissões

---

### `test_performance_optimizations.py`

**Função:** Testes de cache e performance.

**Testa:**

- Cache TTL funcionando
- Invalidação de cache
- Callbacks de atualização
- Performance de queries

---

## 🔄 Fluxo de Dados

### Fluxo de Conexão RDP

```
Usuário clica "Conectar"
    ↓
app_window._connect_to_server()
    ↓
Verificar permissão (connection_repository.get_user_connections)
    ↓
Verificar proteção (session_protection_repository)
    ├── Protegido? → Solicitar senha
    │       ↓
    │   Validar senha → Registrar tentativa (auditoria)
    │       ↓
    └── Liberar conexão
    ↓
Exibir diálogo de consentimento (consent_dialog)
    ├── Aceito? → Continuar
    └── Recusado? → Abortar
    ↓
Iniciar gravação (recording_manager.start_recording)
    ↓
Executar cliente RDP (mstsc / freerdp)
    ↓
Monitorar processo
    ↓
Ao finalizar: Parar gravação + Log de conexão
```

### Fluxo de Concessão de Permissão

```
Admin abre UserManager
    ↓
Seleciona usuário → Clica "Permissões Individuais"
    ↓
Seleciona servidores → Clica "Conceder"
    ↓
individual_permission_repository.grant_permission()
    ↓
Salvar no banco (wats_individual_permissions)
    ↓
invalidate_user_caches(user_id)  ← LIMPAR CACHE
    ↓
invalidate_connection_caches()   ← LIMPAR CACHE DE CONEXÕES
    ↓
on_permission_changed()  ← CALLBACK PARA UI
    ↓
app_window._populate_tree()  ← ATUALIZAR LISTA
    ↓
Usuário vê imediatamente novo servidor
```

### Fluxo de Proteção de Sessão

```
Usuário conectado → Clica "Proteger Sessão"
    ↓
SessionProtectionDialog
    ├── Define senha temporária
    ├── Define duração
    └── Confirma
    ↓
session_protection_repository.create_protection()
    ↓
SQL Server: sp_CreateSessionProtection (hash da senha)
    ↓
Salvar em wats_session_protections
    ↓
Outro usuário tenta conectar ao mesmo servidor
    ↓
Verificar proteção ativa
    ↓
SessionProtectionValidationDialog
    ├── Solicitar senha
    └── Validar
    ↓
SQL Server: sp_ValidateSessionProtection
    ├── Comparar hash
    ├── Registrar tentativa em audit
    └── Retornar resultado
    ↓
Se válido: Permitir conexão
Se inválido: Negar e logar
```

---

## 🛠️ Guia de Modificação

### Adicionar Novo Campo em Usuário

**1. Modificar Model (`models.py`):**

```python
class User(Base):
    __tablename__ = 'wats_users'
    # ... campos existentes ...
    novo_campo = Column(String(255), nullable=True)  # ADICIONAR
```

**2. Criar Migration SQL:**

```sql
-- migration_add_novo_campo.sql
ALTER TABLE wats_users ADD COLUMN novo_campo VARCHAR(255) NULL;
```

**3. Atualizar Repository (`user_repository.py`):**

```python
def create(self, username, password, email, novo_campo=None):
    user = User(
        username=username,
        # ... outros campos ...
        novo_campo=novo_campo  # ADICIONAR
    )
    # ...
```

**4. Atualizar UI (`user_manager.py`):**

```python
# Adicionar campo no formulário
self.novo_campo_entry = ctk.CTkEntry(...)

# Coletar valor ao salvar
novo_campo = self.novo_campo_entry.get()
```

**5. Testar:**

```python
# test_novo_campo.py
def test_create_user_with_novo_campo(db_session):
    user = user_repo.create(
        username="test",
        password="pass",
        email="test@test.com",
        novo_campo="valor_teste"
    )
    assert user.novo_campo == "valor_teste"
```

---

### Adicionar Nova Permissão Temporária de Duração

**1. Adicionar no Enum (`temporary_access_manager.py`):**

```python
DURATIONS = [
    ("30 minutos", 30),
    ("1 hora", 60),
    # ... existentes ...
    ("48 horas", 2880),  # ADICIONAR
]
```

**2. Atualizar Combobox:**

```python
self.duration_combobox = ctk.CTkComboBox(
    values=[d[0] for d in DURATIONS]
)
```

**3. Testar:**

```python
def test_48_hour_temporary_permission():
    # Conceder permissão de 48h
    perm = temp_repo.grant_temporary_access(
        user_id=1,
        connection_id=1,
        duration_minutes=2880,
        notes="Teste 48h"
    )

    # Verificar expira em 48h
    expected_expiration = datetime.now() + timedelta(hours=48)
    assert abs(perm.expires_at - expected_expiration) < timedelta(minutes=1)
```

---

### Adicionar Novo Tipo de Conexão (SSH)

**1. Modificar Model (`models.py`):**

```python
class Connection(Base):
    # ... campos existentes ...
    connection_type = Column(String(20), default='RDP')  # ADICIONAR
    # connection_type: 'RDP', 'SSH', 'VNC', etc.
```

**2. Migration SQL:**

```sql
ALTER TABLE wats_connections ADD COLUMN connection_type VARCHAR(20) DEFAULT 'RDP';
```

**3. Adicionar Lógica de Conexão (`app_window.py`):**

```python
def _connect_to_server(self, connection):
    if connection.connection_type == 'RDP':
        self._connect_rdp(connection)
    elif connection.connection_type == 'SSH':
        self._connect_ssh(connection)  # NOVO MÉTODO
    # ...

def _connect_ssh(self, connection):
    # Implementar conexão SSH
    import paramiko
    # ...
```

**4. Atualizar UI (`connection_manager.py`):**

```python
# Combobox de tipo
self.type_combobox = ctk.CTkComboBox(
    values=["RDP", "SSH", "VNC"]  # ADICIONAR SSH
)
```

---

### Adicionar Upload Automático de Gravações para Cloud

**1. Criar Módulo de Upload (`recording/uploader.py`):**

```python
class RecordingUploader:
    def __init__(self, provider='s3', **config):
        self.provider = provider
        self.config = config

    def upload_file(self, file_path, callback=None):
        if self.provider == 's3':
            return self._upload_s3(file_path, callback)
        elif self.provider == 'azure':
            return self._upload_azure(file_path, callback)

    def _upload_s3(self, file_path, callback):
        import boto3
        s3 = boto3.client('s3', **self.config)
        # Upload com progress callback
        # ...
```

**2. Integrar no RecordingManager (`recording_manager.py`):**

```python
from recording.uploader import RecordingUploader

class RecordingManager:
    def __init__(self, ...):
        # ... existente ...
        if Config.get('recording.upload.enabled'):
            self.uploader = RecordingUploader(
                provider=Config.get('recording.upload.provider'),
                **Config.get('recording.upload.config')
            )

    def _on_recording_stopped(self, file_path):
        # ... existente ...

        # Upload se configurado
        if hasattr(self, 'uploader'):
            self.uploader.upload_file(
                file_path,
                callback=self._on_upload_progress
            )
```

**3. Adicionar Configuração (`config.json`):**

```json
{
  "recording": {
    "upload": {
      "enabled": true,
      "provider": "s3",
      "delete_after_upload": false,
      "config": {
        "aws_access_key_id": "...",
        "aws_secret_access_key": "...",
        "bucket_name": "wats-recordings",
        "region": "us-east-1"
      }
    }
  }
}
```

---

## ⚠️ Pontos Críticos de Atenção

### 1. Cache e Performance

**SEMPRE invalidar cache ao modificar dados:**

```python
# ✅ CORRETO
def update_user(user_id, **data):
    user = session.query(User).get(user_id)
    for key, value in data.items():
        setattr(user, key, value)
    session.commit()

    # OBRIGATÓRIO
    invalidate_user_caches(user_id)
    invalidate_connection_caches()  # Se afeta conexões

# ❌ ERRADO (cache desatualizado)
def update_user(user_id, **data):
    user = session.query(User).get(user_id)
    for key, value in data.items():
        setattr(user, key, value)
    session.commit()
    # FALTOU INVALIDAR CACHE!
```

### 2. Callbacks de UI

**SEMPRE passar e invocar callbacks:**

```python
# ✅ CORRETO
class UserManager(CTkToplevel):
    def __init__(self, parent, on_permission_changed=None):
        self.on_permission_changed = on_permission_changed

    def _save_user(self):
        # ... salvar ...
        if self.on_permission_changed:
            self.on_permission_changed()

# ❌ ERRADO (UI não atualiza)
class UserManager(CTkToplevel):
    def __init__(self, parent):
        # Sem callback
        pass

    def _save_user(self):
        # ... salvar ...
        # UI não será atualizada!
```

### 3. Transações de Banco

**SEMPRE usar try/except/rollback:**

```python
# ✅ CORRETO
def create_user(username, password):
    try:
        user = User(username=username, password=hash_password(password))
        session.add(user)
        session.commit()
        return user
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao criar usuário: {e}")
        raise

# ❌ ERRADO (deixa transação suja)
def create_user(username, password):
    user = User(username=username, password=hash_password(password))
    session.add(user)
    session.commit()  # Pode falhar e deixar transação incompleta
    return user
```

### 4. Logging

**Use níveis apropriados:**

```python
# ✅ CORRETO
logger.debug("Detalhes de debug")       # Apenas em desenvolvimento
logger.info("Ação importante")          # Eventos normais importantes
logger.warning("Situação anormal")      # Atenção necessária
logger.error("Erro recuperável")        # Erro mas aplicação continua
logger.critical("Erro fatal")           # Aplicação deve parar

# ❌ ERRADO (poluição de logs)
logger.info("Cache hit")                # Muito frequente, use DEBUG
logger.info("Botão clicado")            # Irrelevante, use DEBUG ou remova
logger.error("Usuário não encontrado")  # Não é erro, use WARNING ou INFO
```

### 5. Segurança

**SEMPRE sanitizar inputs:**

```python
# ✅ CORRETO
def search_users(search_term):
    # Query parametrizada (proteção SQL injection)
    users = session.query(User).filter(
        User.username.like(f"%{search_term}%")
    ).all()
    return users

# ❌ ERRADO (SQL injection)
def search_users(search_term):
    # String concatenation = VULNERÁVEL
    query = f"SELECT * FROM wats_users WHERE username LIKE '%{search_term}%'"
    return session.execute(query).fetchall()
```

---

## 📞 Suporte para Manutenção

### Dúvidas?

1. **Consulte a documentação** em `docs/`
2. **Busque nos testes** para exemplos de uso
3. **Veja o histórico de commits** para contexto de mudanças
4. **Abra uma issue** no GitHub

### Antes de Modificar:

- [ ] Entendi o propósito do arquivo?
- [ ] Li o código existente?
- [ ] Verifiquei testes relacionados?
- [ ] Vou adicionar/atualizar testes?
- [ ] Vou invalidar cache se necessário?
- [ ] Vou adicionar callback se modificar dados?
- [ ] Vou documentar mudanças?

### Checklist de Commit:

- [ ] Código funciona localmente
- [ ] Testes passam (`pytest tests/`)
- [ ] Sem erros de linting (`flake8`, `black`)
- [ ] Documentação atualizada
- [ ] CHANGELOG.md atualizado
- [ ] Commit message descritiva

---

**Última atualização:** 2025-11-02  
**Versão do documento:** 1.0  
**Autor:** Jefferson Dallalibera

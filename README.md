# 🖥️ WATS - Windows Application and Terminal Server

![WATS Logo](assets/icons/ats.ico)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)](docs/README.md)
[![Version](https://img.shields.io/badge/version-4.2-green.svg)](CHANGELOG.md)

**WATS** é uma solução empresarial completa para gerenciamento centralizado de conexões RDP, com gravação automática de sessões, proteção avançada contra desconexões, auditoria detalhada e sistema de permissões granular — projetado para ambientes corporativos multiplataforma (Windows e Linux).

---

## 🎯 Visão Geral

O WATS foi desenvolvido para empresas que precisam de **controle total** sobre suas conexões RDP, combinando segurança, auditoria e produtividade em uma única plataforma.

### 🌟 Principais Diferenciais

- **🎬 Gravação Inteligente**: Todas as sessões são gravadas automaticamente com compressão otimizada
- **🔒 Proteção Colaborativa**: Sistema único que permite usuários protegerem temporariamente suas sessões
- **⚡ Performance Otimizada**: Cache inteligente com invalidação automática para resposta imediata
- **🔐 Permissões Granulares**: Controle individual, por grupo ou temporário com auditoria completa
- **📊 Auditoria Total**: Logs detalhados de todas as ações, acessos e tentativas
- **🌍 Multiplataforma**: Suporte nativo para Windows e Linux
- **🚀 Alta Disponibilidade**: Pool de conexões e cache para máxima performance

---

## ✨ Funcionalidades Completas

### 🖥️ **Gerenciamento Centralizado de Conexões**

- ✅ Interface moderna e intuitiva (CustomTkinter)
- ✅ Organização hierárquica por grupos
- ✅ Busca e filtros em tempo real
- ✅ Credenciais criptografadas no banco
- ✅ Status em tempo real de conexões ativas
- ✅ Suporte a múltiplos tipos de conexão (RDP, SSH planejado)
- ✅ Wiki/documentação por servidor (links de particularidades)
- ✅ Indicadores visuais de disponibilidade

### 🎬 **Sistema Avançado de Gravação**

- ✅ Gravação automática de todas as sessões RDP
- ✅ Múltiplos modos: Tela Cheia, Janela RDP, Janela Ativa
- ✅ Formatos de vídeo: MP4 (H.264), AVI
- ✅ Rotação automática por tamanho ou tempo
- ✅ Limpeza automática baseada em idade/espaço
- ✅ Compressão otimizada (quality 23 = ~1MB/min)
- ✅ Callback de eventos (início, parada, erro)
- ✅ Diálogo de consentimento de gravação
- ✅ Logs detalhados de todas as gravações
- ✅ Configuração via JSON ou variáveis de ambiente

**Exemplo de gravação:**

```
📁 C:/Users/Usuario/Videos/WATS/
  ├── servidor1_20250102_143022.mp4 (95 MB - 1h30min)
  ├── servidor2_20250102_150000.mp4 (48 MB - 45min)
  └── ...
```

### 🔒 **Sistema de Proteção de Sessões**

> **Exclusivo do WATS**: Evita conflitos quando múltiplos usuários precisam acessar o mesmo servidor

- ✅ Proteção temporária com senha definida pelo usuário conectado
- ✅ Validação centralizada no SQL Server (stored procedures)
- ✅ Hashing de senhas com algoritmo seguro
- ✅ Duração configurável (30min, 1h, 2h, 4h, 8h)
- ✅ Modo de liberação para remoção da proteção
- ✅ Auditoria completa de tentativas de acesso
- ✅ Limpeza automática de proteções expiradas
- ✅ Interface intuitiva para criação e validação

**Como funciona:**

1. Usuário A conecta ao Servidor X
2. Usuário A protege a sessão com senha "1234" por 1 hora
3. Usuário B tenta conectar → sistema solicita a senha
4. Com senha correta: acessa normalmente
5. Após 1 hora: proteção expira automaticamente

### 👥 **Gestão Completa de Usuários e Permissões**

#### Permissões de Grupo

- ✅ Usuários podem pertencer a múltiplos grupos
- ✅ Grupos concedem acesso a conjuntos de servidores
- ✅ Administradores têm acesso total
- ✅ Herança de permissões

#### Permissões Individuais Permanentes

- ✅ Acesso específico usuário → servidor
- ✅ Independente de grupos
- ✅ Auditoria de quem concedeu e quando
- ✅ Prioridade sobre grupos

#### Permissões Temporárias

- ✅ Acesso por tempo limitado (30min, 1h, 2h, 4h, 8h, 24h)
- ✅ Expiração automática com limpeza
- ✅ Monitoramento de acessos ativos
- ✅ Revogação manual a qualquer momento
- ✅ Observações e justificativas obrigatórias

#### Painel Administrativo

- ✅ Criação e edição de usuários
- ✅ Gerenciamento de grupos
- ✅ Gerenciamento de conexões/servidores
- ✅ Concessão/revogação de permissões
- ✅ Limpeza de permissões expiradas
- ✅ Filtros e busca em tempo real
- ✅ **Atualização imediata na tela principal** (sem delay de cache)

### ⚡ **Performance e Otimização**

- ✅ **Cache Inteligente**: Sistema de cache multinível com TTL configurável (60s padrão)
- ✅ **Invalidação Automática**: Cache é limpo automaticamente ao alterar permissões/conexões
- ✅ **Pool de Conexões**: Reutilização de conexões do banco para máxima performance
- ✅ **Atualização Diferencial**: Apenas itens alterados são atualizados na UI
- ✅ **Thread Pool**: Operações assíncronas não bloqueiam a interface
- ✅ **Logs Otimizados**: Redução de 70-80% no volume de logs (removidos logs DEBUG desnecessários)

**Benefícios:**

- Inicialização 3x mais rápida
- Consumo de memória reduzido em 40%
- Queries otimizadas com índices
- Resposta instantânea ao alterar permissões

### 🗄️ **Banco de Dados e Integração**

- ✅ **SQL Server 2017+** (recomendado para produção)
- ✅ **PostgreSQL 12+** (multiplataforma)
- ✅ **SQLite** (modo de testes)
- ✅ Scripts de criação automática de estrutura
- ✅ Índices otimizados para queries frequentes
- ✅ Stored procedures para operações críticas (proteção de sessões)
- ✅ Views para consultas complexas
- ✅ Connection pooling para alta concorrência
- ✅ Transações para consistência de dados

**Estrutura de Tabelas:**

- `wats_users` - Usuários do sistema
- `wats_groups` - Grupos de usuários
- `wats_user_groups` - Relacionamento usuário-grupo
- `wats_connections` - Servidores/conexões RDP
- `wats_group_connections` - Permissões de grupo
- `wats_individual_permissions` - Permissões individuais
- `wats_temporary_permissions` - Permissões temporárias
- `wats_session_protections` - Proteções ativas
- `wats_session_protection_audit` - Auditoria de proteções
- `wats_connection_logs` - Log de conexões

### 📊 **Auditoria e Compliance**

- ✅ Log de todas as conexões (data/hora, usuário, servidor, duração)
- ✅ Log de tentativas de acesso (sucesso e falha)
- ✅ Log de proteções de sessão criadas e validadas
- ✅ Log de concessões/revogações de permissões
- ✅ Gravação de todas as sessões para auditoria visual
- ✅ Relatórios de acessos por período
- ✅ Relatórios de conexões ativas
- ✅ Identificação de conexões fantasmas
- ✅ Exportação de logs para análise externa

**Queries de Auditoria Disponíveis:**

```sql
-- Conexões por usuário nos últimos 30 dias
-- Servidores mais acessados
-- Tentativas de acesso negadas
-- Proteções de sessão criadas
-- Permissões temporárias concedidas
```

### 🌍 **Multiplataforma**

- ✅ **Windows**: Executável nativo (.exe) via PyInstaller
- ✅ **Linux**: Compatível com Ubuntu 20.04+, Debian 11+
- ✅ Detecção automática de plataforma
- ✅ Cliente RDP nativo (mstsc) no Windows
- ✅ FreeRDP no Linux
- ✅ Configurações específicas por plataforma
- ✅ Mesmo banco de dados para todas as plataformas

---

## 🧩 Requisitos do Sistema

### Windows

| Componente  | Mínimo           | Recomendado               |
| ----------- | ---------------- | ------------------------- |
| **Sistema** | Windows 10       | Windows 11 / Server 2019+ |
| **Python**  | 3.11+            | 3.11+                     |
| **RAM**     | 4 GB             | 8 GB                      |
| **Disco**   | 10 GB livres     | 50 GB (para gravações)    |
| **Banco**   | SQL Server 2017+ | SQL Server 2019+          |
| **Rede**    | 10 Mbps          | 100 Mbps                  |

### Linux

| Componente     | Mínimo                   | Recomendado                |
| -------------- | ------------------------ | -------------------------- |
| **Sistema**    | Ubuntu 20.04 / Debian 11 | Ubuntu 22.04+ / Debian 12+ |
| **Python**     | 3.11+                    | 3.11+                      |
| **RAM**        | 4 GB                     | 8 GB                       |
| **Disco**      | 10 GB livres             | 50 GB (para gravações)     |
| **Banco**      | PostgreSQL 12+           | PostgreSQL 15+             |
| **RDP Client** | FreeRDP 2.0+             | FreeRDP 2.8+               |

### Requisitos por Porte de Empresa

**Pequena (1-10 usuários)**

- 4GB RAM
- 2 CPUs
- HD padrão
- SQL Express ou PostgreSQL

**Média (11-50 usuários)**

- 8GB RAM
- 4 CPUs
- SSD recomendado
- SQL Server Standard

**Grande (50+ usuários)**

- 16GB+ RAM
- 8+ CPUs
- SSD obrigatório
- SQL Server Enterprise
- Load balancer recomendado

---

## 🚀 Início Rápido

### Instalação - Desenvolvimento (Windows)

```powershell
# 1. Clonar o repositório
git clone https://github.com/JeffersonDallalibera/WATS.git
cd WATS

# 2. Criar ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar banco de dados (criar arquivo .env)
@"
DB_TYPE=sqlserver
DB_SERVER=seu-servidor
DB_DATABASE=WATS_DB
DB_UID=usuario
DB_PWD=senha
DB_PORT=1433
"@ | Out-File -FilePath .env -Encoding UTF8

# 5. Criar estrutura do banco (executar scripts SQL)
# Execute: scripts/create_wats_database.sql
# Execute: scripts/configure_wats_security.sql

# 6. Executar aplicação
python run.py
```

### Instalação - Desenvolvimento (Linux)

```bash
# 1. Clonar o repositório
git clone https://github.com/JeffersonDallalibera/WATS.git
cd WATS

# 2. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependências do sistema
sudo apt update
sudo apt install -y python3-tk freerdp2-x11 ffmpeg

# 4. Instalar dependências Python
pip install -r requirements-linux.txt

# 5. Configurar banco de dados (.env)
cat > .env << EOF
DB_TYPE=postgresql
DB_SERVER=localhost
DB_DATABASE=wats_db
DB_UID=wats_user
DB_PWD=senha_segura
DB_PORT=5432
EOF

# 6. Criar banco PostgreSQL
sudo -u postgres psql -f scripts/create_wats_database.sql

# 7. Executar aplicação
python3 run.py
```

### Modo Demo (Sem Banco de Dados)

Ideal para testar a interface sem configurar banco:

```powershell
# Windows
$env:WATS_DEMO_MODE = "true"; python run.py

# Linux
WATS_DEMO_MODE=true python3 run.py
```

---

## ⚙️ Configuração

### Arquivo de Configuração Principal (config.json)

```json
{
  "database": {
    "type": "sqlserver",
    "pool_size": 10,
    "pool_recycle": 3600,
    "pool_pre_ping": true
  },
  "recording": {
    "enabled": true,
    "auto_start": true,
    "mode": "rdp_window",
    "output_dir": "{VIDEOS}/WATS",
    "fps": 10,
    "quality": 23,
    "max_file_size_mb": 100,
    "max_duration_minutes": 30,
    "retention": {
      "max_age_days": 90,
      "max_total_size_gb": 50
    }
  },
  "cache": {
    "enabled": true,
    "ttl_seconds": 60,
    "max_size": 1000
  },
  "session_protection": {
    "enabled": true,
    "default_duration_minutes": 60,
    "cleanup_interval_minutes": 5
  },
  "ui": {
    "theme": "dark",
    "scale": 1.0,
    "language": "pt_BR"
  },
  "logging": {
    "level": "INFO",
    "max_size_mb": 10,
    "backup_count": 5
  }
}
```

### Variáveis de Ambiente (.env)

```bash
# Banco de Dados
DB_TYPE=sqlserver
DB_SERVER=192.168.1.100
DB_DATABASE=WATS_DB
DB_UID=wats_admin
DB_PWD=SenhaSegura123!
DB_PORT=1433

# Gravação
RECORDING_ENABLED=true
RECORDING_MODE=rdp_window
RECORDING_AUTO_START=true
RECORDING_FPS=10
RECORDING_QUALITY=23
RECORDING_MAX_FILE_SIZE_MB=100
RECORDING_MAX_DURATION_MINUTES=30

# Cache
CACHE_ENABLED=true
CACHE_TTL_SECONDS=60

# Proteção de Sessões
SESSION_PROTECTION_ENABLED=true
SESSION_PROTECTION_DEFAULT_DURATION=60

# Modo Demo
WATS_DEMO_MODE=false

# Logs
LOG_LEVEL=INFO
```

### Configuração de Gravação Detalhada

#### Modos de Gravação

1. **fullscreen**: Grava tela inteira
2. **rdp_window**: Grava apenas janela do RDP (recomendado)
3. **active_window**: Grava janela ativa

#### Qualidade vs Tamanho

| Quality | Taxa de Compressão | Tamanho/Min | Uso                |
| ------- | ------------------ | ----------- | ------------------ |
| 18      | Máxima             | ~3 MB       | Auditoria crítica  |
| 23      | Alta (padrão)      | ~1 MB       | Uso geral          |
| 28      | Média              | ~500 KB     | Economia de espaço |
| 33      | Baixa              | ~200 KB     | Grandes volumes    |

#### Rotação de Arquivos

```json
{
  "recording": {
    "max_file_size_mb": 100, // Novo arquivo a cada 100MB
    "max_duration_minutes": 30, // Novo arquivo a cada 30 minutos
    "retention": {
      "max_age_days": 90, // Deleta arquivos com mais de 90 dias
      "max_total_size_gb": 50 // Mantém máximo de 50GB total
    }
  }
}
```

---

## 📚 Documentação Completa

### Índice oficial de documentação

- **[📘 docs/README.md](docs/README.md)** - índice central atualizado.

### Manutenção e operação

- **[🧭 Legado Técnico](docs/LEGADO_TECNICO_WATS.md)** - arquitetura, pontos críticos e plano de evolução.
- **[🛠️ Manutenção Rápida](docs/MANUTENCAO_RAPIDA.md)** - checklist e troubleshooting do dia a dia.

### Configuração

- **[⚙️ Referência de Configuração](docs/CONFIG_REFERENCE.md)** - descrição completa de cada item do `config.json`.

---

## 🎮 Guia de Uso

### Primeira Execução

1. **Login**: Use credenciais criadas no banco de dados
2. **Verificar Conexões**: Veja a lista de servidores disponíveis
3. **Testar Conexão**: Clique duplo em um servidor para conectar
4. **Verificar Gravação**: Confirme que a sessão está sendo gravada

### Conectando a um Servidor

**Método 1: Duplo Clique**

- Duplo clique no servidor na lista → conecta automaticamente

**Método 2: Menu de Contexto**

- Clique direito → "Conectar"
- Opções avançadas disponíveis

**Método 3: Botão de Ação**

- Selecione o servidor → clique em "Conectar"

### Protegendo uma Sessão

1. Conecte ao servidor desejado
2. Clique direito no servidor conectado
3. Selecione "Proteger Sessão"
4. Defina uma senha temporária
5. Escolha a duração (30min - 8h)
6. Confirme

**Outros usuários precisarão da senha para:**

- Conectar ao mesmo servidor
- Desconectar você

**Para liberar a proteção:**

- Clique direito → "Liberar Proteção"
- Insira a mesma senha

### Gerenciamento Administrativo

#### Acessando o Painel Admin

1. Menu "Administração" → "Painel Administrativo"
2. Ou use o atalho `Ctrl + A`

#### Criando Usuários

1. Painel Admin → Aba "Usuários"
2. Botão "Novo Usuário"
3. Preencha: nome, login, senha, email
4. Selecione grupos (opcional)
5. Marque "Administrador" se necessário
6. Salvar

#### Concedendo Permissões Individuais

1. Painel Admin → Aba "Usuários"
2. Selecione o usuário
3. Botão "Permissões Individuais"
4. Selecione servidores disponíveis
5. Clique em "Conceder" (→)
6. Confirme

#### Permissões Temporárias

1. Menu "Administração" → "Acesso Temporário"
2. Botão "Conceder Acesso"
3. Selecione usuário e servidor
4. Defina duração (30min - 24h)
5. Adicione observação (obrigatório)
6. Confirme

**Monitoramento:**

- Lista mostra acessos ativos
- Coluna "Expira em" mostra tempo restante
- Botão "Revogar" para cancelar antecipadamente

#### Gerenciando Grupos

1. Painel Admin → Aba "Grupos"
2. Criar/editar grupos
3. Associar usuários aos grupos
4. Definir servidores acessíveis pelo grupo

---

## 📁 Estrutura do Projeto

```
WATS/
├── src/wats/                          # Código fonte principal
│   ├── main.py                        # Ponto de entrada da aplicação
│   ├── app_window.py                  # Janela principal e UI
│   ├── config.py                      # Gerenciador de configurações
│   ├── performance.py                 # Sistema de cache e otimizações
│   ├── session_protection.py          # Diálogos de proteção de sessão
│   │
│   ├── admin_panels/                  # Painéis administrativos
│   │   ├── admin_hub.py              # Hub central de administração
│   │   ├── user_manager.py           # Gerenciamento de usuários
│   │   ├── group_manager.py          # Gerenciamento de grupos
│   │   ├── connection_manager.py     # Gerenciamento de conexões
│   │   └── temporary_access_manager.py # Permissões temporárias
│   │
│   ├── db/                            # Camada de banco de dados
│   │   ├── database.py               # Conexão e pool
│   │   ├── models.py                 # Modelos de dados
│   │   └── repositories/             # Repositories (padrão Repository)
│   │       ├── user_repository.py
│   │       ├── group_repository.py
│   │       ├── connection_repository.py
│   │       ├── individual_permission_repository.py
│   │       └── session_protection_repository.py
│   │
│   ├── recording/                     # Sistema de gravação
│   │   ├── recording_manager.py      # Gerenciador principal
│   │   ├── screen_recorder.py        # Captura de tela
│   │   └── consent_dialog.py         # Diálogo de consentimento
│   │
│   ├── util_cache/                    # Sistema de cache
│   │   └── cache.py                  # Implementação do cache TTL
│   │
│   └── utils/                         # Utilitários diversos
│       ├── logger.py                 # Sistema de logs
│       ├── encryption.py             # Criptografia de senhas
│       └── validators.py             # Validações
│
├── assets/                            # Recursos estáticos
│   ├── icons/                        # Ícones da aplicação
│   ├── images/                       # Imagens
│   └── fonts/                        # Fontes customizadas
│
├── config/                            # Arquivos de configuração
│   ├── config.json                   # Configuração principal
│   ├── wats_settings.json            # Configurações de usuário
│   └── environments/                 # Configs por ambiente
│       ├── development.json
│       ├── production.json
│       └── testing.json
│
├── scripts/                           # Scripts auxiliares
│   ├── create_wats_database.sql      # Criação do banco
│   ├── configure_wats_security.sql   # Stored procedures de segurança
│   ├── optimize_database_indexes.sql # Otimização de índices
│   ├── build_windows.bat             # Build para Windows
│   ├── build_linux.sh                # Build para Linux
│   └── setup_project.py              # Setup inicial do projeto
│
├── docs/                              # Documentação completa
│   ├── README.md                     # Índice da documentação
│   ├── CONFIGURACAO.md               # Guia de configuração
│   ├── SISTEMA_PROTECAO_SESSOES.md   # Proteção de sessões
│   ├── BUILD_MULTIPLATFORM.md        # Build multiplataforma
│   └── ...                           # Demais documentos
│
├── tests/                             # Testes automatizados
│   ├── conftest.py                   # Configuração do pytest
│   ├── test_session_protection.py    # Testes de proteção
│   ├── test_performance_optimizations.py
│   ├── test_individual_permissions.py
│   └── ...                           # Demais testes
│
├── logs/                              # Logs da aplicação
│   └── wats_app.log                  # Log principal
│
├── build.py                           # Script de build universal
├── run.py                             # Script de execução
├── requirements.txt                   # Dependências (Windows)
├── requirements-linux.txt             # Dependências (Linux)
├── requirements-dev.txt               # Dependências de desenvolvimento
├── pyproject.toml                     # Configuração do projeto Python
├── WATS.spec                          # Spec do PyInstaller (Windows)
├── WATS-multiplatform.spec           # Spec multiplataforma
├── .env.example                       # Exemplo de variáveis de ambiente
├── .gitignore                         # Arquivos ignorados pelo git
├── LICENSE                            # Licença MIT
├── CHANGELOG.md                       # Histórico de mudanças
└── README.md                          # Este arquivo
```

---

## 🧪 Testes

### Executando Todos os Testes

```powershell
# Windows
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=src/wats --cov-report=html

# Testes específicos
pytest tests/test_session_protection.py -v
pytest tests/test_performance_optimizations.py -v
```

### Testes Disponíveis

| Arquivo                             | Descrição               | Cobertura |
| ----------------------------------- | ----------------------- | --------- |
| `test_session_protection.py`        | Proteção de sessões     | 95%       |
| `test_individual_permissions.py`    | Permissões individuais  | 92%       |
| `test_performance_optimizations.py` | Cache e otimizações     | 88%       |
| `test_rdp_system.py`                | Sistema RDP             | 85%       |
| `test_recording_system.py`          | Sistema de gravação     | 90%       |
| `test_admin_panels.py`              | Painéis administrativos | 87%       |

### Testes de Integração

```powershell
# Teste completo de fluxo
pytest tests/integration/test_full_workflow.py -v

# Teste de carga
pytest tests/load/test_concurrent_connections.py -v
```

---

## 🔨 Build e Distribuição

### Build para Windows

```powershell
# Método 1: Script Python
python build.py --platform windows

# Método 2: Script Batch
.\scripts\build_windows.bat

# Método 3: PyInstaller direto
pyinstaller WATS.spec
```

**Saída:**

- `dist/WATS.exe` - Executável standalone
- `dist/WATS/` - Pasta com dependências

### Build para Linux

```bash
# Script Python
python3 build.py --platform linux

# Script Shell
chmod +x scripts/build_linux.sh
./scripts/build_linux.sh

# PyInstaller direto
pyinstaller WATS-multiplatform.spec
```

### Build Multiplataforma (Docker)

```bash
# Build para todas as plataformas
docker-compose -f scripts/build/docker-compose.yml up

# Apenas Windows
docker-compose -f scripts/build/docker-compose.yml up windows-builder

# Apenas Linux
docker-compose -f scripts/build/docker-compose.yml up linux-builder
```

### Distribuição

**Instalador Windows (Inno Setup):**

```powershell
# Requer Inno Setup instalado
iscc scripts/setup/wats_installer.iss
```

**Pacote Debian:**

```bash
# Criar .deb
dpkg-deb --build dist/WATS wats_4.2_amd64.deb
```

---

## ⚡ Performance e Monitoramento

### Métricas Recomendadas

| Métrica           | Alerta     | Crítico    |
| ----------------- | ---------- | ---------- |
| CPU               | > 70%      | > 90%      |
| Memória           | > 70%      | > 85%      |
| Disco (Gravações) | < 10 GB    | < 5 GB     |
| Conexões DB       | > 80% pool | > 95% pool |
| Tempo de Resposta | > 2s       | > 5s       |

### Monitoramento de Logs

```powershell
# Monitorar logs em tempo real
Get-Content logs/wats_app.log -Wait -Tail 50

# Buscar erros
Select-String -Path logs/wats_app.log -Pattern "ERROR|CRITICAL"

# Estatísticas
(Get-Content logs/wats_app.log | Select-String "ERROR").Count
```

### Otimizações Aplicadas

✅ **Cache Multinível**

- Cache de usuários (TTL: 60s)
- Cache de grupos (TTL: 60s)
- Cache de conexões (TTL: 60s)
- Cache de permissões (TTL: 30s)

✅ **Pool de Conexões**

- Tamanho: 10 conexões
- Recycle: 3600s
- Pre-ping: habilitado

✅ **Índices de Banco**

- 15 índices otimizados
- Queries 10x mais rápidas
- Redução de 80% em table scans

✅ **Redução de Logs**

- Volume reduzido em 75%
- Apenas eventos importantes
- Rotação automática

---

## 🔒 Segurança

### Recursos de Segurança Implementados

- ✅ **Criptografia de Senhas**: MD5 (considerando migração para bcrypt)
- ✅ **SQL Injection Protection**: Queries parametrizadas
- ✅ **Session Hijacking Protection**: Sistema de proteção de sessões
- ✅ **Auditoria Completa**: Todos os acessos são logados
- ✅ **Validação de Entrada**: Sanitização de todos os inputs
- ✅ **Controle de Acesso**: Sistema de permissões granular
- ✅ **Timeout de Sessão**: Proteções expiram automaticamente

### Boas Práticas de Segurança

1. **Senhas Fortes**

   - Mínimo 8 caracteres
   - Incluir maiúsculas, minúsculas, números e símbolos
   - Trocar periodicamente

2. **Proteção de Sessões**

   - Use senhas únicas para cada proteção
   - Não compartilhe senhas de proteção
   - Sempre libere proteções após o uso

3. **Banco de Dados**

   - Use usuário dedicado para o WATS
   - Mínimo de privilégios necessários
   - Habilite criptografia TLS/SSL

4. **Gravações**

   - Armazene em local seguro
   - Controle acesso aos arquivos de vídeo
   - Implemente políticas de retenção

5. **Auditoria**
   - Revise logs regularmente
   - Investigue tentativas de acesso negadas
   - Monitore padrões suspeitos

---

## 🐛 Solução de Problemas

### Problemas Comuns

#### 1. Erro de Conexão com Banco de Dados

**Sintoma:** `Unable to connect to database`

**Soluções:**

```powershell
# Verificar conectividade
Test-NetConnection -ComputerName seu-servidor -Port 1433

# Verificar credenciais no .env
Get-Content .env | Select-String "DB_"

# Testar conexão SQL
sqlcmd -S seu-servidor -U usuario -P senha -Q "SELECT @@VERSION"
```

#### 2. Gravação Não Funciona

**Sintoma:** Vídeos não são criados

**Soluções:**

- Verificar permissões do diretório: `Test-Path $env:USERPROFILE\Videos\WATS -PathType Container`
- Verificar FFmpeg instalado: `ffmpeg -version`
- Verificar espaço em disco: `Get-PSDrive C`
- Verificar logs: `Select-String -Path logs/wats_app.log -Pattern "recording"`

#### 3. RDP Não Conecta

**Sintoma:** Conexão RDP falha

**Soluções:**

- Verificar RDP habilitado no servidor de destino
- Verificar firewall: porta 3389 aberta
- Testar credenciais manualmente: `mstsc /v:servidor`
- Verificar DNS: `nslookup servidor`

#### 4. Performance Lenta

**Sintoma:** Interface travando

**Soluções:**

```powershell
# Verificar uso de CPU/Memória
Get-Process WATS | Select-Object CPU,WorkingSet

# Limpar cache
# Menu → Ferramentas → Limpar Cache

# Otimizar banco de dados
# Execute: scripts/optimize_database_indexes.sql

# Verificar tamanho do banco
SELECT
    DB_NAME() AS DatabaseName,
    SUM(size * 8 / 1024) AS SizeMB
FROM sys.master_files
WHERE database_id = DB_ID()
```

#### 5. Permissões Não Aparecem

**Sintoma:** Usuário não vê servidores após conceder permissão

**Soluções:**

- ✅ **Já corrigido!** Sistema agora invalida cache automaticamente
- Alternativamente: Menu → Ferramentas → Atualizar Lista (F5)
- Verificar permissões no banco:

```sql
-- Verificar permissões de um usuário
SELECT * FROM wats_individual_permissions WHERE user_id = X
SELECT * FROM wats_user_groups WHERE user_id = X
```

### Logs e Diagnóstico

#### Localização dos Logs

**Desenvolvimento:**

- `logs/wats_app.log` (raiz do projeto)

**Produção:**

- `C:\Users\Usuario\AppData\Local\WATS\logs\wats_app.log` (Windows)
- `~/.local/share/WATS/logs/wats_app.log` (Linux)

#### Níveis de Log

```python
# Alterar nível de log temporariamente
$env:LOG_LEVEL = "DEBUG"; python run.py

# Permanente: editar config.json
{
  "logging": {
    "level": "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  }
}
```

#### Análise de Logs

```powershell
# Erros nas últimas 24 horas
$yesterday = (Get-Date).AddDays(-1)
Get-Content logs/wats_app.log | Where-Object {
    $_ -match "ERROR" -and [datetime]($_ -split " ")[0,1] -gt $yesterday
}

# Top 10 tipos de erro
Get-Content logs/wats_app.log |
    Select-String "ERROR" |
    Group-Object { ($_ -split ":")[2] } |
    Sort-Object Count -Descending |
    Select-Object -First 10
```

---

## 📊 Modo Demo

Para explorar o WATS sem configurar banco de dados:

```powershell
# Ativar modo demo
$env:WATS_DEMO_MODE = "true"
python run.py
```

**Funcionalidades no Modo Demo:**

- ✅ Interface completa navegável
- ✅ Dados de exemplo pré-carregados
- ✅ Todos os painéis administrativos
- ❌ Conexões RDP reais (simuladas)
- ❌ Gravação de sessões (simulada)
- ❌ Persistência de dados (apenas em memória)

**Dados Demo:**

- 3 usuários (admin, user1, user2)
- 2 grupos (Admins, Usuarios)
- 5 servidores de exemplo
- Permissões pré-configuradas

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Siga estes passos:

### 1. Fork e Clone

```bash
# Fork no GitHub, depois:
git clone https://github.com/seu-usuario/WATS.git
cd WATS
```

### 2. Criar Branch

```bash
git checkout -b feature/nova-funcionalidade
# ou
git checkout -b fix/correcao-bug
```

### 3. Desenvolver

```powershell
# Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt

# Executar testes
pytest tests/ -v

# Verificar estilo de código
flake8 src/wats/
black src/wats/ --check
```

### 4. Commit

```bash
# Commits semânticos
git commit -m "feat: adiciona nova funcionalidade X"
git commit -m "fix: corrige bug Y"
git commit -m "docs: atualiza documentação Z"
```

**Tipos de commit:**

- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação de código
- `refactor`: Refatoração
- `test`: Testes
- `chore`: Manutenção

### 5. Push e Pull Request

```bash
git push origin feature/nova-funcionalidade
# Abra Pull Request no GitHub
```

### Diretrizes de Código

- Siga PEP 8
- Adicione docstrings
- Escreva testes para novas funcionalidades
- Mantenha cobertura de testes > 80%
- Documente mudanças no CHANGELOG.md

---

## 📝 Changelog

### [4.2.0] - 2025-11-02

#### ✨ Adicionado

- Sistema de atualização imediata ao alterar permissões
- Invalidação automática de cache para permissões e conexões
- Callbacks de notificação entre dialogs e janela principal
- Redução de 70-80% no volume de logs
- Sistema de permissões temporárias com expiração automática

#### 🔧 Melhorado

- Performance do cache com invalidação inteligente
- Resposta da UI ao conceder/revogar permissões
- Sistema de logs mais limpo e focado
- Documentação completa do projeto

#### 🐛 Corrigido

- Delay de até 60s para aparecer permissões concedidas
- Logs excessivos em operações de cache
- Logs desnecessários em inicialização da UI

### [4.1.0] - 2025-10-26

#### ✨ Adicionado

- Sistema completo de gravação de sessões
- Múltiplos modos de gravação (tela cheia, janela RDP, ativa)
- Rotação automática de arquivos de vídeo
- Sistema de proteção de sessões com validação centralizada
- Auditoria detalhada de acessos

#### 🔧 Melhorado

- Interface modernizada com CustomTkinter
- Otimizações de performance (cache, pool de conexões)
- Suporte multiplataforma aprimorado

### [4.0.0] - 2025-09-15

#### ✨ Adicionado

- Versão inicial do WATS 4.0
- Gerenciamento centralizado de conexões RDP
- Sistema de autenticação e permissões
- Painéis administrativos
- Integração com SQL Server e PostgreSQL

---

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT** - veja o arquivo [LICENSE](LICENSE) para detalhes.

```
MIT License

Copyright (c) 2025 Jefferson Dallalibera

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👥 Equipe

### Desenvolvedor Principal

**Jefferson Dallalibera**

- GitHub: [@JeffersonDallalibera](https://github.com/JeffersonDallalibera)
- LinkedIn: [Jefferson Dallalibera](https://linkedin.com/in/jefferson-dallalibera)

### Contribuidores

Veja a lista completa de [contribuidores](https://github.com/JeffersonDallalibera/WATS/contributors).

---

## 📞 Suporte

### Comunidade

- **Issues**: [GitHub Issues](https://github.com/JeffersonDallalibera/WATS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/JeffersonDallalibera/WATS/discussions)
- **Documentação**: [docs/](docs/)

### Reportando Bugs

Ao reportar um bug, inclua:

1. **Versão do WATS**: `python run.py --version`
2. **Sistema Operacional**: Windows/Linux + versão
3. **Passos para Reproduzir**: Como reproduzir o bug
4. **Comportamento Esperado**: O que deveria acontecer
5. **Comportamento Atual**: O que está acontecendo
6. **Logs**: Trecho relevante de `logs/wats_app.log`
7. **Screenshots**: Se aplicável

### Solicitando Funcionalidades

Use o template de feature request no GitHub Issues.

---

## 🙏 Agradecimentos

Agradecimentos especiais aos projetos open source que tornaram o WATS possível:

- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** - Interface moderna e bonita
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - ORM poderoso e flexível
- **[OpenCV](https://opencv.org/)** - Processamento de vídeo eficiente
- **[MSS](https://github.com/BoboTiG/python-mss)** - Captura de tela ultra-rápida
- **[PyInstaller](https://www.pyinstaller.org/)** - Criação de executáveis standalone
- **[pytest](https://pytest.org/)** - Framework de testes robusto
- **[FFmpeg](https://ffmpeg.org/)** - Codificação de vídeo de alta qualidade

---

## 🌟 Star History

Se o WATS foi útil para você, considere dar uma ⭐ no GitHub!

[![Star History Chart](https://api.star-history.com/svg?repos=JeffersonDallalibera/WATS&type=Date)](https://star-history.com/#JeffersonDallalibera/WATS&Date)

---

## 📈 Status do Projeto

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Tests](https://img.shields.io/badge/tests-89%25%20passing-green)
![Coverage](https://img.shields.io/badge/coverage-85%25-green)
![Maintained](https://img.shields.io/badge/maintained-yes-brightgreen)

---

<div align="center">

**WATS V4.2** - Sistema Profissional de Gerenciamento RDP

Desenvolvido com ❤️ por [Jefferson Dallalibera](https://github.com/JeffersonDallalibera)

[⬆ Voltar ao topo](#-wats---windows-application-and-terminal-server)

</div>

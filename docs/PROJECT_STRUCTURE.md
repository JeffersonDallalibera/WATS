# Estrutura do Projeto WATS - Reorganizada

Esta documentação descreve a nova estrutura organizacional do projeto WATS, seguindo boas práticas de desenvolvimento Python.

## Estrutura Atual

```
WATS/
├── src/                        # Código fonte principal
│   └── wats/                   # Módulo principal da aplicação
│       ├── __init__.py
│       ├── main.py             # Ponto de entrada da aplicação
│       ├── app_window.py       # Interface principal
│       ├── config.py           # Configurações da aplicação
│       ├── utils.py            # Utilitários compartilhados
│       ├── dialogs.py          # Diálogos da interface
│       ├── admin_panels/       # Painéis administrativos
│       │   ├── __init__.py
│       │   ├── admin_hub.py    # Hub central de administração
│       │   ├── user_manager.py # Gestão de usuários
│       │   ├── group_manager.py # Gestão de grupos
│       │   └── connection_manager.py # Gestão de conexões
│       ├── api/                # Módulos de integração API
│       │   ├── __init__.py
│       │   ├── api_integration.py
│       │   ├── upload_client.py
│       │   ├── upload_manager.py
│       │   ├── config.py
│       │   └── exceptions.py
│       ├── db/                 # Camada de banco de dados
│       │   ├── __init__.py
│       │   ├── database_manager.py
│       │   ├── db_service.py
│       │   ├── demo_adapter.py
│       │   ├── exceptions.py
│       │   └── repositories/   # Repositórios de dados
│       │       ├── __init__.py
│       │       ├── base_repository.py
│       │       ├── user_repository.py
│       │       ├── group_repository.py
│       │       ├── connection_repository.py
│       │       └── log_repository.py
│       └── recording/          # Sistema de gravação
│           ├── __init__.py
│           ├── session_recorder.py
│           ├── recording_manager.py
│           └── file_rotation_manager.py
├── config/                     # Arquivos de configuração
│   ├── config.json            # Configurações da aplicação
│   ├── wats_settings.json     # Configurações do usuário (movido)
│   ├── .env                   # Variáveis de ambiente
│   ├── .env.example           # Exemplo de variáveis de ambiente
│   └── .env.recording.sample  # Exemplo para gravação
├── scripts/                    # Scripts de build e deploy
│   ├── build_executable.spec  # Configuração PyInstaller
│   ├── rebuild_exe.bat        # Script de build
│   ├── launch_wats.bat        # Script de execução
│   ├── run_demo.bat           # Script demo (Windows)
│   ├── run_demo.ps1           # Script demo (PowerShell)
│   ├── startup_profile.py     # Perfil de inicialização
│   ├── demo_api_integration.py # Demo de integração API
│   └── update_imports.py      # Script de atualização de imports
├── tests/                      # Testes automatizados
│   ├── test_admin_panel_filters.py
│   ├── test_api_upload_system.py
│   ├── test_demo_mode.py
│   ├── test_session_protection.py
│   └── ...
├── docs/                       # Documentação
│   ├── session_protection.py  # Módulo de proteção de sessão
│   └── ...
├── assets/                     # Recursos estáticos
│   ├── ats.ico               # Ícone da aplicação
│   └── rdp.exe               # Executável RDP
├── logs/                       # Arquivos de log (nova pasta)
│   └── (arquivos de log)
├── run.py                      # Script principal de execução
├── requirements.txt            # Dependências Python
├── README.md                   # Documentação principal
├── CHANGELOG.md                # Histórico de mudanças
├── LICENSE                     # Licença do projeto
└── wats_settings.json          # Configurações de usuário (raiz)
```

## Principais Mudanças

### 1. Código Fonte

- **Antes**: `wats_app/` na raiz
- **Agora**: `src/wats/` seguindo padrão Python

### 2. Configurações

- **Antes**: Arquivos espalhados na raiz
- **Agora**: Centralizados em `config/`
- Busca inteligente: primeiro em `config/`, depois na raiz

### 3. Scripts

- **Antes**: Misturados na raiz
- **Agora**: Organizados em `scripts/`
- Inclui scripts de build, demo e utilitários

### 4. Imports Atualizados

- Todos os imports `wats_app.*` foram convertidos para `src.wats.*`
- Script automatizado criado em `scripts/update_imports.py`

## Benefícios da Reorganização

1. **Clareza**: Cada tipo de arquivo tem seu local específico
2. **Manutenibilidade**: Estrutura mais previsível e padrão
3. **Escalabilidade**: Fácil adição de novos módulos
4. **Profissionalismo**: Segue boas práticas da comunidade Python
5. **Build**: Configuração PyInstaller atualizada para nova estrutura

## Compatibilidade

- ✅ Aplicação funciona corretamente após reorganização
- ✅ Modo demo mantido funcionando
- ✅ Todas as funcionalidades preservadas
- ✅ Configurações carregadas do local correto
- ✅ Build process atualizado

## Scripts Importantes

- `run.py`: Ponto de entrada principal (mantido na raiz)
- `scripts/rebuild_exe.bat`: Rebuild do executável
- `scripts/update_imports.py`: Atualização automática de imports
- `scripts/demo_api_integration.py`: Demo de integração

## Configuração de Desenvolvimento

Para desenvolver após a reorganização:

1. Clone o repositório
2. Install dependencies: `pip install -r requirements.txt`
3. Execute: `python run.py`
4. Para modo demo: `$env:WATS_DEMO_MODE="true"; python run.py`

## Build de Executável

```bash
cd scripts
pyinstaller build_executable.spec
```

A configuração PyInstaller foi atualizada para referenciar a nova estrutura.

# Legado Técnico WATS (Handover de Manutenção)

> Última atualização: 2026-02-20  
> Objetivo: deixar um guia operacional e técnico para continuidade do projeto com baixo risco.

---

## 1) Resumo Executivo

O WATS é uma aplicação desktop (CustomTkinter) para gestão centralizada de conexões RDP com:

- controle de acesso por grupo, individual e temporário;
- proteção colaborativa de sessões com senha;
- auditoria de acesso/heartbeat no banco;
- gravação automática de sessões (com rotação e limpeza);
- suporte principal a SQL Server (com variações por ambiente).

A aplicação é funcionalmente rica, mas concentra muita lógica em `src/wats/app_window.py`, que é o principal ponto de atenção para manutenção evolutiva.

## 1.1 Leitura em 15 minutos (onboarding rápido)

Se você acabou de assumir manutenção, siga esta ordem:

1. Leia este documento até a seção **5) Operação e Manutenção**.
2. Leia `docs/MANUTENCAO_RAPIDA.md` para o runbook diário/semanal.
3. Consulte `docs/CONFIG_REFERENCE.md` antes de alterar `config.json`.

Com isso, você consegue:

- subir o sistema com segurança;
- diagnosticar os incidentes mais comuns;
- evitar mudanças arriscadas em módulos críticos.

---

## 2) Arquitetura e Fluxo Geral

## 2.1 Camadas

- **Entrada/Bootstrap**: `run.py`, `src/wats/main.py`, `src/wats/config.py`
- **UI e Orquestração**: `src/wats/app_window.py`, `src/wats/dialogs.py`, `src/wats/admin_panels/*`
- **Serviços de Negócio**: `src/wats/session_protection.py`, `src/wats/services/access_management_service.py`
- **Dados**: `src/wats/db/database_manager.py`, `src/wats/db/db_service.py`, `src/wats/db/repositories/*`
- **Infra transversal**: `src/wats/util_cache/*`, `src/wats/performance.py`, `src/wats/recording/*`

## 2.2 Fluxo de inicialização

1. `run.py`:
   - configura logging;
   - valida consentimento de gravação (`ConsentDialog`);
   - carrega `.env` e configurações (`Settings`);
   - inicializa otimizações (`initialize_performance_optimizations`);
   - chama `run_app()`.
2. `src/wats/main.py`:
   - instancia `Application(settings_instance)`;
   - entra no loop principal da UI (`mainloop`).
3. `src/wats/app_window.py`:
   - inicializa DBService;
   - configura sessão/proteção/gravação;
   - carrega árvore de conexões;
   - inicia tarefas periódicas (cleanup/heartbeat/refresh).

## 2.3 Fluxo principal de conexão

1. Usuário seleciona conexão na árvore e executa duplo clique.
2. Aplicação valida proteção de sessão (se existir).
3. Conexão RDP é iniciada (`_connect_rdp` + `_execute_connection`).
4. UI atualiza imediatamente e logs assíncronos são persistidos.
5. Heartbeat monitora sessão ativa e encerra/limpa estado quando necessário.
6. Gravação é iniciada somente após detectar processo RDP ativo.

---

## 3) Mapa dos principais arquivos

## 3.1 Raiz do projeto

- `run.py`: bootstrap real de execução, consentimento e carga de config.
- `build.py`: build universal (Windows/Linux/Docker) e rotinas de limpeza.
- `Makefile`: tarefas de instalação, qualidade, testes, build e docs.
- `pyproject.toml`: configuração de Black, isort, mypy, pytest e coverage.
- `requirements*.txt`: dependências por cenário.
- `config.json` / `config/config.json`: runtime principal.

## 3.2 Núcleo da aplicação (`src/wats`)

- `main.py`: entrada da aplicação UI.
- `config.py`: resolução de paths, env vars, logging e classe `Settings`.
- `app_window.py`: janela principal, árvore de conexões, ações de conexão, heartbeats, integrações admin/gravação/proteção.
- `dialogs.py`: diálogos auxiliares da UI.
- `session_protection.py`: telas e manager de proteção colaborativa.
- `performance.py`: bootstrap de pool/cache e funções de invalidação.
- `utils.py`: utilitários (incluindo parsing de particularidades/wiki e hash legado).

## 3.3 Banco de dados (`src/wats/db`)

- `database_manager.py`: conexão por dialeto e execução de queries.
- `connection_pool.py`: pool de conexões para reduzir latência.
- `db_service.py`: fachada de repositórios (`users`, `groups`, `connections`, `logs`).
- `repositories/connection_repository.py`: visibilidade de conexões por permissão.
- `repositories/user_repository.py`: usuários e papel admin.
- `repositories/group_repository.py`: CRUD de grupos.
- `repositories/individual_permission_repository.py`: permissões individuais e temporárias.
- `repositories/log_repository.py`: logs de conexão/heartbeat/auditoria.
- `repositories/session_protection_repository.py`: criação/validação/limpeza de proteção de sessão.

## 3.4 Administração (`src/wats/admin_panels`)

- `admin_hub.py`: hub de entrada do painel admin.
- `user_manager.py`: usuários + permissões individuais.
- `group_manager.py`: CRUD de grupos.
- `connection_manager.py`: CRUD de conexões e particularidades/wiki.
- `temporary_access_manager.py`: concessão e monitoramento de acesso temporário.
- `simple_access_manager.py`: fluxo simplificado para liberar/bloquear acessos.

## 3.5 Infra de conexão/cache (`src/wats/util_cache`)

- `intelligent_cache.py` / `cache.py`: cache em memória com TTL e invalidação por padrão.
- `thread_pool.py`: executores de IO/CPU para não bloquear UI.
- `rdp_connector.py`: estratégia multiplataforma de conexão RDP.
- `freerdp_wrapper.py`: integração com FreeRDP.

## 3.6 Gravação (`src/wats/recording`)

- `multi_session_recording_manager.py`: gerenciamento de múltiplas gravações concorrentes.
- `session_recorder.py`: captura/gravação/segmentação de vídeo.
- `smart_session_recorder.py`: versão “inteligente” com callbacks e estado.
- `window_tracker.py`: rastreio da janela RDP para recorte/captura.
- `interactivity_monitor.py`: atividade/inatividade para eventos de gravação.
- `file_rotation_manager.py`: retenção por idade/tamanho e limpeza automática.
- `recording_manager.py`: fachada de gravação (status, start/stop, cleanup, compressão).

---

## 4) Funções e métodos críticos (para troubleshooting)

## 4.1 Bootstrap e configuração

- `run.py`
  - `main()`: sequenciamento completo de inicialização.
  - `get_config_file_path()`: define origem de `config.json` (script x executável).
  - `update_config_auto_consent(value)`: persiste aceite de consentimento.
- `src/wats/config.py`
  - `load_config_json()`: leitura central de configuração.
  - `setup_logging()`: configuração de logging de runtime.
  - `Settings`: agrega parâmetros operacionais e de banco.
  - `get_app_config()`: subset de configuração de aplicação.

## 4.2 Janela principal e sessão ativa

- `src/wats/app_window.py` (classe `Application`)
  - `_deferred_init()` / `_init_db_and_start()`: inicialização tardia sem travar UI.
  - `_populate_tree()` / `_process_tree_update()`: atualização de conexões exibidas.
  - `_on_item_double_click()`: gatilho primário para conectar.
  - `_connect_rdp()` / `_execute_connection()`: ciclo de conexão e atualização de estado.
  - `heartbeat_task(...)`: persistência de heartbeat e limpeza de sessão desconectada.
  - `_cleanup_orphaned_connections()` / `_cleanup_orphaned_protections()`: higiene operacional.
  - `_open_admin_panel()`: navegação para painel administrativo.

## 4.3 Banco e permissões

- `src/wats/db/repositories/connection_repository.py`
  - `select_all(username)`: regra de visibilidade (admin x permissões).
- `src/wats/db/repositories/individual_permission_repository.py`
  - `grant_individual_access(...)`, `revoke_individual_access(...)`.
  - `grant_temporary_access(...)`, `cleanup_expired_permissions()`.
- `src/wats/db/repositories/log_repository.py`
  - `insert_connection_log(...)`, `update_heartbeat(...)`, `log_access_start/end(...)`.
  - `cleanup_orphaned_access_logs(...)`.
- `src/wats/db/repositories/session_protection_repository.py`
  - `create_session_protection(...)`, `validate_session_password(...)`.
  - `remove_session_protection(...)`, `is_session_protected(...)`, `cleanup_expired_protections()`.

## 4.4 Gravação

- `src/wats/recording/multi_session_recording_manager.py`
  - `start_session_recording(...)`, `stop_session_recording(...)`, `stop_all_recordings()`.
- `src/wats/recording/session_recorder.py`
  - `start_recording(...)`, `stop_recording()`, `_recording_loop(...)`, rotação de arquivo.
- `src/wats/recording/file_rotation_manager.py`
  - `cleanup_recordings()`, `force_cleanup_by_age(...)`, `force_cleanup_by_size(...)`.

---

## 5) Operação e Manutenção (Runbook)

## 5.1 Ambiente local

1. Criar e ativar venv.
2. Instalar dependências:
   - `pip install -r requirements.txt`
   - `pip install -r requirements-dev.txt`
3. Validar conexão de banco e variáveis em `config/config.json` + `.env`.
4. Executar `python run.py`.

## 5.2 Comandos úteis (Makefile)

- `make install-dev`: ambiente completo de desenvolvimento.
- `make format`: black + isort.
- `make lint`: flake8.
- `make type-check`: mypy.
- `make test` / `make test-coverage`: testes.
- `make quality`: pipeline local de qualidade.
- `make build`: build da aplicação.

## 5.3 Rotina recomendada de manutenção

### Diária

- Validar `wats_app.log` por erros críticos/reincidentes.
- Monitorar falhas de conexão e tempo de resposta da árvore de conexões.
- Conferir se heartbeats estão sendo gravados e encerrados corretamente.

### Semanal

- Executar limpeza de permissões temporárias expiradas.
- Executar limpeza de logs/acessos órfãos.
- Verificar espaço em disco dos diretórios de gravação.
- Rodar `make quality` em branch de manutenção.

### Mensal

- Revisar dependências e CVEs.
- Revisar índices/tempo de queries críticas no banco.
- Revisar políticas de retenção das gravações.

---

## 6) Checklist de Handover para o próximo mantenedor

- [ ] Entender o bootstrap completo (`run.py` → `main.py` → `Application`).
- [ ] Testar login admin e todos os painéis (`admin_panels/*`).
- [ ] Testar permissões: grupo, individual, temporária e restauração.
- [ ] Testar proteção de sessão: criar, validar, remover, expirar.
- [ ] Testar conexão RDP real e comportamento de heartbeat/desconexão.
- [ ] Testar gravação: start, stop, rotação e limpeza.
- [ ] Revisar configurações por ambiente em `config/environments/*`.
- [ ] Rodar pipeline de qualidade local (`make quality`).

---

## 7) Riscos técnicos conhecidos (prioridade de legado)

1. **Alta concentração de responsabilidade em `app_window.py`** (dificulta evolução/testes).
2. **Inconsistências entre componentes antigos e novos** (cache/log/config coexistindo em padrões diferentes).
3. **Segurança de senha legada**: presença de MD5 para compatibilidade (`utils.py`), embora haja hashing mais forte em partes específicas.
4. **Acoplamento com SQL Server e regras de banco**: operação depende fortemente de schema/procedures corretos.
5. **Serviços com sinais de desalinhamento** em trechos menos usados (ex.: service layer não totalmente convergente com repositórios).

---

## 8) Plano recomendado de evolução (baixo risco)

### Fase 1 — Estabilização (curto prazo)

- Padronizar logs de erro para facilitar suporte.
- Criar testes de regressão para permissões e heartbeat.
- Revisar e documentar schema/procedures obrigatórias no banco.

### Fase 2 — Refatoração incremental (médio prazo)

- Extrair de `Application` os fluxos de:
  - conexão RDP;
  - heartbeat/log de sessão;
  - sincronização da árvore.
- Reduzir acoplamento UI ↔ DB via serviços menores.

### Fase 3 — Segurança e observabilidade (médio/longo prazo)

- Migrar hash legado para padrão único forte (bcrypt/argon2), com estratégia de transição.
- Criar dashboard simples de saúde (conexões ativas, órfãos, gravações, erros).

---

## 9) Referências rápidas

- Entrada principal: `run.py`
- Configuração: `src/wats/config.py`
- UI principal: `src/wats/app_window.py`
- Banco (fachada): `src/wats/db/db_service.py`
- Regras de acesso: `src/wats/db/repositories/connection_repository.py`
- Proteção de sessão: `src/wats/session_protection.py`
- Gravação: `src/wats/recording/multi_session_recording_manager.py`
- Build: `build.py` e `Makefile`

---

Se este documento for mantido atualizado a cada mudança estrutural, ele reduz bastante o risco de regressão e acelera onboarding de novos mantenedores.

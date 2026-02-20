# Referência Completa do config.json (WATS)

Este documento descreve **cada item** do arquivo `config.json`, para que serve e como impacta o runtime.

---

## Ordem de prioridade das configurações

Para os campos carregados por `Settings`:

1. valor do `config.json`
2. variável de ambiente equivalente
3. valor padrão no código

Exemplo: `database.server` → `DB_SERVER` (env) → `None`.

---

## Estrutura atual

```json
{
  "database": { ... },
  "recording": { ... },
  "application": { ... },
  "rdp": { ... },
  "performance": { ... }
}
```

---

## 1) database

Configura o acesso ao banco de dados.

- `database.type` (string)
  - Função: tipo do banco (`sqlserver` ou `sqlite`).
  - Uso: seleciona dialeto e driver no `DatabaseManager`.
  - Env: `DB_TYPE`.

- `database.server` (string)
  - Função: host/IP do SQL Server.
  - Uso: base da connection string.
  - Env: `DB_SERVER`.

- `database.database` (string)
  - Função: nome do banco (ou caminho para SQLite).
  - Uso: connection string.
  - Env: `DB_DATABASE`.

- `database.username` (string)
  - Função: usuário de conexão.
  - Uso: connection string SQL Server.
  - Env: `DB_UID`.

- `database.password` (string)
  - Função: senha de conexão.
  - Uso: connection string SQL Server.
  - Env: `DB_PWD`.

- `database.port` (string/int)
  - Função: porta do SQL Server.
  - Uso: montada como `SERVER=host,porta`.
  - Env: `DB_PORT`.

---

## 2) recording

Configura gravação de sessões RDP e retenção de arquivos.

### 2.1 Campos principais

- `recording.enabled` (bool)
  - Função: habilita/desabilita gravação.
  - Uso: controla inicialização do manager de gravação.
  - Env: `RECORDING_ENABLED`.

- `recording.auto_start` (bool)
  - Função: inicia gravação automaticamente ao conectar.
  - Uso: fluxo automático de início de gravação.
  - Env: `RECORDING_AUTO_START`.

- `recording.mode` (string)
  - Função: modo de captura (`rdp_window`, `full_screen`, `active_window`).
  - Uso: comportamento de captura no recorder.
  - Env: `RECORDING_MODE`.

- `recording.output_dir` (string)
  - Função: diretório de saída das gravações.
  - Uso: gravação e consulta de arquivos no app.
  - Suporta variáveis: `{USERPROFILE}`, `{APPDATA}`, `{VIDEOS}` etc.
  - Env: `RECORDING_OUTPUT_DIR`.

- `recording.fps` (int)
  - Função: frames por segundo da gravação.
  - Uso: encoder/captura.
  - Env: `RECORDING_FPS`.

- `recording.quality` (int)
  - Função: qualidade da gravação (impacta tamanho/qualidade final).
  - Uso: parâmetros de encoder.
  - Env: `RECORDING_QUALITY`.

- `recording.resolution_scale` (float)
  - Função: escala de resolução da captura.
  - Uso: redimensionamento/captura.
  - Env: `RECORDING_RESOLUTION_SCALE`.

- `recording.max_file_size_mb` (int)
  - Função: limite por arquivo antes de rotação.
  - Uso: política de rotação.
  - Env: `RECORDING_MAX_FILE_SIZE_MB`.

- `recording.max_duration_minutes` (int)
  - Função: duração máxima por segmento.
  - Uso: rotação por tempo.
  - Env: `RECORDING_MAX_DURATION_MINUTES`.

- `recording.max_total_size_gb` (float)
  - Função: limite total de armazenamento.
  - Uso: limpeza de gravações antigas.
  - Env: `RECORDING_MAX_TOTAL_SIZE_GB`.

- `recording.max_file_age_days` (int)
  - Função: idade máxima para retenção de arquivos.
  - Uso: limpeza automática.
  - Env: `RECORDING_MAX_FILE_AGE_DAYS`.

- `recording.cleanup_interval_hours` (int)
  - Função: periodicidade da rotina de limpeza.
  - Uso: scheduler de cleanup.
  - Env: `RECORDING_CLEANUP_INTERVAL_HOURS`.

### 2.2 recording.smart_recording

Refina comportamento inteligente de pausa/rastreio com os campos essenciais de operação.

- `window_tracking_interval` (float): intervalo de rastreamento da janela.
- `inactivity_timeout_minutes` (int): tempo de inatividade antes de pausar.
- `pause_on_minimized` (bool): pausa quando minimizada.
- `pause_on_covered` (bool): pausa quando janela está coberta.
- `create_new_file_after_pause` (bool): cria novo segmento ao retomar.
- `debug_window_tracking` (bool): logs de debug de rastreamento.
- `debug_activity_monitoring` (bool): logs de debug de atividade.

Os campos avançados não essenciais (como `mouse_sensitivity` e logs auxiliares) foram removidos do `config.json` para simplificar operação e manutenção.

### 2.3 recording.compression

Parâmetros de compressão pós-gravação.

- `recording.compression.enabled` (bool)
- `recording.compression.crf` (int)
- `recording.compression.preset` (string)

Observação: parte desses valores é aplicada via pipeline de gravação/smart config; manter coerência com defaults internos.

### 2.4 recording.session_protection

Metadados/intenções para proteção de sessão no contexto de gravação.

- `recording.session_protection.enabled` (bool)
- `recording.session_protection.sanitize_metadata` (bool)
- `recording.session_protection.remove_sensitive_fields` (bool)
- `recording.session_protection.log_protection_actions` (bool)

Observação: proteção de sessão operacional é conduzida principalmente pelos componentes de `session_protection` e repositórios de banco.

---

## 3) application

Configura comportamento geral da aplicação.

- `application.log_level` (string)
  - Função: nível de log (`DEBUG`, `INFO`, `WARNING`, etc.).
  - Uso: setup de logging no bootstrap.

- `application.theme` (string)
  - Função: preferência de tema.
  - Observação: o tema efetivo da janela é persistido também em arquivo de settings local.

- `application.auto_consent` (bool)
  - Função: evita perguntar consentimento em toda execução.
  - Uso: bootstrap em `run.py`.

- `application.window_title` (string)
  - Função: título da janela principal.
  - Uso: aplicado na UI.

- `application.window_geometry` (string)
- `application.window_resizable` (bool)
- `application.minimize_to_tray` (bool)
- `application.start_minimized` (bool)
- `application.check_updates` (bool)
- `application.language` (string)
  - Função: parâmetros de comportamento/UI.
  - Observação: podem existir campos atualmente com uso parcial/planejado.

- `application.monitor` (int)
  - Função: monitor preferencial para comando RDP (`/mon:N`).
  - Uso: aplicado na montagem do comando RDP.

---

## 4) rdp

Configura parâmetros da abertura da sessão RDP.

- `rdp.maximize_window` (bool)
  - Função: inicia sessão maximizada (`/max`) quando não fullscreen.

- `rdp.window_mode` (string)
  - Função: modo declarativo da janela.
  - Observação: pode ser mantido para compatibilidade mesmo com uso parcial.

- `rdp.allow_window_override` (bool)
  - Função: política de “topmost”/sobreposição em componentes de rastreamento de janela.

- `rdp.fullscreen` (bool)
  - Função: inicia em tela cheia (`/f`).

- `rdp.default_width` (int)
- `rdp.default_height` (int)
  - Função: dimensões quando não fullscreen e não maximizado.

---

## 5) performance

Configura limites e tuning de performance.

### 5.1 Governança operacional

- `performance.max_cpu_usage_percent` (int)
  - Função: teto operacional planejado para CPU.

- `performance.memory_limit_mb` (int)
  - Função: limite operacional de memória planejado.

- `performance.disk_space_check_enabled` (bool)
  - Função: habilita política de checagem de disco.

- `performance.min_free_space_gb` (float)
  - Função: espaço mínimo livre desejado.

- `performance.background_cleanup_enabled` (bool)
  - Função: controla limpeza em background.

- `performance.optimize_for_battery` (bool)
  - Função: orientação para perfil conservador.

### 5.2 Tuning efetivo (aplicado no runtime)

- `performance.db_pool_size` (int)
  - Função: tamanho base do pool de conexões de banco.
  - Uso: inicialização do `ConnectionPool`.

- `performance.db_max_overflow` (int)
  - Função: conexões extras permitidas acima do pool base.
  - Uso: `ConnectionPool`.

- `performance.cache_ttl_seconds` (int)
  - Função: TTL padrão do cache inteligente.
  - Uso: criação do cache global.

- `performance.cache_max_size` (int)
  - Função: tamanho máximo do cache em memória.
  - Uso: criação do cache global.

---

## Exemplo recomendado (base)

```json
{
  "database": {
    "type": "sqlserver",
    "server": "MEU-SQL",
    "database": "WATS",
    "username": "wats_user",
    "password": "***",
    "port": "1433"
  },
  "recording": {
    "enabled": true,
    "auto_start": true,
    "mode": "rdp_window",
    "output_dir": "{USERPROFILE}/Videos/Wats",
    "fps": 10,
    "quality": 23,
    "resolution_scale": 1.0,
    "max_file_size_mb": 100,
    "max_duration_minutes": 30,
    "max_total_size_gb": 10.0,
    "max_file_age_days": 30,
    "cleanup_interval_hours": 6
  },
  "application": {
    "log_level": "INFO",
    "auto_consent": true,
    "window_title": "WATS",
    "monitor": 1
  },
  "rdp": {
    "fullscreen": false,
    "maximize_window": true,
    "default_width": 1920,
    "default_height": 1080
  },
  "performance": {
    "db_pool_size": 5,
    "db_max_overflow": 10,
    "cache_ttl_seconds": 300,
    "cache_max_size": 1000
  }
}
```

---

## Boas práticas

- Nunca versionar senha real no `config.json`.
- Preferir variáveis de ambiente para credenciais (`DB_UID`, `DB_PWD`).
- Em produção, manter `log_level` em `INFO` ou `WARNING`.
- Ajustar `db_pool_size` e `cache_max_size` conforme volume real.
- Se houver degradação de memória/disco, reduzir `fps`, aumentar limpeza e revisar retenção.

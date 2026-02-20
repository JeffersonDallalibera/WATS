# Manutenção Rápida WATS

Guia operacional para manter o WATS estável com o menor risco possível.

## 1) Checklist diário (5-10 min)

1. Abrir o app e validar login/conexão básica.
2. Verificar erros críticos em `wats_app.log` (`ERROR`, `CRITICAL`).
3. Confirmar que conexões ativas aparecem/saem corretamente.
4. Confirmar que gravação inicia/encerra em uma conexão de teste.

## 2) Checklist semanal (20-40 min)

1. Limpar permissões temporárias expiradas.
2. Revisar crescimento de pasta de gravações.
3. Validar consistência entre `config.json` e `config/config.json`.
4. Rodar validação rápida de JSON:

```powershell
python -c "import json, pathlib; [json.loads(pathlib.Path(p).read_text(encoding='utf-8')) for p in ['config.json','config/config.json']]; print('JSON OK')"
```

## 3) Fluxo de troubleshooting

## 3.1 Usuário não vê conexão esperada

- Verificar se é admin.
- Verificar permissões por grupo/individual/temporária.
- Validar expiração de acesso temporário.
- Recarregar árvore na UI e revisar cache/permissões.

## 3.2 Conexão RDP cai ou “fantasma” permanece

- Confirmar heartbeat sendo atualizado no banco.
- Rodar limpeza de conexões órfãs.
- Verificar logs de `_execute_connection` e heartbeat.

## 3.3 Gravação não inicia

- Validar `recording.enabled` e `recording.auto_start`.
- Confirmar caminho de saída gravável (`recording.output_dir`).
- Verificar se processo RDP foi realmente detectado.
- Revisar logs de `recording` e `window_tracker`.

## 3.4 Lentidão geral

- Revisar pool/cache em `performance`:
  - `db_pool_size`
  - `db_max_overflow`
  - `cache_ttl_seconds`
  - `cache_max_size`
- Verificar saúde do SQL Server (latência e locks).

## 4) Mudanças seguras em configuração

1. Alterar primeiro em `config/config.json` (dev) e depois no `config.json` da execução real.
2. Alterar um bloco por vez (ex.: `database`, depois `recording`).
3. Validar JSON.
4. Reiniciar app e observar logs por 2-5 minutos.

## 5) Arquivos-chave para manutenção

- Bootstrap: `run.py`
- Configuração: `src/wats/config.py`
- UI principal: `src/wats/app_window.py`
- Banco/fachada: `src/wats/db/db_service.py`
- Permissões: `src/wats/db/repositories/individual_permission_repository.py`
- Gravação: `src/wats/recording/multi_session_recording_manager.py`

## 6) Regra de ouro

Se a mudança for funcional, sempre validar em 3 cenários:

1. Usuário admin.
2. Usuário comum com acesso por grupo.
3. Usuário com permissão individual/temporária.

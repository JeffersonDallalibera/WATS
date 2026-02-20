# Documentação WATS

Este diretório reúne a documentação atual e ativa do WATS.

## Leitura recomendada (ordem)

1. [LEGADO_TECNICO_WATS.md](LEGADO_TECNICO_WATS.md) — Visão geral de arquitetura, operação e pontos críticos.
2. [MANUTENCAO_RAPIDA.md](MANUTENCAO_RAPIDA.md) — Runbook prático para manutenção diária/semanal e troubleshooting.
3. [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) — Referência completa de `config.json`.

## Objetivo de cada documento

- [LEGADO_TECNICO_WATS.md](LEGADO_TECNICO_WATS.md)
  - Para entender a arquitetura e onde mexer com segurança.
  - Útil para onboarding técnico e evolução do sistema.

- [MANUTENCAO_RAPIDA.md](MANUTENCAO_RAPIDA.md)
  - Para operação do dia a dia: checklist, diagnóstico rápido e ações de correção.
  - Útil para sustentação e suporte.

- [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md)
  - Para saber exatamente o que cada chave do `config.json` faz.
  - Útil para mudança de ambiente e tuning.

---

## Início rápido para manutenção

1. Validar configuração em `config.json` e `config/config.json`.
2. Executar `python run.py` e verificar `wats_app.log`.
3. Em caso de incidente, seguir [MANUTENCAO_RAPIDA.md](MANUTENCAO_RAPIDA.md).
4. Para alteração de comportamento, consultar [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md).

---

## Estado da documentação

- Este índice reflete somente documentos existentes no repositório.
- Se criar novo documento técnico, adicione aqui com objetivo e público-alvo.

> Sugestões e correções são bem-vindas via issues no repositório.

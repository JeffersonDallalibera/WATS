# WATS

Sistema desktop para gerenciamento centralizado de conexões RDP com controle de acesso, proteção de sessão e gravação.

## Resumo

O WATS foi construído para operação corporativa, com foco em:

- gestão de conexões por grupo e por usuário;
- permissões temporárias;
- proteção de sessão com validação centralizada;
- gravação de sessões com rotação e retenção;
- configuração por `config.json` e variáveis de ambiente.

## Documentação

Use este índice como fonte oficial de docs:

- [docs/README.md](docs/README.md)

Leitura recomendada:

1. [docs/LEGADO_TECNICO_WATS.md](docs/LEGADO_TECNICO_WATS.md)
2. [docs/MANUTENCAO_RAPIDA.md](docs/MANUTENCAO_RAPIDA.md)
3. [docs/CONFIG_REFERENCE.md](docs/CONFIG_REFERENCE.md)

## Requisitos

- Python 3.11+
- Windows (principal) ou Linux
- Banco SQL Server (padrão) ou SQLite (cenários específicos)

## Instalação rápida (Windows)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

## Instalação rápida (Linux)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-linux.txt
python run.py
```

## Configuração

O runtime lê configuração nesta ordem:

1. `config/config.json` (desenvolvimento)
2. `config.json` (fallback / distribuição)

Para variáveis de ambiente:

1. `config/.env`
2. `.env`

Exemplos de variáveis:

```env
DB_TYPE=sqlserver
DB_SERVER=localhost
DB_DATABASE=WATS
DB_UID=usuario
DB_PWD=senha
DB_PORT=1433
LOG_LEVEL=INFO
```

## Comandos úteis

```powershell
# validar JSON de configuração
python -c "import json, pathlib; [json.loads(pathlib.Path(p).read_text(encoding='utf-8')) for p in ['config.json','config/config.json']]; print('JSON OK')"

# auditoria simples de módulos potencialmente não usados
python scripts/_unused_audit.py
```

## Estrutura atual (resumo)

```text
WATS/
├── run.py
├── build.py
├── WATS.spec
├── config/
├── docs/
├── scripts/
│   ├── setup_project.py
│   └── _unused_audit.py
└── src/wats/
    ├── app_window.py
    ├── config.py
    ├── main.py
    ├── performance.py
    ├── session_protection.py
    ├── admin_panels/
    ├── db/
    ├── recording/
    ├── services/
    ├── util_cache/
    └── utils/
```

## Build

Build principal via PyInstaller usando:

- `WATS.spec`
- `build.py`

## Estado atual do projeto

- documentação consolidada em `docs/`;
- scripts antigos e docs legados foram removidos;
- `tests/` está vazio no estado atual do repositório.

## Licença

Este projeto usa a licença MIT. Veja [LICENSE](LICENSE).

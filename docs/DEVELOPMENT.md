# Desenvolvimento WATS - Configuração

## Configuração do Ambiente de Desenvolvimento

### Pre-requisitos

- Python 3.8+
- Git
- Windows 10/11 (para funcionalidades específicas do SO)

### Setup Inicial

```bash
# 1. Clone o repositório
git clone https://github.com/JeffersonDallalibera/WATS.git
cd WATS

# 2. Crie ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instale dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Ferramentas de desenvolvimento

# 4. Configure arquivo de ambiente
copy config\.env.example config\.env
# Edite config\.env com suas configurações

# 5. Execute em modo desenvolvimento
python run.py

# 6. Execute em modo demo
$env:WATS_DEMO_MODE="true"; python run.py
```

### Comandos de Desenvolvimento

```bash
# Formatação de código
black src/ tests/ scripts/
isort src/ tests/ scripts/

# Linting
flake8 src/ tests/ scripts/
mypy src/

# Testes
pytest tests/ -v --cov=src/wats --cov-report=html

# Build
cd scripts
pyinstaller build_executable.spec
```

### Estrutura de Branches

- `master`: Código estável e em produção
- `develop`: Integração de features
- `feature/*`: Novas funcionalidades
- `bugfix/*`: Correções de bugs
- `release/*`: Preparação de releases

### Commit Convention

Utilize Conventional Commits:

```
feat: adiciona nova funcionalidade de filtro persistente
fix: corrige problema de conexão com banco de dados
docs: atualiza documentação de configuração
style: formata código com black
refactor: reorganiza estrutura de pastas
test: adiciona testes para módulo de gravação
chore: atualiza dependências
```

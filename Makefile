# Makefile para automação de tarefas do projeto WATS
# Para Windows, use: make <target> ou mingw32-make <target>

# Variáveis
PYTHON := python
PIP := pip
PROJECT_NAME := wats
SRC_DIR := src
TESTS_DIR := tests
SCRIPTS_DIR := scripts

# Cores para output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help install install-dev clean format lint type-check test test-coverage build run run-demo docs

# Help
help: ## Mostra esta mensagem de ajuda
	@echo "$(GREEN)Comandos disponíveis:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Instalação
install: ## Instala dependências de produção
	@echo "$(GREEN)Instalando dependências de produção...$(NC)"
	$(PIP) install -r requirements.txt

install-dev: ## Instala dependências de desenvolvimento
	@echo "$(GREEN)Instalando dependências de desenvolvimento...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	pre-commit install

# Limpeza
clean: ## Remove arquivos temporários e cache
	@echo "$(GREEN)Limpando arquivos temporários...$(NC)"
	@if exist "$(SRC_DIR)\**\__pycache__" rmdir /s /q "$(SRC_DIR)\**\__pycache__" 2>nul || true
	@if exist "$(TESTS_DIR)\**\__pycache__" rmdir /s /q "$(TESTS_DIR)\**\__pycache__" 2>nul || true
	@if exist ".pytest_cache" rmdir /s /q ".pytest_cache" 2>nul || true
	@if exist ".mypy_cache" rmdir /s /q ".mypy_cache" 2>nul || true
	@if exist "htmlcov" rmdir /s /q "htmlcov" 2>nul || true
	@if exist "*.egg-info" rmdir /s /q "*.egg-info" 2>nul || true
	@if exist "dist" rmdir /s /q "dist" 2>nul || true
	@if exist "build" rmdir /s /q "build" 2>nul || true

# Formatação de código
format: ## Formata código com black e isort
	@echo "$(GREEN)Formatando código...$(NC)"
	black $(SRC_DIR) $(TESTS_DIR) $(SCRIPTS_DIR)
	isort $(SRC_DIR) $(TESTS_DIR) $(SCRIPTS_DIR)

# Linting
lint: ## Executa linting com flake8
	@echo "$(GREEN)Executando linting...$(NC)"
	flake8 $(SRC_DIR) $(TESTS_DIR) $(SCRIPTS_DIR)

# Type checking
type-check: ## Executa verificação de tipos com mypy
	@echo "$(GREEN)Verificando tipos...$(NC)"
	mypy $(SRC_DIR)

# Verificação de segurança
security: ## Executa verificação de segurança com bandit
	@echo "$(GREEN)Verificando segurança...$(NC)"
	bandit -r $(SRC_DIR) -x tests/

# Testes
test: ## Executa testes unitários
	@echo "$(GREEN)Executando testes...$(NC)"
	pytest $(TESTS_DIR) -v

test-coverage: ## Executa testes com cobertura
	@echo "$(GREEN)Executando testes com cobertura...$(NC)"
	pytest $(TESTS_DIR) -v --cov=$(SRC_DIR)/$(PROJECT_NAME) --cov-report=html --cov-report=term-missing

test-fast: ## Executa testes rápidos (exclui testes lentos)
	@echo "$(GREEN)Executando testes rápidos...$(NC)"
	pytest $(TESTS_DIR) -v -m "not slow"

# Qualidade de código (tudo junto)
quality: format lint type-check security test ## Executa todas as verificações de qualidade

# Build
build: ## Constrói o executável (detecta plataforma automaticamente)
	@echo "$(GREEN)Construindo executável...$(NC)"
	$(PYTHON) build.py

build-windows: ## Constrói executável para Windows
	@echo "$(GREEN)Construindo executável para Windows...$(NC)"
	$(PYTHON) build.py --platform windows

build-linux: ## Constrói executável para Linux
	@echo "$(GREEN)Construindo executável para Linux...$(NC)"
	$(PYTHON) build.py --platform linux

build-docker: ## Constrói usando Docker (multiplataforma)
	@echo "$(GREEN)Construindo com Docker...$(NC)"
	$(PYTHON) build.py --platform docker

build-all: ## Constrói para todas as plataformas (requer Docker)
	@echo "$(GREEN)Construindo para todas as plataformas...$(NC)"
	$(PYTHON) build.py --platform windows || true
	$(PYTHON) build.py --platform linux || true
	$(PYTHON) build.py --platform docker || true

package-deb: build-linux ## Cria pacote .deb para Linux
	@echo "$(GREEN)Criando pacote .deb...$(NC)"
	@if [ -f "wats_1.0.0_amd64.deb" ]; then \
		echo "✅ Pacote .deb criado: wats_1.0.0_amd64.deb"; \
	else \
		echo "❌ Falha ao criar pacote .deb"; \
	fi

# Execução
run: ## Executa a aplicação
	@echo "$(GREEN)Executando WATS...$(NC)"
	$(PYTHON) run.py

run-demo: ## Executa a aplicação em modo demo
	@echo "$(GREEN)Executando WATS em modo demo...$(NC)"
	set WATS_DEMO_MODE=true && $(PYTHON) run.py

# Documentação
docs: ## Gera documentação
	@echo "$(GREEN)Gerando documentação...$(NC)"
	@if not exist "docs\_build" mkdir "docs\_build"
	sphinx-build -b html docs docs/_build

docs-serve: ## Serve documentação localmente
	@echo "$(GREEN)Servindo documentação em http://localhost:8000$(NC)"
	cd docs/_build && $(PYTHON) -m http.server 8000

# Desenvolvimento
dev-setup: install-dev ## Configura ambiente de desenvolvimento completo
	@echo "$(GREEN)Configurando ambiente de desenvolvimento...$(NC)"
	@if not exist "config\.env" copy "config\.env.example" "config\.env"
	pre-commit install

# Git hooks
pre-commit: format lint type-check ## Executa verificações antes do commit
	@echo "$(GREEN)Executando verificações de pre-commit...$(NC)"

# Relatórios
report: ## Gera relatório completo de qualidade
	@echo "$(GREEN)Gerando relatório de qualidade...$(NC)"
	@echo "=== FORMATAÇÃO ===" > quality_report.txt
	black --check $(SRC_DIR) $(TESTS_DIR) $(SCRIPTS_DIR) >> quality_report.txt 2>&1 || true
	@echo "" >> quality_report.txt
	@echo "=== LINTING ===" >> quality_report.txt
	flake8 $(SRC_DIR) $(TESTS_DIR) $(SCRIPTS_DIR) >> quality_report.txt 2>&1 || true
	@echo "" >> quality_report.txt
	@echo "=== TYPE CHECKING ===" >> quality_report.txt
	mypy $(SRC_DIR) >> quality_report.txt 2>&1 || true
	@echo "" >> quality_report.txt
	@echo "=== SECURITY ===" >> quality_report.txt
	bandit -r $(SRC_DIR) >> quality_report.txt 2>&1 || true
	@echo "$(GREEN)Relatório salvo em quality_report.txt$(NC)"

# Benchmark
benchmark: ## Executa testes de performance
	@echo "$(GREEN)Executando benchmarks...$(NC)"
	pytest $(TESTS_DIR) -v -m "benchmark"

# Deploy preparation
prepare-release: quality build ## Prepara uma release (qualidade + build)
	@echo "$(GREEN)Release preparada com sucesso!$(NC)"

# Utilitários
check-deps: ## Verifica dependências desatualizadas
	@echo "$(GREEN)Verificando dependências...$(NC)"
	$(PIP) list --outdated

update-deps: ## Atualiza dependências (cuidado!)
	@echo "$(YELLOW)Atualizando dependências... (use com cuidado!)$(NC)"
	$(PIP) list --outdated --format=freeze | findstr /v "^-e" | for /f "tokens=1 delims==" %i in ('more') do $(PIP) install --upgrade %i

# Informações
info: ## Mostra informações do ambiente
	@echo "$(GREEN)Informações do ambiente:$(NC)"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Pip: $$($(PIP) --version)"
	@echo "Diretório atual: $$(cd)"
	@echo "Diretório do projeto: $(shell pwd)"
	@echo "Arquivos Python encontrados: $$(find $(SRC_DIR) -name "*.py" | wc -l) no src/"
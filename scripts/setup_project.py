#!/usr/bin/env python3
"""Script para aplicar ferramentas de qualidade e configurar o projeto WATS."""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """
    Executa um comando e retorna se foi bem-sucedido.
    
    Args:
        command: Comando a ser executado
        description: Descrição da operação
        
    Returns:
        True se comando foi bem-sucedido
    """
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Sucesso")
            return True
        else:
            print(f"❌ {description} - Erro:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} - Exceção: {e}")
        return False


def install_dependencies():
    """Instala dependências de desenvolvimento."""
    print("📦 Instalando dependências...")
    
    commands = [
        ("pip install -r requirements.txt", "Dependências de produção"),
        ("pip install -r requirements-dev.txt", "Dependências de desenvolvimento"),
    ]
    
    for command, desc in commands:
        if not run_command(command, desc):
            return False
    
    return True


def setup_pre_commit():
    """Configura pre-commit hooks."""
    print("🔒 Configurando pre-commit hooks...")
    
    commands = [
        ("pre-commit install", "Instalação de hooks"),
        ("pre-commit autoupdate", "Atualização de hooks"),
    ]
    
    for command, desc in commands:
        run_command(command, desc)


def format_code():
    """Formata código com black e isort."""
    print("🎨 Formatando código...")
    
    commands = [
        ("black src/ tests/ scripts/", "Formatação com Black"),
        ("isort src/ tests/ scripts/", "Organização de imports"),
    ]
    
    for command, desc in commands:
        run_command(command, desc)


def run_linting():
    """Executa linting."""
    print("🔍 Executando linting...")
    
    commands = [
        ("flake8 src/ tests/ scripts/", "Linting com Flake8"),
        ("mypy src/", "Verificação de tipos"),
        ("bandit -r src/ -x tests/", "Análise de segurança"),
    ]
    
    results = []
    for command, desc in commands:
        results.append(run_command(command, desc))
    
    return all(results)


def run_tests():
    """Executa testes."""
    print("🧪 Executando testes...")
    
    commands = [
        ("pytest tests/ -v --cov=src/wats --cov-report=term-missing", "Testes com cobertura"),
    ]
    
    for command, desc in commands:
        run_command(command, desc)


def create_env_file():
    """Cria arquivo .env se não existir."""
    env_path = Path("config/.env")
    env_example_path = Path("config/.env.example")
    
    if not env_path.exists() and env_example_path.exists():
        print("📄 Criando arquivo .env...")
        try:
            import shutil
            shutil.copy(env_example_path, env_path)
            print("✅ Arquivo .env criado a partir do .env.example")
        except Exception as e:
            print(f"❌ Erro ao criar .env: {e}")


def main():
    """Função principal."""
    print("🚀 Configurando projeto WATS com boas práticas")
    print("=" * 50)
    
    # Verificar se estamos no diretório correto
    if not Path("src/wats").exists():
        print("❌ Execute este script no diretório raiz do projeto WATS")
        sys.exit(1)
    
    # Lista de etapas
    steps = [
        ("📦 Instalação de dependências", install_dependencies),
        ("📄 Criação do arquivo .env", create_env_file),
        ("🎨 Formatação de código", format_code),
        ("🔒 Configuração de pre-commit", setup_pre_commit),
        ("🔍 Linting e verificações", run_linting),
        ("🧪 Execução de testes", run_tests),
    ]
    
    success_count = 0
    total_steps = len(steps)
    
    for step_name, step_func in steps:
        print(f"\n{step_name}")
        print("-" * 30)
        
        try:
            if step_func():
                success_count += 1
        except Exception as e:
            print(f"❌ Erro em {step_name}: {e}")
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DA CONFIGURAÇÃO")
    print("=" * 50)
    print(f"✅ Etapas concluídas: {success_count}/{total_steps}")
    
    if success_count == total_steps:
        print("🎉 Configuração completa! Projeto pronto para desenvolvimento.")
    else:
        print("⚠️  Algumas etapas falharam. Verifique os erros acima.")
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("- Configure as variáveis no arquivo config/.env")
    print("- Execute 'make run-demo' para testar a aplicação")
    print("- Use 'make quality' antes de fazer commits")
    print("- Consulte docs/DEVELOPMENT.md para mais informações")


if __name__ == "__main__":
    main()
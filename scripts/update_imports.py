#!/usr/bin/env python3
"""
Script para atualizar imports após reorganização da estrutura do projeto.
Converte imports de 'wats_app' para 'src.wats' em todos os arquivos Python.
"""

import re
import glob


def update_imports_in_file(filepath):
    """Atualiza imports em um arquivo específico."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Padrões para atualizar
        patterns = [
            (r'from wats_app\.', 'from src.wats.'),
            (r'import src.wats\.', 'import src.wats.'),
            (r'from src.wats import', 'from src.wats import'),
            (r'import src.wats', 'import src.wats'),
        ]

        original_content = content
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        # Se houve mudanças, salva o arquivo
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Atualizado: {filepath}")
            return True
        else:
            print(f"- Sem mudanças: {filepath}")
            return False

    except Exception as e:
        print(f"✗ Erro ao processar {filepath}: {e}")
        return False


def main():
    """Função principal."""
    print("Atualizando imports após reorganização...")

    # Encontra todos os arquivos Python
    python_files = []

    # Arquivos na raiz
    python_files.extend(glob.glob("*.py"))

    # Arquivos em src/
    python_files.extend(glob.glob("src/**/*.py", recursive=True))

    # Arquivos em tests/
    python_files.extend(glob.glob("tests/**/*.py", recursive=True))

    # Arquivos em scripts/
    python_files.extend(glob.glob("scripts/**/*.py", recursive=True))

    updated_count = 0
    total_count = len(python_files)

    print(f"Encontrados {total_count} arquivos Python para processar...")

    for filepath in python_files:
        if update_imports_in_file(filepath):
            updated_count += 1

    print("\nResumo:")
    print(f"- Arquivos processados: {total_count}")
    print(f"- Arquivos atualizados: {updated_count}")
    print(f"- Arquivos sem mudanças: {total_count - updated_count}")


if __name__ == "__main__":
    main()

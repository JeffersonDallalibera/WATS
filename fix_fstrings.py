#!/usr/bin/env python3
"""
Script para corrigir f-strings sem placeholders (F541).
Converte f-strings que não usam variáveis para strings normais.
"""

import re
from pathlib import Path


def fix_fstring_in_line(line: str) -> str:
    """
    Corrige f-strings sem placeholders em uma linha.

    Detecta padrões de f-strings e remove o prefixo f quando não há placeholders.
    """
    # Padrão para f-strings sem {} ou com {} vazios
    patterns = [
        (r'"([^"]*?)"', r'"\1"'),  # "texto" -> "texto"
        (r"'([^']*?)'", r"'\1'"),  # 'texto' -> 'texto'
        (r'"""(.*?)"""', r'"""\1"""'),  # """texto""" -> """texto"""
        (r"'''(.*?)'''", r"'''\1'''"),  # '''texto''' -> '''texto'''
    ]

    modified = line
    for pattern, replacement in patterns:
        # Verifica se a string não contém { ou }
        matches = re.finditer(pattern, modified)
        for match in matches:
            content = match.group(1)
            # Só remove o 'f' se não houver {} na string
            if '{' not in content and '}' not in content:
                modified = modified.replace(match.group(0), match.expand(replacement))

    return modified


def fix_file(file_path: Path) -> tuple[int, int]:
    """
    Corrige f-strings em um arquivo.

    Returns:
        (linhas_modificadas, linhas_totais)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ Erro ao ler {file_path}: {e}")
        return 0, 0

    modified_lines = 0
    new_lines = []

    for line in lines:
        new_line = fix_fstring_in_line(line)
        if new_line != line:
            modified_lines += 1
        new_lines.append(new_line)

    if modified_lines > 0:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"✓ {file_path.relative_to(Path.cwd())}: {modified_lines} linhas corrigidas")
        except Exception as e:
            print(f"❌ Erro ao escrever {file_path}: {e}")
            return 0, len(lines)

    return modified_lines, len(lines)


def main():
    """Processa todos os arquivos Python no projeto."""

    project_root = Path(__file__).parent
    exclude_dirs = {'venv', 'build', 'dist', '.git', '__pycache__', '.pytest_cache', 'node_modules'}

    total_files = 0
    total_modified = 0
    total_lines_fixed = 0

    print("🔧 Corrigindo f-strings sem placeholders...\n")

    for py_file in project_root.rglob('*.py'):
        # Ignora diretórios excluídos
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue

        total_files += 1
        lines_fixed, total_lines = fix_file(py_file)

        if lines_fixed > 0:
            total_modified += 1
            total_lines_fixed += lines_fixed

    print(f"\n{'='*60}")
    print("✅ Processamento concluído!")
    print(f"📁 Arquivos processados: {total_files}")
    print(f"📝 Arquivos modificados: {total_modified}")
    print(f"🔧 Linhas corrigidas: {total_lines_fixed}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()

# WATS_Project/scripts/dependency_scanner.py

"""
Script para detectar todas as dependências do projeto WATS e gerar requirements.txt completo.
Analisa todos os arquivos Python e extrai imports automaticamente.
"""

import ast
import os
import sys
import importlib.util
from pathlib import Path
from typing import Set, Dict, List
import subprocess
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DependencyScanner:
    """Scanner para detectar todas as dependências do projeto."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.internal_modules = set()
        self.external_imports = set()
        self.builtin_modules = set()
        self.stdlib_modules = set()
        
        # Módulos da biblioteca padrão do Python (principais)
        self.python_stdlib = {
            'os', 'sys', 'json', 'logging', 'datetime', 'time', 'threading', 'socket',
            'subprocess', 'webbrowser', 'hashlib', 'secrets', 'string', 'typing',
            'unittest', 'ast', 'pathlib', 'importlib', 're', 'collections', 'itertools',
            'functools', 'operator', 'math', 'random', 'sqlite3', 'urllib', 'http',
            'email', 'xml', 'csv', 'configparser', 'io', 'tempfile', 'shutil', 'glob'
        }
        
        # Módulos que sabemos que são externos (não estão na stdlib)
        self.known_external = {
            'customtkinter', 'pyodbc', 'psycopg2', 'cv2', 'numpy', 'mss', 'psutil',
            'win32gui', 'win32process', 'win32api', 'requests', 'pydantic', 'dotenv',
            'tkinter'  # tkinter é stdlib mas pode ter issues no PyInstaller
        }

    def scan_file(self, file_path: Path) -> Set[str]:
        """Escaneia um arquivo Python e extrai todas as importações."""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse do AST
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
                        
        except Exception as e:
            logging.warning(f"Erro ao escanear {file_path}: {e}")
            
        return imports

    def scan_project(self) -> Dict[str, Set[str]]:
        """Escaneia todo o projeto e categoriza as dependências."""
        logging.info(f"Escaneando projeto em: {self.project_root}")
        
        # Busca todos os arquivos Python
        python_files = []
        for pattern in ['**/*.py']:
            python_files.extend(self.project_root.glob(pattern))
        
        # Remove arquivos de teste e temporários
        python_files = [f for f in python_files if not any(
            exclude in str(f) for exclude in ['__pycache__', '.pyc', 'test_', 'tests/']
        )]
        
        logging.info(f"Encontrados {len(python_files)} arquivos Python")
        
        all_imports = set()
        
        # Escaneia cada arquivo
        for file_path in python_files:
            file_imports = self.scan_file(file_path)
            all_imports.update(file_imports)
            logging.debug(f"{file_path.name}: {file_imports}")
        
        # Categoriza as importações
        for imp in all_imports:
            if imp.startswith('src.wats') or imp.startswith('wats_app') or imp == 'docs':
                self.internal_modules.add(imp)
            elif imp in self.python_stdlib:
                self.stdlib_modules.add(imp)
            elif imp in self.known_external:
                self.external_imports.add(imp)
            else:
                # Tenta determinar se é externo ou interno
                if self._is_external_package(imp):
                    self.external_imports.add(imp)
                else:
                    self.stdlib_modules.add(imp)
        
        return {
            'internal': self.internal_modules,
            'external': self.external_imports,
            'stdlib': self.stdlib_modules
        }

    def _is_external_package(self, module_name: str) -> bool:
        """Verifica se um módulo é um pacote externo."""
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                return True  # Não encontrado, assume externo
            
            # Se está no site-packages, é externo
            if 'site-packages' in str(spec.origin):
                return True
                
            return False
        except Exception:
            return True  # Em caso de erro, assume externo

    def get_installed_packages(self) -> Dict[str, str]:
        """Obtém lista de pacotes instalados com versões."""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                                  capture_output=True, text=True)
            
            packages = {}
            for line in result.stdout.split('\n')[2:]:  # Skip header lines
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        packages[parts[0].lower()] = parts[1]
            
            return packages
        except Exception as e:
            logging.error(f"Erro ao obter pacotes instalados: {e}")
            return {}

    def generate_requirements(self) -> List[str]:
        """Gera lista de requirements baseada nas dependências encontradas."""
        installed_packages = self.get_installed_packages()
        requirements = []
        
        # Mapeia nomes de import para nomes de pacote
        package_mapping = {
            'cv2': 'opencv-python',
            'dotenv': 'python-dotenv',
            'win32gui': 'pywin32',
            'win32process': 'pywin32',
            'win32api': 'pywin32',
            'psycopg2': 'psycopg2-binary'
        }
        
        for imp in sorted(self.external_imports):
            package_name = package_mapping.get(imp, imp)
            
            if package_name.lower() in installed_packages:
                version = installed_packages[package_name.lower()]
                requirements.append(f"{package_name}=={version}")
            else:
                # Pacote não encontrado, adiciona sem versão
                requirements.append(package_name)
                logging.warning(f"Pacote {package_name} não encontrado nos instalados")
        
        return requirements

    def generate_pyinstaller_hiddenimports(self) -> List[str]:
        """Gera lista de hiddenimports para PyInstaller."""
        hidden_imports = []
        
        # Adiciona imports externos essenciais
        for imp in sorted(self.external_imports):
            hidden_imports.append(f"'{imp}'")
        
        # Adiciona módulos internos importantes
        internal_essential = [
            'src.wats',
            'src.wats.main',
            'src.wats.app_window',
            'src.wats.config',
            'src.wats.db',
            'src.wats.db.db_service',
            'src.wats.db.repositories',
            'src.wats.admin_panels',
            'docs.session_protection'
        ]
        
        for imp in internal_essential:
            hidden_imports.append(f"'{imp}'")
            
        return hidden_imports

    def save_results(self, output_dir: Path):
        """Salva os resultados da análise."""
        output_dir.mkdir(exist_ok=True)
        
        # Salva requirements.txt
        requirements = self.generate_requirements()
        with open(output_dir / 'requirements_complete.txt', 'w', encoding='utf-8') as f:
            f.write("# Dependências completas detectadas automaticamente\n")
            f.write("# Gerado pelo dependency_scanner.py\n\n")
            for req in requirements:
                f.write(f"{req}\n")
        
        # Salva hiddenimports para PyInstaller
        hidden_imports = self.generate_pyinstaller_hiddenimports()
        with open(output_dir / 'hiddenimports.txt', 'w', encoding='utf-8') as f:
            f.write("# HiddenImports para PyInstaller\n")
            f.write("# Adicione estas linhas ao seu arquivo .spec\n\n")
            f.write("hiddenimports=[\n")
            for imp in hidden_imports:
                f.write(f"    {imp},\n")
            f.write("]\n")
        
        # Salva relatório completo
        with open(output_dir / 'dependency_report.txt', 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO DE DEPENDÊNCIAS - WATS\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"MÓDULOS EXTERNOS DETECTADOS ({len(self.external_imports)}):\n")
            for imp in sorted(self.external_imports):
                f.write(f"  - {imp}\n")
            
            f.write(f"\nMÓDULOS INTERNOS ({len(self.internal_modules)}):\n")
            for imp in sorted(self.internal_modules):
                f.write(f"  - {imp}\n")
            
            f.write(f"\nMÓDULOS DA STDLIB ({len(self.stdlib_modules)}):\n")
            for imp in sorted(self.stdlib_modules):
                f.write(f"  - {imp}\n")


def main():
    """Função principal do scanner."""
    project_root = Path(__file__).parent.parent  # Vai para WATS_Project
    
    print("🔍 WATS Dependency Scanner")
    print("=" * 50)
    
    scanner = DependencyScanner(str(project_root))
    results = scanner.scan_project()
    
    print(f"\n📊 RESULTADO DA ANÁLISE:")
    print(f"  • Módulos externos: {len(results['external'])}")
    print(f"  • Módulos internos: {len(results['internal'])}")
    print(f"  • Módulos stdlib: {len(results['stdlib'])}")
    
    print(f"\n📦 DEPENDÊNCIAS EXTERNAS DETECTADAS:")
    for imp in sorted(results['external']):
        print(f"  ✓ {imp}")
    
    # Salva resultados
    output_dir = project_root / 'scripts' / 'dependency_analysis'
    scanner.save_results(output_dir)
    
    print(f"\n💾 Arquivos salvos em: {output_dir}")
    print("  • requirements_complete.txt - Requirements completo")
    print("  • hiddenimports.txt - Para PyInstaller")
    print("  • dependency_report.txt - Relatório completo")
    
    print("\n✅ Análise concluída!")


if __name__ == "__main__":
    main()
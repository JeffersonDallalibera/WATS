#!/usr/bin/env python3
"""
Teste da função de expansão de variáveis de sistema no WATS
"""

import sys
import os

# Adiciona o src ao path para importar as funções
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.wats.config import expand_system_variables

def test_variable_expansion():
    """Testa a expansão de variáveis de sistema."""
    print("🧪 Testando expansão de variáveis de sistema no WATS\n")
    
    test_cases = [
        "{USERPROFILE}/Videos/Wats",
        "{VIDEOS}/WATS_Recordings",
        "{DOCUMENTS}/Gravacoes",
        "{DESKTOP}/WATS_Output",
        "{APPDATA}/WATS",
        "{TEMP}/wats_temp",
        "C:/Users/fixo/path",  # Caminho fixo (não deve mudar)
        "{USERPROFILE}/Videos/{USERPROFILE}/nested",  # Múltiplas variáveis
    ]
    
    print("📁 Resultados da expansão:")
    for test_path in test_cases:
        expanded = expand_system_variables(test_path)
        print(f"  🔹 {test_path:<35} → {expanded}")
    
    print(f"\n📋 Informações do sistema:")
    print(f"  👤 USERPROFILE: {os.path.expanduser('~')}")
    print(f"  📁 VIDEOS: {os.path.join(os.path.expanduser('~'), 'Videos')}")
    print(f"  📄 DOCUMENTS: {os.path.join(os.path.expanduser('~'), 'Documents')}")
    print(f"  🖥️ DESKTOP: {os.path.join(os.path.expanduser('~'), 'Desktop')}")

if __name__ == "__main__":
    test_variable_expansion()
#!/usr/bin/env python3
"""
Teste de criação automática de diretórios com variáveis de sistema
"""

from src.wats.config import expand_system_variables
import os
import shutil
import sys
import tempfile

# Adiciona o src ao path para importar as funções
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))


def test_directory_creation():
    """Testa a criação automática de diretórios com variáveis expandidas."""
    print("🧪 Testando criação automática de diretórios com variáveis de sistema\n")

    # Cria um diretório temporário para os testes
    base_temp = tempfile.mkdtemp(prefix="wats_test_")
    print(f"📁 Diretório de teste: {base_temp}")

    try:
        # Simula uma configuração de usuário diferente para teste
        os.environ["TEST_USERPROFILE"] = base_temp

        test_paths = [
            "{TEST_USERPROFILE}/Videos/WATS",
            "{TEST_USERPROFILE}/Documents/Gravacoes/RDP",
            "{TEST_USERPROFILE}/Desktop/WATS_Output",
        ]

        print("\n🔨 Testando criação de diretórios:")

        for test_path in test_paths:
            # Expande as variáveis manualmente para o teste
            expanded_path = test_path.replace("{TEST_USERPROFILE}", base_temp)

            print(f"  🔹 Testando: {test_path}")
            print(f"     Expandido: {expanded_path}")

            # Verifica se não existe
            if not os.path.exists(expanded_path):
                print("     ✅ Diretório não existe, criando...")
                os.makedirs(expanded_path, exist_ok=True)

                if os.path.exists(expanded_path):
                    print("     ✅ Diretório criado com sucesso!")
                else:
                    print("     ❌ Falha na criação do diretório")
            else:
                print("     ⚠️ Diretório já existe")

            # Testa se é gravável
            try:
                test_file = os.path.join(expanded_path, "test.txt")
                with open(test_file, "w") as f:
                    f.write("teste")
                os.remove(test_file)
                print("     ✅ Diretório é gravável")
            except Exception as e:
                print(f"     ❌ Diretório não é gravável: {e}")

            print()

    finally:
        # Limpa o ambiente de teste
        if "TEST_USERPROFILE" in os.environ:
            del os.environ["TEST_USERPROFILE"]

        # Remove o diretório de teste
        try:
            shutil.rmtree(base_temp)
            print("🧹 Limpeza: Diretório de teste removido")
        except Exception as e:
            print(f"⚠️ Erro na limpeza: {e}")


def test_real_user_paths():
    """Testa os caminhos reais do usuário."""
    print("\n📋 Testando caminhos reais do usuário:\n")

    real_paths = [
        "{USERPROFILE}/Videos/WATS_Test",
        "{VIDEOS}/WATS_Test",
        "{DOCUMENTS}/WATS_Test",
    ]

    for path in real_paths:
        expanded = expand_system_variables(path)
        exists = os.path.exists(expanded)
        parent_exists = os.path.exists(os.path.dirname(expanded))

        print(f"  🔹 {path}")
        print(f"     → {expanded}")
        print(f"     📁 Existe: {'✅' if exists else '❌'}")
        print(f"     📂 Pasta pai existe: {'✅' if parent_exists else '❌'}")

        if parent_exists and not exists:
            print("     🔨 Pode ser criado: ✅")
        elif not parent_exists:
            print("     🔨 Pasta pai precisa ser criada primeiro")

        print()


if __name__ == "__main__":
    test_directory_creation()
    test_real_user_paths()

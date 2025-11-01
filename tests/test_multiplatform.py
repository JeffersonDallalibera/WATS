#!/usr/bin/env python3
"""
Teste da funcionalidade RDP multiplataforma do WATS
"""

import os
import sys

# Adiciona o diretório src ao path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_platform_detection():
    """Testa detecção de plataforma"""
    print("=== TESTE DE DETECÇÃO DE PLATAFORMA ===")

    try:
        from wats.utils.platform_utils import (
            HAS_WIN32,
            IS_LINUX,
            IS_MACOS,
            IS_WINDOWS,
            get_platform_info,
            is_platform_supported,
        )

        print(f"Plataforma atual: {get_platform_info()['system']}")
        print(f"Windows: {IS_WINDOWS}")
        print(f"Linux: {IS_LINUX}")
        print(f"macOS: {IS_MACOS}")
        print(f"Win32 disponível: {HAS_WIN32}")
        print(f"Plataforma suportada: {is_platform_supported()}")
        print("✅ Detecção de plataforma OK")

    except Exception as e:
        print(f"❌ Erro na detecção de plataforma: {e}")
        return False

    return True


def test_rdp_connector():
    """Testa conector RDP"""
    print("\n=== TESTE DE CONECTOR RDP ===")

    try:
        from wats.utils.rdp_connector import rdp_connector

        # Verifica disponibilidade
        is_available, status_msg = rdp_connector.is_rdp_available()
        print(f"RDP disponível: {is_available}")
        print(f"Status: {status_msg}")

        # Mostra instruções de instalação
        if not is_available:
            print("\nInstruções de instalação:")
            print(rdp_connector.get_installation_instructions())

        print("✅ Conector RDP OK")

    except Exception as e:
        print(f"❌ Erro no conector RDP: {e}")
        return False

    return True


def test_rdp_connection_simulation():
    """Simula uma conexão RDP (sem executar)"""
    print("\n=== TESTE DE SIMULAÇÃO DE CONEXÃO ===")

    try:
        from wats.utils.rdp_connector import rdp_connector

        # Dados de teste
        test_data = {
            "ip": "192.168.1.100",
            "user": "test_user",
            "pwd": "test_password",
            "title": "Teste WATS",
            "port": "3389",
        }

        print(f"Dados de teste: {test_data['ip']} - {test_data['title']}")

        # Simula verificação (sem executar conexão real)
        is_available, status_msg = rdp_connector.is_rdp_available()

        if is_available:
            print("✅ Conexão seria possível")
            print(f"Cliente disponível: {status_msg}")
        else:
            print("⚠️ Conexão não seria possível")
            print(f"Motivo: {status_msg}")

        print("✅ Simulação de conexão OK")

    except Exception as e:
        print(f"❌ Erro na simulação: {e}")
        return False

    return True


def main():
    """Executa todos os testes"""
    print("🧪 TESTE MULTIPLATAFORMA WATS - RDP")
    print("=" * 50)

    tests = [test_platform_detection, test_rdp_connector, test_rdp_connection_simulation]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Teste falhou: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"Total: {total}")
    print(f"Passou: {passed}")
    print(f"Falhou: {failed}")

    if all(results):
        print("🎉 Todos os testes passaram!")
        return 0
    else:
        print("💥 Alguns testes falharam!")
        return 1


if __name__ == "__main__":
    sys.exit(main())

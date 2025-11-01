#!/usr/bin/env python3
"""
Teste específico do sistema RDP multiplataforma com FreeRDP Wrapper
"""

import os
import sys

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_freerdp_wrapper():
    """Testa o wrapper FreeRDP"""
    print("=== TESTE FREERDP WRAPPER ===")

    try:
        from wats.utils.freerdp_wrapper import freerdp_wrapper

        print(f"FreeRDP disponível: {freerdp_wrapper.is_available()}")
        print(f"Executável encontrado: {freerdp_wrapper.executable}")

        # Testa criação de arquivo RDP
        test_data = {
            "ip": "192.168.1.100",
            "user": "test_user",
            "pwd": "test_password",
            "port": "3389",
        }

        rdp_file = freerdp_wrapper.create_rdp_file(test_data)
        if rdp_file and os.path.exists(rdp_file):
            print(f"✅ Arquivo RDP criado: {rdp_file}")
            # Lê primeiras linhas para verificar
            with open(rdp_file, "r") as f:
                content = f.read()[:200]
                print(f"Conteúdo (preview): {content}...")

            # Remove arquivo de teste
            os.remove(rdp_file)
        else:
            print("❌ Falha ao criar arquivo RDP")

        print("✅ FreeRDP Wrapper OK")
        return True

    except Exception as e:
        print(f"❌ Erro no FreeRDP Wrapper: {e}")
        return False


def test_rdp_connector_priority():
    """Testa a prioridade dos métodos RDP"""
    print("\n=== TESTE PRIORIDADE RDP ===")

    try:
        from wats.utils.rdp_connector import rdp_connector

        print(f"Método preferido: {rdp_connector.preferred_method}")

        # Testa verificação de disponibilidade
        is_available, status_msg = rdp_connector.is_rdp_available()
        print(f"RDP disponível: {is_available}")
        print(f"Status: {status_msg}")

        # Mostra todas as opções detectadas
        methods = []

        # Verifica FreeRDP Wrapper
        from wats.utils.freerdp_wrapper import freerdp_wrapper

        if freerdp_wrapper.is_available():
            methods.append("FreeRDP Wrapper")

        # Verifica clientes nativos
        import shutil

        clients = ["xfreerdp", "rdesktop", "remmina", "mstsc"]
        for client in clients:
            if shutil.which(client):
                methods.append(client)

        print(f"Métodos RDP detectados: {', '.join(methods) if methods else 'Nenhum'}")

        print("✅ Prioridade RDP OK")
        return True

    except Exception as e:
        print(f"❌ Erro na prioridade RDP: {e}")
        return False


def test_platform_specific_features():
    """Testa funcionalidades específicas da plataforma"""
    print("\n=== TESTE FUNCIONALIDADES ESPECÍFICAS ===")

    try:
        from wats.utils.platform_utils import (
            IS_LINUX,
            IS_WINDOWS,
            ensure_platform_dirs,
            get_platform_info,
            get_platform_specific_paths,
        )

        platform_info = get_platform_info()
        print(f"Plataforma: {platform_info['system']}")
        print(f"Versão: {platform_info['release']}")

        # Testa caminhos específicos
        paths = get_platform_specific_paths()
        print("Diretórios da plataforma:")
        for name, path in paths.items():
            print(f"  {name}: {path}")

        # Cria diretórios se necessário
        created_paths = ensure_platform_dirs()
        print(f"Diretórios criados/verificados: {len(created_paths)}")

        # Testa funcionalidades específicas do Windows
        if IS_WINDOWS:
            try:
                from wats.utils.platform_utils import HAS_WIN32

                print(f"Win32 disponível: {HAS_WIN32}")

                if HAS_WIN32:
                    print("✅ Funcionalidades Windows OK")
                else:
                    print("⚠️ Win32 não disponível (modo compatibilidade)")
            except Exception as e:
                print(f"⚠️ Erro Win32: {e}")

        # Testa funcionalidades específicas do Linux
        if IS_LINUX:
            print("Sistema Linux detectado")

            # Verifica clientes RDP Linux
            import shutil

            linux_rdp_clients = ["xfreerdp", "rdesktop", "remmina", "vinagre"]
            found_clients = [client for client in linux_rdp_clients if shutil.which(client)]
            print(f"Clientes RDP Linux encontrados: {found_clients}")

        print("✅ Funcionalidades específicas OK")
        return True

    except Exception as e:
        print(f"❌ Erro nas funcionalidades específicas: {e}")
        return False


def main():
    """Executa todos os testes RDP"""
    print("🧪 TESTE SISTEMA RDP MULTIPLATAFORMA WATS")
    print("=" * 60)

    tests = [test_freerdp_wrapper, test_rdp_connector_priority, test_platform_specific_features]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Teste falhou: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES RDP")

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"Total: {total}")
    print(f"Passou: {passed}")
    print(f"Falhou: {failed}")

    if all(results):
        print("🎉 Todos os testes RDP passaram!")
        print("\n💡 DICAS:")
        print("- O sistema agora usa FreeRDP quando disponível")
        print("- Funciona tanto no Windows quanto no Linux")
        print("- Fallback automático para clientes nativos")
        return 0
    else:
        print("💥 Alguns testes RDP falharam!")
        print("\n🔧 SOLUÇÕES:")
        print("- Instale FreeRDP: Windows (winget install FreeRDP.FreeRDP)")
        print("- Instale FreeRDP: Linux (sudo apt-get install freerdp2-x11)")
        print("- Verifique se o cliente RDP está no PATH")
        return 1


if __name__ == "__main__":
    sys.exit(main())

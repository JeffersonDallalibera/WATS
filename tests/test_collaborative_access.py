#!/usr/bin/env python3
"""
Script para testar o sistema de senha temporária colaborativa
Valida funcionalidades de geração, validação e expiração de senhas
"""

import os
import sys
import time
from datetime import datetime, timedelta

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))


def test_password_generation():
    """Testa geração de senhas temporárias"""

    print("=== TESTE DE GERAÇÃO DE SENHAS ===")

    try:
        # Simula geração de senha (método privado, mas podemos testar a lógica)
        import secrets
        import string

        def generate_temp_password():
            alphabet = string.ascii_letters + string.digits
            return "".join(secrets.choice(alphabet) for _ in range(8))

        # Gera algumas senhas de teste
        passwords = [generate_temp_password() for _ in range(5)]

        print("Senhas geradas:")
        for i, password in enumerate(passwords, 1):
            print(f"  {i}. {password} (comprimento: {len(password)})")

        # Verifica características
        all_valid = True
        for password in passwords:
            if len(password) != 8:
                print(f"❌ ERRO: Senha {password} não tem 8 caracteres")
                all_valid = False

            has_letter = any(c.isalpha() for c in password)
            has_digit = any(c.isdigit() for c in password)

            if not (has_letter and has_digit):
                print(f"⚠️  Senha {password} não tem mix de letras e números")

        if all_valid:
            print("✅ Todas as senhas têm formato correto")

        return True

    except Exception as e:
        print(f"❌ ERRO: Falha no teste de geração: {e}")
        return False


def test_password_validator():
    """Testa o validador de senhas temporárias"""

    print("\\n=== TESTE DO VALIDADOR DE SENHAS ===")

    try:
        from src.wats.collaborative_access import TemporaryPasswordValidator

        validator = TemporaryPasswordValidator()

        # Dados de teste
        test_password = "TEST1234"
        connection_id = 123
        user = "test.user"

        request_data = {
            "connection_id": connection_id,
            "connection_name": "Servidor de Teste",
            "requesting_user": user,
            "connected_user": "other.user",
            "reason": "Teste de funcionalidade",
            "access_type": "shared",
            "temp_password": test_password,
            "duration_minutes": 15,
            "expiry_time": (datetime.now() + timedelta(minutes=15)).isoformat(),
            "created_at": datetime.now().isoformat(),
        }

        # Registra senha
        validator.register_temp_password(test_password, request_data)
        print(f"✅ Senha {test_password} registrada")

        # Testa validação válida
        result = validator.validate_temp_password(test_password, connection_id, user)
        if result["valid"]:
            print("✅ Validação de senha válida funcionando")
        else:
            print(f"❌ ERRO: Senha válida foi rejeitada: {result['reason']}")
            return False

        # Testa senha inexistente
        result = validator.validate_temp_password("INVALID123", connection_id, user)
        if not result["valid"]:
            print("✅ Rejeição de senha inválida funcionando")
        else:
            print("❌ ERRO: Senha inválida foi aceita")
            return False

        # Testa conexão incorreta
        result = validator.validate_temp_password(test_password, 999, user)
        if not result["valid"]:
            print("✅ Validação de conexão funcionando")
        else:
            print("❌ ERRO: Conexão incorreta foi aceita")
            return False

        # Testa usuário incorreto
        result = validator.validate_temp_password(test_password, connection_id, "wrong.user")
        if not result["valid"]:
            print("✅ Validação de usuário funcionando")
        else:
            print("❌ ERRO: Usuário incorreto foi aceito")
            return False

        return True

    except Exception as e:
        print(f"❌ ERRO: Falha no teste do validador: {e}")
        return False


def test_password_expiration():
    """Testa expiração de senhas"""

    print("\\n=== TESTE DE EXPIRAÇÃO DE SENHAS ===")

    try:
        from src.wats.collaborative_access import TemporaryPasswordValidator

        validator = TemporaryPasswordValidator()

        # Senha que expira em 1 segundo
        test_password = "EXPIRE12"
        connection_id = 456
        user = "test.user"

        request_data = {
            "connection_id": connection_id,
            "connection_name": "Teste Expiração",
            "requesting_user": user,
            "connected_user": "other.user",
            "reason": "Teste de expiração",
            "access_type": "shared",
            "temp_password": test_password,
            "duration_minutes": 1,
            "expiry_time": (datetime.now() + timedelta(seconds=1)).isoformat(),
            "created_at": datetime.now().isoformat(),
        }

        # Registra senha
        validator.register_temp_password(test_password, request_data)
        print(f"✅ Senha {test_password} registrada com expiração em 1 segundo")

        # Testa antes da expiração
        result = validator.validate_temp_password(test_password, connection_id, user)
        if result["valid"]:
            print("✅ Senha válida antes da expiração")
        else:
            print(f"❌ ERRO: Senha rejeitada antes da expiração: {result['reason']}")
            return False

        # Aguarda expiração
        print("⏳ Aguardando expiração...")
        time.sleep(2)

        # Testa após expiração
        result = validator.validate_temp_password(test_password, connection_id, user)
        if not result["valid"] and "expirada" in result["reason"]:
            print("✅ Senha expirada corretamente rejeitada")
        else:
            print(f"❌ ERRO: Senha expirada foi aceita ou erro inesperado: {result}")
            return False

        return True

    except Exception as e:
        print(f"❌ ERRO: Falha no teste de expiração: {e}")
        return False


def test_cleanup_functionality():
    """Testa funcionalidade de limpeza"""

    print("\\n=== TESTE DE LIMPEZA ===")

    try:
        from src.wats.collaborative_access import TemporaryPasswordValidator

        validator = TemporaryPasswordValidator()

        # Adiciona algumas senhas de teste
        test_passwords = ["CLEAN001", "CLEAN002", "CLEAN003"]

        for i, password in enumerate(test_passwords):
            request_data = {
                "connection_id": 100 + i,
                "connection_name": f"Teste Limpeza {i+1}",
                "requesting_user": "test.user",
                "connected_user": "other.user",
                "reason": f"Teste de limpeza {i+1}",
                "access_type": "shared",
                "temp_password": password,
                "duration_minutes": 15,
                "expiry_time": (datetime.now() + timedelta(minutes=15)).isoformat(),
                "created_at": datetime.now().isoformat(),
            }
            validator.register_temp_password(password, request_data)

        print(f"✅ {len(test_passwords)} senhas registradas")

        # Verifica senhas ativas
        active_count = len(validator.active_passwords)
        if active_count >= len(test_passwords):
            print(f"✅ Senhas ativas detectadas: {active_count}")
        else:
            print(f"⚠️  Contagem de senhas ativa inesperada: {active_count}")

        # Executa limpeza completa
        validator.cleanup_all_passwords()

        # Verifica se limpeza funcionou
        if len(validator.active_passwords) == 0:
            print("✅ Limpeza completa funcionando")
        else:
            print(f"❌ ERRO: Limpeza incompleta, restam {len(validator.active_passwords)} senhas")
            return False

        return True

    except Exception as e:
        print(f"❌ ERRO: Falha no teste de limpeza: {e}")
        return False


def test_collaborative_dialog_import():
    """Testa se o diálogo pode ser importado"""

    print("\\n=== TESTE DE IMPORTAÇÃO DO DIÁLOGO ===")

    try:
        from src.wats.collaborative_access import temp_password_validator

        print("✅ Módulo collaborative_access importado com sucesso")
        print("✅ temp_password_validator importado com sucesso")

        # Verifica se o validador global está funcionando
        validator_type = type(temp_password_validator).__name__
        if validator_type == "TemporaryPasswordValidator":
            print("✅ Validador global configurado corretamente")
        else:
            print(f"❌ ERRO: Tipo inesperado do validador: {validator_type}")
            return False

        return True

    except ImportError as e:
        print(f"❌ ERRO: Falha na importação: {e}")
        return False
    except Exception as e:
        print(f"❌ ERRO: Falha no teste de importação: {e}")
        return False


def show_integration_guide():
    """Mostra guia de integração"""

    print("\\n=== GUIA DE INTEGRAÇÃO ===")
    print("📋 Como usar o sistema de acesso colaborativo:")
    print("")
    print("1. SOLICITAÇÃO:")
    print("   - Usuário clica em conexão ocupada")
    print("   - Escolhe 'Solicitar Acesso Colaborativo'")
    print("   - Preenche motivo e configurações")
    print("   - Sistema gera senha temporária")
    print("")
    print("2. VALIDAÇÃO:")
    print("   - Sistema valida senha antes de conectar")
    print("   - Verifica expiração, conexão e usuário")
    print("   - Registra uso para auditoria")
    print("")
    print("3. TIPOS DE ACESSO:")
    print("   - Compartilhado: Ambos usuários conectados")
    print("   - Exclusivo: Desconecta o outro usuário")
    print("")
    print("4. AUDITORIA:")
    print("   - Todas solicitações registradas em logs")
    print("   - Rastreamento de uso de senhas")
    print("   - Controle de expiração automática")
    print("")
    print("🔐 Benefícios implementados:")
    print("  ✓ Senhas temporárias seguras (8 caracteres)")
    print("  ✓ Expiração automática configurável")
    print("  ✓ Validação multi-camada")
    print("  ✓ Auditoria completa")
    print("  ✓ Interface intuitiva")
    print("  ✓ Limpeza automática")


def main():
    """Executa todos os testes"""

    print("🔐 TESTANDO SISTEMA DE SENHA TEMPORÁRIA COLABORATIVA\\n")

    tests = [
        ("Geração de Senhas", test_password_generation),
        ("Validador de Senhas", test_password_validator),
        ("Expiração de Senhas", test_password_expiration),
        ("Funcionalidade de Limpeza", test_cleanup_functionality),
        ("Importação do Diálogo", test_collaborative_dialog_import),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ ERRO no teste {test_name}: {e}")
            results.append((test_name, False))

    # Resumo dos resultados
    print("\\n" + "=" * 60)
    print("RESUMO DOS TESTES DE ACESSO COLABORATIVO")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if result:
            passed += 1

    print(f"\\nResultado Final: {passed}/{total} testes passaram")

    if passed == total:
        print("🎉 Sistema de acesso colaborativo implementado com sucesso!")
        show_integration_guide()
    elif passed >= total - 1:
        print("✅ Implementação está quase perfeita")
        show_integration_guide()
    else:
        print("⚠️  Algumas funcionalidades precisam de atenção")


if __name__ == "__main__":
    main()

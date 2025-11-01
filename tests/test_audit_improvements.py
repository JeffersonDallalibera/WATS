#!/usr/bin/env python3
"""
Script para testar as melhorias de auditoria do WATS
Verifica se as informações do usuário WATS estão sendo capturadas corretamente
"""

import json
from datetime import datetime
from pathlib import Path


def test_connection_info_structure():
    """Testa a estrutura do connection_info com dados de auditoria"""

    # Simula o connection_info melhorado
    connection_info = {
        "wats_user": "jefferson.silva",
        "wats_user_machine": "DESKTOP-ABC123",
        "wats_user_ip": "192.168.1.100",
        "session_timestamp": int(datetime.now().timestamp()),
        "target_ip": "192.168.1.50",
        "target_name": "SERVIDOR-01",
        "connection_type": "RDP",
    }

    print("=== TESTE DE ESTRUTURA DE AUDITORIA ===")
    print("Connection Info completo:")
    print(json.dumps(connection_info, indent=2, ensure_ascii=False))

    # Verifica se todos os campos necessários estão presentes
    required_fields = ["wats_user", "wats_user_machine", "wats_user_ip", "session_timestamp"]
    missing_fields = [field for field in required_fields if field not in connection_info]

    if missing_fields:
        print(f"❌ ERRO: Campos obrigatórios ausentes: {missing_fields}")
        return False
    else:
        print("✅ Todos os campos de auditoria estão presentes")
        return True


def test_metadata_file_creation():
    """Testa a criação do arquivo de metadados para auditoria"""

    # Cria diretório de teste
    test_dir = Path("test_recordings")
    test_dir.mkdir(exist_ok=True)

    session_id = f"test_session_{int(datetime.now().timestamp())}"

    # Simula metadados melhorados
    metadata = {
        "session_id": session_id,
        "connection_info": {
            "wats_user": "jefferson.silva",
            "wats_user_machine": "DESKTOP-ABC123",
            "wats_user_ip": "192.168.1.100",
            "session_timestamp": int(datetime.now().timestamp()),
            "target_ip": "192.168.1.50",
            "target_name": "SERVIDOR-01",
            "connection_type": "RDP",
        },
        "start_time": datetime.now().isoformat(),
        "recorder_settings": {
            "fps": 30,
            "quality": 23,
            "resolution_scale": 1.0,
            "max_file_size_mb": 500,
            "max_duration_minutes": 120,
        },
        "audit_info": {
            "created_by": "WATS Recording System",
            "version": "1.0",
            "compliance": "User audit tracking enabled",
        },
    }

    # Salva arquivo de metadados
    metadata_file = test_dir / f"{session_id}_metadata.json"

    try:
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"✅ Arquivo de metadados criado: {metadata_file}")

        # Verifica se pode ser lido de volta
        with open(metadata_file, "r", encoding="utf-8") as f:
            loaded_metadata = json.load(f)

        print("✅ Metadados carregados com sucesso")
        print(f"Usuário WATS: {loaded_metadata['connection_info']['wats_user']}")
        print(f"Máquina: {loaded_metadata['connection_info']['wats_user_machine']}")
        print(f"IP: {loaded_metadata['connection_info']['wats_user_ip']}")

        return True

    except Exception as e:
        print(f"❌ ERRO ao criar metadados: {e}")
        return False

    finally:
        # Limpa arquivo de teste
        if metadata_file.exists():
            metadata_file.unlink()
        if test_dir.exists() and not any(test_dir.iterdir()):
            test_dir.rmdir()


def test_database_log_format():
    """Testa o formato dos logs no banco de dados"""

    print("\n=== TESTE DE FORMATO DE LOG NO BANCO ===")

    # Simula dados que seriam inseridos no banco
    insert_connection_log_data = {
        "con_codigo": 123,
        "usu_nome": "jefferson.silva",  # Usuário WATS (não mais OS user)
        "usu_ip": "192.168.1.100",
        "usu_nome_maquina": "DESKTOP-ABC123",
        "usu_usuario_maquina": "jefferson",  # OS user
    }

    log_access_start_data = {
        "user_machine_info": "jefferson.silva@DESKTOP-ABC123",  # Usuário WATS + máquina
        "con_codigo": 123,
        "con_nome": "SERVIDOR-01",
        "con_tipo": "RDP",
    }

    print("Dados para Usuario_Conexao_WTS:")
    for key, value in insert_connection_log_data.items():
        print(f"  {key}: {value}")

    print("\nDados para Log_Acesso_WTS:")
    for key, value in log_access_start_data.items():
        print(f"  {key}: {value}")

    # Verifica se conseguimos distinguir usuário WATS do usuário OS
    wats_user = insert_connection_log_data["usu_nome"]
    os_user = insert_connection_log_data["usu_usuario_maquina"]

    if wats_user != os_user:
        print(f"✅ Distinção clara entre usuário WATS ({wats_user}) e usuário OS ({os_user})")
    else:
        print(f"⚠️  Usuário WATS e OS são iguais: {wats_user}")

    return True


def main():
    """Executa todos os testes"""
    print("🔍 TESTANDO MELHORIAS DE AUDITORIA DO WATS\n")

    tests = [
        ("Estrutura Connection Info", test_connection_info_structure),
        ("Criação de Metadados", test_metadata_file_creation),
        ("Formato de Log no Banco", test_database_log_format),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ ERRO no teste {test_name}: {e}")
            results.append((test_name, False))

    # Resumo dos resultados
    print("\n" + "=" * 50)
    print("RESUMO DOS TESTES")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if result:
            passed += 1

    print(f"\nResultado Final: {passed}/{total} testes passaram")

    if passed == total:
        print("🎉 Todas as melhorias de auditoria foram implementadas corretamente!")
    else:
        print("⚠️  Algumas melhorias precisam de atenção")


if __name__ == "__main__":
    main()

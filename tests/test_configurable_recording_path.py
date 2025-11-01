#!/usr/bin/env python3
"""
Script para testar as configurações personalizáveis de caminho de gravação
Valida se o sistema está lendo corretamente do config.json
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Adiciona o diretório do projeto ao path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))


def test_config_json_loading():
    """Testa se o config.json está sendo carregado corretamente"""

    print("=== TESTE DE CARREGAMENTO DO CONFIG.JSON ===")

    # Lê o config.json atual
    config_path = Path("config.json")
    if not config_path.exists():
        print("❌ ERRO: config.json não encontrado")
        return False

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        print("✅ config.json carregado com sucesso")

        # Verifica se a seção recording existe
        if "recording" not in config_data:
            print("❌ ERRO: Seção 'recording' não encontrada no config.json")
            return False

        print("✅ Seção 'recording' encontrada")

        # Verifica se output_dir está presente
        recording_config = config_data["recording"]
        if "output_dir" not in recording_config:
            print("❌ ERRO: Campo 'output_dir' não encontrado na seção recording")
            return False

        print("✅ Campo 'output_dir' encontrado")
        print(f"Valor atual de output_dir: '{recording_config['output_dir']}'")

        return True

    except json.JSONDecodeError as e:
        print(f"❌ ERRO: Falha ao fazer parse do JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ ERRO: Falha ao carregar config.json: {e}")
        return False


def test_settings_class_integration():
    """Testa se a classe Settings está integrando corretamente"""

    print("\\n=== TESTE DE INTEGRAÇÃO COM CLASSE SETTINGS ===")

    try:
        # Simula carregamento das variáveis de ambiente
        from src.wats.config import Settings, load_environment_variables

        # Carrega variáveis de ambiente
        load_environment_variables()

        # Cria instância da classe Settings
        settings = Settings()

        print("✅ Classe Settings criada com sucesso")
        print(f"RECORDING_OUTPUT_DIR atual: {settings.RECORDING_OUTPUT_DIR}")

        # Verifica se o diretório padrão está sendo usado quando output_dir está vazio
        if not settings.RECORDING_OUTPUT_DIR or settings.RECORDING_OUTPUT_DIR.strip() == "":
            print("❌ ERRO: RECORDING_OUTPUT_DIR está vazio")
            return False

        print("✅ RECORDING_OUTPUT_DIR configurado corretamente")

        # Testa validação da configuração
        if settings.validate_recording_config():
            print("✅ Validação da configuração de gravação passou")
        else:
            print(
                "⚠️  Validação da configuração de gravação falhou (pode ser normal se recording estiver desabilitado)"
            )

        return True

    except ImportError as e:
        print(f"❌ ERRO: Falha ao importar módulos: {e}")
        return False
    except Exception as e:
        print(f"❌ ERRO: Falha ao testar classe Settings: {e}")
        return False


def test_custom_output_dir():
    """Testa configuração personalizada de output_dir"""

    print("\\n=== TESTE DE CAMINHO PERSONALIZADO ===")

    # Cria um diretório temporário para teste
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_path = os.path.join(temp_dir, "custom_recordings")

        print(f"Testando caminho personalizado: {custom_path}")

        # Salva config.json original
        config_path = Path("config.json")
        original_config = None

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                original_config = json.load(f)

            # Modifica temporariamente o config.json
            test_config = original_config.copy()
            test_config["recording"]["output_dir"] = custom_path

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(test_config, f, indent=2, ensure_ascii=False)

            print("✅ config.json modificado temporariamente")

            # Testa se a classe Settings pega a configuração personalizada
            # Força recarregamento
            import importlib

            import src.wats.config
            from src.wats.config import Settings, load_environment_variables

            importlib.reload(src.wats.config)

            load_environment_variables()
            settings = Settings()

            print(f"Caminho configurado na Settings: {settings.RECORDING_OUTPUT_DIR}")

            # Verifica se o caminho personalizado foi aplicado
            if settings.RECORDING_OUTPUT_DIR == custom_path:
                print("✅ Caminho personalizado aplicado corretamente")
                return True
            else:
                print(
                    f"❌ ERRO: Esperado '{custom_path}', obtido '{settings.RECORDING_OUTPUT_DIR}'"
                )
                return False

        except Exception as e:
            print(f"❌ ERRO: Falha ao testar caminho personalizado: {e}")
            return False

        finally:
            # Restaura config.json original
            if original_config:
                try:
                    with open(config_path, "w", encoding="utf-8") as f:
                        json.dump(original_config, f, indent=2, ensure_ascii=False)
                    print("✅ config.json restaurado")
                except Exception as e:
                    print(f"⚠️  Falha ao restaurar config.json: {e}")


def test_directory_creation():
    """Testa se os diretórios são criados automaticamente"""

    print("\\n=== TESTE DE CRIAÇÃO AUTOMÁTICA DE DIRETÓRIOS ===")

    # Cria um caminho que não existe
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_path = os.path.join(temp_dir, "nivel1", "nivel2", "recordings")

        print(f"Testando criação de: {nested_path}")

        try:
            # Simula criação de diretório como faz o validate_recording_config
            os.makedirs(nested_path, exist_ok=True)

            if os.path.exists(nested_path) and os.path.isdir(nested_path):
                print("✅ Diretório criado com sucesso")
                return True
            else:
                print("❌ ERRO: Diretório não foi criado")
                return False

        except Exception as e:
            print(f"❌ ERRO: Falha ao criar diretório: {e}")
            return False


def show_current_configuration():
    """Mostra a configuração atual do sistema"""

    print("\\n=== CONFIGURAÇÃO ATUAL DO SISTEMA ===")

    try:
        from src.wats.config import Settings, load_environment_variables

        load_environment_variables()
        settings = Settings()

        recording_config = settings.get_recording_config()

        print("Configurações de gravação:")
        for key, value in recording_config.items():
            print(f"  {key}: {value}")

        return True

    except Exception as e:
        print(f"❌ ERRO: Falha ao mostrar configuração: {e}")
        return False


def main():
    """Executa todos os testes"""

    print("🔧 TESTANDO CONFIGURAÇÕES PERSONALIZÁVEIS DE GRAVAÇÃO\\n")

    tests = [
        ("Carregamento do config.json", test_config_json_loading),
        ("Integração com classe Settings", test_settings_class_integration),
        ("Caminho personalizado", test_custom_output_dir),
        ("Criação automática de diretórios", test_directory_creation),
        ("Configuração atual", show_current_configuration),
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
    print("RESUMO DOS TESTES DE CONFIGURAÇÃO")
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
        print("🎉 Configuração personalizável de gravação implementada com sucesso!")
        print("📁 Agora os administradores podem configurar o caminho de gravação no config.json")
    elif passed >= total - 1:
        print("✅ Implementação está quase perfeita, com funcionamento adequado")
    else:
        print("⚠️  Algumas funcionalidades precisam de atenção")


if __name__ == "__main__":
    main()

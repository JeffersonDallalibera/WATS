#!/usr/bin/env python3
"""
Script para atualizar config.json existente com configurações de gravação inteligente.
Preserva configurações existentes e adiciona apenas as novas opções.
"""

import json
import sys
from pathlib import Path


def update_config_with_smart_recording(config_path: Path, backup: bool = True) -> bool:
    """
    Atualiza config.json existente com configurações de gravação inteligente.

    Args:
        config_path: Caminho para o arquivo config.json
        backup: Se deve criar backup antes de modificar

    Returns:
        True se a atualização foi bem-sucedida
    """

    if not config_path.exists():
        print(f"❌ Arquivo não encontrado: {config_path}")
        return False

    try:
        # Carrega configuração existente
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        print(f"✓ Carregado: {config_path}")

        # Cria backup se solicitado
        if backup:
            backup_path = config_path.with_suffix(".json.bak")
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✓ Backup criado: {backup_path}")

        # Garante que existe seção recording
        if "recording" not in config:
            config["recording"] = {}

        recording_config = config["recording"]

        # Configurações básicas de gravação (se não existirem)
        basic_defaults = {
            "enabled": True,
            "fps": 30,
            "quality": 75,
            "resolution_scale": 1.0,
            "max_file_size_mb": 100,
            "max_duration_minutes": 30,
            "compression_enabled": True,
            "compression_crf": 28,
        }

        for key, value in basic_defaults.items():
            if key not in recording_config:
                recording_config[key] = value
                print(f"  + Adicionado: recording.{key} = {value}")

        # Configurações de gravação inteligente
        if "smart_recording" not in recording_config:
            recording_config["smart_recording"] = {}

        smart_config = recording_config["smart_recording"]

        smart_defaults = {
            "window_tracking_interval": 1.0,
            "inactivity_timeout_minutes": 10,
            "pause_on_minimized": True,
            "pause_on_covered": True,
            "create_new_file_after_pause": True,
            "debug_window_tracking": False,
            "debug_activity_monitoring": False,
        }

        for key, value in smart_defaults.items():
            if key not in smart_config:
                smart_config[key] = value
                print(f"  + Adicionado: recording.smart_recording.{key} = {value}")

        # Configurações de rotação de arquivo
        if "file_rotation" not in recording_config:
            recording_config["file_rotation"] = {}

        rotation_config = recording_config["file_rotation"]

        rotation_defaults = {
            "max_total_size_gb": 10.0,
            "max_file_age_days": 30,
            "cleanup_interval_hours": 6,
        }

        for key, value in rotation_defaults.items():
            if key not in rotation_config:
                rotation_config[key] = value
                print(f"  + Adicionado: recording.file_rotation.{key} = {value}")

        # Configurações de proteção de sessão
        if "session_protection" not in recording_config:
            recording_config["session_protection"] = {}

        protection_config = recording_config["session_protection"]

        protection_defaults = {
            "enabled": True,
            "sanitize_metadata": True,
            "remove_sensitive_fields": True,
            "log_protection_actions": True,
        }

        for key, value in protection_defaults.items():
            if key not in protection_config:
                protection_config[key] = value
                print(f"  + Adicionado: recording.session_protection.{key} = {value}")

        # Salva configuração atualizada
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"✓ Configuração atualizada: {config_path}")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Erro ao parsear JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


def create_sample_config(config_path: Path) -> bool:
    """
    Cria um arquivo config.json de exemplo completo.

    Args:
        config_path: Caminho onde criar o arquivo

    Returns:
        True se criado com sucesso
    """

    sample_config = {
        "_comment": "Configuração do WATS com Gravação Inteligente",
        "recording": {
            "_comment_basic": "Configurações básicas de gravação",
            "enabled": True,
            "output_dir": "./recordings",
            "fps": 30,
            "quality": 75,
            "resolution_scale": 1.0,
            "max_file_size_mb": 100,
            "max_duration_minutes": 30,
            "compression_enabled": True,
            "compression_crf": 28,
            "_comment_smart": "Configurações de gravação inteligente",
            "smart_recording": {
                "window_tracking_interval": 1.0,
                "inactivity_timeout_minutes": 10,
                "pause_on_minimized": True,
                "pause_on_covered": True,
                "create_new_file_after_pause": True,
                "debug_window_tracking": False,
                "debug_activity_monitoring": False,
            },
            "_comment_rotation": "Configurações de rotação e limpeza",
            "file_rotation": {
                "max_total_size_gb": 10.0,
                "max_file_age_days": 30,
                "cleanup_interval_hours": 6,
            },
            "_comment_protection": "Proteção de dados sensíveis",
            "session_protection": {
                "enabled": True,
                "sanitize_metadata": True,
                "remove_sensitive_fields": True,
                "log_protection_actions": True,
            },
        },
        "_comment_profiles": "Perfis pré-configurados",
        "recording_profiles": {
            "high_performance": {
                "fps": 15,
                "quality": 50,
                "resolution_scale": 0.8,
                "inactivity_timeout_minutes": 5,
            },
            "high_quality": {
                "fps": 60,
                "quality": 95,
                "compression_crf": 18,
                "inactivity_timeout_minutes": 15,
            },
            "minimal_interruption": {
                "pause_on_covered": False,
                "pause_on_minimized": False,
                "inactivity_timeout_minutes": 60,
            },
        },
    }

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(sample_config, f, indent=2, ensure_ascii=False)

        print(f"✓ Arquivo de exemplo criado: {config_path}")
        return True

    except Exception as e:
        print(f"❌ Erro ao criar arquivo: {e}")
        return False


def main():
    """Função principal do script."""

    if len(sys.argv) < 2:
        print("Uso:")
        print("  python update_config.py <config.json>          - Atualiza config existente")
        print("  python update_config.py --create <config.json> - Cria config de exemplo")
        print("  python update_config.py --help                 - Mostra esta ajuda")
        return

    if sys.argv[1] == "--help":
        print("Script de Atualização do Config.json para Gravação Inteligente")
        print()
        print("Este script:")
        print("  • Preserva todas as configurações existentes")
        print("  • Adiciona apenas configurações novas de gravação inteligente")
        print("  • Cria backup automático (.json.bak)")
        print("  • Valida JSON antes de modificar")
        print()
        print("Configurações adicionadas:")
        print("  • recording.smart_recording.*     - Controles inteligentes")
        print("  • recording.file_rotation.*       - Rotação de arquivos")
        print("  • recording.session_protection.*  - Proteção de dados")
        return

    if sys.argv[1] == "--create":
        if len(sys.argv) < 3:
            print("❌ Especifique o caminho do arquivo para criar")
            return

        config_path = Path(sys.argv[2])
        if config_path.exists():
            response = input(f"Arquivo {config_path} já existe. Sobrescrever? (y/N): ")
            if response.lower() not in ["y", "yes"]:
                print("Cancelado.")
                return

        if create_sample_config(config_path):
            print()
            print("📋 Arquivo de exemplo criado com sucesso!")
            print("   Edite as configurações conforme necessário.")
        return

    # Atualizar arquivo existente
    config_path = Path(sys.argv[1])

    print(f"🔧 Atualizando configuração: {config_path}")
    print()

    if update_config_with_smart_recording(config_path):
        print()
        print("🎉 Configuração atualizada com sucesso!")
        print("   • Configurações existentes preservadas")
        print("   • Novas opções de gravação inteligente adicionadas")
        print("   • Backup criado (.json.bak)")
        print()
        print("Próximos passos:")
        print("  1. Revisar as novas configurações")
        print("  2. Ajustar valores conforme necessário")
        print("  3. Testar o sistema de gravação")
    else:
        print()
        print("❌ Falha na atualização!")
        print("   Verifique se o arquivo JSON é válido.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script para validar configurações de SQL Server.
Verifica se as configurações estão corretas e testa conectividade.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any
import pyodbc

# Adiciona o src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from wats.core.config import Config
    from wats.core.models import DatabaseConfig
except ImportError:
    print("Erro: Não foi possível importar os módulos necessários.")
    print("Execute: pip install -r requirements.txt")
    sys.exit(1)


def validate_config_file(config_path: Path) -> Dict[str, Any]:
    """Valida um arquivo de configuração."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Valida usando Pydantic
        db_config = DatabaseConfig(**config_data.get('database', {}))
        
        print(f"✓ {config_path.name}: Configuração válida")
        return config_data
    
    except Exception as e:
        print(f"✗ {config_path.name}: Erro na validação - {e}")
        return {}


def test_sql_server_connection(db_config: DatabaseConfig) -> bool:
    """Testa conectividade com SQL Server."""
    try:
        if db_config.connection_string:
            conn_str = db_config.connection_string
        else:
            # Constrói connection string
            conn_parts = [
                f"DRIVER={{{db_config.driver}}}",
                f"SERVER={db_config.host},{db_config.port}",
                f"DATABASE={db_config.database}",
            ]
            
            if db_config.integrated_security:
                conn_parts.append("Trusted_Connection=yes")
            else:
                conn_parts.append(f"UID={db_config.username}")
                conn_parts.append(f"PWD={db_config.password}")
            
            if db_config.trust_server_certificate:
                conn_parts.append("TrustServerCertificate=yes")
            
            if db_config.encrypt:
                conn_parts.append("Encrypt=yes")
            
            if db_config.mars_connection:
                conn_parts.append("MARS_Connection=yes")
            
            conn_str = ";".join(conn_parts)
        
        # Tenta conectar
        with pyodbc.connect(conn_str, timeout=db_config.connection_timeout):
            print("✓ Conexão com SQL Server: SUCESSO")
            return True
    
    except Exception as e:
        print(f"✗ Conexão com SQL Server: FALHOU - {e}")
        return False


def check_drivers():
    """Verifica drivers ODBC disponíveis."""
    print("\n=== Drivers ODBC Disponíveis ===")
    drivers = pyodbc.drivers()
    sql_drivers = [d for d in drivers if 'SQL Server' in d]
    
    if sql_drivers:
        for driver in sql_drivers:
            print(f"✓ {driver}")
    else:
        print("✗ Nenhum driver SQL Server encontrado")
        print("Instale o Microsoft ODBC Driver for SQL Server")
    
    return len(sql_drivers) > 0


def main():
    """Função principal."""
    print("=== Validador de Configuração SQL Server ===\n")
    
    # Verifica drivers
    if not check_drivers():
        print("\nInstale drivers SQL Server e tente novamente.")
        return
    
    # Diretório de configurações
    config_dir = Path(__file__).parent.parent / "config" / "environments"
    
    if not config_dir.exists():
        print(f"Erro: Diretório {config_dir} não encontrado")
        return
    
    print("\n=== Validando Arquivos de Configuração ===")
    
    # Valida cada arquivo de configuração
    configs = {}
    for config_file in config_dir.glob("*.json"):
        if config_file.name != "base.json":
            config_data = validate_config_file(config_file)
            if config_data:
                configs[config_file.stem] = config_data
    
    print("\n=== Testando Conectividade ===")
    
    # Testa conectividade para cada ambiente
    for env_name, config_data in configs.items():
        if 'database' in config_data:
            print(f"\n--- Ambiente: {env_name} ---")
            try:
                db_config = DatabaseConfig(**config_data['database'])
                test_sql_server_connection(db_config)
            except Exception as e:
                print(f"✗ Erro ao testar {env_name}: {e}")
    
    print("\n=== Validação Concluída ===")


if __name__ == "__main__":
    main()
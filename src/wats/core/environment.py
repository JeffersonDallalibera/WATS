"""Environment-specific configuration management for WATS."""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union
import logging


class EnvironmentConfig:
    """
    Gerenciador de configurações específicas por ambiente.
    
    Suporta múltiplos ambientes (development, testing, staging, production)
    com substituição de variáveis de ambiente e herança de configurações.
    """
    
    ENVIRONMENTS = {
        "development": "dev",
        "testing": "test", 
        "staging": "stage",
        "production": "prod"
    }
    
    def __init__(self, base_config_dir: Union[str, Path]):
        """
        Inicializa o gerenciador de configurações.
        
        Args:
            base_config_dir: Diretório base das configurações
        """
        self.config_dir = Path(base_config_dir)
        self.environments_dir = self.config_dir / "environments"
        self.current_env = self._detect_environment()
        self._config_cache: Dict[str, Any] = {}
        
    def _detect_environment(self) -> str:
        """
        Detecta o ambiente atual baseado em variáveis de ambiente.
        
        Returns:
            Nome do ambiente detectado
        """
        # Prioridade: WATS_ENV > ENVIRONMENT > NODE_ENV > padrão
        env_vars = ["WATS_ENV", "ENVIRONMENT", "NODE_ENV"]
        
        for var in env_vars:
            env_value = os.getenv(var, "").lower()
            if env_value in self.ENVIRONMENTS:
                logging.info(f"Ambiente detectado via {var}: {env_value}")
                return env_value
            # Verifica aliases
            for full_name, alias in self.ENVIRONMENTS.items():
                if env_value == alias:
                    logging.info(f"Ambiente detectado via {var} (alias): {full_name}")
                    return full_name
        
        # Detecta baseado em características do ambiente
        if os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true":
            logging.info("Ambiente CI detectado, usando 'testing'")
            return "testing"
            
        if os.getenv("WATS_DEMO_MODE") == "true":
            logging.info("Modo demo detectado, usando 'development'")
            return "development"
            
        # Padrão para desenvolvimento local
        logging.info("Nenhum ambiente específico detectado, usando 'development'")
        return "development"
    
    def get_config(self, reload: bool = False) -> Dict[str, Any]:
        """
        Obtém a configuração completa para o ambiente atual.
        
        Args:
            reload: Se deve recarregar do disco ignorando cache
            
        Returns:
            Dicionário com configurações mescladas
        """
        cache_key = f"config_{self.current_env}"
        
        if not reload and cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        # Carrega configuração base se existir
        base_config = self._load_base_config()
        
        # Carrega configuração específica do ambiente
        env_config = self._load_environment_config(self.current_env)
        
        # Mescla configurações (env sobrescreve base)
        merged_config = self._merge_configs(base_config, env_config)
        
        # Substitui variáveis de ambiente
        resolved_config = self._resolve_environment_variables(merged_config)
        
        # Cache resultado
        self._config_cache[cache_key] = resolved_config
        
        logging.info(f"Configuração carregada para ambiente: {self.current_env}")
        return resolved_config
    
    def _load_base_config(self) -> Dict[str, Any]:
        """Carrega configuração base."""
        base_file = self.config_dir / "base.json"
        if base_file.exists():
            return self._load_json_file(base_file)
        return {}
    
    def _load_environment_config(self, environment: str) -> Dict[str, Any]:
        """
        Carrega configuração específica do ambiente.
        
        Args:
            environment: Nome do ambiente
            
        Returns:
            Configuração do ambiente
        """
        env_file = self.environments_dir / f"{environment}.json"
        if not env_file.exists():
            logging.warning(f"Arquivo de configuração não encontrado: {env_file}")
            return {}
        
        return self._load_json_file(env_file)
    
    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Carrega arquivo JSON com tratamento de erros.
        
        Args:
            file_path: Caminho do arquivo JSON
            
        Returns:
            Conteúdo do arquivo como dicionário
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Arquivo de configuração não encontrado: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar JSON em {file_path}: {e}")
            return {}
        except Exception as e:
            logging.error(f"Erro inesperado ao carregar {file_path}: {e}")
            return {}
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mescla configurações recursivamente.
        
        Args:
            base: Configuração base
            override: Configuração que sobrescreve
            
        Returns:
            Configuração mesclada
        """
        if not isinstance(base, dict) or not isinstance(override, dict):
            return override if override is not None else base
        
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _resolve_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve variáveis de ambiente na configuração.
        
        Suporta os formatos: ${VAR_NAME} e ${VAR_NAME:default_value}
        
        Args:
            config: Configuração com possíveis variáveis
            
        Returns:
            Configuração com variáveis resolvidas
        """
        if isinstance(config, dict):
            return {key: self._resolve_environment_variables(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._resolve_environment_variables(item) for item in config]
        elif isinstance(config, str):
            return self._substitute_env_vars(config)
        else:
            return config
    
    def _substitute_env_vars(self, text: str) -> str:
        """
        Substitui variáveis de ambiente em uma string.
        
        Args:
            text: Texto com possíveis variáveis ${VAR} ou ${VAR:default}
            
        Returns:
            Texto com variáveis substituídas
        """
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
        
        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            
            env_value = os.getenv(var_name)
            if env_value is not None:
                return env_value
            elif default_value:
                return default_value
            else:
                logging.warning(f"Variável de ambiente não encontrada: {var_name}")
                return match.group(0)  # Retorna a variável original
        
        return re.sub(pattern, replace_var, text)
    
    def get_environment(self) -> str:
        """Retorna o ambiente atual."""
        return self.current_env
    
    def is_development(self) -> bool:
        """Verifica se está em ambiente de desenvolvimento."""
        return self.current_env == "development"
    
    def is_production(self) -> bool:
        """Verifica se está em ambiente de produção."""
        return self.current_env == "production"
    
    def is_testing(self) -> bool:
        """Verifica se está em ambiente de testes."""
        return self.current_env == "testing"
    
    def get_database_config(self) -> Dict[str, Any]:
        """Obtém configuração específica do banco de dados."""
        config = self.get_config()
        return config.get("database", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Obtém configuração específica de logging."""
        config = self.get_config()
        return config.get("logging", {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """Obtém configuração específica da API."""
        config = self.get_config()
        return config.get("api", {})
    
    def get_recording_config(self) -> Dict[str, Any]:
        """Obtém configuração específica de gravação."""
        config = self.get_config()
        return config.get("recording", {})
    
    def set_environment(self, environment: str) -> None:
        """
        Define o ambiente manualmente (para testes).
        
        Args:
            environment: Nome do ambiente
        """
        if environment not in self.ENVIRONMENTS:
            raise ValueError(f"Ambiente inválido: {environment}. Válidos: {list(self.ENVIRONMENTS.keys())}")
        
        self.current_env = environment
        self._config_cache.clear()  # Limpa cache
        logging.info(f"Ambiente definido manualmente para: {environment}")


# Instância global para facilitar uso
_env_config: Optional[EnvironmentConfig] = None


def get_environment_config(config_dir: Optional[Union[str, Path]] = None) -> EnvironmentConfig:
    """
    Obtém instância singleton do gerenciador de configurações.
    
    Args:
        config_dir: Diretório de configurações (usado apenas na primeira chamada)
        
    Returns:
        Instância do EnvironmentConfig
    """
    global _env_config
    
    if _env_config is None:
        if config_dir is None:
            # Detecta diretório automaticamente
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent
            config_dir = project_root / "config"
        
        _env_config = EnvironmentConfig(config_dir)
    
    return _env_config


def get_config() -> Dict[str, Any]:
    """
    Shortcut para obter configuração do ambiente atual.
    
    Returns:
        Configuração completa
    """
    return get_environment_config().get_config()


def is_development() -> bool:
    """Verifica se está em ambiente de desenvolvimento."""
    return get_environment_config().is_development()


def is_production() -> bool:
    """Verifica se está em ambiente de produção."""
    return get_environment_config().is_production()


def is_testing() -> bool:
    """Verifica se está em ambiente de testes."""
    return get_environment_config().is_testing()
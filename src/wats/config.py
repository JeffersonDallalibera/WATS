# WATS_Project/wats_app/config.py (VERSÃO COMPLETA E CORRETA)

import json
import logging
import os
import sys
from typing import Any, Dict, Final

# Garanta que python-dotenv está instalado no venv: pip install python-dotenv
from dotenv import load_dotenv

# --- Lógica de Caminhos (Paths) ---


def get_base_dir() -> str:
    """
    Retorna o diretório base para o app, funcionando
    tanto em modo script quanto em executável (PyInstaller).
    """
    # Para executável (--onefile ou --onedir)
    if getattr(sys, "frozen", False):
        # Para PyInstaller --onedir: sys.executable aponta para WATS.exe
        # Assets estão em: WATS/_internal/assets/
        # Mas também podem estar na raiz: WATS/assets/
        exe_dir = os.path.dirname(sys.executable)

        # Primeiro tenta na raiz (WATS/assets/)
        if os.path.exists(os.path.join(exe_dir, "assets")):
            return exe_dir
        # Se não encontrar, tenta em _internal (WATS/_internal/)
        elif os.path.exists(os.path.join(exe_dir, "_internal", "assets")):
            return os.path.join(exe_dir, "_internal")
        else:
            # Fallback para a pasta do executável
            return exe_dir
    # Para script Python normal
    else:
        # __file__ -> src/wats/config.py
        # os.path.dirname(__file__) -> src/wats/
        # os.path.dirname(...) -> src/
        # os.path.dirname(...) -> WATS_Project/ (a raiz)
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Diretório raiz (WATS_Project/ ou pasta do .exe)
BASE_DIR: Final[str] = get_base_dir()

# Diretório de assets (WATS_Project/assets/ ou pasta_do_exe/assets/)
ASSETS_DIR: Final[str] = os.path.join(BASE_DIR, "assets")


def get_user_data_dir() -> str:
    """
    Retorna o diretório para dados do usuário (logs, settings json),
    sempre usando a pasta onde o WATS está executado (dist/WATS).
    """
    # Para executável PyInstaller, sempre usa a pasta do executável
    if getattr(sys, "frozen", False):
        # sys.executable aponta para WATS.exe na pasta dist/WATS/
        user_data_dir = os.path.dirname(sys.executable)
        logging.debug(f"Modo executável: usando pasta do executável para dados: {user_data_dir}")
    else:
        # Para desenvolvimento, usa BASE_DIR (pasta do projeto)
        user_data_dir = BASE_DIR
        logging.debug(f"Modo desenvolvimento: usando BASE_DIR para dados: {user_data_dir}")

    # Criar o diretório se não existir (ignora erro se já existir)
    try:
        os.makedirs(user_data_dir, exist_ok=True)
        logging.debug(f"Diretório de dados do usuário definido como: {user_data_dir}")
    except OSError as e:
        logging.error(
            f"Não foi possível criar o diretório de dados do usuário em {user_data_dir}: {e}"
        )
        # Fallback para o diretório atual em caso de erro
        user_data_dir = os.getcwd()
        logging.warning(
            f"Usando diretório atual como fallback para dados do usuário: {user_data_dir}"
        )

    return user_data_dir


# Diretório para dados do usuário (configurações, logs, gravações)
USER_DATA_DIR: Final[str] = get_user_data_dir()


# --- Constantes da Aplicação ---
FILTER_PLACEHOLDER: Final[str] = "🔍 Buscar conexão..."
# Usa USER_DATA_DIR para o log, garantindo que seja gravável
LOG_FILE: Final[str] = os.path.join(USER_DATA_DIR, "wats_app.log")


# --- Modo Demo (para teste sem banco) ---
def is_demo_mode() -> bool:
    """Verifica se o aplicativo deve rodar em modo demo (sem banco de dados)."""
    return os.getenv("WATS_DEMO_MODE", "false").lower() in ("true", "1", "yes")


# --- Função para expandir variáveis de sistema em caminhos ---
def expand_system_variables(path: str) -> str:
    """
    Expande variáveis de sistema em caminhos de arquivo.
    Suporta: {USERPROFILE}, {APPDATA}, {LOCALAPPDATA}, {HOME}, {DESKTOP}, {DOCUMENTS}, {VIDEOS}

    Exemplos:
        {USERPROFILE}/Videos/Wats -> C:/Users/username/Videos/Wats
        {APPDATA}/WATS -> C:/Users/username/AppData/Roaming/WATS
        {VIDEOS}/Gravacoes -> C:/Users/username/Videos/Gravacoes
    """
    if not path or not isinstance(path, str):
        return path

    # Mapeamento de variáveis especiais
    import os

    # Obtém caminhos do sistema
    user_profile = os.path.expanduser("~")

    variables = {
        "USERPROFILE": user_profile,
        "HOME": user_profile,
        "APPDATA": os.getenv("APPDATA", os.path.join(user_profile, "AppData", "Roaming")),
        "LOCALAPPDATA": os.getenv("LOCALAPPDATA", os.path.join(user_profile, "AppData", "Local")),
        "DOCUMENTS": os.path.join(user_profile, "Documents"),
        "DESKTOP": os.path.join(user_profile, "Desktop"),
        "VIDEOS": os.path.join(user_profile, "Videos"),
        "PICTURES": os.path.join(user_profile, "Pictures"),
        "DOWNLOADS": os.path.join(user_profile, "Downloads"),
        "TEMP": os.getenv("TEMP", os.path.join(user_profile, "AppData", "Local", "Temp")),
    }

    # Substitui as variáveis
    expanded_path = path
    for var_name, var_value in variables.items():
        expanded_path = expanded_path.replace(f"{{{var_name}}}", var_value)

    # Também expande variáveis de ambiente padrão do sistema
    expanded_path = os.path.expandvars(expanded_path)

    # Normaliza o caminho (converte separadores)
    expanded_path = os.path.normpath(expanded_path)

    return expanded_path


# --- Função para carregar config.json ---
def load_config_json() -> Dict[str, Any]:
    """Carrega configurações do config.json."""
    config_paths = []

    if getattr(sys, "frozen", False):
        # Executável: prioriza config.json na pasta do executável (dist/WATS)
        exe_dir = os.path.dirname(sys.executable)
        external_path = os.path.join(exe_dir, "config.json")
        config_paths.append(external_path)

        # Fallback: embedded no executável (sys._MEIPASS)
        embedded_path = os.path.join(sys._MEIPASS, "config.json")
        config_paths.append(embedded_path)
    else:
        # Script: primeiro tenta na pasta config/, depois na raiz do projeto
        config_dir_path = os.path.join(BASE_DIR, "config", "config.json")
        config_paths.append(config_dir_path)
        script_path = os.path.join(BASE_DIR, "config.json")
        config_paths.append(script_path)

    # Tenta carregar de cada localização até encontrar um arquivo válido
    for config_path in config_paths:
        if os.path.exists(config_path):
            logging.info(f"Carregando configurações JSON de: {config_path}")
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    logging.info(f"config.json carregado com sucesso de: {config_path}")
                    return config_data
            except json.JSONDecodeError as e:
                logging.error(f"Erro ao fazer parse do JSON em {config_path}: {e}")
                continue
            except Exception as e:
                logging.error(f"Erro ao carregar config.json de {config_path}: {e}")
                continue

    # Se chegou aqui, nenhum arquivo config.json foi encontrado ou carregado
    logging.warning(
        f"Arquivo config.json não encontrado em nenhuma das localizações: {config_paths}"
    )
    return {}


# --- Função para carregar .env ---
def load_environment_variables():
    """Procura e carrega o arquivo .env."""
    dotenv_paths = []

    if getattr(sys, "frozen", False):
        # Executável: prioriza .env na pasta do executável (dist/WATS)
        exe_dir = os.path.dirname(sys.executable)
        external_path = os.path.join(exe_dir, ".env")
        dotenv_paths.append(external_path)

        # Fallback: embedded no executável (sys._MEIPASS)
        embedded_path = os.path.join(sys._MEIPASS, ".env")
        dotenv_paths.append(embedded_path)
    else:
        # Script: primeiro tenta na pasta config/, depois na raiz do projeto
        config_dir_path = os.path.join(BASE_DIR, "config", ".env")
        dotenv_paths.append(config_dir_path)
        script_path = os.path.join(BASE_DIR, ".env")
        dotenv_paths.append(script_path)

    # Tenta carregar de cada localização até encontrar um arquivo válido
    for dotenv_path in dotenv_paths:
        if os.path.exists(dotenv_path):
            logging.info(f"Carregando variáveis de ambiente de: {dotenv_path}")
            try:
                # Carrega as variáveis do arquivo para o ambiente do processo
                loaded = load_dotenv(dotenv_path=dotenv_path, override=True)
                if loaded:
                    logging.info(f".env carregado com sucesso de: {dotenv_path}")
                    return True
                else:
                    logging.warning(f"load_dotenv retornou False para: {dotenv_path}")
            except Exception as e:
                logging.error(f"Erro ao carregar .env de {dotenv_path}: {e}")
                continue

    # Se chegou aqui, nenhum arquivo .env foi encontrado ou carregado
    logging.warning(f"Arquivo .env não encontrado em nenhuma das localizações: {dotenv_paths}")
    return False


# --- FIM ---


# --- Configuração de logging ---
def setup_logging():
    print("Configurando logging...")
    """Configura o logging para o console E para um arquivo no USER_DATA_DIR."""

    # Primeiro tenta carregar o nível de log do config.json
    config_data = load_config_json()
    config_log_level = config_data.get("application", {}).get("log_level", "INFO")

    # Variável de ambiente tem prioridade sobre config.json
    log_level_str = os.getenv("LOG_LEVEL", config_log_level).upper()
    log_level = getattr(logging, log_level_str, logging.INFO)  # Converte string para nível de log
    log_format = (
        "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s"  # Mostra arquivo:linha ao invés de root
    )

    print(
        f"Nível de logging definido: {log_level_str} (fonte: {'variável ambiente' if 'LOG_LEVEL' in os.environ else 'config.json'})"
    )

    # Remove handlers antigos para evitar logs duplicados
    # Usa root logger para garantir que todos os logs sejam afetados
    root_logger = logging.getLogger()
    # Limpa handlers existentes antes de adicionar novos
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Cria os handlers
    try:
        # FileHandler (sempre tenta criar/abrir o arquivo)
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
    except Exception as e:
        print(f"ERRO: Não foi possível criar FileHandler para {LOG_FILE}: {e}")
        file_handler = None  # Define como None se falhar

    # StreamHandler (console)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(log_format))

    # Adiciona os handlers que foram criados com sucesso
    handlers = [h for h in [file_handler, stream_handler] if h is not None]

    # Configura o logger raiz
    root_logger.setLevel(log_level)
    for handler in handlers:
        root_logger.addHandler(handler)

    if file_handler:
        logging.info(f"Logging configurado. Nível: {log_level_str}. Salvando em: {LOG_FILE}")
    else:
        logging.warning(
            f"Logging configurado apenas para console. Nível: {log_level_str}. Falha ao criar arquivo de log em {LOG_FILE}"
        )


# --- Classe Settings ---
class Settings:
    """Armazena as configurações da aplicação. Lê do config.json primeiro, depois do ambiente (.env)."""

    def __init__(self):
        # Carrega configurações do JSON primeiro
        self.config_data = load_config_json()
        
        # Carrega diferentes grupos de configurações
        self._load_database_settings()
        self._load_recording_settings()
        self._load_api_settings()
        
        # Log das configurações carregadas
        self._log_loaded_settings()

    def _get_config_value(self, json_path: list, env_key: str, default_value: str = None):
        """Obtém valor de configuração com fallback JSON -> ENV -> padrão."""
        # Tenta obter do JSON
        try:
            value = self.config_data
            for key in json_path:
                value = value[key]
            if value is not None and str(value).strip():
                return str(value)
        except (KeyError, TypeError):
            pass

        # Fallback para variável de ambiente
        env_value = os.getenv(env_key, default_value)
        return env_value

    def _get_int_config(self, json_path: list, env_key: str, default_value: int) -> int:
        """Obtém valor inteiro com tratamento de erro."""
        try:
            return int(self._get_config_value(json_path, env_key, str(default_value)))
        except (ValueError, TypeError):
            return default_value

    def _get_float_config(self, json_path: list, env_key: str, default_value: float) -> float:
        """Obtém valor float com tratamento de erro."""
        try:
            return float(self._get_config_value(json_path, env_key, str(default_value)))
        except (ValueError, TypeError):
            return default_value

    def _get_bool_config(self, json_path: list, env_key: str, default_value: bool) -> bool:
        """Obtém valor booleano."""
        value = self._get_config_value(json_path, env_key, str(default_value).lower())
        return str(value).lower() == "true"

    def _load_database_settings(self):
        """Carrega configurações do banco de dados."""
        self.DB_TYPE = self._get_config_value(["database", "type"], "DB_TYPE", "sqlserver").lower()
        self.DB_SERVER = self._get_config_value(["database", "server"], "DB_SERVER")
        self.DB_DATABASE = self._get_config_value(["database", "database"], "DB_DATABASE")
        self.DB_UID = self._get_config_value(["database", "username"], "DB_UID")
        self.DB_PWD = self._get_config_value(["database", "password"], "DB_PWD")
        self.DB_PORT = self._get_config_value(["database", "port"], "DB_PORT")

    def _load_recording_settings(self):
        """Carrega configurações de gravação de sessão."""
        # ⚠️ GRAVAÇÃO HABILITADA POR PADRÃO
        # Se a tag "enabled" NÃO existir no config.json → habilita automaticamente (True)
        # Se a tag "enabled" EXISTIR no config.json → respeita o valor configurado
        self.RECORDING_ENABLED = self._get_bool_config(["recording", "enabled"], "RECORDING_ENABLED", True)
        self.RECORDING_AUTO_START = self._get_bool_config(["recording", "auto_start"], "RECORDING_AUTO_START", True)
        
        # Modo de gravação
        self.RECORDING_MODE = self._get_config_value(["recording", "mode"], "RECORDING_MODE", "rdp_window").lower()
        
        # Diretório de gravação
        self._load_recording_directory()
        
        # Configurações numéricas
        self.RECORDING_FPS = self._get_int_config(["recording", "fps"], "RECORDING_FPS", 10)
        self.RECORDING_QUALITY = self._get_int_config(["recording", "quality"], "RECORDING_QUALITY", 23)
        self.RECORDING_RESOLUTION_SCALE = self._get_float_config(
            ["recording", "resolution_scale"], "RECORDING_RESOLUTION_SCALE", 1.0
        )
        
        # Limites de gravação
        self.RECORDING_MAX_FILE_SIZE_MB = self._get_int_config(
            ["recording", "max_file_size_mb"], "RECORDING_MAX_FILE_SIZE_MB", 100
        )
        self.RECORDING_MAX_DURATION_MINUTES = self._get_int_config(
            ["recording", "max_duration_minutes"], "RECORDING_MAX_DURATION_MINUTES", 30
        )
        self.RECORDING_MAX_TOTAL_SIZE_GB = self._get_float_config(
            ["recording", "max_total_size_gb"], "RECORDING_MAX_TOTAL_SIZE_GB", 10.0
        )
        self.RECORDING_MAX_FILE_AGE_DAYS = self._get_int_config(
            ["recording", "max_file_age_days"], "RECORDING_MAX_FILE_AGE_DAYS", 30
        )
        self.RECORDING_CLEANUP_INTERVAL_HOURS = self._get_int_config(
            ["recording", "cleanup_interval_hours"], "RECORDING_CLEANUP_INTERVAL_HOURS", 6
        )

    def _load_recording_directory(self):
        """Carrega e expande o diretório de gravação."""
        default_recording_dir = os.path.join(get_user_data_dir(), "recordings")
        recording_output_dir = self._get_config_value(
            ["recording", "output_dir"], "RECORDING_OUTPUT_DIR", default_recording_dir
        )
        
        # Expande variáveis de sistema no caminho
        if recording_output_dir:
            recording_output_dir = expand_system_variables(recording_output_dir)
        
        self.RECORDING_OUTPUT_DIR = recording_output_dir if recording_output_dir else default_recording_dir

    def _load_api_settings(self):
        """Carrega configurações da API de upload."""
        # Configurações básicas
        self.API_ENABLED = self._get_bool_config(["api", "enabled"], "API_ENABLED", False)
        self.API_BASE_URL = self._get_config_value(["api", "base_url"], "API_BASE_URL", "")
        self.API_TOKEN = self._get_config_value(["api", "api_token"], "API_TOKEN", "")
        self.API_AUTO_UPLOAD = self._get_bool_config(["api", "auto_upload"], "API_AUTO_UPLOAD", False)
        
        # Configurações de timeout e retry
        self.API_UPLOAD_TIMEOUT = self._get_int_config(["api", "upload_timeout"], "API_UPLOAD_TIMEOUT", 60)
        self.API_MAX_RETRIES = self._get_int_config(["api", "max_retries"], "API_MAX_RETRIES", 3)
        self.API_MAX_CONCURRENT_UPLOADS = self._get_int_config(
            ["api", "max_concurrent_uploads"], "API_MAX_CONCURRENT_UPLOADS", 2
        )
        
        # Configurações de limpeza
        self.API_DELETE_AFTER_UPLOAD = self._get_bool_config(
            ["api", "delete_after_upload"], "API_DELETE_AFTER_UPLOAD", False
        )
        self.API_UPLOAD_OLDER_RECORDINGS = self._get_bool_config(
            ["api", "upload_older_recordings"], "API_UPLOAD_OLDER_RECORDINGS", True
        )
        self.API_MAX_FILE_AGE_DAYS = self._get_int_config(
            ["api", "max_file_age_days"], "API_MAX_FILE_AGE_DAYS", 30
        )

    def _log_loaded_settings(self):
        """Registra as configurações carregadas (com senhas mascaradas)."""
        pwd_status = "***" if self.DB_PWD else "None"
        api_token_status = "***" if self.API_TOKEN else "None"
        
        logging.debug(
            f"Settings lidas: DB_TYPE={self.DB_TYPE}, DB_SERVER={self.DB_SERVER}, "
            f"DB_DATABASE={self.DB_DATABASE}, DB_UID={self.DB_UID}, DB_PWD={pwd_status}, DB_PORT={self.DB_PORT}"
        )
        logging.debug(
            f"Recording settings: ENABLED={self.RECORDING_ENABLED}, AUTO_START={self.RECORDING_AUTO_START}, "
            f"FPS={self.RECORDING_FPS}, QUALITY={self.RECORDING_QUALITY}, SCALE={self.RECORDING_RESOLUTION_SCALE}"
        )
        logging.debug(
            f"Recording limits: FILE_SIZE={self.RECORDING_MAX_FILE_SIZE_MB}MB, "
            f"DURATION={self.RECORDING_MAX_DURATION_MINUTES}min, TOTAL_SIZE={self.RECORDING_MAX_TOTAL_SIZE_GB}GB"
        )
        logging.debug(
            f"API settings: ENABLED={self.API_ENABLED}, AUTO_UPLOAD={self.API_AUTO_UPLOAD}, "
            f"BASE_URL={self.API_BASE_URL}, TOKEN={api_token_status}"
        )

    def has_db_config(self) -> bool:
        """Verifica se as configurações essenciais do banco estão presentes E não são strings vazias."""
        required_vars = [self.DB_TYPE, self.DB_SERVER, self.DB_DATABASE, self.DB_UID, self.DB_PWD]
        has_config = all(
            var is not None and var.strip() != "" for var in required_vars
        )  # Verifica None E string vazia
        if not has_config:
            logging.error(
                "Validação has_db_config falhou. Variáveis essenciais do DB ausentes ou vazias."
            )
            # Loga quais variáveis estão faltando ou vazias
            details = {
                "DB_TYPE": bool(self.DB_TYPE and self.DB_TYPE.strip()),
                "DB_SERVER": bool(self.DB_SERVER and self.DB_SERVER.strip()),
                "DB_DATABASE": bool(self.DB_DATABASE and self.DB_DATABASE.strip()),
                "DB_UID": bool(self.DB_UID and self.DB_UID.strip()),
                "DB_PWD": bool(
                    self.DB_PWD and self.DB_PWD.strip()
                ),  # Verifica se PWD está presente, mesmo que seja string vazia (alguns bancos permitem)
            }
            logging.error(f"Status das variáveis DB: {details}")
        return has_config

    def get_recording_config(self) -> dict:
        """Returns recording configuration as a dictionary."""
        return {
            "enabled": self.RECORDING_ENABLED,
            "auto_start": self.RECORDING_AUTO_START,
            "mode": self.RECORDING_MODE,
            "output_dir": self.RECORDING_OUTPUT_DIR,
            "fps": self.RECORDING_FPS,
            "quality": self.RECORDING_QUALITY,
            "resolution_scale": self.RECORDING_RESOLUTION_SCALE,
            "max_file_size_mb": self.RECORDING_MAX_FILE_SIZE_MB,
            "max_duration_minutes": self.RECORDING_MAX_DURATION_MINUTES,
            "max_total_size_gb": self.RECORDING_MAX_TOTAL_SIZE_GB,
            "max_file_age_days": self.RECORDING_MAX_FILE_AGE_DAYS,
            "cleanup_interval_hours": self.RECORDING_CLEANUP_INTERVAL_HOURS,
        }

    def validate_recording_config(self) -> bool:
        """Validates recording configuration settings."""
        try:
            # Check if recording is enabled
            if not self.RECORDING_ENABLED:
                return True  # Valid to have recording disabled

            # Validate numeric ranges
            if not (1 <= self.RECORDING_FPS <= 60):
                logging.error(f"Invalid RECORDING_FPS: {self.RECORDING_FPS} (must be 1-60)")
                return False

            if not (0 <= self.RECORDING_QUALITY <= 51):
                logging.error(f"Invalid RECORDING_QUALITY: {self.RECORDING_QUALITY} (must be 0-51)")
                return False

            if not (0.1 <= self.RECORDING_RESOLUTION_SCALE <= 2.0):
                logging.error(
                    f"Invalid RECORDING_RESOLUTION_SCALE: {self.RECORDING_RESOLUTION_SCALE} (must be 0.1-2.0)"
                )
                return False

            if self.RECORDING_MAX_FILE_SIZE_MB < 1:
                logging.error(
                    f"Invalid RECORDING_MAX_FILE_SIZE_MB: {self.RECORDING_MAX_FILE_SIZE_MB} (must be >= 1)"
                )
                return False

            if self.RECORDING_MAX_DURATION_MINUTES < 1:
                logging.error(
                    f"Invalid RECORDING_MAX_DURATION_MINUTES: {self.RECORDING_MAX_DURATION_MINUTES} (must be >= 1)"
                )
                return False

            # Try to create output directory with improved logging
            try:
                if not os.path.exists(self.RECORDING_OUTPUT_DIR):
                    logging.info(
                        f"Creating recording output directory: {self.RECORDING_OUTPUT_DIR}"
                    )
                    os.makedirs(self.RECORDING_OUTPUT_DIR, exist_ok=True)
                    logging.info(
                        f"Recording directory created successfully: {self.RECORDING_OUTPUT_DIR}"
                    )
                else:
                    logging.debug(
                        f"Recording output directory already exists: {self.RECORDING_OUTPUT_DIR}"
                    )

                # Verify directory is writable
                if not os.access(self.RECORDING_OUTPUT_DIR, os.W_OK):
                    logging.error(
                        f"Recording output directory is not writable: {self.RECORDING_OUTPUT_DIR}"
                    )
                    return False

            except Exception as e:
                logging.error(
                    f"Failed to create recording output directory '{self.RECORDING_OUTPUT_DIR}': {e}"
                )
                return False

            logging.info("Recording configuration validation passed")
            return True

        except Exception as e:
            logging.error(f"Error validating recording config: {e}")
            return False

    def get_api_config(self) -> dict:
        """Returns API configuration as a dictionary."""
        return {
            "enabled": self.API_ENABLED,
            "base_url": self.API_BASE_URL,
            "api_token": self.API_TOKEN,
            "auto_upload": self.API_AUTO_UPLOAD,
            "upload_timeout": self.API_UPLOAD_TIMEOUT,
            "max_retries": self.API_MAX_RETRIES,
            "max_concurrent_uploads": self.API_MAX_CONCURRENT_UPLOADS,
            "delete_after_upload": self.API_DELETE_AFTER_UPLOAD,
            "upload_older_recordings": self.API_UPLOAD_OLDER_RECORDINGS,
            "max_file_age_days": self.API_MAX_FILE_AGE_DAYS,
        }

    def validate_api_config(self) -> bool:
        """Validates API configuration settings."""
        try:
            # Check if API is enabled
            if not self.API_ENABLED:
                return True  # Valid to have API disabled

            # Validate required fields
            if not self.API_BASE_URL or not self.API_BASE_URL.strip():
                logging.error("API_BASE_URL is required when API is enabled")
                return False

            if not self.API_TOKEN or not self.API_TOKEN.strip():
                logging.error("API_TOKEN is required when API is enabled")
                return False

            # Validate URL format
            if not self.API_BASE_URL.startswith(("http://", "https://")):
                logging.error("API_BASE_URL must start with http:// or https://")
                return False

            # Validate numeric ranges
            if self.API_UPLOAD_TIMEOUT < 10:
                logging.warning(f"API_UPLOAD_TIMEOUT is very low: {self.API_UPLOAD_TIMEOUT}s")

            if self.API_MAX_RETRIES < 0:
                logging.error(f"Invalid API_MAX_RETRIES: {self.API_MAX_RETRIES} (must be >= 0)")
                return False

            if self.API_MAX_CONCURRENT_UPLOADS < 1:
                logging.error(
                    f"Invalid API_MAX_CONCURRENT_UPLOADS: {self.API_MAX_CONCURRENT_UPLOADS} (must be >= 1)"
                )
                return False
            elif self.API_MAX_CONCURRENT_UPLOADS > 5:
                logging.warning(
                    f"High API_MAX_CONCURRENT_UPLOADS: {self.API_MAX_CONCURRENT_UPLOADS} may impact performance"
                )

            if self.API_MAX_FILE_AGE_DAYS < 1:
                logging.error(
                    f"Invalid API_MAX_FILE_AGE_DAYS: {self.API_MAX_FILE_AGE_DAYS} (must be >= 1)"
                )
                return False

            logging.info("API configuration validation passed")
            return True

        except Exception as e:
            logging.error(f"Error validating API config: {e}")
            return False


# --- Instância settings NÃO é criada aqui ---
# Será criada no run.py após load_environment_variables() ser chamada.


# --- Função utilitária para acesso à configuração ---
def get_config() -> Dict[str, Any]:
    """
    Função utilitária para obter configuração combinada.
    Retorna um dicionário com configurações do config.json.
    """
    try:
        # Primeiro tenta obter da configuração do ambiente
        try:
            from .core.environment import get_config as get_env_config

            return get_env_config()
        except ImportError:
            # Se não conseguir importar o módulo de ambiente, usa config JSON simples
            pass
        except Exception as e:
            logging.warning(f"Erro ao obter configuração do ambiente: {e}")

        # Fallback para config.json simples
        config_data = load_config_json()
        if not config_data:
            # Se não encontrou config.json, retorna configuração padrão
            config_data = {
                "recording": {
                    "enabled": True,
                    "mode": "rdp_window",
                    "fps": 30,
                    "quality": 75,
                    "output_dir": os.path.join(USER_DATA_DIR, "recordings"),
                    "compress_enabled": True,
                    "compress_crf": 28,
                    "auto_start": True,
                },
                "app": {"log_level": "INFO", "demo_mode": False},
            }
            logging.info("Usando configuração padrão")

        return config_data

    except Exception as e:
        logging.error(f"Erro crítico ao obter configuração: {e}")
        # Retorna configuração mínima em caso de erro
        return {
            "recording": {
                "enabled": False,
                "mode": "full_screen",
                "fps": 30,
                "quality": 75,
                "output_dir": os.path.join(USER_DATA_DIR, "recordings"),
                "compress_enabled": False,
                "compress_crf": 28,
                "auto_start": False,
            }
        }


def get_app_config() -> Dict[str, Any]:
    """
    Retorna as configurações completas do config.json.

    Returns:
        Dict com todas as configurações com valores padrão.
    """
    try:
        config_data = load_config_json()

        # Configurações da aplicação
        app_config = config_data.get("application", {})
        app_defaults = {
            "window_title": "WATS - Sistema de Gravação RDP",
            "window_geometry": "1200x800",
            "window_resizable": True,
            "theme": "Dark",
            "log_level": "INFO",
            "monitor": 1,
            "minimize_to_tray": True,
            "start_minimized": False,
            "check_updates": True,
            "language": "pt-BR",
            "auto_consent": False,
        }
        app_result = app_defaults.copy()
        app_result.update(app_config)

        # Configurações do RDP
        rdp_config = config_data.get("rdp", {})
        rdp_defaults = {
            "maximize_window": False,
            "window_mode": "normal",
            "allow_window_override": True,
            "fullscreen": False,
            "default_width": 1024,
            "default_height": 768,
        }
        rdp_result = rdp_defaults.copy()
        rdp_result.update(rdp_config)

        # Validação do monitor
        monitor = app_result.get("monitor", 1)
        if not isinstance(monitor, int) or monitor < 1:
            logging.warning(f"Valor inválido para monitor: {monitor}. Usando monitor 1.")
            app_result["monitor"] = 1

        # Retorna configurações completas
        full_config = config_data.copy()
        full_config["application"] = app_result
        full_config["rdp"] = rdp_result

        # Para compatibilidade, adiciona as configurações de aplicação no nível raiz
        full_config.update(app_result)

        logging.info(
            f"Configurações da aplicação carregadas: título='{app_result['window_title']}', monitor={app_result['monitor']}"
        )
        return full_config

    except Exception as e:
        logging.error(f"Erro ao carregar configurações da aplicação: {e}")
        # Retorna configuração padrão em caso de erro
        return {
            "window_title": "WATS - Sistema de Gravação RDP",
            "window_geometry": "1200x800",
            "window_resizable": True,
            "theme": "Dark",
            "log_level": "INFO",
            "monitor": 1,
            "minimize_to_tray": True,
            "start_minimized": False,
            "check_updates": True,
            "language": "pt-BR",
            "auto_consent": False,
        }

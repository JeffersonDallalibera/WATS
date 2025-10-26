# WATS_Project/wats_app/config.py (VERSÃO COMPLETA E CORRETA)

import os
import sys
import logging
from typing import Final
# Garanta que python-dotenv está instalado no venv: pip install python-dotenv
from dotenv import load_dotenv

# --- Lógica de Caminhos (Paths) ---

def get_base_dir() -> str:
    """
    Retorna o diretório base para o app, funcionando
    tanto em modo script quanto em executável (PyInstaller).
    """
    # Para executável (--onefile ou --onedir)
    if getattr(sys, 'frozen', False):
        # sys.executable é o caminho para o .exe
        return os.path.dirname(sys.executable)
    # Para script Python normal
    else:
        # __file__ -> wats_app/config.py
        # os.path.dirname(__file__) -> wats_app/
        # os.path.dirname(...) -> WATS_Project/ (a raiz)
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Diretório raiz (WATS_Project/ ou pasta do .exe)
BASE_DIR: Final[str] = get_base_dir()

# Diretório de assets (WATS_Project/assets/ ou pasta_do_exe/assets/)
ASSETS_DIR: Final[str] = os.path.join(BASE_DIR, 'assets')

def get_user_data_dir() -> str:
    """
    Retorna um diretório gravável para dados do usuário (logs, settings json),
    funcionando tanto em modo script quanto em executável.
    """
    # Preferência: Pasta WATS dentro do AppData do usuário para executável
    if getattr(sys, 'frozen', False):
        try:
            # Tenta usar %APPDATA%\WATS (Windows)
            app_data = os.getenv('APPDATA')
            if app_data:
                user_data_dir = os.path.join(app_data, "WATS")
            else: # Fallback para pasta do usuário se APPDATA não estiver definida
                app_data = os.path.expanduser("~")
                user_data_dir = os.path.join(app_data, ".WATS") # Usa .WATS para ser oculta
        except Exception:
             # Fallback final: Usa a pasta do executável (pode ter problemas de permissão)
             user_data_dir = BASE_DIR
    # Script: usar o diretório raiz do projeto (BASE_DIR)
    else:
        user_data_dir = BASE_DIR

    # Criar o diretório se não existir (ignora erro se já existir)
    try:
        os.makedirs(user_data_dir, exist_ok=True)
        logging.debug(f"Diretório de dados do usuário definido como: {user_data_dir}")
    except OSError as e:
        logging.error(f"Não foi possível criar o diretório de dados do usuário em {user_data_dir}: {e}")
        # Fallback para o diretório atual em caso de erro
        user_data_dir = os.getcwd()
        logging.warning(f"Usando diretório atual como fallback para dados do usuário: {user_data_dir}")

    return user_data_dir

# Diretório para dados do usuário (configurações, logs, gravações)
USER_DATA_DIR: Final[str] = get_user_data_dir()


# --- Constantes da Aplicação ---
FILTER_PLACEHOLDER: Final[str] = "🔍 Buscar conexão..."
# Usa USER_DATA_DIR para o log, garantindo que seja gravável
LOG_FILE: Final[str] = os.path.join(USER_DATA_DIR, 'wats_app.log')


# --- Função para carregar .env ---
def load_environment_variables():
    """Procura e carrega o arquivo .env."""
    dotenv_paths = []
    
    if getattr(sys, 'frozen', False):
        # Executável: procura em duas localizações
        # 1. Embedded no executável (sys._MEIPASS)
        embedded_path = os.path.join(sys._MEIPASS, '.env')
        dotenv_paths.append(embedded_path)
        
        # 2. Ao lado do executável (BASE_DIR)
        external_path = os.path.join(BASE_DIR, '.env')
        dotenv_paths.append(external_path)
    else:
        # Script: apenas na raiz do projeto
        script_path = os.path.join(BASE_DIR, '.env')
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
    """Configura o logging para o console E para um arquivo no USER_DATA_DIR."""
    log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO) # Converte string para nível de log
    log_format = '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s' # Adiciona número da linha

    # Remove handlers antigos para evitar logs duplicados
    # Usa root logger para garantir que todos os logs sejam afetados
    root_logger = logging.getLogger()
    # Limpa handlers existentes antes de adicionar novos
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Cria os handlers
    try:
        # FileHandler (sempre tenta criar/abrir o arquivo)
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
    except Exception as e:
        print(f"ERRO: Não foi possível criar FileHandler para {LOG_FILE}: {e}")
        file_handler = None # Define como None se falhar

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
        logging.warning(f"Logging configurado apenas para console. Nível: {log_level_str}. Falha ao criar arquivo de log em {LOG_FILE}")

# --- Classe Settings ---
class Settings:
    """Armazena as configurações da aplicação. Lê do ambiente APÓS load_environment_variables ser chamado."""
    def __init__(self):
        # Database settings
        self.DB_TYPE = os.getenv('DB_TYPE', 'sqlserver').lower()
        self.DB_SERVER = os.getenv('DB_SERVER')
        self.DB_DATABASE = os.getenv('DB_DATABASE')
        self.DB_UID = os.getenv('DB_UID')
        self.DB_PWD = os.getenv('DB_PWD')
        self.DB_PORT = os.getenv('DB_PORT')

        # Session Recording settings
        self.RECORDING_ENABLED = os.getenv('RECORDING_ENABLED', 'false').lower() == 'true'
        self.RECORDING_AUTO_START = os.getenv('RECORDING_AUTO_START', 'true').lower() == 'true'
        self.RECORDING_MODE = os.getenv('RECORDING_MODE', 'full_screen').lower()  # full_screen, rdp_window, active_window
        self.RECORDING_OUTPUT_DIR = os.getenv('RECORDING_OUTPUT_DIR', 
                                            os.path.join(get_user_data_dir(), 'recordings'))
        self.RECORDING_FPS = int(os.getenv('RECORDING_FPS', '10'))
        self.RECORDING_QUALITY = int(os.getenv('RECORDING_QUALITY', '23'))  # H.264 CRF value
        self.RECORDING_RESOLUTION_SCALE = float(os.getenv('RECORDING_RESOLUTION_SCALE', '1.0'))
        self.RECORDING_MAX_FILE_SIZE_MB = int(os.getenv('RECORDING_MAX_FILE_SIZE_MB', '100'))
        self.RECORDING_MAX_DURATION_MINUTES = int(os.getenv('RECORDING_MAX_DURATION_MINUTES', '30'))
        self.RECORDING_MAX_TOTAL_SIZE_GB = float(os.getenv('RECORDING_MAX_TOTAL_SIZE_GB', '10.0'))
        self.RECORDING_MAX_FILE_AGE_DAYS = int(os.getenv('RECORDING_MAX_FILE_AGE_DAYS', '30'))
        self.RECORDING_CLEANUP_INTERVAL_HOURS = int(os.getenv('RECORDING_CLEANUP_INTERVAL_HOURS', '6'))

        # Log para verificar o que foi carregado (SENHA MASCARADA)
        pwd_status = '***' if self.DB_PWD else 'None'
        logging.debug(f"Settings lidas: DB_TYPE={self.DB_TYPE}, DB_SERVER={self.DB_SERVER}, DB_DATABASE={self.DB_DATABASE}, DB_UID={self.DB_UID}, DB_PWD={pwd_status}, DB_PORT={self.DB_PORT}")
        logging.debug(f"Recording settings: ENABLED={self.RECORDING_ENABLED}, AUTO_START={self.RECORDING_AUTO_START}, "
                     f"FPS={self.RECORDING_FPS}, QUALITY={self.RECORDING_QUALITY}, SCALE={self.RECORDING_RESOLUTION_SCALE}")
        logging.debug(f"Recording limits: FILE_SIZE={self.RECORDING_MAX_FILE_SIZE_MB}MB, "
                     f"DURATION={self.RECORDING_MAX_DURATION_MINUTES}min, TOTAL_SIZE={self.RECORDING_MAX_TOTAL_SIZE_GB}GB")

    def has_db_config(self) -> bool:
        """Verifica se as configurações essenciais do banco estão presentes E não são strings vazias."""
        required_vars = [self.DB_TYPE, self.DB_SERVER, self.DB_DATABASE, self.DB_UID, self.DB_PWD]
        has_config = all(var is not None and var.strip() != '' for var in required_vars) # Verifica None E string vazia
        if not has_config:
            logging.error("Validação has_db_config falhou. Variáveis essenciais do DB ausentes ou vazias.")
            # Loga quais variáveis estão faltando ou vazias
            details = {
                "DB_TYPE": bool(self.DB_TYPE and self.DB_TYPE.strip()),
                "DB_SERVER": bool(self.DB_SERVER and self.DB_SERVER.strip()),
                "DB_DATABASE": bool(self.DB_DATABASE and self.DB_DATABASE.strip()),
                "DB_UID": bool(self.DB_UID and self.DB_UID.strip()),
                "DB_PWD": bool(self.DB_PWD and self.DB_PWD.strip()) # Verifica se PWD está presente, mesmo que seja string vazia (alguns bancos permitem)
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
            "cleanup_interval_hours": self.RECORDING_CLEANUP_INTERVAL_HOURS
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
                logging.error(f"Invalid RECORDING_RESOLUTION_SCALE: {self.RECORDING_RESOLUTION_SCALE} (must be 0.1-2.0)")
                return False
                
            if self.RECORDING_MAX_FILE_SIZE_MB < 1:
                logging.error(f"Invalid RECORDING_MAX_FILE_SIZE_MB: {self.RECORDING_MAX_FILE_SIZE_MB} (must be >= 1)")
                return False
                
            if self.RECORDING_MAX_DURATION_MINUTES < 1:
                logging.error(f"Invalid RECORDING_MAX_DURATION_MINUTES: {self.RECORDING_MAX_DURATION_MINUTES} (must be >= 1)")
                return False
                
            # Try to create output directory
            os.makedirs(self.RECORDING_OUTPUT_DIR, exist_ok=True)
            
            logging.info("Recording configuration validation passed")
            return True
            
        except Exception as e:
            logging.error(f"Error validating recording config: {e}")
            return False

# --- Instância settings NÃO é criada aqui ---
# Será criada no run.py após load_environment_variables() ser chamada.
"""
Compatibilidade multiplataforma para WATS
Lida com dependências específicas do Windows
"""

import os
import sys
import platform

# Detecta o sistema operacional
IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')
IS_MACOS = sys.platform.startswith('darwin')

# Importações condicionais para Windows
if IS_WINDOWS:
    try:
        import win32api
        import win32con
        import win32gui
        import win32process
        HAS_WIN32 = True
    except ImportError:
        HAS_WIN32 = False
        print("Aviso: Dependências win32 não encontradas")
else:
    HAS_WIN32 = False
    # Cria mocks para as funções do Windows em outros sistemas
    class Win32Mock:
        def __getattr__(self, name):
            def mock_function(*args, **kwargs):
                raise NotImplementedError(f"Função {name} não disponível em {platform.system()}")
            return mock_function
    
    win32api = Win32Mock()
    win32con = Win32Mock()
    win32gui = Win32Mock()
    win32process = Win32Mock()

def get_platform_info():
    """Retorna informações sobre a plataforma atual"""
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'is_windows': IS_WINDOWS,
        'is_linux': IS_LINUX,
        'is_macos': IS_MACOS,
        'has_win32': HAS_WIN32
    }

def is_platform_supported():
    """Verifica se a plataforma atual é suportada"""
    return IS_WINDOWS or IS_LINUX

def get_platform_specific_paths():
    """Retorna caminhos específicos da plataforma"""
    if IS_WINDOWS:
        return {
            'config_dir': os.path.expanduser('~\\AppData\\Roaming\\WATS'),
            'log_dir': os.path.expanduser('~\\AppData\\Roaming\\WATS\\logs'),
            'temp_dir': os.environ.get('TEMP', 'C:\\temp')
        }
    else:  # Linux/Unix
        return {
            'config_dir': os.path.expanduser('~/.config/wats'),
            'log_dir': os.path.expanduser('~/.config/wats/logs'),
            'temp_dir': '/tmp'
        }

def ensure_platform_dirs():
    """Cria diretórios necessários para a plataforma"""
    import os
    paths = get_platform_specific_paths()
    
    for path in paths.values():
        os.makedirs(path, exist_ok=True)
    
    return paths
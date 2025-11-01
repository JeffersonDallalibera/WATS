"""
Módulo de conexão RDP multiplataforma para WATS
Substitui o rdp.exe específico do Windows por soluções nativas de cada SO
Inclui suporte a bibliotecas Python RDP quando disponíveis
"""

import logging
import os
import platform
import shutil
import subprocess
import threading
import time
from typing import Dict, List, Tuple

from .freerdp_wrapper import freerdp_wrapper
from .platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS

# Importações condicionais para bibliotecas RDP Python
HAS_PYFREERDP = False
HAS_RDPY = False

try:
    import pyfreerdp

    HAS_PYFREERDP = True
except ImportError:
    pass

# rdpy não é usado atualmente, mantido para possível uso futuro
# try:
#     import rdpy
#     HAS_RDPY = True
# except ImportError:
#     pass
HAS_RDPY = False


class RDPConnector:
    """Classe para gerenciar conexões RDP multiplataforma"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.platform = platform.system().lower()
        self.preferred_method = self._determine_preferred_method()

    def _determine_preferred_method(self) -> str:
        """Determina o método preferido de conexão RDP"""
        # Prioriza wrapper FreeRDP se disponível
        if freerdp_wrapper.is_available():
            return "freerdp_wrapper"
        elif HAS_PYFREERDP:
            return "pyfreerdp"
        elif HAS_RDPY:
            return "rdpy"
        elif IS_WINDOWS:
            # Verifica se tem rdp.exe customizado
            assets_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets")
            rdp_exe_path = os.path.join(assets_dir, "rdp.exe")
            if os.path.exists(rdp_exe_path):
                return "custom_rdp"
            else:
                return "mstsc"
        elif IS_LINUX:
            if shutil.which("xfreerdp"):
                return "xfreerdp"
            elif shutil.which("rdesktop"):
                return "rdesktop"
            elif shutil.which("remmina"):
                return "remmina"
            else:
                return "none"
        else:
            return "none"

    def is_rdp_available(self) -> Tuple[bool, str]:
        """
        Verifica se há um cliente RDP disponível no sistema
        Returns: (disponível, mensagem)
        """
        method = self.preferred_method

        if method == "freerdp_wrapper":
            return True, "FreeRDP Wrapper Python disponível"
        elif method == "pyfreerdp":
            return True, "PyFreeRDP biblioteca Python disponível"
        elif method == "rdpy":
            return True, "RDPY biblioteca Python disponível"
        elif method == "custom_rdp":
            return True, "RDP.exe customizado encontrado"
        elif method == "mstsc":
            return True, "MSTSC nativo do Windows disponível"
        elif method in ["xfreerdp", "rdesktop", "remmina"]:
            return True, f"{method} encontrado no Linux"
        else:
            if IS_WINDOWS:
                return self._check_windows_rdp()
            elif IS_LINUX:
                return self._check_linux_rdp()
            elif IS_MACOS:
                return self._check_macos_rdp()
            else:
                return False, f"Plataforma {self.platform} não suportada"

    def _check_windows_rdp(self) -> Tuple[bool, str]:
        """Verifica RDP no Windows"""
        # Primeiro tenta o rdp.exe customizado
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets")
        rdp_exe_path = os.path.join(assets_dir, "rdp.exe")

        if os.path.exists(rdp_exe_path):
            return True, f"RDP customizado encontrado: {rdp_exe_path}"

        # Fallback para MSTSC nativo
        mstsc_path = shutil.which("mstsc")
        if mstsc_path:
            return True, f"MSTSC nativo encontrado: {mstsc_path}"

        return False, "Nenhum cliente RDP encontrado no Windows"

    def _check_linux_rdp(self) -> Tuple[bool, str]:
        """Verifica clientes RDP no Linux"""
        clients = [
            ("rdesktop", "Rdesktop"),
            ("xfreerdp", "FreeRDP"),
            ("remmina", "Remmina"),
            ("vinagre", "Vinagre"),
        ]

        available_clients = []
        for cmd, name in clients:
            if shutil.which(cmd):
                available_clients.append((cmd, name))

        if available_clients:
            client_names = [name for _, name in available_clients]
            return True, f"Clientes RDP encontrados: {', '.join(client_names)}"

        return (
            False,
            "Nenhum cliente RDP encontrado. Instale: rdesktop, xfreerdp, remmina ou vinagre",
        )

    def _check_macos_rdp(self) -> Tuple[bool, str]:
        """Verifica clientes RDP no macOS"""
        # Microsoft Remote Desktop app
        ms_rdp_path = "/Applications/Microsoft Remote Desktop 10.app"
        if os.path.exists(ms_rdp_path):
            return True, "Microsoft Remote Desktop encontrado"

        # FreeRDP via Homebrew
        if shutil.which("xfreerdp"):
            return True, "FreeRDP encontrado"

        return False, "Instale Microsoft Remote Desktop da App Store ou FreeRDP via Homebrew"

    def connect(self, connection_data: Dict[str, str]) -> bool:
        """
        Estabelece conexão RDP multiplataforma
        Args:
            connection_data: Dicionário com dados da conexão (ip, user, pwd, title, etc.)
        Returns:
            True se conexão iniciada com sucesso
        """
        try:
            method = self.preferred_method
            self.logger.info(f"Conectando RDP usando método: {method}")

            if method == "freerdp_wrapper":
                return self._connect_freerdp_wrapper(connection_data)
            elif method == "pyfreerdp":
                return self._connect_pyfreerdp(connection_data)
            elif method == "rdpy":
                return self._connect_rdpy(connection_data)
            elif method == "custom_rdp":
                return self._connect_windows_custom(connection_data)
            elif method == "mstsc":
                return self._connect_windows_mstsc(connection_data)
            elif method == "xfreerdp":
                return self._connect_linux_freerdp(connection_data)
            elif method == "rdesktop":
                return self._connect_linux_rdesktop(connection_data)
            elif method == "remmina":
                return self._connect_linux_remmina(connection_data)
            else:
                # Fallback para detecção automática
                if IS_WINDOWS:
                    return self._connect_windows(connection_data)
                elif IS_LINUX:
                    return self._connect_linux(connection_data)
                elif IS_MACOS:
                    return self._connect_macos(connection_data)
                else:
                    self.logger.error(f"Plataforma {self.platform} não suportada")
                    return False

        except Exception as e:
            self.logger.exception(f"Erro ao conectar RDP: {e}")
            return False

    def _connect_freerdp_wrapper(self, data: Dict[str, str]) -> bool:
        """Conecta usando o wrapper FreeRDP Python"""
        try:
            self.logger.info("Conectando via FreeRDP Wrapper...")

            # Gera ID único para a sessão
            session_id = f"wats_rdp_{data.get('ip', 'unknown')}_{int(time.time())}"

            # Conecta via wrapper
            success = freerdp_wrapper.connect(
                connection_data=data, session_id=session_id, background=True
            )

            if success:
                self.logger.info(f"Conexão FreeRDP Wrapper iniciada: {session_id}")
                return True
            else:
                self.logger.error("Falha ao iniciar conexão FreeRDP Wrapper")
                return False

        except Exception as e:
            self.logger.error(f"Erro ao usar FreeRDP Wrapper: {e}")
            return False

    def _connect_pyfreerdp(self, data: Dict[str, str]) -> bool:
        """Conecta usando a biblioteca PyFreeRDP"""
        try:
            self.logger.info("Conectando via PyFreeRDP...")

            # Configurações da conexão
            config = {
                "hostname": data["ip"],
                "username": data["user"],
                "password": data["pwd"],
                "port": int(data.get("port", 3389)),
                "fullscreen": True,
                "title": data.get("title", data["ip"]),
                "cert_ignore": True,
                "clipboard": True,
            }

            # Executa conexão em thread separada para não bloquear a UI
            def connect_thread():
                try:
                    # Nota: A implementação exata depende da API da pyfreerdp
                    # Aqui é um exemplo conceitual
                    client = pyfreerdp.FreeRDPClient(**config)
                    client.connect()
                    self.logger.info("Conexão PyFreeRDP estabelecida")
                except Exception as e:
                    self.logger.error(f"Erro na conexão PyFreeRDP: {e}")

            thread = threading.Thread(target=connect_thread, daemon=True)
            thread.start()

            return True

        except Exception as e:
            self.logger.error(f"Erro ao usar PyFreeRDP: {e}")
            return False

    def _connect_rdpy(self, data: Dict[str, str]) -> bool:
        """Conecta usando a biblioteca RDPY"""
        try:
            self.logger.info("Conectando via RDPY...")

            # Configurações da conexão
            config = {
                "host": data["ip"],
                "port": int(data.get("port", 3389)),
                "username": data["user"],
                "password": data["pwd"],
                "domain": data.get("domain", ""),
                "fullscreen": True,
            }

            # Executa conexão em thread separada
            def connect_thread():
                try:
                    # Nota: A implementação exata depende da API da rdpy
                    # Aqui é um exemplo conceitual
                    from rdpy.protocol.rdp import rdp

                    client = rdp.RdpClient(**config)
                    client.connect()
                    self.logger.info("Conexão RDPY estabelecida")
                except Exception as e:
                    self.logger.error(f"Erro na conexão RDPY: {e}")

            thread = threading.Thread(target=connect_thread, daemon=True)
            thread.start()

            return True

        except Exception as e:
            self.logger.error(f"Erro ao usar RDPY: {e}")
            return False

    def _connect_python_fallback(self, data: Dict[str, str]) -> bool:
        """Fallback usando subprocess para chamar FreeRDP diretamente"""
        try:
            self.logger.info("Usando fallback Python subprocess...")

            # Cria comando FreeRDP via Python subprocess
            cmd = [
                "xfreerdp" if IS_LINUX else "wfreerdp",
                f'/v:{data["ip"]}',
                f'/u:{data["user"]}',
                f'/p:{data["pwd"]}',
                "/f",  # Fullscreen
                "/cert:ignore",
                "+clipboard",
                f'/title:{data.get("title", data["ip"])}',
            ]

            if "port" in data and data["port"] != "3389":
                cmd[1] = f'{data["ip"]}:{data["port"]}'

            # Executa em subprocess
            def connect_subprocess():
                try:
                    process = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True
                    )
                    self.logger.info(f"Processo RDP iniciado com PID: {process.pid}")
                except Exception as e:
                    self.logger.error(f"Erro no subprocess RDP: {e}")

            thread = threading.Thread(target=connect_subprocess, daemon=True)
            thread.start()

            return True

        except Exception as e:
            self.logger.error(f"Erro no fallback Python: {e}")
            return False

    def _connect_windows(self, data: Dict[str, str]) -> bool:
        """Conecta via RDP no Windows"""
        # Primeiro tenta o rdp.exe customizado
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets")
        rdp_exe_path = os.path.join(assets_dir, "rdp.exe")

        if os.path.exists(rdp_exe_path):
            return self._connect_windows_custom(data, rdp_exe_path)
        else:
            return self._connect_windows_mstsc(data)

    def _connect_windows_custom(self, data: Dict[str, str], rdp_exe_path: str) -> bool:
        """Conecta usando o rdp.exe customizado"""
        cmd = [
            rdp_exe_path,
            f"/v:{data['ip']}",
            f"/u:{data['user']}",
            f"/p:{data['pwd']}",
            f"/title:{data.get('title', data['ip'])}",
            "/max",
            "/noprinters",
            "/nosound",
            "/nowallpaper",
            "/drives:fixed,-c:",
            "/mon:2",
        ]

        # Adiciona ícone se disponível
        icon_path = os.path.join(os.path.dirname(rdp_exe_path), "ats.ico")
        if os.path.exists(icon_path):
            cmd.append(f"/icon:{icon_path}")

        return self._execute_command(cmd, "RDP customizado", data)

    def _connect_windows_mstsc(self, data: Dict[str, str]) -> bool:
        """Conecta usando MSTSC nativo do Windows"""
        # Cria arquivo RDP temporário
        rdp_content = self._generate_rdp_file(data)
        rdp_file = os.path.join(os.environ.get("TEMP", "C:\\temp"), f"wats_rdp_{data['ip']}.rdp")

        try:
            with open(rdp_file, "w", encoding="utf-8") as f:
                f.write(rdp_content)

            cmd = ["mstsc", rdp_file]
            success = self._execute_command(cmd, "MSTSC", data)

            # Remove arquivo temporário após uso
            try:
                os.remove(rdp_file)
            except BaseException:
                pass

            return success

        except Exception as e:
            self.logger.error(f"Erro ao criar arquivo RDP: {e}")
            return False

    def _connect_linux(self, data: Dict[str, str]) -> bool:
        """Conecta via RDP no Linux"""
        # Prioriza FreeRDP (mais moderno)
        if shutil.which("xfreerdp"):
            return self._connect_linux_freerdp(data)
        elif shutil.which("rdesktop"):
            return self._connect_linux_rdesktop(data)
        elif shutil.which("remmina"):
            return self._connect_linux_remmina(data)
        else:
            self.logger.error("Nenhum cliente RDP encontrado no Linux")
            return False

    def _connect_linux_freerdp(self, data: Dict[str, str]) -> bool:
        """Conecta usando FreeRDP no Linux"""
        cmd = [
            "xfreerdp",
            f'/v:{data["ip"]}',
            f'/u:{data["user"]}',
            f'/p:{data["pwd"]}',
            "/f",  # Fullscreen
            "/cert:ignore",
            "+clipboard",
            "/title:" + data.get("title", data["ip"]),
        ]

        # Adiciona porta se especificada
        if "port" in data and data["port"] != "3389":
            cmd[1] = f'{data["ip"]}:{data["port"]}'

        return self._execute_command(cmd, "FreeRDP", data)

    def _connect_linux_rdesktop(self, data: Dict[str, str]) -> bool:
        """Conecta usando rdesktop no Linux"""
        cmd = [
            "rdesktop",
            "-f",  # Fullscreen
            "-u",
            data["user"],
            "-p",
            data["pwd"],
            "-T",
            data.get("title", data["ip"]),
            data["ip"],
        ]

        # Adiciona porta se especificada
        if "port" in data and data["port"] != "3389":
            cmd.extend(["-P", data["port"]])

        return self._execute_command(cmd, "rdesktop", data)

    def _connect_linux_remmina(self, data: Dict[str, str]) -> bool:
        """Conecta usando Remmina no Linux"""
        # Remmina usa URIs para conexão rápida
        uri = f"rdp://{data['user']}:{data['pwd']}@{data['ip']}"

        if "port" in data and data["port"] != "3389":
            uri += f":{data['port']}"

        cmd = ["remmina", "-c", uri]
        return self._execute_command(cmd, "Remmina", data)

    def _connect_macos(self, data: Dict[str, str]) -> bool:
        """Conecta via RDP no macOS"""
        # Primeiro tenta FreeRDP
        if shutil.which("xfreerdp"):
            return self._connect_linux_freerdp(data)  # Usa a mesma lógica do Linux

        # Fallback para Microsoft Remote Desktop (mais complexo)
        self.logger.warning("Microsoft Remote Desktop requer configuração manual")
        return False

    def _generate_rdp_file(self, data: Dict[str, str]) -> str:
        """Gera conteúdo de arquivo .rdp para Windows"""
        # port = data.get("port", "3389")  # TODO: Usar quando necessário

        rdp_content = """screen mode id:i:2
use multimon:i:0
desktopwidth:i:1920
desktopheight:i:1080
session bpp:i:32
winposstr:s:0,3,0,0,800,600
compression:i:1
keyboardhook:i:2
audiocapturemode:i:0
videoplaybackmode:i:1
connection type:i:7
networkautodetect:i:1
bandwidthautodetect:i:1
displayconnectionbar:i:1
enableworkspacereconnect:i:0
disable wallpaper:i:1
allow font smoothing:i:0
allow desktop composition:i:0
disable full window drag:i:1
disable menu anims:i:1
disable themes:i:0
disable cursor setting:i:0
bitmapcachepersistenable:i:1
full address:s:{data['ip']}:{port}
audiomode:i:0
redirectprinters:i:0
redirectcomports:i:0
redirectsmartcards:i:1
redirectclipboard:i:1
redirectposdevices:i:0
autoreconnection enabled:i:1
authentication level:i:2
prompt for credentials:i:0
negotiate security layer:i:1
remoteapplicationmode:i:0
alternate shell:s:
shell working directory:s:
gatewayhostname:s:
gatewayusagemethod:i:4
gatewaycredentialssource:i:4
gatewayprofileusagemethod:i:0
promptcredentialonce:i:0
gatewaybrokeringtype:i:0
use redirection server name:i:0
rdgiskdcproxy:i:0
kdcproxyname:s:
username:s:{data['user']}
"""
        return rdp_content

    def _execute_command(
        self, cmd: List[str], client_name: str, data: Dict[str, str] = None
    ) -> bool:
        """Executa comando de conexão RDP"""
        try:
            # Mascara senha para log
            masked_cmd = []
            for arg in cmd:
                # Verifica se o argumento contém senha
                if (
                    ("/p:" in arg and len(arg) > 3)
                    or ("-p" in cmd and cmd.index(arg) == cmd.index("-p") + 1)
                    or (data and arg == data.get("pwd", ""))
                ):
                    masked_cmd.append("***")
                else:
                    masked_cmd.append(arg)

            self.logger.info(f"Executando {client_name}: {' '.join(masked_cmd)}")

            # Executa em background
            if IS_WINDOWS:
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                subprocess.Popen(cmd, start_new_session=True)

            self.logger.info(f"Conexão {client_name} iniciada com sucesso")
            return True

        except FileNotFoundError:
            self.logger.error(f"Cliente {client_name} não encontrado")
            return False
        except Exception as e:
            self.logger.exception(f"Erro ao executar {client_name}: {e}")
            return False

    def get_installation_instructions(self) -> str:
        """Retorna instruções de instalação para a plataforma atual"""
        if IS_WINDOWS:
            return """
Windows:
- O MSTSC já está instalado por padrão
- Para funcionalidades avançadas, use o rdp.exe customizado na pasta assets/
"""

        elif IS_LINUX:
            return """
Linux - Instale um cliente RDP:

Ubuntu/Debian:
sudo apt-get install freerdp2-x11 remmina

CentOS/RHEL/Fedora:
sudo yum install freerdp remmina
# ou: sudo dnf install freerdp remmina

Arch Linux:
sudo pacman -S freerdp remmina

Clientes disponíveis:
- FreeRDP (xfreerdp): Mais moderno e compatível
- Remmina: Interface gráfica completa
- rdesktop: Cliente clássico
- Vinagre: Cliente GNOME
"""

        elif IS_MACOS:
            return """
macOS:

1. Microsoft Remote Desktop (Recomendado):
   - Baixe da App Store

2. FreeRDP via Homebrew:
   brew install freerdp
"""

        else:
            return f"Plataforma {self.platform} não suportada"


# Instância global para uso
rdp_connector = RDPConnector()

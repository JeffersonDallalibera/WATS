"""
Wrapper Python simples para FreeRDP
Alternativa mais leve às bibliotecas RDP complexas
"""

import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
from typing import Dict, List, Optional


class SimpleFreeRDPWrapper:
    """Wrapper simples para executar FreeRDP via subprocess com controle melhorado"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_connections = {}
        self.executable = self._find_freerdp_executable()

    def _find_freerdp_executable(self) -> Optional[str]:
        """Encontra o executável FreeRDP apropriado"""
        if sys.platform.startswith("win"):
            # Windows - tenta encontrar wfreerdp
            possible_paths = [
                "wfreerdp",
                "wfreerdp.exe",
                r"C:\Program Files\FreeRDP\wfreerdp.exe",
                r"C:\Program Files (x86)\FreeRDP\wfreerdp.exe",
            ]
        else:
            # Linux/macOS
            possible_paths = ["xfreerdp", "freerdp", "/usr/bin/xfreerdp", "/usr/local/bin/xfreerdp"]

        for path in possible_paths:
            if (
                os.path.isfile(path)
                or subprocess.run(["which", path], capture_output=True).returncode == 0
            ):
                self.logger.info(f"FreeRDP encontrado: {path}")
                return path

        return None

    def is_available(self) -> bool:
        """Verifica se FreeRDP está disponível"""
        return self.executable is not None

    def connect(
        self, connection_data: Dict[str, str], session_id: str = None, background: bool = True
    ) -> bool:
        """
        Conecta via FreeRDP
        Args:
            connection_data: Dados da conexão (ip, user, pwd, etc.)
            session_id: ID da sessão para rastreamento
            background: Se True, executa em background
        Returns:
            True se conexão iniciada com sucesso
        """
        if not self.is_available():
            self.logger.error("FreeRDP não está disponível")
            return False

        try:
            session_id = session_id or f"rdp_{int(time.time())}"

            # Constrói comando FreeRDP
            cmd = self._build_freerdp_command(connection_data)

            if background:
                # Executa em background
                thread = threading.Thread(
                    target=self._execute_connection,
                    args=(cmd, session_id, connection_data),
                    daemon=True,
                )
                thread.start()
                return True
            else:
                # Execução síncrona
                return self._execute_connection(cmd, session_id, connection_data)

        except Exception as e:
            self.logger.exception(f"Erro ao conectar FreeRDP: {e}")
            return False

    def _build_freerdp_command(self, data: Dict[str, str]) -> List[str]:
        """Constrói comando FreeRDP baseado nos dados de conexão"""
        cmd = [self.executable]

        # Servidor e porta
        server = data["ip"]
        if "port" in data and data["port"] != "3389":
            server = f"{data['ip']}:{data['port']}"
        cmd.extend(["/v:" + server])

        # Credenciais
        cmd.extend([f"/u:{data['user']}", f"/p:{data['pwd']}"])

        # Domínio (se especificado)
        if "domain" in data and data["domain"]:
            cmd.append(f"/d:{data['domain']}")

        # Configurações de display
        cmd.extend(
            [
                "/f",  # Fullscreen
                "/cert:ignore",  # Ignora certificados
                "+clipboard",  # Compartilha clipboard
                "/compression",  # Ativa compressão
                "/auto-reconnect",  # Reconexão automática
            ]
        )

        # Título da janela
        if "title" in data:
            cmd.append(f"/title:{data['title']}")

        # Configurações adicionais
        cmd.extend(
            [
                "/sound:sys:alsa" if sys.platform.startswith("linux") else "/sound",
                (
                    "/drive:shared,/tmp"
                    if sys.platform.startswith("linux")
                    else "/drive:shared,C:\\temp"
                ),
                "+home-drive",
                "/network:auto",
            ]
        )

        return cmd

    def _execute_connection(self, cmd: List[str], session_id: str, data: Dict[str, str]) -> bool:
        """Executa a conexão FreeRDP"""
        try:
            # Mascara senha para log
            safe_cmd = []
            for arg in cmd:
                if arg.startswith("/p:"):
                    safe_cmd.append("/p:***")
                else:
                    safe_cmd.append(arg)

            self.logger.info(f"Executando FreeRDP [{session_id}]: {' '.join(safe_cmd)}")

            # Executa comando
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True
            )

            # Registra conexão ativa
            self.active_connections[session_id] = {
                "process": process,
                "data": data,
                "start_time": time.time(),
            }

            self.logger.info(f"Conexão FreeRDP [{session_id}] iniciada com PID: {process.pid}")

            # Aguarda conclusão (em thread separada se background)
            stdout, stderr = process.communicate()

            # Remove da lista de conexões ativas
            if session_id in self.active_connections:
                del self.active_connections[session_id]

            if process.returncode == 0:
                self.logger.info(f"Conexão FreeRDP [{session_id}] finalizada com sucesso")
                return True
            else:
                error_msg = (
                    stderr.decode("utf-8", errors="ignore") if stderr else "Erro desconhecido"
                )
                self.logger.error(f"Conexão FreeRDP [{session_id}] falhou: {error_msg}")
                return False

        except Exception as e:
            self.logger.exception(f"Erro ao executar FreeRDP [{session_id}]: {e}")
            return False

    def disconnect(self, session_id: str) -> bool:
        """Desconecta uma sessão ativa"""
        if session_id not in self.active_connections:
            self.logger.warning(f"Sessão {session_id} não encontrada")
            return False

        try:
            connection = self.active_connections[session_id]
            process = connection["process"]

            if process.poll() is None:  # Processo ainda ativo
                process.terminate()
                time.sleep(2)

                if process.poll() is None:  # Força encerramento
                    process.kill()

                self.logger.info(f"Sessão {session_id} desconectada")

            del self.active_connections[session_id]
            return True

        except Exception as e:
            self.logger.exception(f"Erro ao desconectar sessão {session_id}: {e}")
            return False

    def get_active_sessions(self) -> Dict[str, Dict]:
        """Retorna informações sobre sessões ativas"""
        active = {}

        for session_id, connection in self.active_connections.items():
            process = connection["process"]
            if process.poll() is None:  # Processo ainda ativo
                active[session_id] = {
                    "pid": process.pid,
                    "server": connection["data"]["ip"],
                    "user": connection["data"]["user"],
                    "start_time": connection["start_time"],
                    "duration": time.time() - connection["start_time"],
                }
            else:
                # Remove conexões mortas
                del self.active_connections[session_id]

        return active

    def disconnect_all(self) -> int:
        """Desconecta todas as sessões ativas"""
        count = 0
        for session_id in list(self.active_connections.keys()):
            if self.disconnect(session_id):
                count += 1

        self.logger.info(f"Desconectadas {count} sessões")
        return count

    def create_rdp_file(self, connection_data: Dict[str, str], filename: str = None) -> str:
        """Cria arquivo .rdp para usar com outros clientes"""
        if not filename:
            filename = os.path.join(tempfile.gettempdir(), f"wats_rdp_{connection_data['ip']}.rdp")

        rdp_content = """screen mode id:i:2
use multimon:i:0
desktopwidth:i:1920
desktopheight:i:1080
session bpp:i:32
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
full address:s:{connection_data['ip']}:{connection_data.get('port', '3389')}
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
username:s:{connection_data['user']}
"""

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(rdp_content)

            self.logger.info(f"Arquivo RDP criado: {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Erro ao criar arquivo RDP: {e}")
            return None


# Instância global
freerdp_wrapper = SimpleFreeRDPWrapper()

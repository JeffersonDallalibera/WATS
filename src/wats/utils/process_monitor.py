"""
Utilitários para monitoramento de processos RDP
==============================================

Este módulo fornece funcionalidades para verificar se processos RDP
ainda estão ativos, permitindo detectar desconexões inesperadas.
"""

import psutil
import logging
import subprocess
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re
import time

# Importação condicional do win32gui para verificar janelas RDP
try:
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logging.warning("win32gui não disponível - detecção de janelas RDP desabilitada")


@dataclass
class RdpProcessInfo:
    """Informações sobre um processo RDP ativo."""
    pid: int
    server_ip: str
    server_name: str
    user: str
    create_time: float
    cmdline: str


class RdpProcessMonitor:
    """Monitor de processos RDP ativos."""
    
    def __init__(self):
        """Inicializa o monitor."""
        self.tracked_processes: Dict[int, RdpProcessInfo] = {}
    
    def get_active_rdp_processes(self) -> List[RdpProcessInfo]:
        """
        Obtém lista de todos os processos RDP ativos no sistema.
        
        Returns:
            Lista de informações dos processos RDP
        """
        rdp_processes = []
        
        try:
            # Procura por processos rdp.exe e mstsc.exe
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    proc_info = proc.info
                    name = proc_info.get('name', '').lower()
                    
                    if name in ['rdp.exe', 'mstsc.exe']:
                        cmdline = proc_info.get('cmdline', [])
                        if cmdline:
                            cmdline_str = ' '.join(cmdline)
                            
                            # Extrair informações da linha de comando
                            server_ip = self._extract_server_from_cmdline(cmdline_str)
                            server_name = self._extract_title_from_cmdline(cmdline_str)
                            user = self._extract_user_from_cmdline(cmdline_str)
                            
                            rdp_info = RdpProcessInfo(
                                pid=proc_info['pid'],
                                server_ip=server_ip or "Unknown",
                                server_name=server_name or "Unknown",
                                user=user or "Unknown",
                                create_time=proc_info.get('create_time', 0),
                                cmdline=cmdline_str
                            )
                            rdp_processes.append(rdp_info)
                            
                            logging.debug(f"Encontrado processo RDP: PID {rdp_info.pid}, Servidor {rdp_info.server_ip}, Usuário {rdp_info.user}")
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # NOVO: Se não encontrou processos, tenta buscar por janelas RDP (fallback)
            if not rdp_processes and WIN32_AVAILABLE:
                logging.debug("[PROCESS_CHECK] Nenhum processo encontrado, tentando buscar por janelas RDP...")
                rdp_processes.extend(self._get_rdp_processes_from_windows())
                    
        except Exception as e:
            logging.error(f"Erro ao listar processos RDP: {e}")
        
        # Validação final antes de retornar
        if not isinstance(rdp_processes, list):
            logging.error(f"ERRO CRÍTICO: rdp_processes não é uma lista! Tipo: {type(rdp_processes)}")
            return []
        
        return rdp_processes
    
    def _get_rdp_processes_from_windows(self) -> List[RdpProcessInfo]:
        """
        Busca processos RDP através de janelas abertas (fallback).
        
        Returns:
            Lista de processos RDP encontrados via janelas
        """
        rdp_processes = []
        
        if not WIN32_AVAILABLE:
            return rdp_processes
        
        def enum_windows_callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                
                # Procura por títulos típicos de janelas RDP
                rdp_indicators = [
                    'Remote Desktop Plus',
                    'Conexão de Área de Trabalho Remota',
                    'Remote Desktop Connection',
                    'mstsc.exe'
                ]
                
                if any(indicator in window_title for indicator in rdp_indicators):
                    try:
                        # Obtém o PID do processo que possui a janela
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        
                        # Tenta extrair IP do título da janela
                        # Formato comum: "Remote Desktop Plus - 192.168.1.110:3389 - ..."
                        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', window_title)
                        server_ip = ip_match.group(1) if ip_match else "Unknown"
                        
                        # Obtém informações do processo
                        try:
                            proc = psutil.Process(pid)
                            create_time = proc.create_time()
                            cmdline = ' '.join(proc.cmdline())
                        except:
                            create_time = time.time()
                            cmdline = f"Window: {window_title}"
                        
                        rdp_info = RdpProcessInfo(
                            pid=pid,
                            server_ip=server_ip,
                            server_name=window_title,
                            user="Unknown",
                            create_time=create_time,
                            cmdline=cmdline
                        )
                        results.append(rdp_info)
                        logging.debug(f"[WINDOW_SEARCH] Encontrada janela RDP: {window_title} (PID {pid}, IP {server_ip})")
                        
                    except Exception as e:
                        logging.debug(f"[WINDOW_SEARCH] Erro ao processar janela: {e}")
        
        try:
            win32gui.EnumWindows(enum_windows_callback, rdp_processes)
        except Exception as e:
            logging.error(f"[WINDOW_SEARCH] Erro ao enumerar janelas: {e}")
        
        return rdp_processes
    
    def _extract_server_from_cmdline(self, cmdline: str) -> Optional[str]:
        """Extrai o IP/hostname do servidor da linha de comando."""
        # Para rdp.exe: /v:192.168.1.100
        # Para mstsc.exe: /v:192.168.1.100 ou mstsc /v:server.domain.com
        match = re.search(r'/v:([^\s]+)', cmdline)
        if match:
            server = match.group(1)
            # Remove porta se houver (ex: 192.168.1.100:3389 -> 192.168.1.100)
            if ':' in server:
                server = server.split(':')[0]
            return server
        return None
    
    def _extract_title_from_cmdline(self, cmdline: str) -> Optional[str]:
        """Extrai o título/nome da conexão da linha de comando."""
        # Para rdp.exe: /title:"Nome do Servidor"
        match = re.search(r'/title:(["\']?)([^"\']+)\1', cmdline)
        if match:
            return match.group(2)
        return None
    
    def _extract_user_from_cmdline(self, cmdline: str) -> Optional[str]:
        """Extrai o usuário da linha de comando."""
        # Para rdp.exe: /u:usuario
        match = re.search(r'/u:([^\s]+)', cmdline)
        if match:
            return match.group(1)
        return None
    
    def is_rdp_process_active(self, server_ip: str, user: str = None, 
                             title: str = None, tolerance_seconds: int = 10) -> bool:
        """
        Verifica se existe um processo RDP ativo para um servidor específico.
        
        Args:
            server_ip: IP ou hostname do servidor para verificar
            user: Usuário específico (opcional)
            title: Título da conexão (opcional) 
            tolerance_seconds: Tolerância em segundos para criação recente do processo
            
        Returns:
            True se existe processo ativo, False caso contrário
        """
        try:
            active_processes = self.get_active_rdp_processes()
            
            # Validação defensiva
            if not isinstance(active_processes, list):
                logging.error(f"[PROCESS_CHECK] get_active_rdp_processes retornou tipo inválido: {type(active_processes)}")
                return True  # Em caso de erro, assume ativo
            
            current_time = time.time()
            
            # Remove porta do server_ip se presente
            server_ip_clean = server_ip.split(':')[0] if ':' in server_ip else server_ip
            
            logging.debug(f"[PROCESS_CHECK] Verificando RDP para {server_ip_clean} (user={user}, title={title})")
            logging.debug(f"[PROCESS_CHECK] Processos RDP ativos: {len(active_processes)}")
            
            for proc in active_processes:
                # Validação adicional
                if not isinstance(proc, RdpProcessInfo):
                    logging.error(f"[PROCESS_CHECK] Item na lista não é RdpProcessInfo: {type(proc)}")
                    continue
                    
                logging.debug(f"[PROCESS_CHECK] Processo encontrado - IP: {proc.server_ip}, User: {proc.user}, Title: {proc.server_name}, PID: {proc.pid}")
                
                # Verifica se corresponde ao servidor (IP ou hostname)
                # Compara tanto o valor direto quanto por título (que pode conter o nome do servidor)
                matches_server = (
                    proc.server_ip == server_ip_clean or
                    proc.server_name == server_ip_clean or
                    (title and proc.server_name == title)
                )
                
                if matches_server:
                    # Verificações opcionais (mais flexíveis)
                    if user and proc.user != "Unknown" and proc.user != user:
                        logging.debug(f"[PROCESS_CHECK] Usuário não corresponde: esperado '{user}', encontrado '{proc.user}'")
                        continue
                    
                    # Verifica se não é um processo muito recente (evita falsos positivos)
                    uptime = current_time - proc.create_time
                    if uptime > tolerance_seconds:
                        logging.info(f"[PROCESS_CHECK] ✓ Processo RDP ATIVO encontrado para {server_ip_clean} via {proc.server_ip} (PID {proc.pid}, uptime {int(uptime)}s)")
                        return True
                    else:
                        logging.debug(f"[PROCESS_CHECK] Processo muito recente ({int(uptime)}s), ignorando")
            
            logging.warning(f"[PROCESS_CHECK] ✗ Nenhum processo RDP ativo encontrado para {server_ip_clean}")
            return False
            
        except AttributeError as e:
            logging.error(f"Erro de atributo ao verificar processo RDP: {e}", exc_info=True)
            return True  # Em caso de erro, assume que está ativo para não limpar incorretamente
        except Exception as e:
            logging.error(f"Erro ao verificar processo RDP ativo: {e}", exc_info=True)
            return True  # Em caso de erro, assume que está ativo para não limpar incorretamente
    
    def register_rdp_connection(self, server_ip: str, user: str, title: str) -> Optional[int]:
        """
        Registra uma conexão RDP para monitoramento.
        
        Args:
            server_ip: IP do servidor
            user: Usuário da conexão
            title: Título da conexão
            
        Returns:
            PID do processo se encontrado, None caso contrário
        """
        try:
            active_processes = self.get_active_rdp_processes()
            
            # Procura processo correspondente criado recentemente (últimos 30 segundos)
            current_time = time.time()
            for proc in active_processes:
                if (proc.server_ip == server_ip and 
                    proc.user == user and 
                    current_time - proc.create_time <= 30):
                    
                    logging.info(f"Registrado processo RDP PID {proc.pid} para {server_ip}")
                    return proc.pid
            
            return None
            
        except Exception as e:
            logging.error(f"Erro ao registrar conexão RDP: {e}")
            return None
    
    def get_rdp_process_info(self, server_ip: str, user: str = None) -> Optional[RdpProcessInfo]:
        """
        Obtém informações detalhadas sobre um processo RDP específico.
        
        Args:
            server_ip: IP do servidor
            user: Usuário (opcional)
            
        Returns:
            Informações do processo ou None se não encontrado
        """
        try:
            active_processes = self.get_active_rdp_processes()
            
            for proc in active_processes:
                if proc.server_ip == server_ip:
                    if user is None or proc.user == user:
                        return proc
            
            return None
            
        except Exception as e:
            logging.error(f"Erro ao obter informações do processo RDP: {e}")
            return None


def get_rdp_monitor() -> RdpProcessMonitor:
    """Retorna instância singleton do monitor RDP."""
    if not hasattr(get_rdp_monitor, '_instance'):
        get_rdp_monitor._instance = RdpProcessMonitor()
    return get_rdp_monitor._instance


def is_rdp_connection_active(server_ip: str, user: str = None, title: str = None) -> bool:
    """
    Função utilitária para verificar se uma conexão RDP específica está ativa.
    
    Args:
        server_ip: IP do servidor
        user: Usuário (opcional)
        title: Título da conexão (opcional)
        
    Returns:
        True se a conexão está ativa, False caso contrário
    """
    monitor = get_rdp_monitor()
    return monitor.is_rdp_process_active(server_ip, user, title)


def list_all_rdp_connections() -> List[Dict[str, str]]:
    """
    Lista todas as conexões RDP ativas no sistema.
    
    Returns:
        Lista de dicionários com informações das conexões
    """
    monitor = get_rdp_monitor()
    processes = monitor.get_active_rdp_processes()
    
    return [
        {
            'pid': str(proc.pid),
            'server_ip': proc.server_ip,
            'server_name': proc.server_name,
            'user': proc.user,
            'uptime': f"{int(time.time() - proc.create_time)}s"
        }
        for proc in processes
    ]


if __name__ == "__main__":
    # Teste da funcionalidade
    print("=== TESTE DO MONITOR DE PROCESSOS RDP ===")
    
    monitor = RdpProcessMonitor()
    processes = monitor.get_active_rdp_processes()
    
    if processes:
        print(f"Encontrados {len(processes)} processo(s) RDP ativo(s):")
        for proc in processes:
            print(f"  PID: {proc.pid}")
            print(f"  Servidor: {proc.server_ip}")
            print(f"  Nome: {proc.server_name}")
            print(f"  Usuário: {proc.user}")
            print(f"  Tempo ativo: {int(time.time() - proc.create_time)}s")
            print(f"  Comando: {proc.cmdline}")
            print("-" * 40)
    else:
        print("Nenhum processo RDP ativo encontrado.")
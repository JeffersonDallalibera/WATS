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
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            logging.error(f"Erro ao listar processos RDP: {e}")
        
        return rdp_processes
    
    def _extract_server_from_cmdline(self, cmdline: str) -> Optional[str]:
        """Extrai o IP/hostname do servidor da linha de comando."""
        # Para rdp.exe: /v:192.168.1.100
        # Para mstsc.exe: /v:192.168.1.100 ou mstsc /v:server.domain.com
        match = re.search(r'/v:([^\s]+)', cmdline)
        if match:
            return match.group(1)
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
            server_ip: IP do servidor para verificar
            user: Usuário específico (opcional)
            title: Título da conexão (opcional) 
            tolerance_seconds: Tolerância em segundos para criação recente do processo
            
        Returns:
            True se existe processo ativo, False caso contrário
        """
        try:
            active_processes = self.get_active_rdp_processes()
            current_time = time.time()
            
            for proc in active_processes:
                # Verifica se corresponde ao servidor
                if proc.server_ip == server_ip:
                    # Verificações opcionais
                    if user and proc.user != user:
                        continue
                    if title and proc.server_name != title:
                        continue
                    
                    # Verifica se não é um processo muito recente (evita falsos positivos)
                    if current_time - proc.create_time > tolerance_seconds:
                        return True
            
            return False
            
        except Exception as e:
            logging.error(f"Erro ao verificar processo RDP ativo: {e}")
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
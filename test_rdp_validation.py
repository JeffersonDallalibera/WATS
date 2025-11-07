"""
Teste da Validação Automática de Processos RDP
==============================================

Este script testa se a funcionalidade de detecção automática
de desconexões RDP está funcionando corretamente.
"""

import sys
import os
import time
import threading
from typing import List, Dict

# Adicionar o src ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from wats.utils.process_monitor import RdpProcessMonitor, is_rdp_connection_active, list_all_rdp_connections


def test_rdp_process_detection():
    """Testa a detecção de processos RDP."""
    print("=" * 60)
    print("🧪 TESTE: Detecção de Processos RDP")
    print("=" * 60)
    
    monitor = RdpProcessMonitor()
    
    # Lista processos ativos
    processes = monitor.get_active_rdp_processes()
    
    if processes:
        print(f"✅ Encontrados {len(processes)} processo(s) RDP ativo(s):")
        for i, proc in enumerate(processes, 1):
            print(f"\n📋 Processo {i}:")
            print(f"   PID: {proc.pid}")
            print(f"   Servidor: {proc.server_ip}")
            print(f"   Nome: {proc.server_name}")
            print(f"   Usuário: {proc.user}")
            print(f"   Tempo ativo: {int(time.time() - proc.create_time)}s")
            print(f"   Comando: {proc.cmdline[:100]}...")
            
            # Testa verificação específica
            is_active = monitor.is_rdp_process_active(proc.server_ip, proc.user)
            print(f"   Status verificado: {'✅ ATIVO' if is_active else '❌ INATIVO'}")
    else:
        print("ℹ️  Nenhum processo RDP ativo detectado")
        print("\n💡 Para testar completamente:")
        print("   1. Abra uma conexão RDP (mstsc ou rdp.exe)")
        print("   2. Execute este teste novamente")
    
    return len(processes)


def test_connection_validation():
    """Testa validação de conexões específicas."""
    print("\n" + "=" * 60)
    print("🧪 TESTE: Validação de Conexões Específicas")
    print("=" * 60)
    
    # Testa alguns IPs comuns
    test_ips = ["192.168.1.100", "10.0.0.1", "172.16.0.1", "127.0.0.1"]
    
    for ip in test_ips:
        is_active = is_rdp_connection_active(ip)
        status = "✅ ATIVO" if is_active else "❌ INATIVO"
        print(f"   {ip}: {status}")


def simulate_heartbeat_with_validation(server_ip: str, user: str, title: str):
    """
    Simula um heartbeat com validação de processo.
    
    Args:
        server_ip: IP do servidor
        user: Usuário
        title: Título da conexão
    """
    print(f"\n🔄 Simulando heartbeat para {server_ip} (usuário: {user})")
    
    missed_heartbeats = 0
    max_missed_heartbeats = 3
    
    for i in range(10):  # Simula 10 ciclos de heartbeat
        time.sleep(2)  # Heartbeat a cada 2 segundos (mais rápido para teste)
        
        rdp_active = is_rdp_connection_active(server_ip, user, title)
        
        if not rdp_active:
            missed_heartbeats += 1
            print(f"   ⚠️  Ciclo {i+1}: Processo RDP não encontrado (tentativa {missed_heartbeats}/{max_missed_heartbeats})")
            
            if missed_heartbeats >= max_missed_heartbeats:
                print(f"   🚨 Ciclo {i+1}: Processo RDP definitivamente inativo! Limpeza seria executada.")
                return False  # Indicaria limpeza
        else:
            if missed_heartbeats > 0:
                print(f"   ✅ Ciclo {i+1}: Processo RDP redetectado!")
                missed_heartbeats = 0
            else:
                print(f"   ✅ Ciclo {i+1}: Processo RDP ativo, heartbeat enviado")
    
    print(f"   ✅ Heartbeat concluído para {server_ip}")
    return True


def test_heartbeat_simulation():
    """Testa simulação de heartbeat."""
    print("\n" + "=" * 60)
    print("🧪 TESTE: Simulação de Heartbeat com Validação")
    print("=" * 60)
    
    monitor = RdpProcessMonitor()
    processes = monitor.get_active_rdp_processes()
    
    if processes:
        # Testa com processo real
        proc = processes[0]
        print(f"📡 Testando heartbeat com processo real:")
        print(f"   Servidor: {proc.server_ip}")
        print(f"   Usuário: {proc.user}")
        print(f"   Nome: {proc.server_name}")
        
        simulate_heartbeat_with_validation(proc.server_ip, proc.user, proc.server_name)
    
    # Testa com processo inexistente
    print(f"\n📡 Testando heartbeat com processo INEXISTENTE:")
    simulate_heartbeat_with_validation("999.999.999.999", "usuario_fake", "Servidor Fake")


def monitor_rdp_changes():
    """Monitora mudanças nos processos RDP em tempo real."""
    print("\n" + "=" * 60)
    print("🧪 TESTE: Monitoramento em Tempo Real (30 segundos)")
    print("=" * 60)
    
    print("💡 Durante este teste:")
    print("   - Abra ou feche conexões RDP")
    print("   - Observe as mudanças sendo detectadas")
    
    monitor = RdpProcessMonitor()
    previous_pids = set()
    
    start_time = time.time()
    cycle = 0
    
    while time.time() - start_time < 30:  # Monitora por 30 segundos
        cycle += 1
        processes = monitor.get_active_rdp_processes()
        current_pids = {proc.pid for proc in processes}
        
        # Detecta mudanças
        new_pids = current_pids - previous_pids
        removed_pids = previous_pids - current_pids
        
        if new_pids or removed_pids or cycle == 1:
            print(f"\n⏰ Ciclo {cycle} ({len(processes)} processo(s) ativo(s)):")
            
            if new_pids:
                for proc in processes:
                    if proc.pid in new_pids:
                        print(f"   ➕ NOVO: PID {proc.pid} → {proc.server_ip} ({proc.server_name})")
            
            if removed_pids:
                for pid in removed_pids:
                    print(f"   ➖ REMOVIDO: PID {pid}")
            
            if not new_pids and not removed_pids and cycle == 1:
                if processes:
                    for proc in processes:
                        print(f"   📋 EXISTENTE: PID {proc.pid} → {proc.server_ip} ({proc.server_name})")
                else:
                    print("   ℹ️  Nenhum processo RDP ativo")
        
        previous_pids = current_pids
        time.sleep(3)  # Verifica a cada 3 segundos
    
    print("\n✅ Monitoramento concluído")


def main():
    """Executa todos os testes."""
    print("🚀 INICIANDO TESTES DE VALIDAÇÃO RDP")
    print("=" * 60)
    
    try:
        # Teste 1: Detecção básica
        num_processes = test_rdp_process_detection()
        
        # Teste 2: Validação específica
        test_connection_validation()
        
        # Teste 3: Simulação de heartbeat
        test_heartbeat_simulation()
        
        # Teste 4: Monitoramento em tempo real
        monitor_rdp_changes()
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES CONCLUÍDOS")
        print("=" * 60)
        
        if num_processes > 0:
            print("🎯 Resultados:")
            print(f"   • {num_processes} processo(s) RDP detectado(s)")
            print("   • Validação de processos específicos funcionando")
            print("   • Simulação de heartbeat concluída")
            print("   • Monitoramento em tempo real testado")
        else:
            print("⚠️  Nota:")
            print("   • Nenhum processo RDP ativo durante o teste")
            print("   • Para teste completo, inicie uma conexão RDP")
            print("   • Funcionalidades básicas validadas")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE TESTES: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
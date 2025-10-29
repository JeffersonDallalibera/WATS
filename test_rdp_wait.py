#!/usr/bin/env python3
"""
Script de teste para validar que o sistema espera a janela RDP aparecer.
"""

import logging
import time
import sys
from src.wats.recording.smart_session_recorder import SmartSessionRecorder

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def test_rdp_window_wait():
    """Testa se o sistema espera a janela RDP aparecer."""
    
    print("=== Teste de Espera da Janela RDP ===")
    print()
    
    # Configuração de teste
    connection_info = {
        'host': '138.36.217.138',
        'port': '33899',
        'username': 'jefferson.dallaliber',
        'session_id': 'test_session_123'
    }
    
    output_dir = "C:/Users/jefferson.dallaliber/Videos/Wats/test"
    
    print(f"Conexão RDP: {connection_info['host']}:{connection_info['port']}")
    print(f"Usuário: {connection_info['username']}")
    print(f"Diretório de saída: {output_dir}")
    print()
    print("INSTRUÇÕES:")
    print("1. Execute este script")
    print("2. Abra uma conexão RDP para o host/porta especificados")
    print("3. Observe nos logs quando a janela for detectada")
    print("4. A gravação deve iniciar automaticamente")
    print()
    
    try:
        # Cria recorder
        recorder = SmartSessionRecorder(
            connection_info=connection_info,
            output_dir=output_dir
        )
        
        print("SmartSessionRecorder criado. Iniciando gravação...")
        print("Aguardando janela RDP aparecer...")
        print("(Máximo 30 tentativas x 4 segundos = 2 minutos)")
        print()
        
        # Inicia gravação (que vai esperar a janela)
        success = recorder.start_recording()
        
        if success:
            print("Gravação iniciada com sucesso!")
            print("O sistema está aguardando a janela RDP aparecer...")
            print()
            print("Pressione Ctrl+C para parar o teste")
            
            # Mantém o script rodando
            try:
                while True:
                    time.sleep(5)
                    
                    # Mostra status do recorder
                    status = recorder.get_recording_status()
                    print(f"Status atual: {status['state']}")
                    
                    if status['current_file']:
                        print(f"Arquivo atual: {status['current_file']}")
                        print(f"Duração: {status['duration']:.1f}s")
                        print(f"Frames: {status['frame_count']}")
                    
                    print("---")
                    
            except KeyboardInterrupt:
                print("\nParando gravação...")
                recorder.stop_recording()
                print("Gravação parada.")
                
        else:
            print("Falha ao iniciar gravação!")
            return False
            
    except Exception as e:
        print(f"Erro durante teste: {e}")
        logging.exception("Erro detalhado:")
        return False
    
    return True

if __name__ == "__main__":
    success = test_rdp_window_wait()
    sys.exit(0 if success else 1)
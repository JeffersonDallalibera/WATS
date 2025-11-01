"""
Teste rápido para verificar se a detecção de estado da janela está funcionando.
"""

import logging
import time


from src.wats.recording.window_tracker import WindowTracker

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def test_window_state_detection():
    """Testa a detecção de estado da janela."""
    print("=== Teste de Detecção de Estado da Janela ===")

    # Configuração de conexão simulada
    connection_info = {
        "server_ip": "138.36.217.138",
        "server_port": "33899",
        "session_name": "Test Session",
    }

    # Criar window tracker
    tracker = WindowTracker(connection_info, update_interval=1.0)

    # Definir callback para mudanças de estado
    def on_state_changed(old_state, new_state):
        print(f"Estado mudou: {old_state.value} -> {new_state.value}")

    def on_window_found(window_info):
        print(f"Janela encontrada: {window_info.title} (HWND: {window_info.hwnd})")

    def on_window_lost():
        print("Janela perdida!")

    # Configurar callbacks
    tracker.set_callbacks(
        on_state_changed=on_state_changed, on_found=on_window_found, on_lost=on_window_lost
    )

    # Iniciar rastreamento
    print("Iniciando rastreamento (aguardando janela RDP aparecer...)...")
    if tracker.start_tracking():
        print("Rastreamento iniciado com sucesso!")
        print("Aguardando 30 segundos para detectar mudanças...")

        # Aguardar e monitorar
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            print("\nInterrompido pelo usuário")

        # Parar rastreamento
        tracker.stop_tracking()
        print("Rastreamento parado")
    else:
        print("Falha ao iniciar rastreamento")


if __name__ == "__main__":
    test_window_state_detection()

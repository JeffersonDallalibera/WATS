# WATS_Project/examples/integration_session_protection.py

"""
Exemplo de integração do sistema de proteção de sessão com validação no servidor.

Este arquivo demonstra como modificar o código principal do WATS para usar
a validação de senhas no servidor SQL Server em vez de localmente.
"""

import logging
from typing import Dict, Any, Optional
from src.wats.db.db_service import DBService
from docs.session_protection import (
    CreateSessionProtectionDialog,
    ValidateSessionPasswordDialog,
    configure_session_protection_with_db,
    session_protection_manager
)


class WATSConnectionHandler:
    """Exemplo de como integrar a proteção de sessão no WATS."""
    
    def __init__(self, db_service: DBService):
        self.db_service = db_service
        
        # Configura o gerenciador de proteção para usar o servidor
        configure_session_protection_with_db(db_service)
        
        logging.info("Sistema de proteção de sessão configurado com validação no servidor")

    def connect_to_server(self, connection_data: Dict[str, Any], current_user: str) -> bool:
        """
        Tenta conectar a um servidor, verificando proteção de sessão.
        
        Args:
            connection_data: Dados da conexão (id, nome, etc.)
            current_user: Usuário atual tentando conectar
            
        Returns:
            True se conexão autorizada, False caso contrário
        """
        connection_id = connection_data.get('db_id')
        connection_name = connection_data.get('title', 'Unknown')
        
        # Verifica se a sessão está protegida
        if session_protection_manager.is_session_protected(connection_id):
            logging.info(f"Sessão protegida detectada para {connection_name}")
            
            # Busca informações da proteção
            protection_info = session_protection_manager.get_session_protection_info(connection_id)
            protected_by = protection_info.get('protected_by', 'Unknown') if protection_info else 'Unknown'
            
            # Mostra diálogo de validação de senha
            dialog = ValidateSessionPasswordDialog(
                parent=None,  # Substitua pela janela principal
                connection_data=connection_data,
                requesting_user=current_user,
                protected_by=protected_by
            )
            
            # Aguarda resultado
            dialog.wait_window()
            result = dialog.get_result()
            
            if result and result.get("validated"):
                logging.info(f"✅ Acesso autorizado via senha para {current_user} → {connection_name}")
                return True
            else:
                logging.warning(f"❌ Acesso negado para {current_user} → {connection_name}")
                return False
        
        # Sessão não protegida - acesso livre
        logging.info(f"Conectando livremente a {connection_name}")
        return True

    def protect_current_session(self, connection_data: Dict[str, Any], current_user: str) -> bool:
        """
        Permite ao usuário atual proteger sua sessão.
        
        Args:
            connection_data: Dados da conexão atual
            current_user: Usuário que quer proteger a sessão
            
        Returns:
            True se proteção criada, False caso contrário
        """
        dialog = CreateSessionProtectionDialog(
            parent=None,  # Substitua pela janela principal
            connection_data=connection_data,
            current_user=current_user
        )
        
        # Aguarda resultado
        dialog.wait_window()
        result = dialog.get_result()
        
        if result and result.get("activated"):
            logging.info(f"🔒 Proteção ativada por {current_user} para {connection_data.get('title')}")
            return True
        else:
            logging.info(f"Proteção cancelada por {current_user}")
            return False

    def remove_session_protection(self, connection_id: int, current_user: str) -> bool:
        """Remove proteção de sessão (apenas o criador pode)."""
        success = session_protection_manager.remove_session_protection(connection_id, current_user)
        
        if success:
            logging.info(f"🔓 Proteção removida por {current_user}")
            return True
        else:
            logging.warning(f"Falha ao remover proteção por {current_user}")
            return False


# Exemplo de uso no código principal do WATS
def example_integration():
    """Demonstra como usar a integração no código principal."""
    
    # Inicializar DB Service (substitua pela implementação real)
    db_service = DBService()  # Sua instância do DB
    
    # Criar handler de conexões
    connection_handler = WATSConnectionHandler(db_service)
    
    # Exemplo 1: Usuário tentando conectar
    connection_data = {
        'db_id': 123,
        'title': 'Servidor Produção',
        'ip': '192.168.1.100'
    }
    
    current_user = "jefferson.oliveira"
    
    # Tenta conectar (verificará proteção automaticamente)
    can_connect = connection_handler.connect_to_server(connection_data, current_user)
    
    if can_connect:
        print("✅ Conexão autorizada - prosseguir com RDP/AnyDesk")
        
        # Usuário pode optar por proteger sua sessão
        user_wants_protection = True  # Substitua por input do usuário
        if user_wants_protection:
            connection_handler.protect_current_session(connection_data, current_user)
            
    else:
        print("❌ Conexão negada - acesso bloqueado")


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Executar exemplo
    example_integration()
# WATS_Project/tests/test_session_protection_integration.py

"""
Teste de integração do sistema de proteção de sessão com validação no servidor.

Este teste verifica se a integração entre a interface do WATS e o repositório
do SQL Server está funcionando corretamente.
"""

import unittest
import logging
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Mock do CustomTkinter para testes
import sys
sys.modules['customtkinter'] = Mock()
sys.modules['tkinter'] = Mock()

from docs.session_protection import (
    SessionProtectionManager,
    configure_session_protection_with_db
)


class TestSessionProtectionIntegration(unittest.TestCase):
    """Testa a integração do sistema de proteção com o servidor."""

    def setUp(self):
        """Configuração inicial para cada teste."""
        self.mock_db_service = Mock()
        self.mock_db_manager = Mock()
        self.mock_session_repo = Mock()
        
        # Configura mocks
        self.mock_db_service.db_manager = self.mock_db_manager
        
        # Mock do repositório
        with patch('docs.session_protection.SessionProtectionRepository') as mock_repo_class:
            mock_repo_class.return_value = self.mock_session_repo
            self.manager = SessionProtectionManager(self.mock_db_service)

    def test_configure_with_db_service(self):
        """Testa configuração do gerenciador com DBService."""
        # Configura o gerenciador global
        configure_session_protection_with_db(self.mock_db_service)
        
        # Verifica se o repositório foi criado
        self.assertIsNotNone(self.manager.session_repo)

    def test_create_protection_uses_server(self):
        """Testa se a criação de proteção usa o servidor."""
        # Configura mock do repositório
        self.mock_session_repo.create_session_protection.return_value = (True, "Sucesso", 123)
        
        # Dados da proteção
        protection_data = {
            'protected_by': 'user_test',
            'machine_name': 'PC-TEST',
            'duration_minutes': 60,
            'notes': 'Teste',
            'ip_address': '192.168.1.100'
        }
        
        # Cria proteção
        result = self.manager.activate_session_protection(
            connection_id=456,
            password="senha123",
            protection_data=protection_data
        )
        
        # Verifica se usou o servidor
        self.assertTrue(result)
        self.mock_session_repo.create_session_protection.assert_called_once_with(
            con_codigo=456,
            user_name='user_test',
            machine_name='PC-TEST',
            password="senha123",
            duration_minutes=60,
            notes='Teste',
            ip_address='192.168.1.100'
        )

    def test_validate_password_uses_server(self):
        """Testa se a validação de senha usa o servidor."""
        # Configura mock do repositório
        self.mock_session_repo.validate_session_password.return_value = {
            "valid": True,
            "protection_id": 123,
            "protected_by": "user_test",
            "message": "Acesso autorizado"
        }
        
        # Valida senha
        with patch('socket.gethostname', return_value='PC-TEST'), \
             patch('socket.gethostbyname', return_value='192.168.1.100'):
            
            result = self.manager.validate_session_password(
                connection_id=456,
                password="senha123",
                requesting_user="user_solicitante"
            )
        
        # Verifica resultado
        self.assertTrue(result["valid"])
        self.assertEqual(result["protected_by"], "user_test")
        
        # Verifica se chamou o servidor
        self.mock_session_repo.validate_session_password.assert_called_once_with(
            con_codigo=456,
            password="senha123",
            requesting_user="user_solicitante",
            requesting_machine='PC-TEST',
            ip_address='192.168.1.100'
        )

    def test_validate_password_server_failure_fallback(self):
        """Testa fallback local quando servidor falha."""
        # Configura mock para falhar
        self.mock_session_repo.validate_session_password.side_effect = Exception("Conexão perdida")
        
        # Adiciona proteção local para teste de fallback
        self.manager.protected_sessions[456] = {
            "password": "senha123",
            "protection_data": {
                "protected_by": "user_test",
                "connection_name": "Servidor Teste",
                "expiry_time": (datetime.now() + timedelta(hours=1)).isoformat()
            },
            "created_at": datetime.now().isoformat()
        }
        
        # Valida senha (deve usar fallback local)
        result = self.manager.validate_session_password(
            connection_id=456,
            password="senha123",
            requesting_user="user_solicitante"
        )
        
        # Verifica que usou fallback local
        self.assertTrue(result["valid"])
        self.assertIn("(local)", result.get("reason", ""))

    def test_remove_protection_uses_server(self):
        """Testa se a remoção de proteção usa o servidor."""
        # Configura mock do repositório
        self.mock_session_repo.remove_session_protection.return_value = (True, "Removido com sucesso")
        
        # Remove proteção
        result = self.manager.remove_session_protection(
            connection_id=456,
            user="user_test"
        )
        
        # Verifica resultado
        self.assertTrue(result)
        
        # Verifica se chamou o servidor
        self.mock_session_repo.remove_session_protection.assert_called_once_with(
            con_codigo=456,
            removing_user="user_test"
        )

    def test_is_protected_checks_server_first(self):
        """Testa se verificação de proteção consulta o servidor primeiro."""
        # Configura mock do repositório
        self.mock_session_repo.get_active_protections_by_connection.return_value = [
            {"protection_id": 123, "protected_by": "user_test"}
        ]
        
        # Verifica proteção
        result = self.manager.is_session_protected(456)
        
        # Verifica resultado
        self.assertTrue(result)
        
        # Verifica se consultou o servidor
        self.mock_session_repo.get_active_protections_by_connection.assert_called_once_with(456)

    def test_logging_integration(self):
        """Testa se os logs estão sendo gerados corretamente."""
        # Configura mock do repositório
        self.mock_session_repo.validate_session_password.return_value = {
            "valid": True,
            "protection_id": 123,
            "protected_by": "user_test",
            "message": "Acesso autorizado"
        }
        
        # Captura logs
        with self.assertLogs(level='INFO') as log_capture:
            with patch('socket.gethostname', return_value='PC-TEST'), \
                 patch('socket.gethostbyname', return_value='192.168.1.100'):
                
                self.manager.validate_session_password(
                    connection_id=456,
                    password="senha123",
                    requesting_user="user_solicitante"
                )
        
        # Verifica se o log foi gerado
        self.assertTrue(any("ACESSO AUTORIZADO VIA SERVIDOR" in record for record in log_capture.output))


if __name__ == '__main__':
    # Configurar logging para os testes
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    unittest.main()
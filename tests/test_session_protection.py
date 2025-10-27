# WATS_Project/test_session_protection.py - Teste do Sistema de Proteção de Sessão

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import logging

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from docs.session_protection import SessionProtectionDialog, SessionProtectionManager, session_protection_manager
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print("Certifique-se de que o módulo session_protection.py está disponível")
    sys.exit(1)


class TestSessionProtectionManager(unittest.TestCase):
    """Testes para o gerenciador de proteção de sessão."""
    
    def setUp(self):
        """Configura o ambiente de teste."""
        self.manager = SessionProtectionManager()
        self.test_connection_id = 123
        self.test_user = "test_user"
        self.test_connected_user = "connected_user"
        
        # Dados de teste para solicitação
        self.test_request_data = {
            "connection_id": self.test_connection_id,
            "connection_name": "Servidor Teste",
            "requesting_user": self.test_user,
            "connected_user": self.test_connected_user,
            "reason": "Teste de funcionalidade do sistema",
            "priority": "normal",
            "contact": "test@example.com",
            "temp_password": "abc123",
            "duration_minutes": 60,
            "expiry_time": (datetime.now() + timedelta(minutes=60)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
    
    def test_register_release_request(self):
        """Testa registro de solicitação de liberação."""
        password = "test123"
        
        # Registra solicitação
        self.manager.register_release_request(password, self.test_request_data)
        
        # Verifica se foi registrada
        self.assertIn(password, self.manager.active_requests)
        self.assertEqual(
            self.manager.active_requests[password]["connection_id"], 
            self.test_connection_id
        )
        
        print("✅ Teste de registro de solicitação: OK")
    
    def test_validate_release_password_success(self):
        """Testa validação bem-sucedida de senha de liberação."""
        password = "valid123"
        
        # Registra primeiro
        self.manager.register_release_request(password, self.test_request_data)
        
        # Valida
        result = self.manager.validate_release_password(
            password, 
            self.test_connection_id, 
            self.test_user
        )
        
        # Verifica resultado
        self.assertTrue(result["valid"])
        self.assertEqual(result["priority"], "normal")
        
        # Verifica se foi removida após uso
        self.assertNotIn(password, self.manager.active_requests)
        
        print("✅ Teste de validação de senha válida: OK")
    
    def test_validate_release_password_wrong_user(self):
        """Testa validação com usuário incorreto."""
        password = "test456"
        
        # Registra solicitação
        self.manager.register_release_request(password, self.test_request_data)
        
        # Tenta validar com usuário incorreto
        result = self.manager.validate_release_password(
            password, 
            self.test_connection_id, 
            "wrong_user"
        )
        
        # Verifica que falhou
        self.assertFalse(result["valid"])
        self.assertIn("Apenas o solicitante", result["reason"])
        
        print("✅ Teste de validação com usuário incorreto: OK")
    
    def test_validate_release_password_wrong_connection(self):
        """Testa validação com conexão incorreta."""
        password = "test789"
        
        # Registra solicitação
        self.manager.register_release_request(password, self.test_request_data)
        
        # Tenta validar com conexão incorreta
        result = self.manager.validate_release_password(
            password, 
            999,  # ID diferente
            self.test_user
        )
        
        # Verifica que falhou
        self.assertFalse(result["valid"])
        self.assertIn("não válida para este servidor", result["reason"])
        
        print("✅ Teste de validação com conexão incorreta: OK")
    
    def test_emergency_forced_release(self):
        """Testa liberação forçada por emergência."""
        emergency_data = self.test_request_data.copy()
        emergency_data["priority"] = "emergency"
        
        # Marca para liberação forçada
        self.manager.mark_for_forced_release(self.test_connection_id, emergency_data)
        
        # Verifica se está marcada
        self.assertTrue(
            self.manager.is_connection_force_released(self.test_connection_id)
        )
        
        # Remove marca
        self.manager.clear_force_release(self.test_connection_id)
        
        # Verifica se foi removida
        self.assertFalse(
            self.manager.is_connection_force_released(self.test_connection_id)
        )
        
        print("✅ Teste de liberação forçada por emergência: OK")
    
    def test_voluntary_release(self):
        """Testa liberação voluntária de sessão."""
        password = "voluntary123"
        
        # Registra solicitação
        self.manager.register_release_request(password, self.test_request_data)
        
        # Usuário conectado libera voluntariamente
        result = self.manager.release_session_voluntarily(
            self.test_connected_user,
            self.test_connection_id
        )
        
        # Verifica sucesso
        self.assertTrue(result)
        
        # Verifica que solicitação foi removida
        self.assertNotIn(password, self.manager.active_requests)
        
        print("✅ Teste de liberação voluntária: OK")
    
    def test_expired_request_cleanup(self):
        """Testa limpeza de solicitações expiradas."""
        password = "expired123"
        
        # Cria solicitação expirada
        expired_data = self.test_request_data.copy()
        expired_data["expiry_time"] = (datetime.now() - timedelta(minutes=5)).isoformat()
        
        # Registra
        self.manager.register_release_request(password, expired_data)
        
        # Força limpeza
        self.manager.force_cleanup_expired()
        
        # Verifica que foi removida
        self.assertNotIn(password, self.manager.active_requests)
        
        print("✅ Teste de limpeza de solicitações expiradas: OK")
    
    def test_get_pending_requests_for_user(self):
        """Testa obtenção de solicitações pendentes para usuário."""
        password1 = "pending1"
        password2 = "pending2"
        
        # Registra duas solicitações para o mesmo usuário conectado
        self.manager.register_release_request(password1, self.test_request_data)
        
        data2 = self.test_request_data.copy()
        data2["requesting_user"] = "other_user"
        self.manager.register_release_request(password2, data2)
        
        # Obtém pendentes para o usuário conectado
        pending = self.manager.get_pending_requests_for_user(self.test_connected_user)
        
        # Verifica que encontrou ambas
        self.assertEqual(len(pending), 2)
        
        # Verifica que senhas foram mascaradas
        for request in pending:
            self.assertIn("password_masked", request)
            self.assertNotIn("temp_password", request)
        
        print("✅ Teste de obtenção de solicitações pendentes: OK")


class TestSessionProtectionIntegration(unittest.TestCase):
    """Testes de integração do sistema de proteção."""
    
    def setUp(self):
        """Configura ambiente de teste."""
        # Limpa o gerenciador global
        session_protection_manager.cleanup_all_requests()
    
    def test_complete_protection_workflow(self):
        """Testa fluxo completo de proteção de sessão."""
        
        # 1. Usuário solicita liberação
        password = "workflow123"
        request_data = {
            "connection_id": 456,
            "connection_name": "Servidor Produção",
            "requesting_user": "user_a",
            "connected_user": "user_b",
            "reason": "Manutenção crítica necessária",
            "priority": "urgent",
            "contact": "user_a@company.com",
            "temp_password": password,
            "duration_minutes": 15,
            "expiry_time": (datetime.now() + timedelta(minutes=15)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        # 2. Registra a solicitação
        session_protection_manager.register_release_request(password, request_data)
        
        # 3. Verifica se está pendente
        pending = session_protection_manager.get_pending_requests_for_user("user_b")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["priority"], "urgent")
        
        # 4. Usuário solicitante usa a senha
        validation = session_protection_manager.validate_release_password(
            password, 456, "user_a"
        )
        self.assertTrue(validation["valid"])
        
        # 5. Verifica que não há mais solicitações pendentes
        pending_after = session_protection_manager.get_pending_requests_for_user("user_b")
        self.assertEqual(len(pending_after), 0)
        
        print("✅ Teste de fluxo completo de proteção: OK")
    
    def test_multiple_users_same_server(self):
        """Testa múltiplas solicitações para o mesmo servidor."""
        
        connection_id = 789
        
        # Solicitações de diferentes usuários
        requests = [
            {
                "password": "user1_pass",
                "user": "user_1",
                "priority": "normal"
            },
            {
                "password": "user2_pass", 
                "user": "user_2",
                "priority": "urgent"
            },
            {
                "password": "user3_pass",
                "user": "user_3", 
                "priority": "emergency"
            }
        ]
        
        # Registra todas as solicitações
        for req in requests:
            request_data = {
                "connection_id": connection_id,
                "connection_name": "Servidor Compartilhado",
                "requesting_user": req["user"],
                "connected_user": "current_user",
                "reason": f"Solicitação do {req['user']}",
                "priority": req["priority"],
                "contact": f"{req['user']}@company.com",
                "temp_password": req["password"],
                "duration_minutes": 30,
                "expiry_time": (datetime.now() + timedelta(minutes=30)).isoformat(),
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
            session_protection_manager.register_release_request(req["password"], request_data)
        
        # Verifica que todas estão pendentes
        pending = session_protection_manager.get_pending_requests_for_user("current_user")
        self.assertEqual(len(pending), 3)
        
        # Verifica prioridades diferentes
        priorities = [req["priority"] for req in pending]
        self.assertIn("normal", priorities)
        self.assertIn("urgent", priorities)
        self.assertIn("emergency", priorities)
        
        # Usuário libera voluntariamente
        result = session_protection_manager.release_session_voluntarily(
            "current_user", connection_id
        )
        self.assertTrue(result)
        
        # Verifica que todas foram removidas
        pending_after = session_protection_manager.get_pending_requests_for_user("current_user")
        self.assertEqual(len(pending_after), 0)
        
        print("✅ Teste de múltiplas solicitações para mesmo servidor: OK")


def run_all_tests():
    """Executa todos os testes."""
    print("🔒 Iniciando Testes do Sistema de Proteção de Sessão")
    print("=" * 60)
    
    # Configura logging para os testes
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    # Cria suite de testes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adiciona testes
    suite.addTests(loader.loadTestsFromTestCase(TestSessionProtectionManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionProtectionIntegration))
    
    # Executa testes
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # Mostra resultado final
    print("\n" + "=" * 60)
    print("📊 RESULTADO DOS TESTES")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total_tests - failures - errors
    
    print(f"✅ Sucessos: {successes}/{total_tests}")
    print(f"❌ Falhas: {failures}/{total_tests}")
    print(f"🔥 Erros: {errors}/{total_tests}")
    
    if failures > 0:
        print("\n❌ FALHAS:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if errors > 0:
        print("\n🔥 ERROS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if failures == 0 and errors == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema de proteção funcionando corretamente.")
        print("\n📋 Funcionalidades testadas:")
        print("  ✅ Registro de solicitações de liberação")
        print("  ✅ Validação de senhas temporárias")
        print("  ✅ Liberação forçada por emergência") 
        print("  ✅ Liberação voluntária de sessão")
        print("  ✅ Limpeza de solicitações expiradas")
        print("  ✅ Múltiplas solicitações por servidor")
        print("  ✅ Fluxo completo de proteção")
    else:
        print(f"\n⚠️ {failures + errors} teste(s) falharam. Verificar implementação.")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
# WATS_Project/test_session_protection_correct.py - Teste da Implementação CORRETA

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import logging

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from docs.session_protection import CreateSessionProtectionDialog, ValidateSessionPasswordDialog, SessionProtectionManager, session_protection_manager
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print("Certifique-se de que o módulo session_protection.py está disponível")
    sys.exit(1)


class TestSessionProtectionManagerCorrect(unittest.TestCase):
    """Testes para o gerenciador de proteção de sessão - IMPLEMENTAÇÃO CORRETA."""
    
    def setUp(self):
        """Configura o ambiente de teste."""
        self.manager = SessionProtectionManager()
        self.test_connection_id = 123
        self.test_user_a = "user_a_connected"  # Usuário conectado
        self.test_user_b = "user_b_requesting"  # Usuário que quer acessar
        self.test_password = "senha123"
        
        # Dados de teste para proteção
        self.test_protection_data = {
            "connection_id": self.test_connection_id,
            "connection_name": "Servidor Teste",
            "protected_by": self.test_user_a,
            "password": self.test_password,
            "duration_minutes": 60,
            "expiry_time": (datetime.now() + timedelta(minutes=60)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "notes": "Trabalho crítico em andamento",
            "status": "active"
        }
    
    def test_activate_session_protection(self):
        """Testa ativação de proteção pelo usuário conectado."""
        
        # User A (conectado) ativa proteção
        self.manager.activate_session_protection(
            self.test_connection_id,
            self.test_password,
            self.test_protection_data
        )
        
        # Verifica se foi ativada
        self.assertTrue(self.manager.is_session_protected(self.test_connection_id))
        
        # Verifica informações da proteção
        protection_info = self.manager.get_session_protection_info(self.test_connection_id)
        self.assertIsNotNone(protection_info)
        self.assertEqual(protection_info["protected_by"], self.test_user_a)
        
        print("✅ Teste de ativação de proteção: OK")
    
    def test_validate_correct_password(self):
        """Testa validação com senha CORRETA."""
        
        # User A ativa proteção
        self.manager.activate_session_protection(
            self.test_connection_id,
            self.test_password,
            self.test_protection_data
        )
        
        # User B tenta acessar com senha CORRETA
        validation = self.manager.validate_session_password(
            self.test_connection_id,
            self.test_password,
            self.test_user_b
        )
        
        # Verifica que foi aceita
        self.assertTrue(validation["valid"])
        self.assertIn("protection_data", validation)
        
        print("✅ Teste de validação com senha correta: OK")
    
    def test_validate_incorrect_password(self):
        """Testa validação com senha INCORRETA."""
        
        # User A ativa proteção
        self.manager.activate_session_protection(
            self.test_connection_id,
            self.test_password,
            self.test_protection_data
        )
        
        # User B tenta acessar com senha INCORRETA
        validation = self.manager.validate_session_password(
            self.test_connection_id,
            "senha_errada",
            self.test_user_b
        )
        
        # Verifica que foi rejeitada
        self.assertFalse(validation["valid"])
        self.assertIn("incorreta", validation["reason"])
        
        print("✅ Teste de validação com senha incorreta: OK")
    
    def test_validate_unprotected_session(self):
        """Testa validação em sessão não protegida."""
        
        # Tenta validar senha em sessão sem proteção
        validation = self.manager.validate_session_password(
            self.test_connection_id,
            self.test_password,
            self.test_user_b
        )
        
        # Verifica que foi rejeitada
        self.assertFalse(validation["valid"])
        self.assertIn("não está protegida", validation["reason"])
        
        print("✅ Teste de validação em sessão não protegida: OK")
    
    def test_remove_protection_by_creator(self):
        """Testa remoção de proteção pelo criador."""
        
        # User A ativa proteção
        self.manager.activate_session_protection(
            self.test_connection_id,
            self.test_password,
            self.test_protection_data
        )
        
        # User A remove a proteção
        success = self.manager.remove_session_protection(
            self.test_connection_id,
            self.test_user_a
        )
        
        # Verifica que foi removida
        self.assertTrue(success)
        self.assertFalse(self.manager.is_session_protected(self.test_connection_id))
        
        print("✅ Teste de remoção de proteção pelo criador: OK")
    
    def test_remove_protection_unauthorized(self):
        """Testa tentativa de remoção por usuário não autorizado."""
        
        # User A ativa proteção
        self.manager.activate_session_protection(
            self.test_connection_id,
            self.test_password,
            self.test_protection_data
        )
        
        # User B tenta remover (não autorizado)
        success = self.manager.remove_session_protection(
            self.test_connection_id,
            self.test_user_b
        )
        
        # Verifica que foi rejeitada
        self.assertFalse(success)
        self.assertTrue(self.manager.is_session_protected(self.test_connection_id))
        
        print("✅ Teste de remoção não autorizada: OK")
    
    def test_get_user_protected_sessions(self):
        """Testa obtenção de sessões protegidas por usuário."""
        
        # User A ativa proteção em duas conexões
        connection_2 = 456
        protection_data_2 = self.test_protection_data.copy()
        protection_data_2["connection_id"] = connection_2
        protection_data_2["connection_name"] = "Servidor 2"
        
        self.manager.activate_session_protection(
            self.test_connection_id,
            self.test_password,
            self.test_protection_data
        )
        
        self.manager.activate_session_protection(
            connection_2,
            "outra_senha",
            protection_data_2
        )
        
        # Obtém sessões protegidas pelo User A
        user_sessions = self.manager.get_user_protected_sessions(self.test_user_a)
        
        # Verifica que encontrou ambas
        self.assertEqual(len(user_sessions), 2)
        
        # Verifica que senhas foram removidas por segurança
        for session in user_sessions:
            self.assertNotIn("password", session)
            self.assertEqual(session["protected_by"], self.test_user_a)
        
        print("✅ Teste de obtenção de sessões protegidas: OK")
    
    def test_expired_protection_cleanup(self):
        """Testa limpeza de proteções expiradas."""
        
        # Cria proteção expirada
        expired_data = self.test_protection_data.copy()
        expired_data["expiry_time"] = (datetime.now() - timedelta(minutes=5)).isoformat()
        
        self.manager.activate_session_protection(
            self.test_connection_id,
            self.test_password,
            expired_data
        )
        
        # Força limpeza
        self.manager.force_cleanup_expired()
        
        # Verifica que foi removida
        self.assertFalse(self.manager.is_session_protected(self.test_connection_id))
        
        print("✅ Teste de limpeza de proteções expiradas: OK")


class TestSessionProtectionWorkflow(unittest.TestCase):
    """Testes de fluxo completo - IMPLEMENTAÇÃO CORRETA."""
    
    def setUp(self):
        """Configura ambiente de teste."""
        # Limpa o gerenciador global
        session_protection_manager.cleanup_all_protections()
    
    def test_complete_protection_workflow(self):
        """Testa fluxo completo correto de proteção."""
        
        connection_id = 789
        user_a = "usuario_conectado"
        user_b = "usuario_solicitante"
        password = "minha_senha_123"
        
        # 1. User A (conectado) cria proteção
        protection_data = {
            "connection_id": connection_id,
            "connection_name": "Servidor Produção",
            "protected_by": user_a,
            "password": password,
            "duration_minutes": 30,
            "expiry_time": (datetime.now() + timedelta(minutes=30)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "notes": "Manutenção crítica",
            "status": "active"
        }
        
        session_protection_manager.activate_session_protection(
            connection_id,
            password,
            protection_data
        )
        
        # 2. Verifica que está protegida
        self.assertTrue(session_protection_manager.is_session_protected(connection_id))
        
        # 3. User B tenta acessar com senha ERRADA
        validation_wrong = session_protection_manager.validate_session_password(
            connection_id,
            "senha_errada",
            user_b
        )
        self.assertFalse(validation_wrong["valid"])
        
        # 4. User B tenta acessar com senha CORRETA
        validation_correct = session_protection_manager.validate_session_password(
            connection_id,
            password,
            user_b
        )
        self.assertTrue(validation_correct["valid"])
        
        # 5. User A remove a proteção
        removal_success = session_protection_manager.remove_session_protection(
            connection_id,
            user_a
        )
        self.assertTrue(removal_success)
        
        # 6. Verifica que não está mais protegida
        self.assertFalse(session_protection_manager.is_session_protected(connection_id))
        
        print("✅ Teste de fluxo completo correto: OK")
    
    def test_multiple_protected_sessions(self):
        """Testa múltiplas sessões protegidas por diferentes usuários."""
        
        # Três usuários protegem diferentes sessões
        sessions = [
            {"id": 101, "user": "user_1", "password": "senha_1", "server": "Servidor A"},
            {"id": 102, "user": "user_2", "password": "senha_2", "server": "Servidor B"},
            {"id": 103, "user": "user_3", "password": "senha_3", "server": "Servidor C"}
        ]
        
        # Cada usuário cria sua proteção
        for session in sessions:
            protection_data = {
                "connection_id": session["id"],
                "connection_name": session["server"],
                "protected_by": session["user"],
                "password": session["password"],
                "duration_minutes": 60,
                "expiry_time": (datetime.now() + timedelta(minutes=60)).isoformat(),
                "created_at": datetime.now().isoformat(),
                "notes": f"Proteção do {session['user']}",
                "status": "active"
            }
            
            session_protection_manager.activate_session_protection(
                session["id"],
                session["password"],
                protection_data
            )
        
        # Verifica que todas estão protegidas
        for session in sessions:
            self.assertTrue(session_protection_manager.is_session_protected(session["id"]))
        
        # Cada usuário só pode remover sua própria proteção
        for i, session in enumerate(sessions):
            # Usuário correto remove
            success = session_protection_manager.remove_session_protection(
                session["id"],
                session["user"]
            )
            self.assertTrue(success)
            
            # Verifica que foi removida
            self.assertFalse(session_protection_manager.is_session_protected(session["id"]))
        
        print("✅ Teste de múltiplas sessões protegidas: OK")
    
    def test_cross_password_validation(self):
        """Testa que senhas não funcionam entre servidores diferentes."""
        
        # Dois servidores com proteções diferentes
        server_1 = {"id": 201, "password": "senha_servidor_1"}
        server_2 = {"id": 202, "password": "senha_servidor_2"}
        
        user_a = "user_admin"
        user_b = "user_guest"
        
        # Protege ambos os servidores
        for server in [server_1, server_2]:
            protection_data = {
                "connection_id": server["id"],
                "connection_name": f"Servidor {server['id']}",
                "protected_by": user_a,
                "password": server["password"],
                "duration_minutes": 60,
                "expiry_time": (datetime.now() + timedelta(minutes=60)).isoformat(),
                "created_at": datetime.now().isoformat(),
                "notes": "Proteção cruzada",
                "status": "active"
            }
            
            session_protection_manager.activate_session_protection(
                server["id"],
                server["password"],
                protection_data
            )
        
        # Tenta usar senha do servidor 1 no servidor 2 (deve falhar)
        validation_cross = session_protection_manager.validate_session_password(
            server_2["id"],
            server_1["password"],
            user_b
        )
        self.assertFalse(validation_cross["valid"])
        
        # Usa senha correta para cada servidor
        for server in [server_1, server_2]:
            validation_correct = session_protection_manager.validate_session_password(
                server["id"],
                server["password"],
                user_b
            )
            self.assertTrue(validation_correct["valid"])
        
        print("✅ Teste de validação cruzada de senhas: OK")


def run_correct_tests():
    """Executa todos os testes da implementação correta."""
    print("🔒 Iniciando Testes da Implementação CORRETA")
    print("=" * 60)
    print("📋 FLUXO CORRETO:")
    print("  1. User A (conectado) cria proteção com senha")
    print("  2. User B tenta acessar e precisa da senha do User A")
    print("  3. User A controla quem pode acessar")
    print("=" * 60)
    
    # Configura logging para os testes
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    # Cria suite de testes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adiciona testes
    suite.addTests(loader.loadTestsFromTestCase(TestSessionProtectionManagerCorrect))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionProtectionWorkflow))
    
    # Executa testes
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # Mostra resultado final
    print("\n" + "=" * 60)
    print("📊 RESULTADO DOS TESTES CORRETOS")
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
        print("\n🎉 TODOS OS TESTES PASSARAM! Implementação correta funcionando!")
        print("\n📋 Funcionalidades testadas (FLUXO CORRETO):")
        print("  ✅ User A cria proteção com senha")
        print("  ✅ User B valida senha do User A para acessar")
        print("  ✅ Validação de senhas corretas/incorretas")
        print("  ✅ Remoção de proteção apenas pelo criador")
        print("  ✅ Múltiplas sessões protegidas simultaneamente")
        print("  ✅ Limpeza automática de proteções expiradas")
        print("  ✅ Senhas específicas por servidor")
        print("\n🔒 CONTROLE TOTAL: User conectado decide quem acessa!")
    else:
        print(f"\n⚠️ {failures + errors} teste(s) falharam. Verificar implementação.")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_correct_tests()
    sys.exit(0 if success else 1)
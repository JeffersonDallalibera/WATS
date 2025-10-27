#!/usr/bin/env python3
# WATS_Project/test_demo_mode.py

"""
Script de teste para verificar se o modo demo está funcionando corretamente.
Execute este script para testar o mock service sem iniciar a interface gráfica.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_demo_configuration():
    """Testa se o modo demo está configurado corretamente."""
    print("=== TESTE DE CONFIGURAÇÃO DO MODO DEMO ===\n")
    
    # Força modo demo
    os.environ['WATS_DEMO_MODE'] = 'true'
    
    try:
        from src.wats.config import is_demo_mode, Settings
        
        print(f"✅ is_demo_mode(): {is_demo_mode()}")
        
        if not is_demo_mode():
            print("❌ ERRO: Modo demo não está ativo!")
            return False
            
        print("✅ Modo demo ativado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO ao importar configuração: {e}")
        return False

def test_mock_service():
    """Testa o serviço de dados simulados."""
    print("\n=== TESTE DO MOCK SERVICE ===\n")
    
    try:
        from docs.mock_data_service import get_mock_service
        
        mock = get_mock_service()
        
        # Testa usuários
        users = mock.get_all_users()
        print(f"✅ Usuários simulados: {len(users)} encontrados")
        for user in users[:2]:  # Mostra apenas os primeiros 2
            print(f"   - {user['username']} ({user['email']})")
        
        # Testa grupos
        groups = mock.get_all_groups()
        print(f"✅ Grupos simulados: {len(groups)} encontrados")
        for group in groups[:2]:
            print(f"   - {group['name']}")
        
        # Testa conexões
        connections = mock.get_all_connections()
        print(f"✅ Conexões simuladas: {len(connections)} encontradas")
        for conn in connections[:2]:
            print(f"   - {conn['name']} ({conn['host']})")
        
        # Testa logs
        logs = mock.get_logs(limit=3)
        print(f"✅ Logs simulados: {len(logs)} encontrados")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO no mock service: {e}")
        return False

def test_database_manager():
    """Testa o DatabaseManager em modo demo."""
    print("\n=== TESTE DO DATABASE MANAGER ===\n")
    
    try:
        from src.wats.config import Settings
        from src.wats.db.database_manager import DatabaseManager
        
        settings = Settings()
        db_manager = DatabaseManager(settings)
        
        print(f"✅ DatabaseManager criado (demo: {db_manager.is_demo})")
        
        # Testa cursors (devem retornar None em modo demo)
        cursor = db_manager.get_cursor()
        print(f"✅ get_cursor() retornou: {cursor} (esperado: None)")
        
        conn = db_manager.get_transactional_connection()
        print(f"✅ get_transactional_connection() retornou: {conn} (esperado: None)")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO no DatabaseManager: {e}")
        return False

def test_user_repository():
    """Testa o UserRepository com modo demo."""
    print("\n=== TESTE DO USER REPOSITORY ===\n")
    
    try:
        from src.wats.config import Settings
        from src.wats.db.database_manager import DatabaseManager
        from src.wats.db.repositories.user_repository import UserRepository
        
        settings = Settings()
        db_manager = DatabaseManager(settings)
        user_repo = UserRepository(db_manager)
        
        # Testa listagem de usuários
        users = user_repo.admin_get_all_users()
        print(f"✅ admin_get_all_users(): {len(users)} usuários")
        for user in users[:2]:
            print(f"   - ID: {user[0]}, Nome: {user[1]}, Ativo: {user[2]}, Admin: {user[3]}")
        
        # Testa detalhes de usuário
        if users:
            user_id = users[0][0]
            details = user_repo.admin_get_user_details(user_id)
            if details:
                print(f"✅ admin_get_user_details({user_id}):")
                print(f"   - Nome: {details['nome']}")
                print(f"   - Email: {details['email']}")
                print(f"   - Ativo: {details['is_active']}")
                print(f"   - Admin: {details['is_admin']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO no UserRepository: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_admin_authentication():
    """Testa a autenticação do admin em modo demo."""
    print("\n=== TESTE DE AUTENTICAÇÃO ADMIN ===\n")
    
    try:
        from src.wats.config import Settings
        from src.wats.db.database_manager import DatabaseManager
        from src.wats.db.repositories.user_repository import UserRepository
        from src.wats.utils import hash_password_md5
        
        settings = Settings()
        db_manager = DatabaseManager(settings)
        user_repo = UserRepository(db_manager)
        
        # Testa obtenção do hash da senha admin
        admin_hash = user_repo.get_admin_password_hash()
        print(f"✅ get_admin_password_hash(): {admin_hash}")
        
        # Testa se a senha "admin123" funciona
        test_password = "admin123"
        test_hash = hash_password_md5(test_password)
        print(f"✅ Hash de '{test_password}': {test_hash}")
        
        if admin_hash == test_hash:
            print(f"✅ AUTENTICAÇÃO OK: Senha '{test_password}' válida para admin em modo demo")
        else:
            print(f"❌ ERRO: Senha '{test_password}' não confere com hash do admin")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO na autenticação admin: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes."""
    print("WATS - TESTE DO MODO DEMO")
    print("=" * 50)
    
    tests = [
        test_demo_configuration,
        test_mock_service,
        test_database_manager,
        test_user_repository,
        test_admin_authentication
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ ERRO no teste {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("RESUMO DOS TESTES:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\nResultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Modo demo está funcionando.")
        print("\nPara usar o modo demo:")
        print("1. Defina WATS_DEMO_MODE=true")
        print("2. Execute o WATS normalmente")
        print("3. Acesse os Admin Panels para ver dados simulados")
    else:
        print("❌ Alguns testes falharam. Verifique os erros acima.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
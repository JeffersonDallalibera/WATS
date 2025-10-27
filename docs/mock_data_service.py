# WATS_Project/wats_app/mock_data_service.py

"""
Serviço de dados simulados para modo demo do WATS.
Permite testar os Admin Panels sem conexão com banco de dados.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

class MockDataService:
    """Serviço que simula dados do banco para modo demo."""
    
    def __init__(self):
        self._generate_mock_data()
        logger.info("MockDataService inicializado com dados simulados")
    
    def _generate_mock_data(self):
        """Gera dados simulados para demonstração."""
        
        # Dados de usuários simulados
        self.mock_users = [
            {
                'id': 1,
                'username': 'admin',
                'full_name': 'Administrador',
                'email': 'admin@empresa.com',
                'is_admin': True,
                'created_at': datetime.now() - timedelta(days=30),
                'last_login': datetime.now() - timedelta(hours=2),
                'status': 'active'
            },
            {
                'id': 2,
                'username': 'usuario1',
                'full_name': 'João Silva',
                'email': 'joao.silva@empresa.com',
                'is_admin': False,
                'created_at': datetime.now() - timedelta(days=25),
                'last_login': datetime.now() - timedelta(hours=5),
                'status': 'active'
            },
            {
                'id': 3,
                'username': 'usuario2',
                'full_name': 'Maria Santos',
                'email': 'maria.santos@empresa.com',
                'is_admin': False,
                'created_at': datetime.now() - timedelta(days=20),
                'last_login': datetime.now() - timedelta(days=1),
                'status': 'active'
            },
            {
                'id': 4,
                'username': 'suporte',
                'full_name': 'Equipe Suporte',
                'email': 'suporte@empresa.com',
                'is_admin': False,
                'created_at': datetime.now() - timedelta(days=15),
                'last_login': datetime.now() - timedelta(hours=8),
                'status': 'inactive'
            }
        ]
        
        # Dados de grupos simulados
        self.mock_groups = [
            {
                'id': 1,
                'name': 'Administradores',
                'description': 'Grupo de administradores do sistema',
                'created_at': datetime.now() - timedelta(days=30),
                'member_count': 1
            },
            {
                'id': 2,
                'name': 'Usuários Finais',
                'description': 'Grupo de usuários finais do sistema',
                'created_at': datetime.now() - timedelta(days=25),
                'member_count': 2
            },
            {
                'id': 3,
                'name': 'Suporte Técnico',
                'description': 'Equipe de suporte técnico',
                'created_at': datetime.now() - timedelta(days=20),
                'member_count': 1
            }
        ]
        
        # Dados de conexões simuladas
        self.mock_connections = [
            {
                'id': 1,
                'name': 'Servidor Produção',
                'host': '192.168.1.100',
                'port': 3389,
                'username': 'admin',
                'domain': 'EMPRESA',
                'created_at': datetime.now() - timedelta(days=30),
                'last_used': datetime.now() - timedelta(hours=2),
                'status': 'active',
                'connection_count': 45
            },
            {
                'id': 2,
                'name': 'Servidor Desenvolvimento',
                'host': '192.168.1.101',
                'port': 3389,
                'username': 'dev',
                'domain': 'EMPRESA',
                'created_at': datetime.now() - timedelta(days=25),
                'last_used': datetime.now() - timedelta(days=1),
                'status': 'active',
                'connection_count': 12
            },
            {
                'id': 3,
                'name': 'Servidor Backup',
                'host': '192.168.1.102',
                'port': 3389,
                'username': 'backup',
                'domain': 'EMPRESA',
                'created_at': datetime.now() - timedelta(days=20),
                'last_used': datetime.now() - timedelta(days=5),
                'status': 'inactive',
                'connection_count': 3
            }
        ]
        
        # Dados de logs simulados
        self.mock_logs = []
        for i in range(50):
            self.mock_logs.append({
                'id': i + 1,
                'user_id': random.choice([1, 2, 3]),
                'connection_id': random.choice([1, 2, 3]),
                'action': random.choice(['connect', 'disconnect', 'error', 'login']),
                'details': f'Ação simulada #{i + 1}',
                'timestamp': datetime.now() - timedelta(minutes=random.randint(0, 1440)),
                'ip_address': f'192.168.1.{random.randint(1, 254)}',
                'user_agent': 'WATS Client 1.0'
            })
    
    # Métodos para usuários
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Retorna todos os usuários simulados."""
        return self.mock_users.copy()
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retorna usuário por ID."""
        return next((user for user in self.mock_users if user['id'] == user_id), None)
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simula criação de usuário."""
        new_user = {
            'id': max(user['id'] for user in self.mock_users) + 1,
            'created_at': datetime.now(),
            'last_login': None,
            'status': 'active',
            **user_data
        }
        self.mock_users.append(new_user)
        logger.info(f"[DEMO] Usuário criado: {new_user['username']}")
        return new_user
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """Simula atualização de usuário."""
        user = self.get_user_by_id(user_id)
        if user:
            user.update(user_data)
            logger.info(f"[DEMO] Usuário atualizado: ID {user_id}")
            return True
        return False
    
    def delete_user(self, user_id: int) -> bool:
        """Simula exclusão de usuário."""
        user = self.get_user_by_id(user_id)
        if user:
            self.mock_users.remove(user)
            logger.info(f"[DEMO] Usuário excluído: ID {user_id}")
            return True
        return False
    
    # Métodos para grupos
    def get_all_groups(self) -> List[Dict[str, Any]]:
        """Retorna todos os grupos simulados."""
        return self.mock_groups.copy()
    
    def get_group_by_id(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Retorna grupo por ID."""
        return next((group for group in self.mock_groups if group['id'] == group_id), None)
    
    def create_group(self, group_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simula criação de grupo."""
        new_group = {
            'id': max(group['id'] for group in self.mock_groups) + 1,
            'created_at': datetime.now(),
            'member_count': 0,
            **group_data
        }
        self.mock_groups.append(new_group)
        logger.info(f"[DEMO] Grupo criado: {new_group['name']}")
        return new_group
    
    def update_group(self, group_id: int, group_data: Dict[str, Any]) -> bool:
        """Simula atualização de grupo."""
        group = self.get_group_by_id(group_id)
        if group:
            group.update(group_data)
            logger.info(f"[DEMO] Grupo atualizado: ID {group_id}")
            return True
        return False
    
    def delete_group(self, group_id: int) -> bool:
        """Simula exclusão de grupo."""
        group = self.get_group_by_id(group_id)
        if group:
            self.mock_groups.remove(group)
            logger.info(f"[DEMO] Grupo excluído: ID {group_id}")
            return True
        return False
    
    # Métodos para conexões
    def get_all_connections(self) -> List[Dict[str, Any]]:
        """Retorna todas as conexões simuladas."""
        return self.mock_connections.copy()
    
    def get_connection_by_id(self, connection_id: int) -> Optional[Dict[str, Any]]:
        """Retorna conexão por ID."""
        return next((conn for conn in self.mock_connections if conn['id'] == connection_id), None)
    
    def create_connection(self, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simula criação de conexão."""
        new_connection = {
            'id': max(conn['id'] for conn in self.mock_connections) + 1,
            'created_at': datetime.now(),
            'last_used': None,
            'status': 'active',
            'connection_count': 0,
            **connection_data
        }
        self.mock_connections.append(new_connection)
        logger.info(f"[DEMO] Conexão criada: {new_connection['name']}")
        return new_connection
    
    def update_connection(self, connection_id: int, connection_data: Dict[str, Any]) -> bool:
        """Simula atualização de conexão."""
        connection = self.get_connection_by_id(connection_id)
        if connection:
            connection.update(connection_data)
            logger.info(f"[DEMO] Conexão atualizada: ID {connection_id}")
            return True
        return False
    
    def delete_connection(self, connection_id: int) -> bool:
        """Simula exclusão de conexão."""
        connection = self.get_connection_by_id(connection_id)
        if connection:
            self.mock_connections.remove(connection)
            logger.info(f"[DEMO] Conexão excluída: ID {connection_id}")
            return True
        return False
    
    # Métodos para logs
    def get_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retorna logs simulados com paginação."""
        return self.mock_logs[offset:offset + limit]
    
    def get_logs_count(self) -> int:
        """Retorna total de logs simulados."""
        return len(self.mock_logs)
    
    # Método para testar conexão
    def test_connection(self) -> bool:
        """Simula teste de conexão com banco (sempre retorna True em modo demo)."""
        logger.info("[DEMO] Teste de conexão simulado - OK")
        return True
    
    def get_admin_password_hash(self) -> str:
        """Retorna hash MD5 da senha admin em modo demo."""
        # Hash MD5 de "admin123"
        return "0192023a7bbd73250516f069df18b500"

# Instância global do serviço mock
_mock_service_instance = None

def get_mock_service() -> MockDataService:
    """Retorna a instância singleton do MockDataService."""
    global _mock_service_instance
    if _mock_service_instance is None:
        _mock_service_instance = MockDataService()
    return _mock_service_instance
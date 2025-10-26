# WATS_Project/wats_app/db/db_service.py

"""
Ponto de entrada unificado para todos os serviços de banco de dados.

Em vez de instanciar a antiga classe 'Database', a aplicação deve
instanciar esta classe e usá-la para acessar os repositórios.

Exemplo de uso na UI:
---------------------
from wats_app.core.config import settings
from wats_app.db.db_service import DBService
from wats_app.db.exceptions import DatabaseError

try:
    # Instancia o serviço (que lê as settings)
    db_service = DBService(settings)
    
    # Acessa os métodos através dos repositórios
    user_id, is_admin = db_service.users.get_user_role("meu_usuario")
    conexoes = db_service.connections.select_all("meu_usuario")
    
except DatabaseError as e:
    # A UI agora é responsável por mostrar o erro
    messagebox.showerror("Erro de Banco de Dados", str(e))
    sys.exit(1)
"""

from wats_app.config import Settings
from wats_app.db.database_manager import DatabaseManager
from wats_app.db.repositories.user_repository import UserRepository
from wats_app.db.repositories.group_repository import GroupRepository
from wats_app.db.repositories.connection_repository import ConnectionRepository
from wats_app.db.repositories.log_repository import LogRepository

class DBService:
    """Agrega todos os repositórios de banco de dados."""
    
    def __init__(self, settings: Settings):
        """
        Inicializa o gerenciador de banco de dados e todos os repositórios.
        Lança DatabaseConfigError ou DatabaseConnectionError se falhar.
        """
        # Validate DB configuration explicitly here; Settings no longer raises at import time
        if not getattr(settings, 'has_db_config', lambda: False)():
            from wats_app.db.exceptions import DatabaseConfigError
            raise DatabaseConfigError("Configuração de banco ausente. Verifique as variáveis de ambiente ou o arquivo .env.")

        self.db_manager = DatabaseManager(settings)
        
        # Inicializa os repositórios, injetando o db_manager
        self.users = UserRepository(self.db_manager)
        self.groups = GroupRepository(self.db_manager)
        self.logs = LogRepository(self.db_manager)
        
        # Repositórios com dependências
        self.connections = ConnectionRepository(self.db_manager, self.users)
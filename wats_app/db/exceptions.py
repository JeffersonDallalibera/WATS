# WATS_Project/wats_app/db/exceptions.py

class DatabaseError(Exception):
    """Exceção base para erros de banco de dados."""
    pass

class DatabaseConfigError(DatabaseError):
    """Erro nas configurações ou variáveis de ambiente."""
    pass

class DatabaseConnectionError(DatabaseError):
    """Não foi possível conectar ao banco de dados."""
    pass

class DatabaseQueryError(DatabaseError):
    """Erro ao executar uma query."""
    pass
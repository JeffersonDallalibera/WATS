# WATS_Project/wats_app/db/repositories/base_repository.py
from src.wats.db.database_manager import DatabaseManager


class BaseRepository:
    """Classe base para todos os repositórios."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        # Propriedade para facilitar o acesso ao módulo de driver (pyodbc/psycopg2)
        self.driver_module = db_manager.driver_module

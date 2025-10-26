# WATS_Project/wats_app/db/repositories/group_repository.py
import logging
from typing import List, Optional, Tuple, Dict, Any
from wats_app.db.repositories.base_repository import BaseRepository
from wats_app.db.exceptions import DatabaseQueryError, DatabaseConnectionError

class GroupRepository(BaseRepository):
    """Gerencia operações de Grupos (Grupo_WTS)."""

    def admin_get_all_groups(self) -> List[Tuple]:
        query = "SELECT Gru_Codigo, Gru_Nome FROM Grupo_WTS ORDER BY Gru_Nome"
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query)
                return cursor.fetchall()
        except self.driver_module.Error as e:
            logging.error(f"Admin: Erro ao buscar grupos: {e}")
            raise DatabaseQueryError(f"Admin: Erro ao buscar grupos: {e}")
        return []

    def admin_get_group_details(self, group_id: int) -> Optional[Dict[str, str]]:
        query = f"SELECT Gru_Nome, Gru_Descricao FROM Grupo_WTS WHERE Gru_Codigo = {self.db.PARAM}"
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query, (group_id,))
                result = cursor.fetchone()
                if result: 
                    return {"nome": result[0], "desc": result[1] or ""}
        except self.driver_module.Error as e:
            logging.error(f"Admin: Erro ao buscar detalhes do grupo {group_id}: {e}")
            raise DatabaseQueryError(f"Admin: Erro ao buscar detalhes do grupo: {e}")
        return None

    def admin_create_group(self, nome: str, desc: Optional[str]) -> Tuple[bool, str]:
        query = f"INSERT INTO Grupo_WTS (Gru_Nome, Gru_Descricao) VALUES ({self.db.PARAM}, {self.db.PARAM})"
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query, (nome, desc))
                return True, "Grupo criado."
        except self.driver_module.Error as e:
            logging.error(f"Admin: Erro ao CRIAR grupo: {e}")
            if "UNIQUE KEY" in str(e) or "unique constraint" in str(e): return False, f"Erro: Nome '{nome}' já existe."
            return False, f"Erro DB: {e}"

    def admin_update_group(self, group_id: int, nome: str, desc: Optional[str]) -> Tuple[bool, str]:
        query = f"UPDATE Grupo_WTS SET Gru_Nome = {self.db.PARAM}, Gru_Descricao = {self.db.PARAM} WHERE Gru_Codigo = {self.db.PARAM}"
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query, (nome, desc, group_id))
                return True, "Grupo atualizado."
        except self.driver_module.Error as e:
            logging.error(f"Admin: Erro ao ATUALIZAR grupo: {e}")
            if "UNIQUE KEY" in str(e) or "unique constraint" in str(e): return False, f"Erro: Nome '{nome}' já existe."
            return False, f"Erro DB: {e}"

    def admin_delete_group(self, group_id: int) -> Tuple[bool, str]:
        query = f"DELETE FROM Grupo_WTS WHERE Gru_Codigo = {self.db.PARAM}"
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query, (group_id,))
                return True, "Grupo deletado."
        except self.driver_module.Error as e:
            logging.error(f"Admin: Erro ao DELETAR grupo: {e}")
            if "REFERENCE constraint" in str(e) or "foreign key constraint" in str(e): 
                return False, "Erro: Grupo em uso por conexões ou permissões."
            return False, f"Erro DB: {e}"
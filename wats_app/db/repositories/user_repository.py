# WATS_Project/wats_app/db/repositories/user_repository.py (CORRIGIDO)
import logging
from typing import List, Optional, Tuple, Dict, Any, Set
from wats_app.db.repositories.base_repository import BaseRepository
from wats_app.db.exceptions import DatabaseQueryError, DatabaseConnectionError

class UserRepository(BaseRepository):
    """Gerencia operações de Usuários e Permissões."""

    def get_user_role(self, username: str) -> Tuple[Optional[int], bool]:
        # --- CORREÇÃO: "1" foi trocado por um parâmetro {self.db.PARAM} ---
        query = f"SELECT Usu_Id, Usu_Is_Admin FROM Usuario_Sistema_WTS WHERE Usu_Nome = {self.db.PARAM} AND Usu_Ativo = {self.db.PARAM}"
        
        cursor = self.db.get_cursor()
        if not cursor: return None, False 
        
        try:
            with cursor: 
                # --- CORREÇÃO: Passamos True como o segundo parâmetro ---
                cursor.execute(query, (username, True)) 
                result = cursor.fetchone()
                if result:
                    # --- CORREÇÃO: Usamos bool() para ser seguro ---
                    # bool(1) -> True (SQL Server)
                    # bool(True) -> True (PostgreSQL)
                    return result[0], bool(result[1]) 
        except self.driver_module.Error as e:
            # O erro que você viu será logado aqui
            logging.error(f"Erro ao buscar permissão do usuário {username}: {e}")
        return None, False

    def get_admin_password_hash(self) -> Optional[str]:
        query = f"SELECT Cfg_Valor FROM Config_Sistema_WTS WHERE Cfg_Chave = {self.db.PARAM}"
        
        cursor = self.db.get_cursor()
        if not cursor: return None 
        
        try:
            with cursor: 
                cursor.execute(query, ('ADMIN_PASSWORD',))
                result = cursor.fetchone()
                if result: return result[0]
        except self.driver_module.Error as e:
            logging.error(f"Erro ao buscar senha admin: {e}")
        return None

    def admin_get_all_users(self) -> List[Tuple]:
        query = "SELECT Usu_Id, Usu_Nome, Usu_Ativo, Usu_Is_Admin FROM Usuario_Sistema_WTS ORDER BY Usu_Nome"
        
        cursor = self.db.get_cursor()
        if not cursor: 
            raise DatabaseConnectionError("Falha ao obter cursor.")
            
        try:
            with cursor: 
                cursor.execute(query)
                return cursor.fetchall()
        except self.driver_module.Error as e:
            logging.error(f"Admin: Erro ao buscar usuários: {e}")
            raise DatabaseQueryError(f"Admin: Erro ao buscar usuários: {e}")
        return []

    def admin_get_user_details(self, user_id: int) -> Optional[Dict[str, Any]]:
        query_user = f"SELECT Usu_Nome, Usu_Email, Usu_Ativo, Usu_Is_Admin FROM Usuario_Sistema_WTS WHERE Usu_Id = {self.db.PARAM}"
        query_groups = f"SELECT Gru_Codigo FROM Permissao_Grupo_WTS WHERE Usu_Id = {self.db.PARAM}"
        
        cursor = self.db.get_cursor()
        if not cursor: 
            raise DatabaseConnectionError("Falha ao obter cursor.")

        try:
            with cursor: 
                cursor.execute(query_user, (user_id,))
                user_result = cursor.fetchone()
                if not user_result: return None
                
                user_details = {
                    "nome": user_result[0], "email": user_result[1] or "",
                    "is_active": user_result[2], "is_admin": user_result[3],
                    "grupos": set()
                }
                
                cursor.execute(query_groups, (user_id,))
                group_results = cursor.fetchall()
                for row in group_results: 
                    user_details["grupos"].add(row[0])
                return user_details
        except self.driver_module.Error as e:
            logging.error(f"Admin: Erro ao buscar detalhes do usuário {user_id}: {e}")
            raise DatabaseQueryError(f"Admin: Erro ao buscar detalhes: {e}")
        return None

    def admin_create_user(self, username: str, email: str, is_admin: bool, is_active: bool, group_ids: List[int]) -> Tuple[bool, str]:
        conn = self.db.get_transactional_connection()
        if not conn: return False, "Falha ao conectar."
        
        q_create = f"""
            INSERT INTO Usuario_Sistema_WTS (Usu_Nome, Usu_Email, Usu_Ativo, Usu_Is_Admin) 
            VALUES ({self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM})
        """
        params_create = (username, email or None, is_active, is_admin)
        
        try:
            with conn.cursor() as cursor:
                new_user_id = None
                
                if self.db.db_type == 'sqlserver':
                    cursor.execute(q_create, params_create)
                    new_user_id = cursor.execute(self.db.IDENTITY_QUERY).fetchone()[0]
                elif self.db.db_type == 'postgresql':
                    q_create_pg = q_create + " RETURNING Usu_Id"
                    cursor.execute(q_create_pg, params_create)
                    new_user_id = cursor.fetchone()[0]

                if new_user_id and group_ids:
                    q_groups = f"INSERT INTO Permissao_Grupo_WTS (Usu_Id, Gru_Codigo) VALUES ({self.db.PARAM}, {self.db.PARAM})"
                    
                    # --- CORREÇÃO AQUI ---
                    # Removemos a lógica if/else. O executemany padrão funciona para ambos.
                    params_groups = [(new_user_id, gid) for gid in group_ids]
                    cursor.executemany(q_groups, params_groups)
                    # --- FIM DA CORREÇÃO ---
                        
                conn.commit()
                return True, "Usuário criado."
        except self.driver_module.Error as e:
            conn.rollback()
            logging.error(f"Admin: Erro ao CRIAR usuário: {e}")
            if "UNIQUE KEY" in str(e) or "unique constraint" in str(e): return False, f"Erro: Nome '{username}' já existe."
            return False, f"Erro DB: {e}"
        except Exception as ex:
            conn.rollback()
            logging.error(f"Admin: Erro inesperado ao CRIAR usuário: {ex}")
            return False, f"Erro: {ex}"

    def admin_update_user(self, user_id: int, username: str, email: str, is_admin: bool, is_active: bool, group_ids: List[int]) -> Tuple[bool, str]:
        conn = self.db.get_transactional_connection()
        if not conn: return False, "Falha ao conectar."
        
        q_update = f"UPDATE Usuario_Sistema_WTS SET Usu_Nome = {self.db.PARAM}, Usu_Email = {self.db.PARAM}, Usu_Ativo = {self.db.PARAM}, Usu_Is_Admin = {self.db.PARAM} WHERE Usu_Id = {self.db.PARAM}"
        q_delete = f"DELETE FROM Permissao_Grupo_WTS WHERE Usu_Id = {self.db.PARAM}"
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(q_update, (username, email or None, is_active, is_admin, user_id))
                cursor.execute(q_delete, (user_id,))
                
                if group_ids:
                    q_insert = f"INSERT INTO Permissao_Grupo_WTS (Usu_Id, Gru_Codigo) VALUES ({self.db.PARAM}, {self.db.PARAM})"
                    
                    # --- CORREÇÃO AQUI ---
                    # Removemos a lógica if/else. O executemany padrão funciona para ambos.
                    params_groups = [(user_id, gid) for gid in group_ids]
                    cursor.executemany(q_insert, params_groups)
                    # --- FIM DA CORREÇÃO ---

                conn.commit()
                return True, "Usuário atualizado."
        except self.driver_module.Error as e:
            conn.rollback()
            logging.error(f"Admin: Erro ao ATUALIZAR usuário: {e}")
            if "UNIQUE KEY" in str(e) or "unique constraint" in str(e): return False, f"Erro: Nome '{username}' já existe."
            return False, f"Erro DB: {e}"
        except Exception as ex:
            conn.rollback()
            # O erro que você viu ("...more than one '%s' placeholder") será capturado aqui
            logging.error(f"Admin: Erro inesperado ao ATUALIZAR usuário: {ex}")
            return False, f"Erro: {ex}"
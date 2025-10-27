# WATS_Project/wats_app/db/repositories/connection_repository.py
import logging
from typing import List, Optional, Tuple, Dict, Any
from src.wats.db.database_manager import DatabaseManager
from src.wats.db.repositories.base_repository import BaseRepository
from src.wats.db.exceptions import DatabaseQueryError, DatabaseConnectionError

class ConnectionRepository(BaseRepository):
    """Gerencia operações de Conexões (Conexao_WTS)."""

    def __init__(self, db_manager: DatabaseManager, user_repo: 'UserRepository'):
        super().__init__(db_manager)
        self.user_repo = user_repo # Dependência para pegar permissões

    def select_all(self, username: str) -> List[Any]:
        user_id, is_admin = self.user_repo.get_user_role(username)
        
        # Dialeto: ISNULL -> COALESCE
        base_query = f"""
            SELECT
                Con.Con_Codigo, Con.Con_IP, Con.Con_Nome, Con.Con_Usuario, Con.Con_Senha,
                Gru.Gru_Nome, {self.db.ISNULL}(Uco.Usu_Nome, '') AS Usu_Nome, NULL AS Usu_Dat_Conexao,
                {self.db.ISNULL}(Con.Extra, '') AS Extra, con.con_particularidade,
                {self.db.ISNULL}(C2.con_cliente, '') AS con_cliente,
                Con.con_tipo
            FROM Conexao_WTS Con
            LEFT JOIN Grupo_WTS Gru ON Con.Gru_Codigo = Gru.Gru_Codigo
            LEFT JOIN (
                SELECT Con_Codigo,
                    (CASE
                        WHEN MIN(Usu_Nome) = MAX(Usu_Nome) THEN MIN(Usu_Nome)
                        ELSE MIN(Usu_Nome) || '|' || MAX(Usu_Nome) -- PG usa || para concatenar
                    END) AS Usu_Nome
                FROM usuario_conexao_wts
                GROUP BY Con_Codigo
            ) Uco ON Con.Con_Codigo = Uco.Con_Codigo
            LEFT JOIN conexao_wts C2 ON Con.Con_Codigo = C2.Con_Codigo
        """
        # Ajuste específico para SQL Server (que não usa ||)
        if self.db.db_type == 'sqlserver':
             base_query = base_query.replace("|| '|' ||", "+ '|' +")
             
        where_clause = ""
        params = []
        if not is_admin:
            if user_id is None: return []
            where_clause = f"WHERE EXISTS (SELECT 1 FROM Permissao_Grupo_WTS p WHERE p.Usu_Id = {self.db.PARAM} AND p.Gru_Codigo = Con.Gru_Codigo)"
            params.append(user_id)
            
        order_clause = f"ORDER BY {self.db.ISNULL}(Gru.Gru_Nome, Con.Con_Nome), Con.Con_Nome"
        query = f"{base_query} {where_clause} {order_clause}"
        
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query, tuple(params))
                return cursor.fetchall()
        except self.driver_module.Error as e:
            logging.error(f"Erro ao selecionar dados: {e}")
            raise DatabaseQueryError(f"Erro ao buscar dados: {e}")
        return []

    def admin_get_all_connections(self) -> List[Tuple]:
        query = f"""
            SELECT c.Con_Codigo, c.Con_Nome, g.Gru_Nome, c.con_tipo 
            FROM Conexao_WTS c 
            LEFT JOIN Grupo_WTS g ON c.Gru_Codigo = g.Gru_Codigo 
            ORDER BY {self.db.ISNULL}(g.Gru_Nome, c.Con_Nome), c.Con_Nome
        """
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query)
                return cursor.fetchall()
        except self.driver_module.Error as e:
            logging.error(f"Admin: Erro ao buscar conexões: {e}")
            raise DatabaseQueryError(f"Admin: Erro ao buscar conexões: {e}")
        return []

    def admin_get_connection_details(self, con_id: int) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM Conexao_WTS WHERE Con_Codigo = {self.db.PARAM}"
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                    
                cursor.execute(query, (con_id,))
                result = cursor.fetchone()
                
                if result:
                    # Converte o resultado (seja pyodbc.Row ou tupla psycopg2) para dict
                    if hasattr(result, "cursor_description"): # pyodbc
                        return dict(zip([col[0] for col in result.cursor_description], result))
                    elif hasattr(cursor, "description"): # psycopg2
                         return dict(zip([col.name for col in cursor.description], result))
                         
        except self.driver_module.Error as e:
            logging.error(f"Admin: Erro ao buscar detalhes da conexão {con_id}: {e}")
            raise DatabaseQueryError(f"Admin: Erro ao buscar detalhes da conexão: {e}")
        return None

    def admin_create_connection(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        query = f"""
            INSERT INTO Conexao_WTS 
            (con_nome, gru_codigo, con_ip, con_usuario, con_senha, 
             con_particularidade, con_cliente, extra, sec, con_tipo)
            VALUES ({self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, 
                    {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM})
        """
        params = (
            data.get('con_nome'), data.get('gru_codigo'), data.get('con_ip'), data.get('con_usuario'),
            data.get('con_senha'), data.get('con_particularidade'), data.get('con_cliente'), data.get('extra'),
            data.get('sec', None), data.get('con_tipo', 'RDP') # Assume RDP se não especificado
        )
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query, params)
                return True, "Conexão criada."
        except self.driver_module.Error as e:
            logging.error(f"Admin: Erro ao CRIAR conexão: {e}")
            return False, f"Erro DB: {e}"

    def admin_update_connection(self, con_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
        query = f"""
            UPDATE Conexao_WTS
            SET con_nome = {self.db.PARAM}, gru_codigo = {self.db.PARAM}, con_ip = {self.db.PARAM}, 
                con_usuario = {self.db.PARAM}, con_senha = {self.db.PARAM},
                con_particularidade = {self.db.PARAM}, con_cliente = {self.db.PARAM}, 
                extra = {self.db.PARAM}, sec = {self.db.PARAM}, con_tipo = {self.db.PARAM}
            WHERE Con_Codigo = {self.db.PARAM}
        """
        params = (
            data.get('con_nome'), data.get('gru_codigo'), data.get('con_ip'), data.get('con_usuario'),
            data.get('con_senha'), data.get('con_particularidade'), data.get('con_cliente'), data.get('extra'),
            data.get('sec', None), data.get('con_tipo', 'RDP'),
            con_id
        )
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query, params)
                return True, "Conexão atualizada."
        except self.driver_module.Error as e:
            logging.error(f"Admin: Erro ao ATUALIZAR conexão: {e}")
            return False, f"Erro DB: {e}"

    def admin_delete_connection(self, con_id: int) -> Tuple[bool, str]:
        q_logs = f"DELETE FROM Usuario_Conexao_WTS WHERE Con_Codigo = {self.db.PARAM}"
        q_access = f"DELETE FROM Log_Acesso_WTS WHERE Con_Codigo = {self.db.PARAM}"
        q_conn = f"DELETE FROM Conexao_WTS WHERE Con_Codigo = {self.db.PARAM}"

        conn = self.db.get_transactional_connection()
        if not conn: return False, "Falha ao conectar."
        try:
            with conn.cursor() as cursor:
                cursor.execute(q_logs, (con_id,))
                cursor.execute(q_access, (con_id,))
                cursor.execute(q_conn, (con_id,))
                conn.commit()
                return True, "Conexão e logs relacionados deletados."
        except self.driver_module.Error as e:
            conn.rollback()
            logging.error(f"Admin: Erro ao DELETAR conexão {con_id}: {e}")
            if "REFERENCE constraint" in str(e) or "foreign key constraint" in str(e): 
                return False, "Erro: Conexão referenciada em outra tabela."
            return False, f"Erro DB: {e}"
        except Exception as ex:
             conn.rollback()
             logging.error(f"Admin: Erro inesperado ao DELETAR conexão {con_id}: {ex}")
             return False, f"Erro: {ex}"
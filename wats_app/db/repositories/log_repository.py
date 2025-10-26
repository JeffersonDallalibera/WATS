# WATS_Project/wats_app/db/repositories/log_repository.py
import logging
from typing import Optional
from wats_app.db.repositories.base_repository import BaseRepository
from wats_app.db.exceptions import DatabaseQueryError, DatabaseConnectionError

class LogRepository(BaseRepository):
    """Gerencia operações de Log (Usuario_Conexao_WTS e Log_Acesso_WTS)."""

    def insert_connection_log(self, con_codigo: int, username: str, ip: str, computer_name: str, user_name: str) -> bool:
        # Dialeto: GETDATE() -> self.db.NOW
        query = f"""
            INSERT INTO Usuario_Conexao_WTS
            (Con_Codigo, Usu_Nome, Usu_IP, Usu_Nome_Maquina, Usu_Usuario_Maquina, Usu_Dat_Conexao, Usu_Last_Heartbeat) 
            VALUES ({self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.NOW}, {self.db.NOW})
        """
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query, (con_codigo, username, ip, computer_name, user_name))
                return True
        except self.driver_module.Error as e:
            logging.error(f"Erro ao inserir log de conexão: {e}")
        return False

    def delete_connection_log(self, con_codigo: int, username: str) -> bool:
        query = f"DELETE FROM Usuario_Conexao_WTS WHERE Con_Codigo = {self.db.PARAM} AND Usu_Nome = {self.db.PARAM}"
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                user_to_delete = username.split('|')[0]
                cursor.execute(query, (con_codigo, user_to_delete))
                return True
        except self.driver_module.Error as e:
            logging.error(f"Erro ao deletar log de conexão: {e}")
        return False

    def update_heartbeat(self, con_codigo: int, username: str) -> bool:
        # Dialeto: GETDATE() -> self.db.NOW
        query = f"UPDATE Usuario_Conexao_WTS SET Usu_Last_Heartbeat = {self.db.NOW} WHERE Con_Codigo = {self.db.PARAM} AND Usu_Nome = {self.db.PARAM}"
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query, (con_codigo, username))
                return cursor.rowcount > 0
        except self.driver_module.Error as e:
            logging.error(f"Erro ao atualizar heartbeat: {e}")
        return False

    def cleanup_ghost_connections(self):
        # Dialeto: Procedimento específico
        query = ""
        if self.db.db_type == 'sqlserver':
            query = "EXEC sp_Limpar_Conexoes_Fantasma"
        elif self.db.db_type == 'postgresql':
            query = "SELECT sp_Limpar_Conexoes_Fantasma()" # Assume que você criou uma função de mesmo nome
            logging.info("Executando cleanup no PostgreSQL. Certifique-se que a função 'sp_Limpar_Conexoes_Fantasma()' exista.")
        
        if not query: return

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query)
                logging.info("Cleanup executado.")
        except self.driver_module.Error as e:
            logging.error(f"Erro ao executar cleanup: {e}")

    def log_access_start(self, user_machine_name: str, con_codigo: int, con_nome: str, con_tipo: str) -> Optional[int]:
        conn = self.db.get_transactional_connection()
        if not conn: return None

        # Dialeto: GETDATE() -> self.db.NOW
        query = f"""
            INSERT INTO Log_Acesso_WTS 
            (Usu_Nome_Maquina, Con_Codigo, Con_Nome_Acessado, Log_DataHora_Inicio, Log_Tipo_Conexao)
            VALUES ({self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.NOW}, {self.db.PARAM})
        """
        params = (user_machine_name, con_codigo, con_nome, con_tipo)
        
        try:
            with conn.cursor() as cursor:
                log_id = None
                
                # Tratamento de IDENTIDADE (SQLServer vs Postgres)
                if self.db.db_type == 'sqlserver':
                    cursor.execute(query, params)
                    log_id = cursor.execute(self.db.IDENTITY_QUERY).fetchone()[0]
                elif self.db.db_type == 'postgresql':
                    query_pg = query + " RETURNING Log_Id"
                    cursor.execute(query_pg, params)
                    log_id = cursor.fetchone()[0]
                
                conn.commit()
                logging.info(f"Log de acesso iniciado (ID: {log_id}) para {user_machine_name} -> {con_nome} ({con_tipo})")
                return log_id
        except self.driver_module.Error as e:
            conn.rollback()
            logging.error(f"Erro ao registrar início do log de acesso: {e}")
            return None

    def log_access_end(self, log_id: int) -> bool:
        # Dialeto: GETDATE() -> self.db.NOW
        query = f"UPDATE Log_Acesso_WTS SET Log_DataHora_Fim = {self.db.NOW} WHERE Log_Id = {self.db.PARAM}"
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query, (log_id,))
                if cursor.rowcount > 0:
                    logging.info(f"Log de acesso finalizado (ID: {log_id})")
                    return True
                else:
                    logging.warning(f"Tentativa de finalizar log de acesso ID {log_id}, mas ele não foi encontrado.")
                    return False
        except self.driver_module.Error as e:
            logging.error(f"Erro ao registrar fim do log de acesso ID {log_id}: {e}")
            return False
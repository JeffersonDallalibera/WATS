# WATS_Project/wats_app/db/repositories/log_repository.py
import logging
from typing import Optional, List, Dict, Any

from src.wats.db.exceptions import DatabaseConnectionError
from src.wats.db.repositories.base_repository import BaseRepository
from src.wats.util_cache.cache import cached, invalidate_cache


class LogRepository(BaseRepository):
    """Gerencia operações de Log (Usuario_Conexao_WTS e Log_Acesso_WTS)."""

    def __init__(self, db_manager):
        super().__init__(db_manager)

    def insert_connection_log(
        self, con_codigo: int, username: str, ip: str, computer_name: str, user_name: str
    ) -> bool:
        """Insere log de conexão e invalida cache."""
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
                self._invalidate_log_caches()
                return True
        except self.driver_module.Error as e:
            logging.error(f"Erro ao inserir log de conexão: {e}")
        return False

    def delete_connection_log(self, con_codigo: int, username: str) -> bool:
        """
        Deleta log de conexão específico e invalida cache.
        
        CORREÇÃO: Remove o usuário específico ao invés de apenas o primeiro.
        
        Args:
            con_codigo: Código da conexão
            username: Nome específico do usuário a ser removido
            
        Returns:
            True se removeu com sucesso, False caso contrário
        """
        query = f"DELETE FROM Usuario_Conexao_WTS WHERE Con_Codigo = {self.db.PARAM} AND Usu_Nome = {self.db.PARAM}"
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                # CORREÇÃO: Remove o usuário específico (não faz split do primeiro)
                logging.info(f"Removendo usuário específico '{username}' da conexão {con_codigo}")
                cursor.execute(query, (con_codigo, username))
                
                rows_affected = cursor.rowcount
                if rows_affected > 0:
                    logging.info(f"Usuário '{username}' removido com sucesso da conexão {con_codigo}")
                    self._invalidate_log_caches()
                    return True
                else:
                    logging.warning(f"Usuário '{username}' não encontrado na conexão {con_codigo}")
                    return False
                    
        except self.driver_module.Error as e:
            logging.error(f"Erro ao deletar log de conexão {con_codigo} usuário '{username}': {e}")
        return False

    def delete_all_users_from_connection(self, con_codigo: int) -> int:
        """
        Remove TODOS os usuários de uma conexão específica.
        Útil para 'limpar' completamente uma conexão com múltiplos usuários.
        
        Args:
            con_codigo: Código da conexão
            
        Returns:
            Número de usuários removidos
        """
        query = f"DELETE FROM Usuario_Conexao_WTS WHERE Con_Codigo = {self.db.PARAM}"
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                logging.info(f"Removendo TODOS os usuários da conexão {con_codigo}")
                cursor.execute(query, (con_codigo,))
                
                rows_affected = cursor.rowcount
                logging.info(f"Removidos {rows_affected} usuário(s) da conexão {con_codigo}")
                self._invalidate_log_caches()
                return rows_affected
                    
        except self.driver_module.Error as e:
            logging.error(f"Erro ao limpar conexão {con_codigo}: {e}")
        return 0

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
        """
        Limpa conexões fantasmas (sem heartbeat recente).
        Executado periodicamente via stored procedure.
        """
        # Dialeto: Procedimento específico
        query = ""
        if self.db.db_type == "sqlserver":
            query = "EXEC sp_Limpar_Conexoes_Fantasma"
        elif self.db.db_type == "sqlite":
            query = "DELETE FROM Conexoes_WTS WHERE datetime(Data_Disconnect, '+1 hour') < datetime('now')"
            logging.info("Executando cleanup no SQLite. Removendo conexões antigas.")
        else:
            logging.warning(f"Cleanup não implementado para o tipo de banco: {self.db.db_type}")
            return

        if not query:
            return

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query)
                logging.info("Cleanup de conexões fantasmas executado.")
        except self.driver_module.Error as e:
            logging.error(f"Erro ao executar cleanup de conexões fantasmas: {e}")

    def cleanup_orphaned_access_logs(self, hours_limit: int = 24, simulate: bool = False) -> int:
        """
        Limpa logs de acesso órfãos (sem data de fim após X horas).
        
        Args:
            hours_limit: Logs mais antigos que X horas serão finalizados
            simulate: Se True, apenas simula (não executa UPDATE)
            
        Returns:
            Número de logs processados
        """
        if self.db.db_type != "sqlserver":
            logging.warning(f"cleanup_orphaned_access_logs não implementado para {self.db.db_type}")
            return 0

        try:
            cursor = self.db.get_cursor()
            if not cursor:
                raise DatabaseConnectionError("Falha ao obter cursor.")
            
            try:
                # Chama stored procedure (ela executa PRINT e RETURN)
                simulate_param = 1 if simulate else 0
                query = f"EXEC sp_Limpar_Logs_Orfaos @HorasLimite = ?, @SimularExecucao = ?"
                
                cursor.execute(query, (hours_limit, simulate_param))
                
                # Stored procedure usa PRINT para output, não SELECT
                # Vamos tentar pegar mensagens do servidor
                rows_affected = 0
                
                # Processa todos os resultados pendentes (incluindo mensagens PRINT)
                while cursor.nextset():
                    pass
                
                # Como não temos acesso direto ao RETURN value via pyodbc,
                # vamos fazer uma query adicional para contar logs órfãos antes do cleanup
                # Mas isso só funciona em modo simulate
                if simulate:
                    logging.info("Cleanup de logs órfãos simulado (modo dry-run)")
                else:
                    logging.info("Cleanup de logs órfãos executado com sucesso")
                
                if not simulate:
                    self._invalidate_log_caches()
                
                return rows_affected
                
            finally:
                cursor.close()
                
        except Exception as e:
            logging.error(f"Erro ao executar cleanup de logs órfãos: {e}")
            return 0

    def log_access_start(
        self, user_machine_name: str, con_codigo: int, con_nome: str, con_tipo: str
    ) -> Optional[int]:
        """Registra início de acesso e invalida cache."""
        conn = self.db.get_transactional_connection()
        if not conn:
            return None

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

                # Tratamento de IDENTIDADE (SQLServer vs SQLite)
                if self.db.db_type == "sqlserver":
                    cursor.execute(query, params)
                    log_id = cursor.execute(self.db.IDENTITY_QUERY).fetchone()[0]
                elif self.db.db_type == "sqlite":
                    cursor.execute(query, params)
                    log_id = cursor.execute(self.db.IDENTITY_QUERY).fetchone()[0]
                else:
                    # Fallback genérico
                    cursor.execute(query, params)
                    log_id = cursor.lastrowid

                conn.commit()
                self._invalidate_log_caches()
                logging.info(
                    f"Log de acesso iniciado (ID: {log_id}) para {user_machine_name} -> {con_nome} ({con_tipo})"
                )
                return log_id
        except self.driver_module.Error as e:
            conn.rollback()
            logging.error(f"Erro ao registrar início do log de acesso: {e}")
            return None

    def log_access_end(self, log_id: int) -> bool:
        """Finaliza log de acesso e invalida cache."""
        # Dialeto: GETDATE() -> self.db.NOW
        query = f"UPDATE Log_Acesso_WTS SET Log_DataHora_Fim = {self.db.NOW} WHERE Log_Id = {self.db.PARAM}"
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query, (log_id,))
                if cursor.rowcount > 0:
                    self._invalidate_log_caches()
                    logging.info(f"Log de acesso finalizado (ID: {log_id})")
                    return True
                else:
                    logging.warning(
                        f"Tentativa de finalizar log de acesso ID {log_id}, mas ele não foi encontrado."
                    )
                    return False
        except self.driver_module.Error as e:
            logging.error(f"Erro ao registrar fim do log de acesso ID {log_id}: {e}")
            return False

    # ==================== Métodos de Consulta com Cache ====================
    
    @cached(namespace="logs", ttl=60)
    def get_active_connections(self) -> List[Dict[str, Any]]:
        """Retorna conexões ativas (com cache de 60s)."""
        query = f"""
            SELECT Con_Codigo, Usu_Nome, Usu_IP, Usu_Nome_Maquina, Usu_Usuario_Maquina,
                   Usu_Dat_Conexao, Usu_Last_Heartbeat
            FROM Usuario_Conexao_WTS
            ORDER BY Usu_Dat_Conexao DESC
        """
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except self.driver_module.Error as e:
            logging.error(f"Erro ao buscar conexões ativas: {e}")
            return []

    @cached(namespace="logs", ttl=300)
    def get_access_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retorna logs de acesso com paginação (cache de 5min)."""
        query = f"""
            SELECT Log_Id, Usu_Nome_Maquina, Con_Codigo, Con_Nome_Acessado,
                   Log_DataHora_Inicio, Log_DataHora_Fim, Log_Tipo_Conexao
            FROM Log_Acesso_WTS
            ORDER BY Log_DataHora_Inicio DESC
            OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
        """
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except self.driver_module.Error as e:
            logging.error(f"Erro ao buscar logs de acesso: {e}")
            return []

    @cached(namespace="logs", ttl=300)
    def get_user_access_history(self, user_machine_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retorna histórico de acessos de um usuário (cache de 5min)."""
        query = f"""
            SELECT TOP {limit} Log_Id, Con_Codigo, Con_Nome_Acessado,
                   Log_DataHora_Inicio, Log_DataHora_Fim, Log_Tipo_Conexao
            FROM Log_Acesso_WTS
            WHERE Usu_Nome_Maquina = {self.db.PARAM}
            ORDER BY Log_DataHora_Inicio DESC
        """
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                cursor.execute(query, (user_machine_name,))
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except self.driver_module.Error as e:
            logging.error(f"Erro ao buscar histórico do usuário: {e}")
            return []

    def _invalidate_log_caches(self):
        """Invalida todos os caches relacionados a logs."""
        invalidate_cache(namespace="logs")

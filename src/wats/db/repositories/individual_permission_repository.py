# WATS_Project/wats_app/db/repositories/individual_permission_repository.py
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.wats.db.database_manager import DatabaseManager
from src.wats.db.exceptions import DatabaseConnectionError, DatabaseQueryError
from src.wats.db.repositories.base_repository import BaseRepository
from src.wats.performance import cache_permissions, invalidate_user_caches


class IndividualPermissionRepository(BaseRepository):
    """Gerencia permissões individuais de conexão para usuários."""

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)

    def grant_individual_access(
        self,
        user_id: int,
        connection_id: int,
        granted_by_user_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
        observations: str = None,
    ) -> Tuple[bool, str]:
        """
        Concede acesso individual a uma conexão para um usuário.

        Args:
            user_id: ID do usuário que receberá o acesso
            connection_id: ID da conexão
            granted_by_user_id: ID do usuário que está concedendo o acesso
            start_date: Data de início (None = agora)
            end_date: Data de fim (None = permanente)
            observations: Observações sobre a concessão
        """
        if start_date is None:
            start_date = datetime.now()

        # Verificar se já existe uma permissão ativa para este usuário/conexão
        existing_query = """
            SELECT Id FROM Permissao_Conexao_Individual_WTS
            WHERE Usu_Id = {self.db.PARAM} AND Con_Codigo = {self.db.PARAM} AND Ativo = {self.db.PARAM}
        """

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")

                # Verificar se já existe
                cursor.execute(existing_query, (user_id, connection_id, True))
                existing = cursor.fetchone()

                if existing:
                    return False, "Usuário já possui acesso individual ativo para esta conexão."

                # Inserir nova permissão
                insert_query = """
                    INSERT INTO Permissao_Conexao_Individual_WTS
                    (Usu_Id, Con_Codigo, Data_Inicio, Data_Fim, Criado_Por_Usu_Id, Data_Criacao, Ativo, Observacoes)
                    VALUES ({self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM})
                """

                params = (
                    user_id,
                    connection_id,
                    start_date,
                    end_date,
                    granted_by_user_id,
                    datetime.now(),
                    True,
                    observations,
                )
                cursor.execute(insert_query, params)

                invalidate_user_caches()
                return True, "Acesso individual concedido com sucesso."

        except self.driver_module.Error as e:
            logging.error(f"Erro ao conceder acesso individual: {e}")
            return False, f"Erro no banco de dados: {e}"

    def revoke_individual_access(self, user_id: int, connection_id: int) -> Tuple[bool, str]:
        """Remove acesso individual de um usuário a uma conexão."""
        query = f"""
            UPDATE Permissao_Conexao_Individual_WTS
            SET Ativo = {self.db.PARAM}
            WHERE Usu_Id = {self.db.PARAM} AND Con_Codigo = {self.db.PARAM} AND Ativo = {self.db.PARAM}
        """

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")

                cursor.execute(query, (False, user_id, connection_id, True))

                if cursor.rowcount > 0:
                    invalidate_user_caches()
                    return True, "Acesso individual revogado com sucesso."
                else:
                    return False, "Nenhuma permissão ativa encontrada para revogar."

        except self.driver_module.Error as e:
            logging.error(f"Erro ao revogar acesso individual: {e}")
            return False, f"Erro no banco de dados: {e}"

    @cache_permissions(ttl=180)
    def list_user_individual_permissions(self, user_id: int) -> List[Dict[str, Any]]:
        """Lista todas as permissões individuais de um usuário."""
        query = f"""
            SELECT
                pci.Id, pci.Con_Codigo, c.Con_Nome, c.Con_IP,
                pci.Data_Inicio, pci.Data_Fim, pci.Ativo,
                pci.Observacoes, pci.Data_Criacao,
                u.Usu_Nome as Criado_Por
            FROM Permissao_Conexao_Individual_WTS pci
            INNER JOIN Conexao_WTS c ON pci.Con_Codigo = c.Con_Codigo
            INNER JOIN Usuario_Sistema_WTS u ON pci.Criado_Por_Usu_Id = u.Usu_Id
            WHERE pci.Usu_Id = {self.db.PARAM}
            ORDER BY pci.Data_Criacao DESC
        """

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")

                cursor.execute(query, (user_id,))
                results = cursor.fetchall()

                permissions = []
                for result in results:
                    if hasattr(result, "cursor_description"):  # pyodbc
                        permission = dict(
                            zip([col[0] for col in result.cursor_description], result)
                        )
                    elif hasattr(cursor, "description"):  # psycopg2
                        permission = dict(zip([col.name for col in cursor.description], result))
                    else:
                        # Fallback para tupla simples
                        cols = [
                            "Id",
                            "Con_Codigo",
                            "Con_Nome",
                            "Con_IP",
                            "Data_Inicio",
                            "Data_Fim",
                            "Ativo",
                            "Observacoes",
                            "Data_Criacao",
                            "Criado_Por",
                        ]
                        permission = dict(zip(cols, result))

                    permissions.append(permission)

                return permissions

        except self.driver_module.Error as e:
            logging.error(f"Erro ao listar permissões do usuário {user_id}: {e}")
            raise DatabaseQueryError(f"Erro ao buscar permissões: {e}")

    def list_connection_individual_permissions(self, connection_id: int) -> List[Dict[str, Any]]:
        """Lista todos os usuários com acesso individual a uma conexão."""
        query = f"""
            SELECT
                pci.Id, pci.Usu_Id, u.Usu_Nome,
                pci.Data_Inicio, pci.Data_Fim, pci.Ativo,
                pci.Observacoes, pci.Data_Criacao,
                uc.Usu_Nome as Criado_Por
            FROM Permissao_Conexao_Individual_WTS pci
            INNER JOIN Usuario_Sistema_WTS u ON pci.Usu_Id = u.Usu_Id
            INNER JOIN Usuario_Sistema_WTS uc ON pci.Criado_Por_Usu_Id = uc.Usu_Id
            WHERE pci.Con_Codigo = {self.db.PARAM}
            ORDER BY pci.Data_Criacao DESC
        """

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")

                cursor.execute(query, (connection_id,))
                results = cursor.fetchall()

                permissions = []
                for result in results:
                    if hasattr(result, "cursor_description"):  # pyodbc
                        permission = dict(
                            zip([col[0] for col in result.cursor_description], result)
                        )
                    elif hasattr(cursor, "description"):  # psycopg2
                        permission = dict(zip([col.name for col in cursor.description], result))
                    else:
                        # Fallback para tupla simples
                        cols = [
                            "Id",
                            "Usu_Id",
                            "Usu_Nome",
                            "Data_Inicio",
                            "Data_Fim",
                            "Ativo",
                            "Observacoes",
                            "Data_Criacao",
                            "Criado_Por",
                        ]
                        permission = dict(zip(cols, result))

                    permissions.append(permission)

                return permissions

        except self.driver_module.Error as e:
            logging.error(f"Erro ao listar permissões da conexão {connection_id}: {e}")
            raise DatabaseQueryError(f"Erro ao buscar permissões: {e}")

    def has_individual_access(self, user_id: int, connection_id: int) -> bool:
        """Verifica se um usuário tem acesso individual a uma conexão específica."""
        query = f"""
            SELECT 1 FROM Permissao_Conexao_Individual_WTS
            WHERE Usu_Id = {self.db.PARAM} AND Con_Codigo = {self.db.PARAM}
            AND Ativo = {self.db.PARAM}
            AND Data_Inicio <= {self.db.PARAM}
            AND (Data_Fim IS NULL OR Data_Fim >= {self.db.PARAM})
        """

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    return False

                now = datetime.now()
                cursor.execute(query, (user_id, connection_id, True, now, now))
                result = cursor.fetchone()

                return result is not None

        except self.driver_module.Error as e:
            logging.error(f"Erro ao verificar acesso individual: {e}")
            return False

    def get_user_individual_connections(self, user_id: int) -> List[int]:
        """Retorna lista de IDs de conexões que o usuário tem acesso individual."""
        query = f"""
            SELECT DISTINCT Con_Codigo
            FROM Permissao_Conexao_Individual_WTS
            WHERE Usu_Id = {self.db.PARAM} AND Ativo = {self.db.PARAM}
            AND Data_Inicio <= {self.db.PARAM}
            AND (Data_Fim IS NULL OR Data_Fim >= {self.db.PARAM})
        """

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    return []

                now = datetime.now()
                cursor.execute(query, (user_id, True, now, now))
                results = cursor.fetchall()

                return [result[0] for result in results]

        except self.driver_module.Error as e:
            logging.error(f"Erro ao buscar conexões individuais do usuário {user_id}: {e}")
            return []

    # ========== MÉTODOS PARA PERMISSÕES TEMPORÁRIAS ==========

    def grant_temporary_access(
        self,
        user_id: int,
        connection_id: int,
        granted_by_user_id: int,
        duration_hours: float,
        observations: str = None,
    ) -> Tuple[bool, str]:
        """
        Concede acesso temporário a uma conexão para um usuário.

        Args:
            user_id: ID do usuário que receberá o acesso
            connection_id: ID da conexão
            granted_by_user_id: ID do usuário que está concedendo o acesso
            duration_hours: Duração em horas (pode ser decimal para minutos)
            observations: Observações sobre a concessão
        """
        from datetime import timedelta

        start_date = datetime.now()
        end_date = start_date + timedelta(hours=duration_hours)

        # Verificar se já existe uma permissão ativa (permanente ou temporária)
        # para este usuário/conexão
        existing_query = """
            SELECT Id, Data_Fim FROM Permissao_Conexao_Individual_WTS
            WHERE Usu_Id = {self.db.PARAM} AND Con_Codigo = {self.db.PARAM} AND Ativo = {self.db.PARAM}
            AND (Data_Fim IS NULL OR Data_Fim >= {self.db.PARAM})
        """

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")

                # Verificar se já existe
                cursor.execute(existing_query, (user_id, connection_id, True, datetime.now()))
                existing = cursor.fetchone()

                if existing:
                    existing_end = existing[1] if len(existing) > 1 else None
                    if existing_end is None:
                        return False, "Usuário já possui acesso permanente para esta conexão."
                    else:
                        return (
                            False,
                            f"Usuário já possui acesso temporário ativo até {existing_end.strftime('%d/%m/%Y %H:%M')}.",
                        )

                # Inserir nova permissão temporária
                insert_query = """
                    INSERT INTO Permissao_Conexao_Individual_WTS
                    (Usu_Id, Con_Codigo, Data_Inicio, Data_Fim, Criado_Por_Usu_Id, Data_Criacao, Ativo, Observacoes)
                    VALUES ({self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM}, {self.db.PARAM})
                """

                duration_text = (
                    f"{duration_hours}h"
                    if duration_hours >= 1
                    else f"{int(duration_hours * 60)}min"
                )
                final_observations = (
                    f"Acesso temporário ({duration_text}). {observations or ''}".strip()
                )

                params = (
                    user_id,
                    connection_id,
                    start_date,
                    end_date,
                    granted_by_user_id,
                    datetime.now(),
                    True,
                    final_observations,
                )
                cursor.execute(insert_query, params)

                return (
                    True,
                    f"Acesso temporário concedido até {end_date.strftime('%d/%m/%Y %H:%M')}.",
                )

        except self.driver_module.Error as e:
            logging.error(f"Erro ao conceder acesso temporário: {e}")
            return False, f"Erro no banco de dados: {e}"

    def list_active_temporary_permissions(self) -> List[Dict[str, Any]]:
        """Lista todas as permissões temporárias ativas no sistema."""
        query = f"""
            SELECT
                pci.Id, pci.Usu_Id, u.Usu_Nome,
                pci.Con_Codigo, c.Con_Nome, c.Con_IP,
                pci.Data_Inicio, pci.Data_Fim, pci.Observacoes,
                uc.Usu_Nome as Criado_Por
            FROM Permissao_Conexao_Individual_WTS pci
            INNER JOIN Usuario_Sistema_WTS u ON pci.Usu_Id = u.Usu_Id
            INNER JOIN Conexao_WTS c ON pci.Con_Codigo = c.Con_Codigo
            INNER JOIN Usuario_Sistema_WTS uc ON pci.Criado_Por_Usu_Id = uc.Usu_Id
            WHERE pci.Ativo = {self.db.PARAM}
            AND pci.Data_Fim IS NOT NULL
            AND pci.Data_Fim >= {self.db.PARAM}
            ORDER BY pci.Data_Fim ASC
        """

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")

                cursor.execute(query, (True, datetime.now()))
                results = cursor.fetchall()

                permissions = []
                for result in results:
                    if hasattr(result, "cursor_description"):  # pyodbc
                        permission = dict(
                            zip([col[0] for col in result.cursor_description], result)
                        )
                    elif hasattr(cursor, "description"):  # psycopg2
                        permission = dict(zip([col.name for col in cursor.description], result))
                    else:
                        # Fallback para tupla simples
                        cols = [
                            "Id",
                            "Usu_Id",
                            "Usu_Nome",
                            "Con_Codigo",
                            "Con_Nome",
                            "Con_IP",
                            "Data_Inicio",
                            "Data_Fim",
                            "Observacoes",
                            "Criado_Por",
                        ]
                        permission = dict(zip(cols, result))

                    # Calcular tempo restante
                    if permission.get("Data_Fim"):
                        time_left = permission["Data_Fim"] - datetime.now()
                        if time_left.total_seconds() > 0:
                            hours = int(time_left.total_seconds() // 3600)
                            minutes = int((time_left.total_seconds() % 3600) // 60)
                            permission["Tempo_Restante"] = f"{hours}h{minutes:02d}m"
                        else:
                            permission["Tempo_Restante"] = "Expirado"
                    else:
                        permission["Tempo_Restante"] = "N/A"

                    permissions.append(permission)

                return permissions

        except self.driver_module.Error as e:
            logging.error(f"Erro ao listar permissões temporárias ativas: {e}")
            raise DatabaseQueryError(f"Erro ao buscar permissões temporárias: {e}")

    def cleanup_expired_permissions(self) -> Tuple[int, str]:
        """Remove permissões temporárias expiradas (soft delete)."""
        query = f"""
            UPDATE Permissao_Conexao_Individual_WTS
            SET Ativo = {self.db.PARAM}
            WHERE Ativo = {self.db.PARAM}
            AND Data_Fim IS NOT NULL
            AND Data_Fim < {self.db.PARAM}
        """

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")

                cursor.execute(query, (False, True, datetime.now()))
                rows_affected = cursor.rowcount

                return rows_affected, f"{rows_affected} permissões expiradas foram desativadas."

        except self.driver_module.Error as e:
            logging.error(f"Erro ao limpar permissões expiradas: {e}")
            return 0, f"Erro ao limpar permissões: {e}"

    def revoke_temporary_access(self, permission_id: int) -> Tuple[bool, str]:
        """Revoga uma permissão temporária específica pelo ID."""
        query = f"""
            UPDATE Permissao_Conexao_Individual_WTS
            SET Ativo = {self.db.PARAM}
            WHERE Id = {self.db.PARAM} AND Ativo = {self.db.PARAM} AND Data_Fim IS NOT NULL
        """

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")

                cursor.execute(query, (False, permission_id, True))

                if cursor.rowcount > 0:
                    return True, "Acesso temporário revogado com sucesso."
                else:
                    return False, "Permissão temporária não encontrada ou já inativa."

        except self.driver_module.Error as e:
            logging.error(f"Erro ao revogar acesso temporário {permission_id}: {e}")
            return False, f"Erro no banco de dados: {e}"

    def get_duration_options(self) -> List[Tuple[str, float]]:
        """Retorna opções de duração para permissões temporárias."""
        return [
            ("30 minutos", 0.5),
            ("1 hora", 1.0),
            ("2 horas", 2.0),
            ("3 horas", 3.0),
            ("4 horas", 4.0),
            ("8 horas", 8.0),
        ]

    def list_all_individual_permissions(
        self, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista permissões individuais (permanentes e temporárias).

        Args:
            user_id: Se fornecido, filtra apenas as permissões deste usuário
        """
        # Base da query
        query = f"""
            SELECT
                p.Usu_Id,
                u.Usu_Nome,
                p.Con_Codigo,
                c.Con_Nome,
                CASE WHEN p.Data_Fim IS NULL THEN 0 ELSE 1 END as is_temporary,
                p.Data_Fim
            FROM Permissao_Conexao_Individual_WTS p
            INNER JOIN Usuario_Sistema_WTS u ON p.Usu_Id = u.Usu_Id
            INNER JOIN Conexao_WTS c ON p.Con_Codigo = c.Con_Codigo
            WHERE p.Ativo = {self.db.PARAM}
        """

        # Adicionar filtro por usuário se fornecido
        params = [True]
        if user_id is not None:
            query += f" AND p.Usu_Id = {self.db.PARAM}"
            params.append(user_id)

        query += " ORDER BY u.Usu_Nome, c.Con_Nome"

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")

                cursor.execute(query, tuple(params))
                results = cursor.fetchall()

                permissions = []
                for row in results:
                    user_id_result, username, conn_id, conn_name, is_temporary, expires_at = row
                    permissions.append(
                        {
                            "user_id": user_id_result,
                            "username": username,
                            "conn_id": conn_id,
                            "conn_name": conn_name,
                            "is_temporary": bool(is_temporary),
                            "expires_at": expires_at,
                        }
                    )

                return permissions

        except self.driver_module.Error as e:
            logging.error(f"Erro ao listar permissões individuais: {e}")
            return []

# WATS_Project/wats_app/db_manager.py (ATUALIZADO PARA LOG E TIPO)

import logging
import os
import sys
from tkinter import messagebox
from typing import Any, Dict, List, Optional, Tuple

import pyodbc


class Database:
    """Gerencia a interação com o banco de dados SQL Server de forma segura."""

    def __init__(self):
        try:
            self.connection_string = (
                f"DRIVER={{SQL Server}};"
                f"SERVER={os.getenv('DB_SERVER')};"
                f"DATABASE={os.getenv('DB_DATABASE')};"
                f"UID={os.getenv('DB_UID')};"
                f"PWD={os.getenv('DB_PWD')};"
                "TrustServerCertificate=yes;"
            )
            if not all(os.getenv(k) for k in ["DB_SERVER", "DB_DATABASE", "DB_UID", "DB_PWD"]):
                raise ValueError("Credenciais do banco de dados ausentes.")

            self.conn: Optional[pyodbc.Connection] = None
        except Exception as e:
            logging.error(f"Erro ao ler as configurações do banco de dados: {e}")
            messagebox.showerror(
                "Erro de Configuração", f"Não foi possível ler as credenciais do banco: {e}"
            )
            sys.exit(1)

    def _get_connection(self) -> Optional[pyodbc.Connection]:
        """Retorna o objeto de conexão (para transações)."""
        try:
            if self.conn is None or self.conn.autocommit:
                if self.conn:
                    self.conn.close()
                self.conn = pyodbc.connect(self.connection_string, autocommit=False)
            self.conn.execute("SELECT 1")
            return self.conn
        except (pyodbc.Error, AttributeError) as e:
            logging.warning(f"Reconectando ao banco de dados (transação): {e}")
            try:
                self.conn = pyodbc.connect(self.connection_string, autocommit=False)
                return self.conn
            except pyodbc.Error as e_inner:
                logging.error(f"Não foi possível conectar ao banco de dados: {e_inner}")
                messagebox.showerror(
                    "Erro de Banco de Dados", f"Não foi possível conectar: {e_inner}"
                )
                return None
        except Exception as ex:
            logging.error(f"Erro inesperado de conexão: {ex}")
            return None

    def _connect(self) -> Optional[pyodbc.Cursor]:
        """Retorna um cursor com autocommit=True."""
        try:
            if self.conn is not None and not self.conn.autocommit:
                self.conn.close()
                self.conn = pyodbc.connect(self.connection_string, autocommit=True)
            elif self.conn is None:
                self.conn = pyodbc.connect(self.connection_string, autocommit=True)
            self.conn.execute("SELECT 1")
            return self.conn.cursor()
        except (pyodbc.Error, Exception) as e:
            logging.error(f"Falha ao obter cursor com autocommit: {e}")
            try:
                self.conn = pyodbc.connect(self.connection_string, autocommit=True)
                return self.conn.cursor()
            except pyodbc.Error as e_inner:
                logging.error(f"Não foi possível conectar ao banco de dados: {e_inner}")
                messagebox.showerror(
                    "Erro de Banco de Dados", f"Não foi possível conectar: {e_inner}"
                )
                return None

    # --- MÉTODOS DA APLICAÇÃO PRINCIPAL ---

    def get_user_role(self, username: str) -> Tuple[Optional[int], bool]:
        query = "SELECT Usu_Id, Usu_Is_Admin FROM Usuario_Sistema_WTS WHERE Usu_Nome = ? AND Usu_Ativo = 1"
        cursor = self._connect()
        if not cursor:
            return None, False
        try:
            with cursor:
                result = cursor.execute(query, username).fetchone()
                if result:
                    return result[0], (result[1] == 1)
        except pyodbc.Error as e:
            logging.error(f"Erro ao buscar permissão do usuário {username}: {e}")
        return None, False

    def select_all(self, username: str) -> List[pyodbc.Row]:
        user_id, is_admin = self.get_user_role(username)
        # ### ALTERADO: Adicionado con_tipo à seleção ###
        base_query = """
            SELECT
                Con.Con_Codigo, Con.Con_IP, Con.Con_Nome, Con.Con_Usuario, Con.Con_Senha,
                Gru.Gru_Nome, ISNULL(Uco.Usu_Nome, '') AS Usu_Nome, NULL AS Usu_Dat_Conexao,
                ISNULL(Con.Extra, '') AS Extra, con.con_particularidade,
                ISNULL(C2.con_cliente, '') AS con_cliente,
                Con.con_tipo -- <<< NOVO
            FROM Conexao_WTS Con
            LEFT JOIN Grupo_WTS Gru ON Con.Gru_Codigo = Gru.Gru_Codigo
            LEFT JOIN (
                SELECT Con_Codigo,
                    (CASE
                        WHEN MIN(Usu_Nome) = MAX(Usu_Nome) THEN MIN(Usu_Nome)
                        ELSE MIN(Usu_Nome) + '|' + MAX(Usu_Nome)
                    END) AS Usu_Nome
                FROM usuario_conexao_wts
                GROUP BY Con_Codigo
            ) Uco ON Con.Con_Codigo = Uco.Con_Codigo
            LEFT JOIN conexao_wts C2 ON Con.Con_Codigo = C2.Con_Codigo
        """
        where_clause = ""
        params = []
        if not is_admin:
            if user_id is None:
                return []
            where_clause = "WHERE EXISTS (SELECT 1 FROM Permissao_Grupo_WTS p WHERE p.Usu_Id = ? AND p.Gru_Codigo = Con.Gru_Codigo)"
            params.append(user_id)
        order_clause = "ORDER BY ISNULL(Gru.Gru_Nome, Con.Con_Nome), Con.Con_Nome"
        query = f"{base_query} {where_clause} {order_clause}"
        cursor = self._connect()
        if not cursor:
            return []
        try:
            with cursor:
                return cursor.execute(query, tuple(params)).fetchall()
        except pyodbc.Error as e:
            logging.error(f"Erro ao selecionar dados: {e}")
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao buscar dados: {e}")
        return []

    def insert_connection_log(
        self, con_codigo: int, username: str, ip: str, computer_name: str, user_name: str
    ) -> bool:
        query = "INSERT INTO Usuario_Conexao_WTS(Con_Codigo, Usu_Nome, Usu_IP, Usu_Nome_Maquina, Usu_Usuario_Maquina, Usu_Dat_Conexao, Usu_Last_Heartbeat) VALUES (?, ?, ?, ?, ?, GETDATE(), GETDATE())"
        cursor = self._connect()
        if not cursor:
            return False
        try:
            with cursor:
                cursor.execute(query, (con_codigo, username, ip, computer_name, user_name))
                return True
        except pyodbc.Error as e:
            logging.error(f"Erro ao inserir log de conexão: {e}")
        return False

    def delete_connection_log(self, con_codigo: int, username: str) -> bool:
        query = "DELETE FROM Usuario_Conexao_WTS WHERE Con_Codigo = ? AND Usu_Nome = ?"
        cursor = self._connect()
        if not cursor:
            return False
        try:
            with cursor:
                user_to_delete = username.split("|")[0]
                cursor.execute(query, (con_codigo, user_to_delete))
                return True
        except pyodbc.Error as e:
            logging.error(f"Erro ao deletar log de conexão: {e}")
        return False

    def update_heartbeat(self, con_codigo: int, username: str) -> bool:
        query = "UPDATE Usuario_Conexao_WTS SET Usu_Last_Heartbeat = GETDATE() WHERE Con_Codigo = ? AND Usu_Nome = ?"
        cursor = self._connect()
        if not cursor:
            return False
        try:
            with cursor:
                cursor.execute(query, con_codigo, username)
                return cursor.rowcount > 0
        except pyodbc.Error as e:
            logging.error(f"Erro ao atualizar heartbeat: {e}")
        return False

    def cleanup_ghost_connections(self):
        query = "EXEC sp_Limpar_Conexoes_Fantasma"
        cursor = self._connect()
        if not cursor:
            return
        try:
            with cursor:
                cursor.execute(query)
                logging.info("Cleanup executado.")
        except pyodbc.Error as e:
            logging.error(f"Erro ao executar cleanup: {e}")

    def get_admin_password_hash(self) -> Optional[str]:
        query = "SELECT Cfg_Valor FROM Config_Sistema_WTS WHERE Cfg_Chave = ?"
        cursor = self._connect()
        if not cursor:
            return None
        try:
            with cursor:
                result = cursor.execute(query, ("ADMIN_PASSWORD",)).fetchone()
                if result:
                    return result[0]
        except pyodbc.Error as e:
            logging.error(f"Erro ao buscar senha admin: {e}")
        return None

    # NOVO: Métodos para Log de Acesso Detalhado

    def log_access_start(
        self, user_machine_name: str, con_codigo: int, con_nome: str, con_tipo: str
    ) -> Optional[int]:
        """Registra o início de um acesso e retorna o ID do log."""
        query = """
            INSERT INTO Log_Acesso_WTS
            (Usu_Nome_Maquina, Con_Codigo, Con_Nome_Acessado, Log_DataHora_Inicio, Log_Tipo_Conexao)
            VALUES (?, ?, ?, GETDATE(), ?);
        """
        conn = self._get_connection()  # Usa conexão sem autocommit para pegar o ID
        if not conn:
            return None
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (user_machine_name, con_codigo, con_nome, con_tipo))
                # Pega o ID do log recém-inserido
                log_id = cursor.execute("SELECT @@IDENTITY AS ID;").fetchone()[0]
                conn.commit()
                logging.info(
                    f"Log de acesso iniciado (ID: {log_id}) para {user_machine_name} -> {con_nome} ({con_tipo})"
                )
                return log_id
        except pyodbc.Error as e:
            conn.rollback()
            logging.error(f"Erro ao registrar início do log de acesso: {e}")
            return None
        finally:
            conn.autocommit = True  # Restaura autocommit se for usar a conexão depois

    def log_access_end(self, log_id: int) -> bool:
        """Registra o fim de um acesso."""
        query = "UPDATE Log_Acesso_WTS SET Log_DataHora_Fim = GETDATE() WHERE Log_Id = ?"
        cursor = self._connect()  # Usa cursor com autocommit
        if not cursor:
            return False
        try:
            with cursor:
                cursor.execute(query, log_id)
                if cursor.rowcount > 0:
                    logging.info(f"Log de acesso finalizado (ID: {log_id})")
                    return True
                else:
                    logging.warning(
                        f"Tentativa de finalizar log de acesso ID {log_id}, mas ele não foi encontrado."
                    )
                    return False
        except pyodbc.Error as e:
            logging.error(f"Erro ao registrar fim do log de acesso ID {log_id}: {e}")
            return False

    # --- MÉTODOS DO PAINEL ADMIN (RESTANTES) ---

    def admin_get_all_users(self) -> List[Tuple]:
        query = "SELECT Usu_Id, Usu_Nome, Usu_Ativo, Usu_Is_Admin FROM Usuario_Sistema_WTS ORDER BY Usu_Nome"
        cursor = self._connect()
        if not cursor:
            return []
        try:
            with cursor:
                return cursor.execute(query).fetchall()
        except pyodbc.Error as e:
            logging.error(f"Admin: Erro ao buscar usuários: {e}")
        return []

    def admin_get_user_details(self, user_id: int) -> Optional[Dict[str, Any]]:
        query_user = "SELECT Usu_Nome, Usu_Email, Usu_Ativo, Usu_Is_Admin FROM Usuario_Sistema_WTS WHERE Usu_Id = ?"
        query_groups = "SELECT Gru_Codigo FROM Permissao_Grupo_WTS WHERE Usu_Id = ?"
        cursor = self._connect()
        if not cursor:
            return None
        try:
            with cursor:
                user_result = cursor.execute(query_user, user_id).fetchone()
                if not user_result:
                    return None
                user_details = {
                    "nome": user_result.Usu_Nome,
                    "email": user_result.Usu_Email or "",
                    "is_active": user_result.Usu_Ativo,
                    "is_admin": user_result.Usu_Is_Admin,
                    "grupos": set(),
                }
                group_results = cursor.execute(query_groups, user_id).fetchall()
                for row in group_results:
                    user_details["grupos"].add(row.Gru_Codigo)
                return user_details
        except pyodbc.Error as e:
            logging.error(f"Admin: Erro ao buscar detalhes do usuário {user_id}: {e}")
        return None

    def admin_create_user(
        self, username: str, email: str, is_admin: bool, is_active: bool, group_ids: List[int]
    ) -> Tuple[bool, str]:
        conn = self._get_connection()
        if not conn:
            return False, "Falha ao conectar."
        try:
            with conn.cursor() as cursor:
                q_create = "INSERT INTO Usuario_Sistema_WTS (Usu_Nome, Usu_Email, Usu_Ativo, Usu_Is_Admin) VALUES (?, ?, ?, ?);"
                cursor.execute(q_create, (username, email or None, is_active, is_admin))
                new_user_id = cursor.execute("SELECT @@IDENTITY AS ID;").fetchone()[0]
                if group_ids:
                    q_groups = "INSERT INTO Permissao_Grupo_WTS (Usu_Id, Gru_Codigo) VALUES (?, ?)"
                    params = [(new_user_id, gid) for gid in group_ids]
                    cursor.executemany(q_groups, params)
                conn.commit()
                return True, "Usuário criado."
        except pyodbc.Error as e:
            conn.rollback()
            logging.error(f"Admin: Erro ao CRIAR usuário: {e}")
            if "UNIQUE KEY" in str(e) or "Violation of UNIQUE KEY" in str(e):
                return False, f"Erro: Nome '{username}' já existe."
            return False, f"Erro DB: {e}"
        except Exception as ex:
            conn.rollback()
            logging.error(f"Admin: Erro inesperado ao CRIAR usuário: {ex}")
            return False, f"Erro: {ex}"
        finally:
            conn.autocommit = True  # Restaura autocommit

    def admin_update_user(
        self,
        user_id: int,
        username: str,
        email: str,
        is_admin: bool,
        is_active: bool,
        group_ids: List[int],
    ) -> Tuple[bool, str]:
        conn = self._get_connection()
        if not conn:
            return False, "Falha ao conectar."
        try:
            with conn.cursor() as cursor:
                q_update = "UPDATE Usuario_Sistema_WTS SET Usu_Nome = ?, Usu_Email = ?, Usu_Ativo = ?, Usu_Is_Admin = ? WHERE Usu_Id = ?"
                cursor.execute(q_update, (username, email or None, is_active, is_admin, user_id))
                q_delete = "DELETE FROM Permissao_Grupo_WTS WHERE Usu_Id = ?"
                cursor.execute(q_delete, (user_id,))
                if group_ids:
                    q_insert = "INSERT INTO Permissao_Grupo_WTS (Usu_Id, Gru_Codigo) VALUES (?, ?)"
                    params = [(user_id, gid) for gid in group_ids]
                    cursor.executemany(q_insert, params)
                conn.commit()
                return True, "Usuário atualizado."
        except pyodbc.Error as e:
            conn.rollback()
            logging.error(f"Admin: Erro ao ATUALIZAR usuário: {e}")
            if "UNIQUE KEY" in str(e) or "Violation of UNIQUE KEY" in str(e):
                return False, f"Erro: Nome '{username}' já existe."
            return False, f"Erro DB: {e}"
        except Exception as ex:
            conn.rollback()
            logging.error(f"Admin: Erro inesperado ao ATUALIZAR usuário: {ex}")
            return False, f"Erro: {ex}"
        finally:
            conn.autocommit = True

    def admin_get_all_groups(self) -> List[Tuple]:
        query = "SELECT Gru_Codigo, Gru_Nome FROM Grupo_WTS ORDER BY Gru_Nome"
        cursor = self._connect()
        if not cursor:
            return []
        try:
            with cursor:
                return cursor.execute(query).fetchall()
        except pyodbc.Error as e:
            logging.error(f"Admin: Erro ao buscar grupos: {e}")
        return []

    def admin_get_group_details(self, group_id: int) -> Optional[Dict[str, str]]:
        query = "SELECT Gru_Nome, Gru_Descricao FROM Grupo_WTS WHERE Gru_Codigo = ?"
        cursor = self._connect()
        if not cursor:
            return None
        try:
            with cursor:
                result = cursor.execute(query, group_id).fetchone()
                if result:
                    return {"nome": result.Gru_Nome, "desc": result.Gru_Descricao or ""}
        except pyodbc.Error as e:
            logging.error(f"Admin: Erro ao buscar detalhes do grupo {group_id}: {e}")
        return None

    def admin_create_group(self, nome: str, desc: Optional[str]) -> Tuple[bool, str]:
        query = "INSERT INTO Grupo_WTS (Gru_Nome, Gru_Descricao) VALUES (?, ?)"
        cursor = self._connect()
        if not cursor:
            return False, "Falha ao conectar."
        try:
            with cursor:
                cursor.execute(query, (nome, desc))
                return True, "Grupo criado."
        except pyodbc.Error as e:
            logging.error(f"Admin: Erro ao CRIAR grupo: {e}")
            if "UNIQUE KEY" in str(e) or "Violation of UNIQUE KEY" in str(e):
                return False, f"Erro: Nome '{nome}' já existe."
            return False, f"Erro DB: {e}"

    def admin_update_group(self, group_id: int, nome: str, desc: Optional[str]) -> Tuple[bool, str]:
        query = "UPDATE Grupo_WTS SET Gru_Nome = ?, Gru_Descricao = ? WHERE Gru_Codigo = ?"
        cursor = self._connect()
        if not cursor:
            return False, "Falha ao conectar."
        try:
            with cursor:
                cursor.execute(query, (nome, desc, group_id))
                return True, "Grupo atualizado."
        except pyodbc.Error as e:
            logging.error(f"Admin: Erro ao ATUALIZAR grupo: {e}")
            if "UNIQUE KEY" in str(e) or "Violation of UNIQUE KEY" in str(e):
                return False, f"Erro: Nome '{nome}' já existe."
            return False, f"Erro DB: {e}"

    def admin_delete_group(self, group_id: int) -> Tuple[bool, str]:
        query = "DELETE FROM Grupo_WTS WHERE Gru_Codigo = ?"
        cursor = self._connect()
        if not cursor:
            return False, "Falha ao conectar."
        try:
            with cursor:
                cursor.execute(query, group_id)
                return True, "Grupo deletado."
        except pyodbc.Error as e:
            logging.error(f"Admin: Erro ao DELETAR grupo: {e}")
            if "REFERENCE constraint" in str(e):
                return False, "Erro: Grupo em uso por conexões ou permissões."
            return False, f"Erro DB: {e}"

    # ### ALTERADO: Métodos de Conexão agora incluem 'con_tipo' ###

    def admin_get_all_connections(self) -> List[Tuple]:
        query = "SELECT c.Con_Codigo, c.Con_Nome, g.Gru_Nome, c.con_tipo FROM Conexao_WTS c LEFT JOIN Grupo_WTS g ON c.Gru_Codigo = g.Gru_Codigo ORDER BY ISNULL(g.Gru_Nome, c.Con_Nome), c.Con_Nome"
        cursor = self._connect()
        if not cursor:
            return []
        try:
            with cursor:
                return cursor.execute(query).fetchall()
        except pyodbc.Error as e:
            logging.error(f"Admin: Erro ao buscar conexões: {e}")
        return []

    def admin_get_connection_details(self, con_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM Conexao_WTS WHERE Con_Codigo = ?"
        cursor = self._connect()
        if not cursor:
            return None
        try:
            with cursor:
                result = cursor.execute(query, con_id).fetchone()
                if result:
                    return dict(zip([col[0] for col in result.cursor_description], result))
        except pyodbc.Error as e:
            logging.error(f"Admin: Erro ao buscar detalhes da conexão {con_id}: {e}")
        return None

    def admin_create_connection(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        query = """
            INSERT INTO Conexao_WTS
            (con_nome, gru_codigo, con_ip, con_usuario, con_senha,
             con_particularidade, con_cliente, extra, sec, con_tipo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data.get("con_nome"),
            data.get("gru_codigo"),
            data.get("con_ip"),
            data.get("con_usuario"),
            data.get("con_senha"),
            data.get("con_particularidade"),
            data.get("con_cliente"),
            data.get("extra"),
            data.get("sec", None),
            data.get("con_tipo", "RDP"),  # Assume RDP se não especificado
        )
        cursor = self._connect()
        if not cursor:
            return False, "Falha ao conectar."
        try:
            with cursor:
                cursor.execute(query, params)
                return True, "Conexão criada."
        except pyodbc.Error as e:
            logging.error(f"Admin: Erro ao CRIAR conexão: {e}")
            return False, f"Erro DB: {e}"

    def admin_update_connection(self, con_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
        query = """
            UPDATE Conexao_WTS
            SET con_nome = ?, gru_codigo = ?, con_ip = ?, con_usuario = ?, con_senha = ?,
                con_particularidade = ?, con_cliente = ?, extra = ?, sec = ?, con_tipo = ?
            WHERE Con_Codigo = ?
        """
        params = (
            data.get("con_nome"),
            data.get("gru_codigo"),
            data.get("con_ip"),
            data.get("con_usuario"),
            data.get("con_senha"),
            data.get("con_particularidade"),
            data.get("con_cliente"),
            data.get("extra"),
            data.get("sec", None),
            data.get("con_tipo", "RDP"),
            con_id,
        )
        cursor = self._connect()
        if not cursor:
            return False, "Falha ao conectar."
        try:
            with cursor:
                cursor.execute(query, params)
                return True, "Conexão atualizada."
        except pyodbc.Error as e:
            logging.error(f"Admin: Erro ao ATUALIZAR conexão: {e}")
            return False, f"Erro DB: {e}"

    def admin_delete_connection(self, con_id: int) -> Tuple[bool, str]:
        q_logs = "DELETE FROM Usuario_Conexao_WTS WHERE Con_Codigo = ?"
        q_access = "DELETE FROM Log_Acesso_WTS WHERE Con_Codigo = ?"  # <-- NOVO: Deleta logs de acesso também
        q_conn = "DELETE FROM Conexao_WTS WHERE Con_Codigo = ?"

        conn = self._get_connection()
        if not conn:
            return False, "Falha ao conectar."
        try:
            with conn.cursor() as cursor:
                cursor.execute(q_logs, con_id)
                cursor.execute(q_access, con_id)  # <-- NOVO
                cursor.execute(q_conn, con_id)
                conn.commit()
                return True, "Conexão e logs relacionados deletados."
        except pyodbc.Error as e:
            conn.rollback()
            logging.error(f"Admin: Erro ao DELETAR conexão {con_id}: {e}")
            if "REFERENCE constraint" in str(e):
                return False, "Erro: Conexão referenciada em outra tabela."
            return False, f"Erro DB: {e}"
        except Exception as ex:
            conn.rollback()
            logging.error(f"Admin: Erro inesperado ao DELETAR conexão {con_id}: {ex}")
            return False, f"Erro: {ex}"
        finally:
            conn.autocommit = True

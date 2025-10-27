# WATS_Project/src/wats/db/repositories/session_protection_repository.py

import logging
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from src.wats.db.repositories.base_repository import BaseRepository
from src.wats.db.exceptions import DatabaseQueryError, DatabaseConnectionError
from src.wats.db.demo_adapter import DemoAdapter


class SessionProtectionRepository(BaseRepository):
    """Gerencia operações de proteção de sessões temporárias."""

    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.demo_adapter = DemoAdapter(db_manager)

    def _hash_password(self, password: str) -> str:
        """Gera hash SHA-256 da senha."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def _create_protection_direct(self, cursor, con_codigo, user_name, machine_name, 
                                 password_hash, duration_minutes, notes, ip_address):
        """Cria proteção diretamente via INSERT se SP não existir."""
        try:
            # Verifica se a tabela existe
            cursor.execute("""
                SELECT COUNT(*) FROM sys.tables 
                WHERE name = 'Sessao_Protecao_WTS'
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists == 0:
                logging.error("[DB] Tabela Sessao_Protecao_WTS não encontrada")
                # Cria a tabela se não existir
                self._create_protection_table(cursor)
            
            # Calcula data de expiração
            expiry_time = datetime.now() + timedelta(minutes=duration_minutes)
            
            # Insere diretamente na tabela
            cursor.execute("""
                INSERT INTO Sessao_Protecao_WTS (
                    Con_Codigo, Usu_Nome_Protetor, Usu_Maquina_Protetor, 
                    Prot_Senha_Hash, Prot_Data_Criacao, Prot_Data_Expiracao,
                    Prot_Duracao_Minutos, Prot_Observacoes, Prot_IP_Criador,
                    Prot_Status
                ) VALUES (?, ?, ?, ?, GETDATE(), ?, ?, ?, ?, 'ATIVA');
                SELECT SCOPE_IDENTITY() AS ProtectionId;
            """, (con_codigo, user_name, machine_name, password_hash, 
                  expiry_time, duration_minutes, notes, ip_address))
            
            result = cursor.fetchone()
            if result and result[0]:
                protection_id = int(result[0])
                logging.info(f"[DB] ✅ Proteção criada diretamente: ID={protection_id}")
                return True, "Proteção de sessão ativada com sucesso", protection_id
            else:
                logging.error("[DB] ❌ INSERT direto falhou")
                return False, "Erro ao criar proteção diretamente", None
                
        except Exception as e:
            logging.error(f"[DB] ❌ Erro no INSERT direto: {e}")
            return False, f"Erro ao criar proteção: {e}", None

    def _create_protection_table(self, cursor):
        """Cria a tabela de proteção de sessão se não existir."""
        try:
            logging.info("[DB] Criando tabela Sessao_Protecao_WTS...")
            cursor.execute("""
                CREATE TABLE [dbo].[Sessao_Protecao_WTS](
                    [Prot_Id] [int] IDENTITY(1,1) NOT NULL,
                    [Con_Codigo] [int] NOT NULL,
                    [Usu_Nome_Protetor] [nvarchar](100) NOT NULL,
                    [Usu_Maquina_Protetor] [nvarchar](100) NULL,
                    [Prot_Senha_Hash] [nvarchar](255) NOT NULL,
                    [Prot_Data_Criacao] [datetime] NOT NULL,
                    [Prot_Data_Expiracao] [datetime] NOT NULL,
                    [Prot_Data_Remocao] [datetime] NULL,
                    [Prot_Duracao_Minutos] [int] NOT NULL,
                    [Prot_Observacoes] [nvarchar](500) NULL,
                    [Prot_IP_Criador] [nvarchar](50) NULL,
                    [Prot_Status] [nvarchar](20) NOT NULL DEFAULT ('ATIVA'),
                    [Prot_Removida_Por] [nvarchar](100) NULL,
                    CONSTRAINT [PK_Sessao_Protecao_WTS] PRIMARY KEY CLUSTERED ([Prot_Id] ASC)
                );
                
                CREATE INDEX [IX_Sessao_Protecao_Con_Status] ON [dbo].[Sessao_Protecao_WTS] 
                    ([Con_Codigo], [Prot_Status]) INCLUDE ([Prot_Data_Expiracao]);
            """)
            logging.info("[DB] ✅ Tabela Sessao_Protecao_WTS criada com sucesso")
        except Exception as e:
            logging.error(f"[DB] ❌ Erro ao criar tabela: {e}")
            raise

    def _validate_password_direct(self, cursor, con_codigo, password_hash, 
                                 requesting_user, requesting_machine, ip_address):
        """Valida senha diretamente via SELECT se SP não existir."""
        try:
            # Busca proteção ativa para a conexão
            cursor.execute("""
                SELECT TOP 1 Prot_Id, Usu_Nome_Protetor, Prot_Senha_Hash
                FROM Sessao_Protecao_WTS
                WHERE Con_Codigo = ? 
                  AND Prot_Status = 'ATIVA'
                  AND Prot_Data_Expiracao > GETDATE()
                ORDER BY Prot_Data_Criacao DESC
            """, (con_codigo,))
            
            result = cursor.fetchone()
            
            if not result:
                logging.info(f"[DB] Nenhuma proteção ativa encontrada para conexão {con_codigo}")
                return {
                    "valid": False,
                    "protection_id": None,
                    "protected_by": None,
                    "message": "Servidor não está protegido"
                }
            
            prot_id, protected_by, stored_hash = result
            
            # Verifica se a senha está correta
            if password_hash == stored_hash:
                logging.info(f"[DB] ✅ Senha correta: {requesting_user} → Servidor {con_codigo}")
                
                # Registra tentativa bem-sucedida
                self._log_access_attempt(cursor, prot_id, con_codigo, requesting_user, 
                                       requesting_machine, ip_address, 'SUCESSO')
                
                return {
                    "valid": True,
                    "protection_id": prot_id,
                    "protected_by": protected_by,
                    "message": "Senha correta - acesso autorizado"
                }
            else:
                logging.warning(f"[DB] ❌ Senha incorreta: {requesting_user} → Servidor {con_codigo}")
                
                # Registra tentativa malsucedida
                self._log_access_attempt(cursor, prot_id, con_codigo, requesting_user, 
                                       requesting_machine, ip_address, 'SENHA_INCORRETA')
                
                return {
                    "valid": False,
                    "protection_id": prot_id,
                    "protected_by": protected_by,
                    "message": "Senha de proteção incorreta"
                }
                
        except Exception as e:
            logging.error(f"[DB] ❌ Erro na validação direta: {e}")
            return {
                "valid": False,
                "protection_id": None,
                "protected_by": None,
                "message": f"Erro na validação: {e}"
            }

    def _log_access_attempt(self, session_id: int, user: str, machine_name: str, ip_address: str, 
                            success: bool, cursor) -> bool:
        """Registra tentativa de acesso para auditoria."""
        try:
            # Tenta usar stored procedure primeiro
            try:
                cursor.callproc('sp_Log_Tentativa_Protecao', (
                    session_id, user, machine_name, ip_address, success
                ))
                logging.debug(f"[DB] Tentativa de acesso registrada via stored procedure")
                return True
            except Exception as sp_error:
                logging.warning(f"[DB] Falha na stored procedure de log: {sp_error}")
                
                # Fallback: INSERT direto
                cursor.execute("""
                    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
                                   WHERE TABLE_NAME = 'Log_Tentativa_Protecao_WTS')
                    BEGIN
                        CREATE TABLE Log_Tentativa_Protecao_WTS (
                            id INT IDENTITY(1,1) PRIMARY KEY,
                            sessao_id INT NOT NULL,
                            usuario NVARCHAR(100) NOT NULL,
                            maquina NVARCHAR(100),
                            ip_address NVARCHAR(50),
                            sucesso BIT NOT NULL,
                            data_tentativa DATETIME2 DEFAULT GETDATE()
                        )
                    END
                """)
                
                cursor.execute("""
                    INSERT INTO Log_Tentativa_Protecao_WTS 
                    (sessao_id, usuario, maquina, ip_address, sucesso)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, user, machine_name, ip_address, success))
                
                logging.debug(f"[DB] Tentativa de acesso registrada via INSERT direto")
                return True
                
        except Exception as e:
            logging.error(f"[DB] Erro ao registrar tentativa de acesso: {e}")
            return False

    def create_session_protection(
        self,
        con_codigo: int,
        user_name: str,
        machine_name: str,
        password: str,
        duration_minutes: int,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Cria proteção de sessão para um servidor.
        
        Returns:
            (success, message, protection_id)
        """
        if self.demo_adapter.should_use_mock():
            logging.info(f"[DEMO] Proteção criada para conexão {con_codigo} por {user_name}")
            return True, "Proteção criada (modo demo)", 999

        try:
            password_hash = self._hash_password(password)
            logging.info(f"[DB] Criando proteção: con_codigo={con_codigo}, user={user_name}, machine={machine_name}")
            
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                # Verifica se a stored procedure existe
                cursor.execute("""
                    SELECT COUNT(*) FROM sys.objects 
                    WHERE type = 'P' AND name = 'sp_Criar_Protecao_Sessao'
                """)
                sp_exists = cursor.fetchone()[0]
                
                if sp_exists == 0:
                    logging.error("[DB] Stored procedure sp_Criar_Protecao_Sessao não encontrada")
                    # Usa INSERT direto se a SP não existir
                    return self._create_protection_direct(cursor, con_codigo, user_name, machine_name, 
                                                        password_hash, duration_minutes, notes, ip_address)
                
                # Chama stored procedure para criar proteção
                logging.info(f"[DB] Executando SP com senha hash: {password_hash[:10]}...")
                cursor.execute("""
                    DECLARE @Prot_Id INT;
                    EXEC sp_Criar_Protecao_Sessao 
                        @Con_Codigo = ?,
                        @Usu_Nome_Protetor = ?,
                        @Usu_Maquina_Protetor = ?,
                        @Prot_Senha_Hash = ?,
                        @Prot_Duracao_Minutos = ?,
                        @Prot_Observacoes = ?,
                        @Prot_IP_Criador = ?,
                        @Prot_Id = @Prot_Id OUTPUT;
                    SELECT @Prot_Id AS ProtectionId;
                """, (con_codigo, user_name, machine_name, password_hash, 
                      duration_minutes, notes, ip_address))
                
                result = cursor.fetchone()
                if result and result[0]:
                    protection_id = result[0]
                    logging.info(f"[DB] ✅ Proteção criada: ID={protection_id}, Servidor={con_codigo}, Usuário={user_name}")
                    return True, "Proteção de sessão ativada com sucesso", protection_id
                else:
                    logging.error(f"[DB] ❌ SP retornou resultado nulo")
                    return False, "Erro ao criar proteção", None
                    
        except self.driver_module.Error as e:
            logging.error(f"Erro ao criar proteção de sessão: {e}")
            return False, f"Erro no banco de dados: {e}", None
        except Exception as e:
            logging.error(f"Erro inesperado ao criar proteção: {e}")
            return False, f"Erro inesperado: {e}", None

    def validate_session_password(
        self,
        con_codigo: int,
        password: str,
        requesting_user: str,
        requesting_machine: str,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Valida senha de proteção de sessão.
        
        Returns:
            Dict com resultado da validação
        """
        if self.demo_adapter.should_use_mock():
            logging.info(f"[DEMO] Validação de senha simulada para {requesting_user}")
            return {
                "valid": True,
                "protection_id": 999,
                "protected_by": "demo_user",
                "message": "Acesso autorizado (modo demo)"
            }

        try:
            password_hash = self._hash_password(password)
            logging.info(f"[DB] Validando senha para conexão {con_codigo}, usuário {requesting_user}")
            
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                # Verifica se a stored procedure existe
                cursor.execute("""
                    SELECT COUNT(*) FROM sys.objects 
                    WHERE type = 'P' AND name = 'sp_Validar_Protecao_Sessao'
                """)
                sp_exists = cursor.fetchone()[0]
                
                if sp_exists == 0:
                    logging.info("[DB] SP de validação não encontrada, usando validação direta")
                    return self._validate_password_direct(cursor, con_codigo, password_hash, 
                                                        requesting_user, requesting_machine, ip_address)
                
                # Chama stored procedure para validar
                cursor.execute("""
                    DECLARE @Resultado NVARCHAR(20);
                    DECLARE @Prot_Id INT;
                    DECLARE @Usu_Nome_Protetor NVARCHAR(100);
                    
                    EXEC sp_Validar_Protecao_Sessao 
                        @Con_Codigo = ?,
                        @Prot_Senha_Hash = ?,
                        @Usu_Nome_Solicitante = ?,
                        @Usu_Maquina_Solicitante = ?,
                        @LTent_IP_Solicitante = ?,
                        @Resultado = @Resultado OUTPUT,
                        @Prot_Id = @Prot_Id OUTPUT,
                        @Usu_Nome_Protetor = @Usu_Nome_Protetor OUTPUT;
                    
                    SELECT @Resultado AS Resultado, @Prot_Id AS ProtectionId, @Usu_Nome_Protetor AS ProtectedBy;
                """, (con_codigo, password_hash, requesting_user, requesting_machine, ip_address))
                
                result = cursor.fetchone()
                if result:
                    resultado = result[0]
                    protection_id = result[1]
                    protected_by = result[2]
                    
                    if resultado == 'SUCESSO':
                        logging.info(f"[DB] ✅ Acesso autorizado: {requesting_user} → Servidor {con_codigo}")
                        return {
                            "valid": True,
                            "protection_id": protection_id,
                            "protected_by": protected_by,
                            "message": "Senha correta - acesso autorizado"
                        }
                    elif resultado == 'SENHA_INCORRETA':
                        logging.warning(f"[DB] ❌ Senha incorreta: {requesting_user} → Servidor {con_codigo}")
                        return {
                            "valid": False,
                            "protection_id": protection_id,
                            "protected_by": protected_by,
                            "message": "Senha de proteção incorreta"
                        }
                    elif resultado == 'NEGADA':
                        return {
                            "valid": False,
                            "protection_id": None,
                            "protected_by": None,
                            "message": "Servidor não está protegido"
                        }
                    else:
                        return {
                            "valid": False,
                            "protection_id": protection_id,
                            "protected_by": protected_by,
                            "message": f"Acesso negado: {resultado}"
                        }
                else:
                    return {
                        "valid": False,
                        "protection_id": None,
                        "protected_by": None,
                        "message": "Erro na validação"
                    }
                    
        except self.driver_module.Error as e:
            logging.error(f"Erro ao validar proteção de sessão: {e}")
            return {
                "valid": False,
                "protection_id": None,
                "protected_by": None,
                "message": f"Erro no banco de dados: {e}"
            }
        except Exception as e:
            logging.error(f"Erro inesperado na validação: {e}")
            return {
                "valid": False,
                "protection_id": None,
                "protected_by": None,
                "message": f"Erro inesperado: {e}"
            }

    def remove_session_protection(
        self,
        con_codigo: int,
        removing_user: str
    ) -> Tuple[bool, str]:
        """
        Remove proteção de sessão.
        
        Returns:
            (success, message)
        """
        if self.demo_adapter.should_use_mock():
            logging.info(f"[DEMO] Proteção removida para conexão {con_codigo} por {removing_user}")
            return True, "Proteção removida (modo demo)"

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                # Chama stored procedure para remover
                cursor.execute("""
                    DECLARE @Sucesso BIT;
                    EXEC sp_Remover_Protecao_Sessao 
                        @Con_Codigo = ?,
                        @Usu_Nome_Removedor = ?,
                        @Sucesso = @Sucesso OUTPUT;
                    SELECT @Sucesso AS Sucesso;
                """, (con_codigo, removing_user))
                
                result = cursor.fetchone()
                if result and result[0]:
                    logging.info(f"Proteção removida: Servidor={con_codigo}, Por={removing_user}")
                    return True, "Proteção de sessão removida com sucesso"
                else:
                    return False, "Não foi possível remover a proteção. Verifique se você é o criador da proteção."
                    
        except self.driver_module.Error as e:
            logging.error(f"Erro ao remover proteção de sessão: {e}")
            return False, f"Erro no banco de dados: {e}"
        except Exception as e:
            logging.error(f"Erro inesperado ao remover proteção: {e}")
            return False, f"Erro inesperado: {e}"

    def is_session_protected(self, con_codigo: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verifica se uma sessão está protegida.
        
        Returns:
            (is_protected, protection_info)
        """
        if self.demo_adapter.should_use_mock():
            return False, None

        try:
            # Primeiro limpa proteções expiradas
            self.cleanup_expired_protections()
            
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                query = """
                    SELECT TOP 1
                        sp.Prot_Id,
                        sp.Usu_Nome_Protetor,
                        sp.Usu_Maquina_Protetor,
                        sp.Prot_Data_Criacao,
                        sp.Prot_Data_Expiracao,
                        sp.Prot_Observacoes,
                        sp.Prot_Duracao_Minutos,
                        DATEDIFF(MINUTE, GETDATE(), sp.Prot_Data_Expiracao) AS MinutosRestantes,
                        c.Con_Nome
                    FROM Sessao_Protecao_WTS sp
                    INNER JOIN Conexao_WTS c ON sp.Con_Codigo = c.Con_Codigo
                    WHERE sp.Con_Codigo = ? 
                      AND sp.Prot_Status = 'ATIVA'
                      AND sp.Prot_Data_Expiracao > GETDATE()
                    ORDER BY sp.Prot_Data_Criacao DESC
                """
                
                cursor.execute(query, (con_codigo,))
                result = cursor.fetchone()
                
                if result:
                    protection_info = {
                        "protection_id": result[0],
                        "protected_by": result[1],
                        "machine": result[2],
                        "created_at": result[3],
                        "expires_at": result[4],
                        "notes": result[5] or "",
                        "duration_minutes": result[6],
                        "minutes_remaining": result[7],
                        "connection_name": result[8]
                    }
                    return True, protection_info
                else:
                    return False, None
                    
        except self.driver_module.Error as e:
            logging.error(f"Erro ao verificar proteção de sessão: {e}")
            return False, None
        except Exception as e:
            logging.error(f"Erro inesperado ao verificar proteção: {e}")
            return False, None

    def get_user_protected_sessions(self, user_name: str) -> List[Dict[str, Any]]:
        """Retorna lista de sessões protegidas pelo usuário."""
        if self.demo_adapter.should_use_mock():
            return []

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                query = """
                    SELECT 
                        sp.Prot_Id,
                        sp.Con_Codigo,
                        c.Con_Nome,
                        c.Con_IP,
                        sp.Prot_Data_Criacao,
                        sp.Prot_Data_Expiracao,
                        sp.Prot_Observacoes,
                        DATEDIFF(MINUTE, GETDATE(), sp.Prot_Data_Expiracao) AS MinutosRestantes
                    FROM Sessao_Protecao_WTS sp
                    INNER JOIN Conexao_WTS c ON sp.Con_Codigo = c.Con_Codigo
                    WHERE sp.Usu_Nome_Protetor = ?
                      AND sp.Prot_Status = 'ATIVA'
                      AND sp.Prot_Data_Expiracao > GETDATE()
                    ORDER BY sp.Prot_Data_Criacao DESC
                """
                
                cursor.execute(query, (user_name,))
                results = cursor.fetchall()
                
                protections = []
                for row in results:
                    protections.append({
                        "protection_id": row[0],
                        "connection_id": row[1],
                        "connection_name": row[2],
                        "connection_ip": row[3],
                        "created_at": row[4],
                        "expires_at": row[5],
                        "notes": row[6] or "",
                        "minutes_remaining": row[7]
                    })
                
                return protections
                
        except self.driver_module.Error as e:
            logging.error(f"Erro ao buscar proteções do usuário: {e}")
            return []
        except Exception as e:
            logging.error(f"Erro inesperado ao buscar proteções: {e}")
            return []

    def cleanup_expired_protections(self) -> int:
        """Limpa proteções expiradas."""
        if self.demo_adapter.should_use_mock():
            return 0

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                cursor.execute("EXEC sp_Limpar_Protecoes_Expiradas")
                
                # Procedure retorna número de registros atualizados
                # Como é um EXEC, não conseguimos pegar o RETURN value facilmente
                # então contamos manualmente
                cursor.execute("""
                    SELECT COUNT(*) FROM Sessao_Protecao_WTS 
                    WHERE Prot_Status = 'EXPIRADA'
                      AND Prot_Data_Expiracao < GETDATE()
                      AND Prot_Data_Expiracao > DATEADD(MINUTE, -5, GETDATE())
                """)
                
                result = cursor.fetchone()
                cleaned_count = result[0] if result else 0
                
                if cleaned_count > 0:
                    logging.info(f"Proteções expiradas limpas: {cleaned_count}")
                
                return cleaned_count
                
        except self.driver_module.Error as e:
            logging.error(f"Erro ao limpar proteções expiradas: {e}")
            return 0
        except Exception as e:
            logging.error(f"Erro inesperado na limpeza: {e}")
            return 0

    def get_protection_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema de proteção."""
        if self.demo_adapter.should_use_mock():
            return {
                "active_protections": 0,
                "total_attempts_today": 0,
                "successful_attempts_today": 0,
                "failed_attempts_today": 0
            }

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                # Proteções ativas
                cursor.execute("""
                    SELECT COUNT(*) FROM Sessao_Protecao_WTS 
                    WHERE Prot_Status = 'ATIVA' AND Prot_Data_Expiracao > GETDATE()
                """)
                active_protections = cursor.fetchone()[0]
                
                # Tentativas de hoje
                cursor.execute("""
                    SELECT 
                        COUNT(*) as Total,
                        SUM(CASE WHEN LTent_Resultado = 'SUCESSO' THEN 1 ELSE 0 END) as Sucessos,
                        SUM(CASE WHEN LTent_Resultado = 'SENHA_INCORRETA' THEN 1 ELSE 0 END) as Falhas
                    FROM Log_Tentativa_Protecao_WTS 
                    WHERE CAST(LTent_Data_Hora AS DATE) = CAST(GETDATE() AS DATE)
                """)
                
                result = cursor.fetchone()
                total_today = result[0] or 0
                success_today = result[1] or 0
                failed_today = result[2] or 0
                
                return {
                    "active_protections": active_protections,
                    "total_attempts_today": total_today,
                    "successful_attempts_today": success_today,
                    "failed_attempts_today": failed_today
                }
                
        except self.driver_module.Error as e:
            logging.error(f"Erro ao buscar estatísticas: {e}")
            return {}
        except Exception as e:
            logging.error(f"Erro inesperado nas estatísticas: {e}")
            return {}

    def cleanup_orphaned_protections(self) -> Tuple[bool, str, int]:
        """
        Remove proteções órfãs (usuários desconectados mas proteção ainda ativa).
        
        Returns:
            (success, message, count_removed)
        """
        if self.demo_adapter.should_use_mock():
            logging.info("[DEMO] Limpeza de proteções órfãs simulada")
            return True, "Limpeza simulada (modo demo)", 0

        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                # Busca proteções ativas cujos criadores não estão mais conectados
                cursor.execute("""
                    UPDATE sp
                    SET [Prot_Status] = 'REMOVIDA',
                        [Prot_Data_Remocao] = GETDATE(),
                        [Prot_Removida_Por] = 'SISTEMA_LIMPEZA_AUTOMATICA'
                    FROM [dbo].[Sessao_Protecao_WTS] sp
                    WHERE sp.Prot_Status = 'ATIVA'
                      AND NOT EXISTS (
                          SELECT 1 FROM [dbo].[Usuario_Conexao_WTS] uc 
                          WHERE uc.Con_Codigo = sp.Con_Codigo 
                            AND uc.Usu_Nome = sp.Usu_Nome_Protetor
                      );
                      
                    SELECT @@ROWCOUNT as ProtectionsRemoved;
                """)
                
                result = cursor.fetchone()
                count_removed = result[0] if result else 0
                
                # Log das proteções removidas
                if count_removed > 0:
                    cursor.execute("""
                        INSERT INTO [dbo].[Log_Tentativa_Protecao_WTS] (
                            [Prot_Id], [Con_Codigo], [Usu_Nome_Solicitante], 
                            [LTent_Resultado], [LTent_Observacoes]
                        )
                        SELECT 
                            sp.Prot_Id, 
                            sp.Con_Codigo, 
                            'SISTEMA_LIMPEZA',
                            'CANCELADA',
                            'Proteção órfã removida - usuário não está mais conectado'
                        FROM [dbo].[Sessao_Protecao_WTS] sp
                        WHERE sp.Prot_Status = 'REMOVIDA' 
                          AND sp.Prot_Removida_Por = 'SISTEMA_LIMPEZA_AUTOMATICA'
                          AND sp.Prot_Data_Remocao >= DATEADD(MINUTE, -1, GETDATE())
                    """)
                
                logging.info(f"Limpeza automática: {count_removed} proteções órfãs removidas")
                return True, f"Limpeza concluída: {count_removed} proteções removidas", count_removed
                
        except self.driver_module.Error as e:
            logging.error(f"Erro na limpeza de proteções órfãs: {e}")
            return False, f"Erro no banco de dados: {e}", 0
        except Exception as e:
            logging.error(f"Erro inesperado na limpeza: {e}")
            return False, f"Erro inesperado: {e}", 0
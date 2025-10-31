# WATS_Project/src/wats/db/repositories/session_protection_repository.py

import logging
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from src.wats.db.repositories.base_repository import BaseRepository
from src.wats.db.exceptions import DatabaseQueryError, DatabaseConnectionError


class SessionProtectionRepository(BaseRepository):
    """Gerencia operações de proteção de sessões temporárias."""

    def __init__(self, db_manager):
        super().__init__(db_manager)

    def _hash_password(self, password: str) -> str:
        """Gera hash SHA-256 da senha."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def _create_protection_direct(self, cursor, con_codigo, user_name, machine_name, 
                                 password_hash, duration_minutes, notes, ip_address):
        """Cria proteção diretamente via INSERT se SP não existir."""
        try:
            logging.info(f"[DB_PROTECTION] Iniciando criação direta de proteção - con_codigo={con_codigo}, user={user_name}")
            logging.debug(f"[DB_PROTECTION] Parâmetros: machine={machine_name}, duration={duration_minutes}min, ip={ip_address}")
            logging.debug(f"[DB_PROTECTION] Hash da senha (primeiros 10 chars): {password_hash[:10]}...")
            
            # Verifica se a tabela existe
            cursor.execute("""
                SELECT COUNT(*) FROM sys.tables 
                WHERE name = 'Sessao_Protecao_WTS'
            """)
            table_exists = cursor.fetchone()[0]
            logging.info(f"[DB_PROTECTION] Verificação da tabela: existe={table_exists > 0}")
            
            if table_exists == 0:
                logging.warning("[DB_PROTECTION] Tabela Sessao_Protecao_WTS não encontrada - criando...")
                # Cria a tabela se não existir
                self._create_protection_table(cursor)
                logging.info("[DB_PROTECTION] Tabela criada com sucesso")
            
            # Calcula data de expiração
            expiry_time = datetime.now() + timedelta(minutes=duration_minutes)
            logging.info(f"[DB_PROTECTION] Data de expiração calculada: {expiry_time}")
            
            # Insere diretamente na tabela
            logging.info("[DB_PROTECTION] Executando INSERT na tabela Sessao_Protecao_WTS...")
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
                logging.info(f"[DB_PROTECTION] ✅ Proteção criada com sucesso!")
                logging.info(f"[DB_PROTECTION] ID da proteção: {protection_id}")
                logging.info(f"[DB_PROTECTION] Conexão: {con_codigo} | Usuário: {user_name}")
                logging.info(f"[DB_PROTECTION] Hash armazenado: {password_hash}")
                
                # Verifica se foi realmente inserido
                cursor.execute("SELECT COUNT(*) FROM Sessao_Protecao_WTS WHERE Prot_Id = ?", (protection_id,))
                verify_count = cursor.fetchone()[0]
                logging.info(f"[DB_PROTECTION] Verificação pós-inserção: registro encontrado={verify_count > 0}")
                
                return True, "Proteção de sessão ativada com sucesso", protection_id
            else:
                logging.error("[DB_PROTECTION] ❌ INSERT retornou resultado nulo ou inválido")
                logging.error(f"[DB_PROTECTION] Resultado do SCOPE_IDENTITY: {result}")
                return False, "Erro ao criar proteção diretamente", None
                
        except Exception as e:
            logging.error(f"[DB_PROTECTION] ❌ Erro crítico no INSERT direto: {e}")
            logging.error(f"[DB_PROTECTION] Tipo do erro: {type(e).__name__}")
            logging.error(f"[DB_PROTECTION] Detalhes dos parâmetros que falharam:")
            logging.error(f"[DB_PROTECTION]   - con_codigo: {con_codigo}")
            logging.error(f"[DB_PROTECTION]   - user_name: {user_name}")
            logging.error(f"[DB_PROTECTION]   - password_hash: {password_hash[:10]}...")
            return False, f"Erro ao criar proteção: {e}", None

    def _create_protection_table(self, cursor):
        """Cria a tabela de proteção de sessão se não existir."""
        try:
            logging.info("[DB_PROTECTION] 🔨 Iniciando criação da tabela Sessao_Protecao_WTS...")
            
            # Verifica novamente se a tabela não existe
            cursor.execute("""
                SELECT COUNT(*) FROM sys.tables 
                WHERE name = 'Sessao_Protecao_WTS'
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists > 0:
                logging.warning("[DB_PROTECTION] ⚠️ Tabela já existe, pulando criação")
                return
            
            logging.info("[DB_PROTECTION] Executando DDL para criar tabela...")
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
            """)
            logging.info("[DB_PROTECTION] ✅ Tabela criada com sucesso")
            
            logging.info("[DB_PROTECTION] Criando índices...")
            cursor.execute("""
                CREATE INDEX [IX_Sessao_Protecao_Con_Status] ON [dbo].[Sessao_Protecao_WTS] 
                    ([Con_Codigo], [Prot_Status]) INCLUDE ([Prot_Data_Expiracao]);
            """)
            logging.info("[DB_PROTECTION] ✅ Índices criados com sucesso")
            
            # Verifica se a tabela foi criada corretamente
            cursor.execute("""
                SELECT COUNT(*) FROM sys.tables 
                WHERE name = 'Sessao_Protecao_WTS'
            """)
            final_check = cursor.fetchone()[0]
            
            if final_check > 0:
                logging.info("[DB_PROTECTION] ✅ Verificação final: Tabela Sessao_Protecao_WTS criada e verificada")
                
                # Verifica estrutura da tabela
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'Sessao_Protecao_WTS'
                    ORDER BY ORDINAL_POSITION
                """)
                columns = cursor.fetchall()
                logging.info(f"[DB_PROTECTION] Estrutura da tabela criada: {len(columns)} colunas")
                for col in columns:
                    logging.debug(f"[DB_PROTECTION]   - {col[0]}: {col[1]}({col[2]}) NULL={col[3]}")
            else:
                logging.error("[DB_PROTECTION] ❌ Falha na verificação final da tabela")
                
        except Exception as e:
            logging.error(f"[DB_PROTECTION] ❌ Erro crítico ao criar tabela: {e}")
            logging.error(f"[DB_PROTECTION] Tipo do erro: {type(e).__name__}")
            raise

    def _validate_password_direct(self, cursor, con_codigo, password_hash, 
                                 requesting_user, requesting_machine, ip_address):
        """Valida senha diretamente via SELECT se SP não existir."""
        try:
            logging.info(f"[DB_PROTECTION] 🔍 VALIDAÇÃO DIRETA DE SENHA")
            logging.info(f"[DB_PROTECTION] Conexão: {con_codigo}, Usuário: {requesting_user}")
            logging.info(f"[DB_PROTECTION] Máquina: {requesting_machine}, IP: {ip_address}")
            logging.info(f"[DB_PROTECTION] Hash fornecido: {password_hash[:16]}...")
            
            # Busca proteção ativa para a conexão
            logging.info(f"[DB_PROTECTION] Buscando proteção ativa para conexão {con_codigo}...")
            cursor.execute("""
                SELECT TOP 1 Prot_Id, Usu_Nome_Protetor, Prot_Senha_Hash,
                       Prot_Data_Criacao, Prot_Data_Expiracao, Prot_Status
                FROM Sessao_Protecao_WTS
                WHERE Con_Codigo = ? 
                  AND Prot_Status = 'ATIVA'
                  AND Prot_Data_Expiracao > GETDATE()
                ORDER BY Prot_Data_Criacao DESC
            """, (con_codigo,))
            
            result = cursor.fetchone()
            logging.info(f"[DB_PROTECTION] Resultado da busca: {result is not None}")
            
            if not result:
                logging.warning(f"[DB_PROTECTION] ⚠️ Nenhuma proteção ativa encontrada")
                
                # Busca estatísticas para diagnóstico
                cursor.execute("""
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN Prot_Status = 'ATIVA' THEN 1 END) as ativas,
                           COUNT(CASE WHEN Prot_Data_Expiracao > GETDATE() THEN 1 END) as nao_expiradas
                    FROM Sessao_Protecao_WTS 
                    WHERE Con_Codigo = ?
                """, (con_codigo,))
                
                stats = cursor.fetchone()
                if stats:
                    logging.info(f"[DB_PROTECTION] Estatísticas para conexão {con_codigo}:")
                    logging.info(f"[DB_PROTECTION]   - Total de proteções: {stats[0]}")
                    logging.info(f"[DB_PROTECTION]   - Proteções ativas: {stats[1]}")
                    logging.info(f"[DB_PROTECTION]   - Proteções não expiradas: {stats[2]}")
                
                return {
                    "valid": False,
                    "protection_id": None,
                    "protected_by": None,
                    "message": "Servidor não está protegido"
                }
            
            prot_id, protected_by, stored_hash, data_criacao, data_expiracao, status = result
            
            logging.info(f"[DB_PROTECTION] Proteção encontrada:")
            logging.info(f"[DB_PROTECTION]   - ID: {prot_id}")
            logging.info(f"[DB_PROTECTION]   - Protegido por: {protected_by}")
            logging.info(f"[DB_PROTECTION]   - Hash armazenado: {stored_hash[:16]}...")
            logging.info(f"[DB_PROTECTION]   - Data criação: {data_criacao}")
            logging.info(f"[DB_PROTECTION]   - Data expiração: {data_expiracao}")
            logging.info(f"[DB_PROTECTION]   - Status: {status}")
            
            # Compara hashes
            logging.info(f"[DB_PROTECTION] Comparando hashes:")
            logging.info(f"[DB_PROTECTION]   - Hash fornecido: {password_hash[:16]}...")
            logging.info(f"[DB_PROTECTION]   - Hash armazenado: {stored_hash[:16]}...")
            logging.info(f"[DB_PROTECTION]   - Tamanho hash fornecido: {len(password_hash)}")
            logging.info(f"[DB_PROTECTION]   - Tamanho hash armazenado: {len(stored_hash)}")
            
            # Verifica se a senha está correta
            if password_hash == stored_hash:
                logging.info(f"[DB_PROTECTION] ✅ SENHA CORRETA!")
                logging.info(f"[DB_PROTECTION] Usuário {requesting_user} autorizado para servidor {con_codigo}")
                
                # Registra tentativa bem-sucedida
                logging.info(f"[DB_PROTECTION] Registrando tentativa bem-sucedida...")
                self._log_access_attempt(cursor, prot_id, con_codigo, requesting_user, 
                                       requesting_machine, ip_address, 'SUCESSO')
                
                logging.info(f"[DB_PROTECTION] 📝 AUDITORIA: Acesso direto autorizado")
                logging.info(f"[DB_PROTECTION] Proteção ID {prot_id} criada por {protected_by}")
                
                return {
                    "valid": True,
                    "protection_id": prot_id,
                    "protected_by": protected_by,
                    "message": "Senha correta - acesso autorizado"
                }
            else:
                logging.warning(f"[DB_PROTECTION] ❌ SENHA INCORRETA!")
                logging.warning(f"[DB_PROTECTION] Tentativa de acesso negada para {requesting_user}")
                
                # Registra tentativa malsucedida
                logging.warning(f"[DB_PROTECTION] Registrando tentativa malsucedida...")
                self._log_access_attempt(cursor, prot_id, con_codigo, requesting_user, 
                                       requesting_machine, ip_address, 'SENHA_INCORRETA')
                
                logging.warning(f"[DB_PROTECTION] 🚨 AUDITORIA: Senha incorreta na validação direta")
                logging.warning(f"[DB_PROTECTION] Conexão {con_codigo} protegida por {protected_by}")
                
                return {
                    "valid": False,
                    "protection_id": prot_id,
                    "protected_by": protected_by,
                    "message": "Senha de proteção incorreta"
                }
                
        except Exception as e:
            logging.error(f"[DB_PROTECTION] ❌ Erro na validação direta: {e}")
            logging.error(f"[DB_PROTECTION] Tipo de erro: {type(e).__name__}")
            import traceback
            logging.error(f"[DB_PROTECTION] Stack trace: {traceback.format_exc()}")
            return {
                "valid": False,
                "protection_id": None,
                "protected_by": None,
                "message": f"Erro na validação: {e}"
            }

    def _log_access_attempt(self, cursor, prot_id: int, con_codigo: int, user: str, 
                           machine_name: str, ip_address: str, result: str) -> bool:
        """Registra tentativa de acesso para auditoria."""
        try:
            logging.info(f"[DB_PROTECTION] 📝 REGISTRANDO TENTATIVA DE ACESSO")
            logging.info(f"[DB_PROTECTION] Dados do log:")
            logging.info(f"[DB_PROTECTION]   - Protection ID: {prot_id}")
            logging.info(f"[DB_PROTECTION]   - Conexão: {con_codigo}")
            logging.info(f"[DB_PROTECTION]   - Usuário: {user}")
            logging.info(f"[DB_PROTECTION]   - Máquina: {machine_name}")
            logging.info(f"[DB_PROTECTION]   - IP: {ip_address}")
            logging.info(f"[DB_PROTECTION]   - Resultado: {result}")
            
            success = result == 'SUCESSO'
            logging.info(f"[DB_PROTECTION] Sucesso convertido: {success}")
            
            # Tenta usar stored procedure primeiro
            try:
                logging.info(f"[DB_PROTECTION] Tentando stored procedure sp_Log_Tentativa_Protecao...")
                cursor.callproc('sp_Log_Tentativa_Protecao', (
                    prot_id, con_codigo, user, machine_name, ip_address, success
                ))
                logging.info(f"[DB_PROTECTION] ✅ Tentativa de acesso registrada via stored procedure")
                return True
            except Exception as sp_error:
                logging.warning(f"[DB_PROTECTION] ⚠️ Falha na stored procedure de log: {sp_error}")
                logging.info(f"[DB_PROTECTION] Usando fallback - INSERT direto...")
                
                # Verifica se a tabela de log existe
                cursor.execute("""
                    SELECT COUNT(*) FROM sys.tables 
                    WHERE name = 'Log_Tentativa_Protecao_WTS'
                """)
                log_table_exists = cursor.fetchone()[0]
                logging.info(f"[DB_PROTECTION] Tabela de log existe: {log_table_exists > 0}")
                
                # Cria tabela se não existir
                if log_table_exists == 0:
                    logging.info(f"[DB_PROTECTION] Criando tabela Log_Tentativa_Protecao_WTS...")
                    cursor.execute("""
                        CREATE TABLE Log_Tentativa_Protecao_WTS (
                            LTent_Id INT IDENTITY(1,1) PRIMARY KEY,
                            Prot_Id INT NOT NULL,
                            Con_Codigo INT NOT NULL,
                            LTent_Usuario NVARCHAR(100) NOT NULL,
                            LTent_Maquina NVARCHAR(100),
                            LTent_IP NVARCHAR(50),
                            LTent_Sucesso BIT NOT NULL,
                            LTent_Data DATETIME2 DEFAULT GETDATE(),
                            LTent_Resultado NVARCHAR(50)
                        )
                    """)
                    logging.info(f"[DB_PROTECTION] ✅ Tabela de log criada")
                
                # Insere registro de log
                logging.info(f"[DB_PROTECTION] Inserindo registro na tabela de log...")
                cursor.execute("""
                    INSERT INTO Log_Tentativa_Protecao_WTS 
                    (Prot_Id, Con_Codigo, LTent_Usuario, LTent_Maquina, LTent_IP, LTent_Sucesso, LTent_Resultado)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (prot_id, con_codigo, user, machine_name, ip_address, success, result))
                
                logging.info(f"[DB_PROTECTION] ✅ Tentativa de acesso registrada via INSERT direto")
                logging.info(f"[DB_PROTECTION] Log salvo: Prot_Id={prot_id}, User={user}, Result={result}")
                return True
                
        except Exception as e:
            logging.error(f"[DB_PROTECTION] ❌ Erro ao registrar tentativa de acesso: {e}")
            logging.error(f"[DB_PROTECTION] Tipo de erro: {type(e).__name__}")
            import traceback
            logging.error(f"[DB_PROTECTION] Stack trace: {traceback.format_exc()}")
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
        logging.info(f"[DB_PROTECTION] 🔐 INICIANDO CRIAÇÃO DE PROTEÇÃO DE SESSÃO")
        logging.info(f"[DB_PROTECTION] Parâmetros de entrada:")
        logging.info(f"[DB_PROTECTION]   - con_codigo: {con_codigo}")
        logging.info(f"[DB_PROTECTION]   - user_name: {user_name}")
        logging.info(f"[DB_PROTECTION]   - machine_name: {machine_name}")
        logging.info(f"[DB_PROTECTION]   - password length: {len(password) if password else 0} chars")
        logging.info(f"[DB_PROTECTION]   - duration_minutes: {duration_minutes}")
        logging.info(f"[DB_PROTECTION]   - notes: {notes[:50] if notes else 'None'}...")
        logging.info(f"[DB_PROTECTION]   - ip_address: {ip_address}")
        

        try:
            # Gera hash da senha
            logging.info("[DB_PROTECTION] Gerando hash SHA-256 da senha...")
            password_hash = self._hash_password(password)
            logging.info(f"[DB_PROTECTION] Hash gerado: {password_hash[:16]}...")
            logging.info(f"[DB_PROTECTION] Hash completo length: {len(password_hash)} chars")
            
            with self.db.get_cursor() as cursor:
                if not cursor:
                    logging.error("[DB_PROTECTION] ❌ Falha ao obter cursor do banco")
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                logging.info("[DB_PROTECTION] Cursor obtido com sucesso")
                
                # Verifica se a stored procedure existe
                logging.info("[DB_PROTECTION] Verificando existência da stored procedure...")
                cursor.execute("""
                    SELECT COUNT(*) FROM sys.objects 
                    WHERE type = 'P' AND name = 'sp_Criar_Protecao_Sessao'
                """)
                sp_exists = cursor.fetchone()[0]
                logging.info(f"[DB_PROTECTION] SP sp_Criar_Protecao_Sessao existe: {sp_exists > 0}")
                
                if sp_exists == 0:
                    logging.warning("[DB_PROTECTION] ⚠️ Stored procedure não encontrada - usando método direto")
                    # Usa INSERT direto se a SP não existir
                    result = self._create_protection_direct(cursor, con_codigo, user_name, machine_name, 
                                                        password_hash, duration_minutes, notes, ip_address)
                    logging.info(f"[DB_PROTECTION] Resultado método direto: success={result[0]}, msg='{result[1]}', id={result[2]}")
                    return result
                
                # Chama stored procedure para criar proteção
                logging.info("[DB_PROTECTION] Executando stored procedure sp_Criar_Protecao_Sessao...")
                logging.debug(f"[DB_PROTECTION] Parâmetros da SP:")
                logging.debug(f"[DB_PROTECTION]   @Con_Codigo = {con_codigo}")
                logging.debug(f"[DB_PROTECTION]   @Usu_Nome_Protetor = {user_name}")
                logging.debug(f"[DB_PROTECTION]   @Usu_Maquina_Protetor = {machine_name}")
                logging.debug(f"[DB_PROTECTION]   @Prot_Senha_Hash = {password_hash[:16]}...")
                logging.debug(f"[DB_PROTECTION]   @Prot_Duracao_Minutos = {duration_minutes}")
                logging.debug(f"[DB_PROTECTION]   @Prot_Observacoes = {notes}")
                logging.debug(f"[DB_PROTECTION]   @Prot_IP_Criador = {ip_address}")
                
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
                logging.info(f"[DB_PROTECTION] Resultado da SP: {result}")
                
                if result and result[0]:
                    protection_id = result[0]
                    logging.info(f"[DB_PROTECTION] ✅ PROTEÇÃO CRIADA COM SUCESSO VIA SP!")
                    logging.info(f"[DB_PROTECTION] ID da proteção: {protection_id}")
                    logging.info(f"[DB_PROTECTION] Conexão {con_codigo} protegida por {user_name}")
                    
                    # Verificação adicional no banco
                    cursor.execute("""
                        SELECT Prot_Id, Con_Codigo, Usu_Nome_Protetor, Prot_Status, 
                               Prot_Data_Criacao, Prot_Data_Expiracao, Prot_Senha_Hash
                        FROM Sessao_Protecao_WTS 
                        WHERE Prot_Id = ?
                    """, (protection_id,))
                    
                    verification = cursor.fetchone()
                    if verification:
                        logging.info(f"[DB_PROTECTION] ✅ Verificação no banco:")
                        logging.info(f"[DB_PROTECTION]   - ID: {verification[0]}")
                        logging.info(f"[DB_PROTECTION]   - Con_Codigo: {verification[1]}")
                        logging.info(f"[DB_PROTECTION]   - Protetor: {verification[2]}")
                        logging.info(f"[DB_PROTECTION]   - Status: {verification[3]}")
                        logging.info(f"[DB_PROTECTION]   - Criado em: {verification[4]}")
                        logging.info(f"[DB_PROTECTION]   - Expira em: {verification[5]}")
                        logging.info(f"[DB_PROTECTION]   - Hash no banco: {verification[6][:16]}...")
                        logging.info(f"[DB_PROTECTION]   - Hash confere: {verification[6] == password_hash}")
                    else:
                        logging.error(f"[DB_PROTECTION] ❌ Verificação falhou - registro não encontrado no banco!")
                    
                    return True, "Proteção de sessão ativada com sucesso", protection_id
                else:
                    logging.error(f"[DB_PROTECTION] ❌ SP retornou resultado inválido: {result}")
                    return False, "Erro ao criar proteção", None
                    
        except self.driver_module.Error as e:
            logging.error(f"[DB_PROTECTION] ❌ Erro de driver do banco: {e}")
            logging.error(f"[DB_PROTECTION] Tipo de erro: {type(e).__name__}")
            return False, f"Erro no banco de dados: {e}", None
        except Exception as e:
            logging.error(f"[DB_PROTECTION] ❌ Erro inesperado: {e}")
            logging.error(f"[DB_PROTECTION] Tipo de erro: {type(e).__name__}")
            import traceback
            logging.error(f"[DB_PROTECTION] Stack trace: {traceback.format_exc()}")
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
        logging.info(f"[DB_PROTECTION] 🔐 VALIDANDO SENHA DE PROTEÇÃO")
        logging.info(f"[DB_PROTECTION] Parâmetros de validação:")
        logging.info(f"[DB_PROTECTION]   - con_codigo: {con_codigo}")
        logging.info(f"[DB_PROTECTION]   - requesting_user: {requesting_user}")
        logging.info(f"[DB_PROTECTION]   - requesting_machine: {requesting_machine}")
        logging.info(f"[DB_PROTECTION]   - ip_address: {ip_address}")
        logging.info(f"[DB_PROTECTION]   - password length: {len(password) if password else 0} chars")
        
        try:
            # Gera hash da senha
            logging.info("[DB_PROTECTION] Gerando hash SHA-256 da senha fornecida...")
            password_hash = self._hash_password(password)
            logging.info(f"[DB_PROTECTION] Hash gerado: {password_hash[:16]}...")
            logging.info(f"[DB_PROTECTION] Hash length: {len(password_hash)} chars")
            
            with self.db.get_cursor() as cursor:
                if not cursor:
                    logging.error("[DB_PROTECTION] ❌ Falha ao obter cursor do banco")
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                logging.info("[DB_PROTECTION] Cursor obtido com sucesso")
                
                # Verifica se a stored procedure existe
                logging.info("[DB_PROTECTION] Verificando existência da stored procedure sp_Validar_Protecao_Sessao...")
                cursor.execute("""
                    SELECT COUNT(*) FROM sys.objects 
                    WHERE type = 'P' AND name = 'sp_Validar_Protecao_Sessao'
                """)
                sp_exists = cursor.fetchone()[0]
                logging.info(f"[DB_PROTECTION] SP sp_Validar_Protecao_Sessao existe: {sp_exists > 0}")
                
                if sp_exists == 0:
                    logging.warning("[DB_PROTECTION] ⚠️ SP de validação não encontrada - usando validação direta")
                    result = self._validate_password_direct(cursor, con_codigo, password_hash, 
                                                        requesting_user, requesting_machine, ip_address)
                    logging.info(f"[DB_PROTECTION] Resultado validação direta: {result}")
                    return result
                
                # Chama stored procedure para validar
                logging.info("[DB_PROTECTION] Executando stored procedure sp_Validar_Protecao_Sessao...")
                logging.debug(f"[DB_PROTECTION] Parâmetros da SP:")
                logging.debug(f"[DB_PROTECTION]   @Con_Codigo = {con_codigo}")
                logging.debug(f"[DB_PROTECTION]   @Prot_Senha_Hash = {password_hash[:16]}...")
                logging.debug(f"[DB_PROTECTION]   @Usu_Nome_Solicitante = {requesting_user}")
                logging.debug(f"[DB_PROTECTION]   @Usu_Maquina_Solicitante = {requesting_machine}")
                logging.debug(f"[DB_PROTECTION]   @LTent_IP_Solicitante = {ip_address}")
                
                try:
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
                    logging.info(f"[DB_PROTECTION] Resultado da SP: {result}")
                
                except self.driver_module.Error as sp_error:
                    logging.error(f"[DB_PROTECTION] ❌ Erro na stored procedure: {sp_error}")
                    logging.warning("[DB_PROTECTION] Tentando validação direta como fallback...")
                    
                    result = self._validate_password_direct(cursor, con_codigo, password_hash, 
                                                        requesting_user, requesting_machine, ip_address)
                    logging.info(f"[DB_PROTECTION] Resultado validação direta: {result}")
                    return result
                
                if result:
                    resultado = result[0]
                    protection_id = result[1]
                    protected_by = result[2]
                    
                    logging.info(f"[DB_PROTECTION] Dados retornados:")
                    logging.info(f"[DB_PROTECTION]   - Resultado: {resultado}")
                    logging.info(f"[DB_PROTECTION]   - Protection ID: {protection_id}")
                    logging.info(f"[DB_PROTECTION]   - Protegido por: {protected_by}")
                    
                    if resultado == 'SUCESSO':
                        logging.info(f"[DB_PROTECTION] ✅ ACESSO AUTORIZADO!")
                        logging.info(f"[DB_PROTECTION] Usuário {requesting_user} autorizado para servidor {con_codigo}")
                        logging.info(f"[DB_PROTECTION] 📝 AUDITORIA: Acesso bem-sucedido")
                        logging.info(f"[DB_PROTECTION] Proteção ID {protection_id} criada por {protected_by}")
                        
                        return {
                            "valid": True,
                            "protection_id": protection_id,
                            "protected_by": protected_by,
                            "message": "Senha correta - acesso autorizado"
                        }
                    elif resultado == 'SENHA_INCORRETA':
                        logging.warning(f"[DB_PROTECTION] ❌ SENHA INCORRETA!")
                        logging.warning(f"[DB_PROTECTION] Tentativa de acesso negada para {requesting_user}")
                        logging.warning(f"[DB_PROTECTION] 🚨 AUDITORIA: Senha incorreta para servidor {con_codigo}")
                        logging.warning(f"[DB_PROTECTION] Servidor protegido por {protected_by}")
                        
                        return {
                            "valid": False,
                            "protection_id": protection_id,
                            "protected_by": protected_by,
                            "message": "Senha de proteção incorreta"
                        }
                    elif resultado == 'NEGADA':
                        logging.warning(f"[DB_PROTECTION] ⚠️ ACESSO NEGADO - Servidor não protegido")
                        logging.info(f"[DB_PROTECTION] Servidor {con_codigo} não possui proteção ativa")
                        
                        return {
                            "valid": False,
                            "protection_id": None,
                            "protected_by": None,
                            "message": "Servidor não está protegido"
                        }
                    else:
                        logging.error(f"[DB_PROTECTION] ❌ RESULTADO INESPERADO: {resultado}")
                        logging.error(f"[DB_PROTECTION] Protection ID: {protection_id}, Protetor: {protected_by}")
                        
                        return {
                            "valid": False,
                            "protection_id": protection_id,
                            "protected_by": protected_by,
                            "message": f"Acesso negado: {resultado}"
                        }
                else:
                    logging.error(f"[DB_PROTECTION] ❌ SP retornou resultado nulo")
                    
                    return {
                        "valid": False,
                        "protection_id": None,
                        "protected_by": None,
                        "message": "Erro na validação"
                    }
                    
        except self.driver_module.Error as e:
            logging.error(f"[DB_PROTECTION] ❌ Erro de driver do banco: {e}")
            logging.error(f"[DB_PROTECTION] Tipo de erro: {type(e).__name__}")
            return {
                "valid": False,
                "protection_id": None,
                "protected_by": None,
                "message": f"Erro no banco de dados: {e}"
            }
        except Exception as e:
            logging.error(f"[DB_PROTECTION] ❌ Erro inesperado na validação: {e}")
            logging.error(f"[DB_PROTECTION] Tipo de erro: {type(e).__name__}")
            import traceback
            logging.error(f"[DB_PROTECTION] Stack trace: {traceback.format_exc()}")
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
        logging.info(f"[DB_PROTECTION] 🗑️ REMOVENDO PROTEÇÃO DE SESSÃO")
        logging.info(f"[DB_PROTECTION] Conexão: {con_codigo}")
        logging.info(f"[DB_PROTECTION] Usuário removedor: {removing_user}")
        
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    logging.error("[DB_PROTECTION] ❌ Falha ao obter cursor do banco")
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                logging.info("[DB_PROTECTION] Cursor obtido com sucesso")
                
                # Primeiro verifica se existe proteção ativa
                logging.info(f"[DB_PROTECTION] Verificando proteção ativa para conexão {con_codigo}...")
                cursor.execute("""
                    SELECT Prot_Id, Usu_Nome_Protetor, Prot_Data_Criacao, Prot_Data_Expiracao
                    FROM Sessao_Protecao_WTS 
                    WHERE Con_Codigo = ? 
                      AND Prot_Status = 'ATIVA' 
                      AND Prot_Data_Expiracao > GETDATE()
                """, (con_codigo,))
                
                protection = cursor.fetchone()
                
                if not protection:
                    logging.warning(f"[DB_PROTECTION] ⚠️ Nenhuma proteção ativa encontrada para conexão {con_codigo}")
                    return False, "Não há proteção ativa para esta sessão"
                
                prot_id, protected_by, data_criacao, data_expiracao = protection
                logging.info(f"[DB_PROTECTION] Proteção encontrada:")
                logging.info(f"[DB_PROTECTION]   - ID: {prot_id}")
                logging.info(f"[DB_PROTECTION]   - Criado por: {protected_by}")
                logging.info(f"[DB_PROTECTION]   - Data criação: {data_criacao}")
                logging.info(f"[DB_PROTECTION]   - Data expiração: {data_expiracao}")
                
                # Verifica se a stored procedure existe
                logging.info("[DB_PROTECTION] Verificando stored procedure sp_Remover_Protecao_Sessao...")
                cursor.execute("""
                    SELECT COUNT(*) FROM sys.objects 
                    WHERE type = 'P' AND name = 'sp_Remover_Protecao_Sessao'
                """)
                sp_exists = cursor.fetchone()[0]
                logging.info(f"[DB_PROTECTION] SP sp_Remover_Protecao_Sessao existe: {sp_exists > 0}")
                
                if sp_exists > 0:
                    # Chama stored procedure para remover
                    logging.info("[DB_PROTECTION] Executando stored procedure sp_Remover_Protecao_Sessao...")
                    logging.debug(f"[DB_PROTECTION] Parâmetros da SP:")
                    logging.debug(f"[DB_PROTECTION]   @Con_Codigo = {con_codigo}")
                    logging.debug(f"[DB_PROTECTION]   @Usu_Nome_Removedor = {removing_user}")
                    
                    cursor.execute("""
                        DECLARE @Sucesso BIT;
                        EXEC sp_Remover_Protecao_Sessao 
                            @Con_Codigo = ?,
                            @Usu_Nome_Removedor = ?,
                            @Sucesso = @Sucesso OUTPUT;
                        SELECT @Sucesso AS Sucesso;
                    """, (con_codigo, removing_user))
                    
                    result = cursor.fetchone()
                    logging.info(f"[DB_PROTECTION] Resultado da SP: {result}")
                    
                    if result and result[0]:
                        logging.info(f"[DB_PROTECTION] ✅ PROTEÇÃO REMOVIDA COM SUCESSO VIA SP!")
                        logging.info(f"[DB_PROTECTION] Servidor {con_codigo} desprotegido por {removing_user}")
                        logging.info(f"[DB_PROTECTION] 📝 AUDITORIA: Proteção removida via SP")
                        return True, "Proteção de sessão removida com sucesso"
                    else:
                        logging.warning(f"[DB_PROTECTION] ❌ SP retornou falha na remoção")
                        return False, "Não foi possível remover a proteção. Verifique se você é o criador da proteção."
                else:
                    # Fallback: UPDATE direto
                    logging.warning("[DB_PROTECTION] ⚠️ SP não encontrada - usando UPDATE direto")
                    logging.info(f"[DB_PROTECTION] Executando UPDATE direto na tabela...")
                    
                    cursor.execute("""
                        UPDATE Sessao_Protecao_WTS 
                        SET Prot_Status = 'REMOVIDA',
                            Prot_Data_Remocao = GETDATE(),
                            Usu_Nome_Removedor = ?
                        WHERE Con_Codigo = ? 
                          AND Prot_Status = 'ATIVA'
                          AND Prot_Data_Expiracao > GETDATE()
                    """, (removing_user, con_codigo))
                    
                    # Verifica se algum registro foi atualizado
                    rows_affected = cursor.rowcount
                    logging.info(f"[DB_PROTECTION] Registros afetados: {rows_affected}")
                    
                    if rows_affected > 0:
                        logging.info(f"[DB_PROTECTION] ✅ PROTEÇÃO REMOVIDA COM SUCESSO VIA UPDATE!")
                        logging.info(f"[DB_PROTECTION] Servidor {con_codigo} desprotegido por {removing_user}")
                        logging.info(f"[DB_PROTECTION] 📝 AUDITORIA: Proteção removida via UPDATE direto")
                        return True, "Proteção de sessão removida com sucesso"
                    else:
                        logging.error(f"[DB_PROTECTION] ❌ Nenhum registro foi atualizado")
                        return False, "Não foi possível remover a proteção"
                    
        except self.driver_module.Error as e:
            logging.error(f"[DB_PROTECTION] ❌ Erro de driver do banco: {e}")
            logging.error(f"[DB_PROTECTION] Tipo de erro: {type(e).__name__}")
            return False, f"Erro no banco de dados: {e}"
        except Exception as e:
            logging.error(f"[DB_PROTECTION] ❌ Erro inesperado ao remover proteção: {e}")
            logging.error(f"[DB_PROTECTION] Tipo de erro: {type(e).__name__}")
            import traceback
            logging.error(f"[DB_PROTECTION] Stack trace: {traceback.format_exc()}")
            return False, f"Erro inesperado: {e}"

    def remove_user_protections(self, user_name: str):
        """
        Remove todas as proteções criadas por um usuário específico.
        
        Args:
            user_name: Nome do usuário cujas proteções devem ser removidas
            
        Returns:
            (success, message)
        """
        try:
            logging.info(f"[DB_PROTECTION] 🔒 LOGOUT: Removendo todas as proteções do usuário {user_name}")
            
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                # Primeiro busca todas as proteções ativas do usuário
                cursor.execute("""
                    SELECT sp.Prot_Id, sp.Con_Codigo, c.Con_Nome
                    FROM [dbo].[Sessao_Protecao_WTS] sp
                    LEFT JOIN [dbo].[Conexao_WTS] c ON sp.Con_Codigo = c.Con_Codigo
                    WHERE sp.Usu_Nome_Protetor = ? 
                      AND sp.Prot_Status = 'ATIVA'
                      AND sp.Prot_Data_Expiracao > GETDATE()
                """, (user_name,))
                
                user_protections = cursor.fetchall()
                
                if not user_protections:
                    logging.info(f"[DB_PROTECTION] 🔒 LOGOUT: Nenhuma proteção ativa encontrada para {user_name}")
                    return True, "Nenhuma proteção ativa encontrada"
                
                logging.info(f"[DB_PROTECTION] 🔒 LOGOUT: Encontradas {len(user_protections)} proteções para remover")
                
                # Remove cada proteção
                removed_count = 0
                for prot_id, con_codigo, con_nome in user_protections:
                    try:
                        logging.info(f"[DB_PROTECTION] 🔒 LOGOUT: Removendo proteção ID {prot_id} da conexão {con_codigo} ({con_nome})")
                        
                        # Remove a proteção
                        cursor.execute("""
                            UPDATE [dbo].[Sessao_Protecao_WTS]
                            SET [Prot_Status] = 'REMOVIDA',
                                [Prot_Data_Remocao] = GETDATE(),
                                [Prot_Removida_Por] = ?
                            WHERE Prot_Id = ?
                        """, (f"{user_name}_LOGOUT", prot_id))
                        
                        # Log da remoção
                        cursor.execute("""
                            INSERT INTO [dbo].[Log_Tentativa_Protecao_WTS] (
                                [Prot_Id], [Con_Codigo], [Usu_Nome_Solicitante], 
                                [LTent_Resultado], [LTent_Observacoes]
                            ) VALUES (?, ?, ?, 'CANCELADA', 'Proteção removida automaticamente no logout')
                        """, (prot_id, con_codigo, user_name))
                        
                        removed_count += 1
                        logging.info(f"[DB_PROTECTION] ✅ LOGOUT: Proteção ID {prot_id} removida com sucesso")
                        
                    except Exception as e:
                        logging.error(f"[DB_PROTECTION] ❌ LOGOUT: Erro ao remover proteção ID {prot_id}: {e}")
                
                if removed_count > 0:
                    logging.info(f"[DB_PROTECTION] 🔒 LOGOUT CONCLUÍDO: {removed_count} proteções do usuário {user_name} removidas")
                    return True, f"{removed_count} proteções removidas com sucesso"
                else:
                    logging.warning(f"[DB_PROTECTION] ⚠️ LOGOUT: Falha ao remover proteções do usuário {user_name}")
                    return False, "Falha ao remover proteções"
                    
        except self.driver_module.Error as e:
            logging.error(f"[DB_PROTECTION] ❌ LOGOUT: Erro de driver do banco: {e}")
            return False, f"Erro no banco de dados: {e}"
        except Exception as e:
            logging.error(f"[DB_PROTECTION] ❌ LOGOUT: Erro inesperado: {e}")
            import traceback
            logging.error(f"[DB_PROTECTION] LOGOUT Stack trace: {traceback.format_exc()}")
            return False, f"Erro inesperado: {e}"

    def is_session_protected(self, con_codigo: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verifica se uma sessão está protegida.
        
        Returns:
            (is_protected, protection_info)
        """
        try:
            logging.info("Is protected")
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
                    logging.info("cheguei aqui")
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
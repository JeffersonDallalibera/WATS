# WATS_Project/wats_app/services/access_management_service.py
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from src.wats.db.repositories.connection_repository import ConnectionRepository
from src.wats.db.repositories.user_repository import UserRepository


class AccessManagementService:
    """
    Serviço para gerenciamento avançado de liberação de acessos.
    Facilita operações complexas de permissões individuais e por grupo.
    """

    def __init__(self, user_repo: UserRepository, connection_repo: ConnectionRepository):
        self.user_repo = user_repo
        self.connection_repo = connection_repo

    def liberar_acesso_temporario(
        self,
        user_id: int,
        conexao_id: int,
        responsavel: str,
        horas_duracao: int = 24,
        motivo: str = None,
    ) -> Tuple[bool, str]:
        """
        Libera acesso temporário para um usuário por um período específico.

        Args:
            user_id: ID do usuário
            conexao_id: ID da conexão
            responsavel: Quem está liberando o acesso
            horas_duracao: Duração em horas (padrão 24h)
            motivo: Motivo da liberação

        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            # Calcula data de expiração
            data_expiracao = datetime.now() + timedelta(hours=horas_duracao)
            data_expiracao_str = data_expiracao.strftime("%Y-%m-%d %H:%M:%S")

            motivo_completo = f"{motivo or 'Acesso temporário'} - Válido até {data_expiracao.strftime('%d/%m/%Y %H:%M')}"

            sucesso, mensagem = self.user_repo.liberar_acesso_individual(
                user_id, conexao_id, responsavel, motivo_completo, data_expiracao_str
            )

            if sucesso:
                logging.info(
                    f"[ACCESS_MGMT] Acesso temporário liberado: Usuário {user_id} -> Conexão {conexao_id} por {horas_duracao}h"
                )

            return sucesso, mensagem

        except Exception as e:
            logging.error(f"Erro ao liberar acesso temporário: {e}")
            return False, f"Erro interno: {e}"

    def liberar_acesso_permanente(
        self, user_id: int, conexao_id: int, responsavel: str, motivo: str = None
    ) -> Tuple[bool, str]:
        """
        Libera acesso permanente (sem expiração) para um usuário.

        Args:
            user_id: ID do usuário
            conexao_id: ID da conexão
            responsavel: Quem está liberando o acesso
            motivo: Motivo da liberação

        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            motivo_completo = f"{motivo or 'Acesso permanente liberado'}"

            sucesso, mensagem = self.user_repo.liberar_acesso_individual(
                user_id, conexao_id, responsavel, motivo_completo, None
            )

            if sucesso:
                logging.info(
                    f"[ACCESS_MGMT] Acesso permanente liberado: Usuário {user_id} -> Conexão {conexao_id}"
                )

            return sucesso, mensagem

        except Exception as e:
            logging.error(f"Erro ao liberar acesso permanente: {e}")
            return False, f"Erro interno: {e}"

    def bloquear_acesso_usuario(
        self, user_id: int, conexao_id: int, responsavel: str, motivo: str = None
    ) -> Tuple[bool, str]:
        """
        Bloqueia explicitamente o acesso de um usuário, mesmo que ele tenha acesso por grupo.

        Args:
            user_id: ID do usuário
            conexao_id: ID da conexão
            responsavel: Quem está bloqueando o acesso
            motivo: Motivo do bloqueio

        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            motivo_completo = f"{motivo or 'Acesso bloqueado por administrador'}"

            sucesso, mensagem = self.user_repo.bloquear_acesso_individual(
                user_id, conexao_id, responsavel, motivo_completo
            )

            if sucesso:
                logging.info(
                    f"[ACCESS_MGMT] Acesso bloqueado: Usuário {user_id} -> Conexão {conexao_id}"
                )

            return sucesso, mensagem

        except Exception as e:
            logging.error(f"Erro ao bloquear acesso: {e}")
            return False, f"Erro interno: {e}"

    def restaurar_acesso_grupo(self, user_id: int, conexao_id: int) -> Tuple[bool, str]:
        """
        Remove a permissão individual, fazendo o usuário voltar a usar apenas o acesso por grupo.

        Args:
            user_id: ID do usuário
            conexao_id: ID da conexão

        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            sucesso, mensagem = self.user_repo.remover_acesso_individual(user_id, conexao_id)

            if sucesso:
                logging.info(
                    f"[ACCESS_MGMT] Acesso restaurado para grupo: Usuário {user_id} -> Conexão {conexao_id}"
                )

            return sucesso, mensagem

        except Exception as e:
            logging.error(f"Erro ao restaurar acesso por grupo: {e}")
            return False, f"Erro interno: {e}"

    def verificar_status_acesso(self, user_id: int, conexao_id: int) -> Dict[str, Any]:
        """
        Verifica o status detalhado do acesso de um usuário a uma conexão.

        Args:
            user_id: ID do usuário
            conexao_id: ID da conexão

        Returns:
            Dicionário com informações detalhadas do acesso
        """
        try:
            return self.user_repo.verificar_acesso_conexao(user_id, conexao_id)
        except Exception as e:
            logging.error(f"Erro ao verificar status de acesso: {e}")
            return {"tem_acesso": False, "tipo_acesso": "ERRO", "motivo": f"Erro interno: {e}"}

    def listar_acessos_expirados(self) -> List[Dict[str, Any]]:
        """
        Lista todos os acessos individuais que expiraram.

        Returns:
            Lista de acessos expirados
        """
        try:
            # Implementa consulta para acessos expirados
            # Aqui você pode implementar uma consulta específica
            # Por enquanto, retorna lista vazia
            return []
        except Exception as e:
            logging.error(f"Erro ao listar acessos expirados: {e}")
            return []

    def renovar_acesso_temporario(
        self, user_id: int, conexao_id: int, responsavel: str, novas_horas: int = 24
    ) -> Tuple[bool, str]:
        """
        Renova um acesso temporário existente.

        Args:
            user_id: ID do usuário
            conexao_id: ID da conexão
            responsavel: Quem está renovando
            novas_horas: Novas horas de duração

        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            # Verifica se existe acesso atual
            status = self.verificar_status_acesso(user_id, conexao_id)

            if status["tipo_acesso"] not in ["INDIVIDUAL_LIBERADO", "INDIVIDUAL_BLOQUEADO"]:
                return False, "Usuário não possui acesso individual para renovar."

            # Cria nova data de expiração
            nova_expiracao = datetime.now() + timedelta(hours=novas_horas)
            nova_expiracao_str = nova_expiracao.strftime("%Y-%m-%d %H:%M:%S")

            motivo = f"Acesso renovado - Válido até {nova_expiracao.strftime('%d/%m/%Y %H:%M')}"

            sucesso, mensagem = self.user_repo.liberar_acesso_individual(
                user_id, conexao_id, responsavel, motivo, nova_expiracao_str
            )

            if sucesso:
                logging.info(
                    f"[ACCESS_MGMT] Acesso renovado: Usuário {user_id} -> Conexão {conexao_id} por {novas_horas}h"
                )

            return sucesso, mensagem

        except Exception as e:
            logging.error(f"Erro ao renovar acesso: {e}")
            return False, f"Erro interno: {e}"

    def listar_usuarios_com_acesso_individual(self, conexao_id: int) -> List[Dict[str, Any]]:
        """
        Lista usuários que têm permissão individual específica para uma conexão.

        Args:
            conexao_id: ID da conexão

        Returns:
            Lista de usuários com acesso individual
        """
        try:
            todos_usuarios = self.user_repo.listar_acessos_conexao(conexao_id)

            # Filtra apenas os que têm acesso individual
            usuarios_individuais = [
                usuario
                for usuario in todos_usuarios
                if usuario["tipo_acesso"] in ["INDIVIDUAL_LIBERADO", "INDIVIDUAL_BLOQUEADO"]
            ]

            return usuarios_individuais

        except Exception as e:
            logging.error(f"Erro ao listar usuários com acesso individual: {e}")
            return []

    def relatorio_acessos_por_usuario(self, user_id: int) -> Dict[str, Any]:
        """
        Gera relatório completo de acessos de um usuário.

        Args:
            user_id: ID do usuário

        Returns:
            Dicionário com relatório detalhado
        """
        try:
            acessos = self.user_repo.listar_acessos_usuario(user_id)

            # Contabiliza tipos de acesso
            contadores = {
                "ADMIN": 0,
                "GRUPO": 0,
                "INDIVIDUAL_LIBERADO": 0,
                "INDIVIDUAL_BLOQUEADO": 0,
                "SEM_ACESSO": 0,
            }

            for acesso in acessos:
                tipo = acesso["tipo_acesso"]
                if tipo in contadores:
                    contadores[tipo] += 1

            return {
                "user_id": user_id,
                "total_conexoes": len(acessos),
                "acessos_liberados": sum(
                    [contadores["ADMIN"], contadores["GRUPO"], contadores["INDIVIDUAL_LIBERADO"]]
                ),
                "acessos_bloqueados": contadores["INDIVIDUAL_BLOQUEADO"],
                "sem_acesso": contadores["SEM_ACESSO"],
                "detalhamento": contadores,
                "conexoes": acessos,
            }

        except Exception as e:
            logging.error(f"Erro ao gerar relatório de acessos: {e}")
            return {"user_id": user_id, "erro": f"Erro interno: {e}"}


# Exemplo de uso da classe:
"""
# Instanciar o serviço
access_service = AccessManagementService(user_repo, connection_repo)

# Liberar acesso temporário (24 horas)
sucesso, msg = access_service.liberar_acesso_temporario(
    user_id=123,
    conexao_id=456,
    responsavel="admin",
    horas_duracao=24,
    motivo="Manutenção emergencial"
)

# Bloquear acesso específico
sucesso, msg = access_service.bloquear_acesso_usuario(
    user_id=123,
    conexao_id=456,
    responsavel="admin",
    motivo="Violação de política de segurança"
)

# Verificar status
status = access_service.verificar_status_acesso(123, 456)
print(f"Tem acesso: {status['tem_acesso']}")
print(f"Tipo: {status['tipo_acesso']}")

# Gerar relatório do usuário
relatorio = access_service.relatorio_acessos_por_usuario(123)
"""

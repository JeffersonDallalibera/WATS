# WATS_Project/wats_app/examples/access_management_examples.py
"""
Exemplos práticos de como usar o sistema de liberação de acesso melhorado.
Demonstra cenários comuns de uso das novas funcionalidades.
"""

import logging

from src.wats.db.repositories.connection_repository import ConnectionRepository
from src.wats.db.repositories.user_repository import UserRepository
from src.wats.services.access_management_service import AccessManagementService


class AccessManagementExamples:
    """
    Exemplos práticos de gerenciamento de acesso.
    """

    def __init__(self, db_manager):
        self.user_repo = UserRepository(db_manager)
        self.connection_repo = ConnectionRepository(db_manager, self.user_repo)
        self.access_service = AccessManagementService(self.user_repo, self.connection_repo)

    def exemplo_acesso_emergencial(self):
        """
        Cenário: Técnico precisa de acesso emergencial a um servidor
        que normalmente não tem permissão.
        """
        print("\n=== EXEMPLO: ACESSO EMERGENCIAL ===")

        # Dados do exemplo
        user_id = 5  # ID do técnico
        conexao_id = 10  # Servidor de produção
        responsavel = "admin_plantao"

        # 1. Verificar acesso atual
        print("1. Verificando acesso atual...")
        status_inicial = self.access_service.verificar_status_acesso(user_id, conexao_id)
        print(f"   Status atual: {status_inicial}")

        # 2. Liberar acesso temporário (2 horas)
        print("2. Liberando acesso emergencial por 2 horas...")
        sucesso, mensagem = self.access_service.liberar_acesso_temporario(
            user_id=user_id,
            conexao_id=conexao_id,
            responsavel=responsavel,
            horas_duracao=2,
            motivo="Emergência - Falha crítica no sistema",
        )
        print(f"   Resultado: {mensagem}")

        # 3. Verificar novo status
        if sucesso:
            print("3. Verificando novo status...")
            status_final = self.access_service.verificar_status_acesso(user_id, conexao_id)
            print(f"   Novo status: {status_final}")

    def exemplo_bloqueio_especifico(self):
        """
        Cenário: Usuário faz parte de um grupo com acesso, mas precisa ser
        bloqueado especificamente de uma conexão.
        """
        print("\n=== EXEMPLO: BLOQUEIO ESPECÍFICO ===")

        # Dados do exemplo
        user_id = 8  # Usuário do grupo
        conexao_id = 15  # Servidor crítico
        responsavel = "security_admin"

        # 1. Verificar acesso por grupo
        print("1. Verificando acesso atual (provavelmente por grupo)...")
        status_inicial = self.access_service.verificar_status_acesso(user_id, conexao_id)
        print(f"   Status atual: {status_inicial}")

        # 2. Bloquear acesso específico
        print("2. Bloqueando acesso específico...")
        sucesso, mensagem = self.access_service.bloquear_acesso_usuario(
            user_id=user_id,
            conexao_id=conexao_id,
            responsavel=responsavel,
            motivo="Investigação de segurança em andamento",
        )
        print(f"   Resultado: {mensagem}")

        # 3. Verificar que agora está bloqueado
        if sucesso:
            print("3. Verificando que agora está bloqueado...")
            status_final = self.access_service.verificar_status_acesso(user_id, conexao_id)
            print(f"   Novo status: {status_final}")

    def exemplo_acesso_temporario_renovavel(self):
        """
        Cenário: Consultor externo precisa de acesso por tempo determinado,
        com possibilidade de renovação.
        """
        print("\n=== EXEMPLO: ACESSO TEMPORÁRIO RENOVÁVEL ===")

        # Dados do exemplo
        user_id = 12  # Consultor externo
        conexao_id = 20  # Servidor de desenvolvimento
        responsavel = "project_manager"

        # 1. Liberar acesso inicial (8 horas)
        print("1. Liberando acesso inicial para consultor (8 horas)...")
        sucesso, mensagem = self.access_service.liberar_acesso_temporario(
            user_id=user_id,
            conexao_id=conexao_id,
            responsavel=responsavel,
            horas_duracao=8,
            motivo="Consultoria - Análise de performance",
        )
        print(f"   Resultado: {mensagem}")

        # 2. Simular necessidade de renovação
        if sucesso:
            print("2. Simulando renovação do acesso...")
            sucesso_renovacao, msg_renovacao = self.access_service.renovar_acesso_temporario(
                user_id=user_id, conexao_id=conexao_id, responsavel=responsavel, novas_horas=4
            )
            print(f"   Renovação: {msg_renovacao}")

        # 3. Quando terminar, restaurar para acesso por grupo
        print("3. Finalizando consultoria - restaurando acesso por grupo...")
        sucesso_restore, msg_restore = self.access_service.restaurar_acesso_grupo(
            user_id, conexao_id
        )
        print(f"   Restauração: {msg_restore}")

    def exemplo_relatorio_completo(self):
        """
        Cenário: Administrador quer um relatório completo dos acessos de um usuário.
        """
        print("\n=== EXEMPLO: RELATÓRIO COMPLETO ===")

        user_id = 7  # Usuário para análise

        print(f"1. Gerando relatório completo para usuário {user_id}...")
        relatorio = self.access_service.relatorio_acessos_por_usuario(user_id)

        print("2. Resumo dos acessos:")
        print(f"   Total de conexões: {relatorio.get('total_conexoes', 0)}")
        print(f"   Acessos liberados: {relatorio.get('acessos_liberados', 0)}")
        print(f"   Acessos bloqueados: {relatorio.get('acessos_bloqueados', 0)}")
        print(f"   Sem acesso: {relatorio.get('sem_acesso', 0)}")

        print("3. Detalhamento por tipo:")
        detalhamento = relatorio.get("detalhamento", {})
        for tipo, quantidade in detalhamento.items():
            if quantidade > 0:
                print(f"   {tipo}: {quantidade}")

    def exemplo_listagem_usuarios_conexao(self):
        """
        Cenário: Verificar quais usuários têm acesso individual a uma conexão específica.
        """
        print("\n=== EXEMPLO: USUÁRIOS COM ACESSO INDIVIDUAL ===")

        conexao_id = 25  # Servidor específico

        print(f"1. Listando usuários com acesso individual à conexão {conexao_id}...")
        usuarios = self.access_service.listar_usuarios_com_acesso_individual(conexao_id)

        if usuarios:
            print(f"2. Encontrados {len(usuarios)} usuários com acesso individual:")
            for usuario in usuarios:
                status = "LIBERADO" if usuario["tem_acesso"] else "BLOQUEADO"
                expiracao = usuario.get("data_expiracao")
                exp_text = f" (expira: {expiracao})" if expiracao else " (permanente)"
                print(f"   - {usuario['usu_nome']}: {status}{exp_text}")
                if usuario.get("motivo"):
                    print(f"     Motivo: {usuario['motivo']}")
        else:
            print("2. Nenhum usuário com acesso individual encontrado.")

    def exemplo_casos_uso_completos(self):
        """
        Executa todos os exemplos para demonstração completa.
        """
        print("=" * 60)
        print("DEMONSTRAÇÃO COMPLETA - SISTEMA DE LIBERAÇÃO DE ACESSO")
        print("=" * 60)

        try:
            self.exemplo_acesso_emergencial()
            self.exemplo_bloqueio_especifico()
            self.exemplo_acesso_temporario_renovavel()
            self.exemplo_relatorio_completo()
            self.exemplo_listagem_usuarios_conexao()

        except Exception as e:
            print(f"\nERRO durante demonstração: {e}")
            logging.error(f"Erro na demonstração: {e}")

        print("\n" + "=" * 60)
        print("DEMONSTRAÇÃO CONCLUÍDA")
        print("=" * 60)


# Funções utilitárias para interface de linha de comando
def menu_interativo(access_service: AccessManagementService):
    """
    Menu interativo para testar as funcionalidades.
    """
    while True:
        print("\n" + "=" * 50)
        print("SISTEMA DE LIBERAÇÃO DE ACESSO")
        print("=" * 50)
        print("1. Liberar acesso temporário")
        print("2. Liberar acesso permanente")
        print("3. Bloquear acesso específico")
        print("4. Restaurar acesso por grupo")
        print("5. Verificar status de acesso")
        print("6. Renovar acesso temporário")
        print("7. Relatório de usuário")
        print("8. Listar acessos de conexão")
        print("0. Sair")
        print("-" * 50)

        try:
            opcao = input("Escolha uma opção: ").strip()

            if opcao == "0":
                print("Saindo...")
                break
            elif opcao == "1":
                menu_liberar_temporario(access_service)
            elif opcao == "2":
                # TODO: Implementar menu_liberar_permanente
                print("Funcionalidade não implementada ainda")
            elif opcao == "3":
                # TODO: Implementar menu_bloquear_acesso
                print("Funcionalidade não implementada ainda")
            elif opcao == "4":
                # TODO: Implementar menu_restaurar_grupo
                print("Funcionalidade não implementada ainda")
            elif opcao == "5":
                menu_verificar_status(access_service)
            elif opcao == "6":
                # TODO: Implementar menu_renovar_acesso
                print("Funcionalidade não implementada ainda")
            elif opcao == "7":
                # TODO: Implementar menu_relatorio_usuario
                print("Funcionalidade não implementada ainda")
            elif opcao == "8":
                # TODO: Implementar menu_listar_conexao
                print("Funcionalidade não implementada ainda")
            else:
                print("Opção inválida!")

        except KeyboardInterrupt:
            print("\nSaindo...")
            break
        except Exception as e:
            print(f"Erro: {e}")


def menu_liberar_temporario(access_service: AccessManagementService):
    """Menu para liberação de acesso temporário."""
    print("\n--- LIBERAR ACESSO TEMPORÁRIO ---")
    try:
        user_id = int(input("ID do usuário: "))
        conexao_id = int(input("ID da conexão: "))
        responsavel = input("Responsável: ")
        horas = int(input("Duração em horas (padrão 24): ") or "24")
        motivo = input("Motivo (opcional): ") or None

        sucesso, mensagem = access_service.liberar_acesso_temporario(
            user_id, conexao_id, responsavel, horas, motivo
        )

        print(f"\nResultado: {mensagem}")

    except ValueError as e:
        print(f"Erro: Valores inválidos - {e}")
    except Exception as e:
        print(f"Erro: {e}")


def menu_verificar_status(access_service: AccessManagementService):
    """Menu para verificação de status."""
    print("\n--- VERIFICAR STATUS DE ACESSO ---")
    try:
        user_id = int(input("ID do usuário: "))
        conexao_id = int(input("ID da conexão: "))

        status = access_service.verificar_status_acesso(user_id, conexao_id)

        print("\nStatus do acesso:")
        print(f"  Tem acesso: {status['tem_acesso']}")
        print(f"  Tipo: {status['tipo_acesso']}")
        print(f"  Motivo: {status['motivo']}")

    except ValueError as e:
        print(f"Erro: Valores inválidos - {e}")
    except Exception as e:
        print(f"Erro: {e}")


# Outras funções de menu seguem o mesmo padrão...

if __name__ == "__main__":
    # Exemplo de uso direto
    print("Para usar este módulo, importe e configure com seu db_manager:")
    print()
    print("from examples.access_management_examples import AccessManagementExamples")
    print("examples = AccessManagementExamples(db_manager)")
    print("examples.exemplo_casos_uso_completos()")

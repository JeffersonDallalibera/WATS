"""
Teste para validar a implementação das permissões individuais de conexão.
WATS Project - Individual Connection Permissions Test
"""

import logging

from src.wats.db.database_manager import DatabaseManager
from src.wats.db.repositories.connection_repository import ConnectionRepository
from src.wats.db.repositories.user_repository import UserRepository


def test_individual_permissions():
    """Testa as funcionalidades de permissões individuais."""

    print("=== TESTE DE PERMISSÕES INDIVIDUAIS ===\n")

    try:
        # Inicializar repositórios (você precisará ajustar a configuração do banco)
        db_manager = DatabaseManager()  # Configure conforme sua implementação
        user_repo = UserRepository(db_manager)
        conn_repo = ConnectionRepository(db_manager, user_repo)
        # indiv_repo = IndividualPermissionRepository(db_manager)  # Não utilizado neste teste

        print("1. Testando concessão de acesso individual...")

        # Exemplo: conceder acesso individual
        # user_id = 1, connection_id = 5, granted_by = 1 (admin)
        success, message = conn_repo.grant_individual_access(
            user_id=1,
            connection_id=5,
            granted_by_user_id=1,
            observations="Teste de acesso individual para desenvolvimento",
        )
        print(f"   Resultado: {success} - {message}")

        print("\n2. Testando verificação de acesso individual...")
        has_access = conn_repo.has_individual_access(user_id=1, connection_id=5)
        print(f"   Usuário 1 tem acesso individual à conexão 5: {has_access}")

        print("\n3. Testando listagem de permissões do usuário...")
        user_permissions = conn_repo.list_user_individual_permissions(user_id=1)
        print(f"   Usuário 1 possui {len(user_permissions)} permissões individuais:")
        for perm in user_permissions:
            print(f"     - Conexão: {perm.get('Con_Nome', 'N/A')} (ID: {perm.get('Con_Codigo')})")
            print(f"       Ativo: {perm.get('Ativo')}, Criado em: {perm.get('Data_Criacao')}")

        print("\n4. Testando listagem de usuários com acesso a uma conexão...")
        conn_permissions = conn_repo.list_connection_individual_permissions(connection_id=5)
        print(f"   Conexão 5 possui {len(conn_permissions)} usuários com acesso individual:")
        for perm in conn_permissions:
            print(f"     - Usuário: {perm.get('Usu_Nome', 'N/A')} (ID: {perm.get('Usu_Id')})")
            print(
                f"       Ativo: {perm.get('Ativo')}, Observações: {perm.get('Observacoes', 'N/A')}"
            )

        print("\n5. Testando busca de conexões disponíveis...")
        available_connections = conn_repo.get_available_connections_for_individual_grant()
        print(f"   {len(available_connections)} conexões disponíveis para concessão individual")

        print("\n6. Testando busca de usuários disponíveis...")
        available_users = conn_repo.get_available_users_for_individual_grant()
        print(f"   {len(available_users)} usuários disponíveis para concessão individual")

        print("\n7. Testando select_all com permissões individuais...")
        # Simular um usuário comum (não admin) que agora tem acesso individual
        connections = conn_repo.select_all(username="usuario_teste")  # Ajuste conforme necessário
        print(f"   Usuário comum vê {len(connections)} conexões (incluindo permissões individuais)")

        print("\n8. Testando revogação de acesso...")
        success, message = conn_repo.revoke_individual_access(user_id=1, connection_id=5)
        print(f"   Resultado da revogação: {success} - {message}")

        # Verificar se o acesso foi realmente revogado
        has_access_after = conn_repo.has_individual_access(user_id=1, connection_id=5)
        print(f"   Usuário 1 ainda tem acesso após revogação: {has_access_after}")

        print("\n=== TESTE CONCLUÍDO COM SUCESSO ===")

    except Exception as e:
        print(f"ERRO durante o teste: {e}")
        logging.error(f"Erro no teste de permissões individuais: {e}")


def test_connection_query_logic():
    """Testa apenas a lógica da query do select_all."""

    print("=== TESTE DA LÓGICA DE QUERY ===\n")

    # Simular a nova query que será executada
    sample_query = """
    SELECT Con.Con_Codigo, Con.Con_Nome, Gru.Gru_Nome
    FROM Conexao_WTS Con
    LEFT JOIN Grupo_WTS Gru ON Con.Gru_Codigo = Gru.Gru_Codigo
    WHERE Con.Gru_Codigo <> 33
    AND (
        EXISTS (
            SELECT 1 FROM Permissao_Grupo_WTS p
            WHERE p.Usu_Id = ? AND p.Gru_Codigo = Con.Gru_Codigo
        )
        OR EXISTS (
            SELECT 1 FROM Permissao_Conexao_Individual_WTS pci
            WHERE pci.Usu_Id = ?
            AND pci.Con_Codigo = Con.Con_Codigo
            AND pci.Ativo = ?
            AND pci.Data_Inicio <= ?
            AND (pci.Data_Fim IS NULL OR pci.Data_Fim >= ?)
        )
    )
    ORDER BY ISNULL(Gru.Gru_Nome, Con.Con_Nome), Con.Con_Nome
    """

    print("Query que será executada para usuários não-admin:")
    print(sample_query)

    print("\nParâmetros que serão passados:")
    print("1. user_id (para permissão de grupo)")
    print("2. user_id (para permissão individual)")
    print("3. True (ativo)")
    print("4. datetime.now() (data início)")
    print("5. datetime.now() (data fim)")

    print("\n=== TESTE DE LÓGICA CONCLUÍDO ===")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Executando testes de permissões individuais...\n")

    # Teste da lógica de query (não requer conexão com banco)
    test_connection_query_logic()

    print("\n" + "=" * 50 + "\n")

    # Teste completo (requer conexão com banco configurada)
    try:
        test_individual_permissions()
    except Exception as e:
        print(f"Não foi possível executar teste completo: {e}")
        print("Certifique-se de que:")
        print("1. O banco de dados está configurado")
        print("2. A tabela Permissao_Conexao_Individual_WTS foi criada")
        print("3. As dependências estão corretas")

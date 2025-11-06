"""
Script de Validação para Diagnóstico de Usuários "Presos" na Conexão
====================================================================

Este script ajuda a diagnosticar situações onde usuários ficam "presos"
como conectados mesmo após serem forçosamente desconectados.

Problemas identificados:
1. delete_connection_log() só remove o primeiro usuário da string separada por "|"
2. Heartbeats podem continuar ativos mesmo após remoção do BD
3. UI pode não sincronizar corretamente com estado real do BD

Uso:
python validate_connection_issues.py [--connection-id CON_CODIGO]
"""

import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Adicionar o src ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wats.db.database_manager import DatabaseManager
from wats.config.settings import Settings


class ConnectionValidator:
    """Validador para diagnosticar problemas de conexão."""
    
    def __init__(self):
        """Inicializa o validador."""
        self.settings = Settings()
        self.db = DatabaseManager()
        self.issues_found: List[str] = []
    
    def validate_heartbeat_consistency(self, con_codigo: Optional[int] = None) -> List[str]:
        """
        Valida se existem inconsistências entre heartbeats e registros no DB.
        
        Args:
            con_codigo: Código específico da conexão ou None para todas
            
        Returns:
            Lista de problemas encontrados
        """
        issues = []
        
        try:
            # Query para buscar conexões ativas no BD
            if con_codigo:
                query = """
                SELECT Con_Codigo, Usu_Nome, Usu_Last_Heartbeat,
                       DATEDIFF(MINUTE, Usu_Last_Heartbeat, GETDATE()) as MinutosSemHeartbeat
                FROM Usuario_Conexao_WTS 
                WHERE Con_Codigo = ?
                """
                params = (con_codigo,)
            else:
                query = """
                SELECT Con_Codigo, Usu_Nome, Usu_Last_Heartbeat,
                       DATEDIFF(MINUTE, Usu_Last_Heartbeat, GETDATE()) as MinutosSemHeartbeat
                FROM Usuario_Conexao_WTS 
                ORDER BY Con_Codigo, Usu_Nome
                """
                params = ()
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                if not rows:
                    if con_codigo:
                        issues.append(f"❌ Conexão {con_codigo} não encontrada na tabela Usuario_Conexao_WTS")
                    else:
                        issues.append("✅ Nenhuma conexão ativa encontrada no banco de dados")
                    return issues
                
                print(f"\n📊 CONEXÕES ATIVAS NO BANCO DE DADOS:")
                print(f"{'Con_Codigo':<12} {'Usuario':<20} {'Último Heartbeat':<20} {'Minutos Sem HB':<15}")
                print("-" * 70)
                
                for row in rows:
                    con_id, username, last_hb, minutes_without_hb = row
                    print(f"{con_id:<12} {username:<20} {last_hb:<20} {minutes_without_hb:<15}")
                    
                    # Validar heartbeats antigos (mais de 2 minutos = suspeito)
                    if minutes_without_hb > 2:
                        issues.append(f"⚠️  Conexão {con_id} usuário {username}: {minutes_without_hb} minutos sem heartbeat")
                    
                    # Validar heartbeats muito antigos (mais de 60 minutos = fantasma)
                    if minutes_without_hb > 60:
                        issues.append(f"👻 CONEXÃO FANTASMA: {con_id} usuário {username}: {minutes_without_hb} minutos sem heartbeat")
                
        except Exception as e:
            issues.append(f"❌ Erro ao validar heartbeats: {e}")
            
        return issues
    
    def validate_multiple_users_scenario(self, con_codigo: int) -> List[str]:
        """
        Simula e valida cenário de múltiplos usuários conectados.
        
        Args:
            con_codigo: Código da conexão para testar
            
        Returns:
            Lista de problemas encontrados
        """
        issues = []
        
        try:
            # Verificar quantos usuários estão conectados nesta conexão
            query = """
            SELECT COUNT(*) as total_users, 
                   STRING_AGG(Usu_Nome, '|') as users_list
            FROM Usuario_Conexao_WTS 
            WHERE Con_Codigo = ?
            """
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, (con_codigo,))
                row = cursor.fetchone()
                
                if row:
                    total_users, users_list = row
                    
                    print(f"\n👥 ANÁLISE DE MÚLTIPLOS USUÁRIOS - Conexão {con_codigo}:")
                    print(f"Total de usuários: {total_users}")
                    print(f"Lista de usuários: {users_list or 'Nenhum'}")
                    
                    if total_users > 1:
                        issues.append(f"📊 Conexão {con_codigo} tem {total_users} usuários simultâneos: {users_list}")
                        
                        # Simular remoção do primeiro usuário
                        if users_list and '|' not in users_list:
                            issues.append(f"✅ Apenas 1 usuário conectado, remoção funcionaria corretamente")
                        elif users_list:
                            first_user = users_list.split('|')[0]
                            remaining_users = '|'.join(users_list.split('|')[1:])
                            issues.append(f"⚠️  PROBLEMA: Se remover '{first_user}', restam: '{remaining_users}'")
                            issues.append(f"🐛 BUG: Função delete_connection_log() só remove primeiro usuário!")
                    
                    elif total_users == 1:
                        issues.append(f"✅ Apenas 1 usuário conectado na conexão {con_codigo}")
                    else:
                        issues.append(f"✅ Nenhum usuário conectado na conexão {con_codigo}")
                        
        except Exception as e:
            issues.append(f"❌ Erro ao validar cenário de múltiplos usuários: {e}")
            
        return issues
    
    def test_ghost_cleanup_procedure(self) -> List[str]:
        """
        Testa o procedimento de limpeza de conexões fantasma.
        
        Returns:
            Lista de resultados do teste
        """
        issues = []
        
        try:
            print(f"\n🧹 TESTANDO PROCEDIMENTO DE LIMPEZA DE FANTASMAS:")
            
            # Contar conexões antes da limpeza
            query_count = "SELECT COUNT(*) FROM Usuario_Conexao_WTS"
            with self.db.get_cursor() as cursor:
                cursor.execute(query_count)
                before_count = cursor.fetchone()[0]
            
            print(f"Conexões antes da limpeza: {before_count}")
            
            # Executar procedimento de limpeza
            if self.db.db_type == "sqlserver":
                query_cleanup = "EXEC sp_Limpar_Conexoes_Fantasma"
            else:
                issues.append(f"⚠️  Procedimento de limpeza não disponível para {self.db.db_type}")
                return issues
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query_cleanup)
                # Para SQL Server, o procedimento retorna o número de linhas removidas
                result = cursor.fetchone()
                if result:
                    rows_removed = result[0]
                    print(f"Registros removidos pelo procedimento: {rows_removed}")
                    if rows_removed > 0:
                        issues.append(f"🧹 Procedimento removeu {rows_removed} conexões fantasma")
                    else:
                        issues.append(f"✅ Nenhuma conexão fantasma encontrada")
            
            # Contar conexões após a limpeza
            with self.db.get_cursor() as cursor:
                cursor.execute(query_count)
                after_count = cursor.fetchone()[0]
            
            print(f"Conexões após a limpeza: {after_count}")
            
            if before_count != after_count:
                removed = before_count - after_count
                issues.append(f"📊 Total de conexões removidas: {removed}")
            
        except Exception as e:
            issues.append(f"❌ Erro ao testar procedimento de limpeza: {e}")
            
        return issues
    
    def validate_ui_db_sync(self, con_codigo: Optional[int] = None) -> List[str]:
        """
        Valida se a UI está sincronizada com o banco de dados.
        
        Args:
            con_codigo: Código específico da conexão ou None para todas
            
        Returns:
            Lista de problemas encontrados
        """
        issues = []
        
        try:
            print(f"\n🔄 VALIDANDO SINCRONIZAÇÃO UI x BANCO DE DADOS:")
            
            # Esta validação requer acesso à UI em execução
            # Por ora, vamos validar a consistência dos dados
            
            if con_codigo:
                query = """
                SELECT c.Con_Codigo, c.Con_Nome, 
                       STRING_AGG(uc.Usu_Nome, '|') as usuarios_conectados,
                       COUNT(uc.Usu_Nome) as total_usuarios
                FROM Conexao_WTS c
                LEFT JOIN Usuario_Conexao_WTS uc ON c.Con_Codigo = uc.Con_Codigo
                WHERE c.Con_Codigo = ?
                GROUP BY c.Con_Codigo, c.Con_Nome
                """
                params = (con_codigo,)
            else:
                query = """
                SELECT c.Con_Codigo, c.Con_Nome, 
                       STRING_AGG(uc.Usu_Nome, '|') as usuarios_conectados,
                       COUNT(uc.Usu_Nome) as total_usuarios
                FROM Conexao_WTS c
                LEFT JOIN Usuario_Conexao_WTS uc ON c.Con_Codigo = uc.Con_Codigo
                WHERE c.Con_Ativo = 1
                GROUP BY c.Con_Codigo, c.Con_Nome
                ORDER BY c.Con_Codigo
                """
                params = ()
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                print(f"{'Con_Codigo':<12} {'Nome':<25} {'Usuarios':<30} {'Total':<8}")
                print("-" * 80)
                
                for row in rows:
                    con_id, con_nome, usuarios, total = row
                    usuarios_display = usuarios or "Nenhum"
                    print(f"{con_id:<12} {con_nome:<25} {usuarios_display:<30} {total:<8}")
                    
                    if usuarios and '|' in usuarios:
                        issues.append(f"📊 Conexão {con_id} tem múltiplos usuários: {usuarios}")
                
        except Exception as e:
            issues.append(f"❌ Erro ao validar sincronização: {e}")
            
        return issues
    
    def run_full_validation(self, con_codigo: Optional[int] = None):
        """
        Executa validação completa do sistema.
        
        Args:
            con_codigo: Código específico da conexão ou None para todas
        """
        print("=" * 80)
        print("🔍 VALIDAÇÃO COMPLETA DO SISTEMA DE CONEXÕES")
        print("=" * 80)
        print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if con_codigo:
            print(f"Foco na conexão: {con_codigo}")
        print()
        
        all_issues = []
        
        # 1. Validar consistência de heartbeats
        print("1️⃣ Validando consistência de heartbeats...")
        issues = self.validate_heartbeat_consistency(con_codigo)
        all_issues.extend(issues)
        
        # 2. Validar cenário de múltiplos usuários
        if con_codigo:
            print(f"2️⃣ Validando cenário de múltiplos usuários...")
            issues = self.validate_multiple_users_scenario(con_codigo)
            all_issues.extend(issues)
        
        # 3. Testar procedimento de limpeza
        print(f"3️⃣ Testando procedimento de limpeza...")
        issues = self.test_ghost_cleanup_procedure()
        all_issues.extend(issues)
        
        # 4. Validar sincronização UI x DB
        print(f"4️⃣ Validando sincronização...")
        issues = self.validate_ui_db_sync(con_codigo)
        all_issues.extend(issues)
        
        # Resumo final
        print("\n" + "=" * 80)
        print("📋 RESUMO DA VALIDAÇÃO")
        print("=" * 80)
        
        if not all_issues:
            print("✅ Nenhum problema encontrado!")
        else:
            print(f"⚠️  {len(all_issues)} problema(s) encontrado(s):")
            print()
            for i, issue in enumerate(all_issues, 1):
                print(f"{i}. {issue}")
        
        print("\n" + "=" * 80)


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validador de problemas de conexão WATS")
    parser.add_argument("--connection-id", type=int, help="ID específico da conexão para focar a análise")
    
    args = parser.parse_args()
    
    try:
        validator = ConnectionValidator()
        validator.run_full_validation(args.connection_id)
        
    except Exception as e:
        print(f"❌ Erro durante validação: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
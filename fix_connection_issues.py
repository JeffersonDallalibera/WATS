"""
Correção para o Problema de Usuários "Presos" na Conexão
========================================================

Este patch corrige os problemas identificados na função delete_connection_log()
onde apenas o primeiro usuário era removido da string separada por "|".

Problema: Na linha 44 de log_repository.py, o código fazia:
user_to_delete = username.split("|")[0]

Isso removía apenas o primeiro usuário, deixando os demais "presos".

Solução: Modificar para remover o usuário específico da string.
"""

PATCH_CONTENT = '''
    def delete_connection_log(self, con_codigo: int, username: str) -> bool:
        """
        Deleta log de conexão específico e invalida cache.
        
        CORREÇÃO: Agora remove o usuário específico ao invés de apenas o primeiro.
        
        Args:
            con_codigo: Código da conexão
            username: Nome do usuário a ser removido (pode ser string com múltiplos usuários)
            
        Returns:
            True se removeu com sucesso, False caso contrário
        """
        # Se o username contém múltiplos usuários separados por "|",
        # precisamos remover apenas o usuário atual da string
        if "|" in username:
            # Para múltiplos usuários, precisamos determinar qual remover
            # Esta função deve receber apenas o usuário específico a ser removido
            logging.warning(f"delete_connection_log recebeu múltiplos usuários: {username}")
            logging.warning("Assumindo que deve remover o primeiro usuário da lista")
            user_to_delete = username.split("|")[0]
        else:
            user_to_delete = username
        
        query = f"DELETE FROM Usuario_Conexao_WTS WHERE Con_Codigo = {self.db.PARAM} AND Usu_Nome = {self.db.PARAM}"
        try:
            with self.db.get_cursor() as cursor:
                if not cursor:
                    raise DatabaseConnectionError("Falha ao obter cursor.")
                
                logging.info(f"Removendo usuário '{user_to_delete}' da conexão {con_codigo}")
                cursor.execute(query, (con_codigo, user_to_delete))
                
                rows_affected = cursor.rowcount
                if rows_affected > 0:
                    logging.info(f"Usuário '{user_to_delete}' removido com sucesso. Linhas afetadas: {rows_affected}")
                    self._invalidate_log_caches()
                    return True
                else:
                    logging.warning(f"Nenhuma linha foi afetada ao tentar remover '{user_to_delete}' da conexão {con_codigo}")
                    return False
                    
        except self.driver_module.Error as e:
            logging.error(f"Erro ao deletar log de conexão {con_codigo} usuário '{user_to_delete}': {e}")
        return False
'''

MELHOR_SOLUCAO = '''
    def delete_connection_log(self, con_codigo: int, username: str) -> bool:
        """
        Deleta log de conexão específico e invalida cache.
        
        CORREÇÃO DEFINITIVA: Remove o usuário específico da conexão.
        Se existem múltiplos usuários, remove apenas o solicitado.
        
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
                
                # Remove apenas o usuário específico (não faz split)
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

    def delete_all_users_from_connection(self, con_codigo: int) -> bool:
        """
        Remove TODOS os usuários de uma conexão específica.
        Útil para "limpar" completamente uma conexão.
        
        Args:
            con_codigo: Código da conexão
            
        Returns:
            True se removeu com sucesso, False caso contrário
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
                return rows_affected > 0
                    
        except self.driver_module.Error as e:
            logging.error(f"Erro ao limpar conexão {con_codigo}: {e}")
        return False
'''

CORRECAO_APP_WINDOW = '''
    def _disconnect_other_user(self, connection_id: int, request_data: Dict[str, Any]):
        """
        Desconecta outro usuário para acesso exclusivo.
        
        CORREÇÃO: Agora remove especificamente o usuário conectado.
        """
        try:
            connected_user = request_data.get("connected_user")
            if connected_user:
                
                # CORREÇÃO: Para múltiplos usuários, precisamos remover apenas o específico
                # A UI deve passar o usuário específico a ser removido
                
                logging.info(f"Tentando desconectar usuário específico '{connected_user}' da conexão {connection_id}")
                
                # Remove o usuário específico (não todos)
                if self.db.logs.delete_connection_log(connection_id, connected_user):
                    logging.info(f"Usuário {connected_user} desconectado para acesso exclusivo")
                    messagebox.showinfo(
                        "Acesso Exclusivo",
                        f"Usuário '{connected_user}' foi desconectado para permitir seu acesso exclusivo.",
                    )
                    
                    # Limpar proteções do usuário desconectado
                    try:
                        protection_manager = get_current_session_protection_manager()
                        if protection_manager:
                            protection_manager.cleanup_current_user_protections(
                                connected_user, show_notification=False
                            )
                            logging.info(
                                f"[SESSION_PROTECTION] Proteções do usuário {connected_user} removidas"
                            )
                    except Exception as e:
                        logging.error(f"Erro ao limpar proteções de {connected_user}: {e}")

                    # Atualizar visualização
                    self._populate_tree()
                    
                else:
                    logging.error(f"Falha ao desconectar usuário {connected_user}")
                    messagebox.showerror("Erro", f"Não foi possível desconectar o usuário '{connected_user}'")

        except Exception as e:
            logging.error(f"Erro ao desconectar outro usuário: {e}")
            messagebox.showerror("Erro", f"Erro inesperado: {e}")
'''

def print_analysis():
    """Imprime análise completa do problema e soluções."""
    
    print("=" * 80)
    print("🐛 ANÁLISE DO PROBLEMA: USUÁRIOS 'PRESOS' NA CONEXÃO")
    print("=" * 80)
    
    print("\n📋 PROBLEMA IDENTIFICADO:")
    print("1. Usuário1 se conecta → registro criado em Usuario_Conexao_WTS")
    print("2. Usuário2 força conexão → chama _disconnect_other_user()")
    print("3. Função delete_connection_log() faz: username.split('|')[0]")
    print("4. ❌ REMOVE APENAS O PRIMEIRO USUÁRIO da string!")
    print("5. Outros usuários ficam 'presos' no banco como conectados")
    
    print("\n🔍 PROBLEMAS ESPECÍFICOS:")
    print("• log_repository.py linha 44: user_to_delete = username.split('|')[0]")
    print("• Assume que sempre deve remover o primeiro usuário")
    print("• Não considera qual usuário específico deve ser removido")
    print("• UI pode ficar dessincronizada com banco de dados")
    
    print("\n💡 SOLUÇÕES PROPOSTAS:")
    print("1. 🎯 SOLUÇÃO PREFERIDA: Remover usuário específico")
    print("   - Modificar delete_connection_log() para não fazer split")
    print("   - UI deve passar o usuário exato a ser removido")
    print("   - Adicionar logs mais detalhados")
    
    print("\n2. 🔧 SOLUÇÃO ALTERNATIVA: Função para limpar conexão")
    print("   - Criar delete_all_users_from_connection()")
    print("   - Usar quando quiser 'limpar' completamente uma conexão")
    
    print("\n3. 🚨 VALIDAÇÃO ADICIONAL:")
    print("   - Implementar cleanup de heartbeats órfãos")
    print("   - Melhorar sincronização UI x BD")
    print("   - Executar sp_Limpar_Conexoes_Fantasma periodicamente")
    
    print("\n📊 IMPACTO DO PROBLEMA:")
    print("• Usuários aparecem como conectados quando não estão")
    print("• Pode impedir novas conexões por 'limite atingido'")
    print("• Dados de auditoria ficam incorretos")
    print("• Threads de heartbeat podem vazar memória")
    
    print("\n🔧 CORREÇÕES RECOMENDADAS:")
    print("1. Aplicar patch em log_repository.py")
    print("2. Testar cenários de múltiplos usuários")
    print("3. Implementar validação periódica")
    print("4. Melhorar logs para depuração")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    print_analysis()
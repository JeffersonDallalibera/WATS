# 🔧 Como Reativar o Sistema de Liberação Individual de Acessos

## ⚠️ IMPORTANTE: O sistema está temporariamente com algumas funcionalidades comentadas

Para evitar erros durante o startup, as seguintes funcionalidades estão temporariamente desabilitadas:

### 📂 **Arquivos que precisam ser descomentados após executar o script SQL:**

#### 1. **src/wats/admin_panels/admin_hub.py**
```python
# Descomentar estas linhas (linha ~10):
from .simple_access_manager import SimpleAccessManagerDialog

# Descomentar estas linhas (linha ~52-58):
btn_manage_access = ctk.CTkButton(
    self, text="🔐 Liberação de Acessos",
    height=45, command=self._open_access_manager, 
    fg_color="darkgreen", hover_color="green"
)
btn_manage_access.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

# Descomentar a função (linha ~94-102):
def _open_access_manager(self):
    """Abre o diálogo de gerenciamento de liberação de acessos."""
    logging.info("Abrindo gerenciador de liberação de acessos...")
    try:
        dialog = SimpleAccessManagerDialog(self, self.db)
        self.wait_window(dialog)
        self._on_admin_dialog_close()
    except Exception as e:
        logging.error(f"Erro ao abrir gerenciador de acessos: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir painel de acessos: {e}")
```

#### 2. **src/wats/admin_panels/access_manager.py**
```python
# Descomentar esta linha (linha ~9):
from ..services.access_management_service import AccessManagementService

# Descomentar estas linhas (linha ~21-23):
self.access_service = AccessManagementService(
    db.users, db.connections
)
```

#### 3. **src/wats/db/repositories/user_repository.py**
```python
# Adicionar novamente todos os métodos removidos após a linha ~200:
# - verificar_acesso_conexao()
# - liberar_acesso_individual()
# - bloquear_acesso_individual()
# - remover_acesso_individual()
# - _gerenciar_acesso_individual()
# - listar_acessos_usuario()
# - listar_acessos_conexao()
```

#### 4. **src/wats/db/repositories/connection_repository.py**
```python
# Reverter o método select_all() para a versão completa com verificação de acessos individuais
```

---

## 🚀 **Passos para Reativação:**

### **PASSO 1:** Execute o script SQL
```sql
-- Execute no banco WATS:
-- scripts/improve_access_control.sql
```

### **PASSO 2:** Descomente todos os códigos listados acima

### **PASSO 3:** Reinicie a aplicação WATS

### **PASSO 4:** Teste o novo botão "🔐 Liberação de Acessos" no Painel Admin

---

## ✅ **Funcionalidades que estarão disponíveis:**

- **Liberação Temporária:** Acesso por período determinado
- **Liberação Permanente:** Acesso sem data de expiração
- **Bloqueio Individual:** Negar acesso específico mesmo se estiver no grupo
- **Restaurar Acesso:** Voltar para permissão por grupo
- **Auditoria Completa:** Histórico de quem liberou/bloqueou quando
- **Prioridade de Acesso:** Admin > Individual > Grupo > Sem Acesso

---

## 📋 **Checklist de Verificação:**

- [ ] Script SQL executado com sucesso
- [ ] Tabela `Permissao_Conexao_WTS` criada
- [ ] Stored procedures criadas (para SQL Server)
- [ ] Todos os imports descomentados
- [ ] Todas as funções descomentadas
- [ ] Aplicação reiniciada
- [ ] Botão "🔐 Liberação de Acessos" aparece no Painel Admin
- [ ] Funcionalidades testadas com usuário admin

---

## 🔍 **Em caso de problemas:**

1. Verifique se o script SQL foi executado completamente
2. Confirme se a tabela `Permissao_Conexao_WTS` existe
3. Revise os logs da aplicação para erros específicos
4. Verifique se todos os códigos foram descomentados corretamente

**Status atual:** Sistema básico funcionando, aguardando execução do script SQL para ativar funcionalidades avançadas.